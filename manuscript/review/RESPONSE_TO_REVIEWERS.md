# Response to reviewers: round 1 (2026-11-10)

Revised files:
- `paper/manuscript/manuscript.tex` (the round-1 version is kept in `review/manuscript_round1.tex`)
- `paper/manuscript/supplementary.tex`
- tables and figures rebuilt from `paper/results/` with `paper/scripts/make_tables.py` and `make_figures.py`

New analyses are in `paper/results/revision/`. The analysis plan was written before any run; its deviations log is `results/revision/PLAN.md`.

## Required revisions

### RR1. Abstract and Discussion over-claims (EIC W2; R1 W1, W6; DA M4, M5, M7, M8)
The abstract, RQ2 heading, Discussion and Conclusion are rewritten. Each over-claim was replaced as follows:
- **(a) Conformal coverage.** "All conformal methods reached 90% coverage on average", plus a separate statement that only normalized intervals held coverage for high predictions.
- **(b) Cell size.** "Mostly a unit-cell-size effect", now shown for the per-cell, per-atom and per-formula-unit targets.
- **(c) Provenance.** "At chance" was removed. The replacement is the shared-label-space test with a permutation null, together with the label-agreement κ.
- **(d) Calibration source.** Intervals are described as calibrated internally.
- **(e) Curie Tier 3.** The point estimates are now reported as losses ("no detectable gain", MDE about 40 K).
- **(f) "Least informative" ranking.** Removed; the Conclusion now states a recommendation.
- **(g) "None can be inferred from another".** Now "related but not interchangeable", with the co-variation with distance stated.
- **(h) Unseen chemistry.** "Skill could not be established" replaces "fell substantially".

### RR2. RQ1 scope (EIC W4; R2 W1; R3 W5; DA M1, M2)
- **Wording.** "Physics descriptors" became "non-magnetic DFT descriptors" in the title, abstract, RQ1 heading and Fig. 1 caption.
- **Disclosure.** The excluded magnetic DFT columns and the reason for excluding them (label leakage) are now in Results and Methods.
- **New test (A6, Table 3).** For Tc, on the matched population, we added:
  - magnetic-sublattice geometry (M-M distances and connectivity, M-X-M angles and coordination);
  - DFT magnetic outputs;
  - a frozen CHGNet crystal embedding.

  None beats Tier 1. Against Tier 3, CHGNet (+19 K, stable) and the magnetic outputs (borderline) only recover Tier 3's loss.
- **Discussion.** The descriptor-target mismatch explanation is now discussed.

### RR3. Cross-provenance ordering (EIC W3; R1 W6; R2 W3; DA M6)
New test (A2, Table 7):
- **Label agreement.** On 949 formulas labelled by both sources, agreement is 28% and κ = 0.00 [-0.03, 0.03]. Materials Project labels 66% of experimental antiferromagnets as ferromagnetic (cf. Horton et al. 2019).
- **Shared label space (FM/AFM/FiM)** with a 20-refit permutation null:
  - MP -> experimental: balanced accuracy 0.337 [0.273, 0.396], against a null median of 0.342 and 97.5th percentile of 0.374.
  - Experimental -> MP: 0.384 [0.366, 0.401], against a null 97.5th percentile of 0.351.
  - Within-provenance references: 0.769 and 0.591.
- **Composition distance across provenances** shows little covariate shift for MP -> experimental.

### RR4. Stability rule, multiplicity, XGBoost seeds (R1 W2, W3; DA M3)
- **Rule.** The full stability rule is now stated in Methods: Nadeau-Bengio corrected t interval, pooled formula-bootstrap interval, and 7/10 sign agreement.
- **Multiplicity.** A primary family of 9 Tier 1->3 contrasts, with Holm-adjusted p in Table 2. Everything else is labelled secondary.
- **Seeds.** XGBoost is averaged over 8 realisations for Curie and the moment. Ordering XGBoost stays a single realisation: the seed refit was cut for run time and is disclosed. Gradient boosting, which does not depend on thread count, gives the same conclusion.
- **Result.** Only the moment-per-cell Tier 3 gains survive Holm (gradient boosting, XGBoost; p = 0.046). The former "upper limit +3.8 K" for Curie is replaced by the refit-aware interval [-42.5, +13.9].

### RR5. Pre-specification wording and external-benchmark inference (R1 W4; DA M3)
- **Wording.** Methods now says when each set of rules was written, relative to which results:
  - the v1.3 curation rules;
  - the external audit plan, written after an earlier flawed analysis;
  - Amendment 2, made after the first bootstrap run.
- **Resampling counts.** Table 6 now reports the resampling clusters (81 blind, 18 unseen-system), with BCa intervals and a fixed-reference skill score.
- **All clusterings (Table S4).** Under chemical-system clustering, the upper limits are 0.21 (R², BCa) and 0.17 (skill). The text therefore now says that skill in unseen chemical systems "cannot be established".

### RR6. Circular hardest decile and calibration-set reuse (R1 W5)
- **Subgroups (Table 4, Fig. 2).** Coverage is now evaluated on subgroups defined independently of every method's scale: the top decile or third of the prediction, the text-mined source or oxides, and the farthest distance decile. Normalized conformal still holds best, e.g. Curie top decile 87% against 66% and 69%.
- **Design effect (Table S6).** 12-17, giving an effective calibration size of 250-340, which explains the normalized method's split-to-split variability.
- **Ordering calibration.** Temperature and thresholds are now fitted on separate calibration halves; coverage is unchanged (within 0.3 points). Classwise ECE is added (Table 5).

### RR7. Moment target (R2 W2; EIC W5)
- **Name.** The target is renamed everywhere to the DFT total moment, m_cell in μB/cell. The text states it is not an experimental saturation magnetization.
- **New target (A5; Table 2, Fig. 1d, Table S8).** Moment per formula unit, using the same-calculation atom count. The Tier 3 gain is stable but about 3% for gradient boosting, and is not resolved beyond a site-count scalar for the tree models.
- **Data description (Methods).** The GGA/GGA+U/r2SCAN mix and the ordering composition of the MP entries, plus the FM-initialisation caveat.

### RR8. Completeness
Done:
- Supplementary Information document (`supplementary.tex`).
- Data licences researched (Table S10; evidence in `results/revision/research/data_licences.md`).
- Code licence (MIT) stated.
- AI-use disclosure drafted.
- Abstract shortened to 181 words.
- "Ms" renamed; internal codes explained.

Left as `\todo` because only the authors can provide them:
- affiliations;
- funding;
- CRediT confirmation;
- repository DOI;
- implementing the redistribution plan for AFLOW, MAGNDATA, the two compilations and the external table.

### RR9. Related work and prior results (EIC W1; R2 W5; R3 W2)
- **Related work.** The Introduction now cites:
  - UQ/OOD benchmarks: Varivoda, Omee, Li MD-HIT, Xiong, Bartel, Palmer;
  - covariate-shift conformal (Tibshirani), selective prediction (Geifman), WILDS;
  - active learning (Lookman);
  - prior magnetic ML: Long, Merker, Court & Cole 2020, Acosta, ALIGNN.
- **References.** All of the above are verified, in `revision/new_references.bib`.
- **Table S9.** Prior results, reported as random splits with Tc MAE 56-69 K; none is chemistry-grouped.
- **Framing.** The contributions are now led by the magnetism-specific results, with the general thesis as a corollary.
- **Correction.** The text-mined database is now cited as Kelly & Cole 2025 (Figshare 29559686), not Court & Cole 2018.

## Suggested revisions
| Item | Done? | Where |
|---|---|---|
| SR1 magnetic/structure physics test | Curie only (ordering and moment cut for run time; label leakage limits them anyway) | Table 3, Limitations |
| SR2 Curie label noise | partly: a title-based screen of 200 records, classified by the AI assistant from titles (not full texts), flags 11.0% [7.4, 16.1] as likely wrong; within-formula spread. The author spot check of 32 records (`review/curie_spotcheck_32.csv`) is pending | Results, Methods, Table S5 |
| SR3 ordering decomposition | yes: macro-F1 0.681 vs 0.692 on the magnetic-element subset; per-class recall | Results, Table S7 |
| SR4 deployment analysis | yes: abstention, threshold task, interval decisions | Table 8, Discussion |
| SR5 distance-aware conformal | yes: Mondrian-by-distance (farthest decile 88.2 -> 90.3%); weighted conformal (no change) | RQ2, Table S6 |
| SR6 overlap as a field-wide problem | not done, on the authors' instruction | - |
| SR7 baseline mismatch, matched vs full, MDE | yes: LCSO baseline explained; matched Curie MAE 203 K vs 76 K; MDE about 40 K | Results |
| SR8 unstable Ridge row | yes: clipped Ridge reported; unclipped labelled not interpretable | Table 2 |
| SR9 reproducibility | partly: runtimes, thread caveat, plan/deviations log. No container. | Code availability, SI |
| SR10 matched leave-chemical-system-out | not done (cut for run time); caveat stated | RQ3, Limitations |

## Round 2 (re-review: Minor Revision; `review/round2/`). Fixes made 2026-11-10
1. **Per-atom result.** Restored in Results (GB +2.9%, XGB +2.8%, Ridge +6.0%) and in Table S8, with per-atom rows. "Vanished" is now "no longer resolved". The text states that a residual of about 3% remains after cell size is removed.
2. **Transfer wording.** "Does not transfer" (Discussion) is now "transfers poorly". MP -> experimental is indistinguishable from the shuffled-label null; experimental -> MP is only slightly above it.
3. **Prior-corrected transfer.** Now reported in Methods (0.314 and 0.400). The text states that Table 7 uses raw probabilities.
4. **Curie subgroups.** All subgroups are now reported (new Table S11), with a sentence in RQ2 saying where constant-width methods cover more than normalized conformal.
5. **Rescoping.** The title, RQ1 heading, Fig. 1 caption and Conclusion now say "non-magnetic DFT descriptors".
6. **Structure-matched test.** The dropped test is disclosed in Methods and in PLAN.md, and the noisy-join explanation is labelled untested.

Also: the abstract is cut to 154 words, and both authors' affiliation is filled in.

## New problems found during the revision
1. The text-mined database citation was wrong (now Kelly & Cole 2025).
2. The Curie Tier 3 "no practical gain" claim depended on an interval that ignored refit variance.
3. The ordering-set coverage and ECE figures now come from 10 splits (they previously came from one).
4. A geometry bug (missing periodic-image M-X-M pairs) was caught by unit checks on MnO and SrFeO3 before any fit used the descriptors.
