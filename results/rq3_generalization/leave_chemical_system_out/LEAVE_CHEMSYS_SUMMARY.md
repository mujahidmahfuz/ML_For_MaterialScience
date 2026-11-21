# Phase 8 — leave-chemical-system-out test (2026-10-18)

Code: `src/run_phase8_leave_chemsys.py`. For each of the 10 Phase 7 split seeds the same size-aware, stratified 70/15/15 split is made twice on the same population: grouped by reduced_formula (reference) and grouped by chemical system (sorted element set, e.g. Fe-O). Tier 1 XGBoost, selected hyperparameters, fit on train+validation, test scored once. Curie v1.3 (29,740 rows, 5,334 systems), ordering v1.3 (79,125 rows, 36,848 systems), Ms per cell v1.2 (87,513 rows, 41,212 systems).

**Leakage in the reference scheme:** under formula-grouped splits, 78% (Curie), 65% (ordering) and 65% (Ms) of test rows belong to a chemical system that also appears in training. Under the new scheme this is 0% in every split (asserted). Test size is 15% in both.

| Target | Metric | Formula-grouped | System-grouped | Paired delta [95% t-interval] | Worse in | Stable degradation? |
|---|---|---|---|---|---|---|
| Ordering | macro-F1 | 0.712 | 0.684 | **−0.028 [−0.041, −0.016]** | 10/10 | **yes** |
| Ordering | FiM recall | 0.528 | 0.467 | **−0.060 [−0.085, −0.036]** | 10/10 | **yes** |
| Ordering | FM recall | 0.777 | 0.758 | −0.019 [−0.034, −0.005] | 8/10 | yes |
| Ordering | AFM recall | 0.598 | 0.569 | −0.029 [−0.067, +0.009] | 8/10 | no |
| Ordering | NM recall | 0.912 | 0.912 | +0.000 | 4/10 | no |
| Curie | MAE (K) | 99.2 | 101.9 | +2.7 [−16.8, +22.2] | 5/10 | no |
| Ms per cell | MAE (μB) | 2.591 | 2.663 | +0.073 [−0.009, +0.154] | 7/10 | no |
| Ms per cell | R² | 0.681 | 0.683 | +0.002 | 6/10 | no |

## Reading
1. **Ordering degrades stably** when whole chemical systems are unseen (about 3 points of macro-F1; FiM recall loses 6 points). The headline ordering macro-F1 partly reflects interpolation between near-neighbour compositions in the same system.
2. **Ms: small, not stable** (MAE +2.8%, interval touches 0, 7/10 splits worse). The model largely generalises across systems, with a possible small cost.
3. **Curie: no detectable change, but the test is weak.** Per-split Curie MAE varies by tens of K between splits (interval ±20 K), so a drop of a few K could not be detected. Do not read this as proof of system-level generalisation.
4. The test sets of the two schemes contain different materials, so deltas are paired by seed but not by row.

## Caveats
Tier 1 only; XGBoost only; chemical system is one definition of "unseen" (leave-one-element-out would be harsher and was not run); 10 splits reuse the same data.
