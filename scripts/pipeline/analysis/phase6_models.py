"""Model building, selection, evaluation and grouped bootstrap shared by Phase 6 Stages 2-4.

Every stage uses the same algorithms, grids, selection rule and metrics from analysis_config.yaml -> models,
so a tier comparison differs only in the feature set.
"""
from __future__ import annotations

import gc
import itertools
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import (HistGradientBoostingClassifier, HistGradientBoostingRegressor,
                              RandomForestClassifier, RandomForestRegressor)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score,
                             mean_absolute_error, mean_squared_error, median_absolute_error,
                             precision_recall_fscore_support, r2_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier, XGBRegressor

import phase6_common as pc

DISPLAY = {"dummy": "Dummy reference", "linear": "Linear / logistic", "random_forest": "Random Forest",
           "gradient_boosting": "Gradient Boosting (hist)", "xgboost": "XGBoost"}
SPLITS = ("train", "validation", "test")


def load_modeling_frame(cfg: dict, target: str, tier: str, split_path: Path) -> tuple[pd.DataFrame, list[str]]:
    """Split assignment + clean target + tier predictors, joined on material_id; fails on any mismatch."""
    features = pc.read_predictor_list(cfg, tier)
    split = pd.read_csv(split_path, usecols=["material_id", "reduced_formula", "split", "Experimental"])
    y = pc.load_target(cfg, target)[["material_id", "value", "_source"]]
    X = pd.read_parquet(pc.tier_path(cfg, tier), columns=["material_id"] + features)
    frame = (split.merge(y, on="material_id", how="inner", validate="one_to_one")
             .merge(X, on="material_id", how="left", validate="one_to_one"))
    if not len(frame) == len(split) == len(y):
        raise ValueError(f"{target}: split ({len(split)}), clean target ({len(y)}) and joined frame ({len(frame)}) differ")
    bool_cols = [c for c in features if pd.api.types.is_bool_dtype(frame[c])]
    frame[bool_cols] = frame[bool_cols].astype(float)  # e.g. oxidation_solution_found (Tier 2) -> 0/1
    return frame, features


def load_matched_frame(cfg: dict, target: str, tier: str, split_path: Path,
                       categorical: list[str] | None = None) -> tuple[pd.DataFrame, list[str], int]:
    """Like load_modeling_frame, but for a Stage 4 matched-population split file whose N is a strict
    subset of the full clean target population (the Tier 3 physics-complete matched set, plan s9) --
    so it checks the join against the split file's own N, not the full clean target's expected_n.
    Returns (frame, features, n_float32_overflow_masked): a small number of Tier 3 physics rows carry
    a finite-but-astronomical value (e.g. p3_elastic_anisotropy ~5.68e110, a near-zero-denominator ratio
    artifact) that overflows to inf when XGBoost casts to float32 internally; those are masked to NaN
    here so the existing missing-value handling (native for boosters, median impute for linear) applies,
    per plan s13 ("any excluded rows/values must be reported with an explicit rule and count")."""
    features = pc.read_predictor_list(cfg, tier)
    split = pd.read_csv(split_path, usecols=["material_id", "reduced_formula", "split", "Experimental"])
    y = pc.load_target(cfg, target)[["material_id", "value", "_source"]]
    X = pd.read_parquet(pc.tier_path(cfg, tier), columns=["material_id"] + features)
    frame = (split.merge(y, on="material_id", how="inner", validate="one_to_one")
             .merge(X, on="material_id", how="left", validate="one_to_one"))
    if len(frame) != len(split):
        raise ValueError(f"{target}/{tier}: matched split ({len(split)}) and joined frame ({len(frame)}) differ")
    bool_cols = [c for c in features if pd.api.types.is_bool_dtype(frame[c])]
    frame[bool_cols] = frame[bool_cols].astype(float)
    numeric_cols = [c for c in features if pd.api.types.is_numeric_dtype(frame[c]) and c not in (categorical or [])]
    overflow = frame[numeric_cols].abs() > np.finfo(np.float32).max
    n_overflow = int(overflow.to_numpy().sum())
    if n_overflow:
        frame[numeric_cols] = frame[numeric_cols].mask(overflow)
    for c in categorical or []:
        if c in features:
            frame[c] = frame[c].astype("category")
    return frame, features, n_overflow


def expand_grid(grid: dict) -> list[dict]:
    keys = list(grid)
    return [dict(zip(keys, values)) for values in itertools.product(*(grid[k] for k in keys))]


def grid_for(cfg: dict, algorithm: str, task: str) -> list[dict]:
    if algorithm == "dummy":
        return [{}]
    spec = cfg["models"]["grids"][algorithm]
    return expand_grid(spec.get(task, spec.get("both")))


def _numeric_pipeline() -> Pipeline:
    return Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])


def build_estimator(algorithm: str, task: str, params: dict, seed: int, categorical: list[str] | None = None):
    """`categorical` (Stage 4 / Tier 3 only: p3_crystal_system, p3_point_group) routes those columns through
    one-hot encoding for linear; gradient_boosting/xgboost consume them natively via category dtype instead
    (the caller must have already cast those columns with load_matched_frame)."""
    clf = task == "classification"
    if algorithm == "dummy":
        return DummyClassifier(strategy="prior") if clf else DummyRegressor(strategy="mean")
    if algorithm == "linear":
        model = (LogisticRegression(max_iter=5000, class_weight="balanced", random_state=seed, **params) if clf
                 else Ridge(random_state=seed, **params))
        if categorical:
            pre = ColumnTransformer([("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                                                        ("ohe", OneHotEncoder(handle_unknown="ignore"))]), categorical)],
                                    remainder=_numeric_pipeline())
            return Pipeline([("pre", pre), ("model", model)])
        return Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", model)])
    if algorithm == "random_forest":
        model = (RandomForestClassifier(class_weight="balanced_subsample", n_jobs=-1, random_state=seed, **params) if clf
                 else RandomForestRegressor(n_jobs=-1, random_state=seed, **params))
        if categorical:
            pre = ColumnTransformer([("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                                                        ("ohe", OneHotEncoder(handle_unknown="ignore"))]), categorical)],
                                    remainder=SimpleImputer(strategy="median"))
            return Pipeline([("pre", pre), ("model", model)])
        return Pipeline([("impute", SimpleImputer(strategy="median")), ("model", model)])
    if algorithm == "gradient_boosting":
        cat_features = "from_dtype" if categorical else None
        return (HistGradientBoostingClassifier(class_weight="balanced", early_stopping=False, random_state=seed,
                                               categorical_features=cat_features, **params) if clf
                else HistGradientBoostingRegressor(early_stopping=False, random_state=seed,
                                                   categorical_features=cat_features, **params))
    if algorithm == "xgboost":
        common = dict(tree_method="hist", n_jobs=-1, random_state=seed, enable_categorical=bool(categorical), **params)
        return (XGBClassifier(objective="multi:softprob", eval_metric="mlogloss", **common) if clf
                else XGBRegressor(objective="reg:squarederror", **common))
    raise ValueError(f"unknown algorithm {algorithm}")


def fit(estimator, algorithm: str, task: str, X: pd.DataFrame, y: np.ndarray):
    if task == "classification" and algorithm == "xgboost":
        return estimator.fit(X, y, sample_weight=compute_sample_weight("balanced", y))
    return estimator.fit(X, y)


def classification_metrics(y, pred, labels, w=None) -> dict:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return {"macro_f1": f1_score(y, pred, labels=labels, average="macro", sample_weight=w, zero_division=0),
                "balanced_accuracy": balanced_accuracy_score(y, pred, sample_weight=w),
                "accuracy": accuracy_score(y, pred, sample_weight=w)}


def regression_metrics(y, pred, w=None) -> dict:
    return {"mae": mean_absolute_error(y, pred, sample_weight=w),
            "rmse": float(np.sqrt(mean_squared_error(y, pred, sample_weight=w))),
            "r2": r2_score(y, pred, sample_weight=w),
            "median_ae": median_absolute_error(y, pred, sample_weight=w)}


def score(task: str, y, pred, labels) -> dict:
    return classification_metrics(y, pred, labels) if task == "classification" else regression_metrics(y, pred)


def fitted_preprocessing(estimator, features: list[str], categorical: list[str] | None = None) -> dict:
    """Train-fitted preprocessing parameters (plan s13); tree boosters handle missing values natively."""
    if not isinstance(estimator, Pipeline):
        return {"preprocessing": "none (native missing-value handling)"}
    if "pre" in estimator.named_steps:  # ColumnTransformer path (categorical predictors present)
        ohe = estimator.named_steps["pre"].named_transformers_["cat"].named_steps["ohe"]
        return {"preprocessing": "ColumnTransformer: categorical -> most_frequent impute + one-hot; "
                                 "remaining columns -> median impute (+ standardize for linear)",
                "categorical_columns": categorical, "one_hot_categories": {c: cats.tolist() for c, cats in
                                                                           zip(categorical, ohe.categories_)}}
    out = {"imputer_median": dict(zip(features, estimator.named_steps["impute"].statistics_.round(8).tolist()))}
    if "scale" in estimator.named_steps:
        sc = estimator.named_steps["scale"]
        out["scaler_mean"] = dict(zip(features, sc.mean_.round(8).tolist()))
        out["scaler_scale"] = dict(zip(features, sc.scale_.round(8).tolist()))
    return out


def run_algorithm(frame: pd.DataFrame, features: list[str], y: np.ndarray, task: str, algorithm: str,
                  cfg: dict, labels=None, categorical: list[str] | None = None) -> dict:
    """Grid on train -> best validation config -> refit on train+validation -> predict validation and test."""
    seed = cfg["random_seed"]
    metric = cfg["models"]["selection_metric"][task]
    higher_is_better = task == "classification"
    idx = {s: (frame["split"] == s).to_numpy() for s in SPLITS}
    X = frame[features]
    selection = []
    for params in grid_for(cfg, algorithm, task):
        t0 = time.perf_counter()
        est = fit(build_estimator(algorithm, task, params, seed, categorical), algorithm, task, X[idx["train"]], y[idx["train"]])
        val_pred = est.predict(X[idx["validation"]])
        del est  # free each grid model before the next fit: large forests otherwise double peak memory
        gc.collect()
        selection.append({"params": params, "val_score": score(task, y[idx["validation"]], val_pred, labels)[metric],
                          "fit_seconds": round(time.perf_counter() - t0, 1), "val_pred": val_pred})
    best = (max if higher_is_better else min)(selection, key=lambda r: r["val_score"])
    trainval = idx["train"] | idx["validation"]
    t0 = time.perf_counter()
    final = fit(build_estimator(algorithm, task, best["params"], seed, categorical), algorithm, task, X[trainval], y[trainval])
    refit_seconds = round(time.perf_counter() - t0, 1)
    result = {"algorithm": algorithm, "selection_metric": metric, "best_params": best["params"],
              "val_score": best["val_score"], "val_pred": best["val_pred"], "test_pred": final.predict(X[idx["test"]]),
              "refit_seconds": refit_seconds, "preprocessing": fitted_preprocessing(final, features, categorical),
              "selection_table": [{"params": r["params"], f"val_{metric}": r["val_score"], "fit_seconds": r["fit_seconds"]}
                                  for r in selection]}
    model = final.named_steps["model"] if isinstance(final, Pipeline) else final
    if hasattr(model, "feature_importances_"):
        result["feature_importance"] = dict(zip(features, np.asarray(model.feature_importances_, dtype=float)))
    return result


def paired_group_bootstrap(y, preds: dict, groups, metric_fn, keys: list[str], n: int, seed: int,
                           ci: float = 0.95) -> tuple[dict, dict]:
    """Percentile CIs from resampling whole reduced_formula groups. The same draws are used for every model, so
    differences between models (or tiers) are paired. Returns (CIs, raw bootstrap samples)."""
    codes, uniques = pd.factorize(pd.Series(groups))
    n_groups = len(uniques)
    rng = np.random.default_rng(seed)
    samples = {m: {k: [] for k in keys} for m in preds}
    for _ in range(n):
        weights = np.bincount(rng.integers(0, n_groups, n_groups), minlength=n_groups)[codes].astype(float)
        for m, pred in preds.items():
            values = metric_fn(y, pred, weights)
            for k in keys:
                samples[m][k].append(values[k])
    lo, hi = (1 - ci) / 2, 1 - (1 - ci) / 2
    cis = {m: {k: (float(np.quantile(v, lo)), float(np.quantile(v, hi))) for k, v in d.items()} for m, d in samples.items()}
    return cis, samples


def per_class_table(y, pred, labels, names) -> pd.DataFrame:
    p, r, f, s = precision_recall_fscore_support(y, pred, labels=labels, zero_division=0)
    return pd.DataFrame({"class": names, "precision": p, "recall": r, "f1": f, "support": s})


def normalized_confusion(y, pred, labels) -> tuple[np.ndarray, np.ndarray]:
    cm = confusion_matrix(y, pred, labels=labels)
    return cm, cm / cm.sum(axis=1, keepdims=True).clip(min=1)
