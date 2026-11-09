"""Interpretability helpers for Phase 6 Stage 6: descriptor families and exact TreeSHAP for XGBoost.

Families follow plan s11 (composition, d/f-electron proxies, oxidation/chemistry, symmetry, electronic structure,
stability, structural packing, ...). Every Tier 1-3 predictor belongs to exactly one family; an unmapped feature is an
error, so a changed predictor list cannot silently fall out of the family summaries.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
import xgboost as xgb

COMPOSITION = "Composition & stoichiometry"
MAGNETIC_ELEMENTS = "Magnetic-element content"
LIGHT_ELEMENTS = "Light-element (B/C/N/O) content"
DF_ELECTRON = "d/f-electron & valence proxies"
ATOMIC = "Atomic size & periodic statistics"
OXIDATION = "Oxidation chemistry"
STABILITY = "Thermodynamic stability"
ELECTRONIC = "Electronic structure"
SYMMETRY = "Symmetry"
PACKING = "Structural packing"
ELASTIC = "Elastic response"
DIELECTRIC = "Dielectric & optical"

FAMILY_ORDER = [COMPOSITION, MAGNETIC_ELEMENTS, LIGHT_ELEMENTS, DF_ELECTRON, ATOMIC, OXIDATION,
                STABILITY, ELECTRONIC, SYMMETRY, PACKING, ELASTIC, DIELECTRIC]
PHYSICS_FAMILIES = [STABILITY, ELECTRONIC, SYMMETRY, PACKING, ELASTIC, DIELECTRIC]   # the Tier 3 additions

_P3 = {
    "p3_formation_energy_per_atom": STABILITY, "p3_energy_above_hull": STABILITY, "p3_is_stable": STABILITY,
    "p3_band_gap": ELECTRONIC, "p3_is_metal": ELECTRONIC, "p3_is_gap_direct": ELECTRONIC, "p3_efermi": ELECTRONIC,
    "p3_vbm": ELECTRONIC, "p3_cbm": ELECTRONIC,
    "p3_spacegroup_number": SYMMETRY, "p3_crystal_system": SYMMETRY, "p3_point_group": SYMMETRY,
    "p3_density": PACKING, "p3_volume": PACKING, "p3_volume_per_atom": PACKING,
    "p3_bulk_modulus": ELASTIC, "p3_shear_modulus": ELASTIC, "p3_poisson_ratio": ELASTIC, "p3_elastic_anisotropy": ELASTIC,
    "p3_dielectric_static": DIELECTRIC, "p3_dielectric_optical": DIELECTRIC, "p3_dielectric_ionic": DIELECTRIC,
    "p3_refractive_index": DIELECTRIC, "p3_piezo_max": DIELECTRIC,
}
_COMPOSITION = {"basic_comp__n_elements", "basic_comp__total_atoms_formula", "mixing_entropy", "formula_entropy",
                "normalized_formula_entropy", "formula_complexity", "formula_complexity_index", "stoichiometric_variance",
                "maximum_stoichiometric_coefficient", "number_of_unique_elements", "total_atoms"}
_DF_ELECTRON = {"average_unpaired_electron_proxy", "average_d_electron_count", "average_f_electron_count",
                "valence_electron_concentration"}
_ATOMIC = {"average_atomic_radius", "atomic_radius_variance", "atomic_size_mismatch", "electronegativity_difference",
           "electronegativity_variance", "average_atomic_mass", "atomic_mass_variance", "average_melting_temperature",
           "melting_temperature_variance", "period_variance", "group_variance"}
_OXIDATION = {"avg_oxidation_state", "minimum_oxidation_state", "maximum_oxidation_state", "oxidation_state_range",
              "oxidation_state_variance", "oxidation_state_std", "number_of_possible_oxidation_states",
              "oxidation_solution_found"}
_ELEMENT_FLAG = re.compile(r"^basic_comp__(contains|fraction)_([A-Z][a-z]?)$")
_LIGHT = {"B", "C", "N", "O"}
_CLASS_CONTENT = {"basic_comp__contains_transition_metal", "basic_comp__transition_metal_fraction",
                  "basic_comp__contains_rare_earth", "basic_comp__rare_earth_fraction",
                  "basic_comp__contains_actinide", "basic_comp__actinide_fraction", "basic_comp__magnetic_element_fraction"}


def feature_family(name: str) -> str:
    """Descriptor family of one predictor column; KeyError if the column is not covered by the rules."""
    if name in _P3:
        return _P3[name]
    if name in _OXIDATION:
        return OXIDATION
    if name in _COMPOSITION:
        return COMPOSITION
    if name in _DF_ELECTRON or name.startswith("magnetic_prior__"):
        return DF_ELECTRON
    if name in _ATOMIC:
        return ATOMIC
    if name in _CLASS_CONTENT:
        return MAGNETIC_ELEMENTS
    m = _ELEMENT_FLAG.match(name)
    if m:
        return LIGHT_ELEMENTS if m.group(2) in _LIGHT else MAGNETIC_ELEMENTS
    raise KeyError(f"no descriptor family defined for predictor '{name}'")


def family_map(features: list[str]) -> pd.Series:
    return pd.Series({f: feature_family(f) for f in features}, name="family")


def tree_shap(model, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Exact TreeSHAP from the XGBoost booster (handles NaN and category dtype natively).

    Returns (values, bias): values is (n, features) for regression or (n, classes, features) for multi-class, in margin
    units (target units for regression, log-odds for classification); contributions + bias reproduce the raw margin."""
    booster = model.get_booster() if hasattr(model, "get_booster") else model
    contrib = booster.predict(xgb.DMatrix(X, enable_categorical=True), pred_contribs=True)
    return contrib[..., :-1], contrib[..., -1]


def global_importance(values: np.ndarray, features: list[str]) -> pd.Series:
    """Mean |SHAP| per feature; for multi-class, mean |SHAP| averaged over the classes."""
    a = np.abs(values)
    per_feature = a.mean(axis=0) if a.ndim == 2 else a.mean(axis=0).mean(axis=0)
    return pd.Series(per_feature, index=features, name="mean_abs_shap")


def family_share(importance: pd.Series) -> pd.Series:
    """Fraction of total mean |SHAP| carried by each descriptor family (sums to 1), in FAMILY_ORDER."""
    fam = family_map(list(importance.index))
    share = importance.groupby(fam).sum()
    share = share / share.sum()
    return share.reindex([f for f in FAMILY_ORDER if f in share.index])
