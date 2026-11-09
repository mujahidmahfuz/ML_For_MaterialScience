"""Per-atom Ms target (roadmap R: remove the unit-cell-size confound from the Ms-per-cell Tier 3 finding).

Phase 7 found that the Tier 3 gain for the Ms-per-cell target is recovered by a site-count scalar (cell size). If that is the whole story, a
target that does not scale with cell size -- moment per atom = Ms_per_cell / n_sites, n_sites = p3_volume / p3_volume_per_atom -- should show NO stable
Tier 1 -> Tier 3 gain. Same matched population (10,852 rows), same splits (the 10 Phase 7 seeds), grids and algorithms as Phase 7.
Usage (from EDA/src, OMP_NUM_THREADS unset):  python run_phase8_peratom_ms.py [addone]
  default  : Tier 1/2/3 on the per-atom target
  addone   : Tier 2 + ONE physics-column group (Phase 7 A_* variants) on the per-atom target -- attribution of the Tier 3 gain
Outputs: EDA/14_phase8_peratom/peratom__<split>.parquet, peratom_split_metrics.csv, peratom_tier_effect.csv (per-atom and per-cell side by side)
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import phase6_common as pc
import phase6_models as pm
import phase7_validation as p7

OUT = pc.EDA_ROOT / "14_phase8_peratom"
SPLITS = [str(i) for i in range(10)]
MIN_FRACTION_POSITIVE = 0.70


def load_peratom_frame(cfg: dict, cfg7: dict) -> pd.DataFrame:
    spec = cfg7["multisplit"]["targets"]["ms_moment"]
    cat = cfg["predictor_rules"]["categorical_predictors"]
    frame, _, _ = pm.load_matched_frame(cfg, "ms_moment", "tier3", p7.split_dir("v1.2") / spec["frozen_split"], cat)
    sites = frame["p3_volume"] / frame["p3_volume_per_atom"]
    if not (np.isfinite(sites) & (sites > 0)).all():
        raise ValueError("matched Ms rows without a usable site count; the per-atom target would be defined on a different population")
    print(f"matched Ms rows {len(frame):,}; sites median {sites.median():.0f} (range {sites.min():.0f}-{sites.max():.0f})", flush=True)
    frame = frame.assign(value_per_cell=frame["value"], n_sites=sites)
    return frame.assign(value=frame["value_per_cell"] / frame["n_sites"])


def run_split(split_id: str, cfg, cfg7, frame, features, kind: str = "main") -> None:
    path = OUT / (f"peratom__{split_id}.parquet" if kind == "main" else f"peratom_{kind}__{split_id}.parquet")
    if path.exists():
        return
    saved = pd.read_parquet(p7.output_dir(cfg7, "v1.2") / "work" / "ms_moment" / f"labels__{split_id}.parquet").set_index("material_id")["split"]
    labels = frame["material_id"].map(saved).to_numpy()      # the exact Phase 7 per-cell split assignment, so the two targets share rows and splits
    if pd.isna(labels).any():
        raise ValueError(f"split {split_id}: materials without a saved Phase 7 label")
    p7.assert_formula_disjoint(frame["reduced_formula"], labels)
    if kind == "main":
        variants = {t: features[t] for t in ("tier1", "tier2", "tier3")}
    else:
        variants = {name: feats for name, feats in features.items() if name.startswith("A_")}
    preds, _ = p7.run_variants(frame, labels, variants, cfg7["multisplit"]["algorithms"], cfg, cfg["predictor_rules"]["categorical_predictors"])
    preds.insert(0, "split_id", split_id)
    preds.to_parquet(path)
    print(f"[done] split {split_id}", flush=True)


def split_metrics(preds: pd.DataFrame, frame: pd.DataFrame) -> pd.DataFrame:
    sites = frame.set_index("material_id")["n_sites"]
    err = (preds["y_true"] - preds["y_pred"]).abs()
    preds = preds.assign(abs_err=err, abs_err_cell=err * preds["material_id"].map(sites))
    return (preds.groupby(["split_id", "variant", "algorithm"])
            .agg(mae_per_atom=("abs_err", "mean"), mae_per_cell_equivalent=("abs_err_cell", "mean"), n_test=("abs_err", "size")).reset_index())


def tier_effect(per_atom: pd.DataFrame, per_cell: pd.DataFrame) -> pd.DataFrame:
    """Relative MAE improvement Tier 1 -> Tier 3 per split, per-atom target vs per-cell target (same splits, same rows)."""
    rows = []
    for name, df, col in (("per_atom", per_atom, "mae_per_atom"), ("per_cell", per_cell, "mae")):
        wide = df.pivot_table(index=["split_id", "algorithm"], columns="variant", values=col)
        rel = ((wide["tier1"] - wide["tier3"]) / wide["tier1"]).rename("rel_gain").reset_index()
        for alg, g in rel.groupby("algorithm"):
            d = g["rel_gain"].to_numpy()
            lo, hi = p7.t_interval(d)
            rows.append({"target": name, "algorithm": alg, "n_splits": len(d), "mean_relative_mae_gain": d.mean(), "ci_low": lo, "ci_high": hi,
                         "fraction_splits_positive": float((d > 0).mean()), "stable_gain": bool(lo > 0 and (d > 0).mean() >= MIN_FRACTION_POSITIVE)})
    return pd.DataFrame(rows)


def addone_effect(kind_preds: pd.DataFrame, main_metrics: pd.DataFrame) -> pd.DataFrame:
    """Per-atom MAE gain (relative to Tier 2) from adding each physics group to Tier 2, with Tier 3 as the reference; t-interval over splits."""
    err = kind_preds.assign(abs_err=(kind_preds["y_true"] - kind_preds["y_pred"]).abs())
    add = err.groupby(["split_id", "variant", "algorithm"])["abs_err"].mean().rename("mae").reset_index()
    ref = main_metrics.rename(columns={"mae_per_atom": "mae"})[["split_id", "variant", "algorithm", "mae"]]
    base = ref[ref["variant"] == "tier2"].set_index(["split_id", "algorithm"])["mae"]
    rows = []
    for variant, df in pd.concat([add, ref[ref["variant"] == "tier3"]]).groupby("variant"):
        for alg, g in df.groupby("algorithm"):
            d = ((base.loc[list(zip(g["split_id"], g["algorithm"]))].to_numpy() - g["mae"].to_numpy()) / base.loc[list(zip(g["split_id"], g["algorithm"]))].to_numpy())
            lo, hi = p7.t_interval(d)
            rows.append({"added_to_tier2": variant, "algorithm": alg, "n_splits": len(d), "mean_relative_mae_gain": d.mean(), "ci_low": lo, "ci_high": hi,
                         "fraction_splits_positive": float((d > 0).mean()), "stable_gain": bool(lo > 0 and (d > 0).mean() >= MIN_FRACTION_POSITIVE)})
    return pd.DataFrame(rows)


def per_cell_metrics(cfg7: dict) -> pd.DataFrame:
    work = p7.output_dir(cfg7, "v1.2") / "work" / "ms_moment"
    allp = pd.concat([pd.read_parquet(work / f"main__{s}.parquet") for s in SPLITS], ignore_index=True)
    allp["abs_err"] = (allp["y_true"] - allp["y_pred"]).abs()
    return allp.groupby(["split_id", "variant", "algorithm"]).agg(mae=("abs_err", "mean")).reset_index()


def main() -> None:
    cfg, cfg7 = p7.dataset_cfg("v1.2"), p7.load_phase7_config()
    p7.install_diagnostic_algorithm()
    OUT.mkdir(parents=True, exist_ok=True)
    frame = load_peratom_frame(cfg, cfg7)
    features = p7.variant_features(cfg, cfg7)
    kind = sys.argv[1] if len(sys.argv) > 1 else "main"
    if kind == "addone":
        for s in SPLITS:
            run_split(s, cfg, cfg7, frame, features, kind)
        added = pd.concat([pd.read_parquet(OUT / f"peratom_addone__{s}.parquet") for s in SPLITS], ignore_index=True)
        effect = addone_effect(added, pd.read_csv(OUT / "peratom_split_metrics.csv", dtype={"split_id": str}))
        effect.to_csv(OUT / "peratom_addone_effect.csv", index=False, encoding="utf-8")
        pd.set_option("display.width", 200)
        print(effect.round(4).to_string(index=False))
        return
    for s in SPLITS:
        run_split(s, cfg, cfg7, frame, features)
    preds = pd.concat([pd.read_parquet(OUT / f"peratom__{s}.parquet") for s in SPLITS], ignore_index=True)
    metrics = split_metrics(preds, frame)
    metrics.to_csv(OUT / "peratom_split_metrics.csv", index=False, encoding="utf-8")
    effect = tier_effect(metrics, per_cell_metrics(cfg7))
    effect.to_csv(OUT / "peratom_tier_effect.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 200)
    print(effect.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
