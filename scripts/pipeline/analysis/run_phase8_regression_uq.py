"""Phase 8 UQ-R pilot: conformal prediction intervals for Curie (dataset v1.3) and Ms per cell (dataset v1.2; target unchanged in v1.3).

Design: EDA/11_phase8_xai_uq/PLAN.md. A calibration set of whole formulas is carved out of the TRAINING partition; the XGBoost point
model (Phase 6/v1.3 selected hyperparameters) is fit on the rest; the test partition is touched once. Methods: split conformal,
normalized conformal (cross-fitted difficulty model) and CQR. Run from EDA/src, OMP_NUM_THREADS unset:
    python run_phase8_regression_uq.py curie | ms_moment
"""
from __future__ import annotations

import ast
import json
import sys

import numpy as np
import pandas as pd
import xgboost as xgb

import phase6_common as pc
import phase6_models as pm
import phase7_validation as p7
import phase8_uq as uq

ALPHA = 0.10
ALPHA_GRID = [round(a, 2) for a in np.arange(0.05, 0.55, 0.05)]
CAL_FRACTION, N_FOLDS, N_BOOT = 0.20, 3, 1000
CONFIG = {"curie": {"version": "v1.3", "split": "split_curie.csv"}, "ms_moment": {"version": "v1.2", "split": "split_ms.csv"}}
OUT = pc.EDA_ROOT / "11_phase8_xai_uq"
FAMILIES = ["Transition Metal", "Rare Earth", "Oxide", "Intermetallic"]
SIGMA_PARAMS = {"n_estimators": 300, "max_depth": 4, "learning_rate": 0.05, "subsample": 0.8, "colsample_bytree": 0.8}


def xgb_params(target: str) -> dict:
    """Selected XGBoost hyperparameters (no new tuning): Stage 5 v1.3 general model for Curie, Stage 2 v1.2 JSON for Ms."""
    if target == "curie":
        row = pd.read_csv(pc.EDA_ROOT / "10_phase7_validation/v1.3/stage5_families/general_predictions_curie.csv", nrows=1)
        return ast.literal_eval(row["params_xgboost"].iloc[0])
    path = pc.EDA_ROOT / "03_baseline_tier1/v1.2/ms/hyperparameters_and_preprocessing_ms_moment.json"
    return json.loads(path.read_text(encoding="utf-8"))["xgboost"]["selected_hyperparameters"]


def regressor(params: dict, seed: int, **extra) -> xgb.XGBRegressor:
    return xgb.XGBRegressor(tree_method="hist", n_jobs=p7.XGB_N_JOBS, random_state=seed, **params, **extra)


def fit_sets(target: str):
    cfg = p7.dataset_cfg(CONFIG[target]["version"])
    frame, feats = pm.load_modeling_frame(cfg, target, "tier1", p7.split_dir(CONFIG[target]["version"]) / CONFIG[target]["split"])
    frame = frame.reset_index(drop=True)
    frame["source"] = frame["_source"].astype(str).str.split(" ").str[0].str.replace(".csv", "", regex=False)
    train = (frame["split"] == "train").to_numpy()
    cal_in_train = uq.grouped_calibration_split(frame.loc[train, "reduced_formula"].to_numpy(), CAL_FRACTION, cfg["random_seed"] + 8000)
    idx = np.flatnonzero(train)
    role = np.full(len(frame), "unused", dtype=object)
    role[idx[~cal_in_train]], role[idx[cal_in_train]] = "proper_train", "calibration"
    role[(frame["split"] == "test").to_numpy()] = "test"
    return cfg, frame, feats, role


def cross_fitted_abs_residuals(frame, feats, y, mask, params, seed) -> np.ndarray:
    """Out-of-fold |residual| of the point model on proper-train rows (formula-grouped folds), the target of the difficulty model."""
    sub = np.flatnonzero(mask)
    codes = pd.factorize(frame.loc[sub, "reduced_formula"])[0]
    fold = np.random.default_rng(seed).integers(0, N_FOLDS, size=codes.max() + 1)[codes]
    out = np.zeros(len(sub))
    for k in range(N_FOLDS):
        tr, te = sub[fold != k], sub[fold == k]
        out[fold == k] = np.abs(y[te] - regressor(params, seed).fit(frame.loc[tr, feats], y[tr]).predict(frame.loc[te, feats]))
    return out


def build_intervals(frame, feats, y, role, params, seed) -> dict:
    """Fit everything once; return point predictions, difficulty scores and quantile bands for calibration and test rows."""
    tr, cal, te = (role == "proper_train"), (role == "calibration"), (role == "test")
    point = regressor(params, seed).fit(frame.loc[tr, feats], y[tr])
    resid = cross_fitted_abs_residuals(frame, feats, y, tr, params, seed)
    sigma_model = regressor(SIGMA_PARAMS, seed).fit(frame.loc[tr, feats], resid)
    floor = max(float(np.quantile(resid, 0.05)), 1e-6)
    lo_model = regressor(params, seed, objective="reg:quantileerror", quantile_alpha=ALPHA / 2).fit(frame.loc[tr, feats], y[tr])
    hi_model = regressor(params, seed, objective="reg:quantileerror", quantile_alpha=1 - ALPHA / 2).fit(frame.loc[tr, feats], y[tr])
    out = {}
    for name, mask in (("cal", cal), ("test", te)):
        x = frame.loc[mask, feats]
        q_lo, q_hi = lo_model.predict(x), hi_model.predict(x)
        out[name] = {"pred": point.predict(x), "sigma": np.maximum(sigma_model.predict(x), floor), "q_lo": np.minimum(q_lo, q_hi), "q_hi": np.maximum(q_lo, q_hi)}
    return out


def method_intervals(pred: dict, y_cal: np.ndarray, alpha: float, cal_sel=None, test_sel=None) -> dict:
    """Intervals for the test rows from the three methods, calibrated on (a subset of) the calibration rows."""
    cs = np.ones(len(y_cal), dtype=bool) if cal_sel is None else cal_sel
    ts = slice(None) if test_sel is None else test_sel
    c, t = pred["cal"], pred["test"]
    q_split = uq.conformal_quantile(np.abs(y_cal[cs] - c["pred"][cs]), alpha)
    q_norm = uq.conformal_quantile(np.abs(y_cal[cs] - c["pred"][cs]) / c["sigma"][cs], alpha)
    q_cqr = uq.conformal_quantile(uq.cqr_scores(y_cal[cs], c["q_lo"][cs], c["q_hi"][cs]), alpha)
    return {"split_conformal": uq.interval_split(t["pred"][ts], q_split), "normalized_conformal": uq.interval_normalized(t["pred"][ts], t["sigma"][ts], q_norm),
            "cqr": uq.cqr_interval(t["q_lo"][ts], t["q_hi"][ts], q_cqr)}


def subgroup_masks(meta: pd.DataFrame, pred: dict, groups: dict) -> dict:
    sets = {f"family:{f}": meta["material_id"].isin(groups[f]).to_numpy() for f in FAMILIES}
    for src in sorted(meta["source"].unique()):
        sets[f"source:{src}"] = (meta["source"] == src).to_numpy()
    p = pred["test"]["pred"]
    cuts = np.quantile(p, [0, 1 / 3, 2 / 3, 1])
    for i, tier in enumerate(["lowest", "middle", "highest"]):
        sets[f"predicted_value:{tier}_third"] = (p >= cuts[i]) & (p <= cuts[i + 1])
    decile = pd.qcut(pred["test"]["sigma"], 10, labels=False, duplicates="drop")
    for d in sorted(set(decile)):
        sets[f"difficulty_decile:{int(d) + 1:02d}"] = decile == d
    return sets


def summarise(target: str, frame, role, pred, y) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    te = role == "test"
    y_cal, y_te = y[role == "calibration"], y[te]
    meta = frame.loc[te].reset_index(drop=True)
    sets = subgroup_masks(meta, pred, pc.load_group_ids(p7.dataset_cfg(CONFIG[target]["version"])))
    intervals = method_intervals(pred, y_cal, ALPHA)
    rows, by_group = [], []
    for method, (lo, hi) in intervals.items():
        cov = uq.covered_mask(y_te, lo, hi)
        ci = uq.formula_bootstrap_ci(cov, meta["reduced_formula"].to_numpy(), N_BOOT, 0)
        rows.append({"target": target, "method": method, "alpha": ALPHA, "nominal": 1 - ALPHA, "n_test": len(y_te), "coverage": cov.mean(), "coverage_ci_low": ci[0],
                     "coverage_ci_high": ci[1], "mean_width": float(np.mean(hi - lo)), "median_width": float(np.median(hi - lo)),
                     "winkler_score": uq.winkler_score(y_te, lo, hi, ALPHA), "within_2pt_of_nominal": bool(abs(cov.mean() - (1 - ALPHA)) <= 0.02)})
        for name, mask in sets.items():
            if mask.sum():
                tab = uq.coverage_by_group(cov[mask], np.full(int(mask.sum()), name), meta.loc[mask, "reduced_formula"].to_numpy(), 1 - ALPHA)
                by_group.append(tab.assign(method=method, mean_width=float(np.mean((hi - lo)[mask]))))
    curve = [{"method": m, "alpha": a, "nominal": 1 - a, "coverage": uq.coverage(y_te, *method_intervals(pred, y_cal, a)[m])}
             for a in ALPHA_GRID for m in ("split_conformal", "normalized_conformal")]
    return pd.DataFrame(rows), pd.concat(by_group, ignore_index=True), pd.DataFrame(curve), intervals


def shift_table(target: str, frame, role, pred, y) -> pd.DataFrame:
    """Calibrate on rows of source A, test on rows of source B (A == B is the in-source reference)."""
    cal_src = frame.loc[role == "calibration", "source"].to_numpy()
    meta = frame.loc[role == "test"].reset_index(drop=True)
    y_cal, y_te = y[role == "calibration"], y[role == "test"]
    rows = []
    for a in sorted(set(cal_src)):
        cs = cal_src == a
        for b in sorted(meta["source"].unique()):
            ts = (meta["source"] == b).to_numpy()
            if cs.sum() < 50 or meta.loc[ts, "reduced_formula"].nunique() < 30:
                continue
            for method, (lo, hi) in method_intervals(pred, y_cal, ALPHA, cs, ts).items():
                cov = uq.covered_mask(y_te[ts], lo, hi)
                rows.append({"target": target, "calibrated_on": a, "tested_on": b, "method": method, "n_calibration": int(cs.sum()), "n_test": int(ts.sum()),
                             "n_test_formulas": int(meta.loc[ts, "reduced_formula"].nunique()), "coverage": cov.mean(), "gap_vs_nominal": cov.mean() - (1 - ALPHA),
                             "mean_width": float(np.mean(hi - lo))})
    return pd.DataFrame(rows)


def main() -> None:
    target = sys.argv[1]
    p7.install_diagnostic_algorithm()
    cfg, frame, feats, role = fit_sets(target)
    y = frame["value"].to_numpy(dtype=float)
    params = xgb_params(target)
    print(f"{target}: rows by role { {k: int((role == k).sum()) for k in ['proper_train', 'calibration', 'test']} }; params {params}", flush=True)
    pred = build_intervals(frame, feats, y, role, params, cfg["random_seed"])
    summary, by_group, curve, intervals = summarise(target, frame, role, pred, y)
    shift = shift_table(target, frame, role, pred, y)
    out = OUT / target
    out.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out / "uq_summary.csv", index=False, encoding="utf-8")
    by_group.to_csv(out / "uq_coverage_by_group.csv", index=False, encoding="utf-8")
    curve.to_csv(out / "uq_coverage_curve.csv", index=False, encoding="utf-8")
    shift.to_csv(out / "uq_source_shift.csv", index=False, encoding="utf-8")
    te = frame.loc[role == "test", ["material_id", "reduced_formula", "source"]].reset_index(drop=True)
    te = te.assign(y_true=y[role == "test"], y_pred=pred["test"]["pred"], sigma_hat=pred["test"]["sigma"])
    for m, (lo, hi) in intervals.items():
        te[f"{m}_lo"], te[f"{m}_hi"] = lo, hi
    te = te.assign(q_lo_raw=pred["test"]["q_lo"], q_hi_raw=pred["test"]["q_hi"])
    te.to_parquet(out / "uq_test_intervals.parquet")
    cal = frame.loc[role == "calibration", ["material_id", "reduced_formula", "source"]].reset_index(drop=True)   # saved so every qhat can be audited
    cal.assign(y_true=y[role == "calibration"], y_pred=pred["cal"]["pred"], sigma_hat=pred["cal"]["sigma"], q_lo_raw=pred["cal"]["q_lo"],
               q_hi_raw=pred["cal"]["q_hi"]).to_parquet(out / "uq_calibration_arrays.parquet")
    pd.set_option("display.width", 220)
    print(summary.round(3).to_string(index=False))
    print(by_group[by_group["group"].str.startswith(("family", "source"))].round(3).to_string(index=False))
    print(shift.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
