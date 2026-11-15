"""Shared helpers for the revision refits (A1 ordering XGBoost seeds, A5 moment per formula unit, A6 physics variants, A8, A12).

Re-uses the frozen pipeline (EDA/src) unchanged: the same estimators (phase6_models.build_estimator, with the Phase 7 XGBoost thread pin),
grids, validation-based selection rule (grid on train -> best validation score -> refit train+validation -> score test) and split
generator (phase7_validation.random_group_split). The only addition is that test-set class probabilities are returned and that the
estimator seed can be set per realisation (pipeline default = analysis_config random_seed).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "EDA" / "src"))

import phase6_common as pc  # noqa: E402,F401
import phase6_models as pm  # noqa: E402
import phase7_validation as p7  # noqa: E402

REV = ROOT / "final" / "revision" / "outputs"
CLASSES = ["FM", "AFM", "FiM", "NM"]
VERSION = {"curie": "v1.3", "ordering": "v1.3", "ms_moment": "v1.2"}
MATCHED_SPLIT = {"curie": "matched_split_curie.csv", "ordering": "matched_split_ordering.csv", "ms_moment": "matched_split_ms.csv"}
SPLITS = [str(i) for i in range(10)]


def setup(target: str) -> tuple[dict, dict]:
    cfg, cfg7 = p7.dataset_cfg(VERSION[target]), p7.load_phase7_config()
    p7.install_diagnostic_algorithm()   # registers linear_clip and pins XGBoost to 16 threads (thread count acts as a seed)
    return cfg, cfg7


def matched_frame(target: str, cfg: dict) -> pd.DataFrame:
    cat = cfg["predictor_rules"]["categorical_predictors"]
    frame, _, _ = pm.load_matched_frame(cfg, target, "tier3", p7.split_dir(VERSION[target]) / MATCHED_SPLIT[target], cat)
    return frame


def encode(values: pd.Series) -> np.ndarray:
    return values.map({c: i for i, c in enumerate(CLASSES)}).to_numpy()


def split_labels(target: str, frame: pd.DataFrame, cfg7: dict, split_id: str, y: np.ndarray | None = None) -> np.ndarray:
    """The exact Phase 7 split assignment: the saved labels for Curie (v1.3) and the moment (v1.2); regenerated for ordering exactly as
    run_v13_ordering.matched() did (class codes as the stratification value)."""
    if target in ("curie", "ms_moment"):
        work = p7.output_dir(cfg7, VERSION[target]) / "work" / target
        saved = pd.read_parquet(work / f"labels__{split_id}.parquet").set_index("material_id")["split"]
        labels = frame["material_id"].map(saved).to_numpy()
        if pd.isna(labels).any():
            raise ValueError(f"{target} split {split_id}: materials without a saved Phase 7 label")
    else:
        ms = cfg7["multisplit"]
        labels = p7.random_group_split(frame["reduced_formula"], y, ms["fractions"], p7.split_seed(cfg7, int(split_id)),
                                       ms["n_strata_bins"], ms["capacity_tolerance"])
    p7.assert_formula_disjoint(frame["reduced_formula"], labels)
    return labels


def fit_select(frame: pd.DataFrame, labels: np.ndarray, feats: list[str], y: np.ndarray, task: str, alg: str, cfg: dict,
               categorical: list[str] | None = None, seed: int | None = None) -> dict:
    """Phase 6 selection rule with an explicit estimator seed; returns test predictions (and probabilities for classification)."""
    seed = cfg["random_seed"] if seed is None else seed
    metric = cfg["models"]["selection_metric"][task]
    lab = list(range(len(CLASSES))) if task == "classification" else None
    idx = {s: labels == s for s in ("train", "validation", "test")}
    X = frame[feats]
    best = None
    for params in pm.grid_for(cfg, alg, task):
        est = pm.fit(pm.build_estimator(alg, task, params, seed, categorical), alg, task, X[idx["train"]], y[idx["train"]])
        val = pm.score(task, y[idx["validation"]], est.predict(X[idx["validation"]]), lab)[metric]
        better = best is None or (val > best[1] if task == "classification" else val < best[1])
        if better:
            best = (params, val)
    tv = idx["train"] | idx["validation"]
    t0 = time.perf_counter()
    final = pm.fit(pm.build_estimator(alg, task, best[0], seed, categorical), alg, task, X[tv], y[tv])
    out = {"best_params": str(best[0]), "val_score": best[1], "refit_seconds": round(time.perf_counter() - t0, 1),
           "test_pred": np.asarray(final.predict(X[idx["test"]]))}
    if task == "classification":
        proba = np.zeros((int(idx["test"].sum()), len(CLASSES)))
        p = final.predict_proba(X[idx["test"]])
        classes = final.classes_ if hasattr(final, "classes_") else final.named_steps["model"].classes_
        proba[:, np.asarray(classes, dtype=int)] = p
        out["test_proba"] = proba
    return out


def chunk_rows(frame: pd.DataFrame, labels: np.ndarray, y: np.ndarray, res: dict, **tags) -> pd.DataFrame:
    te = labels == "test"
    df = pd.DataFrame({**tags, "material_id": frame.loc[te, "material_id"].to_numpy(), "reduced_formula": frame.loc[te, "reduced_formula"].to_numpy(),
                       "y_true": y[te], "y_pred": res["test_pred"]})
    if "test_proba" in res:
        for k in range(len(CLASSES)):
            df[f"p{k}"] = res["test_proba"][:, k]
    return df
