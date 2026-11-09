"""Aggregate the v1.3 matched ordering experiment: per-split macro-F1, paired differences, pooled formula-bootstrap CIs, robustness.

Run from EDA/src after run_v13_ordering.py matched:  python agg_v13_ordering.py
Improvement = macro-F1(to) - macro-F1(from) (positive = the 'to' variant is better); frozen split is reported but not pooled.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import phase6_models as pm
import phase7_validation as p7

LABELS = [0, 1, 2, 3]
ALGS = ["linear", "gradient_boosting", "xgboost"]
COMPARISONS = [("tier1", "tier2"), ("tier2", "tier3"), ("tier1", "tier3"), ("tier2", "A_T2_plus_same_calculation_outputs"),
               ("tier3", "S_no_same_calculation_outputs"), ("tier2", "A_T2_plus_symmetry"), ("tier3", "S_no_symmetry")]
N_BOOT = 500


def metric_fn(y, p, w):
    return pm.classification_metrics(y, p, LABELS, w)


def load(out) -> pd.DataFrame:
    files = sorted((out / "work" / "ordering").glob("matched__*.parquet"))
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def per_split(preds: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (sid, v, a), g in preds.groupby(["split_id", "variant", "algorithm"]):
        m = pm.classification_metrics(g["y_true"].to_numpy(), g["y_pred"].to_numpy(), LABELS)
        rows.append({"split_id": sid, "variant": v, "algorithm": a, "n_test": len(g), "n_test_formulas": g["reduced_formula"].nunique(), **m})
    return pd.DataFrame(rows)


def pair_stat(pf: pd.DataFrame, pt: pd.DataFrame, seed: int) -> tuple[float, float, float]:
    """(point improvement, CI low, CI high) of macro-F1(to) - macro-F1(from) under a paired formula bootstrap."""
    y, g = pf["y_true"].to_numpy(), pf["reduced_formula"].to_numpy()
    preds = {"f": pf["y_pred"].to_numpy(), "t": pt["y_pred"].to_numpy()}
    _, samples = pm.paired_group_bootstrap(y, preds, g, metric_fn, ["macro_f1"], N_BOOT, seed)
    d = np.array(samples["t"]["macro_f1"]) - np.array(samples["f"]["macro_f1"])
    point = metric_fn(y, preds["t"], None)["macro_f1"] - metric_fn(y, preds["f"], None)["macro_f1"]
    return point, float(np.quantile(d, 0.025)), float(np.quantile(d, 0.975))


def pair_rows(preds: pd.DataFrame, scope: str, seed: int) -> list[dict]:
    rows = []
    groups = [(sid, part) for sid, part in preds.groupby("split_id")] if scope == "per_split" else [("all", preds)]
    for sid, part in groups:
        for a in ALGS:
            for v_from, v_to in COMPARISONS:
                pf = part[(part["variant"] == v_from) & (part["algorithm"] == a)].sort_values(["split_id", "material_id"])
                pt = part[(part["variant"] == v_to) & (part["algorithm"] == a)].sort_values(["split_id", "material_id"])
                if pf.empty or pt.empty:
                    continue
                point, lo, hi = pair_stat(pf, pt, seed if scope == "per_split" else seed + 7)
                rows.append({"scope": scope, "split_id": sid, "algorithm": a, "from_variant": v_from, "to_variant": v_to,
                             "improvement": point, "ci_low": lo, "ci_high": hi})
    return rows


def robustness(paired: pd.DataFrame, min_fraction: float) -> pd.DataFrame:
    keys = ["algorithm", "from_variant", "to_variant"]
    pooled = paired[paired["scope"] == "pooled_concat"].set_index(keys)
    rows = []
    for key, g in paired[paired["scope"] == "per_split"].groupby(keys):
        v = g["improvement"].to_numpy()
        lo_t, hi_t = p7.t_interval(v)
        row = dict(zip(keys, key))
        row.update({"n_splits": len(v), "mean_improvement": v.mean(), "median_improvement": float(np.median(v)), "min": v.min(), "max": v.max(),
                    "n_positive": int((v > 0).sum()), "fraction_positive": float((v > 0).mean()), "t_interval_low": lo_t, "t_interval_high": hi_t})
        if key in pooled.index:
            p = pooled.loc[key]
            row.update({"pooled_improvement": p["improvement"], "pooled_ci_low": p["ci_low"], "pooled_ci_high": p["ci_high"]})
            row["verdict"] = ("stable improvement" if p["ci_low"] > 0 and row["fraction_positive"] >= min_fraction else
                              "stable degradation" if p["ci_high"] < 0 and row["fraction_positive"] <= 1 - min_fraction else "not stable")
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    cfg7 = p7.load_phase7_config()
    out = p7.output_dir(cfg7, "v1.3")
    preds = load(out)
    per_split(preds).to_csv(out / "ordering_v13_matched_results.csv", index=False, encoding="utf-8")
    seed = cfg7["multisplit"]["bootstrap"]["seed"]
    random_preds = preds[preds["split_id"].astype(str) != "frozen"]
    paired = pd.DataFrame(pair_rows(preds, "per_split", seed) + pair_rows(random_preds, "pooled_concat", seed))
    paired.to_csv(out / "ordering_v13_matched_paired_differences.csv", index=False, encoding="utf-8")
    rob = robustness(paired[paired["split_id"].astype(str) != "frozen"], cfg7["decision_gate"]["min_fraction_splits_positive"])
    rob.to_csv(out / "ordering_v13_matched_robustness.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 220)
    print(rob.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
