"""Phase 8 repeated-split coverage check: do the UQ results of the single frozen split hold over the 10 Phase 7 split seeds?

For every split i (random_group_split with the Phase 7 seeds, class-code / target stratification): calibration = 20% of the split's TRAIN formulas
(seed + 8000 + i), proper-train = the rest, test = the split's test partition. Regression (curie v1.3, ms_moment v1.2): split / normalized /
CQR intervals at 90%; classification (ordering v1.3): marginal and class-conditional LAC sets on prior-corrected + temperature-scaled probabilities.
Rows are written per split and group; the summary applies the prespecified Phase 8 criteria (marginal within +-2 points; subgroup flagged when
>5 points below nominal with >=30 formulas) as fractions of splits.
Usage (from EDA/src, OMP_NUM_THREADS unset):  python run_phase8_uq_repeated.py <curie|ms_moment|ordering>
Outputs: EDA/11_phase8_xai_uq/repeated/<target>/repeated_split_coverage.csv and repeated_split_summary.csv
"""
from __future__ import annotations

import ast
import sys

import numpy as np
import pandas as pd

import phase6_common as pc
import phase6_models as pm
import phase7_validation as p7
import phase8_uq as uq
import run_phase8_ordering_uq as ro
import run_phase8_regression_uq as ru

N_SPLITS, NOMINAL = 10, 1 - ru.ALPHA
OUT = pc.EDA_ROOT / "11_phase8_xai_uq" / "repeated"
REGRESSION_GROUPS = ("family:Oxide", "family:Rare Earth", "family:Transition Metal", "family:Intermetallic", "predicted_value:highest_third", "difficulty_decile:10")


def split_roles(frame: pd.DataFrame, y: np.ndarray, cfg7: dict, seed: int, split_id: int) -> np.ndarray:
    probe = pd.DataFrame({"reduced_formula": frame["reduced_formula"].to_numpy(), "value": y.astype(float)})
    labels = p7.split_labels_for(probe, cfg7, split_id)
    p7.assert_formula_disjoint(frame["reduced_formula"], labels)
    train = labels == "train"
    cal_in_train = uq.grouped_calibration_split(frame.loc[train, "reduced_formula"].to_numpy(), ru.CAL_FRACTION, seed + 8000 + split_id)
    idx = np.flatnonzero(train)
    role = np.full(len(frame), "unused", dtype=object)
    role[idx[~cal_in_train]], role[idx[cal_in_train]] = "proper_train", "calibration"
    role[labels == "test"] = "test"
    return role


def regression_split(target, split_id, cfg, cfg7, frame, feats, y, params, groups) -> list[dict]:
    role = split_roles(frame, y, cfg7, cfg["random_seed"], split_id)
    pred = ru.build_intervals(frame, feats, y, role, params, cfg["random_seed"])
    te = role == "test"
    y_te, y_cal = y[te], y[role == "calibration"]
    meta = frame.loc[te].reset_index(drop=True)
    masks = {"all": np.ones(len(y_te), dtype=bool), **ru.subgroup_masks(meta, pred, groups)}
    masks = {k: v for k, v in masks.items() if k == "all" or k in REGRESSION_GROUPS or k.startswith("source:")}
    rows = []
    for method, (lo, hi) in ru.method_intervals(pred, y_cal, ru.ALPHA).items():
        cov = uq.covered_mask(y_te, lo, hi)
        for name, m in masks.items():
            if m.sum():
                rows.append({"target": target, "split_id": split_id, "method": method, "group": name, "n_rows": int(m.sum()),
                             "n_formulas": int(meta.loc[m, "reduced_formula"].nunique()), "coverage": float(cov[m].mean()), "mean_width": float(np.mean((hi - lo)[m]))})
    print(f"{target} split {split_id}: " + ", ".join(f"{r['method'][:5]} {r['coverage']:.3f}" for r in rows if r["group"] == "all"), flush=True)
    return rows


def ordering_split(split_id, cfg, cfg7, frame, feats, y, params) -> list[dict]:
    role = split_roles(frame, y, cfg7, cfg["random_seed"], split_id)
    tr, cal, te = role == "proper_train", role == "calibration", role == "test"
    model = pm.fit(pm.build_estimator("xgboost", "classification", params, cfg["random_seed"]), "xgboost", "classification", frame.loc[tr, feats], y[tr])
    freq = np.bincount(y[tr], minlength=len(ro.CLASSES)) / tr.sum()
    p_cal, p_te = ro.prior_correct(model.predict_proba(frame.loc[cal, feats]), freq), ro.prior_correct(model.predict_proba(frame.loc[te, feats]), freq)
    temp = uq.fit_temperature(p_cal, y[cal])
    p_cal, p_te = uq.apply_temperature(p_cal, temp), uq.apply_temperature(p_te, temp)
    sets, _ = ro.conformal_variants(p_cal, y[cal], p_te, y[te])
    n_formulas = int(frame.loc[te, "reduced_formula"].nunique())
    rows = []
    for method, s in sets.items():
        m = ro.set_metrics(method, s, y[te])
        rows.append({"target": "ordering", "split_id": split_id, "method": method, "group": "all", "n_rows": int(te.sum()), "n_formulas": n_formulas,
                     "coverage": m["coverage"], "mean_width": m["mean_set_size"], **{f"coverage_{c}": m[f"coverage_{c}"] for c in ro.CLASSES}, "temperature": temp})
    print(f"ordering split {split_id}: " + ", ".join(f"{r['method'][:8]} {r['coverage']:.3f} (AFM {r['coverage_AFM']:.2f} FiM {r['coverage_FiM']:.2f})" for r in rows), flush=True)
    return rows


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (method, group), g in df.groupby(["method", "group"]):
        under = (g["coverage"] < NOMINAL - uq.UNDER_COVERAGE_TOLERANCE) & (g["n_formulas"] >= uq.MIN_FORMULAS_FOR_FLAG)
        rows.append({"method": method, "group": group, "n_splits": len(g), "mean_coverage": g["coverage"].mean(), "sd_coverage": g["coverage"].std(),
                     "min_coverage": g["coverage"].min(), "max_coverage": g["coverage"].max(), "mean_width": g["mean_width"].mean(),
                     "fraction_splits_within_2pt": float((abs(g["coverage"] - NOMINAL) <= 0.02).mean()), "fraction_splits_under_covered": float(under.mean()),
                     "median_formulas": float(g["n_formulas"].median())})
    return pd.DataFrame(rows)


def load_ordering() -> tuple[dict, pd.DataFrame, list[str], np.ndarray, dict]:
    cfg = p7.dataset_cfg(ro.VERSION)
    frame, feats = pm.load_modeling_frame(cfg, "ordering", "tier1", p7.split_dir(ro.VERSION) / "split_ordering.csv")
    frame = frame.reset_index(drop=True)
    y = frame["value"].map({c: i for i, c in enumerate(ro.CLASSES)}).to_numpy()
    row = pd.read_csv(pc.EDA_ROOT / "10_phase7_validation/v1.3/stage5_families/general_predictions_ordering.csv", nrows=1)
    return cfg, frame, feats, y, ast.literal_eval(row["params_xgboost"].iloc[0])


def main() -> None:
    target = sys.argv[1]
    p7.install_diagnostic_algorithm()
    cfg7 = p7.load_phase7_config()
    out = OUT / target
    out.mkdir(parents=True, exist_ok=True)
    if target == "ordering":
        cfg, frame, feats, y, params = load_ordering()
    else:
        cfg, frame, feats, _ = ru.fit_sets(target)
        y, params = frame["value"].to_numpy(dtype=float), ru.xgb_params(target)
    groups = pc.load_group_ids(cfg)
    rows = []
    for i in range(N_SPLITS):
        rows += (ordering_split(i, cfg, cfg7, frame, feats, y, params) if target == "ordering"
                 else regression_split(target, i, cfg, cfg7, frame, feats, y, params, groups))
        pd.DataFrame(rows).to_csv(out / "repeated_split_coverage.csv", index=False, encoding="utf-8")
    summary = summarise(pd.DataFrame(rows))
    summary.to_csv(out / "repeated_split_summary.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 230, "display.max_columns", 20)
    print(summary.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
