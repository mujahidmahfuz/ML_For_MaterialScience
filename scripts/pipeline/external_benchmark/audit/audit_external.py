"""Audit of the external Curie benchmark (PLAN.md section 1 and Amendment 1). Loads NO prediction or error.

Each record of the external table gets audit flags A1-A8; the primary benchmark keeps records with no A1, A2 (a/b/d/e/f), A4 or A5 flag.
Hand adjudications are read from adjudication_papers.csv and adjudication_records.csv; Crossref titles from crossref_metadata.csv.
Usage (from this folder): python audit_external.py
Output: audit_flags.csv (one row per external record), audit_counts.csv
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import yaml
from pymatgen.core import Composition, Element

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from audit_common import EXTERNAL_CSV, ROOT, composition_key, doi_set, paper_clusters  # noqa: E402

REPO_KEY_CACHE = HERE / "repository_composition_keys.parquet"

GLASS_FORMERS = {"B", "C", "Si", "P", "Zr", "Nb"}
MIXED_SCALE_MAX_COEF, MIXED_SCALE_MIN_FRACTION = 1000, 0.005
IONIC_ANIONS = {"O": 2, "F": 1}
OTHER_ANION_FORMERS = {"N", "S", "Se", "Te", "Cl", "Br", "I", "H", "C", "As", "Sb", "P"}
VALUE_COPY_TOLERANCE_K = 0.5
A6_PATTERNS = {
    "film": r"thin film|\bfilms?\b|epitax|heterostruct|multilayer",
    "nano": r"nanopart|nanocryst|nanopowder|nanostruct|nanowire|nanorod|nanocluster|nano-sized|nanograin|nanophase|nanoscale|quantum dot",
    "pressure": r"pressure",
    "low_dimensional": r"monolayer|two-dimensional|\b2d\b|few-layer",
    "irradiation": r"irradiat",
    "spin_glass": r"spin[- ]glass",
    "composite": r"composite",
}
PRESSURE_MEASURED = r"under (high )?pressure|pressure dependence|effect of (high )?pressure|pressure[- ]induced|pressure effects?|at high pressure|high[- ]pressure (magnet|x-ray|xmcd)|high pressures"
PRESSURE_SYNTHESIS = r"synthesi[sz]ed under high pressure|high[- ]pressure synthesis|prepared at high pressure|high[- ]pressure nitrogenation|weight pressure"
A2_FLAGS = ["a2a_unparseable", "a2b_bad_symbol", "a2d_mixed_scale", "a2e_impossible_ionic", "a2f_family_shorthand"]
PRIMARY_EXCLUSIONS = {"A1": "a1_computational_label", "A2": "a2_malformed", "A4": "a4_training_rule", "A5": "a5_not_magnetic_tc"}


def is_mixed_scale(formula: str) -> bool:
    """A2d: max coefficient >= 1000 and a glass-former/metalloid below 0.5 at.% (part of a nominal formula scaled by 100, part not)."""
    comp = Composition(formula)
    if max(comp.get_el_amt_dict().values()) < MIXED_SCALE_MAX_COEF:
        return False
    return any(e in GLASS_FORMERS and f < MIXED_SCALE_MIN_FRACTION for e, f in comp.fractional_composition.get_el_amt_dict().items())


def is_impossible_ionic(formula: str) -> bool:
    """A2e: O/F compound (no other anion former) whose anion charge lies outside the range the cations' positive oxidation states can supply."""
    amts = Composition(formula).get_el_amt_dict()
    if not set(amts) & set(IONIC_ANIONS) or set(amts) & OTHER_ANION_FORMERS:
        return False
    anion_charge = sum(IONIC_ANIONS[e] * n for e, n in amts.items() if e in IONIC_ANIONS)
    lo = hi = 0.0
    for e, n in amts.items():
        if e in IONIC_ANIONS:
            continue
        states = [s for s in Element(e).oxidation_states if s > 0] or [0]
        lo, hi = lo + n * min(states), hi + n * max(states)
    return not (lo - 1e-9 <= anion_charge <= hi + 1e-9)


def a6_categories(text: str) -> list[str]:
    """A6 (flag only): form/condition categories named in a source title or abstract. Synthesis under pressure alone is not flagged."""
    text = text.lower()
    cats = [k for k, pat in A6_PATTERNS.items() if re.search(pat, text)]
    if "pressure" in cats:
        measured = re.search(PRESSURE_MEASURED, re.sub(PRESSURE_SYNTHESIS, "", text))
        if not measured:
            cats.remove("pressure")
    return cats


def load_external() -> pd.DataFrame:
    ext = pd.read_csv(EXTERNAL_CSV, keep_default_na=False, na_values=[""]).rename(columns={"Names": "name", "Normalised Value": "tc_exp_k", "DOI": "doi_raw"})
    ext["dois"] = ext["doi_raw"].map(doi_set)
    parsed, reduced, chemsys, bad_symbol = [], [], [], []
    for name in ext["name"]:
        try:
            comp = Composition(name)
        except (ValueError, KeyError, TypeError):
            parsed.append(False), reduced.append(None), chemsys.append(None), bad_symbol.append(True)
            continue
        parsed.append(True)
        reduced.append(comp.reduced_formula)
        chemsys.append(comp.chemical_system)
        bad_symbol.append(any(el.symbol in {"D", "T"} for el in comp.elements))
    return ext.assign(parsed=parsed, reduced_formula=reduced, chemical_system=chemsys, a2b_bad_symbol=bad_symbol)


def adjudications(ext: pd.DataFrame) -> pd.DataFrame:
    """A1 / A2f / A2s / A5 from the hand adjudication tables; A1 is checked against the 'all DOIs computational' rule."""
    papers = pd.read_csv(HERE / "adjudication_papers.csv")
    records = pd.read_csv(HERE / "adjudication_records.csv")
    missing = set(records["name"]) - set(ext["name"])
    if missing:
        raise ValueError(f"adjudicated names not in the table: {sorted(missing)}")
    comp_dois = set(papers.loc[papers["class"] == "computational", "doi"])
    by_name = records.set_index("name")
    code = ext["name"].map(by_name["code"]).fillna("")
    out = ext.assign(adjudication_reason=ext["name"].map(by_name["reason"]).fillna(""), a1_computational_label=code.eq("A1"))
    bad = out.loc[out["a1_computational_label"] & ~out["dois"].map(lambda s: bool(s) and s <= comp_dois), "name"]
    if len(bad):
        raise ValueError(f"A1 records with a non-computational DOI (rule: all DOIs must be computational): {bad.tolist()}")
    out["a1c_cited_in_computational_paper"] = out["dois"].map(lambda s: bool(s & comp_dois)) & ~out["a1_computational_label"]
    out["a1c_only_computational_dois"] = out["dois"].map(lambda s: bool(s) and s <= comp_dois) & ~out["a1_computational_label"]
    out["a2f_family_shorthand"] = code.eq("A2f")
    out["a2s_suspect_extraction"] = code.eq("A2s")
    out["a5_not_magnetic_tc"] = code.eq("A5")
    return out


def curation_rules(ext: pd.DataFrame) -> pd.DataFrame:
    """A4: the v1.3 training-label rules C1-C5, applied unchanged."""
    rules = yaml.safe_load((ROOT / "EDA/00_config/v1_3_curation_rules.yaml").read_text(encoding="utf-8"))["curie"]
    capable, ferro = set(rules["magnetism_capable_elements"]), set(rules["ferromagnetic_elements"])
    order = pd.read_csv(ROOT / "EDA/datasets/v1.2/targets/ordering/target_ordering_clean.csv",
                        usecols=["reduced_formula", "magnetic_ordering_clean", "ordering_valid"], low_memory=False)
    labels = order[order["ordering_valid"].astype(bool)].groupby("reduced_formula")["magnetic_ordering_clean"].agg(set).to_dict()
    elems = ext["reduced_formula"].map(lambda f: {e.symbol for e in Composition(f).elements} if f else set())
    out = ext.copy()
    out["a4_C1_no_magnetism_capable_element"] = elems.map(lambda s: not (s & capable))
    out["a4_C2_elemental_non_magnet"] = elems.map(lambda s: len(s) == 1 and not (s & ferro))
    out["a4_C3_below_1K"] = out["tc_exp_k"] < rules["rules"]["C3_below_1K"]["threshold_k"]
    out["a4_C4_above_1400K"] = out["tc_exp_k"] > rules["rules"]["C4_above_1400K"]["threshold_k"]
    out["a4_C5_afm_only_formula"] = out["reduced_formula"].map(lambda f: labels.get(f) == {"AFM"})
    out["a4_training_rule"] = out[[c for c in out.columns if c.startswith("a4_C")]].any(axis=1)
    return out


def comparability(ext: pd.DataFrame) -> pd.DataFrame:
    """A6 (flag only): categories from the source titles/abstracts."""
    meta = pd.read_csv(HERE / "crossref_metadata.csv", keep_default_na=False).set_index("doi")
    text = (meta["title"].str.replace(r"<[^>]+>", "", regex=True) + " || " + meta["abstract"]).to_dict()
    cats_by_doi = {d: a6_categories(t) for d, t in text.items()}
    out = ext.copy()
    out["a6_categories"] = out["dois"].map(lambda s: ";".join(sorted({c for d in s for c in cats_by_doi.get(d, [])})))
    out["a6_any_source"] = out["a6_categories"].ne("")
    out["a6_all_sources"] = out["dois"].map(lambda s: bool(s) and all(cats_by_doi.get(d) for d in s))
    return out


def _copied(formula: str, value: float, table: dict) -> bool:
    return any(abs(t - value) <= VALUE_COPY_TOLERANCE_K for t in table.get(formula, []))


def repository_keys(repo: set[str]) -> dict[str, str]:
    """reduced_formula string -> composition key for every repository formula (cached; ~350k pymatgen parses)."""
    if REPO_KEY_CACHE.exists():
        cached = pd.read_parquet(REPO_KEY_CACHE)
        if set(cached["reduced_formula"]) == repo:
            return dict(zip(cached["reduced_formula"], cached["key"]))
    table = pd.DataFrame({"reduced_formula": sorted(repo)})
    table["key"] = table["reduced_formula"].map(composition_key)
    table.to_parquet(REPO_KEY_CACHE, index=False)
    return dict(zip(table["reduced_formula"], table["key"]))


def training_overlap(ext: pd.DataFrame) -> pd.DataFrame:
    """A7 (subset definitions): repository composition (Amendment 3), seen chemical system, DOI in our Curie data, copied value."""
    repo = set(pd.read_parquet(ROOT / "EDA/datasets/v1.2/feature_repository_v1.2.parquet", columns=["reduced_formula"])["reduced_formula"].dropna())
    repo_keys = set(k for k in repository_keys(repo).values() if k)
    systems = set()
    for f in repo:
        try:
            systems.add(Composition(f).chemical_system)
        except (ValueError, KeyError, TypeError):      # quarantined pseudo-formula leftovers contribute no system
            continue
    cur = pd.read_csv(ROOT / "EDA/datasets/v1.3/targets/curie/target_curie_clean.csv",
                      usecols=["reduced_formula", "DOI", "TC_K_clean", "target_valid"], low_memory=False)
    cur["dois"] = cur["DOI"].map(doi_set)
    cur_keys = {f: composition_key(f) for f in cur["reduced_formula"].dropna().unique()}
    cur["key"] = cur["reduced_formula"].map(cur_keys)
    valid = cur["target_valid"].astype(bool)
    dois_any, dois_valid = set().union(*cur["dois"]), set().union(*cur.loc[valid, "dois"])
    tc_valid = cur[valid].groupby("key")["TC_K_clean"].agg(list).to_dict()
    tc_any = cur.dropna(subset=["TC_K_clean"]).groupby("key")["TC_K_clean"].agg(list).to_dict()
    old = pd.read_csv(HERE.parent / "external_predictions.csv", usecols=["name", "doi_in_curie_training"], keep_default_na=False, na_values=[""])
    out = ext.merge(old.rename(columns={"doi_in_curie_training": "a7_old_doi_flag_buggy_normaliser"}), on="name", how="left", validate="one_to_one")
    out["composition_key"] = out["reduced_formula"].map(lambda f: composition_key(f) if f else None)
    out["a7a_string_match_october"] = out["reduced_formula"].isin(repo)
    out["a7a_formula_in_repository"] = out["composition_key"].isin(repo_keys)
    out["a7_system_seen"] = out["chemical_system"].isin(systems)
    out["a7b_doi_in_curie_any_row"] = out["dois"].map(lambda s: bool(s & dois_any))
    out["a7b_doi_in_curie_valid_row"] = out["dois"].map(lambda s: bool(s & dois_valid))
    out["a7c_value_copied_valid_row"] = [_copied(k, v, tc_valid) for k, v in zip(out["composition_key"], out["tc_exp_k"])]
    out["a7c_value_copied_any_row"] = [_copied(k, v, tc_any) for k, v in zip(out["composition_key"], out["tc_exp_k"])]
    return out


def merge_duplicates(ext: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """A3b: one record per reduced formula (mean Tc, pooled DOIs). Returns the frame and the number of records merged away."""
    dup = ext.duplicated("reduced_formula", keep=False) & ext["reduced_formula"].notna()
    if not dup.any():
        return ext.assign(a3_merged_from=1), 0
    merged = []
    for _, g in ext[dup].groupby("reduced_formula"):
        row = g.iloc[0].copy()
        row["tc_exp_k"], row["dois"], row["a3_merged_from"] = g["tc_exp_k"].mean(), frozenset().union(*g["dois"]), len(g)
        row["name"] = " | ".join(g["name"])
        merged.append(row)
    return pd.concat([ext[~dup].assign(a3_merged_from=1), pd.DataFrame(merged)], ignore_index=True), int(dup.sum() - len(merged))


def build_flags() -> tuple[pd.DataFrame, dict[str, int]]:
    ext = load_external()
    n_table = len(ext)
    exact_dups = int(ext.duplicated(["name", "tc_exp_k", "doi_raw"]).sum())
    ext = ext.drop_duplicates(["name", "tc_exp_k", "doi_raw"]).reset_index(drop=True)
    ext["a2a_unparseable"] = ~ext["parsed"]
    ok = ext["parsed"]
    ext["a2d_mixed_scale"] = ext["reduced_formula"].where(ok).map(lambda f: bool(f) and is_mixed_scale(f))
    ext["a2e_impossible_ionic"] = ext["name"].where(ok).map(lambda f: isinstance(f, str) and is_impossible_ionic(f))
    ext = adjudications(ext)
    ext["a2_malformed"] = ext[A2_FLAGS].any(axis=1)
    ext, n_merged = merge_duplicates(ext)
    ext = training_overlap(comparability(curation_rules(ext)))
    ext["a8_no_doi"] = ext["dois"].map(len).eq(0)
    ext["paper_cluster"] = paper_clusters(list(ext["dois"]), list(ext["doi_raw"]))
    ext["excluded_primary"] = ext[list(PRIMARY_EXCLUSIONS.values())].any(axis=1)
    ext["exclusion_reasons"] = ext[list(PRIMARY_EXCLUSIONS.values())].apply(
        lambda r: ";".join(k for k, c in PRIMARY_EXCLUSIONS.items() if r[c]), axis=1)
    counts = {"records_in_table": n_table, "a3a_exact_duplicate_rows": exact_dups, "a3b_same_formula_merged": n_merged}
    counts.update({c: int(ext[c].sum()) for c in ext.columns if re.match(r"a\d", c) and ext[c].dtype == bool})
    counts.update({"excluded_primary": int(ext["excluded_primary"].sum()), "primary_benchmark_records": int((~ext["excluded_primary"]).sum()),
                   "paper_clusters_all": int(ext["paper_cluster"].nunique())})
    counts.update({f"excluded_only_by_{k}": int((ext["exclusion_reasons"] == k).sum()) for k in PRIMARY_EXCLUSIONS})
    return ext, counts


def main() -> None:
    ext, counts = build_flags()
    ext.assign(dois=ext["dois"].map(lambda s: ";".join(sorted(s)))).drop(columns=["parsed"]).to_csv(HERE / "audit_flags.csv", index=False, encoding="utf-8")
    pd.Series(counts, name="count").rename_axis("item").to_csv(HERE / "audit_counts.csv", encoding="utf-8")
    print(pd.Series(counts).to_string())


if __name__ == "__main__":
    main()
