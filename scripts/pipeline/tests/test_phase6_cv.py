"""Tests for EDA/src/phase6_cv.py (formula-grouped repeated CV used by Stage 7)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

EDA_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDA_ROOT / "src"))
import phase6_common as pc  # noqa: E402
import phase6_cv as cv  # noqa: E402


def _groups(n_groups=60, seed=0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    sizes = rng.integers(1, 6, n_groups)
    return np.repeat([f"F{i}" for i in range(n_groups)], sizes)


def test_group_folds_keep_every_group_in_exactly_one_fold():
    groups = _groups()
    folds = cv.group_folds(groups, 5, seed=1)
    assert set(folds) == set(range(5))
    per_group = pd.Series(folds).groupby(groups).nunique()
    assert (per_group == 1).all()


def test_group_folds_are_size_balanced_and_deterministic():
    groups = _groups()
    folds = cv.group_folds(groups, 5, seed=1)
    sizes = np.bincount(folds)
    assert sizes.max() - sizes.min() <= 5   # largest group has 5 rows
    np.testing.assert_array_equal(folds, cv.group_folds(groups, 5, seed=1))
    assert not np.array_equal(folds, cv.group_folds(groups, 5, seed=2))


def test_inner_split_is_group_disjoint_and_close_to_requested_fraction():
    groups = _groups(200)
    labels = cv.inner_split_labels(groups, 0.2, seed=3)
    assert set(labels) == {"train", "validation"}
    assert (pd.Series(labels).groupby(groups).nunique() == 1).all()
    assert abs((labels == "validation").mean() - 0.2) < 0.05


def test_weighted_rank_corr_matches_spearman_for_unit_weights():
    rng = np.random.default_rng(0)
    y = rng.normal(size=300)
    pred = y + rng.normal(scale=0.5, size=300)
    expected = pd.Series(y).corr(pd.Series(pred), method="spearman")
    assert cv.weighted_rank_corr(y, pred, np.ones(300)) == pytest.approx(expected, abs=1e-9)


def test_weighted_rank_corr_ignores_zero_weight_rows():
    y = np.array([1.0, 2.0, 3.0, 4.0, 100.0])
    pred = np.array([1.0, 2.0, 3.0, 4.0, -50.0])
    w = np.array([1.0, 1.0, 1.0, 1.0, 0.0])
    assert cv.weighted_rank_corr(y, pred, w) > 0.99


def test_signed_log_is_odd_monotone_and_zero_preserving():
    x = np.array([-1e6, -10.0, 0.0, 10.0, 1e6])
    out = cv.signed_log10(x)
    assert out[2] == 0.0
    np.testing.assert_allclose(out, -out[::-1])
    assert np.all(np.diff(out) > 0)


def test_cv_predictions_cover_every_row_each_repeat_and_learn_a_linear_signal():
    cfg = pc.load_config()
    rng = np.random.default_rng(0)
    groups = _groups(120)
    n = len(groups)
    frame = pd.DataFrame({"reduced_formula": groups, "a": rng.normal(size=n), "b": rng.normal(size=n)})
    y = 3 * frame["a"].to_numpy() - 2 * frame["b"].to_numpy() + rng.normal(scale=0.1, size=n)
    oof, chosen = cv.cv_predictions(frame, ["a", "b"], y, "linear", cfg, n_folds=4, n_repeats=2, seed=5)
    assert oof.shape == (2, n)
    assert np.isfinite(oof).all()
    for r in range(2):
        assert 1 - ((y - oof[r]) ** 2).sum() / ((y - y.mean()) ** 2).sum() > 0.95
    assert len(chosen) == 2 * 4   # one selected-hyperparameter record per outer fold and repeat


def test_cv_predictions_dummy_predicts_training_mean_without_leaking_the_test_fold():
    cfg = pc.load_config()
    groups = _groups(80)
    n = len(groups)
    frame = pd.DataFrame({"reduced_formula": groups, "a": np.zeros(n)})
    y = np.arange(n, dtype=float)
    oof, _ = cv.cv_predictions(frame, ["a"], y, "dummy", cfg, n_folds=4, n_repeats=1, seed=1)
    assert np.isfinite(oof).all()
    # leakage guard: the prediction for a row must not be the global mean (its own fold is excluded from training)
    assert not np.allclose(oof[0], y.mean())
