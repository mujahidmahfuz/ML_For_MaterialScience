"""A20 step 1 (base python env): export the matched Curie rows with Tier 1 predictors, MP structure id and the 10 Phase 7 split labels.

Callers: a20_gnn_train.py and a20_gnn_analysis.py (both read the parquet). Reads existing project files only; writes
final/revision/outputs/a20_gnn/matched_curie_inputs.parquet.
Schema: material_id, reduced_formula, mp_id, y (Curie, K), split_0..split_9 (train | validation | test), then the raw (unimputed) Tier 1 predictors.
Run (repository root):  python final/revision/scripts/a20_gnn_prepare.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rev_common as rc  # noqa: E402

OUT = rc.REV / "a20_gnn"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg, cfg7 = rc.setup("curie")
    frame = rc.matched_frame("curie", cfg).reset_index(drop=True)
    tier1 = rc.pc.read_predictor_list(cfg, "tier1")
    missing = [c for c in tier1 if c not in frame.columns]
    if missing:
        raise KeyError(f"Tier 1 predictors absent from the matched frame: {missing[:5]}")
    ids = pd.read_csv(rc.REV / "a6/matched_mp_ids.csv")
    ids = ids[ids["target"] == "curie"].set_index("material_id")["p3_mp_material_id"]
    out = frame[["material_id", "reduced_formula"]].copy()
    out["mp_id"] = out["material_id"].map(ids)
    out["y"] = frame["value"].astype(float)
    for s in rc.SPLITS:
        out[f"split_{s}"] = rc.split_labels("curie", frame, cfg7, s)
    out = pd.concat([out, frame[tier1].astype(float)], axis=1)
    if out["mp_id"].isna().any():
        raise ValueError("matched rows without an MP structure id")
    out.to_parquet(OUT / "matched_curie_inputs.parquet", index=False)
    print(f"rows {len(out):,}; Tier 1 predictors {len(tier1)}; distinct structures {out.mp_id.nunique()}; mean target {out.y.mean():.1f} K")
    for s in rc.SPLITS[:2]:
        print(s, out[f"split_{s}"].value_counts().to_dict())


if __name__ == "__main__":
    main()
