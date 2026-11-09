"""Phase 7 section 3 supporting checks (no reanalysis): reconciliation, SHAP/ablation consistency, subgroup adequacy,
secondary-target claim audit. Every function returns rows {section, check, status, detail}; status is PASS / FAIL / INFO."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
from scipy.stats import norm

import phase6_common as pc
import phase6_models as pm

EDA = pc.EDA_ROOT
S4 = EDA / "05_matched_tier_physics" / "v1.2"
S6 = EDA / "07_interpretability" / "v1.2"
TARGET_SUBDIR = {"ordering": "ordering", "curie": "curie", "ms_moment": "ms"}
SHAP_STEM = {"ordering": "ordering", "curie": "curie", "ms_moment": "ms_moment"}
PRED_FILE = {"ordering": "predictions_matched_ordering.csv", "curie": "predictions_matched_curie.csv",
             "ms_moment": "predictions_matched_ms_moment.csv"}
SPLIT_FILE = {"ordering": "matched_split_ordering.csv", "curie": "matched_split_curie.csv", "ms_moment": "matched_split_ms.csv"}
PRIMARY = {"ordering": "macro_f1", "curie": "mae", "ms_moment": "mae"}
ALGS = ("linear", "gradient_boosting", "xgboost")
TIER_PAIRS = (("tier1", "tier2"), ("tier2", "tier3"), ("tier1", "tier3"))


def row(section: str, check: str, ok: bool | None, detail: str) -> dict:
    return {"section": section, "check": check, "status": "INFO" if ok is None else ("PASS" if ok else "FAIL"), "detail": detail}


# ------------------------------------------------------------------------------------------------ 3a reconciliation
def recompute_metric(target: str, y, pred, classes: list[str]) -> dict:
    if target == "ordering":
        return pm.classification_metrics(y, pred, classes)
    return pm.regression_metrics(y, pred)


def max_metric_discrepancy(target: str, te: pd.DataFrame, core: pd.DataFrame, classes: list[str]) -> float:
    worst = 0.0
    for tier in ("tier1", "tier2", "tier3"):
        for alg in ALGS:
            m = recompute_metric(target, te["y_true"].to_numpy(), te[f"{tier}_pred_{alg}"].to_numpy(), classes)
            ref = core[(core["target"] == target) & (core["tier"] == tier) & (core["algorithm"] == alg)].iloc[0]
            for k, v in m.items():
                if pd.notna(ref.get(f"test_{k}", np.nan)):
                    worst = max(worst, abs(v - ref[f"test_{k}"]) / max(1.0, abs(ref[f"test_{k}"])))
    return worst


def check_deltas(target: str, te: pd.DataFrame, deltas: pd.DataFrame, classes: list[str]) -> dict:
    key = PRIMARY[target]
    worst = 0.0
    for alg in ALGS:
        for t1, t2 in TIER_PAIRS:
            m1 = recompute_metric(target, te["y_true"].to_numpy(), te[f"{t1}_pred_{alg}"].to_numpy(), classes)[key]
            m2 = recompute_metric(target, te["y_true"].to_numpy(), te[f"{t2}_pred_{alg}"].to_numpy(), classes)[key]
            imp = (m2 - m1) if key == "macro_f1" else (m1 - m2)
            ref = deltas[(deltas["target"] == target) & (deltas["algorithm"] == alg) & (deltas["from_tier"] == t1) &
                         (deltas["to_tier"] == t2) & (deltas["metric"] == key)].iloc[0]
            worst = max(worst, abs(imp - ref["improvement"]) / max(1.0, abs(ref["improvement"])))
    return row("3a", f"{target}: 9 tier-pair improvements ({key}) recomputed from predictions match matched_tier_deltas.csv",
               worst < 1e-8, f"max relative difference {worst:.2e}")


def reconcile_stage4(cfg: dict) -> list[dict]:
    out = []
    core = pd.read_csv(S4 / "matched_tier_core_metrics.csv")
    deltas = pd.read_csv(S4 / "matched_tier_deltas.csv")
    classes = cfg["targets"]["ordering"]["classes"]
    pop = {"ordering": 13914, "curie": 5490, "ms_moment": 10852}
    for target, sub in TARGET_SUBDIR.items():
        preds = pd.read_csv(S4 / sub / PRED_FILE[target])
        split = pd.read_csv(EDA / "02_splits" / "v1.2" / SPLIT_FILE[target])
        held_out_ids = set(split.loc[split["split"] != "train", "material_id"])
        out.append(row("3a", f"{target}: matched population size (split file) and held-out prediction rows",
                       len(split) == pop[target] and len(preds) == len(held_out_ids),
                       f"split file {len(split)} (expected {pop[target]}); prediction rows {len(preds)} = validation + test {len(held_out_ids)}"))
        same = set(preds["material_id"]) == held_out_ids and preds["material_id"].is_unique
        out.append(row("3a", f"{target}: predictions cover exactly the validation + test split ids (unique)", same, "set equality"))
        te = preds[preds["split"] == "test"]
        out.append(row("3a", f"{target}: test rows = split-file test ids",
                       set(te["material_id"]) == set(split.loc[split["split"] == "test", "material_id"]), f"n_test {len(te)}"))
        pred_cols = [c for c in te.columns if "_pred_" in c]
        out.append(row("3a", f"{target}: 9 tier x algorithm prediction columns on one shared, non-null row set",
                       len(pred_cols) == 9 and bool(te[pred_cols].notna().all().all()), f"{len(pred_cols)} columns"))
        worst = max_metric_discrepancy(target, te, core, classes)
        out.append(row("3a", f"{target}: test metrics recomputed from saved predictions reproduce matched_tier_core_metrics.csv",
                       worst < 1e-8, f"max relative difference {worst:.2e}"))
        n_by_tier = {t: sorted(v) for t, v in core[core["target"] == target].groupby("tier")["n_test"].unique().items()}
        out.append(row("3a", f"{target}: n_test identical at every tier (no unmatched samples)",
                       len({tuple(v) for v in n_by_tier.values()}) == 1, str(n_by_tier)))
        out.append(check_deltas(target, te, deltas, classes))
    return out


def first_summary_line(summary: str, prefix: str) -> str:
    return next(ln for ln in summary.splitlines() if ln.strip().startswith(prefix) and "best" in ln)


def reconcile_headlines() -> list[dict]:
    out = []
    base = pd.read_csv(EDA / "03_baseline_tier1" / "v1.2" / "baseline_model_metrics.csv")
    summary = (EDA / "09_final_tables_figures" / "phase6_final_summary.txt").read_text(encoding="utf-8")
    spec = {"ordering": ("Magnetic ordering", "test_macro_f1", max, r"macro-F1 ([0-9.]+)"),
            "curie": ("Curie temperature", "test_mae", min, r"MAE ([0-9.]+)"),
            "ms_moment": ("Ms (moment per unit cell)", "test_mae", min, r"MAE ([0-9.]+)")}
    for target, (prefix, col, fn, regex) in spec.items():
        val = fn(base[(base["target"] == target) & (base["algorithm"] != "dummy")][col])
        found = re.search(regex, first_summary_line(summary, prefix))
        out.append(row("3a", f"headline {target}: Phase 6 final summary value equals best Stage 2 {col}",
                       found is not None and abs(float(found.group(1)) - val) < 5e-3 * max(1.0, val),
                       f"summary {found.group(1) if found else 'n/a'} vs table {val:.4f}"))
    t3b = pd.read_csv(EDA / "09_final_tables_figures" / "tables" / "table3_physics_ablation_matched.csv")
    out.append(row("3a", "final Table 3 uses the matched populations only (13,914 / 5,490 / 10,852)",
                   set(t3b["Matched N"]) == {"13,914", "5,490", "10,852"}, str(sorted(set(t3b["Matched N"])))))
    return out


def reconcile_other_stages() -> list[dict]:
    out = []
    pop = pd.read_csv(EDA / "04_tier2_ablation" / "v1.2" / "tier2_ablation_population_check.csv")
    out.append(row("3a", "Stage 3 (Tier 1 vs Tier 2): identical N at both tiers in every split",
                   bool((pop["N_tier1"] == pop["N_tier2"]).all()), f"{len(pop)} target x split rows"))
    fam = pd.read_csv(EDA / "06_material_groups" / "v1.2" / "family_metrics.csv")
    piv = fam[fam["scope"].isin(["general_on_family", "specific_on_family"])].pivot_table(
        index=["target", "group", "algorithm"], columns="scope", values="n_test")
    out.append(row("3a", "Stage 5: family-specific and general models scored on the same test rows (equal n_test)",
                   bool((piv["general_on_family"] == piv["specific_on_family"]).all()), f"{len(piv)} comparisons"))
    sec = pd.read_csv(EDA / "08_secondary" / "v1.2" / "table_secondary_matched_population.csv")
    out.append(row("3a", "Stage 7 matched sets are the small Tier 3 subsets (N 404 / 247 / 252)",
                   sorted(sec["n_tier3_matched"]) == [247, 252, 404], str(dict(zip(sec["target"], sec["n_tier3_matched"])))))
    repro = pd.read_csv(S6 / "stage4_reproduction_check.csv")
    out.append(row("3a", "Stage 6 refits reproduce Stage 4 test scores", bool(repro["reproduces_stage4"].all()),
                   f"{len(repro)} refits, max abs diff {repro['abs_diff'].max():.1e}"))
    return out


# ------------------------------------------------------------------------------------------------ 3b SHAP and ablation
def shap_consistency(cfg: dict) -> list[dict]:
    out = []
    for target, sub in TARGET_SUBDIR.items():
        stem = SHAP_STEM[target]
        ids = pd.read_csv(S6 / sub / f"shap_test_material_ids_{stem}.csv")["material_id"]
        preds = pd.read_csv(S4 / sub / PRED_FILE[target])
        te = preds[preds["split"] == "test"].reset_index(drop=True)
        out.append(row("3b", f"{target}: SHAP rows = Stage 4 matched test materials (same order)",
                       list(ids) == list(te["material_id"]), f"{len(ids)} materials"))
        for tier in ("tier1", "tier2", "tier3"):
            z = np.load(S6 / sub / f"shap_values_{stem}_{tier}.npz", allow_pickle=True)
            feats = pc.read_predictor_list(cfg, tier)
            out.append(row("3b", f"{target}/{tier}: SHAP feature names and order = model input columns",
                           list(z["features"]) == feats, f"{len(feats)} features"))
            if target != "ordering":
                recon = z["bias"].astype(float) + z["values"].astype(float).sum(axis=1)
                diff = float(np.abs(recon - te[f"{tier}_pred_xgboost"].to_numpy()).max())
                out.append(row("3b", f"{target}/{tier}: bias + sum(SHAP) reproduces the saved XGBoost test predictions",
                               diff < 5e-2, f"max abs error {diff:.2e}"))
    return out


def attribution_vs_increment() -> pd.DataFrame:
    """SHAP physics share next to the matched Tier1->Tier3 improvement verdicts (attribution is not increment)."""
    share = pd.read_csv(S6 / "tier3_physics_shap_share.csv").set_index("target")["ALL_PHYSICS"]
    deltas = pd.read_csv(S4 / "matched_tier_deltas.csv")
    rows = []
    for target in TARGET_SUBDIR:
        d = deltas[(deltas["target"] == target) & (deltas["metric"] == PRIMARY[target]) &
                   (deltas["from_tier"] == "tier1") & (deltas["to_tier"] == "tier3")]
        stable = int((d["verdict"] == "stable improvement").sum())
        rows.append({"target": target, "physics_share_of_total_mean_abs_shap_pct": 100 * float(share[target]),
                     "n_algorithms_stable_improvement_tier1_to_tier3": stable,
                     "n_algorithms_stable_degradation": int((d["verdict"] == "stable degradation").sum()),
                     "reading": "attribution accompanied by a stable increment in every algorithm" if stable == len(d)
                     else "attribution WITHOUT a stable increment in every algorithm"})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------ 3c subgroup adequacy
def distinct_formulas_by_group(cfg: dict, min_test_formulas: int) -> pd.DataFrame:
    members = pd.read_parquet(pc.project_path(cfg, "group_membership"))
    name_to_col = {"Transition Metal": "D_transition_metals", "Rare Earth": "E_rare_earth", "Oxide": "G_oxides",
                   "Intermetallic": "H_intermetallics", "Experimental": "B_experimental", "Computational": "C_computational"}
    split_files = {"ordering": "split_ordering.csv", "curie": "split_curie.csv", "ms_moment": "split_ms.csv"}
    rows = []
    for target, fname in split_files.items():
        sp = pd.read_csv(EDA / "02_splits" / "v1.2" / fname, usecols=["material_id", "reduced_formula", "split"])
        for group, col in name_to_col.items():
            part = sp[sp["material_id"].isin(set(members.loc[members[col], "material_id"]))]
            te = part[part["split"] == "test"]
            rows.append({"target": target, "group": group, "n_rows": len(part),
                         "n_distinct_formulas": part["reduced_formula"].nunique(), "n_test_rows": len(te),
                         "n_test_distinct_formulas": te["reduced_formula"].nunique(),
                         "too_small_for_strong_conclusion": te["reduced_formula"].nunique() < min_test_formulas})
    return pd.DataFrame(rows)


def holm_and_bh(p: pd.Series) -> pd.DataFrame:
    order = p.sort_values().index
    m = len(p)
    sorted_p = p.loc[order].to_numpy()
    holm = np.minimum(1.0, np.maximum.accumulate((m - np.arange(m)) * sorted_p))
    bh = np.minimum(1.0, np.minimum.accumulate((sorted_p * m / (np.arange(m) + 1))[::-1])[::-1])
    return pd.DataFrame({"p_holm": pd.Series(holm, index=order), "q_bh": pd.Series(bh, index=order)}).loc[p.index]


def family_multiplicity(n_boot: int = 500) -> pd.DataFrame:
    """Stage 5 family-specific vs general comparisons (primary metric of each target) with approximate multiplicity
    adjustment. The bootstrap proportion cannot resolve p below 1/n_boot (so Holm could never reject), hence a normal
    approximation from the 95% CI is used: se = CI width / (2 x 1.96), z = improvement / se. A rough guide only."""
    d = pd.read_csv(EDA / "06_material_groups" / "v1.2" / "family_specific_vs_general_deltas.csv")
    d = d[d["metric"] == d["target"].map(lambda t: "macro_f1" if t == "ordering" else "mae")].copy()
    se = ((d["improvement_ci_high"] - d["improvement_ci_low"]) / (2 * 1.96)).clip(lower=1e-12)
    d["approx_p_two_sided"] = np.clip(2 * norm.sf(np.abs(d["improvement"] / se)), 1e-12, 1.0)
    d = pd.concat([d, holm_and_bh(d["approx_p_two_sided"])], axis=1)
    d["stable_unadjusted"] = d["verdict"] != "no stable change"
    d["stable_after_holm_005"] = d["p_holm"] < 0.05
    d["stable_after_bh_005"] = d["q_bh"] < 0.05
    return d


def multiplicity_summary(fam: pd.DataFrame) -> list[dict]:
    n = len(fam)
    return [row("3c", "Stage 5 family-specific vs general: number of comparisons (primary metric)", None,
                f"{n} comparisons; expected chance CI exclusions at 5%: {0.05 * n:.1f}"),
            row("3c", "Stage 5: comparisons stable unadjusted / after Holm / after BH-FDR", None,
                f"{int(fam['stable_unadjusted'].sum())} / {int(fam['stable_after_holm_005'].sum())} / "
                f"{int(fam['stable_after_bh_005'].sum())} (approximate p from the bootstrap proportion)")]


# ------------------------------------------------------------------------------------------------ 3d secondary claims
def secondary_claims() -> list[dict]:
    out = []
    claims = pd.read_csv(EDA / "08_secondary" / "v1.2" / "secondary_matched_tier_claims.csv")
    out.append(row("3d", "K1 / Ms mass / Ms volume: every matched tier comparison is 'no claim'",
                   bool((claims["claim"] == "no claim").all() and (claims["claim_tree_models_only"] == "no claim").all()),
                   f"{len(claims)} comparisons, claims = {sorted(set(claims['claim']))}"))
    texts = {"final summary": EDA / "09_final_tables_figures" / "phase6_final_summary.txt",
             "final tables": EDA / "09_final_tables_figures" / "tables" / "phase6_final_tables.md",
             "stage 7 summary": EDA / "08_secondary" / "v1.2" / "phase6_stage7_secondary_summary.txt"}
    pattern = re.compile(r"(K1|mass|volume)[^\n]*tier[^\n]*(improv|benefit|help|gain)|tier[^\n]*(K1|mass|volume)[^\n]*(improv|benefit|help|gain)",
                         re.IGNORECASE)
    hedge = re.compile(r"no (stable )?(tier|claim)|0 of|not |cannot|exploratory|no tier", re.IGNORECASE)
    for name, path in texts.items():
        hits = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if pattern.search(ln) and not hedge.search(ln)]
        out.append(row("3d", f"{name}: no unqualified tier-improvement sentence about K1 / Ms mass / Ms volume", not hits,
                       "none found" if not hits else " || ".join(hits[:3])))
    return out


def run_all(cfg: dict, min_test_formulas: int) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    fam = family_multiplicity()
    rows = (reconcile_stage4(cfg) + reconcile_headlines() + reconcile_other_stages() + shap_consistency(cfg) +
            multiplicity_summary(fam) + secondary_claims())
    tables = {"attribution_vs_increment": attribution_vs_increment(),
              "subgroup_sizes": distinct_formulas_by_group(cfg, min_test_formulas), "family_multiplicity": fam}
    return pd.DataFrame(rows), tables
