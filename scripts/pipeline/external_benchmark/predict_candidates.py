"""Score real compounds that are absent from the training data (plan: PLAN.md).

Models: Tier 1 XGBoost for Curie temperature (v1.3) and for magnetic ordering (v1.3), selected hyperparameters, no tuning. 80% of the formulas train the
model; the other 20% (seeded, whole formulas) calibrate the Phase 8 uncertainty methods: normalized conformal intervals for Curie, and prior-corrected +
temperature-scaled probabilities with class-conditional conformal sets for ordering. Candidates never touch training or calibration.
Usage (from this folder, OMP_NUM_THREADS unset):  python predict_candidates.py
Outputs: candidates_predictions.csv, secondary_check_computed_ordering.csv
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "EDA" / "src"))
sys.path.insert(0, str(HERE))
import features as F  # noqa: E402
import phase6_models as pm  # noqa: E402
import phase7_validation as p7  # noqa: E402
import phase8_uq as uq  # noqa: E402
import run_phase8_ordering_uq as ro  # noqa: E402
import run_phase8_regression_uq as ru  # noqa: E402

ALPHA, CAL_FRACTION, SEED = 0.10, 0.20, 20269001
MIN_MAGNETIC_ION_FRACTION = 0.25
CLASSES = ro.CLASSES


def calibration_mask(formulas: pd.Series) -> np.ndarray:
    return uq.grouped_calibration_split(formulas.to_numpy(), CAL_FRACTION, SEED)


def candidate_table() -> pd.DataFrame:
    pool = pd.read_csv(HERE / "mp_experimental_magnetic_pool_raw.csv", keep_default_na=False, na_values=[""])   # the real formula "NaN" (sodium nitride) must stay a string
    capable = set(yaml.safe_load((ROOT / "EDA/00_config/v1_3_curation_rules.yaml").read_text(encoding="utf-8"))["curie"]["magnetism_capable_elements"])
    new = pool[~pool["in_training_data"]].copy()
    new["has_magnetism_capable_element"] = new["reduced_formula"].map(lambda f: bool(set(F.Composition(f).chemical_system.split("-")) & capable))
    known = pd.read_parquet(ROOT / "EDA/datasets/v1.2/feature_repository_v1.2.parquet", columns=["reduced_formula"])["reduced_formula"].dropna().unique()
    seen_systems = set()
    for f in known:
        try:
            seen_systems.add(F.Composition(f).chemical_system)
        except Exception:      # noqa: BLE001 - pseudo-formulas were quarantined in v1.2; any leftover unparseable string simply contributes no system
            continue
    new["chemical_system_seen"] = new["chemsys"].isin(seen_systems)
    return new.drop_duplicates("reduced_formula").reset_index(drop=True)


def fit_curie(cands_x: pd.DataFrame) -> pd.DataFrame:
    cfg = p7.dataset_cfg("v1.3")
    frame, feats = pm.load_modeling_frame(cfg, "curie", "tier1", p7.split_dir("v1.3") / "split_curie.csv")
    frame = frame.reset_index(drop=True)
    y, params = frame["value"].to_numpy(dtype=float), ru.xgb_params("curie")
    cal = calibration_mask(frame["reduced_formula"])
    tr = ~cal
    seed = cfg["random_seed"]
    point = ru.regressor(params, seed).fit(frame.loc[tr, feats], y[tr])
    resid = ru.cross_fitted_abs_residuals(frame, feats, y, tr, params, seed)
    sigma_model = ru.regressor(ru.SIGMA_PARAMS, seed).fit(frame.loc[tr, feats], resid)
    floor = max(float(np.quantile(resid, 0.05)), 1e-6)
    cal_pred, cal_sigma = point.predict(frame.loc[cal, feats]), np.maximum(sigma_model.predict(frame.loc[cal, feats]), floor)
    qhat = uq.conformal_quantile(np.abs(y[cal] - cal_pred) / cal_sigma, ALPHA)
    pred, sigma = point.predict(cands_x[feats]), np.maximum(sigma_model.predict(cands_x[feats]), floor)
    print(f"Curie: train {int(tr.sum()):,} rows, calibration {int(cal.sum()):,} rows, qhat {qhat:.2f}", flush=True)
    return pd.DataFrame({"tc_pred_k": pred, "tc_lo_k": np.maximum(pred - qhat * sigma, 0.0), "tc_hi_k": pred + qhat * sigma, "tc_sigma_k": sigma})


def fit_ordering(cands_x: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    cfg = p7.dataset_cfg("v1.3")
    frame, feats = pm.load_modeling_frame(cfg, "ordering", "tier1", p7.split_dir("v1.3") / "split_ordering.csv")
    frame = frame.reset_index(drop=True)
    y = frame["value"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy()
    cal = calibration_mask(frame["reduced_formula"])
    tr = ~cal
    path = ROOT / "EDA/10_phase7_validation/v1.3/stage5_families/general_predictions_ordering.csv"
    params = ast.literal_eval(pd.read_csv(path, nrows=1)["params_xgboost"].iloc[0])
    model = pm.fit(pm.build_estimator("xgboost", "classification", params, cfg["random_seed"]), "xgboost", "classification", frame.loc[tr, feats], y[tr])
    freq = np.bincount(y[tr], minlength=len(CLASSES)) / tr.sum()
    p_cal = ro.prior_correct(model.predict_proba(frame.loc[cal, feats]), freq)
    temp = uq.fit_temperature(p_cal, y[cal])
    p_cal = uq.apply_temperature(p_cal, temp)
    thresholds = uq.class_conditional_thresholds(p_cal, y[cal], ALPHA, len(CLASSES))
    p_new = uq.apply_temperature(ro.prior_correct(model.predict_proba(cands_x[feats]), freq), temp)
    sets = uq.class_conditional_sets(p_new, thresholds)
    print(f"ordering: train {int(tr.sum()):,} rows, calibration {int(cal.sum()):,} rows, temperature {temp:.2f}", flush=True)
    out = pd.DataFrame(p_new, columns=[f"p_{c}" for c in CLASSES])
    out["ordering_set"] = ["/".join(c for c, m in zip(CLASSES, row) if m) or "(empty)" for row in sets]
    out["ordering_top"] = [CLASSES[i] for i in p_new.argmax(1)]
    mean, std = frame.loc[tr, feats].mean(), frame.loc[tr, feats].std().replace(0, 1)
    tree = cKDTree(((frame.loc[tr, feats] - mean) / std).fillna(0).to_numpy())
    dist, _ = tree.query(((cands_x[feats] - mean) / std).fillna(0).to_numpy(), k=1)
    return out, dist


def main() -> None:
    p7.install_diagnostic_algorithm()
    cands = candidate_table()
    print(f"unseen real compounds: {len(cands):,}; with a magnetism-capable element: {int(cands['has_magnetism_capable_element'].sum()):,}; "
          f"unseen chemical system: {int((~cands['chemical_system_seen']).sum()):,}", flush=True)
    cands = cands[cands["has_magnetism_capable_element"]].reset_index(drop=True)
    x = F.feature_frame(cands["reduced_formula"].tolist())
    ok = x.notna().all(axis=1).to_numpy()
    cands, x = cands[ok].reset_index(drop=True), x[ok].reset_index(drop=True)
    print(f"scoreable candidates: {len(cands):,}", flush=True)
    curie = fit_curie(x)
    order, dist = fit_ordering(x)
    result = pd.concat([cands, order, curie], axis=1).assign(nn_distance_to_training=dist)
    result["stratum"] = np.where(result["chemical_system_seen"], "B_seen_system", "A_unseen_system")
    capable = set(yaml.safe_load((ROOT / "EDA/00_config/v1_3_curation_rules.yaml").read_text(encoding="utf-8"))["curie"]["magnetism_capable_elements"])
    result["magnetic_ion_fraction"] = [sum(F.Composition(f).get_atomic_fraction(e) for e in F.Composition(f).elements if e.symbol in capable) for f in result["reduced_formula"]]
    # Deviation 1 (PLAN.md): dilute magnetic ions in large molecular salts cannot order at high temperature; require >= 25% magnetism-capable atoms
    result["eligible"] = result["ordering_set"].isin(["FM", "FiM"]) & (result["magnetic_ion_fraction"] >= MIN_MAGNETIC_ION_FRACTION)
    rng = np.random.default_rng(SEED)
    result["random_order"] = np.nan
    for _, idx in result[result["eligible"]].groupby("stratum").groups.items():
        result.loc[idx, "random_order"] = rng.permutation(len(idx)) + 1
    result.to_csv(HERE / "candidates_predictions.csv", index=False, encoding="utf-8")
    comp = result[result["ordering"].isin(CLASSES)]
    check = pd.DataFrame([{"group": g, "n": len(d), "top_class_matches_MP_computed": float((d["ordering_top"] == d["ordering"]).mean()),
                           "MP_class_inside_set": float(np.mean([o in s.split("/") for o, s in zip(d["ordering"], d["ordering_set"])])),
                           "mean_set_size": float(d["ordering_set"].map(lambda s: len(s.split("/")) if s != "(empty)" else 0).mean())}
                          for g, d in [("all", comp), *comp.groupby("stratum")]])
    check.to_csv(HERE / "secondary_check_computed_ordering.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 200, "display.max_columns", 20)
    print(check.round(3).to_string(index=False))
    print(result.groupby("stratum")["eligible"].agg(["size", "sum"]))


if __name__ == "__main__":
    main()
