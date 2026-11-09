"""Phase 7: build phase7_validation_summary.docx (plain white document) from the saved Phase 7 CSVs and figures.

Run from EDA/src after phase7_run_report.py:  python phase7_summary_doc.py
"""
from __future__ import annotations

import pandas as pd
from docx import Document
from docx.shared import Inches, Pt

import phase7_revision as rev
import phase7_run_report as rep
import phase7_validation as p7

ALG = {"linear": "Linear / Ridge", "gradient_boosting": "Gradient Boosting", "xgboost": "XGBoost"}
TABLE_WIDTHS = [1.2, 1.1, 1.1, 1.4, 0.7, 0.7, 0.9]


def add_table(doc: Document, header: list[str], rows: list[list[str]], widths: list[float] | None = None) -> None:
    table = doc.add_table(rows=1, cols=len(header))
    table.style = "Table Grid"
    for i, h in enumerate(header):
        cell = table.rows[0].cells[i]
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        run.bold = True
        run.font.size = Pt(8.5)
    for row in rows:
        cells = table.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            cells[i].paragraphs[0].add_run(str(v)).font.size = Pt(8.5)
    if widths:
        for row in table.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph()


def bullets(doc: Document, items: list[str]) -> None:
    for text in items:
        doc.add_paragraph(text, style="List Bullet")


def interval(r: pd.Series, d: int) -> str:
    return f"{r['pooled_mean_improvement']:+.{d}f} [{r['pooled_mean_ci_low']:+.{d}f}, {r['pooled_mean_ci_high']:+.{d}f}]"


def tier_table(robust: pd.DataFrame, target: str, d: int) -> tuple[list[str], list[list[str]]]:
    header = ["Algorithm", "Tier 1→2 gain", "Tier 2→3 gain", "Tier 1→3 gain", "% of Tier 1 MAE", "Splits improving", "Verdict"]
    rows = []
    for alg in rep.ALGS:
        a, b, c = (rep.pooled(robust, target, "primary_matched", alg, f, t) for f, t in (("tier1", "tier2"), ("tier2", "tier3"), ("tier1", "tier3")))
        rows.append([ALG[alg], interval(a, d), interval(b, d), interval(c, d), f"{c['pooled_mean_pct_of_from']:+.1f}%",
                     f"{int(c['n_positive'])}/{int(c['n_splits'])}", c["robust_verdict"]])
    return header, rows


def ms_gain_text(alg: str, robust: pd.DataFrame) -> str:
    r = rep.pooled(robust, "ms_moment", "primary_matched", alg, "tier1", "tier3")
    return f"{ALG[alg]} {interval(r, 3)} μB/cell ({int(r['n_positive'])}/10 splits)"


def sens_text(robust: pd.DataFrame, v_from: str, v_to: str, with_ci: bool = True) -> str:
    parts = []
    for a in rep.ALGS:
        r = rep.pooled(robust, "ms_moment", rep.SENS, a, v_from, v_to)
        parts.append(f"{ALG[a]} {interval(r, 3) if with_ci else format(r['pooled_mean_improvement'], '+.3f')}")
    return ", ".join(parts)


def overview(doc: Document, robust: pd.DataFrame) -> None:
    doc.add_heading("1. Bottom line", 1)
    bullets(doc, [
        "Reproducible: 51 of 51 reconciliation checks pass, and the Phase 7 pipeline reproduces all 18 Stage 4 prediction sets on the frozen split exactly (max difference 6e-14).",
        "Ms per unit cell: the Tier 3 gain keeps its direction (positive in 8–10 of 10 repeated splits for every algorithm) but is small — "
        + "; ".join(ms_gain_text(a, robust) for a in rep.ALGS) + ". The PRESPECIFIED criterion (stable for every algorithm) is NOT met: "
        "Ridge and Gradient Boosting satisfy it, XGBoost does not (its interval touches 0). '2 of 3' is a descriptive count, not the prespecified rule.",
        "That gain is a cell-size effect, not a general physics effect: adding one number (the site count of the Materials Project cell, volume / volume-per-atom) to Tier 2 recovers it for the tree models; "
        "the remaining physics columns add nothing demonstrable beyond it for Gradient Boosting and XGBoost.",
        "Curie temperature: the null finding holds across 10 splits and every extreme-value sensitivity. Split-to-split variation (MAE 131–374 K for one model) is larger than any tier difference; the frozen split was one of the harder ones.",
        "The unstable Ridge Tier 3 estimates are caused by non-physical input values in a few formulas (p3_elastic_anisotropy = −5.5e23 for SmNi5; p3_bulk_modulus = 1.4e6 GPa for BaRuO3), not by collinearity; clipping inputs to training percentiles removes the failure.",
        "Decision gate: criteria (i) and (iii) met; (ii) NOT met (the prespecified every-algorithm rule fails for XGBoost; an earlier version of this summary wrongly reported it as met); (iv) NOT a clean pass because of the cell-size finding. The smallest corrective experiment was run and the claim is narrowed (section 8). The package is returned for scientific review before manuscript drafting.",
    ])


def revision_section(doc: Document) -> None:
    """Section 1a: what changed after the simulated peer review (dataset v1.3), generated from the v1.3 result CSVs."""
    out13 = p7.output_dir(p7.load_phase7_config(), "v1.3")
    d = rev.load(out13)
    m = d["manifest"]
    split = {r["file"]: r for r in m["split_derivation"]}
    doc.add_heading("1a. Revision after review: dataset v1.3 (blocking items R1–R4)", 1)
    doc.add_paragraph(
        "The simulated peer review (five reviewers; editorial decision: major revision) blocked on four items. They were addressed in a new dataset version, "
        "v1.3, built from prespecified rules (00_config/v1_3_curation_rules.yaml) and applied only by removing rows into quarantine files. v1.2 and all Phase 6 "
        "results are unchanged. Full detail: 10_phase7_validation/v1.3/revision_response.md; the claims register (claims_register.md) supersedes the Phase 6 headline claims.")
    rows = [["Curie target", f"{m['curie']['v1_2_n']:,}", f"{m['curie']['v1_3_primary_n']:,}", "superconducting / ferroelectric / Neel / out-of-range values (rules C1–C5)"],
            ["Curie, Tier 3 matched set", f"{split['matched_split_curie.csv']['n_previous']:,}", f"{split['matched_split_curie.csv']['n_kept']:,}", "same rules"],
            ["Ordering target", f"{m['ordering']['v1_2_n']:,}", f"{m['ordering']['v1_3_n']:,}", "JARVIS collector hard-codes 'Ferromagnetic' (rule O1)"],
            ["Ordering, Tier 3 matched set", f"{split['matched_split_ordering.csv']['n_previous']:,}", f"{split['matched_split_ordering.csv']['n_kept']:,}", "56% of the old matched set was default-labelled"]]
    add_table(doc, ["Population", "v1.2 N", "v1.3 N", "Reason"], rows, [1.7, 0.8, 0.8, 3.5])
    claims = rev.rows_for(d)
    add_table(doc, ["Claim", "Phase 6 / v1.2", "v1.3 / Phase 7", "Status"], [[c["claim"], c["phase6_or_v12"], c["v13"], c["status"]] for c in claims], [1.2, 1.9, 2.4, 1.3])
    bullets(doc, [
        "R1 (Curie): after the screen the target is easier and the Phase 6 'Curie MAE 94.5 K' described a mixed target; Tier 2 and Tier 3 conclusions are unchanged (no benefit).",
        "R2 (ordering): the headline macro-F1 survives the repair but does not transfer across label provenance (about chance in both directions), so it must not be read as general capability; the Phase 6 matched-ordering Tier 2 'stable improvement' was not replicated.",
        "R3 (reconciliation): one superseding claims register; headline models are no longer selected on the test set. Stage 5 (families) and Stage 6 (SHAP, physics-family ablation) were re-run on v1.3 for ordering and Curie: family-specific models still rarely beat the general model for the strongest algorithm (one stable gain, Curie/Intermetallic +9.7 K; 24 comparisons, 5 stable after Holm), and the ordering interpretation is largely unchanged, but the Curie interpretation changed (top-5 descriptor overlap 1/5, physics SHAP share 49%→36%) so the v1.2 Curie SHAP and ablation statements must not be reused.",
        "R4 (gate): the prespecified Ms criterion is not met and the gate table now says so; the earlier 'met' was an error in this summary.",
        "Limits of this revision: matched ordering used 5 repeated splits (not 10); Stage 5/6 hyperparameters were re-selected on one frozen split, so those results are single-split; the Curie sensitivity target without rule C5 was built but not run; secondary-target cleaning (roadmap R10), the all-10-split site-count control, a leave-chemical-system-out test and the per-atom Ms target remain open.",
    ])


def methods(doc: Document) -> None:
    doc.add_heading("2. Methods (what was run)", 1)
    bullets(doc, [
        "Fixed foundations untouched: the v1.2 dataset, harmonised targets, predictor lists, frozen splits and all Phase 6 outputs were read, never written. Settings were prespecified in EDA/00_config/phase7_config.yaml before any Phase 7 fit.",
        "Populations: the Stage 4 matched sets — Curie N = 5,490 (559 formulas; almost entirely experimental) and Ms per cell N = 10,852 (4,849 formulas; entirely computational, JARVIS 72% and Materials Project 28%). Identical material IDs, splits, metrics and tuning grids at every tier.",
        "Splits: 10 prespecified, seeded, formula-grouped, target-stratified 70/15/15 splits per target (seeds 20267000–20267009); no formula appears in two partitions; test-set formula overlap between two splits is about 9%. The frozen Phase 6 split was re-run as a reproduction reference and excluded from pooled statistics.",
        "Models: the original three families (Ridge, histogram Gradient Boosting, XGBoost) with the Phase 6 grids; hyper-parameters chosen on validation, refit on train+validation, scored once on test; all preprocessing fitted inside the training fold.",
        "Statistics: paired formula-grouped bootstrap (1,000 resamples; identical draws on both sides of each comparison) per split; pooled over splits as the mean of per-split metrics and as concatenated test predictions; across-split sign counts. Gain means lower error (positive is better).",
        "XGBoost was pinned to 16 threads: its output depends on thread count (frozen-split Curie Tier 1 MAE 274.6 / 284.9 / 273.9 K with 1 / 4 / 16 threads), and 16 threads reproduces Phase 6 exactly.",
    ])


def curie_section(doc: Document, robust: pd.DataFrame, out) -> None:
    doc.add_heading("3. A — Curie temperature: stability of the matched experiment", 1)
    header, rows = tier_table(robust, "curie", 1)
    add_table(doc, header, rows, TABLE_WIDTHS)
    doc.add_paragraph("MAE gain in K, pooled over 10 splits with 95% formula-bootstrap intervals. The Ridge row is dominated by exploded fits (below); its median per-split gain is in the CSV.")
    expl = pd.read_csv(out / "phase7_curie_linear_explosion_rows.csv").drop_duplicates(["split_id", "reduced_formula"])
    inst = pd.read_csv(out / "phase7_curie_linear_instability.csv")
    clip = inst[(inst["variant"] == "tier3") & (inst["algorithm"] == "linear_clip") & inst["split_id"].isin(expl["split_id"].astype(str))]
    plain = inst[(inst["variant"] == "tier3") & (inst["algorithm"] == "linear") & inst["split_id"].isin(expl["split_id"].astype(str))]
    bullets(doc, [
        "No algorithm shows a stable Tier 1→Tier 3 change. The only stable Curie result is a Tier 1→Tier 2 degradation for Gradient Boosting (−16.9 K; 0 of 10 splits improving), replicating Stage 3.",
        "Heterogeneity: with only 559 formulas, a test partition holds 58–131 distinct formulas and in one split a single formula supplies 39% of the test rows. XGBoost Tier 1 test MAE spans 131–374 K and R² −1.07 to +0.69 across splits. On the frozen split XGBoost Tier 3 had a 66 K lower MAE than Tier 1; most random splits do not reproduce that.",
        "Extreme values (labelled sensitivity; primary target unchanged): re-scoring without TC > 1,400 K test rows and refitting without TC > 1,400 K observations both leave the conclusion unchanged. Weighting every formula equally (formula-macro MAE) turns the small row-weighted XGBoost 'gain' (+17.6 K) into a loss (−8.2 K, interval −17.0 to +1.5): any apparent gain sits on heavily repeated formulas such as Fe, Mn, Co, Ni and BaTiO3.",
        f"Ridge diagnosis: Tier 3 Ridge predictions exploded in {expl['split_id'].nunique()} of 11 fits. Every exploded row traces to one formula with a non-physical Materials Project value ("
        + "; ".join(f"{r.reduced_formula}, split {r.split_id}: {r.top1_feature} = {r.top1_raw_value:.3g}" for r in expl.itertuples())
        + "). With inputs clipped to training-fold 1st–99th percentiles the same fits give MAE "
        + ", ".join(f"{c:.0f} K (was {p:,.0f} K)" for c, p in zip(clip["mae"], plain["mae"]))
        + ". Boosters are unaffected. Stage 4's explanation (collinearity, 'not a data bug') should be corrected.",
    ])
    doc.add_picture(str(out / "figures" / "phase7_fig_curie_tier_performance_by_split.png"), width=Inches(6.4))


def ms_section(doc: Document, robust: pd.DataFrame, out) -> None:
    doc.add_heading("4. B — Ms per unit cell: robustness of the main positive result", 1)
    header, rows = tier_table(robust, "ms_moment", 3)
    add_table(doc, header, rows, TABLE_WIDTHS)
    doc.add_paragraph("MAE gain in μB/cell, pooled over 10 splits. Distinct formulas per split: train 3,359–3,424, validation 709–754, test 701–759. The target is computational; this is not an experimental validation.")
    bullets(doc, [
        "Stage 4 reported 0.08–0.10 μB/cell. Across 10 repeated splits (test sets overlap by about 9%) the gain is 0.04–0.08 μB/cell (1.8–4.0% of MAE): the same sign, a smaller size, and the frozen split was a favourable one.",
        "Tier 2 adds nothing for Ms (all three intervals include 0), consistent with Stage 3. Ridge did not explode on Ms (largest |prediction| 175 μB/cell).",
    ])
    doc.add_picture(str(out / "figures" / "phase7_fig_ms_paired_tier1_to_tier3.png"), width=Inches(6.4))


def audit_section(doc: Document, robust: pd.DataFrame, audit: pd.DataFrame, out) -> None:
    doc.add_heading("5. C — Tier 3 feature validity and leakage audit", 1)
    doc.add_paragraph("Per-feature table: phase7_tier3_feature_audit.csv (definition, calculation stage, prediction-time requirement, missingness, uniqueness, provenance, univariate predictive power, risk class, sensitivity evidence, judgment, decision).")
    bullets(doc, [
        "Held-out magnetic outputs stay excluded: none of the 97 Tier 3 predictors is a magnetic output (p3_total_magnetization, p3_ordering, p3_magnetization_normalized_vol, p3_is_magnetic, p3_num_magnetic_sites, p3_magnetic_species and p3_elastic_tensor are absent).",
        "Every p3_ column is constant within a reduced_formula (joined from the most stable Materials Project polymorph) and needs a computed structure or DFT run. None is available from composition alone, so Tier 3 is a different prediction setting from Tier 1/2.",
        "Correction to Phase 6 documentation: 'physics-complete rows have 0% missing on the 24 added columns' holds only for the 4-column completeness bundle. In the matched Ms set 11 of the 24 columns are more than 20% missing (elastic 65–83%, dielectric 31–95%, VBM/CBM 60%); missingness itself carries little signal (grouped-CV R² about 0.03 or less).",
        "Non-physical inputs: p3_elastic_anisotropy reaches 5.7e110, p3_bulk_modulus 1.4e8 GPa, p3_shear_modulus 2.0e7 GPa (70, 13 and 2 rows above 1e6 in the full Tier 3 population). Tree models are insensitive to them; Ridge is not.",
        "No single physics column is a strong stand-alone predictor (grouped-CV R² ≤ 0.05 for Ms). The derived site count, which volume and volume-per-atom jointly reveal exactly, is the strongest (0.067).",
    ])
    rows = []
    for rc in ["cell_size", "symmetry_identity", "same_calculation", "independent_response"]:
        part = audit[(audit["risk_class"] == rc) & ~audit["feature"].str.startswith("DERIVED")]
        rows.append([rc.replace("_", " "), ", ".join(part["feature"].str.replace("p3_", "")), part.iloc[0]["leakage_judgment"]])
    add_table(doc, ["Group", "Columns", "Judgment (Ms, prespecified rule)"], rows, [1.1, 2.4, 3.3])
    bullets(doc, [
        "Same 5 splits for every number below. Full Tier 3 gain over Tier 1: " + sens_text(robust, "tier1", "tier3") + ".",
        "Tier 2 plus only the volume family: " + sens_text(robust, "tier1", "A_T2_plus_volume_family") + ".",
        "Corrective control — Tier 2 plus ONE scalar, the site count of the Materials Project cell: " + sens_text(robust, "tier1", "C_T2_plus_nsites")
        + ". What the full Tier 3 adds beyond that scalar: " + sens_text(robust, "C_T2_plus_nsites", "tier3") + ". Only Ridge benefits from the symmetry and same-calculation columns.",
        "Interpretation: for a per-unit-cell target, knowing how many atoms are in the cell is legitimate structural information but it is closer to normalisation than to 'deeper physics'. The Phase 6 statement that Tier 3 physics stably improves Ms must therefore be narrowed (section 8).",
    ])
    doc.add_picture(str(out / "figures" / "phase7_fig_ms_tier3_feature_sensitivity.png"), width=Inches(6.4))


def checks_section(doc: Document, checks: pd.DataFrame, fam: pd.DataFrame, attrib: pd.DataFrame) -> None:
    doc.add_heading("6. Supporting checks (no reanalysis)", 1)
    bullets(doc, [
        f"Reconciliation: {int((checks['status'] == 'PASS').sum())} checks pass, {int((checks['status'] == 'FAIL').sum())} fail. Test metrics and all 27 tier-pair improvements recompute from the saved predictions; matched n_test is identical at every tier; final Table 3 uses matched populations only; Stage 3, 5 and 7 comparisons use identical rows.",
        "SHAP: attribution rows equal the Stage 4 matched test materials in the same order; feature names and order equal the model inputs; for Curie and Ms, bias + sum(SHAP) reproduces the saved XGBoost predictions (max error below 0.05).",
        "Attribution is not increment: physics columns carry " + ", ".join(f"{r.target} {r.physics_share_of_total_mean_abs_shap_pct:.0f}%" for r in attrib.itertuples())
        + " of total mean |SHAP|, yet only Ms shows any Tier 1→3 increment, and Phase 7 shows that increment tracks the cell-size group. Neither SHAP rank (p3_point_group, p3_volume) nor a single ablation is evidence of a general physics advantage.",
        f"Family analyses (Stage 5): {len(fam)} family-vs-general comparisons, about {0.05 * len(fam):.1f} interval exclusions expected by chance; {int(fam['stable_unadjusted'].sum())} stable unadjusted, {int(fam['stable_after_holm_005'].sum())} after Holm, {int(fam['stable_after_bh_005'].sum())} after Benjamini–Hochberg (approximate p from interval width). Every analysed family has at least 717 distinct test formulas; the provenance slices have at least 234 except the Ms Experimental slice (9 rows), which is correctly not analysed.",
        "Secondary targets: every K1 / Ms-mass / Ms-volume tier comparison is 'no claim', and no sentence in the Phase 6 summary or tables asserts a tier improvement for them; they remain exploratory.",
    ])


def closing_sections(doc: Document, gate: pd.DataFrame) -> None:
    doc.add_heading("7. Deviations and limitations", 1)
    bullets(doc, [
        "Compute budget: the main matched experiment ran on all 10 splits for both targets. The Tier 3 sensitivity variants ran on splits 0–4 for Ms (the protocol minimum of five) but only on splits 0–1 for Curie; the clipped-Ridge and refit-without-extremes analyses ran on Curie splits 0–2 plus the two exploding fits. Curie sensitivity results are descriptive.",
        "The add-one variants were registered while the main runs executed, before any multisplit result had been inspected. The single-scalar control was added after the restricted and add-one results were seen, as the protocol's 'smallest necessary corrective experiment'; it is a post-hoc control, not a prespecified test.",
        "Splits overlap in materials, so across-split t-intervals are descriptive; the inferential intervals are the formula-bootstrap intervals. Pooled-mean Ridge Curie values are dominated by exploded fits.",
        "The Ms target is computational and the Tier 3 descriptors come from Materials Project at formula level; the Curie target is experimental. The two targets answer different questions.",
        "Phase 6 results were not altered. Two Phase 6 statements are superseded (the Ridge cause; missingness of the 24 physics columns); they are documented here and in the project wiki rather than edited in place.",
        "Target cleaning: Phase 7 itself changed no target. After the review, demonstrable errors in the Curie and ordering targets were corrected in a NEW dataset version (v1.3, section 1a); sections 3–6 below describe the v1.2 experiments as run. Still not done: a per-atom Ms target, new algorithms, new features.",
    ])
    doc.add_heading("8. Decision gate and recommendation", 1)
    add_table(doc, ["Criterion", "Met", "Evidence", "Consequence"],
              [[r.criterion, "yes" if r.met else "NO", r.evidence, r.consequence] for r in gate.itertuples()], [1.5, 0.4, 3.2, 1.7])
    doc.add_paragraph("Recommendation: proceed to manuscript preparation only after scientific review of this package, with these claims.")
    bullets(doc, [
        "Tier 2 (oxidation chemistry): no benefit on any target. On the repaired v1.3 targets tree models show a small stable degradation (Curie: Gradient Boosting and XGBoost; ordering: XGBoost). The Phase 6 matched-ordering Tier 1→2 'stable improvement' was NOT replicated (it was a single-split result) and is withdrawn.",
        "Tier 3 and Ms per cell: report a small (about 2–4% of MAE), direction-consistent, algorithm-dependent improvement; the prespecified every-algorithm criterion is NOT met (Ridge and Gradient Boosting satisfy it, XGBoost does not). It is explained by unit-cell size information; state that the electronic, thermodynamic, symmetry and elastic/dielectric descriptors add no demonstrable value for the tree models beyond it. Do not claim a general physics advantage.",
        "Tier 3 and Curie / ordering (v1.3 targets): no benefit; report Curie with its split-to-split range and the formula-weighting caveat (formula-weighted MAE shows a small stable degradation for XGBoost). Ordering skill must be presented with the cross-provenance finding: models trained on one label provenance do not transfer to the other.",
        "Report the Ridge Tier 3 failures as a data-quality issue (non-physical elastic values) and present the clipped-input variant, clearly labelled, instead of the unclipped one in headline tables.",
        "Correct the Phase 6 documentation on the Ridge cause and on the missingness of the 24 physics columns.",
        "Optional corrective experiment for the reviewers: repeat the Ms comparison on a per-atom or per-formula-unit target, which removes the cell-size normalisation altogether.",
    ])
    doc.add_heading("9. Output index", 1)
    bullets(doc, [
        "phase7_curie_multisplit_results.csv, phase7_ms_multisplit_results.csv — one row per analysis × split × variant × algorithm with sample and formula counts, metrics and per-split intervals.",
        "phase7_paired_tier_differences.csv (per-split, pooled-mean and pooled-concatenated differences with intervals) and phase7_robustness_summary.csv (across-split robustness and verdicts).",
        "phase7_tier3_feature_audit.csv (+ _static, excluded columns), phase7_reconciliation_checks.csv, phase7_frozen_split_reproduction.csv, phase7_decision_gate.csv, phase7_attribution_vs_increment.csv, phase7_family_multiplicity.csv, phase7_subgroup_sizes.csv.",
        "phase7_curie_linear_instability.csv, phase7_curie_linear_explosion_rows.csv / _features.csv, phase7_ms_linear_instability.csv, phase7_split_composition_*.csv.",
        "figures/ (six PNGs); work/ (every saved prediction); RUN_INSTRUCTIONS.md, phase7_package_versions.txt, phase7_audit_log.md; code in EDA/src/phase7_*.py and EDA/tests/test_phase7_validation.py.",
        "v1.3 revision (EDA/10_phase7_validation/v1.3/): claims_register.md/.csv, revision_response.md, ordering_v13_*.csv (baseline, provenance slices, cross-provenance transfer, matched tiers), v13_full_*_metrics/tier2_deltas.csv, Curie v1.3 multisplit results and robustness summary; datasets in EDA/datasets/v1.3 (MANIFEST, excluded/ quarantine files), splits in EDA/02_splits/v1.3, rules in EDA/00_config/v1_3_curation_rules.yaml, code build_analysis_dataset_v1_3.py, run_v13_*.py, agg_v13_ordering.py, phase7_revision.py.",
    ])


def build(out) -> None:
    robust = pd.read_csv(out / "phase7_robustness_summary.csv")
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(10.5)
    doc.add_heading("Phase 7 — Publication-Readiness Validation: Summary", 0)
    doc.add_paragraph("Physics-Informed AI for Magnetic Materials · Analysis Dataset v1.2 · protocol: Phase_7_Publication_Readiness_Validation_Protocol.docx · files in EDA/10_phase7_validation/v1.2/")
    overview(doc, robust)
    revision_section(doc)
    methods(doc)
    curie_section(doc, robust, out)
    ms_section(doc, robust, out)
    audit_section(doc, robust, pd.read_csv(out / "phase7_tier3_feature_audit.csv"), out)
    checks_section(doc, pd.read_csv(out / "phase7_reconciliation_checks.csv"), pd.read_csv(out / "phase7_family_multiplicity.csv"),
                   pd.read_csv(out / "phase7_attribution_vs_increment.csv"))
    closing_sections(doc, pd.read_csv(out / "phase7_decision_gate.csv"))
    doc.save(out / "phase7_validation_summary.docx")


def main() -> None:
    out = p7.output_dir(p7.load_phase7_config())
    build(out)
    print(f"wrote {out / 'phase7_validation_summary.docx'}")


if __name__ == "__main__":
    main()
