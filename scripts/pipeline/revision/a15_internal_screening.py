"""A15 (round-3 review R4-2): the A9 screening analysis repeated on the INTERNAL formula-grouped test sets (Curie, Tier 1 XGBoost, 10 splits).

A9 evaluated screening rules only on the 465 blind external records. Here the same definitions are applied to the saved per-row test
intervals of the 10 prespecified splits (final/revision/outputs/a4/curie/split__<i>.parquet; 90% normalized conformal intervals,
composition distance to the proper-training formulas), so that the recommendation does not rest on one small external table.

(1) Risk-coverage: abstain on the most distant records, or on the widest intervals; MAE and coverage of the retained records at
    100/75/50/25% (ties at the cut-off are kept, so the retained share can exceed the nominal one; it is reported).
(2) Threshold task Tc > 300 K: point accuracy, precision, recall; interval decisions ('above' if the lower limit > 300 K, 'below' if the
    upper limit < 300 K, else abstain): decision rate and accuracy of the decisions made.
(3) Ranking: precision among the top-k predicted Tc (k = 25, 50, 100) against the base rate.
Every quantity is computed within each split and summarised as the mean over the 10 splits with the standard deviation across splits
(descriptive; the test sets of different splits overlap). No model is refitted.
Output: final/revision/outputs/a15_internal_screening/{risk_coverage.csv, threshold_task.csv, topk.csv}
Run (repository root): python final/revision/scripts/a15_internal_screening.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "final/revision/outputs/a4/curie"
OUT = ROOT / "final/revision/outputs/a15_internal_screening"
THRESH, N_SPLITS = 300.0, 10
LO, HI = "normalized_conformal_lo", "normalized_conformal_hi"


def load(i: int) -> pd.DataFrame:
    d = pd.read_parquet(SRC / f"split__{i}.parquet", columns=["material_id", "y", "pred", "distance", LO, HI])
    d["abs_err"] = (d["y"] - d["pred"]).abs()
    d["width"] = d[HI] - d[LO]
    d["covered"] = (d["y"] >= d[LO]) & (d["y"] <= d[HI])
    return d


def risk_coverage(d: pd.DataFrame, i: int) -> list[dict]:
    rows = []
    for score, label in (("distance", "composition distance"), ("width", "interval width")):
        for keep in (1.0, 0.75, 0.5, 0.25):
            sub = d if keep == 1.0 else d[d[score] <= d[score].quantile(keep)]
            rows.append({"split": i, "abstain_on": label, "nominal_retained": keep, "retained_share": len(sub) / len(d), "n": len(sub),
                         "mae_k": float(sub["abs_err"].mean()), "coverage": float(sub["covered"].mean())})
    return rows


def threshold_task(d: pd.DataFrame, i: int) -> dict:
    truth, pred = d["y"] > THRESH, d["pred"] > THRESH
    decided = (d[LO] > THRESH) | (d[HI] < THRESH)
    return {"split": i, "n": len(d), "base_rate": float(truth.mean()), "point_accuracy": float((truth == pred).mean()),
            "point_precision": float(truth[pred].mean()) if pred.any() else np.nan,
            "point_recall": float(pred[truth].mean()) if truth.any() else np.nan,
            "interval_decision_rate": float(decided.mean()),
            "interval_decision_accuracy": float(((d.loc[decided, LO] > THRESH) == truth[decided]).mean()) if decided.any() else np.nan}


def topk(d: pd.DataFrame, i: int) -> list[dict]:
    return [{"split": i, "k": k, "precision_at_k": float((d.nlargest(k, "pred")["y"] > THRESH).mean()), "base_rate": float((d["y"] > THRESH).mean())}
            for k in (25, 50, 100)]


def summarise(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    cols = [c for c in df.columns if c not in keys + ["split"]]
    g = df.groupby(keys)[cols]
    out = g.mean().add_suffix("_mean").join(g.std(ddof=1).add_suffix("_sd"))
    return out.reset_index()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rc_rows, th_rows, tk_rows = [], [], []
    for i in range(N_SPLITS):
        d = load(i)
        rc_rows += risk_coverage(d, i)
        th_rows.append(threshold_task(d, i))
        tk_rows += topk(d, i)
    rc, th, tk = pd.DataFrame(rc_rows), pd.DataFrame(th_rows), pd.DataFrame(tk_rows)
    rc.to_csv(OUT / "risk_coverage_per_split.csv", index=False)
    th.to_csv(OUT / "threshold_task_per_split.csv", index=False)
    tk.to_csv(OUT / "topk_per_split.csv", index=False)
    pd.set_option("display.width", 220)
    for name, frame, keys in (("risk_coverage", rc, ["abstain_on", "nominal_retained"]), ("topk", tk, ["k"])):
        s = summarise(frame, keys)
        s.to_csv(OUT / f"{name}.csv", index=False)
        print(name)
        print(s.round(3).to_string(index=False))
    s = th.drop(columns="split").agg(["mean", "std"]).T.rename(columns={"mean": "mean_over_splits", "std": "sd_across_splits"})
    s.to_csv(OUT / "threshold_task.csv")
    print("threshold_task")
    print(s.round(3).to_string())


if __name__ == "__main__":
    main()
