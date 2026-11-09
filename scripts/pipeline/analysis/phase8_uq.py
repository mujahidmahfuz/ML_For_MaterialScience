"""Phase 8 uncertainty-quantification helpers: split-conformal regression intervals and their evaluation.

Methods (see EDA/11_phase8_xai_uq/PLAN.md): split conformal (constant width), normalized conformal (width scaled by a difficulty
estimate) and conformalized quantile regression (CQR, Romano et al. 2019). Calibration sets are formed from whole formulas so that
calibration, proper-training and test data share no reduced_formula. All functions are pure numpy/pandas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

UNDER_COVERAGE_TOLERANCE = 0.05     # a subgroup is flagged when its coverage is more than 5 points below nominal ...
MIN_FORMULAS_FOR_FLAG = 30          # ... and it has at least this many distinct formulas


def conformal_quantile(scores, alpha: float) -> float:
    """Finite-sample conformal quantile: the ceil((n+1)(1-alpha))-th smallest score (inf when n is too small for the level)."""
    s = np.sort(np.asarray(scores, dtype=float))
    k = int(np.ceil((len(s) + 1) * (1.0 - alpha)))
    return np.inf if k > len(s) else float(s[k - 1])


def grouped_calibration_split(groups, fraction: float, seed: int) -> np.ndarray:
    """Boolean calibration mask built from whole groups (random order, taken until `fraction` of the rows is reached)."""
    labels = np.asarray(groups).astype(str)
    uniq, codes = np.unique(labels, return_inverse=True)
    sizes = np.bincount(codes)
    chosen = np.zeros(len(uniq), dtype=bool)
    taken, target = 0, fraction * len(labels)
    for g in np.random.default_rng(seed).permutation(len(uniq)):
        if taken >= target:
            break
        chosen[g] = True
        taken += sizes[g]
    return chosen[codes]


def interval_split(pred, qhat: float) -> tuple[np.ndarray, np.ndarray]:
    pred = np.asarray(pred, dtype=float)
    return pred - qhat, pred + qhat


def interval_normalized(pred, sigma, qhat: float) -> tuple[np.ndarray, np.ndarray]:
    pred, sigma = np.asarray(pred, dtype=float), np.asarray(sigma, dtype=float)
    return pred - qhat * sigma, pred + qhat * sigma


def cqr_scores(y, q_lo, q_hi) -> np.ndarray:
    """CQR conformity score: how far y lies outside the predicted [q_lo, q_hi] band (negative when inside)."""
    y = np.asarray(y, dtype=float)
    return np.maximum(np.asarray(q_lo, dtype=float) - y, y - np.asarray(q_hi, dtype=float))


def cqr_interval(q_lo, q_hi, qhat: float) -> tuple[np.ndarray, np.ndarray]:
    return np.asarray(q_lo, dtype=float) - qhat, np.asarray(q_hi, dtype=float) + qhat


def covered_mask(y, lo, hi) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    return (y >= np.asarray(lo)) & (y <= np.asarray(hi))


def coverage(y, lo, hi) -> float:
    return float(covered_mask(y, lo, hi).mean())


def winkler_score(y, lo, hi, alpha: float) -> float:
    """Mean interval score: width plus (2/alpha) times the distance by which y falls outside the interval (lower is better)."""
    y, lo, hi = (np.asarray(a, dtype=float) for a in (y, lo, hi))
    penalty = (2.0 / alpha) * (np.maximum(lo - y, 0.0) + np.maximum(y - hi, 0.0))
    return float(np.mean((hi - lo) + penalty))


def formula_bootstrap_ci(covered, formulas, n_boot: int = 1000, seed: int = 0, level: float = 0.95) -> tuple[float, float]:
    """Percentile CI of the coverage rate, resampling whole formulas (rows of one formula are not independent)."""
    covered = np.asarray(covered, dtype=float)
    codes = pd.factorize(pd.Series(np.asarray(formulas)))[0]
    n_g = np.bincount(codes).astype(float)
    hits = np.bincount(codes, weights=covered)
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(n_g), size=(n_boot, len(n_g)))
    weights = np.stack([np.bincount(d, minlength=len(n_g)) for d in draws]).astype(float)
    rate = (weights @ hits) / (weights @ n_g)
    lo, hi = (1 - level) / 2, 1 - (1 - level) / 2
    return float(np.quantile(rate, lo)), float(np.quantile(rate, hi))


# ------------------------------------------------------------------------------------------ classification
def true_class_prob(probs, y) -> np.ndarray:
    probs, y = np.asarray(probs, dtype=float), np.asarray(y, dtype=int)
    return probs[np.arange(len(y)), y]


def lac_threshold(probs, y, alpha: float) -> float:
    """Least-ambiguous-set conformal threshold on the score 1 - p(true class) (marginal coverage guarantee)."""
    return conformal_quantile(1.0 - true_class_prob(probs, y), alpha)


def prediction_sets(probs, qhat) -> np.ndarray:
    """Boolean (n, K) membership: class k is in the set when 1 - p_k <= threshold (a scalar, or one threshold per class)."""
    return (1.0 - np.asarray(probs, dtype=float)) <= np.asarray(qhat, dtype=float)


def class_conditional_thresholds(probs, y, alpha: float, n_classes: int) -> np.ndarray:
    """One conformal threshold per true class (Mondrian): gives per-class coverage, which marginal conformal does not."""
    scores, y = 1.0 - true_class_prob(probs, y), np.asarray(y, dtype=int)
    return np.array([conformal_quantile(scores[y == k], alpha) if (y == k).any() else np.inf for k in range(n_classes)])


def class_conditional_sets(probs, thresholds) -> np.ndarray:
    return prediction_sets(probs, np.asarray(thresholds, dtype=float)[None, :])


def set_coverage(sets, y) -> float:
    return float(np.asarray(sets)[np.arange(len(y)), np.asarray(y, dtype=int)].mean())


def per_class_coverage(sets, y, n_classes: int) -> np.ndarray:
    hit = np.asarray(sets)[np.arange(len(y)), np.asarray(y, dtype=int)]
    y = np.asarray(y, dtype=int)
    return np.array([hit[y == k].mean() if (y == k).any() else np.nan for k in range(n_classes)])


def mean_set_size(sets) -> float:
    return float(np.asarray(sets).sum(axis=1).mean())


def empty_set_rate(sets) -> float:
    return float((np.asarray(sets).sum(axis=1) == 0).mean())


def expected_calibration_error(probs, y, n_bins: int = 15) -> float:
    """Top-label ECE: weighted mean |accuracy - confidence| over equal-width confidence bins."""
    probs, y = np.asarray(probs, dtype=float), np.asarray(y, dtype=int)
    conf, correct = probs.max(axis=1), (probs.argmax(axis=1) == y).astype(float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins = np.clip(np.digitize(conf, edges[1:-1]), 0, n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        sel = bins == b
        if sel.any():
            ece += sel.mean() * abs(correct[sel].mean() - conf[sel].mean())
    return float(ece)


def brier_score(probs, y) -> float:
    probs, y = np.asarray(probs, dtype=float), np.asarray(y, dtype=int)
    onehot = np.eye(probs.shape[1])[y]
    return float(np.mean(((probs - onehot) ** 2).sum(axis=1)))


def negative_log_likelihood(probs, y) -> float:
    return float(-np.mean(np.log(np.clip(true_class_prob(probs, y), 1e-12, 1.0))))


def apply_temperature(probs, temperature: float) -> np.ndarray:
    z = np.log(np.clip(np.asarray(probs, dtype=float), 1e-12, 1.0)) / temperature
    z -= z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def fit_temperature(probs, y) -> float:
    """Temperature T minimising the NLL of softmax(log p / T) on a calibration set (T > 1 softens overconfident probabilities)."""
    from scipy.optimize import minimize_scalar
    res = minimize_scalar(lambda t: negative_log_likelihood(apply_temperature(probs, t), y), bounds=(0.05, 10.0), method="bounded")
    return float(res.x)


def coverage_by_group(covered, groups, formulas, nominal: float, min_formulas: int = MIN_FORMULAS_FOR_FLAG) -> pd.DataFrame:
    """Coverage per subgroup with the prespecified under-coverage flag (> 5 points below nominal, >= min_formulas distinct formulas)."""
    df = pd.DataFrame({"group": np.asarray(groups), "formula": np.asarray(formulas), "covered": np.asarray(covered, dtype=float)})
    rows = []
    for g, part in df.groupby("group", sort=True):
        n_form = part["formula"].nunique()
        cov = float(part["covered"].mean())
        few = n_form < min_formulas
        rows.append({"group": g, "n_rows": len(part), "n_formulas": n_form, "coverage": cov, "gap_vs_nominal": cov - nominal,
                     "too_few_formulas": few, "under_covered": bool((not few) and cov < nominal - UNDER_COVERAGE_TOLERANCE)})
    return pd.DataFrame(rows)
