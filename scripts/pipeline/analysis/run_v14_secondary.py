"""Stage 7 part B (repeated formula-grouped CV on the whole clean secondary populations, Tier 1) re-run on Analysis Dataset v1.4.

Same estimators, grids, folds (5 x 3 repeats), seed and paired formula bootstrap as Notebook/phase6_stage7_secondary_targets.ipynb; only the target
populations change (R10 screens: 1 Ms-mass, 9 Ms-volume, 15 K1 rows removed). Results are compared with the v1.2 Stage 7 table.
Run from EDA/src (OMP_NUM_THREADS=4 as in Stage 7; HistGB is ~10x slower otherwise):  python run_v14_secondary.py
Outputs: EDA/08_secondary/v1.4/secondary_cv_metrics.csv, secondary_cv_v12_vs_v14.csv
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import phase6_common as pc
import phase6_cv as cv
import phase6_models as pm
import phase7_validation as p7

VARIANTS = {"k1": ("k1", "raw"), "k1_log": ("k1", "signed_log10"), "ms_mass": ("ms_mass", "raw"), "ms_volume": ("ms_volume", "raw")}
KEYS = ["mae", "rmse", "r2", "median_ae", "rank_corr"]
OUT = pc.EDA_ROOT / "08_secondary" / "v1.4"


def main() -> None:
    cfg = p7.dataset_cfg("v1.4")
    seed, s7 = cfg["random_seed"], cfg["stage7"]["cv"]
    n_folds, n_repeats, val_frac = s7["n_folds"], s7["n_repeats"], s7["inner_validation_fraction"]
    n_boot, algs = cfg["models"]["bootstrap"]["n_resamples"], ["dummy"] + cfg["models"]["reduced_algorithms"]
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, (target, scale) in VARIANTS.items():
        frame, feats, n_masked = cv.load_cv_frame(cfg, target, "tier1")
        y = frame["value"].to_numpy(dtype=float)
        y = cv.signed_log10(y) if scale == "signed_log10" else y
        groups = frame["reduced_formula"].to_numpy()
        print(f"{name}: N {len(frame):,}, {len(set(groups)):,} formula groups, {n_masked} overflow values masked", flush=True)
        oof = {a: cv.cv_predictions(frame, feats, y, a, cfg, n_folds, n_repeats, seed, validation_fraction=val_frac)[0] for a in algs}
        preds = {f"{a}|{r}": oof[a][r] for a in algs for r in range(n_repeats)}
        _, samples = pm.paired_group_bootstrap(y, preds, groups, cv.regression_metrics_ext, KEYS, n_boot, seed)
        ones = np.ones(len(y))
        for a in algs:
            per_rep = pd.DataFrame([cv.regression_metrics_ext(y, oof[a][r], ones) for r in range(n_repeats)])
            row = {"target": name, "algorithm": a, "n": len(y), "n_formula_groups": len(set(groups))}
            for k in KEYS:
                draws = np.mean([samples[f"{a}|{r}"][k] for r in range(n_repeats)], axis=0)
                row.update({f"cv_{k}": per_rep[k].mean(), f"cv_{k}_ci_low": float(np.quantile(draws, 0.025)), f"cv_{k}_ci_high": float(np.quantile(draws, 0.975))})
            rows.append(row)
            print(f"   {a:<18} MAE {row['cv_mae']:.4g}  R2 {row['cv_r2']:.3f} [{row['cv_r2_ci_low']:.3f}, {row['cv_r2_ci_high']:.3f}]", flush=True)
        pd.DataFrame(rows).to_csv(OUT / "secondary_cv_metrics.csv", index=False, encoding="utf-8")
    new = pd.DataFrame(rows)
    old = pd.read_csv(pc.EDA_ROOT / "08_secondary/v1.2/secondary_cv_metrics.csv")
    keep = ["target", "algorithm", "n", "cv_mae", "cv_r2", "cv_r2_ci_low", "cv_r2_ci_high"]
    cmp = old[keep].merge(new[keep], on=["target", "algorithm"], suffixes=("_v12", "_v14"))
    cmp["delta_r2"], cmp["delta_mae"] = cmp["cv_r2_v14"] - cmp["cv_r2_v12"], cmp["cv_mae_v14"] - cmp["cv_mae_v12"]
    cmp.to_csv(OUT / "secondary_cv_v12_vs_v14.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 220, "display.max_columns", 20)
    print(cmp.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
