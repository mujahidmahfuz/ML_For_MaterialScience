"""Final check 4: rerun ONLY the per-atom Ms comparisons that the normalisation audit affects (Tier 1/2/3 and the add-one attribution).

Populations (all use the Phase 7 saved per-cell split labels for the same material_ids, the Phase 7 estimators/grids/selection rule and
XGBoost n_jobs=16, i.e. run_phase8_peratom_ms.run_split unchanged):
  A  corrected   rows whose numerator cell is resolved (10,821); target = moment / atoms of the NUMERATOR's own cell   (primary corrected result)
  B  atom_match  rows whose numerator and denominator cells have the same atom count (8,068); target = Phase 8 target (valid there)
  C  same_record rows where numerator and descriptors come from the same MP record and atom count (5,125); strictest subset
  orig_check     all 10,852 rows, original Phase 8 target, split 0 only: must reproduce the stored Phase 8 predictions exactly
Usage (from EDA/src, OMP_NUM_THREADS unset):
  python ../../final/scripts/check4_peratom_rerun.py --populations orig_check A B C --kinds main
  python ../../final/scripts/check4_peratom_rerun.py --populations A C --kinds addone
  python ../../final/scripts/check4_peratom_rerun.py --populations A B C --summarise
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parents[2] / "EDA" / "src"
sys.path.insert(0, str(SRC))

import phase6_common as pc  # noqa: E402
import phase7_validation as p7  # noqa: E402
import run_phase8_peratom_ms as rp  # noqa: E402

FINAL = Path(__file__).resolve().parents[1]
OUT = FINAL / "outputs" / "check4_peratom"
WORK = FINAL / "work"
RESOLVED = ["consistent_same_record", "consistent_atoms_different_record", "mismatch_atoms"]
POPULATIONS = {"A": ("corrected", RESOLVED), "B": ("atom_match", ["consistent_same_record", "consistent_atoms_different_record"]),
               "C": ("same_record", ["consistent_same_record"]), "orig_check": ("orig_check", None)}


def population_frame(code: str, base: pd.DataFrame, cell_map: pd.DataFrame) -> pd.DataFrame:
    """Per-atom frame of a population: n_sites = atoms of the cell the moment was computed in (A) or the Phase 8 denominator (B, C, orig_check)."""
    _, categories = POPULATIONS[code]
    if categories is None:
        return base
    cm = cell_map[cell_map["category"].isin(categories)].set_index("material_id")
    frame = base[base["material_id"].isin(cm.index)].copy()
    frame["n_sites"] = (cm.loc[frame["material_id"], "cell_atoms_numerator"].to_numpy(dtype=float) if code == "A"
                        else cm.loc[frame["material_id"], "n_used"].to_numpy(dtype=float))
    frame["value"] = frame["value_per_cell"] / frame["n_sites"]
    if not (np.isfinite(frame["value"]) & (frame["n_sites"] > 0)).all():
        raise ValueError(f"population {code}: invalid denominator")
    return frame.reset_index(drop=True)


def run(codes: list[str], kinds: list[str], splits: list[str]) -> None:
    cfg, cfg7 = p7.dataset_cfg("v1.2"), p7.load_phase7_config()
    p7.install_diagnostic_algorithm()
    base = rp.load_peratom_frame(cfg, cfg7)
    cell_map = pd.read_parquet(WORK / "peratom_cell_map.parquet")
    features = p7.variant_features(cfg, cfg7)
    for code in codes:
        name, _ = POPULATIONS[code]
        rp.OUT = WORK / f"peratom_{name}"
        rp.OUT.mkdir(parents=True, exist_ok=True)
        frame = population_frame(code, base, cell_map)
        print(f"population {code} ({name}): {len(frame):,} rows", flush=True)
        for kind in kinds:
            for sid in (["0"] if code == "orig_check" else splits):
                rp.run_split(sid, cfg, cfg7, frame, features, kind)


def per_cell_context(cfg7: dict, material_ids: set[str]) -> pd.DataFrame:
    """Per-cell MAE of the saved Phase 7 fits on the same rows (context; those models were trained on all 10,852 rows)."""
    work = p7.output_dir(cfg7, "v1.2") / "work" / "ms_moment"
    allp = pd.concat([pd.read_parquet(work / f"main__{s}.parquet") for s in rp.SPLITS], ignore_index=True)
    allp = allp[allp["material_id"].isin(material_ids)]
    allp["abs_err"] = (allp["y_true"] - allp["y_pred"]).abs()
    return allp.groupby(["split_id", "variant", "algorithm"]).agg(mae=("abs_err", "mean")).reset_index()


def summarise(codes: list[str]) -> None:
    cfg, cfg7 = p7.dataset_cfg("v1.2"), p7.load_phase7_config()
    base = rp.load_peratom_frame(cfg, cfg7)
    cell_map = pd.read_parquet(WORK / "peratom_cell_map.parquet")
    effects, addone = [], []
    for code in codes:
        name, _ = POPULATIONS[code]
        folder = WORK / f"peratom_{name}"
        frame = population_frame(code, base, cell_map)
        preds = pd.concat([pd.read_parquet(folder / f"peratom__{s}.parquet") for s in rp.SPLITS], ignore_index=True)
        metrics = rp.split_metrics(preds, frame)
        metrics.assign(population=name).to_csv(OUT / f"peratom_split_metrics_{name}.csv", index=False, encoding="utf-8")
        eff = rp.tier_effect(metrics, per_cell_context(cfg7, set(frame["material_id"])))
        effects.append(eff.assign(population=name, n_rows=len(frame)))
        add_files = [folder / f"peratom_addone__{s}.parquet" for s in rp.SPLITS]
        if all(p.exists() for p in add_files):
            added = pd.concat([pd.read_parquet(p) for p in add_files], ignore_index=True)
            addone.append(rp.addone_effect(added, metrics).assign(population=name, n_rows=len(frame)))
    pd.concat(effects).to_csv(OUT / "peratom_corrected_tier_effect.csv", index=False, encoding="utf-8")
    if addone:
        pd.concat(addone).to_csv(OUT / "peratom_corrected_addone_effect.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 220, "display.max_columns", 30)
    print(pd.concat(effects).round(4).to_string(index=False))
    if addone:
        print(pd.concat(addone).round(4).to_string(index=False))


def reproduction_check() -> None:
    new = pd.read_parquet(WORK / "peratom_orig_check" / "peratom__0.parquet")
    old = pd.read_parquet(pc.EDA_ROOT / "14_phase8_peratom" / "peratom__0.parquet")
    key = ["variant", "algorithm", "material_id"]
    m = new.merge(old, on=key, suffixes=("_new", "_old"), validate="one_to_one")
    diff = float((m["y_pred_new"] - m["y_pred_old"]).abs().max())
    pd.DataFrame([{"split_id": 0, "n_predictions": len(m), "max_abs_prediction_difference": diff}]).to_csv(
        OUT / "peratom_reproduction_check.csv", index=False, encoding="utf-8")
    print(f"orig_check vs stored Phase 8 split 0: {len(m)} predictions, max abs difference {diff}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--populations", nargs="+", choices=list(POPULATIONS), required=True)
    ap.add_argument("--kinds", nargs="+", choices=["main", "addone"], default=[])
    ap.add_argument("--splits", nargs="+", default=rp.SPLITS)
    ap.add_argument("--summarise", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.kinds:
        run(args.populations, args.kinds, args.splits)
    if "orig_check" in args.populations and (WORK / "peratom_orig_check" / "peratom__0.parquet").exists():
        reproduction_check()
    if args.summarise:
        summarise([c for c in args.populations if c != "orig_check"])


if __name__ == "__main__":
    main()
