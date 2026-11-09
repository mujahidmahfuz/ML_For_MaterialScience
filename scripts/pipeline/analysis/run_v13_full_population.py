"""Full-population Tier 1 baseline and Tier 1 -> Tier 2 comparison on Analysis Dataset v1.3 (Stage 2/3 equivalent) for one target.

Run from EDA/src (OMP_NUM_THREADS unset):  python run_v13_full_population.py curie | ordering
Writes EDA/10_phase7_validation/v1.3/v13_full_<target>_metrics.csv and v13_full_<target>_tier2_deltas.csv.
Same estimators, grids, selection rule and metrics as Phase 6; algorithms = reduced set (random forest dropped, as from Stage 3).
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import phase6_models as pm
import phase7_validation as p7

ALGS = ["linear", "gradient_boosting", "xgboost"]
CLASSES = ["FM", "AFM", "FiM", "NM"]
VERSION = "v1.3"
SPLIT_FILE = {"curie": "split_curie.csv", "ordering": "split_ordering.csv"}
PRIMARY = {"curie": ["mae", "rmse", "r2"], "ordering": ["macro_f1", "balanced_accuracy"]}
HIGHER = {"r2", "macro_f1", "balanced_accuracy"}


def target_array(frame: pd.DataFrame, target: str) -> np.ndarray:
    if target == "ordering":
        return frame["value"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy()
    return frame["value"].to_numpy(dtype=float)


def metric_fn(target: str):
    if target == "ordering":
        return lambda y, p, w: pm.classification_metrics(y, p, list(range(len(CLASSES))), w)
    return lambda y, p, w: pm.regression_metrics(y, p, w)


def fit_all(cfg: dict, target: str, task: str) -> tuple[dict, dict]:
    labels = list(range(len(CLASSES))) if task == "classification" else None
    preds, info = {}, {}
    for tier in ("tier1", "tier2"):
        frame, feats = pm.load_modeling_frame(cfg, target, tier, p7.split_dir(VERSION) / SPLIT_FILE[target])
        y = target_array(frame, target)
        te = (frame["split"] == "test").to_numpy()
        info = {"y": y[te], "groups": frame.loc[te, "reduced_formula"].to_numpy(), "n_test": int(te.sum())}
        for alg in (["dummy"] if tier == "tier1" else []) + ALGS:
            preds[f"{tier}|{alg}"] = np.asarray(pm.run_algorithm(frame, feats, y, task, alg, cfg, labels=labels)["test_pred"])
    return preds, info


def tables(target: str, preds: dict, info: dict, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    keys, fn = PRIMARY[target], metric_fn(target)
    cis, samples = pm.paired_group_bootstrap(info["y"], preds, info["groups"], fn, keys, 500, seed)
    rows, deltas = [], []
    for name, p in preds.items():
        tier, alg = name.split("|")
        m = fn(info["y"], p, None)
        rows.append({"target": target, "tier": tier, "algorithm": alg, "n_test": info["n_test"], **{k: m[k] for k in keys},
                     **{f"{k}_ci_low": cis[name][k][0] for k in keys}, **{f"{k}_ci_high": cis[name][k][1] for k in keys}})
    for alg in ALGS:
        m1, m2 = fn(info["y"], preds[f"tier1|{alg}"], None), fn(info["y"], preds[f"tier2|{alg}"], None)
        for k in keys:
            sign = 1 if k in HIGHER else -1
            imp = sign * (np.array(samples[f"tier2|{alg}"][k]) - np.array(samples[f"tier1|{alg}"][k]))
            lo, hi = float(np.quantile(imp, 0.025)), float(np.quantile(imp, 0.975))
            deltas.append({"target": target, "algorithm": alg, "metric": k, "improvement_tier1_to_tier2": sign * (m2[k] - m1[k]), "ci_low": lo,
                           "ci_high": hi, "verdict": "stable improvement" if lo > 0 else ("stable degradation" if hi < 0 else "no stable change")})
    return pd.DataFrame(rows), pd.DataFrame(deltas)


def run(target: str) -> None:
    cfg, cfg7 = p7.dataset_cfg(VERSION), p7.load_phase7_config()
    p7.install_diagnostic_algorithm()
    out = p7.output_dir(cfg7, VERSION)
    preds, info = fit_all(cfg, target, cfg["targets"][target]["task"])
    metrics, deltas = tables(target, preds, info, cfg["random_seed"])
    metrics.to_csv(out / f"v13_full_{target}_metrics.csv", index=False, encoding="utf-8")
    deltas.to_csv(out / f"v13_full_{target}_tier2_deltas.csv", index=False, encoding="utf-8")
    print(metrics.round(3).to_string(index=False))
    print(deltas.round(3).to_string(index=False))


if __name__ == "__main__":
    run(sys.argv[1])
