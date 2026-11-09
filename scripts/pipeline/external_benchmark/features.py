"""Tier 1 (composition-only) descriptors for an arbitrary formula, so that materials outside the dataset can be scored.

The 65 Tier 1 columns were produced by several notebooks (phase2.ipynb cells 10/12/13, my_cleaning.ipynb) and the v1.1 electronic-descriptor rebuild
(EDA/src/build_analysis_dataset_v1_1.py). This module re-implements them in one place and is VALIDATED against the stored values:
    python features.py validate        # recomputes a random sample of dataset rows and reports per-column agreement
Use compute_features(formula) -> dict for new materials.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pymatgen.core import Composition, Element

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "EDA" / "src"))
import build_analysis_dataset_v1_1 as b11  # noqa: E402  (electronic descriptor convention, D1)

TIER1 = [c.strip() for c in (ROOT / "EDA/00_config/tier1_predictors.txt").read_text(encoding="utf-8").splitlines() if c.strip()]
KEY_ELEMENTS = ["Fe", "Co", "Ni", "Mn", "Cr", "Gd", "Nd", "Sm", "Dy", "Tb", "B", "C", "N", "O"]
MAGNETIC_ELEMENTS = {"Fe", "Co", "Ni", "Mn", "Cr", "Gd", "Nd", "Sm", "Dy", "Tb"}    # the 10 key magnetic elements (checked against stored values)
_ELECTRONIC_TABLE = b11.build_element_table()


def _prop(el: Element, getter) -> float:
    try:
        v = getter(el)
        return float(v) if v is not None else np.nan
    except Exception:
        return np.nan


def _weighted(fracs: np.ndarray, arr: np.ndarray) -> float:
    return float(np.nansum(fracs * arr)) if not np.all(np.isnan(arr)) else np.nan


def _weighted_var(fracs: np.ndarray, arr: np.ndarray) -> float:
    m = _weighted(fracs, arr)
    return np.nan if np.isnan(m) else float(max(np.nansum(fracs * (arr - m) ** 2), 0))


def compute_features(formula: str) -> dict[str, float]:
    comp = Composition(formula)
    els = list(comp.elements)
    amts = np.array([comp[e] for e in els], dtype=float)
    total = amts.sum()
    fracs = amts / total
    frac_of = {e.symbol: f for e, f in zip(els, fracs)}
    out: dict[str, float] = {"basic_comp__n_elements": len(els), "basic_comp__total_atoms_formula": total}
    for tag, test in (("transition_metal", lambda e: e.is_transition_metal and e.symbol not in ("La", "Ac")), ("rare_earth", lambda e: e.is_lanthanoid),
                      ("actinide", lambda e: e.is_actinoid)):
        share = float(sum(f for e, f in zip(els, fracs) if test(e)))
        out[f"basic_comp__contains_{tag}"] = float(share > 0)
        out[f"basic_comp__{tag}_fraction"] = share
    out["basic_comp__magnetic_element_fraction"] = float(sum(f for e, f in zip(els, fracs) if e.symbol in MAGNETIC_ELEMENTS))
    for sym in KEY_ELEMENTS:
        out[f"basic_comp__contains_{sym}"] = float(sym in frac_of)
        out[f"basic_comp__fraction_{sym}"] = float(frac_of.get(sym, 0.0))
    for blk in ("d", "f", "s", "p"):
        out[f"magnetic_prior__{blk}_block_fraction"] = float(sum(f for e, f in zip(els, fracs) if e.block == blk))
    unp, d, f_, vec = b11.formula_descriptors(formula, _ELECTRONIC_TABLE)
    out.update({"average_unpaired_electron_proxy": unp, "average_d_electron_count": d, "average_f_electron_count": f_, "valence_electron_concentration": vec})
    radii = np.array([_prop(e, lambda x: x.atomic_radius) for e in els])
    en = np.array([_prop(e, lambda x: x.X) for e in els])
    masses = np.array([_prop(e, lambda x: x.atomic_mass) for e in els])
    melts = np.array([_prop(e, lambda x: x.melting_point) for e in els])
    periods = np.array([_prop(e, lambda x: x.row) for e in els])
    groups = np.array([_prop(e, lambda x: x.group) for e in els])
    r_avg = _weighted(fracs, radii)
    out.update({
        "average_atomic_radius": r_avg, "atomic_radius_variance": _weighted_var(fracs, radii),
        "atomic_size_mismatch": float(np.sqrt(np.nansum(fracs * ((radii - r_avg) / r_avg) ** 2))) if r_avg and r_avg > 0 else np.nan,
        "electronegativity_difference": float(np.nanmax(en) - np.nanmin(en)) if len(els) > 1 else 0.0,
        "electronegativity_variance": _weighted_var(fracs, en),
        "average_atomic_mass": _weighted(fracs, masses), "atomic_mass_variance": _weighted_var(fracs, masses),
        "average_melting_temperature": _weighted(fracs, melts), "melting_temperature_variance": _weighted_var(fracs, melts),
        "period_variance": _weighted_var(fracs, periods), "group_variance": _weighted_var(fracs, groups),
        "mixing_entropy": float(-np.sum(fracs * np.log(np.clip(fracs, 1e-12, None)))),
    })
    # the formula-complexity block was computed on the REDUCED formula in the original pipeline (e.g. Ba4O12Ti4 -> BaTiO3, total_atoms 5)
    red = Composition(comp.reduced_formula)
    amts = np.array([red[e] for e in red.elements], dtype=float)
    total, fracs = amts.sum(), amts / amts.sum()
    ent = -np.sum(fracs * np.log(np.clip(fracs, 1e-12, None)))
    n = len(els)
    norm_ent = ent / np.log(n) if n > 1 else 0.0
    out.update({"formula_entropy": float(ent), "normalized_formula_entropy": float(norm_ent), "formula_complexity_index": float(n * norm_ent),
                "formula_complexity": float(n * (1 + norm_ent)), "stoichiometric_variance": float(np.var(amts)),
                "maximum_stoichiometric_coefficient": float(amts.max()), "number_of_unique_elements": float(n), "total_atoms": float(total)})
    return out


def feature_frame(formulas: list[str]) -> pd.DataFrame:
    """Feature table for many formulas. Unparseable formulas become all-NaN rows; the number and first cause are printed, never hidden."""
    rows, failures = [], []
    for f in formulas:
        try:
            rows.append(compute_features(f))
        except Exception as exc:       # noqa: BLE001 - reported below
            rows.append({c: np.nan for c in TIER1})
            failures.append((f, repr(exc)))
    if failures:
        print(f"feature_frame: {len(failures)}/{len(formulas)} formulas failed; first: {failures[0]}")
    return pd.DataFrame(rows)[TIER1]


def validate(n_rows: int = 3000, seed: int = 0) -> pd.DataFrame:
    stored = pd.read_parquet(ROOT / "EDA/datasets/v1.2/tiers/tier1_core_v1.2.parquet", columns=["formula_clean"] + TIER1)
    sample = stored.dropna(subset=["formula_clean"]).sample(n_rows, random_state=seed).reset_index(drop=True)
    new = feature_frame(sample["formula_clean"].tolist())
    rows = []
    for c in TIER1:
        a, b = sample[c].to_numpy(dtype=float), new[c].to_numpy(dtype=float)
        both = ~(np.isnan(a) | np.isnan(b))
        close = np.isclose(a[both], b[both], rtol=1e-3, atol=1e-4)
        rows.append({"column": c, "n_compared": int(both.sum()), "share_matching": float(close.mean()) if both.any() else np.nan,
                     "max_abs_diff": float(np.abs(a[both] - b[both]).max()) if both.any() else np.nan,
                     "missing_stored": int(np.isnan(a).sum()), "missing_new": int(np.isnan(b).sum())})
    return pd.DataFrame(rows)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "validate":
    pd.set_option("display.width", 200, "display.max_rows", 100)
    table = validate()
    table.to_csv(ROOT / "new_materials_finding" / "feature_validation.csv", index=False, encoding="utf-8")
    print(table.round(4).to_string(index=False))
    print(f"columns fully matching: {int((table['share_matching'] > 0.999).sum())}/{len(table)}")
