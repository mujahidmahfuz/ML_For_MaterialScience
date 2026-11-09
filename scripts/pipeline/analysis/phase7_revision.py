"""Phase 7 revision after review: superseding claims register (R3), response to the four blocking items, and the summary section.

Everything is generated from result CSVs (v1.3 outputs in EDA/10_phase7_validation/v1.3, Phase 6 outputs in EDA/0*_*), so no number is
retyped by hand. Run:  python phase7_revision.py   (writes claims_register.md/.csv and revision_response.md next to the v1.3 results).
"""
from __future__ import annotations

import json

import pandas as pd

import phase6_common as pc
import phase7_validation as p7

EDA = pc.EDA_ROOT
ALG = {"linear": "Ridge/logistic", "gradient_boosting": "Gradient Boosting", "xgboost": "XGBoost"}
REF = "xgboost"


def load(out13) -> dict:
    out12 = p7.output_dir(p7.load_phase7_config(), "v1.2")
    return {"manifest": json.loads((EDA / "datasets/v1.3/MANIFEST_v1.3.json").read_text(encoding="utf-8")),
            "curie_robust": pd.read_csv(out13 / "phase7_robustness_summary.csv"), "curie_full": pd.read_csv(out13 / "v13_full_curie_metrics.csv"),
            "curie_t2": pd.read_csv(out13 / "v13_full_curie_tier2_deltas.csv"), "ord_base": pd.read_csv(out13 / "ordering_v13_baseline_metrics.csv"),
            "ord_t2": pd.read_csv(out13 / "v13_full_ordering_tier2_deltas.csv"), "ord_slices": pd.read_csv(out13 / "ordering_v13_provenance_slices.csv"),
            "ord_transfer": pd.read_csv(out13 / "ordering_v13_cross_provenance_transfer.csv"),
            "ord_matched": pd.read_csv(out13 / "ordering_v13_matched_robustness.csv"),
            "p6_base": pd.read_csv(EDA / "03_baseline_tier1/v1.2/baseline_model_metrics.csv"),
            "p6_t2": pd.read_csv(EDA / "04_tier2_ablation/v1.2/tier2_ablation_deltas.csv"),
            "p6_matched": pd.read_csv(EDA / "05_matched_tier_physics/v1.2/matched_tier_deltas.csv"),
            "ms_robust": pd.read_csv(out12 / "phase7_robustness_summary.csv"),
            "s5_deltas": pd.read_csv(out13 / "stage5_families/family_specific_vs_general_deltas.csv"),
            "s5_gaps": pd.read_csv(out13 / "stage5_families/family_vs_rest_gap.csv"),
            "s5_mult": pd.read_csv(out13 / "stage5_families/family_multiplicity.csv"),
            "s6_cmp": pd.read_csv(out13 / "stage6_shap/shap_v12_vs_v13_comparison.csv"),
            "s6_abl": pd.read_csv(out13 / "stage6_shap/tier3_physics_family_ablation.csv")}


def ci(row, lo="ci_low", hi="ci_high", dec=3) -> str:
    return f"[{row[lo]:+.{dec}f}, {row[hi]:+.{dec}f}]"


def p6_row(d: dict, target: str, alg: str) -> pd.Series:
    t = d["p6_base"]
    return t[(t["target"] == target) & (t["algorithm"] == alg)].iloc[0]


def ordering_rows(d: dict) -> list[tuple]:
    b = d["ord_base"].set_index("algorithm")
    x2, g2 = p6_row(d, "ordering", "xgboost"), p6_row(d, "ordering", "gradient_boosting")
    rows = [("Ordering, Tier 1 (full population)",
             f"XGBoost macro-F1 {x2['test_macro_f1']:.3f} [{x2['test_macro_f1_ci_low']:.3f}, {x2['test_macro_f1_ci_high']:.3f}] (best on test); validation-selected Gradient Boosting {g2['test_macro_f1']:.3f}",
             f"XGBoost {b.loc['xgboost','macro_f1']:.3f} [{b.loc['xgboost','macro_f1_ci_low']:.3f}, {b.loc['xgboost','macro_f1_ci_high']:.3f}]; Gradient Boosting {b.loc['gradient_boosting','macro_f1']:.3f}; Ridge {b.loc['linear','macro_f1']:.3f}; dummy {b.loc['dummy','macro_f1']:.3f}",
             "REVISED (target repaired: default-FM JARVIS rows removed) and CAVEATED (provenance rows below)", "ordering_v13_baseline_metrics.csv")]
    xs = d["ord_slices"][d["ord_slices"]["algorithm"] == "xgboost"].set_index("slice")
    tr = d["ord_transfer"]
    pick = lambda src, alg: tr[(tr["train_on"] == src) & (tr["algorithm"] == alg)].iloc[0]   # noqa: E731
    a, ad, c, cd = pick("computational_MP", "xgboost"), pick("computational_MP", "dummy"), pick("experimental", "xgboost"), pick("experimental", "dummy")
    rows.append(("Ordering, provenance", "not examined (Phase 6 pooled computed and experimental labels)",
                 f"within-slice XGBoost macro-F1: computed (MP) {xs.loc['computational_MP','macro_f1']:.3f}, experimental {xs.loc['experimental','macro_f1']:.3f}. "
                 f"Cross-provenance transfer: train MP -> test experimental {a['macro_f1']:.3f} (balanced accuracy {a['balanced_accuracy']:.3f}; 3-class chance 0.333; majority dummy {ad['macro_f1']:.3f}); "
                 f"train experimental -> test MP {c['macro_f1']:.3f} (balanced accuracy {c['balanced_accuracy']:.3f}; majority dummy {cd['macro_f1']:.3f})",
                 "NEW FINDING: ordering skill does not transfer across data provenance (about chance); the headline macro-F1 is not a general capability",
                 "ordering_v13_provenance_slices.csv; ordering_v13_cross_provenance_transfer.csv"))
    return rows


def curie_ms_rows(d: dict) -> list[tuple]:
    c1 = d["curie_full"][d["curie_full"]["tier"] == "tier1"].set_index("algorithm")
    gb, rf = p6_row(d, "curie", "gradient_boosting"), p6_row(d, "curie", "random_forest")
    ms, msv = p6_row(d, "ms_moment", "xgboost"), d["p6_base"][(d["p6_base"]["target"] == "ms_moment") & d["p6_base"]["best_by_validation"]].iloc[0]
    return [("Curie, Tier 1 (full population)",
             f"Gradient Boosting MAE {gb['test_mae']:.1f} K (best on test); Random Forest {rf['test_mae']:.1f} K was best by validation; R2 {gb['test_r2']:.3f}",
             f"Gradient Boosting {c1.loc['gradient_boosting','mae']:.1f} K [{c1.loc['gradient_boosting','mae_ci_low']:.1f}, {c1.loc['gradient_boosting','mae_ci_high']:.1f}], XGBoost {c1.loc['xgboost','mae']:.1f} K, Ridge {c1.loc['linear','mae']:.1f} K, dummy {c1.loc['dummy','mae']:.1f} K; R2 {c1.loc['gradient_boosting','r2']:.3f}",
             "REVISED: with superconducting-Tc / ferroelectric / Neel / out-of-range values removed the target is easier; the old figure described a mixed target", "v13_full_curie_metrics.csv"),
            ("Ms per cell, Tier 1", f"XGBoost MAE {ms['test_mae']:.3f} (best on test); validation-selected {msv['algorithm']} {msv['test_mae']:.3f}",
             "unchanged (the Ms target is identical in v1.3)", "UNCHANGED; quote the validation-selected model or all models, not the best-on-test model", "03_baseline_tier1/v1.2")]


def tier_rows(d: dict) -> list[tuple]:
    ct2 = d["curie_t2"][d["curie_t2"]["metric"] == "mae"].set_index("algorithm")
    ot2 = d["ord_t2"][d["ord_t2"]["metric"] == "macro_f1"].set_index("algorithm")
    p6t = d["p6_t2"]
    p6c = p6t[(p6t["target"] == "curie") & (p6t["metric"] == "mae")].set_index("algorithm")
    rows = [("Tier 2 (oxidation chemistry), full populations",
             f"Curie: Gradient Boosting {p6c.loc['gradient_boosting','improvement']:+.1f} K, XGBoost {p6c.loc['xgboost','improvement']:+.1f} K (stable degradation); ordering and Ms: no stable benefit",
             f"Curie MAE gain: Gradient Boosting {ct2.loc['gradient_boosting','improvement_tier1_to_tier2']:+.1f} K {ci(ct2.loc['gradient_boosting'], dec=1)}, XGBoost {ct2.loc['xgboost','improvement_tier1_to_tier2']:+.1f} K {ci(ct2.loc['xgboost'], dec=1)} (stable degradation); "
             f"ordering macro-F1 gain: XGBoost {ot2.loc['xgboost','improvement_tier1_to_tier2']:+.4f} {ci(ot2.loc['xgboost'], dec=4)} (stable degradation), others no stable change",
             "CONFIRMED: no benefit from Tier 2; small stable degradation for tree models on Curie and for XGBoost on ordering", "v13_full_*_tier2_deltas.csv")]
    pm_, om = d["p6_matched"], d["ord_matched"]
    pg = pm_[(pm_["target"] == "ordering") & (pm_["algorithm"] == "gradient_boosting") & (pm_["from_tier"] == "tier1") & (pm_["to_tier"] == "tier2") & (pm_["metric"] == "macro_f1")].iloc[0]
    og = om[(om["algorithm"] == "gradient_boosting") & (om["from_variant"] == "tier1") & (om["to_variant"] == "tier2")].iloc[0]
    rows.append(("Tier 1 -> Tier 2, matched ordering (Gradient Boosting)",
                 f"{pg['improvement']:+.3f} [{pg['improvement_ci_low']:+.3f}, {pg['improvement_ci_high']:+.3f}] 'stable improvement' on ONE frozen split (13,914 rows, 56% default-FM JARVIS)",
                 f"{og['pooled_improvement']:+.3f} [{og['pooled_ci_low']:+.3f}, {og['pooled_ci_high']:+.3f}] over {int(og['n_splits'])} repeated splits on the repaired 6,061-row population; positive in {int(og['n_positive'])}/{int(og['n_splits'])} splits",
                 "NOT REPLICATED: the Phase 6 'stable improvement' was a single-split result; withdrawn", "ordering_v13_matched_robustness.csv"))
    ot3 = om[(om["from_variant"] == "tier1") & (om["to_variant"] == "tier3")].set_index("algorithm")
    rows.append(("Tier 3 physics, matched ordering", "no stable benefit (single frozen split)",
                 "; ".join(f"{ALG[a]} {ot3.loc[a,'pooled_improvement']:+.3f} [{ot3.loc[a,'pooled_ci_low']:+.3f}, {ot3.loc[a,'pooled_ci_high']:+.3f}]" for a in ALG)
                 + f" over {int(ot3['n_splits'].iloc[0])} repeated splits; no algorithm stable",
                 "CONFIRMED on the repaired target (5 splits, fewer than the 10 used for Curie and Ms)", "ordering_v13_matched_robustness.csv"))
    return rows


def tier3_rows(d: dict) -> list[tuple]:
    cr, mr = d["curie_robust"], d["ms_robust"]
    cp = lambda a, m: cr[(cr["analysis"] == "primary_matched") & (cr["algorithm"] == a) & (cr["from_variant"] == "tier1") & (cr["to_variant"] == "tier3") & (cr["metric"] == m)].iloc[0]   # noqa: E731
    mp = {a: mr[(mr["target"] == "ms_moment") & (mr["analysis"] == "primary_matched") & (mr["algorithm"] == a) & (mr["from_variant"] == "tier1") & (mr["to_variant"] == "tier3") & (mr["metric"] == "mae")].iloc[0] for a in ALG}
    fmt = lambda a: (f"{ALG[a]} {cp(a,'mae')['pooled_mean_improvement']:+.1f} K [{cp(a,'mae')['pooled_mean_ci_low']:+.1f}, {cp(a,'mae')['pooled_mean_ci_high']:+.1f}] "   # noqa: E731
                     f"(formula-weighted {cp(a,'mae_formula_macro')['pooled_mean_improvement']:+.1f} [{cp(a,'mae_formula_macro')['pooled_mean_ci_low']:+.1f}, {cp(a,'mae_formula_macro')['pooled_mean_ci_high']:+.1f}])")
    return [("Tier 3 physics, matched Curie (4,602 rows)", "no stable benefit (frozen split: XGBoost +66 K); Ridge unstable", "; ".join(fmt(a) for a in ALG),
             "CONFIRMED: no benefit; formula-weighted MAE shows a small stable degradation for XGBoost (and for Ridge, driven by numerically exploded fits) on the curated target", "phase7_robustness_summary.csv (v1.3)"),
            ("Tier 3 physics, Ms per cell", "'stable improvement for 3 of 3 algorithms' (0.08-0.10 muB/cell, frozen split)",
             "; ".join(f"{ALG[a]} {mp[a]['pooled_mean_improvement']:+.3f} [{mp[a]['pooled_mean_ci_low']:+.3f}, {mp[a]['pooled_mean_ci_high']:+.3f}]" for a in ALG)
             + " over 10 repeated splits. Prespecified criterion (stable for every algorithm) NOT met: Ridge and Gradient Boosting satisfy it, XGBoost does not",
             "REVISED: small (about 2-4% of MAE), algorithm-dependent, explained by unit-cell size for the tree models (Tier 2 + MP-cell site count recovers it)",
             "10_phase7_validation/v1.2"),
            ] + stage56_rows(d) + [
            ("Ms and K1 / Ms-mass / Ms-volume analyses (Stage 7, repeated formula-grouped CV, Tier 1)", "computed on the v1.2 targets: K1 raw R2 0.13-0.18 (intervals include 0), Ms-volume R2 0.44-0.46, Ms-mass R2 0.63",
             "after R10 screens (v1.4: 15 K1, 9 Ms-volume, 1 Ms-mass rows removed): K1 raw R2 0.38 [0.22, 0.51] (GB) / 0.36 [0.20, 0.48] (XGB); K1 signed-log10 R2 0.17 (no gain); Ms-volume R2 0.57 (GB, XGB); Ms-mass R2 0.62 (unchanged). Linear models still fail on K1 and Ms-volume. Ms-per-cell moment renamed 'DFT total magnetic moment per unit cell (0 K)'; MP total_magnetization verified per cell, Phase 3 label muB/f.u. is wrong",
             "REVISED: raw-K1 and Ms-volume skill was depressed by impossible values (cleaning, not a better model); log-K1 and Ms-mass unchanged; targets are different populations so v1.2 and v1.4 are not row-matched", "08_secondary/v1.4/R10_SUMMARY.md")]


def n_stable(df: pd.DataFrame, alg: str, verdict: str) -> int:
    return int(((df["algorithm"] == alg) & (df["verdict"] == verdict)).sum())


def stage56_rows(d: dict) -> list[tuple]:
    dl = d["s5_deltas"]
    prim = dl[dl["metric"].isin(["macro_f1", "mae"])]
    px = prim[prim["algorithm"] == REF].set_index(["target", "group"])
    gain = px[px["verdict"] == "stable improvement"]
    loss = px[px["verdict"] == "stable degradation"]
    mult, gaps = d["s5_mult"], d["s5_gaps"]
    gx = gaps[(gaps["algorithm"] == REF) & gaps["metric"].isin(["macro_f1", "mae"])]
    fam = gx[~gx["group"].isin(["Experimental", "Computational"])]
    label = lambda df, v: "; ".join(f"{t}/{g}" for (t, g) in zip(df[df['verdict'] == v]['target'], df[df['verdict'] == v]['group'])) or "none"   # noqa: E731
    per_alg = "; ".join(f"{ALG[a]}: {n_stable(prim, a, 'stable improvement')} stable gains, {n_stable(prim, a, 'stable degradation')} stable losses of {int((prim['algorithm'] == a).sum())}" for a in ALG)
    gain_txt = "; ".join(f"{t}/{g} {r['improvement']:+.4g} [{r['improvement_ci_low']:+.4g}, {r['improvement_ci_high']:+.4g}]" for (t, g), r in gain.iterrows()) or "none"
    s6, abl = d["s6_cmp"].set_index("target"), d["s6_abl"]
    abl_pk = abl[((abl["target"] == "ordering") & (abl["metric"] == "macro_f1")) | ((abl["target"] == "curie") & (abl["metric"] == "mae"))]
    pick = lambda t, kind: abl_pk[(abl_pk["target"] == t) & (abl_pk["analysis"] == kind) & (abl_pk["verdict"] != "no stable contribution")]   # noqa: E731
    fmt_abl = lambda df: "; ".join(f"{r.physics_family} {r.value_gained_by_family:+.3g} [{r.ci_low:+.3g}, {r.ci_high:+.3g}] ({r.verdict})" for r in df.itertuples()) or "none"   # noqa: E731
    return [
        ("Material families (Stage 5), ordering and Curie: family-specific vs general model",
         "XGBoost: stable gains only Curie/Intermetallic (+6.2 K) and Ms/Intermetallic; stable losses ordering/Transition Metal and Ms/Rare Earth",
         f"XGBoost (strongest algorithm): stable gains {gain_txt}; stable losses {', '.join(f'{t}/{g}' for (t, g) in loss.index) or 'none'}. All algorithms: {per_alg}. "
         f"Multiplicity ({len(mult)} comparisons, primary metric, ordering+Curie): {int(mult['stable_unadjusted'].sum())} stable unadjusted, {int(mult['stable_after_holm_005'].sum())} after Holm, {int(mult['stable_after_bh_005'].sum())} after BH",
         "CONFIRMED for the strongest algorithm (family-specific models rarely help; Curie/Intermetallic is the one stable gain); the extra stable gains are for weaker models (mostly Ridge/logistic) and are not evidence of family structure; the v1.2 ordering/Transition Metal degradation did not recur",
         "stage5_families/ (v1.3)"),
        ("Material families (Stage 5): general model on a family vs the rest",
         "worse on Oxide (ordering F1 0.666 vs 0.739), Transition Metal and Oxide (Ms)",
         f"ordering/Curie, XGBoost: worse on family: {label(fam, 'worse on family')}; better on family: {label(fam, 'better on family')}",
         "CONFIRMED for ordering/Oxide; NEW pattern for Curie (worse on Transition Metal and Intermetallic, better on Rare Earth and Oxide)", "stage5_families/family_vs_rest_gap.csv"),
        ("Interpretation (Stage 6 SHAP and physics-family ablation), ordering and Curie",
         "ordering: p3_point_group, magnetic_element_fraction lead; physics share 41%. Curie: p3_point_group, p3_volume lead; physics share 49%; stable add-one gains Electronic +17.5 K, Symmetry +57.8 K",
         f"ordering: top-5 overlap with v1.2 {int(s6.loc['ordering','top5_overlap'])}/5, physics SHAP share {100 * s6.loc['ordering','physics_shap_share_v13']:.0f}%; stable family cells: add-one {fmt_abl(pick('ordering', 'add_one_to_tier2'))}; drop-one {fmt_abl(pick('ordering', 'drop_one_from_tier3'))}. "
         f"Curie: top-5 overlap {int(s6.loc['curie','top5_overlap'])}/5 (now {s6.loc['curie','tier3_top5_v13']}), physics SHAP share {100 * s6.loc['curie','physics_shap_share_v13']:.0f}%; stable family cells: add-one {fmt_abl(pick('curie', 'add_one_to_tier2'))}; drop-one {fmt_abl(pick('curie', 'drop_one_from_tier3'))}",
         "ORDERING: interpretation largely unchanged and no family carries a tier gain. CURIE: attribution changed (do not reuse the v1.2 Curie SHAP or ablation statements); the add-one cells are exploratory and conflict with the null tier-level result; p3_piezo_max (91.6% missing in the v1.3 matched Curie set) ranks 4th and is probably a missingness proxy",
         "stage6_shap/ (v1.3)")]


def phase8_rows() -> list[tuple]:
    """Phase 8 (uncertainty, explanation stability, bias) rows; values copied from 11_phase8_xai_uq/ and 12_phase8_bias/ outputs."""
    nr = "not examined before Phase 8"
    return [
        ("Phase 8 UQ, Curie prediction intervals (90% nominal, v1.3, test N=4,541)", nr,
         "split conformal 95.1% [93.9, 96.1] (width 552 K); normalized conformal 91.7% [90.4, 92.9] (366 K); CQR 92.5% (438 K). Constant-width intervals cover the hardest difficulty decile at 79%. Calibrating on curated and testing on text-mined rows: split -13 points (76.9%), CQR 80.3%, normalized 85.1%",
         "NEW: only normalized conformal is within the prespecified +-2 points on the frozen split, and that is not reproducible split-to-split: over 10 repeated splits marginal coverage is 89.3% (SD 6.0, split), 90.3% (SD 2.5, normalized), 89.4% (SD 5.8, CQR), within +-2 points in 1/5/0 of 10 splits; hardest decile, high-Tc and text-mined rows are systematically under-covered; coverage is not guaranteed under label-source shift", "11_phase8_xai_uq/curie/uq_summary.csv; uq_source_shift.csv"),
        ("Phase 8 UQ, Ms per cell prediction intervals (90% nominal, test N=13,129)", nr,
         "split 90.4%, normalized 90.3%, CQR 89.4% marginally; split conformal under-covers hardest decile (49%), highest-moment third (74%) and Oxides (84.8%). CQR calibrated on JARVIS and tested on MP covers 35%: 37.8% of MP rows have moment exactly 0 and a negative CQR correction excludes them",
         "NEW: marginal coverage hides subgroup failures (CONFIRMED over 10 repeated splits: marginal 90.0-90.1% in 10/10 splits for all methods; split conformal Oxide 84.0%, hardest decile 49.7%; CQR flagged on hardest decile and high-moment third in 10/10 splits; normalized never flagged); CQR is fragile at a point mass at zero", "11_phase8_xai_uq/ms_moment/uq_summary.csv; uq_coverage_by_group.csv; uq_source_shift.csv"),
        ("Phase 8 UQ, ordering probabilities and prediction sets (test N=11,902)", nr,
         "ECE raw 0.058 [0.051, 0.068]; prior-corrected 0.093; prior-corrected + temperature (T=1.65) 0.016 [0.012, 0.027]. Marginal conformal sets 89.3% overall but AFM 58% and FiM 53%; class-conditional sets 89-92% per class (mean size 1.58). MP-calibrated sets tested on experimental rows: marginal 83.5%",
         "NEW: probabilities usable only after prior correction + temperature scaling; use class-conditional sets for AFM/FiM (CONFIRMED over 10 repeated splits: class-conditional per-class coverage 89.9-91.1%, marginal sets AFM 57.2% and FiM 54.8% at 90.0% overall)", "11_phase8_xai_uq/ordering/uq_calibration_metrics.csv; uq_conformal_sets.csv; uq_source_shift.csv"),
        ("Phase 8 explanation stability (TreeSHAP over 10 splits)", "Stage 6 SHAP rankings from one frozen split",
         "ordering and Ms: mean pairwise Spearman >= 0.95, magnetic_element_fraction top feature in 10/10 splits (Ms Tier 3: 9/10). Curie: Spearman 0.83-0.94, top-1 feature changes between splits (group_variance 5/10), Tier 3 family shares vary by about +-8 points (Atomic-size 23%, Magnetic-element 20%). Ordering splits use the Phase 7 seeds with class-code stratification (extension)",
         "REVISED for Curie: only family-level statements with intervals are supportable, not single-feature rankings; ordering and Ms rankings CONFIRMED stable", "11_phase8_xai_uq/xai_stability/"),
        ("Phase 8 bias audit and reduction (ordering, Curie; single frozen split)", nr,
         "material gaps: AFM recall 0.60 and FiM 0.51 (FM 0.79, NM 0.91); Curie text-mined MAE 105 K vs curated 64 K; high-Tc third 100 K vs 76 K overall. Formula dominance not material. AFM recall gain, single split: provenance weights +4.9 points, class offsets +5.1 (FiM -1.9), weights + offsets +11.2. Over 10 repeated splits only provenance weights are stable: AFM +4.3 [3.2, 5.3] points, positive in 10/10 splits, at FM -1.0 and NM -0.7 recall; class offsets borderline (+2.7 [0.1, 5.3], 7/10 splits, NM -2.2); weights + offsets NOT stable (+2.9 [-2.2, 8.1]). Reweighting leaves the Curie gaps unchanged (all intervals include 0)",
         "NEW: AFM recall gap narrowed by about 4 points with provenance weights (stable over 10 splits); the single-split +11 points did not replicate; FiM gap and Curie text-mined/high-Tc gaps NOT narrowed (label-side); no claim that bias is removed", "12_phase8_bias/BIAS_SUMMARY.md"),
    ]


def leave_chemsys_row() -> tuple:
    return ("Phase 8 leave-chemical-system-out generalisation (Tier 1 XGBoost, 10 paired splits)", "formula-grouped splits only (65-78% of test rows share a chemical system with training)",
            "ordering macro-F1 0.712 -> 0.684 (-0.029 [-0.041, -0.017], worse in 10/10 splits; FiM recall -0.061 [-0.085, -0.036]); Ms MAE 2.591 -> 2.663 (+0.073 [-0.009, +0.154], 7/10 worse); Curie MAE 99.2 -> 101.9 K (+2.7 [-16.8, +22.2], 5/10 worse)",
            "NEW: ordering skill stably degrades for unseen chemical systems; Ms degradation small and not stable; Curie test too noisy to conclude", "13_phase8_leave_chemsys/LEAVE_CHEMSYS_SUMMARY.md")


def followup_rows() -> list[tuple]:
    return [
        ("Ms per cell, site-count control on all 10 splits", "site-count control run on splits 0-4 only",
         "Tier 1 -> Tier 2 + site count: Ridge +0.028 [0.007, 0.050], Gradient Boosting +0.055 [0.031, 0.080], XGBoost +0.051 [0.025, 0.076] (all stable); what Tier 3 adds beyond site count: Ridge +0.027 [-0.025, 0.065], GB +0.024 [-0.003, 0.050], XGB -0.014 [-0.045, 0.018] (none stable)",
         "CONFIRMED on all 10 splits: for the per-cell target the Tier 3 gain is recovered by cell size", "10_phase7_validation/v1.2/phase8_sitecount_control_10splits_robustness.csv"),
        ("Ms per atom (moment / sites) target, Tier 1 -> Tier 3", "not examined",
         "relative MAE gain GB +14.1% [12.6, 15.6], XGBoost +9.0% [6.7, 11.3], Ridge +6.1% [5.0, 7.2], stable in 10/10 splits (per-cell: +4.0%, +1.9% not stable, +2.4%). Attribution: volume family (volume, density, volume per atom) carries GB +11.7% / XGB +10.2% / Ridge +4.1% of the gain; symmetry +1-3.5%; same-calculation outputs +1.5-2%; elastic/dielectric none",
         "NEW: removing cell size does not remove the Tier 3 gain; it is carried by volume per atom / density (packing), not by electronic or elastic outputs; 'cell size explains it' holds for the per-cell target only. The descriptors need a relaxed DFT structure", "14_phase8_peratom/"),
        ("Curie, C5 sensitivity (AFM-only formulas kept, N=30,059)", "primary target excludes AFM-only formulas (rule C5)",
         "Tier 1 test MAE GB 81.2 K, XGB 72.7 K, R2 0.77-0.79 (primary 76.2 / 75.4 K, 0.78); C5-only test rows (42 rows) error 54.8-72.1 K vs 72.9-81.3 K others; Tier 1 -> Tier 2: GB -0.7 K [-3.2, +1.8], XGB -3.9 K [-8.8, +0.4], no stable change",
         "Curie baselines ROBUST to rule C5; the Tier 2 'stable degradation' for Curie is NOT robust (same direction, intervals include 0)", "10_phase7_validation/v1.3/c5_sensitivity/"),
    ]


def rows_for(d: dict) -> list[dict]:
    rows = ordering_rows(d) + curie_ms_rows(d) + tier_rows(d) + tier3_rows(d) + phase8_rows() + [leave_chemsys_row()] + followup_rows()
    return [dict(zip(["claim", "phase6_or_v12", "v13", "status", "source"], r)) for r in rows]


def register_markdown(d: dict) -> str:
    m = d["manifest"]
    head = ("# Superseding claims register (Phase 6 + Phase 7) — written after the Phase 7 review\n\n"
            "Replaces the headline claims of `09_final_tables_figures/phase6_final_summary.txt` wherever they differ. Phase 6 files are not edited.\n"
            f"Dataset v1.3 (rules `00_config/v1_3_curation_rules.yaml`): Curie {m['curie']['v1_2_n']:,} -> {m['curie']['v1_3_primary_n']:,} rows; "
            f"ordering {m['ordering']['v1_2_n']:,} -> {m['ordering']['v1_3_n']:,} rows. All v1.3 comparisons use identical rows, splits, grids and metrics at every tier.\n\n"
            "Reading rule: where this register and a Phase 6 file disagree, this register applies. Headline models are not chosen on the test set here: "
            "all algorithms are shown, or the validation-selected one is named.\n\n")
    body = "| Claim | Phase 6 / v1.2 | v1.3 / Phase 7 | Status | Source |\n|---|---|---|---|---|\n"
    for r in rows_for(d):
        body += f"| {r['claim']} | {r['phase6_or_v12']} | {r['v13']} | **{r['status']}** | `{r['source']}` |\n"
    return head + body + ("\nAll single-split Phase 6 intervals are conditional on one frozen training run (the Ms gain on that split, 0.08-0.10, was larger than across "
                          "10 repeated splits, 0.04-0.08).\n")


def per_rule_text(m: dict) -> str:
    return "; ".join(f"{k.split('_')[0]} {v['rows']:,}" for k, v in m["curie"]["per_rule"].items()) + " rows flagged per rule (rules overlap)"


def response_markdown(d: dict) -> str:
    m = d["manifest"]
    return f"""# Response to the Phase 7 review — blocking items R1–R4

Decision under review: major revision (`10_phase7_validation/v1.2/review/editorial_decision.md`). Dataset v1.3 and every v1.3 result leave v1.2 untouched.

## R1 — Curie target (the domain reviewer's D2 block)
- **Action:** prespecified screen, written before any model was fit on the curated target (`00_config/v1_3_curation_rules.yaml`): no magnetism-capable element (C1), non-magnetic elemental formula (C2), TC < 1 K (C3), TC > 1,400 K (C4), formula whose every ordering label is AFM (C5). Rows removed: {m['curie']['removed_primary']:,} ({100 * m['curie']['removed_primary'] / m['curie']['v1_2_n']:.1f}%); {per_rule_text(m)}. Quarantined with reason codes in `datasets/v1.3/excluded/R1_curie_quarantine.csv`.
- **Why those rows are not magnetic Curie temperatures:** text-mined entries such as elemental Ti 0.39 K, Pb, Al, Si, MgB2 (superconducting Tc), BaTiO3, PbTiO3, LiNbO3 (ferroelectric Curie points), and values above the highest known ferromagnetic Curie temperature (Co, about 1,388 K).
- **Known losses (documented):** Ti3+ ferromagnets (YTiO3); elemental Co values just above 1,400 K; multiferroics keep a Curie/Neel ambiguity; rule C5 depends on ordering labels that can themselves be wrong (a sensitivity target without C5 was built, `targets/curie/target_curie_sensitivity_without_C5.csv`, but not yet run).
- **Re-run:** full-population Tier 1 and Tier 2, and the matched Tier 1/2/3 experiment on 10 repeated splits (4,602 matched rows). Results are in `claims_register.md`.
- **Still open:** the secondary targets (Ms-volume, Ms-mass, K1 impossible values; roadmap R10) were not touched.

## R2 — Ordering target
- **Action:** the JARVIS collector hard-codes `Ferromagnetic` for every entry (`scripts/collect_jarvis_magnetic.py::infer_magnetic_type`), so all {m['ordering']['removed']:,} JARVIS rows ({100 * m['ordering']['removed'] / m['ordering']['v1_2_n']:.0f}% of the ordering target; 56% of the matched ordering set) were removed from the ordering target (`datasets/v1.3/excluded/R2_ordering_jarvis_default_fm_quarantine.csv`). They stay in the repository and in all other targets.
- **Provenance analyses added:** per-slice models and cross-provenance transfer with formula overlap removed. Finding: ordering skill does not transfer between computed and experimental labels.
- **Leakage audit extended to ordering:** matched Tier 1/2/3 plus 'same-calculation' and symmetry variants on 5 repeated splits (`ordering_v13_matched_*.csv`): no stable tier benefit; isolated cells among 21 unadjusted comparisons are treated as noise.
- **Limits:** 5 repeated splits (not 10) for the matched ordering experiment because of compute time; MP's own ordering was not substituted for the removed JARVIS labels.

## R3 — Phase 6 / Phase 7 reconciliation
- `claims_register.md` supersedes the Phase 6 headline claims; each row states the Phase 6 value, the v1.3 value, a status and the source file. Headline models are no longer chosen on the test set. The one-frozen-split caveat is stated. Stage 5 (families) and Stage 6 (SHAP and physics-family ablation) were re-run on v1.3 for ordering and Curie (`stage5_families/`, `stage6_shap/`); Ms rows are unchanged. Family results confirm the earlier picture for the strongest algorithm; the Curie interpretation changed and the v1.2 Curie SHAP statements must not be reused.

## R4 — Prespecified Ms gate
- The prespecified criterion (pooled CI excludes 0 and at least 70% of splits positive, for every algorithm) is **not met**: XGBoost's interval touches 0. The decision-gate table now reports it as not met; '2 of 3 algorithms' is described as a descriptive post-hoc count. The earlier wording 'stable by the prespecified rule for 2 of 3' was wrong and has been replaced.
"""


def main() -> None:
    out13 = p7.output_dir(p7.load_phase7_config(), "v1.3")
    d = load(out13)
    (out13 / "claims_register.md").write_text(register_markdown(d), encoding="utf-8")
    (out13 / "revision_response.md").write_text(response_markdown(d), encoding="utf-8")
    pd.DataFrame(rows_for(d)).to_csv(out13 / "claims_register.csv", index=False, encoding="utf-8")
    print(register_markdown(d))


if __name__ == "__main__":
    main()
