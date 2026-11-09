"""Final check 3 (R9), fitting step: XGBoost on the frozen Phase 7 Ms-per-cell experiment with 1, 4 and 16 threads.

Everything except the XGBoost thread count (n_jobs) is held at the Phase 7 settings: data (matched Ms population, N=10,852, dataset v1.2),
saved train/validation/test assignments (v1.2/work/ms_moment/labels__<split>.parquet), preprocessing, seed (analysis_config random_seed),
tier predictor lists, and the grid.  Two modes per (threads, split):
  refit  : the hyperparameters Phase 7 selected (main__<split>__selection.csv) are applied unchanged; only the final train+validation
           refit and the test prediction are repeated.  This isolates the numerical effect of the thread count.
  select : the whole Phase 7 procedure is repeated (grid on train -> best validation RMSE -> refit); this adds the effect of the
           thread count on which grid point wins.
Resumable: one parquet per (mode, threads, split) in final/work/ms_threads/.
Usage (from EDA/src, OMP_NUM_THREADS unset):
  python ../../final/scripts/check3_ms_threads_fit.py --mode refit --threads 16 4 1 --splits frozen 0 1 2 3 4 5 6 7 8 9
"""
from __future__ import annotations

import argparse
import ast
import sys
import time
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

SRC =Path(__file__).resolve().parents[2] / "EDA" / "src"
sys.path.insert(0, str(SRC))

import phase6_models as pm  # noqa: E402
import phase7_validation as p7  # noqa: E402

WORK = Path(__file__).resolve().parents[1] / "work" / "ms_threads"
TIERS = ("tier1", "tier2", "tier3")


def load_inputs() -> tuple[dict, dict, pd.DataFrame, dict]:
    cfg, cfg7 = p7.dataset_cfg("v1.2"), p7.load_phase7_config()
    spec = cfg7["multisplit"]["targets"]["ms_moment"]
    categorical = cfg["predictor_rules"]["categorical_predictors"]
    frame, _, _ = pm.load_matched_frame(cfg, "ms_moment", "tier3", p7.split_dir("v1.2") / spec["frozen_split"], categorical)
    features = p7.variant_features(cfg, cfg7)
    return cfg, cfg7, frame, {t: features[t] for t in TIERS}


def saved_labels(cfg7: dict, frame: pd.DataFrame, split_id: str) -> np.ndarray:
    work = p7.output_dir(cfg7, "v1.2") / "work" / "ms_moment"
    saved = pd.read_parquet(work / f"labels__{split_id}.parquet").set_index("material_id")["split"]
    labels = frame["material_id"].map(saved).to_numpy()
    if pd.isna(labels).any():
        raise ValueError(f"split {split_id}: materials without a saved Phase 7 label")
    p7.assert_formula_disjoint(frame["reduced_formula"], labels)
    return labels


def saved_xgb_params(cfg7: dict, split_id: str) -> dict[str, dict]:
    sel = pd.read_csv(p7.output_dir(cfg7, "v1.2") / "work" / "ms_moment" / f"main__{split_id}__selection.csv")
    sel = sel[sel["algorithm"] == "xgboost"].set_index("variant")
    return {t: ast.literal_eval(sel.loc[t, "best_params"]) for t in TIERS}


def refit_predict(frame, labels, feats, params, cats, cfg, algorithm: str = "xgboost", seed_offset: int = 0) -> np.ndarray:
    y = frame["value"].to_numpy(dtype=float)
    trainval = np.isin(labels, ["train", "validation"])
    est = pm.fit(pm.build_estimator(algorithm, "regression", params, cfg["random_seed"] + seed_offset, cats), algorithm, "regression",
                 frame.loc[trainval, feats], y[trainval])
    return np.asarray(est.predict(frame.loc[labels == "test", feats]), dtype=float)


def saved_params(cfg7: dict, split_id: str, algorithm: str) -> dict[str, dict]:
    sel = pd.read_csv(p7.output_dir(cfg7, "v1.2") / "work" / "ms_moment" / f"main__{split_id}__selection.csv")
    sel = sel[sel["algorithm"] == algorithm].set_index("variant")
    return {t: ast.literal_eval(sel.loc[t, "best_params"]) for t in TIERS}


def run_one(mode: str, threads: int, split_id: str, cfg, cfg7, frame, features, seed_offset: int = 0) -> None:
    """mode 'refit'/'select': XGBoost at `threads` (seed_offset != 0 changes only the model seed, a seed-noise reference);
    mode 'hgb_refit': sklearn HistGradientBoosting refit with the OpenMP thread pool limited to `threads` (sensitivity of the other booster)."""
    tag = "" if seed_offset == 0 else f"__s{seed_offset}"
    path = WORK / f"{mode}__t{threads}{tag}__{split_id}.parquet"
    if path.exists():
        return
    t0 = time.perf_counter()
    p7.install_diagnostic_algorithm()
    p7.XGB_N_JOBS = threads          # read at estimator-build time by the patched pm.build_estimator
    labels = saved_labels(cfg7, frame, split_id)
    categorical = cfg["predictor_rules"]["categorical_predictors"]
    work = frame.assign(split=labels)
    test = labels == "test"
    y = work["value"].to_numpy(dtype=float)
    algorithm = "gradient_boosting" if mode == "hgb_refit" else "xgboost"
    chosen = saved_params(cfg7, split_id, algorithm)
    parts = []
    for tier in TIERS:
        feats = features[tier]
        cats = [c for c in categorical if c in feats] or None
        if mode in ("refit", "hgb_refit"):
            with threadpool_limits(limits=threads) if mode == "hgb_refit" else nullcontext():
                pred, params = refit_predict(work, labels, feats, chosen[tier], cats, cfg, algorithm, seed_offset), chosen[tier]
        else:
            res = pm.run_algorithm(work, feats, y, "regression", "xgboost", cfg, categorical=cats)
            pred, params = np.asarray(res["test_pred"], dtype=float), res["best_params"]
        parts.append(pd.DataFrame({"threads": threads, "mode": mode, "split_id": split_id, "variant": tier, "algorithm": algorithm,
                                   "material_id": work.loc[test, "material_id"].to_numpy(),
                                   "reduced_formula": work.loc[test, "reduced_formula"].to_numpy(), "y_true": y[test], "y_pred": pred,
                                   "params": str(params), "phase7_params": str(chosen[tier])}))
    WORK.mkdir(parents=True, exist_ok=True)
    pd.concat(parts, ignore_index=True).to_parquet(path)
    print(f"[done] {mode} threads={threads}{tag} split={split_id} {time.perf_counter() - t0:.0f}s", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["refit", "select", "hgb_refit"], required=True)
    ap.add_argument("--threads", nargs="+", type=int, required=True)
    ap.add_argument("--splits", nargs="+", required=True)
    ap.add_argument("--seed-offsets", nargs="+", type=int, default=[0], help="added to the model seed (seed-noise reference; 0 = Phase 7 seed)")
    args = ap.parse_args()
    cfg, cfg7, frame, features = load_inputs()
    print(f"matched Ms N={len(frame)} formulas={frame['reduced_formula'].nunique()}", flush=True)
    for split_id in args.splits:
        for threads in args.threads:
            for offset in args.seed_offsets:
                run_one(args.mode, threads, split_id, cfg, cfg7, frame, features, offset)


if __name__ == "__main__":
    main()
