"""Build Analysis Dataset v1.1 from frozen v1.0 (reviewer decisions D1, D2, D6 of 2026-09-26).

v1.0 inputs are read-only; every v1.1 file is new, under EDA/datasets/v1.1/.
  D1  Recompute the 4 Protocol II electronic descriptors that are 0.0 for every material in v1.0.
  D2  Exclude the non-zero github_datasets_magnetic.csv Curie values (encoded, non-physical field).
  D6  Exclude secondary-Ms values outside physical plausibility (mass > 300 emu/g; 0 < volume < 100 A/m).
D3/D4/D5 change no data; they are recorded in analysis_config.yaml.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from pymatgen.core import Composition, Element

ROOT = Path(__file__).resolve().parents[2]
V10_PARQUET = ROOT / "new_datasets/MMFD/phase4/data/phase4_ml_ready.parquet"
V10_DICT = ROOT / "new_datasets/MMFD/phase4/data/phase4_data_dictionary.csv"
V10_TARGETS = ROOT / "new_work(8-1-2026)/datasets/target_harmonization"
OUT = ROOT / "EDA/datasets/v1.1"
OUT_TARGETS = OUT / "targets"

ELECTRONIC_COLS = ["average_unpaired_electron_proxy", "average_d_electron_count",
                   "average_f_electron_count", "valence_electron_concentration"]
ENCODED_CURIE_SOURCE = "github_datasets_magnetic.csv"
MS_MASS_MAX_EMU_G = 300.0
MS_VOLUME_MIN_A_M = 100.0
SUBSHELL_CAPACITY = {"s": 2, "p": 6, "d": 10, "f": 14}
NOBLE_GAS_Z = [2, 10, 18, 36, 54, 86]
OXIDATION_COLS = ["avg_oxidation_state", "minimum_oxidation_state", "maximum_oxidation_state",
                  "oxidation_state_range", "oxidation_state_variance", "oxidation_state_std",
                  "number_of_possible_oxidation_states", "oxidation_solution_found"]
PHYSICS_BUNDLE = ["p3_formation_energy_per_atom", "p3_band_gap", "p3_volume_per_atom", "p3_crystal_system"]
V10_TIERS = ROOT / "new_work(8-1-2026)/datasets/tiers"
V10_GROUPS = ROOT / "new_work(8-1-2026)/datasets/groups"
TIER_FILES = {"tier1_core": "tier1_core.csv", "tier2_extended": "tier2_extended.csv", "tier3_physics": "tier3_physics.csv"}
GROUP_FILES = {"A_all": "groupA_all.csv", "B_experimental": "groupB_experimental.csv",
               "C_computational": "groupC_computational.csv", "D_transition_metals": "groupD_transition_metals.csv",
               "E_rare_earth": "groupE_rare_earth.csv", "F_actinides": "groupF_actinides.csv",
               "G_oxides": "groupG_oxides.csv", "H_intermetallics": "groupH_intermetallics.csv",
               "I_physics_complete": "groupI_physics_complete.csv",
               "J_descriptor_complete": "groupJ_descriptor_complete.csv"}
BUILD_HISTORY = [
    {"build": "2026-09-26", "note": "initial v1.1 build (D1, D2, D6)"},
    {"build": "2026-09-27", "note": "pre-freeze correction found by the required manual D1 check: d/f counts now use "
     "the noble-gas-core valence convention (the 2026-09-26 build counted the filled inner 4d10 shell as d "
     "electrons for lanthanides without 5d electrons, e.g. Nd/Sm/Dy d=10). D1 values propagated to v1.1 Tier "
     "files and group membership. Supersedes the 2026-09-26 build; nothing downstream used it except Stage 1 EDA, "
     "which was re-run."},
]


def valence_occupancy(el: Element, subshell: str) -> int:
    """Electrons of this subshell type outside the preceding noble-gas core (Magpie N*Valence convention).

    Nd [Xe]4f4 6s2 -> d 0, f 4; Ga [Ar]3d10 4s2 4p1 -> d 10; Hf [Xe]4f14 5d2 6s2 -> d 2, f 14.
    """
    cores = [z for z in NOBLE_GAS_Z if z < el.Z]
    core = {} if not cores else {(n, l): occ for n, l, occ in Element.from_Z(max(cores)).full_electronic_structure}
    return sum(occ - core.get((n, l), 0) for n, l, occ in el.full_electronic_structure if l == subshell)


def element_electronic_props(el: Element) -> dict[str, float]:
    """Free-atom ground-state descriptors for one element (pymatgen electronic configuration)."""
    config = el.full_electronic_structure
    d_count = valence_occupancy(el, "d")
    f_count = valence_occupancy(el, "f")
    # Hund's rule: a subshell with occ electrons out of capacity c has min(occ, c - occ) unpaired spins.
    unpaired = sum(min(occ, SUBSHELL_CAPACITY[l] - occ) for _, l, occ in config)
    group = el.group
    if el.symbol == "He":
        valence = 2
    elif el.is_lanthanoid or el.is_actinoid:
        valence = 3
    else:
        valence = group if group <= 12 else group - 10
    return {"d": d_count, "f": f_count, "unpaired": unpaired, "vec": valence}


def build_element_table() -> dict[str, dict[str, float]]:
    table = {}
    for el in Element:
        try:
            table[el.symbol] = element_electronic_props(el)
        except (ValueError, KeyError, AttributeError):
            continue
    return table


def formula_descriptors(formula: str, table: dict) -> tuple[float, float, float, float]:
    try:
        comp = Composition(formula)
    except (ValueError, KeyError):
        return (np.nan,) * 4
    total = comp.num_atoms
    if total == 0 or any(el.symbol not in table for el in comp.elements):
        return (np.nan,) * 4
    acc = {"unpaired": 0.0, "d": 0.0, "f": 0.0, "vec": 0.0}
    for el, amt in comp.items():
        frac = float(amt) / total
        for key in acc:
            acc[key] += table[el.symbol][key] * frac
    return tuple(round(acc[k], 6) for k in ("unpaired", "d", "f", "vec"))


def check_reference_elements(table: dict) -> None:
    expected = {"Fe": {"d": 6, "f": 0, "unpaired": 4, "vec": 8},
                "Gd": {"d": 1, "f": 7, "unpaired": 8, "vec": 3},
                "Cr": {"d": 5, "f": 0, "unpaired": 6, "vec": 6},
                "O": {"d": 0, "f": 0, "unpaired": 2, "vec": 6},
                "Al": {"d": 0, "f": 0, "unpaired": 1, "vec": 3},
                "Hf": {"d": 2, "f": 14, "unpaired": 2, "vec": 4},
                "Cu": {"d": 10, "f": 0, "unpaired": 1, "vec": 11},
                "Nd": {"d": 0, "f": 4, "unpaired": 4, "vec": 3},
                "Sm": {"d": 0, "f": 6, "unpaired": 6, "vec": 3},
                "Dy": {"d": 0, "f": 10, "unpaired": 4, "vec": 3},
                "Ga": {"d": 10, "f": 0, "unpaired": 1, "vec": 3},
                "Pb": {"d": 10, "f": 14, "unpaired": 2, "vec": 4},
                "U": {"d": 1, "f": 3, "unpaired": 4, "vec": 3},
                "Mn": {"d": 5, "f": 0, "unpaired": 5, "vec": 7}}
    for sym, props in expected.items():
        got = {k: table[sym][k] for k in props}
        if got != props:
            raise AssertionError(f"{sym}: expected {props}, got {got}")


def build_feature_repository() -> tuple[pd.DataFrame, dict]:
    v10 = pd.read_parquet(V10_PARQUET)
    table = build_element_table()
    check_reference_elements(table)
    formulas = v10["reduced_formula"].dropna().unique()
    lookup = {f: formula_descriptors(f, table) for f in formulas}
    values = np.array([lookup.get(f, (np.nan,) * 4) for f in v10["reduced_formula"]], dtype=float)

    v11 = v10.copy()
    for i, col in enumerate(ELECTRONIC_COLS):
        v11[col] = values[:, i]
    untouched = [c for c in v10.columns if c not in ELECTRONIC_COLS]
    assert v11[untouched].equals(v10[untouched]), "non-D1 columns changed"
    stats = {col: {"n_nonmissing": int(v11[col].notna().sum()), "n_unique": int(v11[col].nunique()),
                   "min": float(v11[col].min()), "median": float(v11[col].median()),
                   "max": float(v11[col].max())} for col in ELECTRONIC_COLS}
    stats["n_formulas_evaluated"] = int(len(formulas))
    return v11, stats


def exclude(df: pd.DataFrame, mask: pd.Series, reason: str, tag: str, null_cols: list[str] = ()) -> pd.DataFrame:
    out = df.copy()
    for col in null_cols:
        out.loc[mask, col] = np.nan
    out.loc[mask, "target_valid"] = False
    out.loc[mask, "exclusion_reason"] = reason
    out.loc[mask, "v1_1_change"] = tag
    return out


def build_targets() -> dict:
    OUT_TARGETS.mkdir(parents=True, exist_ok=True)
    for sub in ("ordering/target_ordering_clean.csv", "k1/target_k1_clean.csv"):
        (OUT_TARGETS / sub).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(V10_TARGETS / sub, OUT_TARGETS / sub)

    curie = pd.read_csv(V10_TARGETS / "curie/target_curie_clean.csv", low_memory=False)
    curie["v1_1_change"] = ""
    d2 = curie["target_valid"] & curie["_source"].eq(ENCODED_CURIE_SOURCE)
    curie = exclude(curie, d2, "v1.1 D2: encoded non-physical source value (github_datasets_magnetic.csv "
                    "Curie(TC) column confined to [0, 0.75]; see curie_zero_reconciliation_summary.txt)", "D2_excluded")
    (OUT_TARGETS / "curie").mkdir(exist_ok=True)
    curie.to_csv(OUT_TARGETS / "curie/target_curie_clean.csv", index=False, encoding="utf-8")

    ms = pd.read_csv(V10_TARGETS / "ms/target_ms_clean.csv", low_memory=False)
    ms["v1_1_change"] = ""
    mass_col, vol_col = "Ms_massMagnetization_clean", "Ms_volumeMagnetization_clean"
    d6_mass = ms[mass_col] > MS_MASS_MAX_EMU_G
    d6_vol = (ms[vol_col] > 0) & (ms[vol_col] < MS_VOLUME_MIN_A_M)
    ms = exclude(ms, d6_mass, f"v1.1 D6: mass magnetization > {MS_MASS_MAX_EMU_G:g} emu/g exceeds physical "
                 "ceiling (~245 emu/g, Fe65Co35)", "D6_excluded_mass", [mass_col])
    ms = exclude(ms, d6_vol, f"v1.1 D6: volume magnetization in (0, {MS_VOLUME_MIN_A_M:g}) A/m implausible; "
                 "consistent with MA/m labelled as A/m", "D6_excluded_volume", [vol_col])
    (OUT_TARGETS / "ms").mkdir(exist_ok=True)
    ms.to_csv(OUT_TARGETS / "ms/target_ms_clean.csv", index=False, encoding="utf-8")

    return {"D2_curie_excluded": int(d2.sum()), "D6_ms_mass_excluded": int(d6_mass.sum()),
            "D6_ms_volume_excluded": int(d6_vol.sum()),
            "clean_n": {"ordering": None, "curie": int(curie["target_valid"].sum()),
                        "ms_moment": int(ms["Ms_momentPerUnitCell_clean"].notna().sum()),
                        "ms_mass": int(ms[mass_col].notna().sum()), "ms_volume": int(ms[vol_col].notna().sum())}}


def v10_ids(path: Path) -> list:
    return pd.read_csv(path, usecols=["material_id"], engine="pyarrow")["material_id"].tolist()


def build_tiers(v11: pd.DataFrame, dd_group: pd.Series) -> dict:
    """Same column sets and row filter as build_datasets.py step_3_tiers, from the v1.1 repository."""
    tiers_dir = OUT / "tiers"
    tiers_dir.mkdir(parents=True, exist_ok=True)
    phase3 = set(dd_group[dd_group == "Phase 3 DFT-derived"].index)
    tier1_cols = [c for c in v11.columns if c not in phase3 and c not in OXIDATION_COLS]
    frames = {"tier1_core": v11[tier1_cols], "tier2_extended": v11[tier1_cols + OXIDATION_COLS],
              "tier3_physics": v11.loc[v11[PHYSICS_BUNDLE].notna().all(axis=1)]}
    stats = {}
    for name, frame in frames.items():
        v10_path = V10_TIERS / TIER_FILES[name]
        assert list(frame.columns) == list(pd.read_csv(v10_path, nrows=0).columns), f"{name}: columns differ from v1.0"
        assert frame["material_id"].tolist() == v10_ids(v10_path), f"{name}: rows differ from v1.0"
        frame.to_parquet(tiers_dir / f"{name}_v1.1.parquet", index=False)
        stats[name] = {"rows": int(len(frame)), "cols": int(frame.shape[1])}
    return stats


def build_group_membership(v11: pd.DataFrame, dd_group: pd.Series) -> dict:
    """build_datasets.py step_4_groups rules on v1.1 values; A-I must equal v1.0, J is re-derived."""
    groups_dir = OUT / "groups"
    groups_dir.mkdir(parents=True, exist_ok=True)
    phase3 = set(dd_group[dd_group == "Phase 3 DFT-derived"].index)
    descriptor_groups = {"Composition (Protocol I)", "Elemental/Electronic (Protocol II)"}
    tier1_descriptors = [c for c in v11.columns if c not in phase3 and c not in OXIDATION_COLS
                         and dd_group[c] in descriptor_groups]
    rules = {
        "A_all": pd.Series(True, index=v11.index),
        "B_experimental": v11["Experimental"] == True,  # noqa: E712
        "C_computational": v11["Experimental"] == False,  # noqa: E712
        "D_transition_metals": (v11["basic_comp__contains_transition_metal"] == 1)
        | (v11["basic_comp__transition_metal_fraction"] > 0),
        "E_rare_earth": (v11["basic_comp__contains_rare_earth"] == 1) | (v11["basic_comp__rare_earth_fraction"] > 0),
        "F_actinides": v11["basic_comp__contains_actinide"] == 1,
        "G_oxides": (v11["basic_comp__contains_O"] == 1) | (v11["basic_comp__fraction_O"] > 0),
        "H_intermetallics": (v11["basic_comp__contains_O"] == 0) & (v11["basic_comp__contains_C"] == 0)
        & (v11["basic_comp__contains_N"] == 0) & (v11["basic_comp__contains_B"] == 0)
        & (v11["basic_comp__n_elements"] >= 2),
        "I_physics_complete": v11[PHYSICS_BUNDLE].notna().all(axis=1),
        "J_descriptor_complete": v11[tier1_descriptors].notna().all(axis=1),
    }
    membership = pd.DataFrame({"material_id": v11["material_id"], **{k: m.to_numpy() for k, m in rules.items()}})
    stats = {}
    for name, fname in GROUP_FILES.items():
        old, new = set(v10_ids(V10_GROUPS / fname)), set(membership.loc[membership[name], "material_id"])
        stats[name] = {"v1.0": len(old), "v1.1": len(new), "removed": len(old - new), "added": len(new - old)}
        if name != "J_descriptor_complete":
            assert old == new, f"group {name} membership changed: {stats[name]}"
    membership.to_parquet(groups_dir / "group_membership_v1.1.parquet", index=False)
    return stats


def write_dictionary(v11: pd.DataFrame) -> None:
    dd = pd.read_csv(V10_DICT)
    avail = (100 * v11[ELECTRONIC_COLS].notna().mean()).round(2)
    dd.loc[dd["column"].isin(ELECTRONIC_COLS), "pct_available"] = dd["column"].map(avail)
    dd.to_csv(OUT / "data_dictionary_v1.1.csv", index=False, encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    v11, d1_stats = build_feature_repository()
    v11.to_parquet(OUT / "feature_repository_v1.1.parquet", index=False)
    write_dictionary(v11)
    dd_group = pd.read_csv(V10_DICT).set_index("column")["group"]
    tier_stats = build_tiers(v11, dd_group)
    group_stats = build_group_membership(v11, dd_group)
    target_stats = build_targets()
    ordering = pd.read_csv(OUT_TARGETS / "ordering/target_ordering_clean.csv", usecols=["ordering_valid"])
    target_stats["clean_n"]["ordering"] = int(ordering["ordering_valid"].sum())
    k1 = pd.read_csv(OUT_TARGETS / "k1/target_k1_clean.csv", usecols=["target_valid"])
    target_stats["clean_n"]["k1"] = int(k1["target_valid"].sum())

    files = sorted(p for p in OUT.rglob("*") if p.is_file() and p.suffix in {".parquet", ".csv"})
    manifest = {
        "analysis_dataset_version": "v1.1", "built_on": date.today().isoformat(), "derived_from": "v1.0",
        "builder": "EDA/src/build_analysis_dataset_v1_1.py",
        "decisions": {"D1": "recompute 4 electronic descriptors", "D2": "exclude encoded Curie values",
                      "D3": "keep 4 Tier 3 columns excluded from predictors (config only)",
                      "D4": "reduced_formula-grouped primary split (config only)",
                      "D5": "Experimental ordering = provenance slice only (config only)",
                      "D6": "exclude implausible secondary Ms values"},
        "build_history": BUILD_HISTORY,
        "D1_convention": "composition-weighted free-atom values from reduced_formula: d/f electrons outside the "
                         "preceding noble-gas core; Hund's-rule unpaired electrons min(occ, capacity-occ) summed "
                         "over subshells; VEC = group (1-12), group-10 (13-18), He 2, lanthanides/actinides 3",
        "D1_descriptor_stats": d1_stats, "targets": target_stats,
        "tiers": tier_stats, "groups": group_stats,
        "files": {str(p.relative_to(OUT)).replace("\\", "/"): sha256(p) for p in files},
    }
    (OUT / "MANIFEST_v1.1.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("D1_descriptor_stats", "targets", "tiers", "groups")}, indent=2))


if __name__ == "__main__":
    main()
