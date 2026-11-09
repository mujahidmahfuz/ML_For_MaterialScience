"""Phase 7 driver: aggregate the saved multi-split fits into the protocol's CSV outputs.

Run from EDA/src after run_phase7_multisplit.py has finished:  python phase7_run_aggregate.py
Writes into EDA/10_phase7_validation/v1.2/ (never into Phase 6 folders).
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import phase6_common as pc
import phase6_models as pm
import phase7_aggregate as agg
import phase7_linear as linr
import phase7_validation as p7

SCRIPT = "src/phase7_run_aggregate.py"
FILE_STEM = {"curie": "phase7_curie_multisplit_results.csv", "ms_moment": "phase7_ms_multisplit_results.csv"}


def restricted_comparisons(cfg7: dict) -> list[tuple]:
    comps = [("tier1", "tier3"), ("tier2", "tier3"), ("tier1", "tier2"),
             ("tier2", "C_T2_plus_nsites"), ("tier1", "C_T2_plus_nsites"), ("C_T2_plus_nsites", "tier3")]
    for name in cfg7["tier3_restricted_variants"]:
        comps += [("tier1", name), (name, "tier3")]
    for name in cfg7["tier2_plus_variants"]:
        comps += [("tier2", name), ("tier1", name)]
    return comps


def analyses_for(target: str, cfg7: dict, work_dir, pop: agg.Population) -> list[dict]:
    """Every analysis block of one target: name, stats dict, comparisons, algorithms, selection table, population."""
    algs = cfg7["multisplit"]["algorithms"]
    extreme = cfg7["curie_sensitivity"]["extreme_threshold_k"]
    main = agg.load_kind(work_dir, "main")
    blocks = [{"name": "primary_matched", "stats": agg.keyed_stats(main, pop), "comps": agg.PRIMARY_COMPARISONS, "algs": algs,
               "sel": agg.load_selection(work_dir, "main"), "pop": pop}]
    extra = [e for e in (agg.load_kind(work_dir, k) for k in ("restricted", "addone", "control")) if len(e)]
    if extra:
        sens_ids = set.intersection(*(set(e["split_id"]) for e in extra))   # splits where every sensitivity kind was run
        extra = [e[e["split_id"].isin(sens_ids)] for e in extra]
        both = pd.concat([main[main["split_id"].isin(sens_ids)], *extra], ignore_index=True)
        sel = pd.concat([agg.load_selection(work_dir, k) for k in ("main", "restricted", "addone", "control")], ignore_index=True)
        blocks.append({"name": "tier3_feature_sensitivity", "stats": agg.keyed_stats(both, pop), "comps": restricted_comparisons(cfg7),
                       "algs": algs, "sel": sel, "pop": pop})
    diag = agg.load_kind(work_dir, "diag")
    if len(diag):
        blocks.append({"name": "diag_linear_clip", "stats": agg.keyed_stats(diag, pop), "comps": agg.PRIMARY_COMPARISONS,
                       "algs": [p7.LINEAR_CLIP], "sel": agg.load_selection(work_dir, "diag"), "pop": pop})
    if target == "curie":
        blocks.append({"name": "sens_rescore_excluding_extreme_test_rows", "stats": agg.keyed_stats(main, pop, extreme),
                       "comps": agg.PRIMARY_COMPARISONS, "algs": algs, "sel": pd.DataFrame(), "pop": pop})
        trunc = agg.load_kind(work_dir, "trunc")
        if len(trunc):
            sub = agg.Population(target, pop.frame[pop.frame["value"] <= extreme].reset_index(drop=True), pop.formulas, pop.code_of)
            blocks.append({"name": "sens_refit_without_extreme_rows", "stats": agg.keyed_stats(trunc, sub),
                           "comps": agg.PRIMARY_COMPARISONS, "algs": algs, "sel": agg.load_selection(work_dir, "trunc"), "pop": sub})
    return blocks


def run_target(cfg: dict, cfg7: dict, target: str, out, version: str = "v1.2") -> tuple[pd.DataFrame, pd.DataFrame]:
    work_dir = out / "work" / target
    pop = agg.Population.load(cfg, cfg7, target, version)
    extreme = cfg7["curie_sensitivity"]["extreme_threshold_k"] if target == "curie" else None
    comp = agg.split_composition_table(pop, work_dir, extreme)
    comp.to_csv(out / f"phase7_split_composition_{target}.csv", index=False, encoding="utf-8")
    results, paired = [], []
    for block in analyses_for(target, cfg7, work_dir, pop):
        if not block["stats"]:
            continue
        counts = agg.count_columns(agg.split_composition_table(block["pop"], work_dir, None))
        results.append(agg.per_split_rows(block["stats"], block["pop"], cfg7, block["name"], block["sel"], counts))
        paired.append(agg.paired_rows(block["stats"], block["pop"], cfg7, block["name"], list(block["comps"]), block["algs"]))
        print(f"{target}: {block['name']} done", flush=True)
    results_df = pd.concat(results, ignore_index=True)
    results_df["included_in_pooled_statistics"] = results_df["split_id"] != "frozen"
    results_df.to_csv(out / FILE_STEM[target], index=False, encoding="utf-8")
    return results_df, pd.concat(paired, ignore_index=True)


def frozen_reproduction(out) -> pd.DataFrame:
    """Phase 7 pipeline on the frozen Phase 6 split vs the saved Stage 4 test predictions."""
    rows = []
    s4 = pc.EDA_ROOT / "05_matched_tier_physics" / "v1.2"
    for target, sub, fname in (("curie", "curie", "predictions_matched_curie.csv"), ("ms_moment", "ms", "predictions_matched_ms_moment.csv")):
        ref = pd.read_csv(s4 / sub / fname)
        ref = ref[ref["split"] == "test"].set_index("material_id")
        frozen = pd.read_parquet(out / "work" / target / "main__frozen.parquet")
        for (variant, alg), g in frozen.groupby(["variant", "algorithm"]):
            diff = float(np.abs(ref.loc[g["material_id"], f"{variant}_pred_{alg}"].to_numpy() - g["y_pred"].to_numpy()).max())
            rows.append({"target": target, "variant": variant, "algorithm": alg, "max_abs_prediction_difference": diff,
                         "reproduces_stage4": diff < 1e-6})
    return pd.DataFrame(rows)


def linear_diagnosis(cfg: dict, cfg7: dict, out, target: str, version: str = "v1.2") -> pd.DataFrame:
    """Section 2.A: where and why the Ridge Tier 3 predictions explode (tables written; returns the instability table)."""
    work_dir = out / "work" / target
    tag = {"curie": "curie", "ms_moment": "ms"}[target]
    preds = [agg.load_kind(work_dir, k) for k in ("main", "diag")]
    table = linr.instability_table(pd.concat([p for p in preds if len(p)], ignore_index=True))
    table.to_csv(out / f"phase7_{tag}_linear_instability.csv", index=False, encoding="utf-8")
    bad = table[(table["variant"] == "tier3") & (table["algorithm"] == "linear") & (table["n_exploded_predictions"] > 0)]
    if bad.empty:
        return table
    categorical = cfg["predictor_rules"]["categorical_predictors"]
    spec = cfg7["multisplit"]["targets"][target]
    frame, _, _ = pm.load_matched_frame(cfg, target, "tier3", p7.split_dir(version) / spec["frozen_split"], categorical)
    explained = linr.explain_explosions(frame, pc.read_predictor_list(cfg, "tier3"), work_dir, list(bad["split_id"]),
                                        cfg["random_seed"], categorical)
    explained.to_csv(out / f"phase7_{tag}_linear_explosion_rows.csv", index=False, encoding="utf-8")
    linr.feature_blame(explained).to_csv(out / f"phase7_{tag}_linear_explosion_features.csv", index=False, encoding="utf-8")
    return table


def main() -> None:
    version = sys.argv[sys.argv.index("--dataset") + 1] if "--dataset" in sys.argv else "v1.2"
    targets = sys.argv[sys.argv.index("--targets") + 1:] if "--targets" in sys.argv else None
    cfg, cfg7 = p7.dataset_cfg(version), p7.load_phase7_config()
    out = p7.output_dir(cfg7, version)
    all_paired = []
    for target in targets or cfg7["multisplit"]["targets"]:
        _, paired = run_target(cfg, cfg7, target, out, version)
        all_paired.append(paired)
    paired = pd.concat(all_paired, ignore_index=True)
    paired.to_csv(out / "phase7_paired_tier_differences.csv", index=False, encoding="utf-8")
    robust = agg.robustness_summary(paired, cfg7["decision_gate"]["min_fraction_splits_positive"])
    robust.to_csv(out / "phase7_robustness_summary.csv", index=False, encoding="utf-8")
    for target in targets or cfg7["multisplit"]["targets"]:
        linear_diagnosis(cfg, cfg7, out, target, version)
    names = [FILE_STEM[t] for t in (targets or FILE_STEM)] + ["phase7_paired_tier_differences.csv", "phase7_robustness_summary.csv"]
    if version == "v1.2":   # Stage 4 predictions exist only for the frozen v1.2 matched populations
        repro = frozen_reproduction(out)
        repro.to_csv(out / "phase7_frozen_split_reproduction.csv", index=False, encoding="utf-8")
        names.append("phase7_frozen_split_reproduction.csv")
        print(f"frozen-split reproduction: {int(repro['reproduces_stage4'].sum())}/{len(repro)} fits identical to Stage 4")
    for name in names:
        pc.log_run(cfg, SCRIPT, f"phase7_aggregate_{version}", "curie+ms_moment", "tier1/2/3", "Physics-complete", 0,
                   (out / name).relative_to(pc.EDA_ROOT.parent))


if __name__ == "__main__":
    main()
