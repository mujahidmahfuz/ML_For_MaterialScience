"""Final check 2 (R7): matched Tier 1 -> Tier 2 -> Tier 3 ordering experiment on 10 formula-grouped splits (dataset v1.3).

Inputs : EDA/10_phase7_validation/v1.3/work/ordering/matched__<split>.parquet  (splits 0-4 from Phase 7 revision, 5-9 from this check;
         run_v13_ordering.py matched, identical estimators/grids/selection/n_jobs=16; the frozen split is reported separately, never pooled)
Outputs: final/outputs/check2_ordering/
  ordering_10split_results.csv        macro-F1, balanced accuracy, accuracy and per-class recall per split x tier x algorithm
  ordering_10split_paired.csv         paired tier differences (per split with CI; pooled mean-of-splits and pooled concatenated, formula bootstrap)
  ordering_10split_robustness.csv     across-split spread, sign counts and the existing stability verdict (pooled CI excludes 0 AND >=70% of splits)
  ordering_5_vs_10_split_comparison.csv   the Phase 7 five-split result next to the ten-split result
  ordering_class_recall_by_tier.csv   mean per-class recall per tier (AFM, FiM highlighted)
  ordering_reproduction_check.csv     point estimates recomputed here vs the stored Phase 7 five-split tables (must agree)
Usage (from EDA/src):  python ../../final/scripts/check2_ordering_10split.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parents[2] / "EDA" / "src"
sys.path.insert(0, str(SRC))

import phase7_validation as p7  # noqa: E402

FINAL = Path(__file__).resolve().parents[1]
OUT = FINAL / "outputs" / "check2_ordering"
PRIOR = FINAL / "work" / "prior_5split"
CLASSES = ["FM", "AFM", "FiM", "NM"]
K = len(CLASSES)
ALGS = ["linear", "gradient_boosting", "xgboost"]
TIERS = ["tier1", "tier2", "tier3"]
COMPARISONS = [("tier1", "tier2"), ("tier2", "tier3"), ("tier1", "tier3")]
METRICS = ["macro_f1", "balanced_accuracy", "recall_FM", "recall_AFM", "recall_FiM", "recall_NM"]
SPLITS = [str(i) for i in range(10)]
N_BOOT = 2000


# ------------------------------------------------------------------------------------------------ metrics from confusion counts
def metrics_from_confusion(conf: np.ndarray) -> dict[str, np.ndarray]:
    """conf: (..., K, K) weighted counts, rows = true class, columns = predicted. Same definitions as sklearn in phase6_models:
    macro-F1 over all four labels (0 for an empty class), balanced accuracy = mean recall over classes with support."""
    tp = np.diagonal(conf, axis1=-2, axis2=-1)
    support, predicted = conf.sum(axis=-1), conf.sum(axis=-2)
    denom_f1 = support + predicted
    f1 = np.divide(2 * tp, denom_f1, out=np.zeros_like(tp, dtype=float), where=denom_f1 > 0)
    recall = np.divide(tp, support, out=np.full_like(tp, np.nan, dtype=float), where=support > 0)
    out = {"macro_f1": f1.mean(axis=-1), "balanced_accuracy": np.nanmean(recall, axis=-1),
           "accuracy": tp.sum(axis=-1) / np.maximum(conf.sum(axis=(-2, -1)), 1e-12)}
    out.update({f"recall_{c}": recall[..., i] for i, c in enumerate(CLASSES)})
    return out


def formula_confusion(g: pd.DataFrame, code_of: dict, n_groups: int) -> np.ndarray:
    """(G, K, K) confusion counts per reduced_formula."""
    codes = g["reduced_formula"].map(code_of).to_numpy()
    flat = codes * K * K + g["y_true"].to_numpy(dtype=int) * K + g["y_pred"].to_numpy(dtype=int)
    return np.bincount(flat, minlength=n_groups * K * K).reshape(n_groups, K, K).astype(float)


def weighted(conf_g: np.ndarray, w: np.ndarray) -> np.ndarray:
    return np.einsum("bg,gij->bij", np.atleast_2d(w), conf_g)


def bootstrap_w(conf_members: list[np.ndarray], n_boot: int, seed: int) -> np.ndarray:
    """B x G formula-count matrix resampling only formulas present (in any of the given confusion arrays)."""
    present = np.flatnonzero(sum(c.sum(axis=(1, 2)) for c in conf_members) > 0)
    w = np.zeros((n_boot, conf_members[0].shape[0]))
    w[:, present] = p7.bootstrap_weights(len(present), n_boot, seed)
    return w


# ------------------------------------------------------------------------------------------------ data
def load_predictions(work: Path) -> pd.DataFrame:
    parts = [pd.read_parquet(work / f"matched__{s}.parquet") for s in SPLITS]
    out = pd.concat(parts, ignore_index=True)
    out["split_id"] = out["split_id"].astype(str)
    out = out[out["variant"].isin(TIERS) & out["algorithm"].isin(ALGS)]
    counts = out.groupby(["split_id", "variant", "algorithm"]).size().unstack(["variant", "algorithm"])
    if counts.shape != (len(SPLITS), len(TIERS) * len(ALGS)) or counts.isna().any().any():
        raise ValueError("matched ordering predictions are incomplete: every split needs all 3 tiers x 3 algorithms")
    if (counts.nunique(axis=1) != 1).any():
        raise ValueError("a split has different test-row counts across tiers/algorithms (not matched)")
    return out


def build_confusions(preds: pd.DataFrame) -> tuple[dict, dict, list[str]]:
    formulas = sorted(preds["reduced_formula"].unique())
    code_of = {f: i for i, f in enumerate(formulas)}
    conf = {key: formula_confusion(g, code_of, len(formulas)) for key, g in preds.groupby(["split_id", "variant", "algorithm"])}
    return conf, code_of, formulas


def results_table(preds: pd.DataFrame, conf: dict) -> pd.DataFrame:
    rows = []
    for (sid, variant, alg), c in conf.items():
        m = {k: float(v) for k, v in metrics_from_confusion(c.sum(axis=0)).items()}
        n_formulas = int((c.sum(axis=(1, 2)) > 0).sum())
        support = c.sum(axis=(0, 2))
        rows.append({"split_id": sid, "variant": variant, "algorithm": alg, "n_test": int(c.sum()), "n_test_formulas": n_formulas,
                     **{f"n_{cl}": int(support[i]) for i, cl in enumerate(CLASSES)}, **m})
    out = pd.DataFrame(rows)
    out["order"] = out["split_id"].astype(int)
    return out.sort_values(["order", "algorithm", "variant"]).drop(columns="order").reset_index(drop=True)


# ------------------------------------------------------------------------------------------------ paired inference
def improvement(draw_from: np.ndarray, draw_to: np.ndarray) -> np.ndarray:
    return draw_to - draw_from      # all metrics are higher-is-better


def metric_stack(conf_g: np.ndarray, w: np.ndarray) -> np.ndarray:
    """(len(METRICS), B) metric draws of one confusion array under formula weights w."""
    m = metrics_from_confusion(weighted(conf_g, w))
    return np.array([m[k] for k in METRICS])


def per_split_rows(conf: dict, cfg7: dict, n_g: int) -> list[dict]:
    boot_seed = cfg7["multisplit"]["bootstrap"]["seed"]
    unit = np.ones((1, n_g))
    rows = []
    for alg in ALGS:
        for v_from, v_to in COMPARISONS:
            for si, sid in enumerate(SPLITS):
                cf, ct = conf[(sid, v_from, alg)], conf[(sid, v_to, alg)]
                w = bootstrap_w([cf, ct], N_BOOT, boot_seed + 101 * (si + 1))
                d = improvement(metric_stack(cf, w), metric_stack(ct, w))
                pf, pt = metric_stack(cf, unit)[:, 0], metric_stack(ct, unit)[:, 0]
                for i, m in enumerate(METRICS):
                    lo, hi = np.nanquantile(d[i], [0.025, 0.975])
                    rows.append({"scope": "per_split", "split_id": sid, "algorithm": alg, "from_variant": v_from, "to_variant": v_to,
                                 "metric": m, "from_value": float(pf[i]), "to_value": float(pt[i]), "improvement": float(pt[i] - pf[i]),
                                 "ci_low": float(lo), "ci_high": float(hi)})
    return rows


def pooled_rows(conf: dict, cfg7: dict, n_g: int) -> list[dict]:
    """Pooled over the 10 splits with ONE set of formula draws shared by every tier (paired): the mean of per-split metrics and the
    metric of the concatenated test predictions."""
    boot_seed = cfg7["multisplit"]["bootstrap"]["seed"]
    unit = np.ones((1, n_g))
    rows = []
    for alg in ALGS:
        for v_from, v_to in COMPARISONS:
            w = bootstrap_w([conf[(s, v, alg)] for s in SPLITS for v in (v_from, v_to)], N_BOOT, boot_seed + 7)

            def sides(v: str) -> dict[str, tuple[np.ndarray, np.ndarray]]:
                total = sum(conf[(s, v, alg)] for s in SPLITS)
                return {"pooled_mean": (np.mean([metric_stack(conf[(s, v, alg)], w) for s in SPLITS], axis=0),
                                        np.mean([metric_stack(conf[(s, v, alg)], unit) for s in SPLITS], axis=0)[:, 0]),
                        "pooled_concat": (metric_stack(total, w), metric_stack(total, unit)[:, 0])}
            sf, st = sides(v_from), sides(v_to)
            for scope in ("pooled_mean", "pooled_concat"):
                d = improvement(sf[scope][0], st[scope][0])
                for i, m in enumerate(METRICS):
                    lo, hi = np.nanquantile(d[i], [0.025, 0.975])
                    rows.append({"scope": scope, "split_id": "all", "algorithm": alg, "from_variant": v_from, "to_variant": v_to,
                                 "metric": m, "from_value": float(sf[scope][1][i]), "to_value": float(st[scope][1][i]),
                                 "improvement": float(st[scope][1][i] - sf[scope][1][i]), "ci_low": float(lo), "ci_high": float(hi)})
    return rows


def paired_rows(conf: dict, cfg7: dict) -> pd.DataFrame:
    n_g = next(iter(conf.values())).shape[0]
    return pd.DataFrame(per_split_rows(conf, cfg7, n_g) + pooled_rows(conf, cfg7, n_g))


def robustness(paired: pd.DataFrame, min_fraction: float) -> pd.DataFrame:
    keys = ["algorithm", "from_variant", "to_variant", "metric"]
    pooled = {s: paired[paired["scope"] == s].set_index(keys) for s in ("pooled_mean", "pooled_concat")}
    rows = []
    for key, g in paired[paired["scope"] == "per_split"].groupby(keys):
        v = g["improvement"].to_numpy()
        lo_t, hi_t = p7.t_interval(v)
        row = dict(zip(keys, key))
        row.update({"n_splits": len(v), "mean_improvement": v.mean(), "median_improvement": float(np.median(v)), "sd": v.std(ddof=1),
                    "min": v.min(), "max": v.max(), "n_positive": int((v > 0).sum()), "fraction_positive": float((v > 0).mean()),
                    "sign_test_p": p7.sign_test_p(int((v > 0).sum()), len(v)), "t_interval_low": lo_t, "t_interval_high": hi_t})
        for scope, table in pooled.items():
            p = table.loc[key]
            row.update({f"{scope}_improvement": p["improvement"], f"{scope}_ci_low": p["ci_low"], f"{scope}_ci_high": p["ci_high"]})
            pos = p["ci_low"] > 0 and row["fraction_positive"] >= min_fraction
            neg = p["ci_high"] < 0 and row["fraction_positive"] <= 1 - min_fraction
            row[f"{scope}_verdict"] = "stable improvement" if pos else ("stable degradation" if neg else "not stable")
        rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------ checks and comparisons
def reproduction_check(results: pd.DataFrame) -> pd.DataFrame:
    prior = pd.read_csv(PRIOR / "ordering_v13_matched_results.csv")
    prior = prior[prior["split_id"].astype(str).isin(SPLITS[:5]) & prior["variant"].isin(TIERS)].assign(split_id=lambda d: d["split_id"].astype(str))
    mine = results[results["split_id"].isin(SPLITS[:5])]
    merged = mine.merge(prior, on=["split_id", "variant", "algorithm"], suffixes=("", "_prior"), validate="one_to_one")
    rows = [{"metric": m, "max_abs_difference": float((merged[m] - merged[f"{m}_prior"]).abs().max()), "n_compared": len(merged)}
            for m in ("macro_f1", "balanced_accuracy", "accuracy")]
    out = pd.DataFrame(rows)
    if (out["max_abs_difference"] > 1e-9).any():
        raise AssertionError(f"point estimates differ from the stored Phase 7 tables:\n{out}")
    return out


def five_vs_ten(rob: pd.DataFrame) -> pd.DataFrame:
    prior = pd.read_csv(PRIOR / "ordering_v13_matched_robustness.csv")
    prior = prior[[(f, t) in COMPARISONS for f, t in zip(prior["from_variant"], prior["to_variant"])]]
    prior = prior.rename(columns={"mean_improvement": "mean_5", "n_positive": "n_positive_5", "pooled_improvement": "pooled_5",
                                  "pooled_ci_low": "ci_low_5", "pooled_ci_high": "ci_high_5", "verdict": "verdict_5"})
    now = rob[rob["metric"] == "macro_f1"].rename(columns={"mean_improvement": "mean_10", "n_positive": "n_positive_10",
                                                           "pooled_concat_improvement": "pooled_10", "pooled_concat_ci_low": "ci_low_10",
                                                           "pooled_concat_ci_high": "ci_high_10", "pooled_concat_verdict": "verdict_10"})
    keep_now = ["algorithm", "from_variant", "to_variant", "mean_10", "n_positive_10", "pooled_10", "ci_low_10", "ci_high_10", "verdict_10"]
    keep_prior = ["algorithm", "from_variant", "to_variant", "mean_5", "n_positive_5", "pooled_5", "ci_low_5", "ci_high_5", "verdict_5"]
    return prior[keep_prior].merge(now[keep_now], on=["algorithm", "from_variant", "to_variant"])


def class_recall_by_tier(results: pd.DataFrame) -> pd.DataFrame:
    cols = [f"recall_{c}" for c in CLASSES] + ["macro_f1", "balanced_accuracy"]
    out = results.groupby(["algorithm", "variant"])[cols].agg(["mean", "std"])
    out.columns = [f"{a}_{b}" for a, b in out.columns]
    return out.reset_index()


def plot_differences(rob: pd.DataFrame, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
    for ax, metric in zip(axes, ("macro_f1", "recall_AFM", "recall_FiM")):
        d = rob[(rob["metric"] == metric) & (rob["from_variant"] == "tier1")]
        labels = [f"{r.algorithm.replace('_', ' ')}\n1->{r.to_variant[-1]}" for r in d.itertuples()]
        y = np.arange(len(d))[::-1]
        ax.errorbar(d["pooled_concat_improvement"], y, xerr=[d["pooled_concat_improvement"] - d["pooled_concat_ci_low"],
                                                             d["pooled_concat_ci_high"] - d["pooled_concat_improvement"]], fmt="o", capsize=3)
        ax.axvline(0, color="k", lw=0.8)
        ax.set_yticks(y, labels, fontsize=7)
        ax.set_title(metric, fontsize=9)
        ax.set_xlabel("improvement vs Tier 1 (95% formula-bootstrap CI)", fontsize=7)
    fig.suptitle("Matched ordering, 10 splits: deeper tier minus Tier 1", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg7 = p7.load_phase7_config()
    work = p7.output_dir(cfg7, "v1.3") / "work" / "ordering"
    preds = load_predictions(work)
    conf, _, formulas = build_confusions(preds)
    results = results_table(preds, conf)
    results.to_csv(OUT / "ordering_10split_results.csv", index=False, encoding="utf-8")
    reproduction_check(results).to_csv(OUT / "ordering_reproduction_check.csv", index=False, encoding="utf-8")
    paired = paired_rows(conf, cfg7)
    paired.to_csv(OUT / "ordering_10split_paired.csv", index=False, encoding="utf-8")
    rob = robustness(paired, cfg7["decision_gate"]["min_fraction_splits_positive"])
    rob.to_csv(OUT / "ordering_10split_robustness.csv", index=False, encoding="utf-8")
    five_vs_ten(rob).to_csv(OUT / "ordering_5_vs_10_split_comparison.csv", index=False, encoding="utf-8")
    class_recall_by_tier(results).to_csv(OUT / "ordering_class_recall_by_tier.csv", index=False, encoding="utf-8")
    plot_differences(rob, OUT / "ordering_tier_differences_forest.png")
    pd.set_option("display.width", 250, "display.max_columns", 40)
    print(f"matched ordering: {len(formulas)} distinct formulas in test partitions over 10 splits")
    print(rob[rob["metric"].isin(["macro_f1", "balanced_accuracy", "recall_AFM", "recall_FiM"])][
        ["algorithm", "from_variant", "to_variant", "metric", "mean_improvement", "sd", "n_positive", "pooled_concat_improvement",
         "pooled_concat_ci_low", "pooled_concat_ci_high", "pooled_concat_verdict", "pooled_mean_verdict"]].round(4).to_string(index=False))
    print(pd.read_csv(OUT / "ordering_5_vs_10_split_comparison.csv").round(4).to_string(index=False))


if __name__ == "__main__":
    main()
