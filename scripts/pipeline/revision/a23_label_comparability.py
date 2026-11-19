"""A23 (revision guide 2026-11-20, item 5.1). Are the computed and experimental ordering labels about comparable phases?

Specification and claim rule: final/revision/PLAN.md, item A23 (written before this script was run). No model is fitted.

Subsets of the formulas labelled by both Materials Project (MP) and an experimental source (A2 definitions, v1.3 ordering target):
  all        : every shared formula (reproduces A2: modal label per provenance);
  bulk       : experimental records that are thin films or nanostructures removed before taking the modal label;
  phase      : an experimental record reports a space group (A19 parser, unchanged) equal to the space-group number of at least one MP entry of the
               same composition; MP label = that entry's ordering in the raw MP file used for training (lowest energy above hull among the
               matching entries); experimental label = modal label of the matching records;
  phase_stoich_bulk : phase, restricted to stoichiometric formulas (integer subscripts) and bulk records.
Each subset: agreement and Cohen's kappa with formula-bootstrap 95% intervals (1,000 resamples), confusion matrix and the share of experimental
AFM formulas that MP labels FM. A seeded random sample of 30 shared formulas with their source fields is written for the validation note.

Usage (repository root):  MP_API_KEY=<key> python final/revision/scripts/a23_label_comparability.py fetch   (once; caches MP fields)
                          python final/revision/scripts/a23_label_comparability.py run
Outputs: final/revision/outputs/a23_label_comparability/{mp_entries.csv, comparability_agreement.csv, confusion_<subset>.csv,
         phase_matched_pairs.csv, shared_formula_sample.csv, coverage_counts.csv}
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "new_materials_finding" / "external_audit"))

from a19_same_spacegroup import parse_sg  # noqa: E402
from audit_common import composition_key  # noqa: E402

OUT = ROOT / "final/revision/outputs/a23_label_comparability"
N_BOOT, SEED, SAMPLE_SEED, N_SAMPLE, CHUNK = 1000, 20261110, 20261120, 30, 500
CLASSES = ["FM", "AFM", "FiM", "NM"]
MP_MAP = {"FM": "FM", "AFM": "AFM", "FiM": "FiM", "NM": "NM"}          # 'Unknown' entries are not labels
NOT_BULK = re.compile(r"film|nano|thin|layer|wire|particle|dot|cluster|monolayer|multilayer|ribbon", re.I)


def kappa(a: np.ndarray, b: np.ndarray) -> float:
    labs = sorted(set(a) | set(b))
    cm = np.array([[np.sum((a == i) & (b == j)) for j in labs] for i in labs], dtype=float)
    n = cm.sum()
    po, pe = np.trace(cm) / n, (cm.sum(0) * cm.sum(1)).sum() / n ** 2
    return float((po - pe) / (1 - pe)) if pe < 1 else float("nan")


def load_target() -> pd.DataFrame:
    t = pd.read_csv(ROOT / "EDA/datasets/v1.3/targets/ordering/target_ordering_clean.csv", low_memory=False)
    t = t[t["ordering_valid"] == True].copy()  # noqa: E712 - column holds booleans
    meta = pd.read_csv(ROOT / "new_datasets/MMFD/data/metadata.csv",
                       usecols=["material_id", "space_group", "crystal_structure", "material_type"], low_memory=False)
    t = t.merge(meta.drop_duplicates("material_id"), on="material_id", how="left")
    t["prov"] = np.where(t["_source"].astype(str).str.startswith("mp_reformatted"), "MP", "experimental")
    t["value"] = t["magnetic_ordering_clean"]
    return t


def shared_formulas(t: pd.DataFrame) -> pd.Index:
    modal_label = t.groupby(["reduced_formula", "prov"])["value"].agg(lambda s: s.value_counts().index[0]).unstack()
    return modal_label.dropna().index


def mp_entries(formulas: pd.Index) -> pd.DataFrame:
    raw = pd.read_csv(ROOT / "raw_MP_magnetic_materials.csv")
    keys = {composition_key(f): f for f in formulas}
    raw["key"] = raw["formula"].map(composition_key)
    sub = raw[raw["key"].isin(keys)].copy()
    sub["reduced_formula"] = sub["key"].map(keys)
    return sub[["material_id", "formula", "reduced_formula", "ordering"]]


def fetch() -> None:
    from mp_api.client import MPRester
    OUT.mkdir(parents=True, exist_ok=True)
    t = load_target()
    entries = mp_entries(shared_formulas(t))
    ids = sorted(entries["material_id"].unique())
    rows = []
    with MPRester(os.environ["MP_API_KEY"]) as mpr:
        for i in range(0, len(ids), CHUNK):
            for d in mpr.materials.summary.search(material_ids=ids[i:i + CHUNK],
                                                  fields=["material_id", "symmetry", "energy_above_hull", "ordering"]):
                rows.append({"material_id": str(d.material_id), "sg_number": int(d.symmetry.number), "sg_symbol": str(d.symmetry.symbol),
                             "e_above_hull": d.energy_above_hull, "ordering_api_now": str(d.ordering)})
            print(f"fetched {min(i + CHUNK, len(ids))}/{len(ids)}", flush=True)
    api = pd.DataFrame(rows)
    entries.merge(api, on="material_id", how="left").to_csv(OUT / "mp_entries.csv", index=False)
    print(f"{len(entries):,} MP entries for {entries['reduced_formula'].nunique():,} formulas; {api['material_id'].nunique():,} returned by the API")


def score(name: str, frame: pd.DataFrame) -> dict:
    a, b = frame["experimental"].to_numpy(), frame["MP"].to_numpy()
    rng = np.random.default_rng(SEED)
    boots = np.array([(np.mean(a[ix] == b[ix]), kappa(a[ix], b[ix])) for ix in (rng.integers(0, len(a), len(a)) for _ in range(N_BOOT))])
    ct = pd.crosstab(pd.Categorical(a, CLASSES, ordered=True), pd.Categorical(b, CLASSES, ordered=True), dropna=False,
                     rownames=["experimental label"], colnames=["MP label"])
    ct.to_csv(OUT / f"confusion_{name}.csv")
    n_afm = int((a == "AFM").sum())
    return {"subset": name, "n_formulas": len(a), "agreement": float(np.mean(a == b)), "agreement_lo": np.nanquantile(boots[:, 0], .025),
            "agreement_hi": np.nanquantile(boots[:, 0], .975), "kappa": kappa(a, b), "kappa_lo": np.nanquantile(boots[:, 1], .025),
            "kappa_hi": np.nanquantile(boots[:, 1], .975), "n_exp_AFM": n_afm,
            "exp_AFM_called_FM_by_MP": float(np.mean(b[a == "AFM"] == "FM")) if n_afm else float("nan")}


def modal(s: pd.Series) -> str:
    return s.value_counts().index[0]


def stoichiometric(formula: str) -> bool:
    return not re.search(r"\d+\.\d+", str(formula))


def phase_matched(exp: pd.DataFrame, entries: pd.DataFrame) -> pd.DataFrame:
    lab = entries.dropna(subset=["label", "sg_number"])
    rows = []
    for f, g in exp.dropna(subset=["sg_number"]).groupby("reduced_formula"):
        cand = lab[lab["reduced_formula"] == f]
        for sg, gg in g.groupby("sg_number"):
            m = cand[cand["sg_number"] == sg].sort_values("e_above_hull")
            if len(m):
                rows.append({"reduced_formula": f, "sg_number": int(sg), "experimental": modal(gg["value"]), "MP": m.iloc[0]["label"],
                             "mp_id": m.iloc[0]["material_id"], "mp_e_above_hull": m.iloc[0]["e_above_hull"],
                             "n_exp_records": len(gg), "bulk": bool(gg["bulk"].all())})
    return pd.DataFrame(rows)


def sample(shared: pd.Index, exp: pd.DataFrame, entries: pd.DataFrame, mp_modal: pd.Series, matched: pd.Index) -> None:
    rng = np.random.default_rng(SAMPLE_SEED)
    pick = rng.choice(np.array(sorted(shared)), N_SAMPLE, replace=False)
    rows = []
    for f in pick:
        e = exp[exp["reduced_formula"] == f]
        en = entries[entries["reduced_formula"] == f].sort_values("e_above_hull")
        rows.append({"reduced_formula": f, "exp_label": modal(e["value"]), "exp_records": len(e),
                     "exp_material_type": "; ".join(sorted(set(e["material_type"].dropna().astype(str))))[:60],
                     "exp_space_group": "; ".join(sorted(set(e["space_group"].dropna().astype(str))))[:40],
                     "exp_crystal_structure": "; ".join(sorted(set(e["crystal_structure"].dropna().astype(str))))[:60],
                     "exp_doi": "; ".join(sorted(set(e["DOI"].dropna().astype(str))))[:80],
                     "mp_modal_label": mp_modal.get(f), "mp_entries": len(en),
                     "mp_lowest_energy_entries": "; ".join(f"{r.material_id}:{r.ordering}:{r.sg_symbol}:{r.e_above_hull:.3f}"
                                                           for r in en.head(4).itertuples()),
                     "phase_matched": f in matched})
    pd.DataFrame(rows).to_csv(OUT / "shared_formula_sample.csv", index=False)


def run() -> None:
    t = load_target()
    shared = shared_formulas(t)
    t = t[t["reduced_formula"].isin(shared)].copy()
    exp, mp = t[t["prov"] == "experimental"].copy(), t[t["prov"] == "MP"]
    exp["sg_number"] = [parse_sg(v)[0] for v in exp["space_group"]]
    exp["bulk"] = ~exp["material_type"].astype(str).str.contains(NOT_BULK) & ~exp["crystal_structure"].astype(str).str.contains(NOT_BULK)
    entries = pd.read_csv(OUT / "mp_entries.csv")
    entries["label"] = entries["ordering"].map(MP_MAP)

    mp_modal = mp.groupby("reduced_formula")["value"].agg(modal)
    sets = {"all": pd.DataFrame({"experimental": exp.groupby("reduced_formula")["value"].agg(modal), "MP": mp_modal}).dropna()}
    eb = exp[exp["bulk"]]
    sets["bulk"] = pd.DataFrame({"experimental": eb.groupby("reduced_formula")["value"].agg(modal), "MP": mp_modal}).dropna()

    ph = phase_matched(exp, entries)
    ph.to_csv(OUT / "phase_matched_pairs.csv", index=False)
    # one pair per formula: the space group with the most experimental records
    ph1 = ph.sort_values(["reduced_formula", "n_exp_records"], ascending=[True, False]).drop_duplicates("reduced_formula").set_index("reduced_formula")
    sets["phase"] = ph1[["experimental", "MP"]]
    keep = ph1["bulk"] & ph1.index.to_series().map(stoichiometric)
    sets["phase_stoich_bulk"] = ph1.loc[keep, ["experimental", "MP"]]

    res = pd.DataFrame([score(k, v) for k, v in sets.items()])
    res.to_csv(OUT / "comparability_agreement.csv", index=False)
    print(res.round(3).to_string())

    labelled = entries.dropna(subset=["label"])
    cov = {"shared_formulas": len(shared), "formulas_with_exp_space_group": exp.dropna(subset=["sg_number"])["reduced_formula"].nunique(),
           "formulas_with_mp_entries": entries["reduced_formula"].nunique(), "mp_entries": len(entries),
           "mp_entries_unknown_ordering": int(entries["label"].isna().sum()),
           "mp_formulas_with_multiple_polymorph_labels": int((labelled.groupby("reduced_formula")["label"].nunique() > 1).sum()),
           "mp_label_differs_from_api_now": int((entries["ordering"] != entries["ordering_api_now"]).sum()),
           "phase_matched_formulas": len(ph1), "phase_matched_stoich_bulk": int(keep.sum())}
    pd.Series(cov).to_csv(OUT / "coverage_counts.csv", header=["value"])
    print(pd.Series(cov).to_string())
    sample(shared, exp, entries, mp_modal, ph1.index)


if __name__ == "__main__":
    {"fetch": fetch, "run": run}[sys.argv[1]]()
