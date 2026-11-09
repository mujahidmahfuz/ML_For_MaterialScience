"""Blind test on an independent experimental Curie-temperature dataset (Deviation 3 in PLAN.md).

Data: 2,500 ferromagnets with experimental Curie temperatures and the DOI of the source paper (malaei/Magnetic_data, FM/; no licence stated, used for
evaluation only, not redistributed). For each compound we ask: is its reduced formula in our training repository? is its chemical system? does its DOI
appear in our Curie training data? The Curie model (Tier 1, v1.3, trained on 80% of the formulas, normalized conformal 90% intervals calibrated on the other
20%) then predicts every parsable compound. Compounds whose formula we never trained on are the blind test; those whose paper we never used are the
strictest subset. Usage (from this folder, OMP_NUM_THREADS unset):  python predict_external.py
Outputs: external_predictions.csv, external_summary.csv
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import features as F  # noqa: E402
import predict_candidates as pc_  # noqa: E402
import phase7_validation as p7  # noqa: E402

ROOT = F.ROOT
SOURCE = HERE / "external_data" / "malaei_Magnetic_data" / "curie_temperature_of_ferromagnetic_materials.csv"


def normalise_doi(value) -> str:
    return re.sub(r"[\[\]\s]", "", str(value)).lower()


def load_external() -> pd.DataFrame:
    ext = pd.read_csv(SOURCE, keep_default_na=False, na_values=[""]).rename(columns={"Names": "name", "Normalised Value": "tc_exp_k", "DOI": "doi"})
    ext["doi_norm"] = ext["doi"].map(normalise_doi)
    reduced = []
    for name in ext["name"]:
        try:
            reduced.append(F.Composition(name).reduced_formula)
        except Exception:       # noqa: BLE001 - unparsable names are counted and dropped below
            reduced.append(None)
    ext["reduced_formula"] = reduced
    return ext


def training_flags(ext: pd.DataFrame) -> pd.DataFrame:
    repo = set(pd.read_parquet(ROOT / "EDA/datasets/v1.2/feature_repository_v1.2.parquet", columns=["reduced_formula"])["reduced_formula"].dropna())
    curie = pd.read_csv(ROOT / "EDA/datasets/v1.3/targets/curie/target_curie_clean.csv", usecols=["reduced_formula", "DOI", "target_valid"], low_memory=False)
    curie = curie[curie["target_valid"].astype(bool)]
    curie_dois = {normalise_doi(d) for d in curie["DOI"].dropna()}
    systems = set()
    for f in repo:
        try:
            systems.add(F.Composition(f).chemical_system)
        except Exception:       # noqa: BLE001 - leftover non-chemical strings add no system
            continue
    out = ext.copy()
    out["formula_in_repository"] = out["reduced_formula"].isin(repo)
    out["formula_in_curie_training"] = out["reduced_formula"].isin(set(curie["reduced_formula"]))
    out["chemical_system"] = [F.Composition(f).chemical_system if f else None for f in out["reduced_formula"]]
    out["system_seen"] = out["chemical_system"].isin(systems)
    out["doi_in_curie_training"] = out["doi_norm"].isin(curie_dois)
    return out


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    groups = {
        "all parsable": df,
        "formula seen in training": df[df["formula_in_repository"]],
        "formula NEVER seen (blind)": df[~df["formula_in_repository"]],
        "blind + paper never used": df[~df["formula_in_repository"] & ~df["doi_in_curie_training"]],
        "blind + unseen chemical system": df[~df["formula_in_repository"] & ~df["system_seen"]],
        "blind + paper never used + unseen system": df[~df["formula_in_repository"] & ~df["doi_in_curie_training"] & ~df["system_seen"]],
    }
    rows = []
    for name, g in groups.items():
        if len(g) == 0:
            continue
        err = (g["tc_pred_k"] - g["tc_exp_k"]).abs()
        ss_res, ss_tot = float(((g["tc_exp_k"] - g["tc_pred_k"]) ** 2).sum()), float(((g["tc_exp_k"] - g["tc_exp_k"].mean()) ** 2).sum())
        rows.append({"subset": name, "n": len(g), "n_papers": g["doi_norm"].nunique(), "mae_k": err.mean(), "median_ae_k": err.median(),
                     "r2": 1 - ss_res / ss_tot if ss_tot > 0 else np.nan, "coverage_90pct_interval": float(g["in_interval"].mean()),
                     "mean_interval_width_k": float((g["tc_hi_k"] - g["tc_lo_k"]).mean()), "mean_exp_tc_k": g["tc_exp_k"].mean(),
                     "share_within_50k": float((err <= 50).mean())})
    return pd.DataFrame(rows)


def main() -> None:
    p7.install_diagnostic_algorithm()
    ext = training_flags(load_external().dropna(subset=["reduced_formula"]).drop_duplicates("name"))
    print(f"external compounds parsed: {len(ext):,}", flush=True)
    x = F.feature_frame(ext["reduced_formula"].tolist())
    ok = x.notna().all(axis=1).to_numpy()
    ext, x = ext[ok].reset_index(drop=True), x[ok].reset_index(drop=True)
    print(f"scoreable: {len(ext):,}; formula never seen: {int((~ext['formula_in_repository']).sum()):,}; "
          f"blind and paper never used: {int((~ext['formula_in_repository'] & ~ext['doi_in_curie_training']).sum()):,}", flush=True)
    pred = pc_.fit_curie(x)
    out = pd.concat([ext, pred], axis=1)
    out["in_interval"] = (out["tc_exp_k"] >= out["tc_lo_k"]) & (out["tc_exp_k"] <= out["tc_hi_k"])
    out["abs_err_k"] = (out["tc_pred_k"] - out["tc_exp_k"]).abs()
    out.to_csv(HERE / "external_predictions.csv", index=False, encoding="utf-8")
    summary = summarise(out)
    summary.to_csv(HERE / "external_summary.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 220, "display.max_columns", 20)
    print(summary.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
