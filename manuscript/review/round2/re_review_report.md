# Verification Review Report (round 2)

Manuscript: "Accuracy is not reliability: DFT descriptors, calibration and chemical generalization in machine learning of magnetic materials" (revision 1, 2026-11-10)
Simulated venue: npj Computational Materials. Mode: academic-paper-reviewer re-review (EIC only). Checklist: round-1 `editorial_decision.md`.
Companion file: `traceability_matrix.md` (item-by-item evidence).

## Decision
**Minor Revision** (EIC check of the next version; no new external panel needed). The manuscript is **not submittable as-is**: author-only placeholders and the abstract length remain (see Conditions).

## 1. Summary

The revision is substantial and mostly honest. The authors ran nine new analyses (A1-A7, A9, A10) within one day, rewrote the abstract, Introduction, RQ2 heading, Discussion and Conclusion, assembled the SI and drafted the declarations. The key round-1 problems are resolved in substance:
- the conformal-guarantee misstatement (the F1 block) is fixed;
- the stability rule is stated in full, with refit-aware Nadeau-Bengio intervals and a Holm-corrected primary family. Only the per-cell moment gains survive Holm (p = 0.046);
- the provenance test now uses a shared label space and a permutation null, and the agreement statistic (kappa = 0.00 on 949 formulas) is a strong new result;
- the pre-specification history is told accurately, with resampling-cluster counts and all three clusterings;
- a magnetic-sublattice, magnetic-DFT and CHGNet test for Tc closes much of the "wrong descriptors" objection;
- related work and a prior-results table are added.

I spot-checked 40 numbers against the result files. All 40 match (Section 2).

The paper is not yet at Accept, because 7 of 9 required items are only partially addressed. Most residuals are of one kind, and it is the kind round 1 was about. Where the new analyses gave mixed results, the text sometimes reports the favourable part or keeps a stronger word than the evidence allows:
- per-atom moment claim: unsupported (RR1(b));
- "does not transfer": violates the authors' own pre-registered claim rule (RR1(c), RR3);
- Curie family and source subgroups: computed but only the favourable ones reported (RR6);
- prior-corrected transfer: run but not reported, and the Methods imply the reported numbers are prior-corrected (RR3);
- title and RQ1 heading: not rescoped, although the response letter says they were (RR2);
- structure-matched subset: pre-planned, silently dropped, yet the explanation it would test is asserted (NEW-4).

All of these can be fixed with existing outputs and rewording; none needs new data collection. Hence Minor Revision rather than Major.

## 2. Verified-number spot check (40 numbers)

| # | Number (as in manuscript) | Location | Source file | Match |
|---|---|---|---|---|
| 1 | 79,125 / 29,740 / 87,513 records | Abstract L40 | tables/table1_dataset.csv | yes |
| 2 | Class counts sum to 79,125 (FM 34,098, NM 31,673, FiM 7,161, AFM 6,193) | Table 1 notes | table1 notes (arithmetic) | yes |
| 3 | Matched Curie Tier 1 GB MAE 203 K | L74 | table3 notes 202.9; a6 curie_variant_mae.csv | yes |
| 4 | Ordering macro-F1 0.681 vs 0.692; AFM 0.55, FiM 0.49 | L82 | tableS7 / a4_uq/ordering_decomposition_10splits.csv | yes |
| 5 | Curie GB Tier 1->3 -14.3 [-42.5, +13.9] | L97 | a1_tier_inference.csv (nb_ci) | yes |
| 6 | Curie XGB 8-realisation -8.2 [-48.3, +32.0] | L98 | a1 (xgboost_seedmean) | yes |
| 7 | Clipped Ridge -14.4 [-33.5, +4.8] | L99 | a1 (linear_clip) | yes |
| 8 | Primary Holm p = 1.0 for ordering and Curie | L95 | a1 holm_p | yes (but family includes unclipped Ridge, see NEW-9) |
| 9 | MDE "about 40 K" | L101 | a1 mde80: GB 39.2, XGB 55.8, clip-Ridge 26.6 | partial (GB only) |
| 10 | Ordering GB Tier 1->2 -0.028 | L101 | a1 (-0.0284; verdict "borderline loss") | value yes; label see RR4 |
| 11 | Moment GB +0.079 [+0.030, +0.127], XGB +0.062 [+0.023, +0.101], Holm p 0.046 | L103 | a1 | yes |
| 12 | Beyond-site-count +0.024 [-0.003, +0.050] | L103 | round-1 text / sitecount_control_10splits | yes |
| 13 | Per-f.u. GB +0.031 [+0.014, +0.048]; XGB +0.023; Ridge +0.053 | L107-109 | a5_moment_per_fu/per_fu_tier_effects.csv | yes |
| 14 | Per-f.u. beyond site count GB +0.014 [-0.001, +0.028], XGB +0.004 [-0.026, +0.033], Ridge +0.030 | L111 | a5 | yes (wording "vanished" not supported) |
| 15 | 10,821 per-f.u. rows | L105 | a5 / Table 1 notes | yes |
| 16 | Table 3 vs Tier 1 range -10.8 to +9.5 K | L127 | a6 curie_physics_contrasts.csv | yes |
| 17 | CHGNet XGB vs Tier 3 +19.2 (stable), magnetic DFT GB +19.6 (borderline) | L127 | a6 | yes (single XGB realisation) |
| 18 | SHAP share 40% / 36% | L131 | rq1/interpretation/tier3_physics_shap_share.csv (0.404 / 0.363) | yes |
| 19 | Spearman >= 0.95 ordering & moment; Curie 0.83-0.94 | L131 | xai_stability_summary.csv | yes (Curie range mixes min and mean) |
| 20 | Curie marginal 89.3 / 90.3 / 89.4% | L142 | a4_uq/curie_subgroup_coverage.csv | yes |
| 21 | Top decile 87.4 / 65.5 / 68.6% | L148, abstract | a4 curie_subgroup_coverage.csv | yes |
| 22 | Text-mined 86.0 vs 78-79% | L149 | a4 (85.97, 78.18, 79.30) | yes |
| 23 | Moment top third 86.7 / 72.3 / 83.4; oxides 91.0 vs 84.0 | L150-151 | Phase 8 repeated_split_summary via table4 | yes |
| 24 | Design effect 12-17; effective n 250-340; implied SD 1.6-1.9; ~4,200 rows | L154 | a4 curie_design_effect.csv (12.4-16.7; 251-337; 1.63-1.89; 4,184.5) | yes |
| 25 | Mondrian farthest decile 88.2 -> 90.3% | L156 | a4 curie_distance_aware_by_decile.csv | yes |
| 26 | Source shift 76.9 / 80.3 / 85.1% | L156 | rq2_uncertainty/curie/uq_source_shift.csv (frozen split) | yes (single split; not stated) |
| 27 | ECE 0.064 -> 0.090 -> 0.014; classwise 0.035/0.049/0.032 | L162-164 | a4 ordering_ece_summary.csv | yes |
| 28 | Marginal sets 89.8% (FM 96.2, NM 97.7, AFM 57.0, FiM 54.3), size 1.39; class-conditional 89.8-90.9, size 1.61 | L166, abstract | a4 ordering_calibration_split_summary.csv (split rows) | yes |
| 29 | MP->experimental sets 83.5% | L166 | rq2/ordering/uq_source_shift.csv (marginal) | yes |
| 30 | LCSO 0.712 -> 0.684, -0.028 [-0.041, -0.016], 10/10 | L179 | table7 | yes |
| 31 | 949 formulas, 28%, kappa 0.00 [-0.03, 0.03]; 336/508 = 66% | L181 | a2 label_agreement.csv, label_confusion.csv | yes |
| 32 | MP->exp BA 0.337 [0.273, 0.396]; null median 0.342, 97.5th 0.374; AFM recall 7% | L185 | a2 transfer.csv (raw XGB), transfer_null.csv | yes (raw, not prior-corrected) |
| 33 | Exp->MP 0.384 [0.366, 0.401]; null 0.351; within-source 0.591, 0.769 | L185-186 | a2 | yes |
| 34 | Distance median 0.081 vs 0.077 | L188 | a2 distance_shift.csv | yes (exp->MP 0.169 omitted) |
| 35 | 1,998 (80%) seen; 1,200 (48%) identical; 105 excluded (60/18/35); 2,395 primary | L194 | tableS1 | yes |
| 36 | Blind 465 (81): MAE 102.7 [75.1, 143.6], R2 0.69 [0.43, 0.82], coverage 89.5% | L198 | a3_external_inference.csv (BCa) / table6 | yes |
| 37 | Unseen system 69 (18): MAE 171.9 [82.6, 293.7], R2 -0.17 [-1.02, 0.64], skill -0.17 [-0.77, 0.56] | L200 | a3 | yes |
| 38 | Chem-system clustering upper limits 0.21 (R2 BCa), 0.17 (skill) | L203 | a3 / tableS4 | yes |
| 39 | Spearman rho 0.28 [0.10, 0.49]; MAE 62 -> 165 K; width 388 -> 529; coverage 0.95 -> 0.85; seen-system comparable-distance R2 0.75 | L213 | similarity_spearman.csv, tableS3, similarity_unseen_system_comparison.csv (0.748) | yes |
| 40 | Screening: keep 50% MAE 103 -> 71 K, coverage 0.93; recall 0.94, precision 0.77; decided 37%, accuracy 92.5%; base rate 0.57 | L223-225 | a9_screening/risk_coverage.csv, threshold_task.csv | yes |

Also checked: title screen 11.0% [7.4, 16.1], 3.5/3.5/4.0% and "most from text-mined" (12/22) against a7 (match); median within-formula SD 4.2 K and 13% > 100 K (match); prior-results ranges in L49 against Table S9 (match).

## 3. Residual issues from round 1 (summary; details in traceability matrix)

1. **RR1(b)/RR7: per-atom statement unsupported.** L111 says the "mostly cell size" conclusion holds per atom and cites Table S8, which has no per-atom rows. Saved evidence says the per-atom gain is carried by same-calculation DFT outputs. The per-atom gain the reviewers asked to be added (2.9% / 2.8% / 6.0%) was removed. L111 also says the per-f.u. gain "vanished" beyond the site count, but GB keeps +0.014 [-0.001, +0.028] with 9/10 splits positive.
2. **RR1(c)/RR3: Discussion L239 "does not transfer"** violates the PLAN.md A2 claim rule in both directions. The experimental -> MP result is above its null.
3. **RR1(g): Discussion L234** "none can be read off another" restates the withdrawn claim.
4. **RR2: rescoping not done where claimed.** The title, RQ1 heading, Fig. 1 caption title and Conclusion still say "DFT descriptors". The response letter says these were changed to "non-magnetic DFT descriptors".
5. **RR3:** prior-corrected transfer results are not reported (0.314 and 0.400). Methods L391 implies the reported numbers are prior-corrected. The confusion matrix is not shown (add it to the SI; it has 4 x 4 cells).
6. **RR4:** ordering XGBoost is a single realisation (disclosed). Table 3's only stable gain rests on one XGBoost realisation. "Borderline" labels are not used consistently. The MDE is given as one number (about 40 K), but it ranges from 27 to 56 K.
7. **RR6: selective subgroup reporting** (family and label source) for Curie. Normalized conformal is worst on computational-source labels (86.6% vs 90.4% split) and below CQR in the farthest decile.
8. **RR8:** 14 TODOs remain, and the abstract is 182 words (see Conditions).

## 4. New issues introduced by the revision

| # | Type | Location | Severity | Description | Concrete fix |
|---|---|---|---|---|---|
| NEW-1 | Unsupported claim / deleted result | L111; Table S8; Discussion L248 | MAJOR | "Holds for per-cell, per-atom and per-formula-unit normalizations (Table S8); per-atom estimate superseded." No per-atom result is in the paper or SI. No analysis supersedes the corrected per-atom estimate. The add-one evidence contradicts "cell size". L248 attributes the same-calculation effect to the per-cell target, but the evidence is for per-atom. | Restore the per-atom Tier 1->3 gains (GB 2.9% [1.5, 4.4], XGB 2.8%, Ridge 6.0%) as an SI row. State that per atom the gain is carried mainly by same-calculation outputs (add-one). Drop "per-atom" from the L111 sentence. Replace "vanished" with "was not resolved". |
| NEW-2 | Claim-rule violation / over-claim | Discussion L239 | MAJOR | "Does not transfer" contradicts the pre-registered rule and the exp->MP result above the null. It also compares 4-class macro-F1 with 3-class balanced accuracy. | Use "transfers poorly: at the permuted-label null from MP to experiment, barely above it in reverse, far below within-source". |
| NEW-3 | Method misdescription / unreported analysis | Methods L391; L183-186; Table 7 | MAJOR | The prior-corrected transfer was run but is not reported. The Methods sentence implies the reported results are prior-corrected. | Report raw and prior-corrected values side by side, or state that the table shows raw probabilities. One sentence plus a Table 7 column. |
| NEW-4 | Undisclosed deviation from the analysis plan | L127, L245; SI reproducibility notes; L375 | MAJOR | PLAN.md A6(e) (structure-matched Curie subset: source space group = MP polymorph) was pre-planned. It is not in the outputs, not in the deviations log and not in the list of cut analyses. This is the test of the explanation the paper now favours ("Tier 3 losses are what a noisy join would produce"; "our data favour two"). The SI also lists 3 cut analyses; PLAN lists 5 (plus the A4 moment rerun and the A8 refit), and the top-k result (A9) is unreported. | Either run A6(e) (cheap: existing descriptors, one subset) or list it as dropped and present the noisy-join explanation as a hypothesis ("consistent with", not "our data favour"). Make the SI list of cuts complete. |
| NEW-5 | Selective reporting | Table 4; L146-152; Conclusion L278 | MAJOR | Family and label-source subgroups are computed for Curie but omitted, and they are less favourable to normalized conformal (see residual 7). The Conclusion generalizes "only normalized ... held it for ... weak labels". | Add a family and source panel for all three methods (SI is fine). Qualify: normalized conformal is best for high predictions and text-mined labels, not uniformly. Rename the Table 4 column ("second subgroup"), because oxides are not "weak labels". |
| NEW-6 | Response-letter accuracy | RESPONSE_TO_REVIEWERS RR2 | MINOR (integrity) | The letter claims the title and RQ1 heading were rescoped. They were not. | Fix the text or the letter. Re-check every "Where" claim in the letter. |
| NEW-7 | Selective covariate-shift evidence | L188 | MINOR | "Not of chemistry" cites only the MP->exp distance. The exp->MP direction has a large shift (median 0.169 vs 0.033). | Report both directions. Restrict the label-definition conclusion to MP->exp, where kappa and distance support it. |
| NEW-8 | Figure/text inconsistency | Fig. 3 vs L196 and Table 6 | MINOR | Fig. 3 shows percentile intervals (round-1 values, e.g. R2 [-0.93, 0.66]). The text says BCa ([-1.02, 0.64]). Fig. 2b has no SD bars although the caption says it does. The Fig. 2 legend says "Top decile" for panel b, which is the top third. | Rebuild Fig. 3 from a3 BCa columns. Fix the Fig. 2 legend and bars. |
| NEW-9 | Statistical reporting | Table 2 notes; a1 | MINOR | The Holm family uses the unclipped Ridge Curie contrast, which the paper calls not interpretable. The table shows the clipped row with "-". Ordering GB Tier 1->2 is "borderline loss" by the stated rule but is called "not stable" (L101). | State the family composition in the notes (or recompute with clipped Ridge; conclusions are unchanged). Use "borderline". |
| NEW-10 | Small numeric mis-summaries | L101, L131, L154, L227 | MINOR | (a) "gains of 14-32 K" should be 5-32 K. (b) MDE about 40 K should be 27-56 K. (c) Spearman "0.83-0.94" mixes minimum and mean. (d) "Explains most of the normalized-conformal variability" (implied 1.6 vs observed 2.5 SD). (e) "Distance is the better abstention signal" is untested (MAE 71 [61, 97] vs 73 [59, 109]). | Reword each one. |
| NEW-11 | Title-screen method | L343; Table S5; PLAN A7 | MINOR | The rubric categories were extended after PLAN.md, with no log entry. The 16% "different compound" category is excluded from "likely wrong" without justification. Whether the stratified estimate needs weighting is not stated. | Log the deviation, justify the exclusion, and report a range (11% to 27% if "different compound" counts), weighted if allocation was not proportional. |
| NEW-12 | Unstated single-split numbers | L156, L166 | MINOR | The source-shift coverages (76.9/80.3/85.1, 83.5%) come from the single frozen split (Phase 8), while the neighbouring numbers come from 10 splits. | Add "(frozen split)". |
| NEW-13 | Abstract wording | L40, L278 | MINOR | "Held coverage for high predictions (87% vs 66%)": 87% is below nominal. | "Came closest to nominal (87% vs 66%)". |

No CRITICAL new issue was found. No headline conclusion is invalidated. Each MAJOR item is a reporting or wording correction on outputs that already exist.

### Cross-reference integrity (mechanical check)
- All 9 `\input{../tables/...}` paths (main) and 8 (SI) exist. All 5 `\includegraphics` targets exist.
- Every `\ref` resolves to a `\label`.
- All 54 (main) and 8 (SI) cite keys exist in references.bib; no duplicate keys.
- 8 bib entries are uncited (harmless with BibTeX): barber2021jackknife, bouckaert2004replicability, court2018curie, dunn2023hierarchical, liechtenstein1987exchange, sanvito2017heusler, wilkinson2016fair, zhang2024gptarticleextractor. Cite Sanvito 2017 (RR9) or remove it.
- New references spot-checked for plausible metadata: Kelly & Cole 2025, Abedi Orang 2026, Varivoda, Omee, Li MD-HIT, Tibshirani, Geifman, Long, Merker, Belot, Acosta, Nadeau-Bengio, Kull. Deep verification is left to the integrity stage.

### Honesty of disclosures
- **AI use** (L441): candid and specific. It states that the AI wrote code, ran analyses, drafted text and made the title-screen calls. Adequate; adapt it to the journal policy.
- **Title-based label screen** (L70, L269, L343, Table S5): disclosed repeatedly as a title-only, AI-made screen, "not a verified error rate". Good. The author check is pending (TODO).
- **Cut analyses**: partly disclosed. 3 of 5 cuts are listed, A6(e) is undisclosed and the A9 top-k result is not reported (NEW-4).
- **Errors found** (L404-414): exemplary; it includes the revision-round errors.

## 5. Remaining TODOs (all author-only unless marked)

Main text (13):
1. L36 department.
2. L36 institution.
3. L36 city.
4. L36 country (corresponding author's affiliation).
5. L38 confirm department and address (Tokyo International University).
6. **L343 author check of the title screen: "checked by the authors on N records with M disagreements"** (requires the 32-record spot check in `review/curie_spotcheck_32.csv`). This is the only TODO with scientific content.
7. L423 funding and acknowledgements.
8. L428 funding statement.
9. L430 repository and DOI.
10. L438 implement the redistribution plan (AFLOW, MAGNDATA, compilations), and drop external compound names and values from the three result files.
11. L439 repository URL.
12. L440 confirm CRediT contributions.
13. L441 adapt the AI disclosure to the journal policy.

SI (1):
14. Table S10 footnote: implement the plan before deposit.

Not a TODO macro but required before submission: shorten the abstract from 182 words to the venue limit (npj Computational Materials guide: 150 words, to my understanding; verify).

## 6. Decision rationale

- **Priority 1:** 2 FULLY_ADDRESSED (RR5, RR9), 7 PARTIALLY_ADDRESSED (RR1, RR2, RR3, RR4, RR6, RR7, RR8), 0 NOT_ADDRESSED, 0 MADE_WORSE at item level. Accept requires all Priority 1 items fully addressed, so **Accept is not possible**.
- **Priority 2:** 10/10 have a response (above the 80% threshold). SR6 is declined, which is acceptable for a suggested item because the finding is reported and translated into recommendations; give one sentence of rationale. SR10 is not done but the caveat is stated, which is acceptable.
- **Why not Major Revision:** the per standards, Major Revision is for re-analysis, new data or methodological flaws. The F1 block (the conformal misstatement) is resolved. The panel's core methodological requests (refit-aware inference, multiplicity, shared-label-space provenance test, non-circular subgroups, magnetic-physics test) were all carried out, and the numbers are correct (40/40 checked). The remaining problems are reporting choices on results that already exist: wording, missing rows, one misdescribed Methods sentence and one undisclosed plan deviation. They do not restructure the argument, and they can be fixed in about a week.
- **Why not a light "accept with edits":** the residuals sit on the paper's own thesis (do not over-claim; report subgroups; follow pre-registered rules). Several are MAJOR because they repeat the round-1 failure mode. The next version should therefore be checked by the EIC against this report before submission.

**Can it be submitted as-is?** No. Besides the scientific residuals, it has 14 TODOs (affiliations, funding, CRediT, repository DOI/URL, licence implementation, author check of the title screen) and an over-length abstract. These author-only items are **conditions**, not scientific failures.

**Is it ready for external review once the residual roadmap is done?** Yes. After the items below and the author placeholders, I would expect it to go to external review with a reasonable chance of minor revisions at most. The core science is sound and the transparency is unusually high.

## 7. Prioritized residual roadmap

| Priority | Item | Action | Effort |
|---|---|---|---|
| 1 | NEW-1 / RR1(b) | Restore the per-atom gains (SI row). Remove the unsupported per-atom clause. Replace "vanished" with "not resolved". Explain the site-count effect for the intensive target. | 2 h |
| 1 | NEW-2 / RR1(c) | Rewrite Discussion L239 according to the A2 claim rule. | 15 min |
| 1 | NEW-3 / RR3 | Report raw and prior-corrected transfer. Fix Methods L391. Add the 4 x 4 agreement matrix to the SI. | 1 h |
| 1 | NEW-5 / RR6 | Add the Curie family and label-source subgroup coverage for all three methods. Qualify the Conclusion and abstract ("came closest"). Rename the Table 4 column. | 2 h |
| 1 | RR2 / NEW-6 | Add "non-magnetic" to the title, RQ1 heading, Fig. 1 caption and Conclusion, or restrict to Tc. Correct the response letter. | 30 min |
| 1 | NEW-4 | Run A6(e), or disclose it as dropped and soften "our data favour". Complete the list of cut analyses. | 0.5-1 day |
| 2 | RR1(g) | Discussion L234: "related but not interchangeable". | 5 min |
| 2 | RR4 / NEW-9 | Flag Table 3 XGBoost as a single realisation (or average 3 seeds for the CHGNet row). Document the Holm-family composition. Use "borderline". Give the MDE range. | 2 h |
| 2 | NEW-7, NEW-8, NEW-10, NEW-12, NEW-13 | Fix the distance in both directions, rebuild Fig. 3 with BCa intervals, fix the Fig. 2 legend and bars, correct the numeric wording, mark single-split numbers. | 2 h |
| 2 | NEW-11 / SR2 | Log the rubric deviation, give the range with "different compound", and complete the author spot check (TODO L343). | author |
| 3 | RR7 | One sentence justifying per-cell as primary (or switch). Quantify the share of FM initializations. | 30 min |
| 3 | RR8 conditions | Abstract to 150 words or fewer; affiliations; funding; CRediT; deposit with DOI; licence implementation; scrub external names. Cite Sanvito 2017 or drop it. | author |

Residual items that may instead be stated as acknowledged limitations: ordering XGBoost seed averaging (already stated), the matched leave-chemical-system-out comparison (stated), and the magnetic-physics test for ordering and the moment (stated, with leakage as the reason).
