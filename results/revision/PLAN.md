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

## Added after the round-3 review (2026-11-16; not in the original plan; specifications are in the script docstrings, written before the runs)
**A14 (R3-1, R3-2). Pooled Tier 1 -> 3 contrast and the planned Holm family.** `scripts/a14_pooled_tier_inference.py`, no refit. Per split, the
mean of the three algorithms' improvements (Curie: clipped ridge, gradient boosting, XGBoost seed mean; moment: ridge, gradient boosting,
XGBoost seed mean; ordering: logistic, gradient boosting, XGBoost single realisation); corrected-t interval from the split-to-split spread of
that mean, bootstrap with formula draws shared by the algorithms. Also recomputes the Holm family with the CLIPPED Curie ridge member, as A1
planned. Output `outputs/a14_pooled/`. Result: Curie -12.3 K [-32.7, +8.1] (worse in 8/10 splits; upper limit below the 10 K margin),
moment +0.065 [+0.038, +0.092] (10/10 splits), ordering -0.002 [-0.035, +0.031] (does not exclude the 0.02 margin); Holm with the clipped member:
Curie ridge 0.740, the other eight unchanged.

**A15 (R4-2). A9 screening rules on the internal test sets.** `scripts/a15_internal_screening.py`, no refit. Saved per-row Curie test intervals
of the 10 splits (A4), the A9 definitions (abstain on composition distance or interval width; threshold task Tc > 300 K; interval decisions;
top-k), computed per split and averaged. Output `outputs/a15_internal_screening/`. Result: abstaining on interval width works inside the
training chemistry (MAE 103 -> 43 K at 50% retained, coverage 0.92); abstaining on composition distance does not (closest 25%: 103 K); interval
decisions settle 44% of records at 97.6% accuracy.

**A20 (R1-5). End-to-end graph-network check for the Curie temperature. STATUS: STOPPED 2026-11-17 BY THE USER, NOT COMPLETED, NOT ANALYSED, NOT IN THE PAPER.** Reason: optional; the manuscript already limits its null to formula-joined descriptors and a frozen embedding. About 26 of 90 planned runs finished (seed 0, splits 0-8 partly); the files in outputs/a20_gnn/preds are partial and were never scored against the claim rule, so they must not be quoted. a20_gnn_analysis.py was written but not run. (Specified 2026-11-16, before any model was trained.)
Question: the null for Tier 3 concerns descriptors joined by formula and a frozen CHGNet embedding (A6c). Does a pretrained graph network that is fine-tuned
end to end on the matched Curie rows (4,602 records, only 521 distinct MP structures) add anything to composition features?
Variants, same matched rows and the SAME 10 Phase 7 split labels (train / validation / test), same head for all:
  - mlp_t1  : MLP on the Tier 1 predictors only (control, no structure);
  - gnn_t1  : pretrained CHGNet (v0.3.0 weights), crystal feature (64-d) trainable, concatenated with the Tier 1 predictors, MLP head;
  - gnn_only: the CHGNet branch alone with the same head (no Tier 1 predictors).
Fixed settings (no tuning): target standardised on the training rows; Huber loss; AdamW, weight decay 1e-4; learning rate 1e-3 head / 1e-4 CHGNet; batch 32;
max 60 epochs, early stopping on validation MAE (patience 10), best-validation weights scored on test (NOT refitted on train+validation, unlike the boosting
baselines, which slightly favours them); Tier 1 predictors median-imputed and standardised on the training rows; 3 seeds per split averaged in prediction space.
Contrasts (MAE, K; positive = first variant better; refit-aware interval as in A1/A19, 10 splits): PRIMARY C1 = mlp_t1 - gnn_t1 (does end-to-end structure add
to composition?). Secondary: boosting Tier 1 (saved, gradient_boosting and XGBoost seed-mean) - gnn_t1; boosting Tier 3 - gnn_t1; boosting Tier 1 - gnn_only.
Claim rule, fixed before the run:
  * C1 interval above zero => 'end-to-end structure learning adds to composition for this network'; it is then reported against the boosting baselines, and
    'beats the boosting Tier 1 baseline' is claimed only if that secondary interval is also above zero;
  * C1 interval includes zero => 'no detectable gain from end-to-end structure learning either', with the minimum detectable effect; the null is then NOT specific to
    formula-joined descriptors or to a frozen embedding, but remains limited to this network, this data size (521 distinct structures) and these fixed settings;
  * C1 interval below zero => reported as a loss.
Limits to state: MP structures are those of the lowest-energy polymorph (the same join as Tier 3); results hold for CHGNet only, not other architectures; no tuning.

**A19 (R1-3; plan item A6(e), originally dropped). Same-space-group test of the descriptor join. STATUS: RUN 2026-11-16, claim rule fixed in the script docstring BEFORE the run.**
`scripts/a19_same_spacegroup.py`. Saved test predictions scored on records whose source space group (parsed by fixed rules) equals the polymorph's (536) vs differs (237); 69
unparsable, 3,760 report none. RESULT: pooled Tier 1 -> 3 on 'same' = -10.9 K [-23.8, +2.0] (3/10 splits better, MDE 17.9 K); 'different' -6.0 [-27.3, +15.3]; difference -4.9
[-28.0, +18.2] => no detectable gain even where the join is right; the noisy-join explanation is NOT supported (limits: models trained on all rows, only 18% of records report a
space group, small). Parsing rules were not extended after the unresolved symbols were seen.

**A18 (round-2 follow-up to R2-2). Why a site count helps the intensive per-formula-unit moment. STATUS: RUN 2026-11-16 (descriptive, no fit; hypothesis in the script docstring written before
the data were read). `scripts/a18_sitecount_explanation.py`. Result: cells holding more than one formula unit (42% of 10,821 rows) have a lower moment per formula unit (3.11 -> 1.71 muB from one
to three-or-four formula units) and more AFM labels (3.2% -> 16.7%); near-zero moments 1.1% -> 8.8%; Spearman -0.16, AUC 0.70 => a weak proxy for the ordering, hypothesis partly supported, mechanism
not tested. The other round-2 item (frequency of FM configurations in MP) is answered from the source: Horton et al. 2019 report 31,631 of 33,986 magnetic MP entries (93%) in a FM configuration.**

**A17 (R1-1). Larger hyperparameter search for the primary Curie contrast. STATUS: RUN 2026-11-16 (the first attempt with 4 workers was killed by the host's low-memory
reaper before any split finished; rerun with 2 workers, 10 splits, about 1.5 h). RESULT: the null is robust to tuning. Original grid Tier 1 -> 3 = -14.3 K [-42.5, +13.9]; larger
search -11.8 K [-35.2, +11.7] (bootstrap [-21.9, -0.04] -> "borderline loss" by the A1 rule); test MAE Tier 1 202.9 -> 203.7 K, Tier 3 217.2 -> 215.5 K (moved < 2 K) although the
validation RMSE of the selected settings fell by 27 K (Tier 1) and 34 K (Tier 3): the search fitted validation noise. Specified 2026-11-16 BEFORE the run.** `scripts/a17_tuning_grid.py`.
Matched Curie population (4,602), the 10 splits, histogram gradient boosting (deterministic), Tier 1 vs Tier 3. Candidates: the 4 original settings + 60 random draws from
learning_rate {0.02, 0.05, 0.1} x max_leaf_nodes {7, 15, 31, 63, 127} x min_samples_leaf {5, 10, 20, 40} x l2 {0, 1, 10} x max_features {0.3, 0.5, 0.75, 1.0} x
max_iter {250, 500} (seed 20261116), the SAME 64 for both tiers; selection rule unchanged (validation RMSE). Decision rule: if the tuned Tier 1 -> 3 contrast still
shows no stable gain (A1 rule) the null is robust to tuning; if it shows a stable gain, report it and revise the claim. Scope: gradient boosting only (XGBoost depends on the
thread count and is not covered). Run with OMP_NUM_THREADS=3 x 4 workers (thread-invariant for this algorithm).

**A16 (R2-1). MAGNDATA as an independent anchor for the ordering labels. STATUS: RUN 2026-11-16 on the official repository download (2,997 paths; 509 macOS
'._' stubs skipped; 2,488 structure files).** Two script changes were made after the first parse and BEFORE any comparison was seen: skip the '._' stubs, and label
partial-occupancy structures 'disordered' (not used) instead of 'unparseable'. Result: 936 AFM / 91 FM / 80 FiM collinear entries (840 compositions; 19 with conflicting
entries), 797 non-collinear, 397 disordered, 169 incommensurate, 18 unlabelled. Agreement with the structure: experimental 0.923 [0.900, 0.948] (n = 442, kappa 0.715),
Materials Project 0.219 [0.171, 0.275] (n = 251, kappa 0.032); where MP and experiment disagree (114 compositions) the experimental label matches the structure in 107.
Labeller sanity check: 7/7 textbook compounds present are AFM as expected. Result tables AND the derived per-entry / per-composition labels are in the package (2026-11-16: the user read the MAGNDATA usage conditions: use is for science, with
the condition to cite the Bilbao Crystallographic Server and MAGNDATA, done in the manuscript, the SI and SOURCE_AND_CITATION.md); the .mcif structure files are not redistributed. Original status line follows.
`scripts/a16_magndata_anchor.py`. Input: the MAGNDATA repository (.mcif files) from the official download, which needs a registered academic account and
acceptance of the usage conditions (to be done by the user; `magndata_download.html`). Each structure is labelled FM/AFM/FiM from its own collinear moments
(pymatgen CollinearMagneticStructureAnalyzer; incommensurate and non-collinear entries are not used); MP and the experimental sources (A2 definitions) are
scored against that label on shared compositions (matched by composition key): agreement, kappa, per-class recall, confusion matrices, and a three-way table of
who is right when MP and experiment disagree. Claim rule, fixed before any real run: report the agreement of each source with the anchor with formula-bootstrap
intervals; say "source X is wrong in Y% of cases" only if the sample is at least 20 compositions per source and the intervals support it; collinear entries only,
so the anchor covers a subset of compounds (state the coverage). The earlier project copy of MAGNDATA (no formulas, keyword-inferred labels) is NOT used.

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
- 2026-11-10 (logged late, 2026-11-16, found in the round-3 check of `paper/results/revision/a1_tier_inference.csv`): A1 did NOT replace the
  unstable Ridge row by the clipped one in the Holm family. The family kept the unclipped Curie `linear` contrast (mean -825.2 K,
  Holm p = 1.0), and `linear_clip` (-14.4 K [-33.5, +4.8], NB p = 0.123) was labelled secondary. The manuscript states this (Extended Data
  Table 1 note: using the clipped contrast gives an adjusted p of 0.740 for it and leaves the other eight unchanged).
- 2026-11-10 (logged late, 2026-11-16): A5 declared the moment per formula unit the "new primary target". The manuscript kept the per-cell
  moment (m_cell) as primary (it is the quantity the databases report, and the comparisons were configured on it in advance) and
  analyses m_fu alongside it (Fig. 1d, Supplementary Table 8). Round 2 flagged this as an unlogged deviation (RR7); open follow-ups from
  round 2: quantify "most entries were computed from ferromagnetic initial configurations"; explain why a site count still helps for the
  intensive per-formula-unit target.
- 2026-11-10 (disclosed after the round-2 re-review): A6(e), the Curie comparison restricted to records whose source space group matches the
  computed polymorph, was also not run (dropped with the other A6 cuts, before any result was seen). The manuscript now says the
  "noisy join" explanation is untested.
