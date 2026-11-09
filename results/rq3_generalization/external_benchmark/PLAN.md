# External Curie benchmark: audit, chemical similarity, grouped uncertainty — plan

Written 2026-11-09, BEFORE any of the three analyses below was run.

What had been seen when this plan was written (stated so the reader can judge what is prespecified):
- The subset-level results of 2026-10-19 (`../external_summary.csv`: MAE, R2, coverage per subset). No per-record error had been
  inspected against any audit flag or distance.
- The raw external table (names, values, DOIs), to design the audit checks.
- One bug, found while designing the audit: the old DOI normaliser (`predict_external.normalise_doi`) did not strip the
  `https://doi.org/` prefix that our text-mined training source (chemdata_curie_neel) uses. With a correct normaliser, 363 external
  DOIs are in that training source and the "blind + paper never used" subset shrinks from 807 to 555 records. All subsets below use
  the corrected normaliser; the old numbers are reported next to the new ones.

The model, its predictions and its 90% intervals are NOT changed: the saved predictions in `../external_predictions.csv`
(Tier 1 XGBoost, v1.3, 80% of formulas train, normalized conformal intervals calibrated on the other 20%) are reused.

## 1. Audit of the external table (no prediction or error is loaded by the audit script)

Every record gets flags. Exclusion is allowed only for the categories marked EXCLUDE; everything else is reported and used to
define stricter subsets, never silently removed.

| Code | Check | Rule | Action |
|---|---|---|---|
| A1 | Computational label | source paper is computational/theoretical only (DFT, ML prediction, model calculation, no measurement). Screen: Crossref title/journal/abstract keywords; every flagged paper adjudicated by hand from its title (+ abstract when Crossref has one); criteria fixed here: EXCLUDE only if the paper reports no measurement. Mixed theory+experiment = keep. | EXCLUDE |
| A2 | Malformed composition | (a) formula cannot be parsed; (b) a symbol is not a real element or is a hydrogen isotope written as an element (D, T); (c) the record's chemical system is incompatible with the compound named in the source-paper title, checked by hand only for flagged cases. Large normalised coefficients (e.g. `Lu300Co777Sn400`) are NOT malformed by themselves: they are valid dilute or off-stoichiometric compositions. | EXCLUDE (a,b,c) |
| A3 | Duplicate records | (a) exact duplicate row; (b) two records with the same reduced formula (same composition written differently). Same-formula records are averaged into one composition-level record (mean Tc; DOIs pooled) so no composition is counted twice. | MERGE |
| A4 | Same target definition as training | the v1.3 training-label curation rules C1-C5 (`EDA/00_config/v1_3_curation_rules.yaml`) applied unchanged: C1 no magnetism-capable element, C2 elemental non-ferromagnet, C3 Tc < 1 K, C4 Tc > 1400 K, C5 formula labelled only AFM in our ordering data (value is probably a Neel temperature). The model was trained only on labels that pass these rules. | EXCLUDE |
| A5 | Not a magnetic Curie temperature | source title says the transition is ferroelectric, superconducting or a Neel/antiferromagnetic transition for this compound (same reason as v1.3 R1). Adjudicated by hand from titles. | EXCLUDE |
| A6 | Possibly not directly comparable | thin film, nanoparticle/nanocrystalline, under pressure, irradiated, monolayer/2D, spin-glass, or a composite/multilayer, from the title. Training data also contain such forms, so they are NOT excluded; reported as a sensitivity analysis (results with and without A6). | FLAG ONLY |
| A7 | Overlap with training sources | (a) formula in our repository (as before); (b) any DOI of the record in our Curie data (any source, valid or excluded rows, corrected normaliser); (c) the external value equals (within 0.5 K) a training Tc for the same formula, i.e. the table copies an upstream compilation we also used; (d) near-copy composition: composition distance (section 2) to the nearest training formula < 0.01. | DEFINE SUBSETS |
| A8 | No DOI | reference is a book or missing. | FLAG ONLY |

Primary benchmark = all records minus A1, A2, A4, A5 exclusions, after A3 merge. Results are reported for the ORIGINAL table
(as in October) and for the primary benchmark, subset by subset, with the number removed by each rule.

## 2. Chemical similarity to the training materials (metric fixed before any distance is compared with an error)

Reference set: the unique reduced formulas of the Curie rows that fit the point model (the 80% training part; 23,757 rows).
Sensitivity: all v1.3 Curie formulas (training + calibration).

- PRIMARY metric, composition distance d_comp: for element-fraction vectors p (record) and q (training formula),
  d = 0.5 * sum_e |p_e - q_e| (total-variation distance; 0 = identical composition, 1 = no element in common).
  d_comp = minimum over the reference set (k = 1). Independent of how the formula is written.
- SECONDARY metric, descriptor distance d_desc: Euclidean distance in the 65 Tier 1 descriptors, each z-scored with the
  training mean and SD, to the nearest training formula (k = 1); this is the model-input distance proposed in the October report.
- Sensitivity: mean distance to the 5 nearest training formulas, for both metrics.

Analysis unit and dependence: one record per composition (A3 merge). Records from the same paper are dependent, and repeated
measurements of a composition are pooled into one record, so all intervals come from a cluster bootstrap over source-paper
clusters (records connected by any shared DOI; records without a DOI form one cluster per reference string).

Statistics (all on the primary benchmark; repeated on the blind subset = formula not in repository):
1. Spearman rho between distance and absolute error, and between distance and interval width (reported width hi - lo), with
   95% paper-cluster bootstrap CI (10,000 resamples, seed 20261109).
2. Distance bins fixed from the distance values only (no errors looked at): bin 0 = d_comp == 0 (formula used in training);
   the remaining records split into quartiles of d_comp. Per bin: n, papers, MAE, median AE, R2, coverage, mean width, with CIs.
3. Trend contrast: MAE(top quartile) - MAE(bottom non-zero quartile) and the same for width and coverage, CI from the same
   bootstrap (both bins resampled jointly).
4. Does distance explain the unseen-chemical-system failure? Report the d_comp distribution of the unseen-system records and the
   MAE of seen-system blind records in the same distance range.

## 3. Uncertainty of the external-subset comparisons

For every subset (all, seen formula, blind, blind + paper never used, blind + unseen system, blind + paper never used + unseen
system; original table and primary benchmark): MAE, median AE, R2, 90% coverage, mean width, each with a 95% percentile CI from
a cluster bootstrap over source-paper clusters (10,000 resamples, seed 20261109). Sensitivity: clusters = chemical systems.
R2 in each resample is computed against that resample's own mean (same definition as the point estimate).
Comparisons (joint resampling of the clusters of both subsets): MAE and R2 of blind + unseen system minus blind + seen system;
reported as a difference with CI and the share of resamples in which the unseen-system subset is worse. The share of resamples
with R2 < 0 is reported for the unseen-system subset.

How the generalization claim will be worded (fixed now): "no skill beyond the mean in unseen chemical systems" only if the
upper CI limit of R2 is <= 0.2; otherwise "much weaker, with wide uncertainty", giving the CI.

## Amendment 1 (2026-11-09, during the audit, from compositions and Crossref titles only; still no prediction or error loaded)
Findings that refined the A1/A2 rules:
- The table is text-mined: a value is attached to EVERY paper that mentions a compound, so a computational paper often carries a
  cited experimental value of a different compound (e.g. CeRh3B2 = 115 K in a LaRh3B2 band-structure paper). A1 is therefore applied
  at record level: a record is a computational label only if ALL its DOIs are computational-only papers AND the record is that
  paper's own subject compound (named in the title, or the paper's predicted list). Cited background values in computational papers
  are kept and flagged (A1c); a sensitivity run removes them too. Adjudications: adjudication_papers.csv, adjudication_records.csv.
- A title/record element mismatch is NOT evidence of malformation (papers cite other compounds), so A2(c) as first written would
  remove valid records; it is replaced by three objective composition checks, each confirmed by hand on every flagged record:
  (d) mixed-scale normalisation: max coefficient >= 1000 and a glass-former/metalloid (B, C, Si, P, Zr, Nb) below 0.5 at.% -- part of
      a nominal formula was scaled by 100 and part was not (e.g. Zr7Fe6230(Ni1335B2)2 = (Fe0.7Ni0.3)89Zr7B4 garbled to B 0.04 at.%);
  (e) impossible ionic stoichiometry: formula with O or F (and no other anion-forming element) whose anion charge lies outside the
      range reachable by the cations' known positive oxidation states (e.g. Ba2La8MnFeO30: A10 B2 O30 is not a perovskite);
  (f) alloy-family shorthand written as an equiatomic formula and used as such in the source title (NdFeB for Nd2Fe14B, LaFeCoSi for
      La(Fe,Co,Si)13).
- Records whose composition looks mis-extracted but cannot be proven so (e.g. CeFeCoGe = 866 K in a CoTcCrZ Heusler theory paper)
  are kept and flagged A2s (suspect); a sensitivity run removes them.
- Correction to the October report: Fe3125(Ir7Rh118)27 is NOT garbled; it is Ir-substituted FeRh (Fe48Rh49Ir3) from a paper on
  FeRh pseudobinaries, and 643 K is its Curie point.

## Amendment 2 (2026-11-09, AFTER the first bootstrap run -- stated as outcome-aware)
Diagnostic seen after the first run: the pre-specified paper clusters (records linked by ANY shared DOI, transitively) form one
giant component of 727 records (29%, 233 DOIs), because text-mined records that average several papers (e.g. La0.7Ca0.3MnO3 with
23 DOIs) chain unrelated papers together. This is valid but very conservative for the large subsets. Added, as a sensitivity only:
clusters = the FIRST-listed DOI of each record (each paper one cluster; a multi-paper average attached to its first paper). The
pre-specified clustering stays the primary one; all three clusterings (pre-specified, first DOI, chemical system) are reported.
Post-hoc diagnostic also added (labelled as such): the k = 5 composition distance split by whether the exact formula is in training.

## Amendment 3 (2026-11-09, after the first analysis run; a definition bug, fixed objectively)
The distance scatter showed 539 of the 1,302 October "blind" records at composition distance 0 from a Curie TRAINING formula. Cause:
our repository stores `reduced_formula` as fractional strings (Ca0.33La0.57Mn1O3) while the external table is integer-normalised
(Ca33La57Mn100O300); the October blind flag compared strings. Fix: "formula seen" is now COMPOSITION identity -- canonical key =
sorted element:atomic-fraction pairs rounded to 6 decimals -- against every formula in the v1.2 repository (A7a), and the
copied-value check (A7c) matches by the same key. The October string flag is kept and reported for comparison. Consistency check:
every record at d_comp = 0 from a Curie training formula must have its key in the repository.
Side finding (same cause, inside our own data): 86 Curie compositions have more than one spelling; 30 straddle the formula-grouped
splits (27 of 4,541 Curie test rows; ordering 157 of 11,902 test rows; Ms none). Reported as a limitation of the Phase 6-8 splits.

## Outputs (this folder)
audit_flags.csv, crossref_metadata.csv, adjudication_*.csv, benchmark_primary.csv, subset_metrics_bootstrap.csv,
subset_comparisons.csv, similarity_records.csv, similarity_bins.csv, similarity_trend.csv, figures/*.png, AUDIT_RESULTS.md.
