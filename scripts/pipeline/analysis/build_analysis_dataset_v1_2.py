"""Build Analysis Dataset v1.2 from frozen v1.1 (reviewer decision D7 of 2026-09-28).

D7: materials whose reduced_formula is not a chemical formula (mineral names, acronyms, structural templates,
text-mining corruptions) carry pseudo-values in every composition descriptor. They are moved to a quarantine
file with all their columns and clean target values, and excluded from every analysis population.
v1.1 inputs are read-only; every v1.2 file is new, under EDA/datasets/v1.2/.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from pymatgen.core import Composition, Element

ROOT = Path(__file__).resolve().parents[2]
V11 = ROOT / "EDA/datasets/v1.1"
OUT = ROOT / "EDA/datasets/v1.2"
D1_COLS = ["average_unpaired_electron_proxy", "average_d_electron_count", "average_f_electron_count",
           "valence_electron_concentration"]
FIRST_SYNTHETIC_SUPERHEAVY_Z = 104
REAL_ELEMENTS = {el.symbol for el in Element}
EXPECTED_D7_N = 1940
REASON = ("v1.2 D7: reduced_formula is not a chemical formula (unparseable, unknown symbol, or synthetic "
          "superheavy element such as the 'BaTiOg' corruption of BaTiO3); composition descriptors are pseudo-values")
TAG = "D7_excluded_pseudo_formula"
TIER_FILES = ["tier1_core", "tier2_extended", "tier3_physics"]
TARGETS = {  # file, validity column, clean value columns
    "ordering": ("ordering/target_ordering_clean.csv", "ordering_valid", ["magnetic_ordering_clean"]),
    "curie": ("curie/target_curie_clean.csv", "target_valid", ["TC_K_clean"]),
    "ms": ("ms/target_ms_clean.csv", "target_valid",
           ["Ms_momentPerUnitCell_clean", "Ms_massMagnetization_clean", "Ms_volumeMagnetization_clean"]),
    "k1": ("k1/target_k1_clean.csv", "target_valid", ["K1_clean"]),
}


def is_chemical_formula(formula: str) -> bool:
    try:
        comp = Composition(formula)
    except (ValueError, KeyError, TypeError):
        return False
    return comp.num_atoms > 0 and all(
        el.symbol in REAL_ELEMENTS and el.Z < FIRST_SYNTHETIC_SUPERHEAVY_Z for el in comp.elements)


def d7_material_ids(repo: pd.DataFrame) -> set:
    labels = repo["reduced_formula"].dropna().unique()
    chemical = {f: is_chemical_formula(f) for f in labels}
    pseudo = set(repo.loc[~repo["reduced_formula"].map(chemical).fillna(False).astype(bool), "material_id"])
    d1_nan = set(repo.loc[repo[D1_COLS].isna().all(axis=1), "material_id"])
    if pseudo != d1_nan or len(pseudo) != EXPECTED_D7_N:
        raise AssertionError(f"D7 rule gives {len(pseudo)}, D1-NaN set {len(d1_nan)}; expected {EXPECTED_D7_N}")
    return pseudo


def clean_values(pseudo: set) -> pd.DataFrame:
    """Clean target values the excluded materials had in v1.1, kept for traceability / later recovery."""
    frames = []
    for path, valid_col, value_cols in TARGETS.values():
        t = pd.read_csv(V11 / "targets" / path, usecols=["material_id", valid_col] + value_cols, low_memory=False)
        t = t[t["material_id"].isin(pseudo) & t[valid_col].astype(bool)]
        frames.append(t.set_index("material_id")[value_cols])
    return pd.concat(frames, axis=1)


def write_quarantine(repo: pd.DataFrame, pseudo: set) -> dict:
    q_dir = OUT / "excluded"
    q_dir.mkdir(parents=True, exist_ok=True)
    values = clean_values(pseudo)
    quarantine = repo[repo["material_id"].isin(pseudo)].set_index("material_id")
    flags = pd.DataFrame(index=quarantine.index)
    flags["exclusion_decision"] = "D7"
    flags["exclusion_reason"] = REASON
    for col in values.columns:
        flags[f"clean_{col}"] = values[col].reindex(quarantine.index)
    out = flags.join(quarantine).reset_index()
    out.to_csv(q_dir / "D7_pseudo_formula_materials.csv", index=False, encoding="utf-8")
    labels = out.groupby("reduced_formula").size().rename("n_materials").sort_values(ascending=False).reset_index()
    labels.to_csv(q_dir / "D7_pseudo_formula_labels.csv", index=False, encoding="utf-8")
    affected = {col: int(values[col].notna().sum()) for col in values.columns}
    return {"n_materials": len(out), "n_labels": len(labels), "clean_target_rows_excluded": affected}


def build_repository_tiers_groups(repo: pd.DataFrame, pseudo: set) -> dict:
    v12 = repo[~repo["material_id"].isin(pseudo)].reset_index(drop=True)
    v12.to_parquet(OUT / "feature_repository_v1.2.parquet", index=False)
    (OUT / "tiers").mkdir(parents=True, exist_ok=True)
    stats = {"feature_repository": {"v1.1": len(repo), "v1.2": len(v12)}}
    for name in TIER_FILES:
        t = pd.read_parquet(V11 / "tiers" / f"{name}_v1.1.parquet")
        t12 = t[~t["material_id"].isin(pseudo)].reset_index(drop=True)
        t12.to_parquet(OUT / "tiers" / f"{name}_v1.2.parquet", index=False)
        stats[name] = {"v1.1": len(t), "v1.2": len(t12)}
    (OUT / "groups").mkdir(parents=True, exist_ok=True)
    g = pd.read_parquet(V11 / "groups/group_membership_v1.1.parquet")
    g12 = g[~g["material_id"].isin(pseudo)].reset_index(drop=True)
    g12.to_parquet(OUT / "groups/group_membership_v1.2.parquet", index=False)
    stats["groups"] = {c: {"v1.1": int(g[c].sum()), "v1.2": int(g12[c].sum())} for c in g.columns if c != "material_id"}
    dd = pd.read_csv(V11 / "data_dictionary_v1.1.csv")
    dd["pct_available"] = dd["column"].map((100 * v12.notna().mean()).round(2))
    dd.to_csv(OUT / "data_dictionary_v1.2.csv", index=False, encoding="utf-8")
    return stats


def build_targets(pseudo: set) -> dict:
    stats = {}
    for name, (path, valid_col, value_cols) in TARGETS.items():
        t = pd.read_csv(V11 / "targets" / path, low_memory=False)
        mask = t["material_id"].isin(pseudo)
        before = {c: int((t[c].notna() & t[valid_col].astype(bool)).sum()) for c in value_cols}
        t["v1_2_change"] = np.where(mask, TAG, "")
        t.loc[mask, valid_col] = False
        t.loc[mask, "exclusion_reason"] = REASON
        if name == "ms":  # Ms validity is defined per unit family by non-null clean values
            t.loc[mask, value_cols] = np.nan
        after = {c: int((t[c].notna() & t[valid_col].astype(bool)).sum()) for c in value_cols}
        (OUT / "targets" / path).parent.mkdir(parents=True, exist_ok=True)
        t.to_csv(OUT / "targets" / path, index=False, encoding="utf-8")
        stats.update({c: {"v1.1": before[c], "v1.2": after[c], "excluded": before[c] - after[c]} for c in value_cols})
    return stats


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    repo = pd.read_parquet(V11 / "feature_repository_v1.1.parquet")
    pseudo = d7_material_ids(repo)
    quarantine = write_quarantine(repo, pseudo)
    structure = build_repository_tiers_groups(repo, pseudo)
    targets = build_targets(pseudo)
    v11_manifest = json.loads((V11 / "MANIFEST_v1.1.json").read_text(encoding="utf-8"))
    files = sorted(p for p in OUT.rglob("*") if p.is_file() and p.suffix in {".parquet", ".csv"})
    manifest = {
        "analysis_dataset_version": "v1.2", "built_on": date.today().isoformat(), "derived_from": "v1.1",
        "builder": "EDA/src/build_analysis_dataset_v1_2.py",
        "decisions": {**v11_manifest["decisions"],
                      "D7": "exclude pseudo-formula materials from all analysis; quarantined in excluded/"},
        "D7_rule": "reduced_formula fails pymatgen Composition parsing, contains a non-element symbol, or contains a "
                   f"synthetic superheavy element (Z >= {FIRST_SYNTHETIC_SUPERHEAVY_Z}); identical to the set with "
                   "NaN D1 descriptors in v1.1",
        "D7_quarantine": quarantine, "structure": structure, "targets": targets,
        "inherited_from_v1.1": {k: v11_manifest[k] for k in ("build_history", "D1_convention")},
        "files": {str(p.relative_to(OUT)).replace("\\", "/"): sha256(p) for p in files},
    }
    (OUT / "MANIFEST_v1.2.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("D7_quarantine", "structure", "targets")}, indent=2))


if __name__ == "__main__":
    main()
