"""Phase 8 XAI-stability: TreeSHAP importance and family shares over the 10 prespecified Phase 7 formula-grouped splits.

For each target (ordering, curie on dataset v1.3; ms_moment on v1.2, whose inputs are unchanged) and each of tier1/tier2/tier3, the XGBoost
model with the already-selected hyperparameters (no re-tuning) is refit on train+validation of split i and TreeSHAP is computed on that split's
test rows. Saved per fit: mean |SHAP| per feature. Ordering has no Phase 7 split set; the same seeds and random_group_split rule are applied
with the formula-mean of the class code as the stratification value (documented extension).
Usage (from EDA/src, OMP_NUM_THREADS unset):  python run_phase8_xai_stability.py <ordering|curie|ms_moment>
Outputs: EDA/11_phase8_xai_uq/xai_stability/<target>/shap_importance_per_split.csv
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

import phase6_common as pc
import phase6_interp as pi
import phase6_models as pm
import phase7_validation as p7

CLASSES = ["FM", "AFM", "FiM", "NM"]
TIERS = ["tier1", "tier2", "tier3"]
SETUP = {
    "ordering": {"version": "v1.3", "split": "matched_split_ordering.csv", "task": "classification"},
    "curie": {"version": "v1.3", "split": "matched_split_curie.csv", "task": "regression"},
    "ms_moment": {"version": "v1.2", "split": "matched_split_ms.csv", "task": "regression"},
}
OUT = pc.EDA_ROOT / "11_phase8_xai_uq" / "xai_stability"


def selected_params(target: str) -> dict:
    """XGBoost hyperparameters per tier from the existing selections (Phase 7 v1.3 Stage 6 for ordering/curie, Phase 6 Stage 4 for Ms)."""
    if target == "ms_moment":
        d = json.loads((pc.EDA_ROOT / "05_matched_tier_physics/v1.2/ms/hyperparameters_and_preprocessing_matched_ms_moment.json").read_text(encoding="utf-8"))
        return {tr: d[tr]["xgboost"]["selected_hyperparameters"] for tr in TIERS}
    d = json.loads((pc.EDA_ROOT / "10_phase7_validation/v1.3/stage6_shap/selected_hyperparameters_v13.json").read_text(encoding="utf-8"))
    return {tr: d[target][tr]["selected_hyperparameters"] for tr in TIERS}


def encode(frame: pd.DataFrame, task: str) -> np.ndarray:
    if task == "classification":
        return frame["value"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy()
    return frame["value"].to_numpy(dtype=float)


def one_split(target: str, split_id: int, cfg: dict, cfg7: dict, frames: dict, feats: dict, params: dict, y: np.ndarray, task: str) -> list[pd.DataFrame]:
    base = frames["tier1"]
    probe = pd.DataFrame({"reduced_formula": base["reduced_formula"].to_numpy(), "value": y.astype(float)})
    labels = p7.split_labels_for(probe, cfg7, split_id)
    p7.assert_formula_disjoint(base["reduced_formula"], labels)
    trval, test = np.isin(labels, ["train", "validation"]), labels == "test"
    cat_all = cfg["predictor_rules"]["categorical_predictors"]
    rows = []
    for tr in TIERS:
        cat = [c for c in cat_all if c in feats[tr]]
        est = pm.build_estimator("xgboost", task, params[tr], cfg["random_seed"], categorical=cat)
        model = pm.fit(est, "xgboost", task, frames[tr].loc[trval, feats[tr]], y[trval])
        vals, _ = pi.tree_shap(model, frames[tr].loc[test, feats[tr]])
        imp = pi.global_importance(vals, feats[tr])
        rows.append(pd.DataFrame({"target": target, "split_id": split_id, "tier": tr, "feature": feats[tr], "family": pi.family_map(feats[tr]).to_numpy(),
                                  "mean_abs_shap": imp.to_numpy(), "n_test": int(test.sum()), "n_test_formulas": int(base.loc[test, "reduced_formula"].nunique())}))
        print(f"{target} split {split_id} {tr}: n_test={int(test.sum())}", flush=True)
    return rows


def main() -> None:
    target = sys.argv[1]
    spec = SETUP[target]
    cfg, cfg7 = p7.dataset_cfg(spec["version"]), p7.load_phase7_config()
    p7.install_diagnostic_algorithm()
    feats = {tr: pc.read_predictor_list(cfg, tr) for tr in TIERS}
    cat_all = cfg["predictor_rules"]["categorical_predictors"]
    frames = {tr: pm.load_matched_frame(cfg, target, tr, p7.split_dir(spec["version"]) / spec["split"], categorical=[c for c in cat_all if c in feats[tr]])[0]
              for tr in TIERS}
    ref = frames["tier1"]["material_id"].to_numpy()
    assert all(np.array_equal(frames[tr]["material_id"].to_numpy(), ref) for tr in TIERS)
    y, params = encode(frames["tier1"], spec["task"]), selected_params(target)
    out = OUT / target
    out.mkdir(parents=True, exist_ok=True)
    pieces = []
    for i in range(cfg7["multisplit"]["n_splits"]):
        pieces += one_split(target, i, cfg, cfg7, frames, feats, params, y, spec["task"])
        pd.concat(pieces).to_csv(out / "shap_importance_per_split.csv", index=False, encoding="utf-8")


if __name__ == "__main__":
    main()
