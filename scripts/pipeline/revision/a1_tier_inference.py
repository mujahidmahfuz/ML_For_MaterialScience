"""A1 (RR4, SR8): refit-aware inference, multiplicity and the full stability rule for the matched Tier 1/2/3 comparisons.

Inputs (saved per-split test predictions, nothing is refitted here):
  Curie    EDA/10_phase7_validation/v1.3/work/curie/main__<i>.parquet (+ diag__<i> for the clipped Ridge 'linear_clip')
           XGBoost: mean of the 8 thread/seed realisations in final/work/curie_xgb_noise/
  moment   EDA/10_phase7_validation/v1.2/work/ms_moment/main__<i>.parquet; XGBoost: mean of the 7 realisations in final/work/ms_threads/
  ordering EDA/10_phase7_validation/v1.3/work/matched__<i>.parquet; XGBoost: mean probabilities over 3 seeds from
           final/revision/outputs/a1/ordering_xgb_seeds/ when present (else the single saved realisation, flagged)
Rule (PLAN.md): stable = pooled formula-bootstrap CI excludes 0 AND Nadeau-Bengio corrected-t CI excludes 0 AND >= 70% splits same sign;
borderline = exactly one of the two intervals excludes 0. Primary family = Tier 1 -> 3, primary metric, 3 targets x 3 algorithms (Holm).
Output: final/revision/outputs/a1/tier_inference.csv
"""
from __future__ import annotations

import glob
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import f1_score

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "final/revision/outputs/a1"
SPLITS = [str(i) for i in range(10)]
N_BOOT, SEED, MIN_FRAC = 1000, 20261110, 0.70
PAIRS = (("tier1", "tier2"), ("tier2", "tier3"), ("tier1", "tier3"))
MARGIN = {"curie": 10.0, "ms_moment": 0.10, "ordering": 0.02}
CLASSES = 4


def _read(pattern: str) -> pd.DataFrame:
    files = sorted(glob.glob(str(pattern)))
    if not files:
        raise FileNotFoundError(pattern)
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def regression_predictions(target: str) -> tuple[pd.DataFrame, dict]:
    if target == "curie":
        work = ROOT / "EDA/10_phase7_validation/v1.3/work/curie"
        xgb_glob = ROOT / "final/work/curie_xgb_noise/xgb__*__[0-9].parquet"
    else:
        work = ROOT / "EDA/10_phase7_validation/v1.2/work/ms_moment"
        xgb_glob = ROOT / "final/work/ms_threads/refit__*__[0-9].parquet"
    main = pd.concat([pd.read_parquet(work / f"main__{s}.parquet") for s in SPLITS], ignore_index=True)
    main = main[main["variant"].isin(["tier1", "tier2", "tier3"])]
    keep = main[main["algorithm"].isin(["linear", "gradient_boosting"])]
    xgb = _read(xgb_glob)
    xgb = xgb[(xgb["algorithm"] == "xgboost") & xgb["variant"].isin(["tier1", "tier2", "tier3"])]
    xgb["split_id"] = xgb["split_id"].astype(str)
    n_real = xgb.groupby(["split_id", "variant", "material_id"]).size().min()
    xgb_mean = (xgb.groupby(["split_id", "variant", "material_id", "reduced_formula"], as_index=False)
                .agg(y_true=("y_true", "first"), y_pred=("y_pred", "mean")).assign(algorithm="xgboost_seedmean"))
    parts = [keep, xgb_mean]
    if target == "curie":
        diag = pd.concat([pd.read_parquet(work / f"diag__{s}.parquet") for s in SPLITS], ignore_index=True)
        parts.append(diag[(diag["algorithm"] == "linear_clip") & diag["variant"].isin(["tier1", "tier2", "tier3"])])
    out = pd.concat(parts, ignore_index=True)
    out["split_id"] = out["split_id"].astype(str)
    return out, {"xgb_realisations": int(n_real)}


def ordering_predictions() -> tuple[pd.DataFrame, dict]:
    work = ROOT / "EDA/10_phase7_validation/v1.3/work/ordering"
    main = pd.concat([pd.read_parquet(work / f"matched__{s}.parquet") for s in SPLITS], ignore_index=True)
    main = main[main["variant"].isin(["tier1", "tier2", "tier3"])]
    main["split_id"] = main["split_id"].astype(str)
    seeds_dir = OUT / "ordering_xgb_seeds"
    files = sorted(seeds_dir.glob("seed*__*.parquet")) if seeds_dir.exists() else []
    if files:
        s = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
        s["split_id"] = s["split_id"].astype(str)
        prob_cols = [f"p{k}" for k in range(CLASSES)]
        n_real = int(s.groupby(["split_id", "variant", "material_id"]).size().min())
        m = s.groupby(["split_id", "variant", "material_id", "reduced_formula"], as_index=False).agg(
            y_true=("y_true", "first"), **{c: (c, "mean") for c in prob_cols})
        m["y_pred"] = m[prob_cols].to_numpy().argmax(axis=1)
        xgb = m.drop(columns=prob_cols).assign(algorithm="xgboost_seedmean")
        main = pd.concat([main[main["algorithm"] != "xgboost"], xgb], ignore_index=True)
        info = {"xgb_realisations": n_real}
    else:
        info = {"xgb_realisations": 1}
    return main, info


def n_total(target: str) -> int:
    path = {"curie": "EDA/02_splits/v1.3/matched_split_curie.csv", "ms_moment": "EDA/02_splits/v1.2/matched_split_ms.csv",
            "ordering": "EDA/02_splits/v1.3/matched_split_ordering.csv"}[target]
    return len(pd.read_csv(ROOT / path, usecols=["material_id"]))


def metric_point(df: pd.DataFrame, task: str) -> float:
    if task == "regression":
        return float((df["y_true"] - df["y_pred"]).abs().mean())
    return float(f1_score(df["y_true"], df["y_pred"], labels=list(range(CLASSES)), average="macro", zero_division=0))


def weighted_metric(y: np.ndarray, p: np.ndarray, w: np.ndarray, task: str) -> np.ndarray:
    """w: B x n row weights -> B metric values (MAE for regression, macro-F1 for classification)."""
    if task == "regression":
        return (w * np.abs(y - p)).sum(axis=1) / w.sum(axis=1)
    out = np.empty(w.shape[0])
    idx = y * CLASSES + p
    for b in range(w.shape[0]):
        cm = np.bincount(idx, weights=w[b], minlength=CLASSES * CLASSES).reshape(CLASSES, CLASSES)
        tp, fp, fn = np.diag(cm), cm.sum(axis=0) - np.diag(cm), cm.sum(axis=1) - np.diag(cm)
        denom = 2 * tp + fp + fn
        present = cm.sum(axis=1) > 0
        f1 = np.divide(2 * tp, denom, out=np.zeros(CLASSES), where=denom > 0)
        out[b] = f1[present | (cm.sum(axis=0) > 0)].mean()
    return out


def improvement(task: str, a, b):
    """positive = the deeper tier (b) is better."""
    return (b - a) if task == "classification" else (a - b)


def contrast(df: pd.DataFrame, alg: str, v_from: str, v_to: str, task: str, n_all: int, rng_seed: int) -> dict:
    sub = df[df["algorithm"] == alg]
    per_split, boots = [], []
    formulas = pd.Index(sorted(sub["reduced_formula"].unique()))
    rng = np.random.default_rng(rng_seed)
    counts = np.vstack([np.bincount(rng.integers(0, len(formulas), len(formulas)), minlength=len(formulas)) for _ in range(N_BOOT)])
    n_test = []
    for s in SPLITS:
        a = sub[(sub["split_id"] == s) & (sub["variant"] == v_from)].set_index("material_id")
        b = sub[(sub["split_id"] == s) & (sub["variant"] == v_to)].set_index("material_id")
        common = a.index.intersection(b.index)
        if len(common) != len(a) or len(common) != len(b):
            raise ValueError(f"{alg} split {s}: tiers scored on different rows")
        a, b = a.loc[common], b.loc[common]
        n_test.append(len(common))
        per_split.append(improvement(task, metric_point(a, task), metric_point(b, task)))
        codes = formulas.get_indexer(a["reduced_formula"])
        w = counts[:, codes].astype(float)
        y = a["y_true"].to_numpy()
        ya = a["y_pred"].to_numpy()
        yb = b["y_pred"].to_numpy()
        if task == "classification":
            y, ya, yb = y.astype(int), ya.astype(int), yb.astype(int)
        boots.append(improvement(task, weighted_metric(y, ya, w, task), weighted_metric(y, yb, w, task)))
    d = np.array(per_split)
    pooled = np.mean(np.vstack(boots), axis=0)
    J, mean = len(d), float(d.mean())
    ratio = float(np.mean(n_test)) / (n_all - float(np.mean(n_test)))
    se = float(d.std(ddof=1) * np.sqrt(1.0 / J + ratio))
    tcrit = stats.t.ppf(0.975, J - 1)
    p = float(2 * stats.t.sf(abs(mean) / se, J - 1)) if se > 0 else 0.0
    boot_lo, boot_hi = np.quantile(pooled, [0.025, 0.975])
    frac_same = float(max((d > 0).mean(), (d < 0).mean()))
    boot_ex, t_ex = (boot_lo > 0 or boot_hi < 0), (mean - tcrit * se > 0 or mean + tcrit * se < 0)
    verdict = ("stable" if boot_ex and t_ex and frac_same >= MIN_FRAC and np.sign(boot_lo) == np.sign(mean - tcrit * se)
               else "borderline" if (boot_ex or t_ex) else "not stable")
    if verdict != "not stable":
        verdict += " gain" if mean > 0 else " loss"
    return {"algorithm": alg, "from": v_from, "to": v_to, "mean_improvement": mean, "boot_ci_low": float(boot_lo), "boot_ci_high": float(boot_hi),
            "nb_ci_low": mean - tcrit * se, "nb_ci_high": mean + tcrit * se, "nb_se": se, "nb_p": p, "n_splits": J,
            "fraction_same_sign": frac_same, "n_positive": int((d > 0).sum()), "test_over_train": ratio,
            "mde80": float((tcrit + stats.t.ppf(0.80, J - 1)) * se), "verdict": verdict}


def holm(p: np.ndarray) -> np.ndarray:
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(p) - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for target, task in (("curie", "regression"), ("ms_moment", "regression"), ("ordering", "classification")):
        df, info = ordering_predictions() if target == "ordering" else regression_predictions(target)
        n_all = n_total(target)
        for k, alg in enumerate(sorted(df["algorithm"].unique())):
            for j, (a, b) in enumerate(PAIRS):
                r = contrast(df, alg, a, b, task, n_all, SEED + 100 * k + j)
                r.update(target=target, metric="mae" if task == "regression" else "macro_f1", practical_margin=MARGIN[target], **info)
                margin_ok = (r["nb_ci_high"] < MARGIN[target]) and (r["boot_ci_high"] < MARGIN[target])
                r["practical"] = ("no practical gain" if margin_ok and r["mean_improvement"] < MARGIN[target]
                                  else "gain cannot be ruled out above margin")
                rows.append(r)
        print(f"{target}: done ({info})", flush=True)
    out = pd.DataFrame(rows)
    # ordering XGBoost enters as a single realisation (seed averaging was cut, PLAN.md deviations); 'xgb_realisations' records this
    primary = (out["from"] == "tier1") & (out["to"] == "tier3") & out["algorithm"].isin(["linear", "gradient_boosting", "xgboost_seedmean", "xgboost"])
    out["family"] = np.where(primary, "primary (Tier 1->3)", "secondary")
    out["holm_p"] = np.nan
    out.loc[primary, "holm_p"] = holm(out.loc[primary, "nb_p"].to_numpy())
    cols = ["target", "metric", "algorithm", "from", "to", "family", "mean_improvement", "boot_ci_low", "boot_ci_high", "nb_ci_low", "nb_ci_high",
            "nb_p", "holm_p", "n_positive", "n_splits", "fraction_same_sign", "mde80", "practical_margin", "practical", "verdict", "xgb_realisations",
            "test_over_train"]
    out[cols].to_csv(OUT / "tier_inference.csv", index=False)
    pd.set_option("display.width", 250)
    print(out[cols].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
