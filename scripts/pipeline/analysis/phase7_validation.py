"""Phase 7 publication-readiness validation: multi-split matched Tier 1/2/3 experiments and paired statistics.

Reuses the Phase 6 estimators, grids, selection rule and metrics unchanged (phase6_models.run_algorithm); only the
split assignment, the feature-set variants and the statistics are new. Nothing here writes into Phase 6 folders.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats as sps
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import phase6_common as pc
import phase6_models as pm

PHASE7_CONFIG = pc.EDA_ROOT / "00_config" / "phase7_config.yaml"
SPLIT_NAMES = ("train", "validation", "test")
HIGHER_BETTER = {"r2"}
TIER_PAIRS = (("tier1", "tier2"), ("tier2", "tier3"), ("tier1", "tier3"))
LINEAR_CLIP = "linear_clip"
# Corrective-control column (not in the feature repository): number of sites in the MP cell = p3_volume / p3_volume_per_atom.
DERIVED_NSITES_COLUMN = "derived_nsites_in_mp_cell"


def load_phase7_config() -> dict:
    with open(PHASE7_CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ----------------------------------------------------------------------------------------------- split generation
def random_group_split(groups, values, fractions: dict, seed: int, n_bins: int = 5, tolerance: float = 0.25) -> np.ndarray:
    """Seeded random, size-aware, target-stratified assignment of whole reduced_formula groups to train/validation/test.

    Mirrors the frozen-split rule (strata = quantile bins of the formula-mean target, row fractions respected) but is
    randomised so different seeds give genuinely different splits: groups are visited by descending log2 size band
    (random order inside a band) and each is sent to a split drawn with probability proportional to that split's
    remaining row deficit, among the splits it still fits in (capacity = target rows x (1 + tolerance))."""
    groups = pd.Series(np.asarray(groups)).astype(str)
    values = pd.Series(np.asarray(values, dtype=float))
    frac = np.array([fractions[s] for s in SPLIT_NAMES], dtype=float)
    sizes = groups.value_counts()
    means = values.groupby(groups.to_numpy()).mean().loc[sizes.index]
    q = max(1, min(n_bins, len(sizes)))
    strata = pd.qcut(means.rank(method="first"), q=q, labels=False)
    rng = np.random.default_rng(seed)
    split_of = {}
    for b in sorted(strata.unique()):
        names = strata.index[strata == b].to_numpy()
        sz = sizes.loc[names].to_numpy()
        band = np.floor(np.log2(sz)).astype(int)
        order = np.lexsort((rng.random(len(names)), -band))
        target = frac * sz.sum()
        filled = np.zeros(3)
        for i in order:
            deficit = target - filled
            fits = filled + sz[i] <= target * (1.0 + tolerance)
            if not fits.any():
                k = int(np.argmax(deficit))
            else:
                p = np.clip(deficit, 0, None) * fits
                if p.sum() <= 0:
                    p = frac * fits
                k = int(rng.choice(3, p=p / p.sum()))
            split_of[names[i]] = SPLIT_NAMES[k]
            filled[k] += sz[i]
    return groups.map(split_of).to_numpy()


def split_seed(cfg7: dict, i: int) -> int:
    return int(cfg7["multisplit"]["base_seed"]) + int(i)


def split_labels_for(frame: pd.DataFrame, cfg7: dict, split_id) -> np.ndarray:
    """Frozen Phase 6 labels for split_id == 'frozen', else the prespecified random split number `split_id`."""
    if split_id == "frozen":
        return frame["split"].to_numpy()
    ms = cfg7["multisplit"]
    return random_group_split(frame["reduced_formula"], frame["value"], ms["fractions"], split_seed(cfg7, int(split_id)),
                              ms["n_strata_bins"], ms["capacity_tolerance"])


def assert_formula_disjoint(formulas, labels) -> None:
    n = pd.Series(np.asarray(labels)).groupby(np.asarray(formulas)).nunique()
    if (n > 1).any():
        raise AssertionError(f"{int((n > 1).sum())} reduced_formula groups span more than one split")


def split_composition(frame: pd.DataFrame, labels: np.ndarray, split_id, extreme_k: float | None = None) -> list[dict]:
    rows = []
    for s in SPLIT_NAMES:
        part = frame[labels == s]
        row = {"split_id": split_id, "partition": s, "n_rows": len(part), "pct_rows": 100 * len(part) / len(frame),
               "n_distinct_formulas": part["reduced_formula"].nunique(), "target_mean": part["value"].mean(),
               "target_median": part["value"].median(), "target_p90": part["value"].quantile(0.90),
               "target_max": part["value"].max(),
               "max_formula_share_pct": 100 * part["reduced_formula"].value_counts(normalize=True).iloc[0]}
        if extreme_k is not None:
            row["n_above_extreme"] = int((part["value"] > extreme_k).sum())
        rows.append(row)
    return rows


# ----------------------------------------------------------------------------------------------- feature variants
def variant_features(cfg: dict, cfg7: dict) -> dict[str, list[str]]:
    """tier1/tier2/tier3 predictor lists plus the labelled Tier 3 restricted variants (Tier 3 minus the listed columns)."""
    tier3 = pc.read_predictor_list(cfg, "tier3")
    out = {t: pc.read_predictor_list(cfg, t) for t in ("tier1", "tier2", "tier3")}
    for name, drop in cfg7["tier3_restricted_variants"].items():
        unknown = set(drop) - set(tier3)
        if unknown:
            raise ValueError(f"{name}: columns not in Tier 3 predictors: {sorted(unknown)}")
        out[name] = [c for c in tier3 if c not in set(drop)]
    for name, add in cfg7.get("tier2_plus_variants", {}).items():
        unknown = set(add) - set(tier3)
        if unknown:
            raise ValueError(f"{name}: columns not in Tier 3 predictors: {sorted(unknown)}")
        out[name] = out["tier2"] + [c for c in tier3 if c in set(add)]
    return out


# ----------------------------------------------------------------------------------------------- diagnostic linear model
class QuantileClipper(BaseEstimator, TransformerMixin):
    """Clip each column to the [lower, upper] percentiles of the TRAINING data only (fit/transform split, no leakage)."""

    def __init__(self, lower: float = 1.0, upper: float = 99.0):
        self.lower, self.upper = lower, upper

    def fit(self, X, y=None):
        X = np.asarray(X, dtype=float)
        self.low_ = np.nanpercentile(X, self.lower, axis=0)
        self.high_ = np.nanpercentile(X, self.upper, axis=0)
        return self

    def transform(self, X):
        return np.clip(np.asarray(X, dtype=float), self.low_, self.high_)


def _clip_numeric_pipeline() -> Pipeline:
    return Pipeline([("impute", SimpleImputer(strategy="median")), ("clip", QuantileClipper()), ("scale", StandardScaler())])


def build_linear_clip(params: dict, seed: int, categorical: list[str] | None = None):
    """Ridge identical to Phase 6 'linear' except that numeric columns are clipped to train-fold 1st/99th percentiles."""
    model = Ridge(random_state=seed, **params)
    if categorical:
        pre = ColumnTransformer([("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                                                    ("ohe", OneHotEncoder(handle_unknown="ignore"))]), categorical)],
                                remainder=_clip_numeric_pipeline())
        return Pipeline([("pre", pre), ("model", model)])
    return Pipeline([("impute", SimpleImputer(strategy="median")), ("clip", QuantileClipper()),
                     ("scale", StandardScaler()), ("model", model)])


# XGBoost's multithreaded 'hist' trees are deterministic only for a fixed thread count (floating-point summation order):
# on the frozen Curie split Tier 1 MAE is 274.6 / 284.9 / 273.9 K with 1 / 4 / 16 threads. Phase 6 ran with n_jobs=-1 on this
# 16-thread machine, so Phase 7 pins 16 explicitly to reproduce it independent of OMP_NUM_THREADS (which only throttles sklearn).
XGB_N_JOBS = 16


def install_diagnostic_algorithm() -> None:
    """Register 'linear_clip' with the Phase 6 runner (same grid/selection rule as 'linear') and pin the XGBoost thread
    count (see XGB_N_JOBS); idempotent."""
    if getattr(pm, "_phase7_patched", False):
        return
    orig_build, orig_grid = pm.build_estimator, pm.grid_for

    def build(algorithm, task, params, seed, categorical=None):
        if algorithm == LINEAR_CLIP:
            return build_linear_clip(params, seed, categorical)
        est = orig_build(algorithm, task, params, seed, categorical)
        if algorithm == "xgboost":
            est.set_params(n_jobs=XGB_N_JOBS)
        return est

    def grid(cfg, algorithm, task):
        return orig_grid(cfg, "linear" if algorithm == LINEAR_CLIP else algorithm, task)

    pm.build_estimator, pm.grid_for, pm._phase7_patched = build, grid, True


# ----------------------------------------------------------------------------------------------- model runs
def run_variants(frame: pd.DataFrame, labels: np.ndarray, variants: dict[str, list[str]], algorithms: list[str],
                 cfg: dict, categorical: list[str]) -> tuple[pd.DataFrame, list[dict]]:
    """Fit every variant x algorithm on one split (grid on train -> best validation RMSE -> refit train+val -> score test).
    Returns (long test-prediction table, one selection record per fit)."""
    install_diagnostic_algorithm()
    work = frame.assign(split=labels)
    y = work["value"].to_numpy(dtype=float)
    test = labels == "test"
    pred_rows, records = [], []
    for variant, feats in variants.items():
        cats = [c for c in categorical if c in feats] or None
        for alg in algorithms:
            res = pm.run_algorithm(work, feats, y, "regression", alg, cfg, categorical=cats)
            pred_rows.append(pd.DataFrame({"variant": variant, "algorithm": alg,
                                           "material_id": work.loc[test, "material_id"].to_numpy(),
                                           "reduced_formula": work.loc[test, "reduced_formula"].to_numpy(),
                                           "y_true": y[test], "y_pred": np.asarray(res["test_pred"], dtype=float)}))
            records.append({"variant": variant, "algorithm": alg, "n_features": len(feats),
                            "best_params": str(res["best_params"]), "val_rmse": res["val_score"],
                            "refit_seconds": res["refit_seconds"]})
    return pd.concat(pred_rows, ignore_index=True), records


# ----------------------------------------------------------------------------------------------- statistics
def formula_stats(codes: np.ndarray, y: np.ndarray, pred: np.ndarray, n_groups: int) -> dict[str, np.ndarray]:
    """Per-formula sufficient statistics for every weighted regression metric: n, sum y, sum y^2, sum |e|, sum e^2."""
    e = pred - y
    f = lambda v: np.bincount(codes, weights=v, minlength=n_groups)  # noqa: E731
    return {"n": f(np.ones(len(y))), "sy": f(y), "syy": f(y * y), "sae": f(np.abs(e)), "sse": f(e * e)}


def add_stats(a: dict, b: dict) -> dict:
    return {k: a[k] + b[k] for k in a}


def metrics_from_stats(st: dict, weights: np.ndarray) -> dict[str, np.ndarray]:
    """MAE, RMSE, R2 and formula-macro MAE under formula weights (B x G; one row of ones gives the point estimate)."""
    w = np.atleast_2d(weights)
    sw = w @ st["n"]
    mae = (w @ st["sae"]) / sw
    sse = w @ st["sse"]
    rmse = np.sqrt(sse / sw)
    sst = (w @ st["syy"]) - (w @ st["sy"]) ** 2 / sw
    present = (st["n"] > 0).astype(float)
    macro = (w @ np.divide(st["sae"], st["n"], out=np.zeros_like(st["sae"]), where=st["n"] > 0)) / (w @ present)
    return {"mae": mae, "rmse": rmse, "r2": 1.0 - sse / sst, "mae_formula_macro": macro}


def bootstrap_weights(n_groups: int, n_boot: int, seed: int) -> np.ndarray:
    """B x G multinomial formula counts: each row resamples whole reduced_formula groups with replacement."""
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n_groups, size=(n_boot, n_groups))
    out = np.zeros((n_boot, n_groups))
    for b in range(n_boot):
        out[b] = np.bincount(idx[b], minlength=n_groups)
    return out


def ci(samples: np.ndarray, level: float = 0.95) -> tuple[float, float]:
    lo, hi = (1 - level) / 2, 1 - (1 - level) / 2
    return float(np.quantile(samples, lo)), float(np.quantile(samples, hi))


def improvement(metric: str, from_value, to_value):
    """Sign-adjusted: positive = the deeper tier is better (lower error, higher R2)."""
    return (to_value - from_value) if metric in HIGHER_BETTER else (from_value - to_value)


def sign_test_p(n_positive: int, n_total: int) -> float:
    return float(sps.binomtest(n_positive, n_total, 0.5).pvalue) if n_total else float("nan")


def t_interval(values: np.ndarray, level: float = 0.95) -> tuple[float, float]:
    """Descriptive t interval of the across-split mean (splits overlap in materials, so it is not an inferential CI)."""
    v = np.asarray(values, dtype=float)
    if len(v) < 2:
        return float("nan"), float("nan")
    half = sps.t.ppf(0.5 + level / 2, len(v) - 1) * v.std(ddof=1) / np.sqrt(len(v))
    return float(v.mean() - half), float(v.mean() + half)


def output_dir(cfg7: dict, version: str = "v1.2") -> Path:
    """Phase 7 output folder for an analysis-dataset version (the configured path is the v1.2 one)."""
    return Path(pc.load_config()["paths"]["project_root"]) / cfg7["output_dir"].replace("v1.2", version)


def dataset_cfg(version: str = "v1.2") -> dict:
    """Phase 6 config, with the Curie/ordering target folder and expected N switched to v1.3 when requested.

    v1.3 only changes the Curie and ordering targets (EDA/datasets/v1.3, rules in 00_config/v1_3_curation_rules.yaml); features,
    tiers and every other target are the v1.2 files. The frozen analysis_config.yaml on disk is never modified."""
    cfg = pc.load_config()
    if version == "v1.2":
        return cfg
    if version not in ("v1.3", "v1.4"):
        raise ValueError(f"unknown dataset version {version}")
    import json
    manifest = json.loads((pc.EDA_ROOT / "datasets" / "v1.3" / "MANIFEST_v1.3.json").read_text(encoding="utf-8"))
    cfg["paths"]["target_harmonization_dir"] = "EDA/datasets/v1.3/targets"
    cfg["targets"]["curie"]["expected_n"] = manifest["curie"]["v1_3_primary_n"]
    cfg["targets"]["ordering"]["expected_n"] = manifest["ordering"]["v1_3_n"]
    cfg["analysis_dataset_version"] = "v1.3"
    if version == "v1.4":     # v1.4 = v1.3 + R10 secondary-target screens (Ms-mass, Ms-volume, K1); Curie/ordering/Ms-moment files are identical copies
        m14 = json.loads((pc.EDA_ROOT / "datasets" / "v1.4" / "MANIFEST_v1.4.json").read_text(encoding="utf-8"))
        cfg["paths"]["target_harmonization_dir"] = "EDA/datasets/v1.4/targets"
        cfg["targets"]["ms_mass"]["expected_n"] = m14["ms"]["ms_mass"]["v1_4_n"]
        cfg["targets"]["ms_volume"]["expected_n"] = m14["ms"]["ms_volume"]["v1_4_n"]
        cfg["targets"]["k1"]["expected_n"] = m14["k1"]["v1_4_n"]
        cfg["analysis_dataset_version"] = "v1.4"
    return cfg


def split_dir(version: str = "v1.2") -> Path:
    return pc.EDA_ROOT / "02_splits" / version
