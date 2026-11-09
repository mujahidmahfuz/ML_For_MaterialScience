"""Build Analysis Dataset v1.4 from the frozen v1.3 (roadmap item R10: secondary-target cleaning).

Rules: EDA/00_config/v1_4_curation_rules.yaml (written before any model was fit on the cleaned secondary targets).
v1.3 inputs are read-only; every v1.4 file is new. Rules only REMOVE rows from the Ms-mass, Ms-volume and K1 populations (target_valid -> False,
reason in exclusion_reason); removed rows are kept with all columns and reason codes under EDA/datasets/v1.4/excluded/. Curie, ordering and the
Ms-per-cell moment target are copied unchanged. Splits are derived from v1.3 by dropping removed rows.
Run from EDA/src:  python build_analysis_dataset_v1_4.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd
import yaml
from pymatgen.core import Composition

ROOT = Path(__file__).resolve().parents[2]
V13, OUT = ROOT / "EDA/datasets/v1.3", ROOT / "EDA/datasets/v1.4"
S13, S14 = ROOT / "EDA/02_splits/v1.3", ROOT / "EDA/02_splits/v1.4"
RULES = ROOT / "EDA/00_config/v1_4_curation_rules.yaml"
MASS_FAMILY, VOLUME_FAMILIES = "mass_magnetization", ("volume_Am", "volume_emu_cm3")
MASS_UNIT_PATTERN = r"m\^?2\s*/\s*kg|m\^?2\s*kg\^?-1"
SECONDARY_SPLITS = {"ms_mass": "split_ms_mass.csv", "ms_volume": "split_ms_volume.csv", "k1": "split_k1.csv"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def has_heavy_re(formula: str, heavy: set[str]) -> bool:
    try:
        return bool({el.symbol for el in Composition(formula).elements} & heavy)
    except (ValueError, KeyError, TypeError):
        return False


def ms_mass_flags(df: pd.DataFrame, rules: dict) -> pd.DataFrame:
    heavy = set(rules["heavy_rare_earths"])
    r, v = rules["ms_mass"]["rules"], df["Ms_massMagnetization_clean"]
    re_rich = df["reduced_formula"].map(lambda f: has_heavy_re(f, heavy))
    return pd.DataFrame({"M1_above_ceiling_no_heavy_RE": (v > r["M1_above_ceiling_no_heavy_RE"]["threshold_emu_g"]) & ~re_rich,
                         "M2_above_ceiling_heavy_RE": (v > r["M2_above_ceiling_heavy_RE"]["threshold_emu_g"]) & re_rich,
                         "M3_zero_value": v == 0}, index=df.index)


def ms_volume_flags(df: pd.DataFrame, rules: dict) -> pd.DataFrame:
    heavy = set(rules["heavy_rare_earths"])
    r, v = rules["ms_volume"]["rules"], df["Ms_volumeMagnetization_clean"]
    re_rich = df["reduced_formula"].map(lambda f: has_heavy_re(f, heavy))
    return pd.DataFrame({"V1_above_ceiling_no_heavy_RE": (v > r["V1_above_ceiling_no_heavy_RE"]["threshold_a_per_m"]) & ~re_rich,
                         "V2_above_ceiling_heavy_RE": (v > r["V2_above_ceiling_heavy_RE"]["threshold_a_per_m"]) & re_rich,
                         "V3_zero_value": v == 0,
                         "V4_mass_unit_misparsed": df["unit_raw"].astype(str).str.contains(MASS_UNIT_PATTERN, case=False, regex=True)}, index=df.index)


def k1_flags(df: pd.DataFrame, rules: dict) -> pd.DataFrame:
    return pd.DataFrame({"K1_above_ceiling": df["K1_clean"].abs() > rules["k1"]["rules"]["K1_above_ceiling"]["threshold_j_per_m3"]}, index=df.index)


def reason_text(row: pd.Series, rule_names: list[str]) -> str:
    return "v1.4 R10: " + "+".join(name.split("_")[0] for name in rule_names if row[name])


def mask_to_scope(flags: pd.DataFrame, in_scope: pd.Series) -> pd.DataFrame:
    return flags.mul(in_scope, axis=0).astype(bool)


def apply_flags(frame: pd.DataFrame, flags: pd.DataFrame, label: str) -> tuple[pd.DataFrame, pd.Series]:
    """Mark flagged rows invalid; returns the new frame and the removal mask (flags are already restricted to the in-scope rows)."""
    names = list(flags.columns)
    removed = flags.any(axis=1)
    new = frame.copy()
    new.loc[removed, "target_valid"] = False
    new.loc[removed, "exclusion_reason"] = [reason_text(flags.loc[i], names) for i in new.index[removed]]
    new.loc[removed, "v1_4_change"] = label
    return new, removed


def with_reason(original: pd.DataFrame, flagged: pd.DataFrame, removed: pd.Series) -> pd.DataFrame:
    """Removed rows with their ORIGINAL values plus the v1.4 reason columns."""
    return original[removed].assign(exclusion_reason=flagged.loc[removed, "exclusion_reason"], v1_4_change=flagged.loc[removed, "v1_4_change"])


def blank_clean_values(frame: pd.DataFrame, removed: pd.Series, column: str) -> pd.DataFrame:
    """Set the cleaned value of removed rows to missing (the raw value stays in value_raw and in the quarantine file)."""
    out = frame.copy()
    out.loc[removed, column] = float("nan")
    return out


def per_rule(flags: pd.DataFrame) -> dict:
    only = flags.sum(axis=1) == 1
    return {c: {"rows": int(flags[c].sum()), "only_this_rule": int((flags[c] & only).sum())} for c in flags.columns}


def build_ms(rules: dict) -> dict:
    ms = pd.read_csv(V13 / "targets/ms/target_ms_clean.csv", low_memory=False)
    ms["v1_4_change"] = ""
    valid = ms["target_valid"].astype(bool)
    mass_scope, vol_scope = valid & (ms["unit_family"] == MASS_FAMILY), valid & ms["unit_family"].isin(VOLUME_FAMILIES)
    mass_flags, vol_flags = mask_to_scope(ms_mass_flags(ms, rules), mass_scope), mask_to_scope(ms_volume_flags(ms, rules), vol_scope)
    new, mass_removed = apply_flags(ms, mass_flags, "R10_ms_mass_excluded")
    new, vol_removed = apply_flags(new, vol_flags, "R10_ms_volume_excluded")
    quarantine_mass = with_reason(ms, new, mass_removed)       # original values + reason, taken before the clean values are blanked
    quarantine_vol = with_reason(ms, new, vol_removed)
    new = blank_clean_values(new, mass_removed, "Ms_massMagnetization_clean")   # the Ms loaders select rows by non-missing value
    new = blank_clean_values(new, vol_removed, "Ms_volumeMagnetization_clean")
    path = OUT / "targets/ms/target_ms_clean.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new.to_csv(path, index=False, encoding="utf-8")
    pd.concat([quarantine_mass, mass_flags[mass_removed].add_prefix("rule_")], axis=1).to_csv(OUT / "excluded/R10_ms_mass_quarantine.csv", index=False, encoding="utf-8")
    pd.concat([quarantine_vol, vol_flags[vol_removed].add_prefix("rule_")], axis=1).to_csv(OUT / "excluded/R10_ms_volume_quarantine.csv", index=False, encoding="utf-8")
    return {"ms_mass": {"v1_3_n": int(mass_scope.sum()), "v1_4_n": int((mass_scope & ~mass_removed).sum()), "removed": int(mass_removed.sum()), "per_rule": per_rule(mass_flags)},
            "ms_volume": {"v1_3_n": int(vol_scope.sum()), "v1_4_n": int((vol_scope & ~vol_removed).sum()), "removed": int(vol_removed.sum()),
                          "per_rule": per_rule(vol_flags), "recoverable_ms_mass_candidates": int(vol_flags["V4_mass_unit_misparsed"].sum())},
            "removed_ids": {"ms_mass": set(ms.loc[mass_removed, "material_id"]), "ms_volume": set(ms.loc[vol_removed, "material_id"])},
            "ms_moment_unchanged_n": int((valid & (ms["unit_family"] == "moment_per_unit_cell")).sum())}


def build_k1(rules: dict) -> dict:
    k1 = pd.read_csv(V13 / "targets/k1/target_k1_clean.csv", low_memory=False)
    k1["v1_4_change"] = ""
    valid = k1["target_valid"].astype(bool)
    flags = mask_to_scope(k1_flags(k1, rules), valid)
    new, removed = apply_flags(k1, flags, "R10_k1_excluded")
    path = OUT / "targets/k1/target_k1_clean.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new.to_csv(path, index=False, encoding="utf-8")
    pd.concat([new[removed], flags[removed].add_prefix("rule_")], axis=1).to_csv(OUT / "excluded/R10_k1_quarantine.csv", index=False, encoding="utf-8")
    kept = new[new["target_valid"].astype(bool)]
    return {"v1_3_n": int(valid.sum()), "v1_4_n": int((valid & ~removed).sum()), "removed": int(removed.sum()), "per_rule": per_rule(flags),
            "kept_zero_k1_rows": int((kept["K1_clean"] == 0).sum()), "kept_between_2e7_and_5e7": int(((kept["K1_clean"].abs() > 2e7) & (kept["K1_clean"].abs() <= 5e7)).sum()),
            "removed_ids": set(k1.loc[removed, "material_id"])}


def derive_splits(removed: dict[str, set]) -> list[dict]:
    S14.mkdir(parents=True, exist_ok=True)
    log = []
    for path in sorted(S13.glob("*.csv")):
        if path.name == "split_derivation_log.csv":
            continue
        key = next((k for k, name in SECONDARY_SPLITS.items() if name == path.name), None)
        prev = pd.read_csv(path)
        kept = prev if key is None else prev[~prev["material_id"].isin(removed[key])]
        kept.to_csv(S14 / path.name, index=False, encoding="utf-8")
        log.append({"file": path.name, "n_previous": len(prev), "n_dropped": len(prev) - len(kept), "n_kept": len(kept)})
    pd.DataFrame(log).to_csv(S14 / "split_derivation_log.csv", index=False, encoding="utf-8")
    return log


def main() -> None:
    rules = yaml.safe_load(RULES.read_text(encoding="utf-8"))
    (OUT / "excluded").mkdir(parents=True, exist_ok=True)
    ms, k1 = build_ms(rules), build_k1(rules)
    for sub in ("curie/target_curie_clean.csv", "ordering/target_ordering_clean.csv"):    # unchanged targets, copied so the v1.4 loader is self-contained
        (OUT / "targets" / sub).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(V13 / "targets" / sub, OUT / "targets" / sub)
    log = derive_splits({"ms_mass": ms["removed_ids"]["ms_mass"], "ms_volume": ms["removed_ids"]["ms_volume"], "k1": k1["removed_ids"]})
    files = sorted(OUT.rglob("*.csv"))
    manifest = {"version": "v1.4", "parent": "v1.3", "rules_file": "EDA/00_config/v1_4_curation_rules.yaml",
                "ms": {k: v for k, v in ms.items() if k != "removed_ids"}, "k1": {k: v for k, v in k1.items() if k != "removed_ids"}, "split_derivation": log,
                "sha256": {str(p.relative_to(OUT)): sha256(p) for p in files},
                "ms_moment_official_name": "DFT total magnetic moment per unit cell (0 K)",
                "unchanged": "feature repository, tiers, groups (v1.2 files), Curie and ordering targets (copied from v1.3), Ms-per-cell moment target"}
    (OUT / "MANIFEST_v1.4.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("ms", "k1")}, indent=2))
    print(pd.DataFrame(log).to_string(index=False))


if __name__ == "__main__":
    main()
