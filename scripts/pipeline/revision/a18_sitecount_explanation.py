"""A18 (round-2 follow-up to R2-2): why does a site count still help for the intensive per-formula-unit moment?

Hypothesis, stated before looking at the data: cells that are larger than the formula unit (supercell multiplicity Z = atoms in the DFT cell /
atoms in the reduced formula > 1) are mostly the cells of magnetic orderings with a multi-site magnetic unit cell (antiferromagnets, ferrimagnets) or
of low-symmetry structures; such cells have a net moment per formula unit near zero. A site count then works as a proxy for the ordering type.
Descriptive test on the matched rows of the per-formula-unit target (A5):
  * by multiplicity bin (Z = 1, 2, 3-4, 5-8, > 8): number of rows, share with |m_fu| < 0.05 muB (near zero), mean and median m_fu,
    and the Materials Project ordering label of the entry (p3_ordering; excluded from every predictor set, used here only to describe the data);
  * Spearman correlation of Z with m_fu and with the ordering label (FM vs the rest);
  * AUC of Z (and of the number of atoms in the cell) for telling near-zero from non-zero moments.
No model is fitted. Output: final/revision/outputs/a18_sitecount/{by_multiplicity.csv, summary.csv}
Run (repository root): python final/revision/scripts/a18_sitecount_explanation.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "final/revision/outputs/a18_sitecount"
NEAR_ZERO = 0.05


def load() -> pd.DataFrame:
    d = pd.read_parquet(ROOT / "final/revision/outputs/a5/per_fu_target.parquet")
    p3 = pd.read_csv(ROOT / "new_datasets/MMFD/phase3/data/phase3_master_dataset.csv", usecols=["material_id", "p3_ordering"])
    d = d.merge(p3.drop_duplicates("material_id"), on="material_id", how="left")
    d["Z"] = d["cell_atoms"] / d["fu_atoms"]
    d["near_zero"] = d["value"].abs() < NEAR_ZERO
    d["bin"] = pd.cut(d["Z"], [0, 1.0001, 2.0001, 4.0001, 8.0001, np.inf], labels=["Z = 1", "Z = 2", "Z = 3-4", "Z = 5-8", "Z > 8"])
    d["order"] = d["p3_ordering"].fillna("missing").astype(str)
    return d


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = load()
    labels = ["FM", "AFM", "FiM", "NM", "Unknown"]
    rows = []
    for b, g in d.groupby("bin", observed=True):
        row = {"multiplicity": b, "n": len(g), "share_near_zero_moment": g["near_zero"].mean(), "mean_m_fu": g["value"].mean(), "median_m_fu": g["value"].median()}
        for lab in labels:
            row[f"share_{lab}"] = float((g["order"] == lab).mean())
        rows.append(row)
    by = pd.DataFrame(rows)
    by.to_csv(OUT / "by_multiplicity.csv", index=False)
    rho_m = spearmanr(d["Z"], d["value"])
    magn = d[d["order"].isin(["FM", "AFM", "FiM"])]
    rho_o = spearmanr(magn["Z"], (magn["order"] == "FM").astype(int))
    summary = pd.DataFrame([{
        "n_rows": len(d), "share_near_zero_overall": d["near_zero"].mean(),
        "spearman_Z_vs_m_fu": rho_m.statistic, "spearman_Z_vs_is_FM_(FM_AFM_FiM_rows)": rho_o.statistic, "n_FM_AFM_FiM_rows": len(magn),
        "auc_Z_for_near_zero": roc_auc_score(d["near_zero"], d["Z"]), "auc_cell_atoms_for_near_zero": roc_auc_score(d["near_zero"], d["cell_atoms"]),
        "share_Z_gt_1": float((d["Z"] > 1.0001).mean()), "share_missing_ordering": float((d["order"] == "missing").mean())}])
    summary.to_csv(OUT / "summary.csv", index=False)
    pd.set_option("display.width", 220)
    print(by.round(3).to_string(index=False))
    print(summary.round(3).T.to_string(header=False))


if __name__ == "__main__":
    main()
