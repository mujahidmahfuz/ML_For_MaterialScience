"""A4 (RR6) + A10 (SR5) analysis of the saved per-split UQ outputs (a4_uq_run.py). No refitting.

Regression targets (curie, ms_moment):
  A4(b) coverage of split / normalized / CQR intervals (90%) on subgroups NOT defined by any method's own scale:
        farthest composition-distance decile, top decile of the point prediction, material families, label source; and, for reference,
        the sigma-defined hardest decile used in the first submission (marked 'circular').
  A4(c) design effect: within-formula intraclass correlation of the calibration exceedance indicator, effective calibration size,
        the coverage SD implied by exchangeable sampling of formulas vs of rows, and the observed split-to-split SD.
  A10   distance-aware conformal: (i) Mondrian normalized conformal with calibration-distance quartile bins, (ii) weighted
        (covariate-shift) normalized conformal, weights = calibration->test density ratio of log(1+distance) estimated by logistic
        regression on calibration vs test rows (Tibshirani et al. 2019); coverage and width by test-distance decile and marginally.
Ordering:
  A4(d) prior correction + temperature; marginal and class-conditional sets with the temperature fitted on half of the calibration formulas
        and thresholds on the other half (no reuse), vs the original reuse; top-label and classwise ECE (15 bins).
Usage: python a4_a10_analysis.py <curie|ms_moment|ordering>
Outputs: final/revision/outputs/a4/<target>_*.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "final/revision/outputs/a4"
ALPHA = 0.10
METHODS = ["split_conformal", "normalized_conformal", "cqr"]
CLASSES = ["FM", "AFM", "FiM", "NM"]


def conformal_q(scores: np.ndarray, alpha: float = ALPHA) -> float:
    n = len(scores)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    return float(np.sort(scores)[k - 1]) if k <= n else np.inf


def weighted_q(scores_sorted: np.ndarray, w_sorted: np.ndarray, w_test: float, alpha: float = ALPHA) -> float:
    p = np.cumsum(w_sorted) / (w_sorted.sum() + w_test)
    idx = np.searchsorted(p, 1 - alpha)
    return float(scores_sorted[idx]) if idx < len(scores_sorted) else np.inf


def load(target: str) -> tuple[list[pd.DataFrame], list[pd.DataFrame]]:
    d = OUT / target
    ids = sorted(int(p.stem.split("__")[1]) for p in d.glob("split__*.parquet"))
    return [pd.read_parquet(d / f"split__{i}.parquet") for i in ids], [pd.read_parquet(d / f"cal__{i}.parquet") for i in ids]


def covered(df: pd.DataFrame, m: str) -> np.ndarray:
    return ((df["y"] >= df[f"{m}_lo"]) & (df["y"] <= df[f"{m}_hi"])).to_numpy()


def subgroup_masks(t: pd.DataFrame) -> dict[str, np.ndarray]:
    out = {"all": np.ones(len(t), bool),
           "farthest distance decile": (t["distance"] >= t["distance"].quantile(0.9)).to_numpy(),
           "top decile of predicted value": (t["pred"] >= t["pred"].quantile(0.9)).to_numpy(),
           "hardest sigma decile (circular, first submission)": (t["sigma"] >= t["sigma"].quantile(0.9)).to_numpy()}
    for c in [c for c in t.columns if c.startswith("grp_")]:
        out[f"group: {c[4:]}"] = t[c].to_numpy(bool)
    for s in t["source"].unique():
        out[f"source: {s}"] = (t["source"] == s).to_numpy()
    return out


def a4_subgroups(tests: list[pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for t in tests:
        for name, m in subgroup_masks(t).items():
            if m.sum() < 20:
                continue
            for meth in METHODS:
                rows.append({"split_id": int(t["split_id"].iloc[0]), "group": name, "method": meth, "n_rows": int(m.sum()),
                             "n_formulas": int(t.loc[m, "reduced_formula"].nunique()), "coverage": float(covered(t, meth)[m].mean()),
                             "mean_width": float((t[f"{meth}_hi"] - t[f"{meth}_lo"])[m].mean())})
    df = pd.DataFrame(rows)
    return (df.groupby(["group", "method"]).agg(n_splits=("coverage", "size"), mean_coverage=("coverage", "mean"), sd_coverage=("coverage", "std"),
                                                min_coverage=("coverage", "min"), mean_width=("mean_width", "mean"), median_rows=("n_rows", "median"),
                                                median_formulas=("n_formulas", "median")).reset_index())


def icc(indicator: np.ndarray, groups: np.ndarray) -> tuple[float, float]:
    """ANOVA estimator of the intraclass correlation of a 0/1 indicator; returns (icc, size-weighted mean cluster size)."""
    df = pd.DataFrame({"x": indicator.astype(float), "g": groups})
    g = df.groupby("g")["x"]
    sizes, means = g.size().to_numpy(), g.mean().to_numpy()
    k, n = len(sizes), len(df)
    m0 = (n - (sizes ** 2).sum() / n) / (k - 1)
    grand = df["x"].mean()
    msb = (sizes * (means - grand) ** 2).sum() / (k - 1)
    msw = (df["x"] - df["g"].map(g.mean())).pow(2).sum() / (n - k)
    den = msb + (m0 - 1) * msw
    rho = (msb - msw) / den if den > 0 else 0.0
    return float(max(rho, 0.0)), float((sizes ** 2).sum() / sizes.sum())


def scores(c: pd.DataFrame, meth: str) -> np.ndarray:
    if meth == "split_conformal":
        return np.abs(c["y"] - c["pred"]).to_numpy()
    if meth == "normalized_conformal":
        return (np.abs(c["y"] - c["pred"]) / c["sigma"]).to_numpy()
    return np.maximum(c["q_lo"] - c["y"], c["y"] - c["q_hi"]).to_numpy()


def a4_design_effect(tests, cals) -> pd.DataFrame:
    rows = []
    for meth in METHODS:
        covs, deffs, ncal = [], [], []
        for t, c in zip(tests, cals):
            covs.append(covered(t, meth).mean())
            s = scores(c, meth)
            rho, mbar = icc(s > np.quantile(s, 1 - ALPHA), c["reduced_formula"].to_numpy())
            deffs.append(1 + (mbar - 1) * rho)
            ncal.append(len(c))
        n_cal, deff = float(np.mean(ncal)), float(np.mean(deffs))
        rows.append({"method": meth, "n_splits": len(covs), "mean_calibration_rows": n_cal, "design_effect": deff,
                     "effective_calibration_size": n_cal / deff, "sd_implied_iid_rows": float(np.sqrt(ALPHA * (1 - ALPHA) / (n_cal + 2))),
                     "sd_implied_effective": float(np.sqrt(ALPHA * (1 - ALPHA) / (n_cal / deff + 2))),
                     "observed_sd_marginal_coverage": float(np.std(covs, ddof=1)), "mean_marginal_coverage": float(np.mean(covs))})
    return pd.DataFrame(rows)


def a10_distance_aware(tests, cals) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, marg = [], []
    for t, c in zip(tests, cals):
        s_cal = scores(c, "normalized_conformal")
        d_cal, d_te = c["distance"].to_numpy(), t["distance"].to_numpy()
        variants = {"normalized (plain)": np.full(len(t), conformal_q(s_cal))}
        edges = np.unique(np.quantile(d_cal, [0, .25, .5, .75, 1]))
        b_cal = np.clip(np.searchsorted(edges, d_cal, side="right") - 1, 0, len(edges) - 2)
        b_te = np.clip(np.searchsorted(edges, d_te, side="right") - 1, 0, len(edges) - 2)
        qb = {b: conformal_q(s_cal[b_cal == b]) for b in np.unique(b_cal)}
        variants["Mondrian by distance quartile"] = np.array([qb.get(b, conformal_q(s_cal)) for b in b_te])
        X = np.log1p(np.concatenate([d_cal, d_te]))[:, None]
        lr = LogisticRegression().fit(X, np.r_[np.zeros(len(d_cal)), np.ones(len(d_te))])
        def odds(d):
            p = lr.predict_proba(np.log1p(d)[:, None])[:, 1]
            return p / (1 - p) * (len(d_cal) / len(d_te))
        w_cal, w_te = odds(d_cal), odds(d_te)
        order = np.argsort(s_cal)
        s_sorted, w_sorted = s_cal[order], w_cal[order]
        variants["weighted (covariate shift)"] = np.array([weighted_q(s_sorted, w_sorted, w) for w in w_te])
        dec = pd.qcut(pd.Series(d_te).rank(method="first"), 10, labels=False).to_numpy()
        y, pred, sig = t["y"].to_numpy(), t["pred"].to_numpy(), t["sigma"].to_numpy()
        for name, q in variants.items():
            lo, hi = pred - q * sig, pred + q * sig
            cov = (y >= lo) & (y <= hi)
            width = np.where(np.isfinite(q), hi - lo, np.nan)
            marg.append({"split_id": int(t["split_id"].iloc[0]), "variant": name, "coverage": float(cov.mean()), "mean_width": float(np.nanmean(width)),
                         "share_infinite": float(np.mean(~np.isfinite(q)))})
            for k in range(10):
                m = dec == k
                rows.append({"split_id": int(t["split_id"].iloc[0]), "variant": name, "distance_decile": k + 1, "coverage": float(cov[m].mean()),
                             "mean_width": float(np.nanmean(width[m])), "mean_distance": float(d_te[m].mean())})
    by_dec = pd.DataFrame(rows).groupby(["variant", "distance_decile"]).agg(coverage=("coverage", "mean"), sd=("coverage", "std"),
                                                                             min_coverage=("coverage", "min"), mean_width=("mean_width", "mean"),
                                                                             mean_distance=("mean_distance", "mean")).reset_index()
    marg = pd.DataFrame(marg).groupby("variant").agg(coverage=("coverage", "mean"), sd=("coverage", "std"), mean_width=("mean_width", "mean"),
                                                      share_infinite=("share_infinite", "mean")).reset_index()
    return by_dec, marg


# ------------------------------------------------------------------------------------------------------------------------ ordering
def softmax_temp(p: np.ndarray, t: float) -> np.ndarray:
    z = np.log(np.clip(p, 1e-12, 1)) / t
    z -= z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def fit_temp(p: np.ndarray, y: np.ndarray) -> float:
    def nll(t):
        return -np.mean(np.log(np.clip(softmax_temp(p, t)[np.arange(len(y)), y], 1e-12, 1)))
    return float(minimize_scalar(nll, bounds=(0.05, 10), method="bounded").x)


def _ece(conf: np.ndarray, hit: np.ndarray, bins: int = 15) -> float:
    idx = np.clip((conf * bins).astype(int), 0, bins - 1)
    return float(sum(abs(hit[idx == b].mean() - conf[idx == b].mean()) * (idx == b).mean() for b in range(bins) if (idx == b).any()))


def top_ece(p, y):
    return _ece(p.max(1), (p.argmax(1) == y).astype(float))


def classwise_ece(p, y):
    return float(np.mean([_ece(p[:, k], (y == k).astype(float)) for k in range(p.shape[1])]))


def sets_eval(p_cal, y_cal, p_te, y_te) -> dict:
    s_cal = 1 - p_cal[np.arange(len(y_cal)), y_cal]
    q = conformal_q(s_cal)
    qk = np.array([conformal_q(s_cal[y_cal == k]) if (y_cal == k).any() else np.inf for k in range(4)])
    out = {}
    for name, thr in (("marginal", np.full(4, q)), ("class-conditional", qk)):
        S = (1 - p_te) <= thr[None, :]
        cov = S[np.arange(len(y_te)), y_te]
        out[name] = {"coverage": float(cov.mean()), "set_size": float(S.sum(1).mean()),
                     **{f"coverage_{c}": float(cov[y_te == k].mean()) for k, c in enumerate(CLASSES)}}
    return out


def ordering() -> None:
    rows = []
    for f in sorted((OUT / "ordering").glob("proba__*.npz")):
        z = np.load(f, allow_pickle=True)
        i = int(f.stem.split("__")[1])
        prior = z["train_freq"]

        def corr(p):   # balanced-weight probabilities -> training prior (Saerens et al. 2002), as in Phase 8
            q = p * prior[None, :]
            return q / q.sum(1, keepdims=True)
        p_cal, p_te, y_cal, y_te = corr(z["p_cal"]), corr(z["p_te"]), z["y_cal"], z["y_te"]
        t_all = fit_temp(p_cal, y_cal)
        res = {"reuse (first submission)": sets_eval(softmax_temp(p_cal, t_all), y_cal, softmax_temp(p_te, t_all), y_te)}
        fu = pd.unique(z["f_cal"])
        half = set(np.random.default_rng(20261110 + i).permutation(fu)[: len(fu) // 2])
        a = np.isin(z["f_cal"], list(half))
        t_a = fit_temp(p_cal[a], y_cal[a])
        res["split calibration (T on half A, thresholds on half B)"] = sets_eval(softmax_temp(p_cal[~a], t_a), y_cal[~a], softmax_temp(p_te, t_a), y_te)
        for scheme, r in res.items():
            for kind, m in r.items():
                rows.append({"split_id": i, "calibration": scheme, "sets": kind, **m})
        pt = softmax_temp(p_te, t_all)
        rows.append({"split_id": i, "calibration": "probabilities", "sets": "ECE", "top_label_ece_raw": top_ece(z["p_te"], y_te),
                     "classwise_ece_raw": classwise_ece(z["p_te"], y_te), "top_label_ece_prior": top_ece(p_te, y_te),
                     "classwise_ece_prior": classwise_ece(p_te, y_te), "top_label_ece_prior_temp": top_ece(pt, y_te),
                     "classwise_ece_prior_temp": classwise_ece(pt, y_te), "temperature": t_all, "temperature_half": t_a})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "ordering_calibration_split.csv", index=False)
    sets = df[df["sets"] != "ECE"]
    summ = sets.groupby(["calibration", "sets"]).agg(**{c: (c, "mean") for c in ["coverage", "set_size"] + [f"coverage_{k}" for k in CLASSES]},
                                                     sd_coverage=("coverage", "std"), n_splits=("coverage", "size")).reset_index()
    summ.to_csv(OUT / "ordering_calibration_split_summary.csv", index=False)
    ece = df[df["sets"] == "ECE"].drop(columns=["split_id", "calibration", "sets"]).dropna(axis=1, how="all")
    ece.agg(["mean", "std"]).to_csv(OUT / "ordering_ece_summary.csv")
    pd.set_option("display.width", 250)
    print(summ.round(3).to_string(index=False), "\n", ece.agg(["mean", "std"]).round(4).to_string())


def main() -> None:
    target = sys.argv[1]
    if target == "ordering":
        ordering()
        return
    tests, cals = load(target)
    print(f"{target}: {len(tests)} splits", flush=True)
    sub = a4_subgroups(tests)
    sub.to_csv(OUT / f"{target}_subgroup_coverage.csv", index=False)
    de = a4_design_effect(tests, cals)
    de.to_csv(OUT / f"{target}_design_effect.csv", index=False)
    by_dec, marg = a10_distance_aware(tests, cals)
    by_dec.to_csv(OUT / f"{target}_distance_aware_by_decile.csv", index=False)
    marg.to_csv(OUT / f"{target}_distance_aware_marginal.csv", index=False)
    pd.set_option("display.width", 250)
    print(sub.round(3).to_string(index=False), "\n", de.round(4).to_string(index=False), "\n", marg.round(3).to_string(index=False))
    print(by_dec[by_dec["distance_decile"].isin([1, 5, 9, 10])].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
