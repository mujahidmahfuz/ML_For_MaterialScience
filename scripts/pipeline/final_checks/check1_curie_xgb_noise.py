"""Check 1 addendum: how much of the matched-Curie XGBoost tier difference is thread-count / seed noise?

Check 3 found that XGBoost predictions depend on the thread count (and on the model seed) at the level of individual predictions.  The Curie
XGBoost estimates in check 1 come from one realisation (16 threads, Phase 7 seed).  Here the XGBoost fits are repeated with the Phase 7
hyperparameters (main__<split>__selection.csv) under 8 realisations -- threads 1/4/16 with the Phase 7 seed, and seed offsets 1-5 at 16 threads --
and the pooled paired tier differences, their 95% formula-bootstrap CIs and the equivalence verdict are recomputed for each.
Usage (from EDA/src):  python ../../final/scripts/check1_curie_xgb_noise.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parents[2] / "EDA" / "src"
sys.path.insert(0, str(SRC))

import phase6_models as pm  # noqa: E402
import phase7_aggregate as agg  # noqa: E402
import phase7_validation as p7  # noqa: E402

FINAL = Path(__file__).resolve().parents[1]
WORK = FINAL / "work" / "curie_xgb_noise"
OUT = FINAL / "outputs" / "check1_curie"
TIERS = ("tier1", "tier2", "tier3")
SPLITS = [str(i) for i in range(10)]
REALISATIONS = [(1, 0), (4, 0), (16, 0)] + [(16, s) for s in range(1, 6)]     # (threads, seed offset)
MARGIN_K = 10.0
COMPARISONS = [("tier1", "tier2"), ("tier1", "tier3")]


def fit_split(sid: str, threads: int, seed_offset: int, cfg: dict, cfg7: dict, frame: pd.DataFrame, features: dict) -> None:
    path = WORK / f"xgb__t{threads}__s{seed_offset}__{sid}.parquet"
    if path.exists():
        return
    out = p7.output_dir(cfg7, "v1.3") / "work" / "curie"
    saved = pd.read_parquet(out / f"labels__{sid}.parquet").set_index("material_id")["split"]
    labels = frame["material_id"].map(saved).to_numpy()
    p7.assert_formula_disjoint(frame["reduced_formula"], labels)
    sel = pd.read_csv(out / f"main__{sid}__selection.csv")
    sel = sel[sel["algorithm"] == "xgboost"].set_index("variant")
    p7.install_diagnostic_algorithm()
    p7.XGB_N_JOBS = threads
    categorical = cfg["predictor_rules"]["categorical_predictors"]
    y = frame["value"].to_numpy(dtype=float)
    trainval, test = np.isin(labels, ["train", "validation"]), labels == "test"
    parts = []
    for tier in TIERS:
        feats = features[tier]
        cats = [c for c in categorical if c in feats] or None
        params = ast.literal_eval(sel.loc[tier, "best_params"])
        est = pm.fit(pm.build_estimator("xgboost", "regression", params, cfg["random_seed"] + seed_offset, cats), "xgboost", "regression",
                     frame.loc[trainval, feats], y[trainval])
        parts.append(pd.DataFrame({"split_id": sid, "variant": tier, "algorithm": "xgboost", "material_id": frame.loc[test, "material_id"].to_numpy(),
                                   "reduced_formula": frame.loc[test, "reduced_formula"].to_numpy(), "y_true": y[test],
                                   "y_pred": np.asarray(est.predict(frame.loc[test, feats]), dtype=float)}))
    WORK.mkdir(parents=True, exist_ok=True)
    pd.concat(parts, ignore_index=True).to_parquet(path)


def summarise(cfg: dict, cfg7: dict) -> pd.DataFrame:
    pop = agg.Population.load(cfg, cfg7, "curie", "v1.3")
    boot = cfg7["multisplit"]["bootstrap"]
    rows = []
    for threads, seed in REALISATIONS:
        preds = pd.concat([pd.read_parquet(WORK / f"xgb__t{threads}__s{seed}__{s}.parquet") for s in SPLITS], ignore_index=True)
        stats = agg.keyed_stats(preds, pop)
        members = list(stats.values())
        cols = np.flatnonzero(sum(v["n"] for v in members) > 0)
        w = np.zeros((boot["n_resamples"], len(pop.formulas)))
        w[:, cols] = p7.bootstrap_weights(len(cols), boot["n_resamples"], boot["seed"] + 7)
        for v_from, v_to in COMPARISONS:
            lists = {"from": [stats[(s, v_from, "xgboost")] for s in SPLITS], "to": [stats[(s, v_to, "xgboost")] for s in SPLITS]}
            imp, draws, m_from, _ = agg.pooled_draws(lists, "mae", w)["pooled_mean"]
            lo, hi = p7.ci(draws, boot["ci"])
            rows.append({"threads": threads, "seed_offset": seed, "from_variant": v_from, "to_variant": v_to, "tier_from_mae": m_from,
                         "mae_improvement": imp, "ci95_low": lo, "ci95_high": hi,
                         "upper_limit_below_margin": bool(hi < MARGIN_K), "equivalent_within_margin": bool(lo > -MARGIN_K and hi < MARGIN_K)})
    return pd.DataFrame(rows)


def main() -> None:
    cfg, cfg7 = p7.dataset_cfg("v1.3"), p7.load_phase7_config()
    spec = cfg7["multisplit"]["targets"]["curie"]
    categorical = cfg["predictor_rules"]["categorical_predictors"]
    frame, _, _ = pm.load_matched_frame(cfg, "curie", "tier3", p7.split_dir("v1.3") / spec["frozen_split"], categorical)
    features = p7.variant_features(cfg, cfg7)
    for sid in SPLITS:
        for threads, seed in REALISATIONS:
            fit_split(sid, threads, seed, cfg, cfg7, frame, {t: features[t] for t in TIERS})
        print(f"[done] split {sid}", flush=True)
    table = summarise(cfg, cfg7)
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / "curie_xgb_thread_seed_noise.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 220, "display.max_columns", 20)
    print(table.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
