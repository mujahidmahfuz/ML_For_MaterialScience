"""Tests for the Phase 8 conformal / UQ helpers (synthetic data only)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import phase8_uq as uq  # noqa: E402


def test_conformal_quantile_uses_finite_sample_rank():
    scores = np.arange(1.0, 10.0)                       # n = 9
    assert uq.conformal_quantile(scores, 0.2) == 8.0    # ceil((9+1)*0.8) = 8th smallest
    assert uq.conformal_quantile(scores, 0.01) == np.inf  # too few points for 99% coverage


def test_split_conformal_reaches_nominal_coverage_on_exchangeable_data():
    covs = []
    for seed in range(20):
        rng = np.random.default_rng(seed)
        resid_cal, resid_test = rng.normal(size=400), rng.normal(size=4000)
        qhat = uq.conformal_quantile(np.abs(resid_cal), 0.1)
        covs.append(np.mean(np.abs(resid_test) <= qhat))
    assert np.mean(covs) == pytest.approx(0.90, abs=0.01)


def test_grouped_calibration_split_never_splits_a_formula():
    groups = np.repeat([f"F{i}" for i in range(200)], np.random.default_rng(0).integers(1, 6, 200))
    mask = uq.grouped_calibration_split(groups, 0.2, seed=3)
    assert set(groups[mask]).isdisjoint(set(groups[~mask]))
    assert 0.12 < mask.mean() < 0.30
    assert (mask == uq.grouped_calibration_split(groups, 0.2, seed=3)).all()


def test_interval_helpers_and_score():
    y, lo, hi = np.array([1.0, 5.0, 9.0]), np.array([0.0, 0.0, 0.0]), np.array([2.0, 4.0, 10.0])
    assert uq.coverage(y, lo, hi) == pytest.approx(2 / 3)
    # Winkler: width + (2/alpha) * miss distance
    assert uq.winkler_score(y, lo, hi, 0.1) == pytest.approx(np.mean([2.0, 4.0 + 20.0 * 1.0, 10.0]))
    lo2, hi2 = uq.interval_split(np.array([10.0]), 3.0)
    assert (lo2[0], hi2[0]) == (7.0, 13.0)
    lo3, hi3 = uq.interval_normalized(np.array([10.0, 10.0]), np.array([1.0, 4.0]), 2.0)
    assert (hi3 - lo3).tolist() == [4.0, 16.0]


def test_cqr_adapts_width_and_covers_on_heteroscedastic_data():
    rng = np.random.default_rng(1)
    x_cal, x_te = rng.uniform(0.5, 3.0, 3000), rng.uniform(0.5, 3.0, 6000)
    y_cal, y_te = rng.normal(0, x_cal), rng.normal(0, x_te)
    z = 1.645   # true 5% / 95% quantiles of N(0, x)
    scores = uq.cqr_scores(y_cal, -z * x_cal, z * x_cal)
    qhat = uq.conformal_quantile(scores, 0.1)
    lo, hi = uq.cqr_interval(-z * x_te, z * x_te, qhat)
    assert uq.coverage(y_te, lo, hi) == pytest.approx(0.90, abs=0.02)
    assert np.corrcoef(hi - lo, x_te)[0, 1] > 0.99            # width follows the noise level


def test_coverage_by_group_flags_under_covered_groups_with_enough_formulas():
    n = 300
    df = pd.DataFrame({"group": ["A"] * n + ["B"] * n, "formula": [f"a{i}" for i in range(n)] + [f"b{i}" for i in range(n)],
                       "covered": [True] * 290 + [False] * 10 + [True] * 150 + [False] * 150})
    tab = uq.coverage_by_group(df["covered"].to_numpy(), df["group"].to_numpy(), df["formula"].to_numpy(), nominal=0.9, min_formulas=30)
    row = tab.set_index("group")
    assert not row.loc["A", "under_covered"] and row.loc["B", "under_covered"]
    small = uq.coverage_by_group(np.array([False] * 10), np.array(["C"] * 10), np.array([f"c{i}" for i in range(10)]), 0.9, 30)
    assert not small.loc[0, "under_covered"] and small.loc[0, "too_few_formulas"]


def synthetic_classifier(n: int, seed: int, sharpen: float = 1.0, k: int = 3):
    """Labels drawn from the true class probabilities; the model reports softmax(sharpen * logits) (sharpen > 1 = overconfident)."""
    rng = np.random.default_rng(seed)
    logits = rng.normal(0, 1.5, size=(n, k))
    true_p = np.exp(logits) / np.exp(logits).sum(axis=1, keepdims=True)
    y = np.array([rng.choice(k, p=p) for p in true_p])
    z = sharpen * logits
    return np.exp(z) / np.exp(z).sum(axis=1, keepdims=True), y


def test_lac_sets_reach_nominal_coverage_and_shrink_with_alpha():
    p_cal, y_cal = synthetic_classifier(4000, 0)
    p_te, y_te = synthetic_classifier(6000, 1)
    q90 = uq.lac_threshold(p_cal, y_cal, 0.1)
    sets90 = uq.prediction_sets(p_te, q90)
    assert uq.set_coverage(sets90, y_te) == pytest.approx(0.90, abs=0.02)
    sets50 = uq.prediction_sets(p_te, uq.lac_threshold(p_cal, y_cal, 0.5))
    assert uq.mean_set_size(sets50) < uq.mean_set_size(sets90)


def test_ece_is_small_for_calibrated_and_large_for_overconfident_probabilities():
    p_ok, y_ok = synthetic_classifier(20000, 2)
    p_bad, y_bad = synthetic_classifier(20000, 2, sharpen=3.0)
    assert uq.expected_calibration_error(p_ok, y_ok, 15) < 0.03
    assert uq.expected_calibration_error(p_bad, y_bad, 15) > 0.10


def test_temperature_scaling_recovers_the_overconfidence_factor_and_lowers_nll():
    p, y = synthetic_classifier(20000, 3, sharpen=2.0)
    t = uq.fit_temperature(p, y)
    assert t == pytest.approx(2.0, abs=0.25)
    assert uq.negative_log_likelihood(uq.apply_temperature(p, t), y) < uq.negative_log_likelihood(p, y)


def test_brier_and_nll_known_values():
    p, y = np.array([[0.8, 0.2], [0.3, 0.7]]), np.array([0, 1])
    assert uq.brier_score(p, y) == pytest.approx(np.mean([0.2 ** 2 + 0.2 ** 2, 0.3 ** 2 + 0.3 ** 2]))
    assert uq.negative_log_likelihood(p, y) == pytest.approx(-(np.log(0.8) + np.log(0.7)) / 2)


def test_class_conditional_thresholds_protect_a_rare_hard_class():
    rng = np.random.default_rng(4)

    def make(n):
        y = rng.choice(3, size=n, p=[0.55, 0.40, 0.05])
        p = np.full((n, 3), 0.0)
        p[:, 0], p[:, 1] = rng.beta(4, 2, n), rng.beta(4, 2, n)
        p[:, 2] = np.where(y == 2, rng.beta(1.2, 6, n), rng.beta(1, 12, n))     # weak signal for the rare class
        return p / p.sum(axis=1, keepdims=True), y
    p_cal, y_cal = make(20000)
    p_te, y_te = make(20000)
    marginal = uq.prediction_sets(p_te, uq.lac_threshold(p_cal, y_cal, 0.1))
    cond = uq.class_conditional_sets(p_te, uq.class_conditional_thresholds(p_cal, y_cal, 0.1, 3))
    rare_marginal, rare_cond = uq.per_class_coverage(marginal, y_te, 3)[2], uq.per_class_coverage(cond, y_te, 3)[2]
    assert rare_marginal < 0.80 and rare_cond == pytest.approx(0.90, abs=0.04)


def test_formula_bootstrap_interval_brackets_the_estimate_and_respects_clusters():
    rng = np.random.default_rng(2)
    formulas = np.repeat(np.arange(100), 5)
    covered = np.repeat(rng.random(100) < 0.9, 5)       # coverage is constant within a formula
    lo, hi = uq.formula_bootstrap_ci(covered, formulas, n_boot=400, seed=0)
    assert lo <= covered.mean() <= hi
    lo_row, hi_row = uq.formula_bootstrap_ci(covered, np.arange(len(covered)), n_boot=400, seed=0)
    assert (hi - lo) > (hi_row - lo_row)               # ignoring clustering would give a falsely narrow interval
