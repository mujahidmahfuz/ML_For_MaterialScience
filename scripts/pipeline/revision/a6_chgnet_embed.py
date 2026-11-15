"""A6(c): frozen CHGNet (pretrained universal potential, v0.3.0 weights shipped with chgnet 0.4.2) crystal embedding per MP structure.

The 64-d crystal feature vector is the pooled representation CHGNet uses before its energy head; it is used here unchanged (no training)
as a structure-aware 'physics-informed' representation. Run with the pimm-discovery conda env (chgnet is not in the base env):
    /c/Users/USER/anaconda3/envs/pimm-discovery/python.exe final/revision/scripts/a6_chgnet_embed.py
Output: final/revision/outputs/a6/chgnet_embedding.parquet  (mp_id, chg_00 ... chg_63)
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
from chgnet.model import CHGNet
from pymatgen.core import Structure

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "final/revision/outputs/a6"
BATCH = 32


def main() -> None:
    with gzip.open(OUT / "mp_structures.json.gz", "rt", encoding="utf-8") as f:
        structures = json.load(f)
    model = CHGNet.load()
    ids, feats = list(structures), []
    for i in range(0, len(ids), BATCH):
        batch = [Structure.from_dict(structures[m]) for m in ids[i:i + BATCH]]
        preds = model.predict_structure(batch, task="e", return_crystal_feas=True, batch_size=BATCH)
        feats.extend(np.asarray(p["crystal_fea"], dtype=float) for p in preds)
        if (i // BATCH) % 20 == 0:
            print(f"{min(i + BATCH, len(ids))}/{len(ids)}", flush=True)
    arr = np.vstack(feats)
    df = pd.DataFrame(arr, columns=[f"chg_{k:02d}" for k in range(arr.shape[1])]).assign(mp_id=ids)
    df.to_parquet(OUT / "chgnet_embedding.parquet", index=False)
    print(f"embedded {len(df):,} structures, dim {arr.shape[1]}")


if __name__ == "__main__":
    main()
