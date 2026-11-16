"""A14 (round-3 review R3-1, R3-2): pooled Tier 1 -> Tier 3 estimate across the three algorithms, and the Holm family with the clipped ridge member.

Why: the per-algorithm Curie contrasts are individually underpowered (minimum detectable effect 27-56 K against a declared margin of 10 K).
The three algorithms are scored on the same test rows of the same ten splits, so their improvements are correlated; the pooled contrast is
therefore the per-split MEAN of the three algorithm improvements, and its uncertainty is taken from the split-to-split spread of that mean
(Nadeau-Bengio correction as in A1) and from one formula bootstrap whose draws are shared by all algorithms. No model is refitted: the inputs
are the saved per-split test predictions that A1 reads, through the A1 helper functions (same rows, same rule, same seeds convention).

Algorithms pooled: Curie = linear_clip (clipped ridge; the unclipped ridge is numerically unstable), gradient_boosting, xgboost_seedmean;
moment per cell = linear, gradient_boosting, xgboost_seedmean; ordering = linear, gradient_boosting, xgboost (single realisation, as in A1).

Holm family (PLAN.md A1, as planned): the 9 Tier 1 -> 3 contrasts with the CLIPPED Curie ridge member; adjusted p-values are computed from the
corrected-t p-values already saved by A1 (final/revision/outputs/a1/tier_inference.csv).

Outputs: final/revision/outputs/a14_pooled/pooled_tier13.csv, holm_clipped_family.csv
Run (repository root, foreground):  python final/revision/scripts/a14_pooled_tier_inference.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a1_tier_inference as a1  # noqa: E402  (helpers: predictions loaders, metrics, bootstrap weights, Holm)

OUT = a1.ROOT / "final/revision/outputs/a14_pooled"
POOL = {
    "curie": ("regression", ["linear_clip", "gradient_boosting", "xgboost_seedmean"]),
    "ms_moment": ("regression", ["linear", "gradient_boosting", "xgboost_seedmean"]),
    "ordering": ("classification", ["linear", "gradient_boosting", "xgboost"]),
}


def per_algorithm_arrays(df: pd.DataFrame, alg: str, task: str, counts: np.ndarray, formulas: pd.Index):
    """Per-split improvement (Tier 1 -> Tier 3) and its bootstrap replicates, using the SHARED formula draws `counts`."""
    sub = df[df["algorithm"] == alg]
    per_split, boots, n_test = [], [], []
    for s in a1.SPLITS:
        a = sub[(sub["split_id"] == s) & (sub["variant"] == "tier1")].set_index("material_id")
        b = sub[(sub["split_id"] == s) & (sub["variant"] == "tier3")].set_index("material_id")
        common = a.index.intersection(b.index)
        if len(common) != len(a) or len(common) != len(b):
            raise ValueError(f"{alg} split {s}: tiers scored on different rows")
        a, b = a.loc[common], b.loc[common]
        n_test.append(len(common))
        per_split.append(a1.improvement(task, a1.metric_point(a, task), a1.metric_point(b, task)))
        w = counts[:, formulas.get_indexer(a["reduced_formula"])].astype(float)
        y, ya, yb = a["y_true"].to_numpy(), a["y_pred"].to_numpy(), b["y_pred"].to_numpy()
        if task == "classification":
            y, ya, yb = y.astype(int), ya.astype(int), yb.astype(int)
        boots.append(a1.improvement(task, a1.weighted_metric(y, ya, w, task), a1.weighted_metric(y, yb, w, task)))
    return np.array(per_split), np.mean(np.vstack(boots), axis=0), n_test


def summarize(label: str, target: str, d: np.ndarray, boot: np.ndarray, n_test: list[int], n_all: int, metric: str) -> dict:
    J, mean = len(d), float(d.mean())
    ratio = float(np.mean(n_test)) / (n_all - float(np.mean(n_test)))
    se = float(d.std(ddof=1) * np.sqrt(1.0 / J + ratio))
    tcrit = stats.t.ppf(0.975, J - 1)
    p = float(2 * stats.t.sf(abs(mean) / se, J - 1)) if se > 0 else 0.0
    lo_b, hi_b = np.quantile(boot, [0.025, 0.975])
    frac = float(max((d > 0).mean(), (d < 0).mean()))
    margin = a1.MARGIN[target]
    return {"target": target, "metric": metric, "pooled_over": label, "mean_improvement": mean,
            "nb_ci_low": mean - tcrit * se, "nb_ci_high": mean + tcrit * se, "nb_p": p,
            "boot_ci_low": float(lo_b), "boot_ci_high": float(hi_b), "n_positive": int((d > 0).sum()), "n_splits": J,
            "fraction_same_sign": frac, "mde80": float((tcrit + stats.t.ppf(0.80, J - 1)) * se),
            "practical_margin": margin,
            "excludes_margin_gain": bool(mean + tcrit * se < margin and hi_b < margin)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for target, (task, algs) in POOL.items():
        df, info = a1.ordering_predictions() if target == "ordering" else a1.regression_predictions(target)
        n_all = a1.n_total(target)
        formulas = pd.Index(sorted(df["reduced_formula"].unique()))
        rng = np.random.default_rng(a1.SEED + 7000)
        counts = np.vstack([np.bincount(rng.integers(0, len(formulas), len(formulas)), minlength=len(formulas)) for _ in range(a1.N_BOOT)])
        arrays = {alg: per_algorithm_arrays(df, alg, task, counts, formulas) for alg in algs}
        n_test = arrays[algs[0]][2]
        metric = "mae" if task == "regression" else "macro_f1"
        d_pool = np.mean([arrays[alg][0] for alg in algs], axis=0)
        b_pool = np.mean([arrays[alg][1] for alg in algs], axis=0)
        rows.append(summarize("+".join(algs), target, d_pool, b_pool, n_test, n_all, metric) | info)
        for alg in algs:  # same shared-draw bootstrap per algorithm, for comparison with A1
            rows.append(summarize(alg, target, arrays[alg][0], arrays[alg][1], n_test, n_all, metric) | info)
        print(f"{target}: done", flush=True)
    pooled = pd.DataFrame(rows)
    pooled.to_csv(OUT / "pooled_tier13.csv", index=False)

    a1_tab = pd.read_csv(a1.ROOT / "final/revision/outputs/a1/tier_inference.csv")
    fam = a1_tab[(a1_tab["from"] == "tier1") & (a1_tab["to"] == "tier3")].copy()
    keep = {("curie", "linear_clip"), ("curie", "gradient_boosting"), ("curie", "xgboost_seedmean"),
            ("ms_moment", "linear"), ("ms_moment", "gradient_boosting"), ("ms_moment", "xgboost_seedmean"),
            ("ordering", "linear"), ("ordering", "gradient_boosting"), ("ordering", "xgboost")}
    fam = fam[[(t, a) in keep for t, a in zip(fam["target"], fam["algorithm"])]].copy()
    if len(fam) != 9:
        raise SystemExit(f"Holm family has {len(fam)} members, expected 9")
    fam["holm_p_clipped_family"] = a1.holm(fam["nb_p"].to_numpy())
    fam[["target", "algorithm", "mean_improvement", "nb_ci_low", "nb_ci_high", "nb_p", "holm_p", "holm_p_clipped_family", "verdict"]].to_csv(
        OUT / "holm_clipped_family.csv", index=False)
    pd.set_option("display.width", 220)
    print(pooled[["target", "pooled_over", "mean_improvement", "nb_ci_low", "nb_ci_high", "boot_ci_low", "boot_ci_high", "n_positive", "mde80", "excludes_margin_gain"]]
          .round(4).to_string(index=False))
    print(fam[["target", "algorithm", "nb_p", "holm_p", "holm_p_clipped_family"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
