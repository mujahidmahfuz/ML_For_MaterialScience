"""A17 (round-3 review R1-1): does a larger hyperparameter search change the Tier 1 -> Tier 3 result for the Curie temperature?

The tier comparisons used 2 x 2 grids that were identical for every tier. Tier 3 has 97 inputs against 65, so a model with more, noisier inputs
may need different regularisation; with a small fixed grid "Tier 3 adds nothing" could partly mean "Tier 3 was not tuned". This run repeats the
primary contrast with a much larger search, for the algorithm that is deterministic (histogram gradient boosting; its predictions do not depend on
the thread count).

Design (fixed before any result was seen):
  * matched Curie population (4,602 records), the same 10 prespecified formula-grouped splits, the same rows for both tiers (A1);
  * candidate settings: the 4 settings of the original grid + 60 random draws from the space below, the SAME 64 for both tiers and all splits;
  * selection rule unchanged: lowest validation RMSE, refit on train + validation, test scored once;
  * inference unchanged (A14/A1 helpers): per-split improvement, Nadeau-Bengio corrected interval, formula bootstrap.
Space: learning_rate {0.02, 0.05, 0.1}; max_leaf_nodes {7, 15, 31, 63, 127}; min_samples_leaf {5, 10, 20, 40}; l2_regularization {0, 1, 10};
max_features {0.3, 0.5, 0.75, 1.0} (feature subsampling per split); max_iter {250, 500}.
Decision rule: if the tuned Tier 1 -> Tier 3 contrast still shows no stable gain (A1 rule), the null is robust to tuning; if tuned Tier 3 shows a
stable gain, that is reported and the claim is revised.

Usage (repository root; resumable, one parquet per split):
    python final/revision/scripts/a17_tuning_grid.py fit [workers=4]      fits all splits (about 6-7 s per fit at 3 threads)
    python final/revision/scripts/a17_tuning_grid.py summarize            contrast, comparison with the original grid
Outputs: final/revision/outputs/a17_tuning/{tuned__<split>.parquet, val_scores__<split>.csv, tuned_tier13.csv, tuned_vs_original_mae.csv}
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "3")   # histogram gradient boosting is thread-invariant; 4 workers x 3 threads on 16 cores

import itertools
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rev_common as rc  # noqa: E402

OUT = rc.REV / "a17_tuning"
ALG, TIERS = "gradient_boosting", ("tier1", "tier3")
SPACE = {"learning_rate": [0.02, 0.05, 0.1], "max_leaf_nodes": [7, 15, 31, 63, 127], "min_samples_leaf": [5, 10, 20, 40],
         "l2_regularization": [0.0, 1.0, 10.0], "max_features": [0.3, 0.5, 0.75, 1.0], "max_iter": [250, 500]}
N_RANDOM, GRID_SEED = 60, 20261116
ORIGINAL = [{"max_iter": 500, "learning_rate": lr, "max_leaf_nodes": nl} for lr, nl in itertools.product([0.05, 0.1], [31, 127])]


def candidate_grid() -> list[dict]:
    rng = np.random.default_rng(GRID_SEED)
    full = [dict(zip(SPACE, v)) for v in itertools.product(*SPACE.values())]
    keys = {tuple(sorted(p.items())) for p in ORIGINAL}
    extra = [full[i] for i in rng.permutation(len(full)) if tuple(sorted(full[i].items())) not in keys][:N_RANDOM]
    return ORIGINAL + extra


def fit_split(sid: str) -> str:
    warnings.filterwarnings("ignore")
    path = OUT / f"tuned__{sid}.parquet"
    if path.exists():
        return f"split {sid}: exists"
    t0 = time.perf_counter()
    cfg, cfg7 = rc.setup("curie")
    frame = rc.matched_frame("curie", cfg)
    y = frame["value"].to_numpy(dtype=float)
    feats = rc.p7.variant_features(cfg, cfg7)
    cat = cfg["predictor_rules"]["categorical_predictors"]
    labels = rc.split_labels("curie", frame, cfg7, sid)
    idx = {s: labels == s for s in ("train", "validation", "test")}
    tv, grid, parts, scores = idx["train"] | idx["validation"], candidate_grid(), [], []
    for tier in TIERS:
        cats = [c for c in cat if c in feats[tier]] or None
        X = frame[feats[tier]]
        tier_scores = []
        for k, params in enumerate(grid):
            est = rc.pm.fit(rc.pm.build_estimator(ALG, "regression", params, cfg["random_seed"], cats), ALG, "regression", X[idx["train"]], y[idx["train"]])
            val = rc.pm.score("regression", y[idx["validation"]], est.predict(X[idx["validation"]]), None)["rmse"]
            tier_scores.append({"split_id": sid, "tier": tier, "cfg_id": k, "original_grid": k < len(ORIGINAL), "params": str(params), "val_rmse": float(val)})
        scores += tier_scores
        best = grid[int(np.argmin([r["val_rmse"] for r in tier_scores]))]
        final = rc.pm.fit(rc.pm.build_estimator(ALG, "regression", best, cfg["random_seed"], cats), ALG, "regression", X[tv], y[tv])
        res = {"test_pred": np.asarray(final.predict(X[idx["test"]]))}
        parts.append(rc.chunk_rows(frame, labels, y, res, split_id=sid, variant=tier, algorithm="gradient_boosting_tuned", best_params=str(best)))
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(scores).to_csv(OUT / f"val_scores__{sid}.csv", index=False)
    pd.concat(parts).to_parquet(path)
    return f"split {sid}: done in {time.perf_counter() - t0:.0f} s"


def fit_all(workers: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"{len(candidate_grid())} candidate settings per tier and split; {workers} workers", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for msg in pool.map(fit_split, rc.SPLITS):
            print(msg, flush=True)


def summarize() -> None:
    import a1_tier_inference as a1
    import a14_pooled_tier_inference as a14
    tuned = pd.concat([pd.read_parquet(OUT / f"tuned__{s}.parquet") for s in rc.SPLITS], ignore_index=True)
    tuned["split_id"] = tuned["split_id"].astype(str)
    base, _ = a1.regression_predictions("curie")
    base = base[base["algorithm"] == "gradient_boosting"]
    n_all = a1.n_total("curie")
    runs = (("original 2x2 grid", base, "gradient_boosting"), ("larger search (64 settings)", tuned, "gradient_boosting_tuned"))
    rows, mae = [], []
    for name, df, alg in runs:
        formulas = pd.Index(sorted(df["reduced_formula"].unique()))
        rng = np.random.default_rng(a1.SEED + 7000)
        counts = np.vstack([np.bincount(rng.integers(0, len(formulas), len(formulas)), minlength=len(formulas)) for _ in range(a1.N_BOOT)])
        d, boot, n_test = a14.per_algorithm_arrays(df, alg, "regression", counts, formulas)
        rows.append(a14.summarize(name, "curie", d, boot, n_test, n_all, "mae"))
        for tier in TIERS:
            per = [(g["y_true"] - g["y_pred"]).abs().mean() for _, g in df[df["variant"] == tier].groupby("split_id")]
            mae.append({"search": name, "tier": tier, "mae_mean_over_splits": float(np.mean(per)), "mae_sd_across_splits": float(np.std(per, ddof=1))})
    pd.DataFrame(rows).to_csv(OUT / "tuned_tier13.csv", index=False)
    pd.DataFrame(mae).to_csv(OUT / "tuned_vs_original_mae.csv", index=False)
    val = pd.concat([pd.read_csv(OUT / f"val_scores__{s}.csv") for s in rc.SPLITS])
    gain = val.groupby(["split_id", "tier"]).apply(lambda g: g[g["original_grid"]]["val_rmse"].min() - g["val_rmse"].min(), include_groups=False)
    pd.set_option("display.width", 200)
    print(pd.DataFrame(rows)[["pooled_over", "mean_improvement", "nb_ci_low", "nb_ci_high", "boot_ci_low", "boot_ci_high", "n_positive", "mde80"]].round(2).to_string(index=False))
    print(pd.DataFrame(mae).round(2).to_string(index=False))
    print("validation RMSE gain (K) of the larger search over the original grid, mean over splits:\n", gain.groupby("tier").mean().round(2).to_string())
    print("settings chosen:\n", tuned.groupby(["variant", "split_id"])["best_params"].first().unstack(0).to_string())


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "fit"
    if mode == "fit":
        fit_all(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
    else:
        summarize()
