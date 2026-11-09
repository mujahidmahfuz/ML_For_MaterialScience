"""Final check 1 (R6): statistical precision of the matched Curie Tier 1 -> Tier 2 -> Tier 3 comparison, on dataset v1.3.

Reads the saved Phase 7 v1.3 per-split test predictions (10 prespecified formula-grouped splits; nothing is refit) and adds:
  * distinct formulas / Kish effective sample size of every train, validation and test partition,
  * paired formula-level bootstrap effects (same resampling draws for both tiers), pooled over the 10 splits, with the per-split spread,
  * realised design effect (formula clustering) and the minimum improvement the data could have detected,
  * equivalence / non-superiority assessment against a margin in kelvin fixed in MARGINS_K below,
  * the C5 distinction: matched-population overlap with / without rule C5, plus the full-population Tier 1 -> Tier 2 results of both.

Reproduction check: the pooled-mean MAE improvement is recomputed with the Phase 7 bootstrap seed and must equal
10_phase7_validation/v1.3/phase7_robustness_summary.csv (asserted at run time).

Usage (from EDA/src, OMP_NUM_THREADS unset):  python ../../final/scripts/check1_curie_inference.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parents[2] / "EDA" / "src"
sys.path.insert(0, str(SRC))

import phase6_common as pc  # noqa: E402
import phase7_aggregate as agg  # noqa: E402
import phase7_validation as p7  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "outputs" / "check1_curie"
VERSION = "v1.3"
ALGORITHMS = ["linear", "gradient_boosting", "xgboost"]
COMPARISONS = [("tier1", "tier2"), ("tier2", "tier3"), ("tier1", "tier3")]
# Equivalence margin (kelvin). PRIMARY_MARGIN_K is the prespecified decision margin; the others are sensitivity bounds.
# Rationale (see CHECK1 report): repeated measurements of one formula differ by a median range of 7.8 K in the v1.3 population
# (label-noise floor), so differences below ~10 K cannot be resolved against the labels; 10 K is also ~5% of the matched Tier 1 MAE (~205 K).
MARGINS_K = (5.0, 10.0, 20.0)
PRIMARY_MARGIN_K = 10.0
POWER_Z = 1.96 + 0.8416      # two-sided alpha 0.05, 80% power
UNSTABLE = {"linear"}        # Ridge Tier 3 predictions numerically explode on this population (Phase 7 finding)


def partition_table(pop: agg.Population, work_dir: Path) -> pd.DataFrame:
    """Rows, distinct formulas and Kish effective sample size (sum n_f)^2 / sum n_f^2 for every split x partition."""
    rows = []
    for path in sorted(work_dir.glob("labels__*.parquet")):
        sid = path.stem.split("__")[1]
        frame = pop.frame.merge(pd.read_parquet(path), on="material_id", validate="one_to_one")
        for part in p7.SPLIT_NAMES:
            sizes = frame.loc[frame["split"] == part, "reduced_formula"].value_counts().to_numpy(dtype=float)
            rows.append({"split_id": sid, "partition": part, "n_rows": int(sizes.sum()), "n_distinct_formulas": len(sizes),
                         "rows_per_formula": sizes.sum() / len(sizes), "kish_effective_n": sizes.sum() ** 2 / (sizes ** 2).sum(),
                         "largest_formula_share_pct": 100 * sizes.max() / sizes.sum()})
    out = pd.DataFrame(rows)
    out["order"] = out["split_id"].map(agg.split_order)
    return out.sort_values(["order", "partition"]).drop(columns="order").reset_index(drop=True)


def partition_summary(table: pd.DataFrame, pop: agg.Population) -> pd.DataFrame:
    random = table[table["split_id"] != "frozen"]
    summary = random.groupby("partition")[["n_rows", "n_distinct_formulas", "kish_effective_n", "largest_formula_share_pct"]].agg(["mean", "min", "max"])
    summary.columns = ["_".join(c) for c in summary.columns]
    summary = summary.reset_index()
    summary.insert(1, "population_rows", len(pop.frame))
    summary.insert(2, "population_formulas", len(pop.formulas))
    return summary


def pooled_weights(stats: dict, n_formulas: int, cfg7: dict) -> np.ndarray:
    boot = cfg7["multisplit"]["bootstrap"]
    members = [v for k, v in stats.items() if k[0] != "frozen"]
    cols = np.flatnonzero(sum(v["n"] for v in members) > 0)
    w = np.zeros((boot["n_resamples"], n_formulas))
    w[:, cols] = p7.bootstrap_weights(len(cols), boot["n_resamples"], boot["seed"] + 7)
    return w


def design_effect(preds: pd.DataFrame, pop: agg.Population, alg: str, v_from: str, v_to: str, cfg7: dict) -> dict:
    """Mean over splits of (formula-bootstrap variance / naive row-independence variance) of the paired absolute-error difference."""
    boot = cfg7["multisplit"]["bootstrap"]
    effects, n_eff, n_test = [], [], []
    for si, sid in enumerate(sorted(preds["split_id"].unique(), key=agg.split_order)):
        if sid == "frozen":
            continue
        a = preds[(preds["split_id"] == sid) & (preds["variant"] == v_from) & (preds["algorithm"] == alg)].sort_values("material_id")
        b = preds[(preds["split_id"] == sid) & (preds["variant"] == v_to) & (preds["algorithm"] == alg)].sort_values("material_id")
        d = (b["y_pred"] - b["y_true"]).abs().to_numpy() - (a["y_pred"] - a["y_true"]).abs().to_numpy()   # >0: deeper tier worse
        codes = pop.codes(a["reduced_formula"])
        n_g = len(pop.formulas)
        s_f, n_f = np.bincount(codes, weights=d, minlength=n_g), np.bincount(codes, minlength=n_g).astype(float)
        cols = np.flatnonzero(n_f > 0)
        w = np.zeros((boot["n_resamples"], n_g))
        w[:, cols] = p7.bootstrap_weights(len(cols), boot["n_resamples"], boot["seed"] + 101 * (si + 1))
        var_boot = np.var((w @ s_f) / (w @ n_f), ddof=1)
        var_naive = np.var(d, ddof=1) / len(d)
        effects.append(var_boot / var_naive)
        n_test.append(len(d))
        n_eff.append(len(d) * var_naive / var_boot)
    return {"design_effect": float(np.mean(effects)), "mean_test_rows": float(np.mean(n_test)), "effective_independent_rows": float(np.mean(n_eff))}


def margin_verdict(lo: float, hi: float, margin: float) -> str:
    if lo > -margin and hi < margin:
        return "equivalent (|difference| < margin)"
    if hi < margin:
        return "no meaningful improvement (non-superior); a worsening larger than the margin is not excluded"
    if lo >= margin:
        return "meaningful improvement"
    return "inconclusive"


def inference_rows(stats: dict, preds: pd.DataFrame, pop: agg.Population, cfg7: dict, analysis: str, algorithms: list[str]) -> list[dict]:
    boot = cfg7["multisplit"]["bootstrap"]
    sids = sorted({k[0] for k in stats if k[0] != "frozen"}, key=agg.split_order)
    per_split = pd.DataFrame(agg.per_split_pairs(stats, pop, cfg7, analysis, COMPARISONS, algorithms, sids))
    w = pooled_weights(stats, len(pop.formulas), cfg7)
    rows = []
    for alg in algorithms:
        for v_from, v_to in COMPARISONS:
            lists = {"from": [stats[(s, v_from, alg)] for s in sids], "to": [stats[(s, v_to, alg)] for s in sids]}
            de = design_effect(preds, pop, alg, v_from, v_to, cfg7)
            for metric in agg.METRICS:
                imp, draws, m_from, m_to = agg.pooled_draws(lists, metric, w)["pooled_mean"]
                lo, hi = p7.ci(draws, boot["ci"])
                lo90, hi90 = p7.ci(draws, 0.90)
                sel = per_split[(per_split["algorithm"] == alg) & (per_split["from_variant"] == v_from)
                                & (per_split["to_variant"] == v_to) & (per_split["metric"] == metric)]["improvement"].to_numpy()
                se = float(np.std(draws, ddof=1))
                row = {"analysis": analysis, "algorithm": alg, "from_variant": v_from, "to_variant": v_to, "metric": metric,
                       "from_value": m_from, "to_value": m_to, "improvement": imp, "ci95_low": lo, "ci95_high": hi,
                       "ci90_low": lo90, "ci90_high": hi90, "bootstrap_se": se,
                       "min_detectable_improvement_80pct_power": POWER_Z * se,
                       "n_splits": len(sel), "split_mean": sel.mean(), "split_sd": sel.std(ddof=1), "split_min": sel.min(),
                       "split_max": sel.max(), "n_splits_improved": int((sel > 0).sum()),
                       "sign_test_p": p7.sign_test_p(int((sel > 0).sum()), len(sel)),
                       "numerically_unstable_model": alg in UNSTABLE, **de}
                if metric in ("mae", "mae_formula_macro"):
                    for k in MARGINS_K:
                        row[f"verdict_margin_{k:g}K"] = margin_verdict(lo, hi, k)
                        row[f"tost90_equivalent_margin_{k:g}K"] = bool(lo90 > -k and hi90 < k)
                rows.append(row)
    return rows


def reproduce_phase7(inference: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    """The primary pooled-mean MAE rows must equal the stored Phase 7 v1.3 robustness summary."""
    ref = pd.read_csv(out_dir / "phase7_robustness_summary.csv")
    ref = ref[(ref["analysis"] == "primary_matched") & (ref["metric"] == "mae")].set_index(["algorithm", "from_variant", "to_variant"])
    mine = inference[(inference["analysis"] == "primary_matched") & (inference["metric"] == "mae")].set_index(["algorithm", "from_variant", "to_variant"])
    comp = pd.DataFrame({"final_check_improvement": mine["improvement"], "phase7_improvement": ref["pooled_mean_improvement"],
                         "final_check_ci_low": mine["ci95_low"], "phase7_ci_low": ref["pooled_mean_ci_low"],
                         "final_check_ci_high": mine["ci95_high"], "phase7_ci_high": ref["pooled_mean_ci_high"]}).dropna()
    comp["max_abs_difference"] = comp.filter(like="final_check").sub(comp.filter(like="phase7").to_numpy()).abs().max(axis=1)
    if not (comp["max_abs_difference"] < 1e-6).all():
        raise AssertionError(f"Phase 7 pooled MAE estimates not reproduced:\n{comp}")
    return comp.reset_index()


def c5_overlap(cfg: dict) -> pd.DataFrame:
    """Matched (Tier 3 physics-complete) population with and without rule C5."""
    import run_v13_curie_c5_sensitivity as c5
    sens, prim = c5.sensitivity_ids()
    repo = pc.load_feature_repository(cfg, columns=["material_id"] + cfg["predictor_rules"]["physics_bundle"])
    physics = set(repo.loc[pc.physics_complete_mask(cfg, repo), "material_id"])
    matched = set(pd.read_csv(p7.split_dir(VERSION) / "matched_split_curie.csv", usecols=["material_id"])["material_id"])
    return pd.DataFrame([
        {"population": "full v1.3 Curie (rule C5 applied)", "rows": len(prim)},
        {"population": "full sensitivity Curie (rule C5 not applied)", "rows": len(sens)},
        {"population": "rows removed only by C5", "rows": len(sens - prim)},
        {"population": "primary matched population (Tier 3 physics-complete)", "rows": len(matched)},
        {"population": "matched population without rule C5", "rows": len(sens & physics)},
        {"population": "C5-only rows that are physics-complete (added to matched set)", "rows": len((sens - prim) & physics)},
        {"population": "primary matched set identical to the no-C5 matched set", "rows": int(matched == (sens & physics))}])


def full_population_tier2(out_dir: Path) -> pd.DataFrame:
    """Full-population Tier 1 -> Tier 2 (single frozen split, Phase 7 v1.3 files), primary vs without C5, against each margin."""
    frames = []
    for label, path in (("primary (C5 applied), N=29,740", out_dir / "v13_full_curie_tier2_deltas.csv"),
                        ("sensitivity (no C5), N=30,059", out_dir / "c5_sensitivity" / "c5_tier2_deltas.csv")):
        d = pd.read_csv(path)
        d = d[d["metric"] == "mae"].assign(population=label)
        for k in MARGINS_K:
            d[f"verdict_margin_{k:g}K"] = [margin_verdict(lo, hi, k) for lo, hi in zip(d["ci_low"], d["ci_high"])]
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def forest_plot(inference: pd.DataFrame, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = inference[(inference["analysis"] == "primary_matched") & (inference["metric"] == "mae") & (~inference["numerically_unstable_model"])]
    labels = [f"{r.algorithm.replace('_', ' ')}: {r.from_variant[-1]}->{r.to_variant[-1]}" for r in d.itertuples()]
    y = np.arange(len(d))[::-1]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.axvspan(-PRIMARY_MARGIN_K, PRIMARY_MARGIN_K, color="0.88", label=f"equivalence margin +/-{PRIMARY_MARGIN_K:g} K")
    ax.errorbar(d["improvement"], y, xerr=[d["improvement"] - d["ci95_low"], d["ci95_high"] - d["improvement"]], fmt="o", color="C0", capsize=3)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_yticks(y, labels)
    ax.set_xlabel("MAE improvement (K); positive = deeper tier better; 95% formula-bootstrap CI")
    ax.set_title("Matched Curie (v1.3, 4,602 rows, 10 splits): paired tier differences")
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg, cfg7 = p7.dataset_cfg(VERSION), p7.load_phase7_config()
    out_dir = p7.output_dir(cfg7, VERSION)
    work_dir = out_dir / "work" / "curie"
    pop = agg.Population.load(cfg, cfg7, "curie", VERSION)
    table = partition_table(pop, work_dir)
    table.to_csv(OUT / "curie_partition_formula_counts.csv", index=False, encoding="utf-8")
    partition_summary(table, pop).to_csv(OUT / "curie_effective_sample_size_summary.csv", index=False, encoding="utf-8")

    main_preds, diag_preds = agg.load_kind(work_dir, "main"), agg.load_kind(work_dir, "diag")
    rows = inference_rows(agg.keyed_stats(main_preds, pop), main_preds, pop, cfg7, "primary_matched", ALGORITHMS)
    rows += inference_rows(agg.keyed_stats(diag_preds, pop), diag_preds, pop, cfg7, "diagnostic_linear_clip", [p7.LINEAR_CLIP])
    inference = pd.DataFrame(rows)
    inference.to_csv(OUT / "curie_inference_table.csv", index=False, encoding="utf-8")
    reproduce_phase7(inference, out_dir).to_csv(OUT / "curie_phase7_reproduction_check.csv", index=False, encoding="utf-8")

    c5_overlap(cfg).to_csv(OUT / "curie_c5_population_overlap.csv", index=False, encoding="utf-8")
    full_population_tier2(out_dir).to_csv(OUT / "curie_c5_full_population_tier2_equivalence.csv", index=False, encoding="utf-8")
    forest_plot(inference, OUT / "curie_tier_differences_forest.png")

    pd.set_option("display.width", 250, "display.max_columns", 40)
    show = inference[(inference["metric"] == "mae")].drop(columns=[c for c in inference.columns if c.startswith("tost90")])
    print(partition_summary(table, pop).round(1).to_string(index=False))
    print(show[["analysis", "algorithm", "from_variant", "to_variant", "from_value", "improvement", "ci95_low", "ci95_high", "split_sd",
                "n_splits_improved", "design_effect", "effective_independent_rows", "min_detectable_improvement_80pct_power",
                f"verdict_margin_{PRIMARY_MARGIN_K:g}K"]].round(2).to_string(index=False))
    print(pd.read_csv(OUT / "curie_c5_population_overlap.csv").to_string(index=False))


if __name__ == "__main__":
    main()
