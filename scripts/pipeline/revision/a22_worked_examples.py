"""A22: three worked examples for the screening rules (Curie temperature, Tier 1 XGBoost, 90% normalized conformal intervals).

Callers: final/scripts/build_paper_package.py copies the output; the values of Extended Data Table 9 in the manuscript are copied from it.
Input: final/revision/outputs/a4/curie/split__<i>.parquet (saved per-record test predictions of the ten uncertainty splits; columns used:
material_id, reduced_formula, y, pred, distance, normalized_conformal_lo, normalized_conformal_hi).
Output: final/revision/outputs/a22_worked_examples/worked_examples.csv, one row per compound:
  compound, split, records, y_median, y_min, y_max, pred_median, lo_median, hi_median, distance_median, share_at_least_as_close, decision, abs_error_of_median
Selection (made by looking at the saved test sets before writing the text, so these are illustrations and not a sample): three compounds with a
well-known Curie temperature that show three outcomes of the 300 K rule (decided and correct; abstained although the point prediction was close;
abstained far from the training chemistry with a large point error). Each compound is taken from one test set in which every record of its formula
is a test record (formula-grouped splits), so no record of the formula was seen in training. Values are medians over the records of the formula.
Decision rule as in Results: 'above' if the interval lies wholly above 300 K, 'below' if wholly below, otherwise 'abstain'.
Run (repository root): python final/revision/scripts/a22_worked_examples.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "final/revision/outputs/a4/curie"
OUT = ROOT / "final/revision/outputs/a22_worked_examples"
THRESH = 300.0
CASES = (("SmCo5", 1), ("Gd5Si4", 4), ("Ho", 2))


def decide(lo: float, hi: float) -> str:
    if lo > THRESH:
        return "above"
    if hi < THRESH:
        return "below"
    return "abstain"


def example(formula: str, split: int) -> dict:
    cols = ["material_id", "reduced_formula", "y", "pred", "distance", "normalized_conformal_lo", "normalized_conformal_hi"]
    test = pd.read_parquet(SRC / f"split__{split}.parquet", columns=cols)
    rows = test[test["reduced_formula"] == formula]
    if rows.empty:
        raise ValueError(f"{formula} is not in test split {split}")
    lo, hi = float(rows["normalized_conformal_lo"].median()), float(rows["normalized_conformal_hi"].median())
    dist = float(rows["distance"].median())
    return {"compound": formula, "split": split, "records": len(rows), "y_median": float(rows["y"].median()), "y_min": float(rows["y"].min()),
            "y_max": float(rows["y"].max()), "pred_median": float(rows["pred"].median()), "lo_median": lo, "hi_median": hi, "distance_median": dist,
            "share_at_least_as_close": float((test["distance"].to_numpy() <= dist).mean()), "decision": decide(lo, hi),
            "abs_error_of_median": abs(float(rows["pred"].median()) - float(rows["y"].median()))}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame([example(f, s) for f, s in CASES])
    table.to_csv(OUT / "worked_examples.csv", index=False)
    pd.set_option("display.width", 220)
    print(table.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
