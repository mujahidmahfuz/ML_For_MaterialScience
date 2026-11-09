"""Phase 8 UQ-C: probability calibration and conformal prediction sets for magnetic ordering (dataset v1.3, Tier 1).

Design: EDA/11_phase8_xai_uq/PLAN.md. Whole formulas are carved out of the TRAINING partition as a calibration set; the XGBoost classifier
(Phase 6/v1.3 selected hyperparameters, balanced class weights as in Phase 6) is fit on the rest; the test partition is touched once.
Reported: raw vs prior-corrected vs prior-corrected + temperature-scaled probabilities (ECE, Brier, NLL); marginal (LAC) and class-conditional
conformal sets (coverage, size, per-class coverage); subgroup coverage; calibration-source shift. Run from EDA/src, OMP_NUM_THREADS unset:
    python run_phase8_ordering_uq.py
"""
from __future__ import annotations

import ast

import numpy as np
import pandas as pd

import phase6_common as pc
import phase6_models as pm
import phase7_validation as p7
import phase8_uq as uq

ALPHA, CAL_FRACTION, N_BINS = 0.10, 0.20, 15
CLASSES = ["FM", "AFM", "FiM", "NM"]
FAMILIES = ["Transition Metal", "Rare Earth", "Oxide", "Intermetallic"]
VERSION = "v1.3"
OUT = pc.EDA_ROOT / "11_phase8_xai_uq" / "ordering"


def provenance(frame: pd.DataFrame) -> np.ndarray:
    return np.where(frame["_source"].astype(str).str.startswith("mp_reformatted"), "computational_MP", "experimental")


def prior_correct(probs: np.ndarray, train_freq: np.ndarray) -> np.ndarray:
    """Undo the 'balanced' class weighting: multiply by the training class frequencies and renormalise."""
    adj = probs * train_freq[None, :]
    return adj / adj.sum(axis=1, keepdims=True)


def ece_with_formula_ci(p: np.ndarray, y: np.ndarray, formulas: np.ndarray, n_boot: int = 300) -> tuple[float, float, float]:
    codes = pd.factorize(pd.Series(formulas))[0]
    rng = np.random.default_rng(0)
    boots = []
    for _ in range(n_boot):
        w = np.bincount(rng.integers(0, codes.max() + 1, codes.max() + 1), minlength=codes.max() + 1)[codes]
        rows = np.repeat(np.arange(len(y)), w)
        boots.append(uq.expected_calibration_error(p[rows], y[rows], N_BINS))
    return uq.expected_calibration_error(p, y, N_BINS), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))


def calibration_rows(variants: dict, y_te: np.ndarray, formulas: np.ndarray) -> pd.DataFrame:
    rows = []
    for name, p in variants.items():
        ece, lo, hi = ece_with_formula_ci(p, y_te, formulas)
        rows.append({"probabilities": name, "ece": ece, "ece_ci_low": lo, "ece_ci_high": hi, "brier": uq.brier_score(p, y_te),
                     "nll": uq.negative_log_likelihood(p, y_te), "accuracy": float((p.argmax(axis=1) == y_te).mean())})
    return pd.DataFrame(rows)


def set_metrics(name: str, sets: np.ndarray, y: np.ndarray) -> dict:
    per = uq.per_class_coverage(sets, y, len(CLASSES))
    return {"method": name, "coverage": uq.set_coverage(sets, y), "mean_set_size": uq.mean_set_size(sets), "empty_set_rate": uq.empty_set_rate(sets),
            **{f"coverage_{c}": per[i] for i, c in enumerate(CLASSES)}}


def conformal_variants(p_cal, y_cal, p_te, y_te) -> tuple[dict, pd.DataFrame]:
    sets = {"marginal_LAC": uq.prediction_sets(p_te, uq.lac_threshold(p_cal, y_cal, ALPHA)),
            "class_conditional": uq.class_conditional_sets(p_te, uq.class_conditional_thresholds(p_cal, y_cal, ALPHA, len(CLASSES)))}
    return sets, pd.DataFrame([set_metrics(k, v, y_te) for k, v in sets.items()])


def subgroup_table(sets: dict, y_te: np.ndarray, meta: pd.DataFrame, groups: dict) -> pd.DataFrame:
    masks = {f"family:{f}": meta["material_id"].isin(groups[f]).to_numpy() for f in FAMILIES}
    masks.update({f"provenance:{p}": (meta["provenance"] == p).to_numpy() for p in ("computational_MP", "experimental")})
    masks.update({f"true_class:{c}": (y_te == i) for i, c in enumerate(CLASSES)})
    rows = []
    for method, s in sets.items():
        hit = s[np.arange(len(y_te)), y_te]
        for name, m in masks.items():
            if m.any():
                tab = uq.coverage_by_group(hit[m], np.full(int(m.sum()), name), meta.loc[m, "reduced_formula"].to_numpy(), 1 - ALPHA)
                rows.append(tab.assign(method=method, mean_set_size=float(s[m].sum(axis=1).mean())))
    return pd.concat(rows, ignore_index=True)


def shift_table(p_cal, y_cal, prov_cal, p_te, y_te, prov_te, meta) -> pd.DataFrame:
    rows = []
    for a in ("computational_MP", "experimental"):
        for b in ("computational_MP", "experimental"):
            cs, ts = prov_cal == a, prov_te == b
            if cs.sum() < 50 or meta.loc[ts, "reduced_formula"].nunique() < 30:
                continue
            enough = [CLASSES[k] for k in range(len(CLASSES)) if (y_cal[cs] == k).sum() >= 100]
            sets, _ = conformal_variants(p_cal[cs], y_cal[cs], p_te[ts], y_te[ts])
            for method, s in sets.items():
                rows.append({"calibrated_on": a, "tested_on": b, "n_calibration": int(cs.sum()), "n_test": int(ts.sum()),
                             "classes_with_100_plus_calibration_rows": "/".join(enough), **set_metrics(method, s, y_te[ts])})
    return pd.DataFrame(rows)


def assign_roles(frame: pd.DataFrame, seed: int) -> np.ndarray:
    train = (frame["split"] == "train").to_numpy()
    cal_in_train = uq.grouped_calibration_split(frame.loc[train, "reduced_formula"].to_numpy(), CAL_FRACTION, seed + 8000)
    idx = np.flatnonzero(train)
    role = np.full(len(frame), "unused", dtype=object)
    role[idx[~cal_in_train]], role[idx[cal_in_train]] = "proper_train", "calibration"
    role[(frame["split"] == "test").to_numpy()] = "test"
    return role


def main() -> None:
    cfg = p7.dataset_cfg(VERSION)
    p7.install_diagnostic_algorithm()
    frame, feats = pm.load_modeling_frame(cfg, "ordering", "tier1", p7.split_dir(VERSION) / "split_ordering.csv")
    frame = frame.reset_index(drop=True)
    y = frame["value"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy()
    role = assign_roles(frame, cfg["random_seed"])
    row = pd.read_csv(pc.EDA_ROOT / "10_phase7_validation/v1.3/stage5_families/general_predictions_ordering.csv", nrows=1)
    params = ast.literal_eval(row["params_xgboost"].iloc[0])
    tr, cal, te = role == "proper_train", role == "calibration", role == "test"
    print(f"ordering: rows by role { {k: int((role == k).sum()) for k in ['proper_train', 'calibration', 'test']} }; params {params}", flush=True)
    model = pm.fit(pm.build_estimator("xgboost", "classification", params, cfg["random_seed"]), "xgboost", "classification", frame.loc[tr, feats], y[tr])
    p_cal, p_te = model.predict_proba(frame.loc[cal, feats]), model.predict_proba(frame.loc[te, feats])
    train_freq = np.bincount(y[tr], minlength=len(CLASSES)) / tr.sum()
    pc_cal, pc_te = prior_correct(p_cal, train_freq), prior_correct(p_te, train_freq)
    temp = uq.fit_temperature(pc_cal, y[cal])
    names = ["raw (balanced-weight) probabilities", "prior-corrected", "prior-corrected + temperature"]
    variants_te = dict(zip(names, [p_te, pc_te, uq.apply_temperature(pc_te, temp)]))
    variants_cal = dict(zip(names, [p_cal, pc_cal, uq.apply_temperature(pc_cal, temp)]))
    meta = frame.loc[te].reset_index(drop=True)
    meta["provenance"] = provenance(meta)
    y_te, y_cal = y[te], y[cal]
    OUT.mkdir(parents=True, exist_ok=True)
    cal_tab = calibration_rows(variants_te, y_te, meta["reduced_formula"].to_numpy()).assign(temperature_fitted_on_calibration=temp)
    cal_tab.to_csv(OUT / "uq_calibration_metrics.csv", index=False, encoding="utf-8")
    set_rows, sub_rows, groups = [], [], pc.load_group_ids(cfg)
    for vname in names:
        sets, tab = conformal_variants(variants_cal[vname], y_cal, variants_te[vname], y_te)
        set_rows.append(tab.assign(probabilities=vname))
        if vname == "prior-corrected":
            sub_rows.append(subgroup_table(sets, y_te, meta, groups))
    pd.concat(set_rows).to_csv(OUT / "uq_conformal_sets.csv", index=False, encoding="utf-8")
    pd.concat(sub_rows).to_csv(OUT / "uq_coverage_by_group.csv", index=False, encoding="utf-8")
    prov_cal = provenance(frame.loc[cal].reset_index(drop=True))
    shift = shift_table(variants_cal["prior-corrected"], y_cal, prov_cal, variants_te["prior-corrected"], y_te, meta["provenance"].to_numpy(), meta)
    shift.to_csv(OUT / "uq_source_shift.csv", index=False, encoding="utf-8")
    np.savez_compressed(OUT / "uq_probabilities.npz", p_cal=p_cal, p_te=p_te, y_cal=y_cal, y_te=y_te, train_freq=train_freq, temperature=temp)
    pd.set_option("display.width", 230, "display.max_columns", 30)
    print(cal_tab.round(4).to_string(index=False))
    print(pd.concat(set_rows).round(3).to_string(index=False))
    print(shift.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
