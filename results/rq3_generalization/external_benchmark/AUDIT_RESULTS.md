# External Curie benchmark: audit, chemical similarity and grouped uncertainty — results (2026-11-09)

Plan, written before the analyses, and three dated amendments: `PLAN.md`. Code: `audit_common.py`, `fetch_crossref.py`, `audit_external.py`,
`analyze_external.py`, `make_figures.py`; tests `test_external_audit.py` (10 pass). The model, predictions and 90% intervals are the October ones
(`../external_predictions.csv`); nothing was refit. All intervals are 95% percentile intervals from 10,000 cluster-bootstrap resamples (seed 20261109).
Unless stated otherwise, clusters are the pre-specified paper clusters (records linked by any shared DOI).

## 0. Two definition errors in the October analysis (both corrected here)
1. **"Paper never used" was too generous.** Our text-mined training source stores DOIs as `https://doi.org/...`, and the October code did not strip that
   prefix. With a correct match, the October "blind + paper never used" subset (807 records) contains 252 records from papers that are in our Curie data.
2. **"Formula never seen" was not blind.** Our repository stores formulas as fractional strings (`Ca0.33La0.57Mn1O3`), while the external table uses
   integer ones (`Ca33La57Mn100O300`), and the October code compared strings. When compositions are compared instead, **1,998 of the 2,500 records (80%)
   are compositions that are already in our repository; only 502 are truly blind** (October: 1,302). 539 of the October "blind" records have exactly the
   same composition in the Curie training set.
   Side finding with the same cause, inside our own data: 30 Curie compositions are spelled two ways and fall on both sides of the formula-grouped split
   (27 of 4,541 Curie test rows, 0.6%; ordering 157 of 11,902 test rows, 1.3%; Ms none). This is small, but the Phase 6-8 splits are not perfectly
   formula-disjoint.

**Reproducibility fix (same day):** re-running the pipeline from the publication package showed that the paper-cluster *labels* depended
on Python's per-process hash seed. The clusters themselves (the partition) were identical, but the labels came from set iteration order,
so the seeded bootstrap assigned its weights to different clusters. Labels are now numbered by first appearance (test added), and all
results here were regenerated. Point estimates did not change; paper-cluster interval limits moved at Monte Carlo level (e.g. blind MAE
upper limit 152.3 → 154.3 K); no conclusion or wording-rule outcome changed. The results now reproduce bit-for-bit.

**Correction to the October report:** `Fe3125(Ir7Rh118)27` is not a garbled formula. It is Ir-substituted FeRh (Fe48Rh49Ir3), from a paper on FeRh
pseudobinaries, and 643 K is its Curie point. The October verified example (Fe86Zr11B3, 310 K predicted vs about 302 K published) is still truly blind
under the corrected definition (composition distance 0.010 to the nearest training formula).

## 1. Audit (`audit_flags.csv`, `audit_counts.csv`, `adjudication_*.csv`, `crossref_metadata.csv`)
All 834 DOIs were resolved with Crossref (titles, journals, abstracts where available). Every exclusion was decided without looking at any prediction.

| Check | Records | Action | Notes |
|---|---|---|---|
| A1 computational label | 60 | excluded | from 25 computational-only papers; the record is the paper's own subject or prediction (e.g. 19 ML-predicted 2D magnets, Chem 2022; 4 predicted MnGaX3 monolayers up to 910 K; ab initio Ti-doped ZnSe/CdSe). 22 more records only *cite* a value inside a computational paper and are kept (8 of them have no other source; removed in a sensitivity run). |
| A2 malformed composition | 18 | excluded | 4 mixed-scale normalisations (e.g. `Zr7Fe6230(Ni1335B2)2` = (Fe0.7Ni0.3)89Zr7B4 with boron reduced to 0.04 at.%); 12 impossible ionic stoichiometries (e.g. `Ba2La8MnFeO30`, `Ca3300La63Mn80(FeO15)20` = 87% Ca, a garbled copy of a record from the same paper); 2 alloy-family shorthands (`NdFeB`, `LaFeCoSi`). 2 more look mis-extracted but cannot be proven (A2s, kept; removed in a sensitivity run). |
| A3 duplicates | 0 | merge | no exact duplicate rows, and no two records with the same composition. The 2 garbled copies are counted under A2. |
| A4 training-label rules C1-C5 | 35 | excluded | 21 AFM-only formulas, whose values are Néel temperatures (e.g. the orthoferrites PrFeO3 707 K, GdFeO3, DyFeO3, YbFeO3, and EuTe); 13 with no magnetism-capable element (this also removes real ferromagnets such as ZrZn2, YTiO3 and K2AgF4, which the model's target definition excludes; kept in a sensitivity run); 1 below 1 K. |
| A5 not a magnetic Curie point | 0 | — | no title identifies a ferroelectric or superconducting transition for the record's compound. |
| A6 possibly not directly comparable | 160 (124 only from such papers) | flag only | nano 90, low-dimensional 34, pressure 13, film 13, composite 10, spin glass 3, irradiation 1. |
| A7 overlap with training sources | — | defines subsets | composition in repository 1,998; source DOI in our Curie data 1,457; **value identical (±0.5 K) to a value we hold for the same composition: 1,200** (the table and our data copy the same upstream compilations); near-copy blind compositions (distance < 0.01) 65. |
| A8 no DOI | 34 | flag only | textbook references. |

**Primary benchmark = 2,395 records** (105 excluded; overlaps between rules counted once). The excluded records were harder than average
(MAE: A1 135 K, A2 100 K, A4 165 K), so removing them lowers the error slightly. That is why each exclusion needs its stated reason.

## 2. Performance before and after the exclusions (`subset_metrics_bootstrap.csv`, Figure 1)
| Subset (corrected definitions) | n (original / primary) | Original table: MAE K [95% CI] / R² [CI] | Primary benchmark: MAE K [CI] / R² [CI] | 90% coverage (primary) |
|---|---|---|---|---|
| all | 2,500 / 2,395 | 69.5 [59.7, 85.0] / 0.77 [0.67, 0.84] | 66.5 [57.4, 82.0] / 0.79 [0.69, 0.85] | 0.925 |
| composition seen in repository | 1,998 / 1,930 | 59.7 [51.3, 72.2] / 0.79 | 57.7 [49.7, 68.8] / 0.80 [0.72, 0.87] | 0.933 |
|   seen + value copied from a shared compilation | 1,200 / 1,163 | 40.9 / 0.90 | 40.1 [32.1, 45.0] / 0.90 | 0.960 |
|   seen + value not copied | 798 / 767 | 88.1 / 0.68 | 84.5 [67.7, 110.1] / 0.70 [0.54, 0.80] | 0.890 |
| **composition never seen (blind)** | 502 / 465 | 108.3 [83.8, 157.2] / 0.65 [0.31, 0.78] | **102.7 [78.7, 154.3] / 0.69 [0.36, 0.81]** | 0.895 [0.83, 0.92] |
| blind + paper never used | 311 / 293 | 100.0 [81.0, 139.1] / 0.65 | 95.1 [76.7, 134.6] / 0.68 [0.35, 0.81] | 0.898 |
| blind + seen chemical system | 428 / 396 | 97.2 [80.5, 132.3] / 0.73 | 90.6 [75.7, 123.7] / 0.78 [0.57, 0.84] | 0.902 |
| **blind + unseen chemical system** | 74 / 69 | 172.4 [75.3, 261.5] / −0.18 [−0.87, 0.62] | **171.9 [69.1, 267.7] / −0.17 [−0.93, 0.66]** | 0.855 [0.66, 0.96] |
| blind + paper never used + unseen system | 38 / 37 | 127.9 / −0.14 [−2.33, 0.78] | 129.0 [56.1, 260.4] / −0.19 [−3.31, 0.76] | 0.757 |
| *October definition*: formula string never seen | 1,302 | 85.5 [72.5, 112.7] / 0.70 | — | 0.882 |

Reading:
- The audit exclusions change little (MAE −3 to −6 K); the corrected **definitions** change a lot. The truly blind error is about 103 K (median 64 K),
  not the 85 K reported in October. 60% of the "seen" records carry a value copied from a compilation we also used; on those the model scores R² 0.90,
  which is label recall, not prediction. Where the value was not copied, even seen compositions give MAE 85 K.
- Sensitivity runs (keep A4 records; remove A6-only records; remove records cited only in computational papers and suspect extractions) move the MAE
  by at most 2.5 K in the subsets with more than 250 records. They move it by up to 6.2 K in the unseen-system subset and 13 K in the 37-record strictest
  subset (`subset_metrics_bootstrap.csv`).
- Clustering choice: the pre-specified paper clusters put 727 records (29%) into one component, because multi-paper averages chain papers together
  (Amendment 2). First-DOI clusters give the same point estimates and slightly narrower intervals. Chemical-system clusters give much narrower ones
  (e.g. unseen-system MAE [121.5, 234.6], R² [−0.71, 0.23]).

## 3. Uncertainty of the generalization comparisons (`subset_comparisons.csv`)
Joint resampling of the clusters of both subsets; the share is the fraction of resamples in which the first subset is worse.

| Comparison (primary benchmark) | Clusters | MAE difference K [95% CI] (share worse) | R² difference [CI] (share worse) | Coverage difference [CI] |
|---|---|---|---|---|
| blind, unseen system (69) vs blind, seen system (396) | paper (pre-specified) | +81 [−27, +165] (0.89) | −0.95 [−1.69, −0.06] (0.99) | −0.05 [−0.25, +0.08] |
| same | first-listed DOI | +81 [−23, +164] (0.91) | −0.95 [−1.68, −0.08] (0.99) | −0.05 [−0.23, +0.07] |
| same | chemical system | +81 [+29, +145] (1.00) | −0.95 [−1.50, −0.53] (1.00) | −0.05 [−0.19, +0.07] |
| blind (465) vs seen composition (1,930) | paper | +45 [+22, +94] (1.00) | −0.12 [−0.44, +0.01] (0.96) | −0.04 [−0.11, −0.00] |
| blind + paper never used: unseen (37) vs seen system (256) | paper | +39 [−42, +170] (0.77) | −0.95 [−4.95, +0.06] (0.96) | −0.16 [−0.45, +0.04] |

**How confidently can the generalization failure be stated?** The prespecified wording rule was: say "no skill beyond the mean" only if the upper CI
limit of R² is ≤ 0.2. With paper clusters the R² interval for unseen systems is [−0.93, 0.66], and R² is below 0 in 70% of resamples. The rule
therefore applies the weaker wording: **skill in unseen chemical systems is much weaker than in seen systems, with wide uncertainty.** The drop in R²
relative to seen systems is resolved under every clustering (CI excludes 0). The MAE increase (+81 K) is probable (89% of resamples) but its paper-cluster
interval includes 0. With only 18–26 independent papers the subset cannot pin down the size of the gap. The strictest subset (37 records, 12 paper
clusters) carries almost no information (R² interval −3.4 to 0.8).

## 4. Chemical similarity to the training materials (`similarity_*.csv`, Figures 2-3)
Metric fixed in advance: composition distance = total-variation distance between element-fraction vectors (0 = identical composition, 1 = no common
element) to the nearest of the 23,757 training-row formulas. Secondary: z-scored Tier 1 descriptor distance. Records from one paper are dependent, so all
intervals come from the paper-cluster bootstrap.

On the **465 truly blind records** (primary benchmark):
- Spearman ρ(distance, absolute error) = **0.28 [0.10, 0.49]**. Descriptor distance gives 0.21 [0.01, 0.31], k = 5 nearest gives 0.29 [0.11, 0.49], and
  the all-Curie reference gives 0.28 [0.10, 0.50].
- Spearman ρ(distance, interval width) = 0.17 [−0.05, 0.39]; with descriptor distance 0.28 [0.12, 0.43]. The intervals do widen, but less clearly than
  the errors grow.
- By distance quartile (edges 0.015 / 0.033 / 0.083): MAE **62 → 80 → 106 → 165 K**; width 388 → 380 → 424 → 529 K; coverage **0.95 → 0.91 → 0.87 →
  0.85**. Farthest minus closest quartile: MAE **+103 K [+31, +176]** (worse in more than 99.9% of resamples), coverage **−0.10 [−0.23, −0.01]**, width +141 K
  [−53, +296].
  -> Error rises with chemical distance, and the normalized-conformal intervals widen too little to keep 90% coverage for the most dissimilar quarter.
- Does distance explain the unseen-system failure? Partly. Unseen-system records are farther away (median distance 0.10 vs 0.03). Seen-system blind
  records in the same distance range give MAE 109 K and R² 0.75, against 172 K and −0.17 for unseen systems. Distance accounts for about a fifth of the
  MAE gap, and R² stays lower (difference −0.92 [−1.66, −0.05]). Not having seen the element combination at all costs more than distance alone.
- Over all primary records, including exact matches, ρ(distance, error) = 0.28 [0.21, 0.38]. The k = 5 version is slightly negative (−0.11). Post-hoc
  diagnostic (Amendment 2): among exact matches, isolated compounds with few neighbours mostly carry copied values (about 72%) and very small errors.
  Among non-exact matches the k = 5 rank correlation is about 0, while MAE still rises from 69 to 104 K across quartiles. The pooled k = 5 sign is
  therefore a mixture effect and is not used as evidence.

## 5. What can be claimed
- On compositions the model has never seen, Curie temperature is predicted with MAE about 100 K (95% CI roughly 79-154 K), R² about 0.7, and 90%
  intervals that cover about 89-90%. That is clearly worse than on seen compositions (+45 K [22, 94]).
- Error grows with chemical distance from the training set, and interval coverage falls to about 85% for the most dissimilar quarter.
- In chemical systems absent from training, accuracy is much weaker (R² −0.17, CI −0.93 to 0.66). The data cannot say whether skill is truly zero:
  69 records from 18–26 papers are too few.
- Benchmark quality: the table is a text-mined compilation. 80% of its compositions and 48% of its values already exist in our training sources, and 4% of
  records are computed, malformed or outside the target definition. Any external number quoted without these corrections overstates generalization.
