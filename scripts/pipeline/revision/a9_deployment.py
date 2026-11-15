"""A9 (SR4): what a screening team can do with the predictions -- evaluated on the 465 truly blind external records (primary benchmark).

(1) Risk-coverage: abstain on the most distant records (composition distance to the nearest training formula) or on the widest 90%
    intervals; MAE and interval coverage of the retained records at 100/75/50/25% retained.
(2) Threshold task Tc > 300 K (room temperature): accuracy, precision, recall of the point prediction; interval-based decisions
    (call 'above' only if the 90% lower limit > 300 K, 'below' only if the upper limit < 300 K, otherwise abstain): decision rate and
    accuracy of the decisions made.
(3) Ranking: precision among the top-k predicted Tc (k = 25, 50, 100) for Tc > 300 K, against the base rate.
All intervals: paper-cluster (shared-DOI) bootstrap, 10,000 resamples.
Output: final/revision/outputs/a9/{risk_coverage.csv, threshold_task.csv, topk.csv}
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
AUD = ROOT / "new_materials_finding/external_audit"
sys.path.insert(0, str(AUD))
sys.path.insert(0, str(AUD.parent))
from analyze_external import subsets  # noqa: E402

OUT = ROOT / "final/revision/outputs/a9"
N_BOOT, SEED, THRESH = 10_000, 20261110, 300.0


def boot(d: pd.DataFrame, fn, seed: int) -> tuple[float, float, float]:
    codes = pd.factorize(d["paper_cluster"].astype(str))[0]
    k = codes.max() + 1
    members = [np.flatnonzero(codes == c) for c in range(k)]
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(N_BOOT):
        ix = np.concatenate([members[c] for c in rng.integers(0, k, k)])
        v = fn(d.iloc[ix])
        if np.isfinite(v):
            vals.append(v)
    return fn(d), float(np.quantile(vals, .025)), float(np.quantile(vals, .975))


def risk_coverage(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for score, label in (("d_comp_train", "composition distance"), ("width_k", "interval width")):
        for keep in (1.0, 0.75, 0.5, 0.25):
            thr = d[score].quantile(keep) if keep < 1 else np.inf
            sub = d[d[score] <= thr]
            mae = boot(sub, lambda x: float(x["abs_err_k"].mean()), SEED)
            cov = boot(sub, lambda x: float(((x["tc_exp_k"] >= x["tc_lo_k"]) & (x["tc_exp_k"] <= x["tc_hi_k"])).mean()), SEED + 1)
            rows.append({"abstain_on": label, "retained_fraction": keep, "n": len(sub), "n_papers": sub["paper_cluster"].nunique(),
                         "mae_k": mae[0], "mae_lo": mae[1], "mae_hi": mae[2], "coverage": cov[0], "coverage_lo": cov[1], "coverage_hi": cov[2]})
    return pd.DataFrame(rows)


def threshold_task(d: pd.DataFrame) -> pd.DataFrame:
    def acc(x):
        return float(((x["tc_pred_k"] > THRESH) == (x["tc_exp_k"] > THRESH)).mean())

    def prec(x):
        p = x["tc_pred_k"] > THRESH
        return float((x.loc[p, "tc_exp_k"] > THRESH).mean()) if p.any() else np.nan

    def rec(x):
        t = x["tc_exp_k"] > THRESH
        return float((x.loc[t, "tc_pred_k"] > THRESH).mean()) if t.any() else np.nan

    def decided(x):
        return (x["tc_lo_k"] > THRESH) | (x["tc_hi_k"] < THRESH)

    def dec_rate(x):
        return float(decided(x).mean())

    def dec_acc(x):
        m = decided(x)
        return float(((x.loc[m, "tc_lo_k"] > THRESH) == (x.loc[m, "tc_exp_k"] > THRESH)).mean()) if m.any() else np.nan

    rows = [{"quantity": "base rate Tc > 300 K", **dict(zip(["value", "lo", "hi"], boot(d, lambda x: float((x["tc_exp_k"] > THRESH).mean()), SEED)))}]
    for name, fn in (("point accuracy", acc), ("point precision", prec), ("point recall", rec), ("interval decision rate", dec_rate),
                     ("accuracy of interval decisions", dec_acc)):
        rows.append({"quantity": name, **dict(zip(["value", "lo", "hi"], boot(d, fn, SEED + len(rows))))})
    out = pd.DataFrame(rows)
    out["n"], out["n_true_above"] = len(d), int((d["tc_exp_k"] > THRESH).sum())
    return out


def topk(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for k in (25, 50, 100):
        def p_at_k(x, k=k):
            return float((x.nlargest(min(k, len(x)), "tc_pred_k")["tc_exp_k"] > THRESH).mean())
        v = boot(d, p_at_k, SEED + k)
        rows.append({"k": k, "precision_at_k": v[0], "lo": v[1], "hi": v[2], "base_rate": float((d["tc_exp_k"] > THRESH).mean())})
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(AUD / "similarity_records.csv", keep_default_na=False, na_values=[""])
    prim = df[~df["excluded_primary"].astype(bool)].reset_index(drop=True)
    blind = prim[subsets(prim, include_old=False)["composition NEVER seen (blind)"].to_numpy()].reset_index(drop=True)
    print(f"blind records: {len(blind)}", flush=True)
    for name, frame in (("risk_coverage", risk_coverage(blind)), ("threshold_task", threshold_task(blind)), ("topk", topk(blind))):
        frame.to_csv(OUT / f"{name}.csv", index=False)
        print(frame.round(3).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
