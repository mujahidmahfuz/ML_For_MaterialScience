"""Build Analysis Dataset v1.3 from the frozen v1.2 (Phase 7 review items R1 Curie target, R2 ordering provenance).

Rules: EDA/00_config/v1_3_curation_rules.yaml (written before any model was fit on the curated targets).
v1.2 inputs are read-only; every v1.3 file is new. Rules only REMOVE rows from a target population; removed rows are kept,
with all columns and reason codes, under EDA/datasets/v1.3/excluded/. Splits are derived from v1.2 by dropping removed rows.
Run from EDA/src:  python build_analysis_dataset_v1_3.py
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
V12, OUT = ROOT / "EDA/datasets/v1.2", ROOT / "EDA/datasets/v1.3"
S12, S13 = ROOT / "EDA/02_splits/v1.2", ROOT / "EDA/02_splits/v1.3"
RULES = ROOT / "EDA/00_config/v1_3_curation_rules.yaml"
CURIE_RULES = ["C1_no_magnetism_capable_element", "C2_elemental_non_magnet", "C3_below_1K", "C4_above_1400K", "C5_afm_only_formula"]
TARGET_SPLITS = {"curie": ["split_curie.csv", "matched_split_curie.csv"], "ordering": ["split_ordering.csv", "matched_split_ordering.csv"]}
UNCHANGED_SPLITS = ["split_ms.csv", "split_ms_mass.csv", "split_ms_volume.csv", "split_k1.csv", "matched_split_ms.csv"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def symbols(formula: str) -> set[str]:
    try:
        return {el.symbol for el in Composition(formula).elements}
    except (ValueError, KeyError, TypeError):
        return set()


def curie_flags(df: pd.DataFrame, ordering_labels: dict, rules: dict) -> pd.DataFrame:
    capable, ferro = set(rules["magnetism_capable_elements"]), set(rules["ferromagnetic_elements"])
    elems = df["reduced_formula"].map(symbols)
    flags = pd.DataFrame(index=df.index)
    flags["C1_no_magnetism_capable_element"] = elems.map(lambda s: not (s & capable))
    flags["C2_elemental_non_magnet"] = elems.map(lambda s: len(s) == 1) & ~elems.map(lambda s: bool(s & ferro))
    flags["C3_below_1K"] = df["TC_K_clean"] < rules["rules"]["C3_below_1K"]["threshold_k"]
    flags["C4_above_1400K"] = df["TC_K_clean"] > rules["rules"]["C4_above_1400K"]["threshold_k"]
    flags["C5_afm_only_formula"] = df["reduced_formula"].map(lambda f: ordering_labels.get(f) == {"AFM"})
    return flags


def reason_text(row: pd.Series) -> str:
    return "v1.3 R1: " + "+".join(c.split("_")[0] for c in CURIE_RULES if row[c])


def build_curie(rules: dict) -> dict:
    cur = pd.read_csv(V12 / "targets/curie/target_curie_clean.csv", low_memory=False)
    order = pd.read_csv(V12 / "targets/ordering/target_ordering_clean.csv", usecols=["reduced_formula", "magnetic_ordering_clean", "ordering_valid"], low_memory=False)
    labels = order[order["ordering_valid"].astype(bool)].groupby("reduced_formula")["magnetic_ordering_clean"].agg(set).to_dict()
    valid = cur["target_valid"].astype(bool)
    flags = pd.DataFrame(False, index=cur.index, columns=CURIE_RULES)
    flags.loc[valid] = curie_flags(cur[valid], labels, rules["curie"])
    primary_out = flags.any(axis=1) & valid
    sensitivity_out = flags[CURIE_RULES[:4]].any(axis=1) & valid
    new = cur.copy()
    new["v1_3_change"] = ""
    new.loc[primary_out, "target_valid"] = False
    new.loc[primary_out, "exclusion_reason"] = [reason_text(flags.loc[i]) for i in new.index[primary_out]]
    new.loc[primary_out, "v1_3_change"] = "R1_curie_curation_excluded"
    path = OUT / "targets/curie/target_curie_clean.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new.to_csv(path, index=False, encoding="utf-8")
    pd.concat([cur[primary_out], flags[primary_out].add_prefix("rule_")], axis=1).to_csv(
        OUT / "excluded/R1_curie_quarantine.csv", index=False, encoding="utf-8")
    sens = cur.copy()
    sens["v1_3_change"] = "sensitivity_C1_to_C4_only"
    sens["target_valid"] = valid & ~sensitivity_out
    sens.to_csv(OUT / "targets/curie/target_curie_sensitivity_without_C5.csv", index=False, encoding="utf-8")
    per_rule = {c: {"rows": int((flags[c] & valid).sum()), "only_this_rule": int((flags[c] & (flags.sum(axis=1) == 1)).sum())} for c in CURIE_RULES}
    return {"v1_2_n": int(valid.sum()), "v1_3_primary_n": int((valid & ~primary_out).sum()), "v1_3_sensitivity_n": int((valid & ~sensitivity_out).sum()),
            "removed_primary": int(primary_out.sum()), "per_rule": per_rule, "removed_ids": set(cur.loc[primary_out, "material_id"])}


def build_ordering() -> dict:
    o = pd.read_csv(V12 / "targets/ordering/target_ordering_clean.csv", low_memory=False)
    valid = o["ordering_valid"].astype(bool)
    jarvis = o["_source"].astype(str).str.startswith("jarvis_magnetic.csv") & valid
    new = o.copy()
    new["v1_3_change"] = ""
    new.loc[jarvis, "ordering_valid"] = False
    new.loc[jarvis, "exclusion_reason"] = "v1.3 R2: O1 JARVIS collector hard-codes 'Ferromagnetic' (not an ordering assignment)"
    new.loc[jarvis, "v1_3_change"] = "R2_ordering_default_fm_excluded"
    path = OUT / "targets/ordering/target_ordering_clean.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new.to_csv(path, index=False, encoding="utf-8")
    o[jarvis].to_csv(OUT / "excluded/R2_ordering_jarvis_default_fm_quarantine.csv", index=False, encoding="utf-8")
    classes = new[new["ordering_valid"].astype(bool)]["magnetic_ordering_clean"].value_counts().to_dict()
    return {"v1_2_n": int(valid.sum()), "v1_3_n": int((valid & ~jarvis).sum()), "removed": int(jarvis.sum()), "classes": classes,
            "removed_ids": set(o.loc[jarvis, "material_id"])}


def derive_splits(removed: dict[str, set]) -> list[dict]:
    S13.mkdir(parents=True, exist_ok=True)
    log = []
    for target, files in TARGET_SPLITS.items():
        for name in files:
            prev = pd.read_csv(S12 / name)
            kept = prev[~prev["material_id"].isin(removed[target])]
            kept.to_csv(S13 / name, index=False, encoding="utf-8")
            log.append({"file": name, "n_previous": len(prev), "n_dropped": len(prev) - len(kept), "n_kept": len(kept)})
    for name in UNCHANGED_SPLITS:
        shutil.copy2(S12 / name, S13 / name)
        n = len(pd.read_csv(S12 / name))
        log.append({"file": name, "n_previous": n, "n_dropped": 0, "n_kept": n})
    pd.DataFrame(log).to_csv(S13 / "split_derivation_log.csv", index=False, encoding="utf-8")
    return log


def main() -> None:
    rules = yaml.safe_load(RULES.read_text(encoding="utf-8"))
    (OUT / "excluded").mkdir(parents=True, exist_ok=True)
    curie, ordering = build_curie(rules), build_ordering()
    for sub in ("ms/target_ms_clean.csv", "k1/target_k1_clean.csv"):   # unchanged targets, copied so the v1.3 loader is self-contained
        (OUT / "targets" / sub).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(V12 / "targets" / sub, OUT / "targets" / sub)
    log = derive_splits({"curie": curie["removed_ids"], "ordering": ordering["removed_ids"]})
    files = sorted(OUT.rglob("*.csv"))
    manifest = {"version": "v1.3", "parent": "v1.2", "rules_file": "EDA/00_config/v1_3_curation_rules.yaml",
                "curie": {k: v for k, v in curie.items() if k != "removed_ids"},
                "ordering": {k: v for k, v in ordering.items() if k != "removed_ids"}, "split_derivation": log,
                "sha256": {str(p.relative_to(OUT)): sha256(p) for p in files},
                "unchanged": "feature repository, tiers, groups, data dictionary, ms/k1 targets (copied), D1-D7 decisions (see v1.2 manifest)"}
    (OUT / "MANIFEST_v1.3.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("curie", "ordering")}, indent=2))
    print(pd.DataFrame(log).to_string(index=False))


if __name__ == "__main__":
    main()
