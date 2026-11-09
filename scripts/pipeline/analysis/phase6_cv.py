"""Formula-grouped repeated cross-validation for the small Stage 7 targets (K1, Ms mass, Ms volume).

Single 15% test splits are only 122-648 rows for these targets, so Stage 7 scores every material once per repeat as
an out-of-fold prediction. Folds are grouped by reduced_formula (same leakage rule as the frozen splits); inside each
outer fold the hyperparameter grid is selected on a formula-grouped validation split and refit on the remaining rows,
using the same estimators/grids/selection rule as Stages 2-6 (phase6_models.run_algorithm).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import rankdata

import phase6_common as pc
import phase6_models as pm


def group_folds(groups, n_folds: int, seed: int) -> np.ndarray:
    """Size-balanced assignment of whole groups to folds (largest group first to the lightest fold, random tie-break)."""
    codes, _ = pd.factorize(pd.Series(groups))
    sizes = np.bincount(codes)
    rng = np.random.default_rng(seed)
    order = np.lexsort((rng.random(len(sizes)), -sizes))
    load = np.zeros(n_folds)
    fold_of_group = np.empty(len(sizes), dtype=int)
    for g in order:
        fold = int(np.argmin(load))
        fold_of_group[g] = fold
        load[fold] += sizes[g]
    return fold_of_group[codes]


def inner_split_labels(groups, validation_fraction: float, seed: int) -> np.ndarray:
    """'train'/'validation' labels with whole groups assigned to validation until the requested row fraction is reached."""
    codes, _ = pd.factorize(pd.Series(groups))
    sizes = np.bincount(codes)
    rng = np.random.default_rng(seed)
    target_rows = validation_fraction * len(codes)
    is_val = np.zeros(len(sizes), dtype=bool)
    taken = 0
    for g in rng.permutation(len(sizes)):
        if taken >= target_rows:
            break
        is_val[g] = True
        taken += sizes[g]
    return np.where(is_val[codes], "validation", "train")


def signed_log10(x) -> np.ndarray:
    """sign(x) * log10(1 + |x|): odd, monotone, zero-preserving; for values spanning many orders of magnitude."""
    x = np.asarray(x, dtype=float)
    return np.sign(x) * np.log10(1.0 + np.abs(x))


def weighted_rank_corr(y, pred, w) -> float:
    """Weighted Pearson correlation of average ranks (equals Spearman for unit weights); zero-weight rows drop out."""
    ry, rp = rankdata(y), rankdata(pred)
    w = np.asarray(w, dtype=float)
    sw = w.sum()
    my, mp = (w * ry).sum() / sw, (w * rp).sum() / sw
    cov = (w * (ry - my) * (rp - mp)).sum()
    var = (w * (ry - my) ** 2).sum() * (w * (rp - mp) ** 2).sum()
    return float(cov / np.sqrt(var)) if var > 0 else float("nan")


def regression_metrics_ext(y, pred, w=None) -> dict:
    """Stage 2-6 regression metrics plus the outlier-robust rank correlation."""
    w_ = np.ones(len(y)) if w is None else w
    return {**pm.regression_metrics(y, pred, w), "rank_corr": weighted_rank_corr(y, pred, w_)}


def cv_predictions(frame: pd.DataFrame, features: list[str], y: np.ndarray, algorithm: str, cfg: dict,
                   n_folds: int, n_repeats: int, seed: int, categorical: list[str] | None = None,
                   validation_fraction: float = 0.20) -> tuple[np.ndarray, list[dict]]:
    """Out-of-fold predictions, shape (n_repeats, n_rows): every row is predicted once per repeat by a model that never
    saw its reduced_formula. Returns (predictions, selected-hyperparameter record per outer fold)."""
    groups = frame["reduced_formula"].to_numpy()
    oof = np.full((n_repeats, len(frame)), np.nan)
    chosen = []
    for r in range(n_repeats):
        folds = group_folds(groups, n_folds, seed + r)
        for k in range(n_folds):
            test = folds == k
            labels = np.empty(len(frame), dtype=object)
            labels[test] = "test"
            labels[~test] = inner_split_labels(groups[~test], validation_fraction, seed + 1000 * (r + 1) + k)
            res = pm.run_algorithm(frame.assign(split=labels), features, y, "regression", algorithm, cfg,
                                   categorical=categorical)
            oof[r, test] = res["test_pred"]
            chosen.append({"repeat": r, "fold": k, "algorithm": algorithm, "params": res["best_params"],
                           "val_rmse": res["val_score"], "n_test": int(test.sum())})
    return oof, chosen


def tier3_material_ids(cfg: dict) -> set:
    """material_ids of the Tier 3 physics-complete population (the matched set for the secondary targets)."""
    return set(pd.read_parquet(pc.tier_path(cfg, "tier3"), columns=["material_id"])["material_id"])


def load_cv_frame(cfg: dict, target: str, tier: str, ids: set | None = None,
                  categorical: list[str] | None = None) -> tuple[pd.DataFrame, list[str], int]:
    """Clean target + tier predictors keyed by material_id (optionally restricted to `ids`), for grouped CV.

    Same hygiene as Stage 4's load_matched_frame: booleans -> 0/1, finite-but-float32-overflow values masked to NaN
    (returned count), categorical predictors cast to category dtype."""
    features = pc.read_predictor_list(cfg, tier)
    y = pc.load_target(cfg, target)[["material_id", "reduced_formula", "Experimental", "_source", "value"]]
    if ids is not None:
        y = y[y["material_id"].isin(ids)]
    # read only this target's rows (the tier parquet has ~475k rows; the secondary targets need <= 4.3k)
    X = pd.read_parquet(pc.tier_path(cfg, tier), columns=["material_id"] + features,
                        filters=[("material_id", "in", y["material_id"].tolist())])
    frame = y.merge(X, on="material_id", how="left", validate="one_to_one").reset_index(drop=True)
    for c in [c for c in features if pd.api.types.is_bool_dtype(frame[c])]:
        frame[c] = frame[c].astype(float)
    numeric = [c for c in features if pd.api.types.is_numeric_dtype(frame[c]) and c not in (categorical or [])]
    overflow = frame[numeric].abs() > np.finfo(np.float32).max
    n_overflow = int(overflow.to_numpy().sum())
    if n_overflow:
        frame[numeric] = frame[numeric].mask(overflow)
    for c in categorical or []:
        if c in features:
            frame[c] = frame[c].astype("category")
    return frame, features, n_overflow
