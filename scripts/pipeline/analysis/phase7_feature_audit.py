"""Phase 7 section 2.C: Tier 3 feature validity and leakage audit (static documentation + measured properties).

Output: phase7_tier3_feature_audit.csv (one row per Tier 3 physics predictor; the aggregation step later appends the
restricted-feature sensitivity evidence and the final inclusion decision) and phase7_tier3_excluded_columns.csv.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score

import phase6_common as pc
import phase6_cv as pcv

TARGET_FILES = {"ms_moment": "matched_split_ms.csv", "curie": "matched_split_curie.csv"}
HELD_OUT = {"p3_total_magnetization": "MP/JARVIS computed magnetic output - the quantity the Ms label comes from",
            "p3_magnetization_normalized_vol": "magnetic output normalised by volume",
            "p3_ordering": "MP computed magnetic ordering - a label of the ordering target",
            "p3_is_magnetic": "decision D3 (target-proximal)", "p3_num_magnetic_sites": "decision D3 (target-proximal)",
            "p3_magnetic_species": "decision D3 (target-proximal)", "p3_elastic_tensor": "decision D3 (non-scalar)"}
MAGNETIC_PATTERN = re.compile(r"magnet|moment|ordering|curie|neel|^tc|ms_", re.IGNORECASE)

# (family, physical definition, units, source / calculation stage, needed at prediction time, risk class)
META = {
    "p3_formation_energy_per_atom": ("Thermodynamic", "Formation energy per atom relative to elemental reference phases", "eV/atom",
                                     "MP: GGA/GGA+U total energy of the relaxed structure with MP corrections", "relaxed structure + DFT energy", "same_calculation"),
    "p3_energy_above_hull": ("Thermodynamic", "Energy above the convex hull of the chemical system", "eV/atom",
                             "MP: post-processing of DFT energies of all phases in the chemical system", "DFT energies of competing phases", "same_calculation"),
    "p3_is_stable": ("Thermodynamic", "Indicator energy_above_hull == 0", "bool", "MP: derived from energy_above_hull",
                     "DFT energies of competing phases", "same_calculation"),
    "p3_band_gap": ("Electronic", "Electronic band gap", "eV", "MP: GGA band structure / DOS of the (spin-polarised) relaxed structure",
                    "relaxed structure + DFT electronic structure", "same_calculation"),
    "p3_is_metal": ("Electronic", "Indicator band gap == 0", "bool", "MP: derived from the electronic structure", "DFT electronic structure", "same_calculation"),
    "p3_is_gap_direct": ("Electronic", "Indicator that the band gap is direct", "bool", "MP: band-structure analysis",
                         "DFT electronic structure", "same_calculation"),
    "p3_efermi": ("Electronic", "Fermi energy of the DFT run", "eV", "MP: DFT run output", "DFT electronic structure", "same_calculation"),
    "p3_vbm": ("Electronic", "Valence-band maximum (non-metals only)", "eV", "MP: band-structure analysis", "DFT electronic structure", "same_calculation"),
    "p3_cbm": ("Electronic", "Conduction-band minimum (non-metals only)", "eV", "MP: band-structure analysis", "DFT electronic structure", "same_calculation"),
    "p3_spacegroup_number": ("Symmetry", "International space-group number (1-230)", "-", "MP: symmetry analysis (spglib) of the relaxed structure",
                             "crystal structure", "symmetry_identity"),
    "p3_crystal_system": ("Symmetry", "Crystal system (7 classes)", "-", "MP: symmetry analysis of the relaxed structure", "crystal structure", "symmetry_identity"),
    "p3_point_group": ("Symmetry", "Crystallographic point group (32 classes)", "-", "MP: symmetry analysis of the relaxed structure",
                       "crystal structure", "symmetry_identity"),
    "p3_density": ("Structural", "Mass density of the cell", "g/cm^3", "MP/AFLOW/JARVIS: cell mass / relaxed cell volume", "crystal structure", "cell_size"),
    "p3_volume": ("Structural", "Unit-cell volume of the MP polymorph", "A^3", "MP: relaxed-structure cell volume", "crystal structure", "cell_size"),
    "p3_volume_per_atom": ("Structural", "Cell volume per atom (volume / volume_per_atom = number of sites in the MP cell)", "A^3/atom",
                           "MP: relaxed-structure cell volume per atom", "crystal structure", "cell_size"),
    "p3_bulk_modulus": ("Elastic", "Voigt-Reuss-Hill bulk modulus", "GPa", "MP elastic workflow (or JARVIS/AFLOW fallback): strain-stress DFT",
                        "relaxed structure + elastic-constant DFT", "independent_response"),
    "p3_shear_modulus": ("Elastic", "Voigt-Reuss-Hill shear modulus", "GPa", "MP elastic workflow (or JARVIS/AFLOW fallback)",
                         "relaxed structure + elastic-constant DFT", "independent_response"),
    "p3_poisson_ratio": ("Elastic", "Homogeneous Poisson ratio", "-", "MP elastic workflow (or fallback)", "elastic-constant DFT", "independent_response"),
    "p3_elastic_anisotropy": ("Elastic", "Universal elastic anisotropy index (ratio; unbounded for near-singular tensors)", "-",
                              "MP elastic workflow", "elastic-constant DFT", "independent_response"),
    "p3_dielectric_static": ("Dielectric", "Static dielectric constant (e_total)", "-", "MP/JARVIS: DFPT", "relaxed structure + DFPT", "independent_response"),
    "p3_dielectric_optical": ("Dielectric", "Electronic (optical) dielectric constant (e_electronic)", "-", "MP/JARVIS: DFPT", "relaxed structure + DFPT", "independent_response"),
    "p3_dielectric_ionic": ("Dielectric", "Ionic dielectric constant (e_ionic)", "-", "MP/JARVIS: DFPT", "relaxed structure + DFPT", "independent_response"),
    "p3_refractive_index": ("Dielectric", "Refractive index", "-", "MP: DFPT", "relaxed structure + DFPT", "independent_response"),
    "p3_piezo_max": ("Dielectric", "Maximum piezoelectric coefficient e_ij", "C/m^2", "MP/JARVIS: DFPT", "relaxed structure + DFPT", "independent_response"),
}

RISK_TEXT = {
    "same_calculation": "Output of the same family of spin-polarised DFT runs that produce the computational magnetic labels; "
                        "no direct target term, but computed-property dependence on the labelling method.",
    "symmetry_identity": "Coarse structural identifier shared by chemically related compounds; can act as a material-family proxy "
                         "even though splits are formula-grouped.",
    "cell_size": "Describes the size of one MP cell; a per-unit-cell target scales with the number of atoms in the cell "
                 "(volume / volume_per_atom = number of sites), so these columns can act as a cell-size proxy.",
    "independent_response": "Response property from a separate elastic or DFPT workflow; no obvious link to the magnetic target.",
}
FAMILY_VARIANT = {"same_calculation": "S_no_same_calculation_outputs", "symmetry_identity": "S_no_symmetry",
                  "cell_size": "S_no_volume_family", "independent_response": "S_elastic_dielectric_only"}


DERIVED_NSITES = "DERIVED: p3_volume / p3_volume_per_atom"


def derived_row() -> dict:
    """Not a model input: the number of sites in the MP cell implied by two Tier 3 columns (an exact integer)."""
    return {"feature": DERIVED_NSITES, "family": "Structural (derived)",
            "physical_definition": "Number of sites in the Materials Project cell (volume / volume per atom)", "units": "sites",
            "source_and_calculation_stage": "arithmetic on two Tier 3 columns", "available_from_composition_alone": False,
            "needed_at_prediction_time": "crystal structure", "join_level": "reduced_formula (MP polymorph)",
            "risk_class": "cell_size", "risk_description": RISK_TEXT["cell_size"] + " Audit-only row: documents what the volume family implies.",
            "restricted_variant_testing_this_risk": FAMILY_VARIANT["cell_size"]}


def matched_ids(target: str) -> pd.DataFrame:
    path = pc.EDA_ROOT / "02_splits" / "v1.2" / TARGET_FILES[target]
    return pd.read_csv(path, usecols=["material_id", "reduced_formula", "split"])


def provenance_share(cfg: dict, ids: set, columns: list[str]) -> pd.DataFrame:
    path = Path(cfg["paths"]["project_root"]) / "new_datasets/MMFD/phase3/data/property_provenance.csv"
    prov = pd.read_csv(path, usecols=["material_id"] + columns)
    prov = prov[prov["material_id"].isin(ids)]
    return pd.DataFrame({c: prov[c].fillna("missing").value_counts(normalize=True) for c in columns}).fillna(0.0).T


def is_categorical(x: pd.Series) -> bool:
    return x.dtype == object or str(x.dtype) == "category"


def univariate_grouped_r2(x: pd.Series, y: np.ndarray, groups: np.ndarray, seed: int) -> float:
    """Pooled out-of-fold R2 of a one-feature gradient-boosting model with formula-grouped 5-fold CV."""
    cat = is_categorical(x)
    frame = pd.DataFrame({"x": x.astype("category").cat.codes if cat else x.astype(float)})
    folds = pcv.group_folds(groups, 5, seed)
    oof = np.full(len(y), np.nan)
    for k in range(5):
        te = folds == k
        model = HistGradientBoostingRegressor(max_iter=100, max_leaf_nodes=15, learning_rate=0.1, random_state=seed,
                                              categorical_features=[0] if cat else None)
        model.fit(frame[~te], y[~te])
        oof[te] = model.predict(frame[te])
    return float(r2_score(y, oof))


def measure_feature(col: str, frame: pd.DataFrame) -> dict:
    x = frame[col]
    per_formula = frame.groupby("reduced_formula")[col].nunique(dropna=False)
    out = {"missing_pct": 100 * float(x.isna().mean()), "n_unique": int(x.nunique()),
           "max_unique_within_formula": int(per_formula.max())}
    if not is_categorical(x) and x.dtype != bool:
        xv = x.astype(float)
        out.update({"max_abs_value": float(xv.abs().max()), "n_rows_abs_value_gt_1e6": int((xv.abs() > 1e6).sum()),
                    "n_formulas_abs_value_gt_1e6": int(frame.loc[xv.abs() > 1e6, "reduced_formula"].nunique())})
    return out


def static_rows(physics: list[str]) -> dict[str, dict]:
    return {c: {"feature": c, "family": META[c][0], "physical_definition": META[c][1], "units": META[c][2],
                "source_and_calculation_stage": META[c][3], "available_from_composition_alone": False,
                "needed_at_prediction_time": META[c][4],
                "join_level": "reduced_formula (most stable MP polymorph; constant within a formula)",
                "risk_class": META[c][5], "risk_description": RISK_TEXT[META[c][5]],
                "restricted_variant_testing_this_risk": FAMILY_VARIANT[META[c][5]]} for c in physics}


def build_feature_audit(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    tier3 = pc.read_predictor_list(cfg, "tier3")
    physics = [c for c in tier3 if c.startswith("p3_")]
    missing_meta = set(physics) - set(META)
    if missing_meta:
        raise ValueError(f"no audit metadata for {sorted(missing_meta)}")
    seed = cfg["random_seed"]
    t3 = pd.read_parquet(pc.tier_path(cfg, "tier3"), columns=["material_id"] + physics)
    rows = static_rows(physics)
    rows[DERIVED_NSITES] = derived_row()
    for c in physics:
        x = t3[c]
        rows[c]["tier3_population_n"] = len(t3)
        rows[c]["tier3_population_missing_pct"] = 100 * float(x.isna().mean())
        if not is_categorical(x) and x.dtype != bool:
            rows[c]["tier3_population_n_abs_value_gt_1e6"] = int((x.astype(float).abs() > 1e6).sum())
    for target in TARGET_FILES:
        y = pc.load_target(cfg, target)[["material_id", "value", "_source"]]
        d = matched_ids(target).merge(y, on="material_id").merge(t3, on="material_id", how="left")
        d[DERIVED_NSITES] = d["p3_volume"] / d["p3_volume_per_atom"]
        prov = provenance_share(cfg, set(d["material_id"]), physics)
        mix = str(d["_source"].value_counts(normalize=True).round(4).to_dict())
        yv, groups = d["value"].to_numpy(dtype=float), d["reduced_formula"].to_numpy()
        for c in physics + [DERIVED_NSITES]:
            rows[c].update({f"{target}_{k}": v for k, v in measure_feature(c, d).items()})
            rows[c][f"{target}_share_values_from_MP_pct"] = 100 * float(prov.loc[c].get("MP", 0.0)) if c in prov.index else np.nan
            rows[c][f"{target}_univariate_grouped_cv_r2"] = univariate_grouped_r2(d[c], yv, groups, seed)
            informative = 1.0 < rows[c][f"{target}_missing_pct"] < 99.0
            rows[c][f"{target}_missing_indicator_grouped_cv_r2"] = (
                univariate_grouped_r2(d[c].isna().astype(float), yv, groups, seed) if informative else np.nan)
            rows[c][f"{target}_label_source_mix"] = mix
    excluded = pd.DataFrame([{"column": c, "reason": r, "in_tier3_predictors": c in tier3} for c, r in HELD_OUT.items()])
    flagged_p3 = [c for c in tier3 if c.startswith("p3_") and MAGNETIC_PATTERN.search(c)]
    flagged_comp = [c for c in tier3 if not c.startswith("p3_") and MAGNETIC_PATTERN.search(c)]
    excluded["p3_predictors_matching_magnetic_output_pattern"] = ", ".join(flagged_p3) if flagged_p3 else "none"
    excluded["composition_predictors_matching_pattern (formula-derived, allowed)"] = len(flagged_comp)
    return pd.DataFrame(rows.values()), excluded
