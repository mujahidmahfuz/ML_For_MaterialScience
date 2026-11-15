"""A6(a)/A5: fetch the Materials Project structures (and thermo run types) of every matched-population material.

Matched populations: Curie and ordering (v1.3 matched splits), DFT moment (v1.2 matched split). Each material's Tier 3 values were joined
from the MP entry recorded in phase3_master_dataset.csv (p3_mp_material_id); that same entry's structure is fetched, so the new
structure descriptors describe exactly the polymorph the Tier 3 scalars describe.

Usage (from the project root): MP_API_KEY=<key> python final/revision/scripts/a6_fetch_structures.py
Outputs: final/revision/outputs/a6/mp_structures.json.gz  {mp_id: structure dict}
         final/revision/outputs/a6/mp_entry_meta.csv        mp_id, run types, ordering, total magnetization, nsites
         final/revision/outputs/a6/matched_mp_ids.csv       material_id, target, p3_mp_material_id
"""
from __future__ import annotations

import gzip
import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "final/revision/outputs/a6"
SPLITS = {"curie": ROOT / "EDA/02_splits/v1.3/matched_split_curie.csv",
          "ordering": ROOT / "EDA/02_splits/v1.3/matched_split_ordering.csv",
          "ms_moment": ROOT / "EDA/02_splits/v1.2/matched_split_ms.csv"}
CHUNK = 500


def matched_ids() -> pd.DataFrame:
    p3 = pd.read_csv(ROOT / "new_datasets/MMFD/phase3/data/phase3_master_dataset.csv", usecols=["material_id", "p3_mp_material_id"])
    rows = [pd.read_csv(path, usecols=["material_id"]).assign(target=t) for t, path in SPLITS.items()]
    out = pd.concat(rows, ignore_index=True).merge(p3, on="material_id", how="left", validate="many_to_one")
    return out


def fetch(ids: list[str], key: str) -> tuple[dict, pd.DataFrame]:
    from mp_api.client import MPRester
    structures, meta = {}, []
    with MPRester(key) as mpr:
        for i in range(0, len(ids), CHUNK):
            chunk = ids[i:i + CHUNK]
            for d in mpr.materials.summary.search(material_ids=chunk, fields=["material_id", "structure", "ordering", "total_magnetization",
                                                                                 "nsites", "is_magnetic", "num_magnetic_sites"]):
                mid = str(d.material_id)
                structures[mid] = d.structure.as_dict()
                meta.append({"mp_id": mid, "ordering": str(d.ordering), "total_magnetization": d.total_magnetization, "nsites": d.nsites,
                             "is_magnetic": d.is_magnetic, "num_magnetic_sites": d.num_magnetic_sites})
            print(f"summary {min(i + CHUNK, len(ids))}/{len(ids)}", flush=True)
        runtypes = {}
        for i in range(0, len(ids), CHUNK):
            chunk = ids[i:i + CHUNK]
            for d in mpr.materials.thermo.search(material_ids=chunk, fields=["material_id", "thermo_type", "energy_type"]):
                runtypes.setdefault(str(d.material_id), set()).add(str(d.thermo_type))
            print(f"thermo {min(i + CHUNK, len(ids))}/{len(ids)}", flush=True)
    meta = pd.DataFrame(meta)
    meta["thermo_types"] = meta["mp_id"].map(lambda m: ";".join(sorted(runtypes.get(m, []))))
    return structures, meta


def main() -> None:
    key = os.environ["MP_API_KEY"]
    OUT.mkdir(parents=True, exist_ok=True)
    ids = matched_ids()
    ids.to_csv(OUT / "matched_mp_ids.csv", index=False)
    print(ids.groupby("target")["p3_mp_material_id"].agg(n="size", with_mp_id="count").to_string(), flush=True)
    unique = sorted(ids["p3_mp_material_id"].dropna().astype(str).unique())
    print(f"unique MP entries to fetch: {len(unique):,}", flush=True)
    structures, meta = fetch(unique, key)
    with gzip.open(OUT / "mp_structures.json.gz", "wt", encoding="utf-8") as f:
        json.dump(structures, f)
    meta.to_csv(OUT / "mp_entry_meta.csv", index=False)
    print(f"fetched {len(structures):,} structures; missing {len(set(unique) - set(structures)):,}", flush=True)


if __name__ == "__main__":
    main()
