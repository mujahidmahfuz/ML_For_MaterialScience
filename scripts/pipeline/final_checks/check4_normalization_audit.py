"""Final check 4: audit of the Phase 8 per-atom Ms normalisation (numerator / denominator cell consistency).

Per-atom target used in Phase 8 (run_phase8_peratom_ms.py):  Ms_momentPerUnitCell_clean / n_sites,  n_sites = p3_volume / p3_volume_per_atom,
where the p3_* fields are the Materials Project record chosen per reduced formula in Phase 3 (best polymorph), while the numerator is the DFT total
moment of the SOURCE ROW'S OWN cell: JARVIS-DFT (magmom_oszicar, JARVIS cell) for 72% of the matched rows, Materials Project total_magnetization
(MP cell, original mp-id no longer stored) for 28%.  The numerator and denominator therefore refer to the same cell only if those cells coincide.

This script
  1. validates the denominator (finite, positive, integer after rounding, equal to the MP nsites stored in Phase 3);
  2. recovers the true atom count of the numerator's cell:  JARVIS rows -> dft_3d record (reference == DOI, formula, moment) -> atoms in the JARVIS cell;
     MP rows -> raw MP rows with the same reduced formula and moment (candidate mp-ids) -> nsites from the MP API;
  3. classifies every matched row (cell-consistent same record / consistent different record / atom-count mismatch / ambiguous), by source and cell size;
  4. verifies the arithmetic of the stored Phase 8 per-atom targets;
  5. builds a stratified, seeded sample of material-level checks (volume per atom of the two cells, MP vs JARVIS) and writes the row-level mapping used by
     check4_peratom_rerun.py.
Usage (from EDA/src, OMP_NUM_THREADS unset):  python ../../final/scripts/check4_normalization_audit.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parents[2] / "EDA" / "src"
sys.path.insert(0, str(SRC))

import phase6_common as pc  # noqa: E402
import phase7_validation as p7  # noqa: E402

FINAL = Path(__file__).resolve().parents[1]
OUT = FINAL / "outputs" / "check4_peratom"
WORK = FINAL / "work"
ROOT = FINAL.parent
MOMENT_DECIMALS = 4              # the Saturation_Magnetization strings carry 4 decimals
SAMPLE_PER_CELL = 8
SAMPLE_SEED = 20267400
P3_COLUMNS = ["material_id", "p3_mp_material_id", "p3_nsites", "p3_volume", "p3_volume_per_atom", "p3_density", "p3_total_magnetization"]


def matched_rows() -> pd.DataFrame:
    """Matched Ms population (dataset v1.2, 10,852 rows) with numerator, source and the Phase 3 MP-record fields."""
    target = pd.read_csv(pc.EDA_ROOT / "datasets/v1.2/targets/ms/target_ms_clean.csv", low_memory=False,
                         usecols=["material_id", "reduced_formula", "_source", "DOI", "Ms_momentPerUnitCell_clean"])
    matched = pd.read_csv(p7.split_dir("v1.2") / "matched_split_ms.csv", usecols=["material_id", "split"])
    p3 = pd.read_csv(ROOT / "combine_updated_dataset.csv", usecols=P3_COLUMNS, low_memory=False)
    d = matched.merge(target, on="material_id", validate="one_to_one").merge(p3, on="material_id", how="left", validate="one_to_one")
    d["n_sites_raw"] = d["p3_volume"] / d["p3_volume_per_atom"]
    d["n_used"] = d["n_sites_raw"].round().astype("Int64")
    return d


def denominator_checks(d: pd.DataFrame) -> pd.DataFrame:
    n = d["n_sites_raw"]
    checks = {
        "matched rows": len(d),
        "denominator finite": int(np.isfinite(n).sum()),
        "denominator > 0": int((n > 0).sum()),
        "zero or missing denominators": int((~(n > 0)).sum()),
        "denominator integer within 1e-6": int(((n - n.round()).abs() < 1e-6).sum()),
        "max |n_sites_raw - round(n_sites_raw)|": float((n - n.round()).abs().max()),
        "denominator equals stored MP nsites (p3_nsites)": int((d["n_used"] == d["p3_nsites"]).sum()),
        "numerator finite": int(np.isfinite(d["Ms_momentPerUnitCell_clean"]).sum()),
        "numerator exactly 0 (valid non-magnetic rows)": int((d["Ms_momentPerUnitCell_clean"] == 0).sum()),
        "denominator range (min)": int(round(n.min())), "denominator range (max)": int(round(n.max()))}
    return pd.DataFrame({"check": list(checks), "value": list(checks.values())})


# ------------------------------------------------------------------------------------------------ JARVIS side
def jarvis_cell_atoms(d: pd.DataFrame) -> pd.DataFrame:
    """Atoms (and volume) of the JARVIS cell that produced each JARVIS-sourced moment."""
    from jarvis.db.figshare import data
    from pymatgen.core import Composition

    records = []
    for r in data("dft_3d"):
        try:
            formula = Composition(r["formula"]).reduced_formula
        except Exception:   # noqa: BLE001  (malformed formula strings are simply unmatched)
            formula = None
        lat = np.array(r["atoms"]["lattice_mat"], dtype=float)
        records.append({"jid": r["jid"], "reference": str(r.get("reference")), "reduced_formula": formula,
                        "magmom_oszicar": pd.to_numeric(r.get("magmom_oszicar"), errors="coerce"),
                        "magmom_outcar": pd.to_numeric(r.get("magmom_outcar"), errors="coerce"),
                        "jarvis_atoms": len(r["atoms"]["elements"]), "jarvis_volume": abs(float(np.linalg.det(lat)))})
    jar = pd.DataFrame(records)
    jar["m4"] = jar["magmom_oszicar"].round(MOMENT_DECIMALS)
    rows = d[d["_source"] == "jarvis_magnetic.csv"].assign(m4=lambda x: x["Ms_momentPerUnitCell_clean"].round(MOMENT_DECIMALS)).reset_index(names="row")
    cand = rows.merge(jar, on=["reduced_formula", "m4"], how="left", suffixes=("", "_j"))

    def pick(g: pd.DataFrame) -> pd.Series:
        g = g[g["jid"].notna()]
        if g.empty:
            return pd.Series({"cell_atoms_numerator": np.nan, "numerator_record": None, "n_candidates": 0, "n_distinct_atoms": 0,
                              "jarvis_volume": np.nan, "magmom_outcar": np.nan, "record_linked": False})
        linked = g[g["reference"] == g["DOI"].astype(str)]
        use = linked if len(linked) else g
        return pd.Series({"cell_atoms_numerator": use["jarvis_atoms"].iloc[0], "numerator_record": use["jid"].iloc[0], "n_candidates": len(g),
                          "n_distinct_atoms": use["jarvis_atoms"].nunique(), "jarvis_volume": use["jarvis_volume"].iloc[0],
                          "magmom_outcar": use["magmom_outcar"].iloc[0], "record_linked": len(linked) > 0})
    res = cand.groupby("row").apply(pick, include_groups=False)
    out = rows.set_index("row")[["material_id"]].join(res)
    out.loc[out["n_distinct_atoms"] > 1, "cell_atoms_numerator"] = np.nan      # candidates disagree on the atom count -> ambiguous
    return out.set_index("material_id")


# ------------------------------------------------------------------------------------------------ MP side
def mp_cell_atoms(d: pd.DataFrame) -> pd.DataFrame:
    """Atoms of the MP cell that produced each MP-sourced moment: raw MP rows with the same reduced formula and moment give the candidate mp-ids."""
    from pymatgen.core import Composition

    cache = WORK / "mp_candidates_api.parquet"
    rows = d[d["_source"] == "mp_reformatted.csv"].assign(m4=lambda x: x["Ms_momentPerUnitCell_clean"].round(MOMENT_DECIMALS))
    raw = pd.read_csv(ROOT / "raw_MP_magnetic_materials.csv", usecols=["material_id", "formula", "magnetic_moment"])
    memo: dict[str, str | None] = {}

    def reduced(f: str) -> str | None:
        if f not in memo:
            try:
                memo[f] = Composition(f).reduced_formula
            except Exception:   # noqa: BLE001
                memo[f] = None
        return memo[f]
    raw = raw.assign(reduced_formula=raw["formula"].map(reduced), m4=raw["magnetic_moment"].round(MOMENT_DECIMALS)).rename(columns={"material_id": "mp_id"})
    cand = rows.reset_index(names="row").merge(raw[["mp_id", "reduced_formula", "m4"]], on=["reduced_formula", "m4"], how="left")
    ids_by_row = cand.groupby("row")["mp_id"].agg(lambda s: sorted(s.dropna()))
    wanted = sorted({i for ids in ids_by_row for i in ids})
    if cache.exists():
        api = pd.read_parquet(cache)
    else:
        from mp_api.client import MPRester
        key = os.environ["MP_API_KEY"]  # set your own Materials Project API key
        fetched = []
        with MPRester(key) as mpr:
            for i in range(0, len(wanted), 400):
                docs = mpr.materials.summary.search(material_ids=wanted[i:i + 400], chunk_size=200,
                                                    fields=["material_id", "nsites", "volume", "total_magnetization", "formula_pretty"])
                fetched += [{"material_id": str(x.material_id), "nsites": x.nsites, "volume": x.volume,
                             "total_magnetization": x.total_magnetization, "formula_pretty": x.formula_pretty} for x in docs]
        api = pd.DataFrame(fetched)
        api.to_parquet(cache)
    api = api.set_index("material_id")
    out = []
    for row, material_id in zip(rows.reset_index(names="row")["row"], rows["material_id"]):
        ids = [i for i in ids_by_row.get(row, []) if i in api.index]
        sites = sorted({int(api.loc[i, "nsites"]) for i in ids})
        first = ids[0] if ids else None
        out.append({"material_id": material_id, "cell_atoms_numerator": sites[0] if len(sites) == 1 else np.nan,
                    "numerator_record": ",".join(ids[:3]) if ids else None, "n_candidates": len(ids), "n_distinct_atoms": len(sites),
                    "jarvis_volume": np.nan, "magmom_outcar": np.nan,
                    "mp_volume": float(api.loc[first, "volume"]) if len(sites) == 1 and first else np.nan,
                    "record_linked": False, "candidate_ids": ids})
    return pd.DataFrame(out).set_index("material_id")


# ------------------------------------------------------------------------------------------------ classification
def classify(d: pd.DataFrame) -> pd.DataFrame:
    jar, mp = jarvis_cell_atoms(d), mp_cell_atoms(d)
    p3_id = d.set_index("material_id")["p3_mp_material_id"]
    mp["record_linked"] = [p3_id.loc[m] in ids for m, ids in zip(mp.index, mp["candidate_ids"])]
    cell = pd.concat([jar, mp.drop(columns=["candidate_ids"])])
    d = d.merge(cell, left_on="material_id", right_index=True, how="left", validate="one_to_one")
    d["same_mp_record"] = np.where(d["_source"] == "jarvis_magnetic.csv", d["DOI"].astype(str) == d["p3_mp_material_id"].astype(str),
                                   d["record_linked"].fillna(False).astype(bool)).astype(bool)
    resolved = d["cell_atoms_numerator"].notna()
    equal = (d["cell_atoms_numerator"] == d["n_used"].astype(float)).fillna(False).astype(bool)
    d["category"] = np.select(
        [~resolved & (d["_source"] != "magnetic_anisotropy_materials.csv"), equal & d["same_mp_record"], equal & ~d["same_mp_record"], ~equal & resolved],
        ["ambiguous_or_unresolved", "consistent_same_record", "consistent_atoms_different_record", "mismatch_atoms"], default="experimental_no_cell_reference")
    d["atom_ratio_numerator_to_used"] = d["cell_atoms_numerator"] / d["n_used"]
    d["per_atom_phase8"] = d["Ms_momentPerUnitCell_clean"] / d["n_sites_raw"]
    d["per_atom_corrected"] = d["Ms_momentPerUnitCell_clean"] / d["cell_atoms_numerator"]
    d["size_bin"] = pd.cut(d["n_used"].astype(float), [0, 4, 10, 20, 200], labels=["1-4", "5-10", "11-20", ">20"])
    return d


def summaries(d: pd.DataFrame) -> dict[str, pd.DataFrame]:
    by_source = d.groupby(["_source", "category"]).size().rename("rows").reset_index()
    by_source["share_of_source_pct"] = 100 * by_source["rows"] / by_source.groupby("_source")["rows"].transform("sum")
    by_size = d.groupby(["size_bin", "category"], observed=True).size().rename("rows").reset_index()
    by_size["share_of_bin_pct"] = 100 * by_size["rows"] / by_size.groupby("size_bin", observed=True)["rows"].transform("sum")
    mism = d[d["category"] == "mismatch_atoms"]
    ratio = mism["atom_ratio_numerator_to_used"].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).rename("atom_ratio_numerator_to_used").reset_index()
    ratio["rows_wrong_by_factor_of_2_or_more_pct"] = 100 * ((mism["atom_ratio_numerator_to_used"] >= 2) | (mism["atom_ratio_numerator_to_used"] <= 0.5)).mean()
    totals = d.groupby("category").size().rename("rows").reset_index()
    totals["share_pct"] = 100 * totals["rows"] / len(d)
    return {"normalization_audit_by_category.csv": totals, "normalization_audit_by_source.csv": by_source, "normalization_audit_by_cell_size.csv": by_size,
            "normalization_mismatch_ratio.csv": ratio}


def volume_per_atom_check(d: pd.DataFrame) -> pd.DataFrame:
    """If the MP and JARVIS cells describe the same material in different settings, volume per ATOM agrees even when the atom counts differ."""
    j = d[(d["_source"] == "jarvis_magnetic.csv") & d["jarvis_volume"].notna()].copy()
    j["vpa_jarvis"] = j["jarvis_volume"] / j["cell_atoms_numerator"]
    j["vpa_ratio_jarvis_over_mp"] = j["vpa_jarvis"] / j["p3_volume_per_atom"]
    rows = []
    for cat, g in j.groupby("category"):
        r = g["vpa_ratio_jarvis_over_mp"]
        rows.append({"category": cat, "rows": len(g), "median_ratio": r.median(), "share_within_10pct": float(((r - 1).abs() < 0.10).mean()),
                     "share_within_25pct": float(((r - 1).abs() < 0.25).mean()), "share_off_by_more_than_50pct": float(((r - 1).abs() > 0.50).mean())})
    return pd.DataFrame(rows)


def stored_target_check(d: pd.DataFrame) -> pd.DataFrame:
    """The arithmetic of the stored Phase 8 per-atom targets: y_true in peratom__<split>.parquet vs moment / (p3_volume / p3_volume_per_atom)."""
    rows = []
    base = pc.EDA_ROOT / "14_phase8_peratom"
    ref = d.set_index("material_id")["per_atom_phase8"]
    for split in range(10):
        p = pd.read_parquet(base / f"peratom__{split}.parquet", columns=["material_id", "y_true"]).drop_duplicates("material_id")
        diff = (p["y_true"].to_numpy() - ref.loc[p["material_id"]].to_numpy())
        rows.append({"split_id": split, "n_test_rows": len(p), "max_abs_difference": float(np.abs(diff).max())})
    return pd.DataFrame(rows)


def material_sample(d: pd.DataFrame) -> pd.DataFrame:
    """Seeded stratified sample: SAMPLE_PER_CELL rows per (source x category), spread over cell-size bins."""
    rng = np.random.default_rng(SAMPLE_SEED)
    parts = []
    for (_, _), g in d.groupby(["_source", "category"]):
        take = min(SAMPLE_PER_CELL, len(g))
        order = g.assign(r=rng.random(len(g))).sort_values(["size_bin", "r"])
        idx = np.linspace(0, len(order) - 1, take).round().astype(int)       # evenly spaced through the size-sorted list
        parts.append(order.iloc[np.unique(idx)])
    s = pd.concat(parts)
    cols = ["material_id", "_source", "category", "reduced_formula", "DOI", "p3_mp_material_id", "numerator_record", "Ms_momentPerUnitCell_clean",
            "cell_atoms_numerator", "n_used", "atom_ratio_numerator_to_used", "per_atom_phase8", "per_atom_corrected", "p3_volume_per_atom",
            "jarvis_volume", "mp_volume", "magmom_outcar", "p3_total_magnetization"]
    return s[cols].rename(columns={"_source": "source"})


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = matched_rows()
    denominator_checks(d).to_csv(OUT / "denominator_integrity_checks.csv", index=False, encoding="utf-8")
    d = classify(d)
    for name, table in summaries(d).items():
        table.to_csv(OUT / name, index=False, encoding="utf-8")
    volume_per_atom_check(d).to_csv(OUT / "normalization_volume_per_atom_check.csv", index=False, encoding="utf-8")
    stored_target_check(d).to_csv(OUT / "stored_per_atom_target_arithmetic_check.csv", index=False, encoding="utf-8")
    material_sample(d).to_csv(OUT / "representative_material_checks.csv", index=False, encoding="utf-8")
    keep = ["material_id", "reduced_formula", "_source", "DOI", "p3_mp_material_id", "Ms_momentPerUnitCell_clean", "n_used", "cell_atoms_numerator",
            "numerator_record", "same_mp_record", "category", "atom_ratio_numerator_to_used", "per_atom_phase8", "per_atom_corrected", "size_bin"]
    d[keep].to_csv(OUT / "normalization_audit_rows.csv", index=False, encoding="utf-8")
    d[keep].assign(size_bin=d["size_bin"].astype(str), n_used=d["n_used"].astype(int)).to_parquet(WORK / "peratom_cell_map.parquet")
    pd.set_option("display.width", 220, "display.max_columns", 30)
    for name in ("denominator_integrity_checks.csv", "normalization_audit_by_category.csv", "normalization_audit_by_source.csv",
                 "normalization_audit_by_cell_size.csv", "normalization_mismatch_ratio.csv", "normalization_volume_per_atom_check.csv",
                 "stored_per_atom_target_arithmetic_check.csv"):
        print(name)
        print(pd.read_csv(OUT / name).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
