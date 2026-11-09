"""Final check 3 (R9), analysis step: does the XGBoost thread count change the Ms-per-cell predictions or the tier conclusions?

Inputs : final/work/ms_threads/{refit,select}__t<threads>__<split>.parquet  (check3_ms_threads_fit.py)
         EDA/10_phase7_validation/v1.2/work/ms_moment/main__<split>.parquet (saved Phase 7 predictions, n_jobs=16)
Outputs: final/outputs/check3_ms_threads/*.csv, thread_prediction_differences.png

Tables
  thread_reproduction_check.csv      16-thread rerun vs the saved Phase 7 predictions (same configuration -> must be identical)
  thread_prediction_differences.csv  |prediction(t) - prediction(16)| per mode, thread count, tier (max, mean, RMS, 99th percentile)
  thread_metrics_by_split.csv        test MAE / R2 per mode, threads, split, tier
  thread_tier_comparison.csv         pooled Tier 1 -> Tier 3 (and 1->2, 2->3) XGBoost improvement per thread count with formula-bootstrap CI,
                                     per-split spread and the Phase 7 stability verdict
  thread_hyperparameter_concordance.csv  (select mode) share of fits whose selected hyperparameters differ from the Phase 7 selection
Usage (from EDA/src):  python ../../final/scripts/check3_ms_threads_analysis.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parents[2] / "EDA" / "src"
sys.path.insert(0, str(SRC))

import phase7_aggregate as agg  # noqa: E402
import phase7_validation as p7  # noqa: E402

FINAL = Path(__file__).resolve().parents[1]
WORK = FINAL / "work" / "ms_threads"
OUT = FINAL / "outputs" / "check3_ms_threads"
THREADS = (1, 4, 16)
REFERENCE_THREADS = 16
TIERS = ("tier1", "tier2", "tier3")
COMPARISONS = [("tier1", "tier3"), ("tier1", "tier2"), ("tier2", "tier3")]
SPLIT_IDS = ["frozen"] + [str(i) for i in range(10)]
DIFF_TOLERANCE = 0.01      # muB per unit cell: a prediction change below this is far below the Ms-per-cell MAE (~2.5)


def load_runs(modes: tuple[str, ...] = ("refit", "select"), with_seeds: bool = False) -> pd.DataFrame:
    """All fit files of the given modes; seed_offset 0 = Phase 7 seed (file names without a seed tag)."""
    parts = []
    for path in sorted(WORK.glob("*__t*__*.parquet")):
        mode, tail = path.stem.split("__", 1)
        seed = int(tail.split("__s")[1].split("__")[0]) if "__s" in tail else 0
        if mode in modes and (with_seeds or seed == 0):
            parts.append(pd.read_parquet(path).assign(seed_offset=seed))
    out = pd.concat(parts, ignore_index=True)
    out["split_id"] = out["split_id"].astype(str)
    return out


def load_phase7(cfg7: dict) -> pd.DataFrame:
    work = p7.output_dir(cfg7, "v1.2") / "work" / "ms_moment"
    parts = [pd.read_parquet(work / f"main__{s}.parquet") for s in SPLIT_IDS]
    out = pd.concat(parts, ignore_index=True)
    out["split_id"] = out["split_id"].astype(str)
    return out[out["algorithm"] == "xgboost"]


def aligned(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    key = ["split_id", "variant", "material_id"]
    return a[key + ["y_pred"]].merge(b[key + ["y_pred"]], on=key, suffixes=("_a", "_b"), validate="one_to_one")


def diff_summary(merged: pd.DataFrame, mae_ref: float) -> dict:
    d = (merged["y_pred_a"] - merged["y_pred_b"]).abs().to_numpy()
    return {"n_predictions": len(d), "max_abs_diff": d.max(), "mean_abs_diff": d.mean(), "rms_diff": float(np.sqrt((d ** 2).mean())),
            "p99_abs_diff": float(np.quantile(d, 0.99)), "share_rows_diff_gt_0.01": float((d > DIFF_TOLERANCE).mean()),
            "n_identical": int((d == 0).sum()), "mean_abs_diff_pct_of_mae": 100 * d.mean() / mae_ref}


def reproduction_check(runs: pd.DataFrame, phase7: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for mode in ("refit", "select"):
        ref = runs[(runs["mode"] == mode) & (runs["threads"] == REFERENCE_THREADS)]
        for tier in TIERS:
            m = aligned(ref[ref["variant"] == tier], phase7[phase7["variant"] == tier])
            rows.append({"mode": mode, "variant": tier, **diff_summary(m, 1.0)})
    return pd.DataFrame(rows).drop(columns="mean_abs_diff_pct_of_mae")


def prediction_differences(runs: pd.DataFrame) -> pd.DataFrame:
    mae = runs.assign(e=(runs["y_pred"] - runs["y_true"]).abs()).groupby(["mode", "threads", "variant"])["e"].mean()
    rows = []
    for mode in ("refit", "select"):
        ref = runs[(runs["mode"] == mode) & (runs["threads"] == REFERENCE_THREADS)]
        for threads in (1, 4):
            cur = runs[(runs["mode"] == mode) & (runs["threads"] == threads)]
            for tier in TIERS:
                m = aligned(cur[cur["variant"] == tier], ref[ref["variant"] == tier])
                rows.append({"mode": mode, "threads_vs_16": threads, "variant": tier, **diff_summary(m, mae.loc[(mode, REFERENCE_THREADS, tier)])})
    return pd.DataFrame(rows)


def metrics_by_split(runs: pd.DataFrame) -> pd.DataFrame:
    def score(g: pd.DataFrame) -> pd.Series:
        e = g["y_pred"] - g["y_true"]
        sst = ((g["y_true"] - g["y_true"].mean()) ** 2).sum()
        return pd.Series({"n_test": len(g), "mae": e.abs().mean(), "r2": 1 - (e ** 2).sum() / sst})
    return runs.groupby(["mode", "threads", "split_id", "variant"]).apply(score, include_groups=False).reset_index()


def tier_comparison(runs: pd.DataFrame, cfg: dict, cfg7: dict) -> pd.DataFrame:
    pop = agg.Population.load(cfg, cfg7, "ms_moment", "v1.2")
    rows = []
    for (mode, threads, seed), part in runs.groupby(["mode", "threads", "seed_offset"]):
        stats = agg.keyed_stats(part, pop)
        paired = agg.paired_rows(stats, pop, cfg7, f"{mode}_t{threads}_s{seed}", COMPARISONS, ["xgboost"])
        robust = agg.robustness_summary(paired, cfg7["decision_gate"]["min_fraction_splits_positive"])
        robust = robust[robust["metric"] == "mae"]
        for r in robust.itertuples():
            rows.append({"mode": mode, "threads": threads, "seed_offset": seed, "from_variant": r.from_variant, "to_variant": r.to_variant,
                         "tier_from_mae": r.pooled_mean_from_value, "mae_improvement": r.pooled_mean_improvement,
                         "ci95_low": r.pooled_mean_ci_low, "ci95_high": r.pooled_mean_ci_high, "pct_of_from": r.pooled_mean_pct_of_from,
                         "split_mean": r.mean_improvement, "split_sd": r.sd, "split_min": r.min, "split_max": r.max,
                         "n_splits_improved": r.n_positive, "n_splits": r.n_splits, "stability_verdict": r.robust_verdict})
    return pd.DataFrame(rows)


def seed_noise_reference(seed_runs: pd.DataFrame) -> pd.DataFrame:
    """Prediction differences between model seeds at a FIXED thread count (16), same layout as thread_prediction_differences."""
    base = seed_runs[(seed_runs["seed_offset"] == 0)]
    rows = []
    for seed in sorted(set(seed_runs["seed_offset"]) - {0}):
        cur = seed_runs[seed_runs["seed_offset"] == seed]
        for tier in TIERS:
            m = aligned(cur[cur["variant"] == tier], base[base["variant"] == tier])
            mae = (base[base["variant"] == tier]["y_pred"] - base[base["variant"] == tier]["y_true"]).abs().mean()
            rows.append({"mode": "refit", "seed_offset_vs_0_at_16_threads": seed, "variant": tier, **diff_summary(m, mae)})
    return pd.DataFrame(rows)


def hgb_thread_check() -> pd.DataFrame:
    """sklearn HistGradientBoosting refit (saved Phase 7 hyperparameters) with the OpenMP pool limited to 1, 4, 16 threads."""
    parts = [pd.read_parquet(p) for p in sorted(WORK.glob("hgb_refit__t*__*.parquet"))]
    if not parts:
        return pd.DataFrame()
    runs = pd.concat(parts, ignore_index=True)
    runs["split_id"] = runs["split_id"].astype(str)
    ref = runs[runs["threads"] == REFERENCE_THREADS]
    rows = []
    for threads in (1, 4):
        cur = runs[runs["threads"] == threads]
        for tier in TIERS:
            m = aligned(cur[cur["variant"] == tier], ref[ref["variant"] == tier])
            mae = (ref[ref["variant"] == tier]["y_pred"] - ref[ref["variant"] == tier]["y_true"]).abs().mean()
            rows.append({"algorithm": "gradient_boosting (HistGB)", "threads_vs_16": threads, "variant": tier, "splits": ",".join(sorted(set(cur["split_id"]))),
                         **diff_summary(m, mae)})
    return pd.DataFrame(rows)


def hyperparameter_concordance(runs: pd.DataFrame) -> pd.DataFrame:
    sel = runs[runs["mode"] == "select"].drop_duplicates(["threads", "split_id", "variant"])
    sel = sel.assign(differs=sel["params"] != sel["phase7_params"])
    return (sel.groupby(["threads", "variant"]).agg(n_fits=("differs", "size"), n_selected_params_differ_from_phase7=("differs", "sum")).reset_index())


def phase7_reference(cfg7: dict) -> pd.DataFrame:
    path = p7.output_dir(cfg7, "v1.2") / "phase7_robustness_summary.csv"
    r = pd.read_csv(path)
    r = r[(r["target"] == "ms_moment") & (r["analysis"] == "primary_matched") & (r["metric"] == "mae") & (r["algorithm"] == "xgboost")]
    return r[["from_variant", "to_variant", "pooled_mean_improvement", "pooled_mean_ci_low", "pooled_mean_ci_high", "n_positive", "robust_verdict"]]


def plot_differences(runs: pd.DataFrame, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8), sharey=True)
    for ax, mode in zip(axes, ("refit", "select")):
        ref = runs[(runs["mode"] == mode) & (runs["threads"] == REFERENCE_THREADS)]
        for threads, color in ((4, "C0"), (1, "C1")):
            cur = runs[(runs["mode"] == mode) & (runs["threads"] == threads)]
            d = np.concatenate([(aligned(cur[cur["variant"] == t], ref[ref["variant"] == t])
                                 .eval("abs(y_pred_a - y_pred_b)")).to_numpy() for t in TIERS])
            ax.hist(np.log10(d[d > 0]), bins=60, alpha=0.6, color=color, label=f"{threads} vs 16 threads ({(d == 0).mean():.0%} identical)")
        ax.set_title(f"{mode} mode")
        ax.set_xlabel("log10 |prediction difference| (muB per cell), non-zero differences")
        ax.legend(fontsize=8)
    axes[0].set_ylabel("test predictions")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg, cfg7 = p7.dataset_cfg("v1.2"), p7.load_phase7_config()
    runs, phase7 = load_runs(), load_phase7(cfg7)
    seed_runs = load_runs(("refit",), with_seeds=True)
    seed_runs = seed_runs[seed_runs["threads"] == REFERENCE_THREADS]
    expected = 2 * len(THREADS) * len(SPLIT_IDS) * len(TIERS)
    if runs.groupby(["mode", "threads", "split_id", "variant"]).ngroups != expected:
        raise ValueError("incomplete thread-count runs")
    reproduction_check(runs, phase7).to_csv(OUT / "thread_reproduction_check.csv", index=False, encoding="utf-8")
    diffs = prediction_differences(runs)
    diffs.to_csv(OUT / "thread_prediction_differences.csv", index=False, encoding="utf-8")
    metrics_by_split(runs).to_csv(OUT / "thread_metrics_by_split.csv", index=False, encoding="utf-8")
    comp = tier_comparison(runs, cfg, cfg7)
    comp.to_csv(OUT / "thread_tier_comparison.csv", index=False, encoding="utf-8")
    seed_comp = tier_comparison(seed_runs, cfg, cfg7)
    seed_comp.to_csv(OUT / "seed_noise_tier_comparison.csv", index=False, encoding="utf-8")
    seed_diffs = seed_noise_reference(seed_runs)
    seed_diffs.to_csv(OUT / "seed_noise_prediction_differences.csv", index=False, encoding="utf-8")
    hgb = hgb_thread_check()
    hgb.to_csv(OUT / "hgb_thread_prediction_differences.csv", index=False, encoding="utf-8")
    hyperparameter_concordance(runs).to_csv(OUT / "thread_hyperparameter_concordance.csv", index=False, encoding="utf-8")
    phase7_reference(cfg7).to_csv(OUT / "phase7_reference_xgboost_ms.csv", index=False, encoding="utf-8")
    plot_differences(runs, OUT / "thread_prediction_differences.png")
    pd.set_option("display.width", 250, "display.max_columns", 40)
    print(pd.read_csv(OUT / "thread_reproduction_check.csv").round(6).to_string(index=False))
    print(diffs.round(5).to_string(index=False))
    print(comp[comp["from_variant"].eq("tier1") & comp["to_variant"].eq("tier3")].round(4).to_string(index=False))
    print(seed_comp[seed_comp["from_variant"].eq("tier1") & seed_comp["to_variant"].eq("tier3")].round(4).to_string(index=False))
    print(seed_diffs.groupby("variant")[["max_abs_diff", "mean_abs_diff", "mean_abs_diff_pct_of_mae"]].mean().round(4).to_string())
    print(hgb.round(6).to_string(index=False))
    print(pd.read_csv(OUT / "phase7_reference_xgboost_ms.csv").round(4).to_string(index=False))
    print(pd.read_csv(OUT / "thread_hyperparameter_concordance.csv").to_string(index=False))


if __name__ == "__main__":
    main()
