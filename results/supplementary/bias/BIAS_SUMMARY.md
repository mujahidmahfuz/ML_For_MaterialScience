# Phase 8b — Bias audit and reduction: results (2026-10-18)

Plan: `PLAN.md` (written before fitting). Code: `src/run_phase8_bias.py`. Tier 1, v1.3, frozen split, XGBoost with the selected hyperparameters, fit on train only (baseline here: ordering macro-F1 0.713, Curie MAE 75.8 K). Intervals are paired formula-bootstrap (300). Full tables: `ordering/bias_metrics.csv`, `curie/bias_metrics.csv`.

## Step 1 — audit
| Gap | Ordering | Curie (MAE, K) | Judged against the plan's rule |
|---|---|---|---|
| B1 class | AFM recall 0.598, FiM 0.511 vs FM 0.789, NM 0.908 | — | **material** (AFM, FiM) |
| B2 family | Oxide macro-F1 0.671 vs overall 0.713 (−0.042) | Intermetallic 83.5 vs overall 75.8 (+10%, CI wide); Rare Earth best at 48.2 | not material by the plan's rule (ordering < 0.05; Curie interval overlaps) |
| B3 provenance | MP 0.595 vs other 0.546 (within-subgroup macro-F1, not comparable to overall) | curated 64.3 vs **text-mined 105.3 (+39%)** | **material for Curie** |
| B4 formula dominance | equal-weight 0.694 vs pooled 0.713 | 76.2 vs 75.8 | not material |
| B5 target range | — | high-Tc third 99.9 (+32%), middle 52.5 | **material (high-Tc)** |

## Step 2 — interventions (delta vs baseline, 95% paired CI)
Ordering:
- **I1 formula weights:** no gain (overall −0.003 [−0.009, 0.003], AFM recall −0.013 [−0.034, 0.009]). Not kept.
- **I2 provenance weights:** AFM recall **+0.049 [0.022, 0.079]**, overall −0.002 [−0.009, 0.006]. Modest gain, kept.
- **I3 class offsets (fitted on validation):** AFM recall **+0.051 [0.031, 0.074]** but FiM recall **−0.019 [−0.028, −0.012]**; overall +0.001. A trade-off, not a free gain.
- **I4 formula weights + offsets:** AFM recall **+0.112 [0.074, 0.155]**, FiM −0.019 [−0.035, −0.004], overall −0.004 [−0.014, 0.009]. Largest AFM improvement.
- No intervention improved FiM, so the FiM gap is **not narrowed**. The Oxide gap is unchanged (CI includes 0).

Curie: neither I1 nor I2 changes any gap; every delta CI includes 0 (text-mined MAE −2.4 [−9.0, 3.6] with I1, −1.6 [−6.3, 3.1] with I2).

## Reading
1. The AFM recall gap is partly a decision-threshold problem and can be narrowed (+5 to +11 points) at an overall cost that stays within the CI. FiM trades off against AFM, so re-weighting alone cannot fix both. Report per-class recall, not only macro-F1.
2. The Curie text-mined and high-Tc gaps are **not removed by reweighting**. They look like label noise and extrapolation rather than sampling imbalance; the remedy is on the data side (cleaner labels, more high-Tc examples), which is out of scope here.
3. Formula dominance does not materially distort pooled metrics.
4. Nothing here shows bias "removed": only the AFM recall gap is demonstrably narrowed.

## Caveats
Single frozen split (no repeated-split intervals for the interventions); offsets and weights tuned on one validation set; subgroup macro-F1 is computed within the subgroup, so it is not comparable to the overall value; test used once per variant. Ms not included (point mass at zero is a separate issue).

## Addendum — repeated-split check of the AFM gain (10 splits, ordering full v1.3 population; `ordering/repeated_split_summary.csv`)
Criterion (fixed in PLAN.md before the run): t-interval of the per-split mean delta excludes 0 AND delta > 0 in >= 70% of splits.
- **I2 provenance weights: stable.** AFM recall +0.043 [0.032, 0.053], positive in 10/10 splits; cost FM -0.010 [-0.014, -0.006], NM -0.007; overall macro-F1 -0.002 [-0.004, 0.000]; FiM unchanged.
- **I3 class offsets: borderline.** AFM +0.027 [0.001, 0.053], positive in 7/10 (sign test p = 0.34); NM recall -0.022 [-0.034, -0.010]; overall unchanged. Meets the letter of the criterion only barely; not a firm result.
- **I4 formula weights + offsets: NOT stable.** AFM +0.029 [-0.022, 0.081]; FiM +0.024 [-0.003, 0.051]; NM -0.018. The single-split +11.2 points was an optimistic draw (AFM ranged 0.49-0.72 across splits).
- Conclusion: only the provenance-weighting gain survives repetition (about +4 points AFM at ~1 point of FM/NM recall); the earlier "+11 points" must not be quoted. FiM gap remains un-narrowed.
