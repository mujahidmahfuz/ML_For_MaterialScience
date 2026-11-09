"""Tests for EDA/src/phase6_interp.py (descriptor families, TreeSHAP wrapper)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xgboost as xgb
from xgboost import XGBClassifier, XGBRegressor

EDA_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDA_ROOT / "src"))
import phase6_interp as pi  # noqa: E402


def _predictors(tier: str) -> list[str]:
    path = EDA_ROOT / "00_config" / f"{tier}_predictors.txt"
    return [c for c in path.read_text(encoding="utf-8").splitlines() if c.strip()]


def test_every_tier3_predictor_has_exactly_one_known_family():
    feats = _predictors("tier3")
    fam = pi.family_map(feats)
    assert len(fam) == len(feats) == len(set(feats))
    assert set(fam) <= set(pi.FAMILY_ORDER)


def test_physics_families_cover_exactly_the_tier3_additions():
    tier2 = _predictors("tier2")
    added = [f for f in _predictors("tier3") if f not in tier2]
    assert set(pi.family_map(added)) == set(pi.PHYSICS_FAMILIES)
    assert not set(pi.family_map(tier2)) & set(pi.PHYSICS_FAMILIES)


def test_unknown_feature_raises_instead_of_being_silently_dropped():
    with pytest.raises(KeyError):
        pi.feature_family("some_new_descriptor")


def test_family_share_sums_to_one_and_follows_family_order():
    imp = pd.Series({"basic_comp__fraction_Fe": 2.0, "basic_comp__fraction_O": 1.0, "p3_band_gap": 1.0})
    share = pi.family_share(imp)
    assert share.sum() == pytest.approx(1.0)
    assert list(share.index) == [pi.MAGNETIC_ELEMENTS, pi.LIGHT_ELEMENTS, pi.ELECTRONIC]
    assert share[pi.MAGNETIC_ELEMENTS] == pytest.approx(0.5)


def _frame(n=300, seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    X = pd.DataFrame({"a": rng.normal(size=n), "b": rng.normal(size=n), "c": rng.normal(size=n)})
    X.loc[::7, "b"] = np.nan   # native missing-value handling
    return X


def test_tree_shap_regression_reconstructs_the_margin():
    X = _frame()
    y = 2 * X["a"] + np.nan_to_num(X["b"]) ** 2
    model = XGBRegressor(n_estimators=30, max_depth=3, tree_method="hist", random_state=0).fit(X, y)
    values, bias = pi.tree_shap(model, X)
    assert values.shape == (len(X), 3)
    np.testing.assert_allclose(values.sum(axis=1) + bias, model.predict(X), atol=1e-3)
    imp = pi.global_importance(values, list(X.columns))
    assert imp["c"] < imp["a"]


def test_tree_shap_multiclass_shape_and_margin():
    X = _frame()
    y = np.digitize(X["a"] + 0.5 * np.nan_to_num(X["b"]), [-0.5, 0.5])   # 3 classes
    model = XGBClassifier(n_estimators=20, max_depth=3, tree_method="hist", random_state=0).fit(X, y)
    values, bias = pi.tree_shap(model, X)
    assert values.shape == (len(X), 3, 3)
    margin = model.get_booster().predict(xgb.DMatrix(X), output_margin=True)
    np.testing.assert_allclose(values.sum(axis=2) + bias, margin, atol=1e-3)
    assert pi.global_importance(values, list(X.columns)).shape == (3,)


def test_tree_shap_accepts_category_dtype_columns():
    X = _frame()
    X["k"] = pd.Categorical(np.where(X["a"] > 0, "cubic", "hexagonal"))
    y = 3.0 * (X["k"] == "cubic").astype(float) + X["c"]
    model = XGBRegressor(n_estimators=30, max_depth=3, tree_method="hist", enable_categorical=True, random_state=0).fit(X, y)
    values, bias = pi.tree_shap(model, X)
    np.testing.assert_allclose(values.sum(axis=1) + bias, model.predict(X), atol=1e-3)
