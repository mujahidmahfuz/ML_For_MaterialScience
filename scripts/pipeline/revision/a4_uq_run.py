"""A4 / A10 data generation: the Phase 8 repeated-split UQ runs (same code, seeds and roles as run_phase8_uq_repeated.py), but saving
per-row test intervals, the calibration arrays and composition distances, so that coverage can be evaluated on subgroups that are NOT
defined by the method's own difficulty score, and distance-aware conformal variants can be computed without refitting.

Regression (curie v1.3, ms_moment v1.2): per split, test rows (y, prediction, sigma, CQR band, split/normalized/CQR intervals at 90%) and
calibration rows (y, prediction, sigma, CQR band); composition (TV) distance of every test and calibration formula to the nearest
proper-training formula.
Ordering (v1.3): per split, raw test and calibration probabilities of the Phase 8 XGBoost model (prior correction / temperature are
applied in the analysis step so that the calibration-split variant can be evaluated).
Usage (from the project root): python final/revision/scripts/a4_uq_run.py <curie|ms_moment|ordering>
Outputs: final/revision/outputs/a4/<target>/split__<i>.parquet (+ cal__<i>.parquet; ordering: proba__<i>.npz)
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from pymatgen.core import Composition

import rev_common as rc
import phase6_common as pc  # noqa: E402  (on sys.path via rev_common)
import run_phase8_regression_uq as ru  # noqa: E402
import run_phase8_uq_repeated as rr  # noqa: E402

sys.path.insert(0, str(rc.ROOT / "new_materials_finding" / "external_audit"))
from audit_common import fraction_vectors, nearest_tv_distance  # noqa: E402

OUT = rc.REV / "a4"


def distances(frame: pd.DataFrame, role: np.ndarray) -> np.ndarray:
    """TV distance of every row's formula to the nearest proper-training formula (0 for proper-training rows)."""
    train_f = frame.loc[role == "proper_train", "reduced_formula"].unique()
    query_f = frame.loc[np.isin(role, ["calibration", "test"]), "reduced_formula"].unique()
    elements = sorted({el.symbol for f in np.concatenate([train_f, query_f]) for el in Composition(f).elements})
    d, _, _ = nearest_tv_distance(fraction_vectors(query_f, elements), fraction_vectors(train_f, elements))
    dmap = dict(zip(query_f, np.asarray(d).ravel()))
    return frame["reduced_formula"].map(dmap).fillna(0.0).to_numpy()


def regression(target: str) -> None:
    rc.p7.install_diagnostic_algorithm()
    cfg7 = rc.p7.load_phase7_config()
    cfg, frame, feats, _ = ru.fit_sets(target)
    y, params = frame["value"].to_numpy(dtype=float), ru.xgb_params(target)
    groups = pc.load_group_ids(cfg)
    out = OUT / target
    out.mkdir(parents=True, exist_ok=True)
    for i in range(rr.N_SPLITS):
        if (out / f"split__{i}.parquet").exists():
            continue
        role = rr.split_roles(frame, y, cfg7, cfg["random_seed"], i)
        pred = ru.build_intervals(frame, feats, y, role, params, cfg["random_seed"])
        dist = distances(frame, role)
        te, cal = role == "test", role == "calibration"
        intervals = ru.method_intervals(pred, y[cal], ru.ALPHA)
        meta = frame.loc[te, ["material_id", "reduced_formula", "source"]].reset_index(drop=True)
        test = meta.assign(split_id=i, y=y[te], pred=pred["test"]["pred"], sigma=pred["test"]["sigma"], q_lo=pred["test"]["q_lo"],
                           q_hi=pred["test"]["q_hi"], distance=dist[te])
        for name, members in groups.items():
            test[f"grp_{name}"] = test["material_id"].isin(members).to_numpy()
        for method, (lo, hi) in intervals.items():
            test[f"{method}_lo"], test[f"{method}_hi"] = lo, hi
        calib = frame.loc[cal, ["material_id", "reduced_formula", "source"]].reset_index(drop=True).assign(
            split_id=i, y=y[cal], pred=pred["cal"]["pred"], sigma=pred["cal"]["sigma"], q_lo=pred["cal"]["q_lo"], q_hi=pred["cal"]["q_hi"],
            distance=dist[cal])
        test.to_parquet(out / f"split__{i}.parquet")
        calib.to_parquet(out / f"cal__{i}.parquet")
        cov = {m: round(float(((test["y"] >= test[f"{m}_lo"]) & (test["y"] <= test[f"{m}_hi"])).mean()), 3) for m in intervals}
        print(f"[done] {target} split {i}: {cov}", flush=True)


def ordering() -> None:
    rc.p7.install_diagnostic_algorithm()
    cfg7 = rc.p7.load_phase7_config()
    cfg, frame, feats, y, params = rr.load_ordering()
    out = OUT / "ordering"
    out.mkdir(parents=True, exist_ok=True)
    for i in range(rr.N_SPLITS):
        path = out / f"proba__{i}.npz"
        if path.exists():
            continue
        role = rr.split_roles(frame, y, cfg7, cfg["random_seed"], i)
        tr, cal, te = role == "proper_train", role == "calibration", role == "test"
        model = rc.pm.fit(rc.pm.build_estimator("xgboost", "classification", params, cfg["random_seed"]), "xgboost", "classification",
                          frame.loc[tr, feats], y[tr])
        np.savez_compressed(path, p_cal=model.predict_proba(frame.loc[cal, feats]), y_cal=y[cal], f_cal=frame.loc[cal, "reduced_formula"].to_numpy(),
                            p_te=model.predict_proba(frame.loc[te, feats]), y_te=y[te], train_freq=np.bincount(y[tr], minlength=4) / tr.sum(),
                            src_te=frame.loc[te, "_source"].to_numpy(), f_te=frame.loc[te, "reduced_formula"].to_numpy())
        print(f"[done] ordering split {i}", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "ordering":
        ordering()
    else:
        regression(sys.argv[1])
