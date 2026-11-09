"""Phase 8b bias audit and interventions (ordering, Curie; dataset v1.3, Tier 1). Design: EDA/12_phase8_bias/PLAN.md.

Baseline and interventions are fit on TRAIN only (selected XGBoost hyperparameters, no tuning); the class-offset intervention is fitted on
VALIDATION; the test partition is scored once. Every metric carries a paired formula-bootstrap interval (same resamples for all variants).
Usage (from EDA/src, OMP_NUM_THREADS unset):  python run_phase8_bias.py <ordering|curie>
Outputs: EDA/12_phase8_bias/<target>/bias_metrics.csv (variant x subgroup: value, CI, delta vs baseline, CI).
"""
from __future__ import annotations

import ast
import sys

import numpy as np
import pandas as pd

import phase6_common as pc
import phase6_models as pm
import phase7_validation as p7

VERSION, N_BOOT, SEED = "v1.3", 300, 20268000
CLASSES = ["FM", "AFM", "FiM", "NM"]
FAMILIES = ["Transition Metal", "Rare Earth", "Oxide", "Intermetallic"]
OUT = pc.EDA_ROOT / "12_phase8_bias"
OFFSET_GRID, OFFSET_PASSES = np.arange(-1.5, 1.51, 0.1), 3


def load(target: str):
    cfg = p7.dataset_cfg(VERSION)
    p7.install_diagnostic_algorithm()
    split = "split_ordering.csv" if target == "ordering" else "split_curie.csv"
    frame, feats = pm.load_modeling_frame(cfg, target, "tier1", p7.split_dir(VERSION) / split)
    frame = frame.reset_index(drop=True)
    col = "_source" if "_source" in frame.columns else "source"
    src = frame[col].astype(str)
    frame["provenance"] = (np.where(src.str.startswith("mp_reformatted"), "computational_MP", "other") if target == "ordering"
                           else np.where(src.str.contains("chemdata|nemad", case=False), "text_mined", "curated"))
    path = pc.EDA_ROOT / "10_phase7_validation/v1.3/stage5_families" / f"general_predictions_{target}.csv"
    params = ast.literal_eval(pd.read_csv(path, nrows=1)["params_xgboost"].iloc[0])
    return cfg, frame, feats, params


def formula_weights(formulas: pd.Series) -> np.ndarray:
    return 1.0 / np.sqrt(formulas.map(formulas.value_counts()).to_numpy(dtype=float))


def provenance_weights(prov: np.ndarray) -> np.ndarray:
    """Equalise the total weight of each label source (mean weight 1)."""
    counts = pd.Series(prov).value_counts()
    return pd.Series(prov).map(len(prov) / (len(counts) * counts)).to_numpy(dtype=float)


def class_offsets(log_p: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Per-class log-probability offsets (FM fixed at 0) maximising validation macro-F1 by coordinate search."""
    off, labels = np.zeros(log_p.shape[1]), list(range(log_p.shape[1]))
    best = pm.classification_metrics(y, (log_p + off).argmax(1), labels)["macro_f1"]
    for _ in range(OFFSET_PASSES):
        for k in range(1, log_p.shape[1]):
            for v in OFFSET_GRID:
                trial = off.copy()
                trial[k] = v
                s = pm.classification_metrics(y, (log_p + trial).argmax(1), labels)["macro_f1"]
                if s > best + 1e-9:
                    best, off = s, trial
    return off


def subgroup_masks(target: str, meta: pd.DataFrame, y: np.ndarray, groups: dict) -> dict:
    masks = {f"family:{f}": meta["material_id"].isin(groups[f]).to_numpy() for f in FAMILIES}
    masks.update({f"provenance:{p}": (meta["provenance"] == p).to_numpy() for p in sorted(meta["provenance"].unique())})
    if target == "ordering":
        masks.update({f"recall:{c}": y == i for i, c in enumerate(CLASSES)})
    else:
        cuts = np.quantile(y, [1 / 3, 2 / 3])
        masks.update({"range:low_third": y <= cuts[0], "range:middle_third": (y > cuts[0]) & (y <= cuts[1]), "range:high_third": y > cuts[1]})
    return masks


def metric(target: str, name: str, y, pred, w) -> float:
    if w.sum() <= 0:
        return np.nan
    if target == "curie":
        return float(np.average(np.abs(y - pred), weights=w))
    if name.startswith("recall:"):
        return float(np.average(pred == y, weights=w))
    return pm.classification_metrics(y, pred, list(range(len(CLASSES))), w)["macro_f1"]


def all_metrics(target, y, pred, base_w, masks, eq_w) -> dict:
    out = {"overall": metric(target, "overall", y, pred, base_w), "eq_weight_overall": metric(target, "overall", y, pred, base_w * eq_w)}
    for name, m in masks.items():
        out[name] = metric(target, name, y, pred, base_w * m)
    pick = max if target == "curie" else min       # worst = highest MAE / lowest F1
    for key, prefix in (("worst_family", "family:"), ("worst_provenance", "provenance:")):
        vals = [v for k, v in out.items() if k.startswith(prefix) and not np.isnan(v)]
        out[key] = pick(vals) if vals else np.nan
    return out


def bootstrap(target, y, preds: dict, formulas, masks, eq_w) -> dict:
    codes = pd.factorize(pd.Series(formulas))[0]
    rng = np.random.default_rng(SEED)
    boots = {v: [] for v in preds}
    for _ in range(N_BOOT):
        w = np.bincount(rng.integers(0, codes.max() + 1, codes.max() + 1), minlength=codes.max() + 1)[codes].astype(float)
        for v, p in preds.items():
            boots[v].append(all_metrics(target, y, p, w, masks, eq_w))
    return {v: pd.DataFrame(b) for v, b in boots.items()}


def main() -> None:
    target = sys.argv[1]
    cfg, frame, feats, params = load(target)
    task = cfg["targets"][target]["task"]
    y = frame["value"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy() if task == "classification" else frame["value"].to_numpy(dtype=float)
    tr, va, te = ((frame["split"] == s).to_numpy() for s in ("train", "validation", "test"))
    base_w = pm.compute_sample_weight("balanced", y[tr]) if task == "classification" else np.ones(tr.sum())
    w_form = formula_weights(frame.loc[tr, "reduced_formula"])
    w_prov = provenance_weights(frame.loc[tr, "provenance"].to_numpy())
    models = {"baseline": base_w, "I1_formula_weights": base_w * w_form, "I2_provenance_weights": base_w * w_prov}
    pred, proba_va, proba_te = {}, {}, {}
    for name, w in models.items():
        est = pm.build_estimator("xgboost", task, params, cfg["random_seed"])
        m = est.fit(frame.loc[tr, feats], y[tr], sample_weight=w * len(w) / w.sum())
        if task == "classification":
            proba_va[name], proba_te[name] = m.predict_proba(frame.loc[va, feats]), m.predict_proba(frame.loc[te, feats])
            pred[name] = proba_te[name].argmax(1)
        else:
            pred[name] = m.predict(frame.loc[te, feats])
        print(f"{target}: fitted {name}", flush=True)
    if task == "classification":
        for src, label in (("baseline", "I3_class_offsets"), ("I1_formula_weights", "I4_formula_weights+offsets")):
            off = class_offsets(np.log(np.clip(proba_va[src], 1e-9, 1)), y[va])
            pred[label] = (np.log(np.clip(proba_te[src], 1e-9, 1)) + off).argmax(1)
            print(f"{target}: {label} offsets {np.round(off, 2).tolist()}", flush=True)
    meta, y_te = frame.loc[te].reset_index(drop=True), y[te]
    masks = subgroup_masks(target, meta, y_te, pc.load_group_ids(cfg))
    eq_w = formula_weights(meta["reduced_formula"])
    point = {v: all_metrics(target, y_te, p, np.ones(len(y_te)), masks, eq_w) for v, p in pred.items()}
    boots = bootstrap(target, y_te, pred, meta["reduced_formula"].to_numpy(), masks, eq_w)
    rows = []
    for v in pred:
        for k, val in point[v].items():
            lo, hi = np.nanquantile(boots[v][k], [0.025, 0.975])
            d = boots[v][k] - boots["baseline"][k]
            rows.append({"target": target, "variant": v, "subgroup_or_metric": k, "value": val, "ci_low": lo, "ci_high": hi,
                         "delta_vs_baseline": val - point["baseline"][k], "delta_ci_low": np.nanquantile(d, 0.025), "delta_ci_high": np.nanquantile(d, 0.975),
                         "n_test_rows": int(masks[k].sum()) if k in masks else len(y_te)})
    res = pd.DataFrame(rows)
    out = OUT / target
    out.mkdir(parents=True, exist_ok=True)
    res.to_csv(out / "bias_metrics.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 220, "display.max_columns", 20)
    print(res.pivot(index="subgroup_or_metric", columns="variant", values="value").round(3).to_string())
    print(res[res.variant == "baseline"].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
