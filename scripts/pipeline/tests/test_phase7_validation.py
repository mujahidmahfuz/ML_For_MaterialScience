"""Tests for the Phase 7 validation helpers (synthetic data only)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import phase7_validation as p7  # noqa: E402

FRACTIONS = {"train": 0.70, "validation": 0.15, "test": 0.15}


def synthetic_groups(n_groups=300, seed=0):
    rng = np.random.default_rng(seed)
    sizes = np.maximum(1, (rng.pareto(1.5, n_groups) * 3).astype(int))
    groups = np.repeat([f"F{i}" for i in range(n_groups)], sizes)
    values = np.repeat(rng.normal(300, 100, n_groups), sizes)
    return groups, values


def test_split_keeps_every_formula_in_one_partition():
    groups, values = synthetic_groups()
    labels = p7.random_group_split(groups, values, FRACTIONS, seed=1)
    p7.assert_formula_disjoint(groups, labels)
    assert set(labels) == {"train", "validation", "test"}


def test_split_row_fractions_are_close_to_target():
    groups, values = synthetic_groups(600)
    labels = p7.random_group_split(groups, values, FRACTIONS, seed=2)
    share = pd.Series(labels).value_counts(normalize=True)
    assert share["train"] == pytest.approx(0.70, abs=0.06)
    assert share["test"] == pytest.approx(0.15, abs=0.05)


def test_split_is_reproducible_and_seed_dependent():
    groups, values = synthetic_groups()
    a = p7.random_group_split(groups, values, FRACTIONS, seed=3)
    b = p7.random_group_split(groups, values, FRACTIONS, seed=3)
    c = p7.random_group_split(groups, values, FRACTIONS, seed=4)
    assert (a == b).all()
    assert (a != c).any()


def test_disjointness_check_detects_leakage():
    with pytest.raises(AssertionError):
        p7.assert_formula_disjoint(np.array(["A", "A", "B"]), np.array(["train", "test", "train"]))


def test_formula_stats_metrics_match_sklearn_with_unit_weights():
    rng = np.random.default_rng(5)
    codes = rng.integers(0, 20, 400)
    y = rng.normal(size=400) * 10
    pred = y + rng.normal(size=400) * 3
    m = p7.metrics_from_stats(p7.formula_stats(codes, y, pred, 20), np.ones((1, 20)))
    assert m["mae"][0] == pytest.approx(mean_absolute_error(y, pred))
    assert m["rmse"][0] == pytest.approx(np.sqrt(mean_squared_error(y, pred)))
    assert m["r2"][0] == pytest.approx(r2_score(y, pred))


def test_weighted_metrics_equal_repeating_rows():
    rng = np.random.default_rng(6)
    codes = rng.integers(0, 8, 120)
    y, pred = rng.normal(size=120), rng.normal(size=120)
    counts = rng.integers(0, 4, 8).astype(float)
    m = p7.metrics_from_stats(p7.formula_stats(codes, y, pred, 8), counts[None, :])
    rep = np.repeat(np.arange(120), counts[codes].astype(int))
    assert m["mae"][0] == pytest.approx(mean_absolute_error(y[rep], pred[rep]))
    assert m["r2"][0] == pytest.approx(r2_score(y[rep], pred[rep]))


def test_formula_macro_mae_averages_per_formula_first():
    codes = np.array([0, 0, 0, 1])
    y = np.zeros(4)
    pred = np.array([1.0, 1.0, 1.0, 5.0])
    m = p7.metrics_from_stats(p7.formula_stats(codes, y, pred, 2), np.ones((1, 2)))
    assert m["mae"][0] == pytest.approx(2.0)
    assert m["mae_formula_macro"][0] == pytest.approx(3.0)


def test_bootstrap_weights_resample_whole_groups():
    w = p7.bootstrap_weights(50, 200, seed=7)
    assert w.shape == (200, 50)
    assert (w.sum(axis=1) == 50).all()


def test_improvement_sign_convention():
    assert p7.improvement("mae", 2.0, 1.5) == pytest.approx(0.5)
    assert p7.improvement("r2", 0.2, 0.3) == pytest.approx(0.1)


def test_quantile_clipper_uses_training_percentiles_only():
    train = np.arange(101, dtype=float).reshape(-1, 1)
    clip = p7.QuantileClipper(1.0, 99.0).fit(train)
    out = clip.transform(np.array([[-1000.0], [50.0], [1e9]]))
    assert out[0, 0] == pytest.approx(1.0) and out[1, 0] == 50.0 and out[2, 0] == pytest.approx(99.0)


def test_t_interval_and_sign_test():
    lo, hi = p7.t_interval(np.array([1.0, 2.0, 3.0, 2.0, 2.5]))
    assert lo < 2.1 < hi
    assert p7.sign_test_p(10, 10) < 0.01
    assert p7.sign_test_p(5, 10) == pytest.approx(1.0)
