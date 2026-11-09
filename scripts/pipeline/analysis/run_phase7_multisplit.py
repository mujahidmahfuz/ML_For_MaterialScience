"""Phase 7 runner: fit the prespecified model grid on prespecified formula-grouped splits (resumable, one file per fit set).

Usage (from EDA/src, see 10_phase7_validation/v1.2/RUN_INSTRUCTIONS.md):
    python run_phase7_multisplit.py --target curie --splits frozen 0 1 2 --kinds main restricted diag trunc

kinds:
    main        tier1 / tier2 / tier3 x {linear, gradient_boosting, xgboost}          (sections 2.A, 2.B)
    restricted  Tier 3 minus feature groups (S_* variants) x the same algorithms      (section 2.C sensitivity)
    addone      Tier 2 plus ONE physics-column group (A_* variants) x the same algorithms (section 2.C companion)
    diag        tier1 / tier2 / tier3 x linear_clip (train-fold clipped Ridge)         (Curie instability diagnosis)
    trunc       Curie only: main grid refit on the population with TC <= extreme threshold (sensitivity)
"""
from __future__ import annotations

import argparse
import time

import pandas as pd

import phase6_common as pc
import phase6_models as pm
import phase7_validation as p7

KINDS = ("main", "restricted", "addone", "control", "diag", "trunc")


def kind_plan(kind: str, features: dict[str, list[str]], algorithms: list[str]) -> tuple[dict, list[str]]:
    tiers = {t: features[t] for t in ("tier1", "tier2", "tier3")}
    if kind in ("main", "trunc"):
        return tiers, algorithms
    if kind == "restricted":
        return {k: v for k, v in features.items() if k.startswith("S_")}, algorithms
    if kind == "addone":
        return {k: v for k, v in features.items() if k.startswith("A_")}, algorithms
    if kind == "control":   # corrective experiment: Tier 2 + ONE derived cell-size scalar (sites in the MP cell)
        return {"C_T2_plus_nsites": features["tier2"] + [p7.DERIVED_NSITES_COLUMN]}, algorithms
    if kind == "diag":
        return tiers, [p7.LINEAR_CLIP]
    raise ValueError(kind)


def run_one(target: str, split_id: str, kind: str, cfg: dict, cfg7: dict, work_dir, frame, features) -> None:
    out = work_dir / f"{kind}__{split_id}.parquet"
    if out.exists():
        print(f"[skip] {out.name}")
        return
    t0 = time.perf_counter()
    labels = p7.split_labels_for(frame, cfg7, split_id)
    p7.assert_formula_disjoint(frame["reduced_formula"], labels)
    pd.DataFrame({"material_id": frame["material_id"], "split": labels}).to_parquet(work_dir / f"labels__{split_id}.parquet")
    used = frame
    if kind == "control":
        used = frame.assign(**{p7.DERIVED_NSITES_COLUMN: frame["p3_volume"] / frame["p3_volume_per_atom"]})
    if kind == "trunc":
        keep = (frame["value"] <= cfg7["curie_sensitivity"]["extreme_threshold_k"]).to_numpy()
        used, labels = frame[keep].reset_index(drop=True), labels[keep]
    variants, algorithms = kind_plan(kind, features, cfg7["multisplit"]["algorithms"])
    preds, records = p7.run_variants(used, labels, variants, algorithms, cfg,
                                     cfg["predictor_rules"]["categorical_predictors"])
    preds.insert(0, "split_id", split_id)
    preds.insert(0, "target", target)
    meta = pd.DataFrame(records).assign(target=target, split_id=split_id, kind=kind, n_test=int((labels == "test").sum()))
    meta.to_csv(work_dir / f"{kind}__{split_id}__selection.csv", index=False)
    preds.to_parquet(out)
    print(f"[done] {target} {kind} split={split_id} rows={len(preds)} {time.perf_counter() - t0:.0f}s", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, choices=["curie", "ms_moment"])
    ap.add_argument("--splits", nargs="+", required=True, help="'frozen' and/or integers 0..n_splits-1")
    ap.add_argument("--kinds", nargs="+", default=["main"], choices=KINDS)
    ap.add_argument("--dataset", default="v1.2", choices=["v1.2", "v1.3"])
    args = ap.parse_args()
    cfg, cfg7 = p7.dataset_cfg(args.dataset), p7.load_phase7_config()
    spec = cfg7["multisplit"]["targets"][args.target]
    split_path = p7.split_dir(args.dataset) / spec["frozen_split"]
    categorical = cfg["predictor_rules"]["categorical_predictors"]
    frame, _, n_overflow = pm.load_matched_frame(cfg, args.target, "tier3", split_path, categorical)
    features = p7.variant_features(cfg, cfg7)
    work_dir = p7.output_dir(cfg7, args.dataset) / "work" / args.target
    work_dir.mkdir(parents=True, exist_ok=True)
    print(f"{args.target}: N={len(frame)} formulas={frame['reduced_formula'].nunique()} float32-overflow masked={n_overflow}")
    for split_id in args.splits:
        for kind in args.kinds:
            if kind == "trunc" and args.target != "curie":
                continue
            run_one(args.target, split_id, kind, cfg, cfg7, work_dir, frame, features)


if __name__ == "__main__":
    main()
