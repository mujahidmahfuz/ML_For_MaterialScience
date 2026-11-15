# Revision plan (round-1 simulated review, 2026-11-10)

Written BEFORE any of the analyses below was run. Source of every item: `paper/manuscript/review/editorial_decision.md`
(RR = required, SR = suggested). User instruction: fix every item except the external-benchmark-overlap framing (SR6 is NOT done).
Code: `final/revision/scripts/`. Outputs: `final/revision/outputs/<item>/`. Frozen inputs (datasets v1.2-v1.4, splits, Phase 6-8 and
final-check outputs) are read-only; nothing earlier is overwritten. Deviations from this plan are logged at the end of this file.

## Shared conventions
- "Splits" = the 10 prespecified Phase 7 formula-grouped splits (seeds 20267000+i) unless stated otherwise.
- **Stability rule (now stated in full; RR4).** A tier difference is called *stable* only if ALL of the following hold:
  (a) the pooled formula-bootstrap 95% interval excludes 0;
  (b) the Nadeau-Bengio corrected resampled-t 95% interval (variance x (1/J + n_test/n_train), t with J-1 df) excludes 0;
  (c) at least 70% of the splits have the same sign.
  It is called *borderline* if (a) or (b) holds but not both. Otherwise it is *not stable*.
- **Multiplicity (RR4).**
  - The primary confirmatory family is the 9 Tier 1->3 contrasts: 3 targets (ordering macro-F1, Curie MAE, moment MAE) x 3 algorithms.
  - Holm adjustment is applied to the corrected-t p-values of that family.
  - Every other contrast (Tier 1->2, Tier 2->3, per-atom, per-f.u., site count, new descriptor tiers) is labelled secondary/exploratory and
    reported unadjusted.
- **XGBoost seed averaging (RR4).**
  - XGBoost results enter the tier tables as the per-split mean over all available thread/seed realisations.
  - Curie: the 8 saved realisations. Moment: the saved thread/seed realisations.
  - Ordering: 3 realisations (seeds 0, 1, 2 at 16 threads), refitted for this revision.
- **Practical margins (minor, DA m3).** Fixed here, before results:
  - Curie: 10 K (unchanged).
  - Ordering: 0.02 macro-F1.
  - Moment per cell: 0.10 muB/cell (about 4% of MAE).
  - Wording: "no practical gain" requires the upper improvement limit to be below the margin. Otherwise say "no detectable gain".

## Items

**A1 (RR4, SR8). Refit-aware tier inference.** Inputs are the saved per-split test predictions:
- Curie: v1.3 Phase 7 work.
- Moment: v1.2 Phase 7 work.
- Ordering: v1.3 matched work.

Outputs:
- the pooled bootstrap interval, the corrected-t interval, the sign count, Holm p-values and the verdict under the rule above;
- the clipped-Ridge Curie Tier 1->3 from the saved `linear_clip` diagnostic, which replaces the unstable Ridge row (labelled "not interpretable" if still unstable);
- the minimum detectable effect (80% power) per contrast, from the corrected-t SE.

**A2 (RR3). Cross-provenance ordering.**
- (a) Formulas labelled both by MP and by an experimental source: confusion matrix, raw agreement and Cohen's kappa, with a formula-cluster
  bootstrap CI.
- (b) Transfer on the shared FM/AFM/FiM label space:
  - Train both directions without NM rows, frozen v1.3 split, test-formula exclusion as before, XGBoost and gradient boosting.
  - Report raw results, and results after prior correction to the target-domain class prior. That prior is estimated from the target
    domain's TRAINING partition, never from its test set.
  - Report balanced accuracy and macro-F1 with a formula-cluster bootstrap CI.
  - Compare against an empirical null from 20 label-permutation refits (fixed selected hyperparameters), and against the analytic 1/3.
- (c) Covariate shift: the composition-distance distribution of the experimental test rows to the MP training formulas, and vice versa.
- Claim rule: write "does not transfer" only if the corrected balanced-accuracy upper limit is below the permutation-null 97.5th
  percentile. Otherwise report the size of the drop.

**A3 (RR5). External benchmark inference.** On the saved `similarity_records.csv` (primary benchmark):
- the number of resampling clusters per subset under paper (shared-DOI), first-DOI and chemical-system clustering;
- percentile and BCa cluster-bootstrap intervals (10,000 resamples; jackknife over clusters for the acceleration) for MAE and R²;
- a skill score against a fixed reference, 1 - MSE/MSE(training-mean predictor), plus the target SD per subset;
- the wording-rule verdict under all 3 clusterings x 2 interval types.

The rule stays as written (upper R² limit <= 0.2 means "no skill"). The text will state that it was fixed after the October subset
results were known.

**A4 (RR6). UQ without circular subgroups.**
- (a) Rerun the 10-split regression UQ (Curie, moment), saving per-row intervals. Use the same code and seeds as Phase 8 repeated.
- (b) Report coverage of all 3 methods on subgroups defined independently of `sigma`:
  - composition-distance decile of the test formula to the proper-training formulas (TV distance, as in the external audit);
  - top decile of the point prediction;
  - material family;
  - label source.
- (c) Design effect: within-formula intraclass correlation of the coverage indicator, effective n, the implied i.i.d. SD of coverage
  next to the observed split-to-split SD, and the training-conditional Beta bound.
- (d) Ordering: split each calibration set 50/50 by formula; the temperature is fitted on half A and the conformal thresholds on half B.
  Report per-class set coverage and size, plus classwise ECE, over 10 splits.

**A5 (RR7). Moment target.**
- Rename to "DFT total moment" (`m_cell`, muB/cell).
- New primary target: moment per formula unit, `m_fu` = m_cell x n_atoms(reduced formula) / n_sites(cell), using the corrected
  same-calculation site counts (`peratom_cell_map.parquet`).
- Refit Tier 1/2/3 and the site-count control on the 10 splits.
- Sensitivity analyses: rows with m > 0 only, and a zero vs non-zero split reported separately.
- Report the GGA/GGA+U mix of the MP entries, from MP thermo run types fetched once.

**A6 (SR1, RR2). Magnetic physics test.**
- (a) Fetch the MP structures of the matched rows.
- (b) Magnetic-structure descriptors (pymatgen; magnetic ion = C1 magnetism-capable element):
  - magnetic-ion number density and site fraction;
  - nearest and mean M-M distance;
  - number of M neighbours within 1.15 x d_min;
  - mean M-X-M angle over anion-bridged pairs;
  - fractions of M-X-M angles in [150, 180] and [80, 100] degrees.
- (c) A frozen CHGNet crystal embedding (64-d; pretrained universal potential), as a structure-aware representation.
- (d) Variants, 10 splits x 3 algorithms:
  - tier1 + magstruct;
  - tier3 + magstruct;
  - tier3 + CHGNet;
  - for Curie only, tier3 + the excluded magnetic DFT outputs (p3_total_magnetization per atom, p3_num_magnetic_sites fraction,
    p3_magnetization_normalized_vol, p3_is_magnetic). There is no leakage for experimental Tc. These outputs are not used for ordering
    or the moment because of label leakage.
- (e) A structure-matched Curie subset: rows whose source record gives a space group equal to the MP polymorph's space group. Compare
  Tier 1 vs Tier 3 there.
- Claim rule: the RQ1 conclusion is broadened to "physics descriptors" only if none of these shows a stable gain. Otherwise the paper
  reports which physics helps.

**A7 (SR2). Curie label noise.**
- Within-formula SD and MAD of Tc after C1-C5, overall and by source, for formulas with at least 2 records.
- A title-based audit of a stratified random sample of 200 retained records: strata = source x Tc tercile, seed 20261110. Crossref titles
  are adjudicated against a written rubric: magnetic Curie transition / other transition / film-nano-pressure / unclear.
- Report the contamination rate with a Wilson CI.

**A8 (SR3). Ordering decomposition.**
- Frozen v1.3 Tier 1 full-population predictions (refit, saved).
- Per-class recall.
- Macro-F1 on the subset with at least one magnetism-capable element.
- The fraction of NM rows that contain one.

**A9 (SR4). Deployment on the 465 blind records.**
- Risk-coverage curves, abstaining by composition distance and by interval width: MAE and coverage at 100/75/50% retained.
- Threshold task Tc > 300 K: accuracy, precision and recall. Interval-based decisions (decide only when the interval lies wholly on one
  side) report decision rate and accuracy.
- Top-k enrichment of Tc > 300 K materials.
- All with paper-cluster bootstrap CIs.

**A10 (SR5). Distance-aware conformal.**
- Mondrian normalized conformal with distance bins (calibration-set distance quartiles) for the internal 10 splits (from A4).
- Weighted (covariate-shift) conformal with weights from a calibration-vs-test distance density ratio, on the same splits.
- Report coverage by distance decile versus plain normalized conformal.
- The external benchmark is used only if the external model's calibration arrays can be regenerated exactly.

**A11 (SR7). Reconciliation and population checks.**
- Explain Table 6 against the headline baselines (split / population / algorithm).
- Tier 1 performance on matched vs unmatched test rows.

**A12 (SR10). Matched leave-chemical-system-out.**
- For each of 10 chemical-system splits, the same held-out test rows are scored under two training regimes:
  - (A) all non-test-formula rows available, so other formulas of the same chemical system are allowed;
  - (B) the held-out chemical systems are removed from training.
- Tier 1 XGBoost at 16 threads, the 3 targets.
- The difference A - B isolates chemical-system novelty.

**A13 (RR1, RR2, RR8, RR9, SR9). Writing.** Manuscript rewrite, related work and prior-results table, SI, data/code availability,
licences, AI disclosure, reproducibility notes (lock file, smoke run, runtimes from the saved `refit_seconds`).

## Deviations log
- 2026-11-10 A6: the descriptor geometry was first checked on MnO and SrFeO3 and found to miss periodic-image M-X-M pairs. It was fixed
  (angles are now measured around each anion site) before any fit used it.
- 2026-11-10 A7: the "hand audit" is an adjudication of Crossref titles + compound + value plausibility by the analyst. The per-record
  labels are in `outputs/a7/title_audit_adjudicated.csv`; full-text reading was not done.
- 2026-11-10: all background runs were stopped by the host's low-memory reaper mid-way (queue at A6 Curie split 3; A2 after
  MP->experimental; A4 after Curie). All jobs are resumable; nothing finished was lost.
- 2026-11-10 (found during A2/A6): the ChemDataExtractor Curie/Neel files used are Kelly & Cole 2025 (Figshare 29559686), not Court &
  Cole 2018. The manuscript citation is to be corrected.
- 2026-11-10 SCOPE CUT (user instruction: keep only what matters for acceptance, to save run time). Dropped before any of their results
  were seen:
  - A6 for ordering and for the moment (kept for Curie). RQ1 is rescoped in the text instead.
  - A12 matched leave-chemical-system-out. The caveat is stated in the text.
  - A4 moment rerun. The saved Phase 8 repeated-split subgroups that are not defined by sigma are used instead (families, label source,
    highest predicted third).
  - A8 refit. Its quantities come from the A4 ordering probabilities instead.
  - A1 ordering XGBoost seed averaging (4 partial splits moved to `outputs/a1/ordering_xgb_seeds_partial_unused`, not used). Ordering
    XGBoost is reported as a single realisation, and the deterministic gradient-boosting result is the reference.
  Kept: A2, A4 ordering, A5.
- 2026-11-10 (disclosed after the round-2 re-review): A6(e), the Curie comparison restricted to records whose source space group matches the
  computed polymorph, was also not run (dropped with the other A6 cuts, before any result was seen). The manuscript now says the
  "noisy join" explanation is untested.
