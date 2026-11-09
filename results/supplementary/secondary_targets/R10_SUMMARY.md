# R10 secondary-target cleaning (dataset v1.4) - results (2026-10-18)

Rules: `00_config/v1_4_curation_rules.yaml`; builder `src/build_analysis_dataset_v1_4.py` (6 tests); data `datasets/v1.4/` (quarantine in `excluded/`); CV re-run `src/run_v14_secondary.py` (same 5x3 formula-grouped CV, Tier 1, as Stage 7). Table: `secondary_cv_v12_vs_v14.csv`.

Removed (screens, not proofs): Ms-mass 1/4,318 (257 emu/g, above the Fe-Co ceiling); Ms-volume 9/788 (5 above 2.0e6 A/m, 2 exact zeros, 2 mass-unit mis-parses A.m^2/kg filed as A/m); K1 15/1,862 (|K1| > 5e7 J/m^3, mostly erg/cm^3 or prefix errors). Ms-per-cell moment, Curie, ordering unchanged. The moment target is documented as "DFT total magnetic moment per unit cell (0 K)"; MP total_magnetization verified per CELL by API (Fe3O4: 28 uB per 14-site cell, 14 per f.u.), so the Phase 3 dictionary label "muB/f.u." for p3_total_magnetization is wrong.

| Target (tree models) | v1.2 R2 [95% CI] | v1.4 R2 [95% CI] | Reading |
|---|---|---|---|
| K1 raw, gradient boosting | 0.129 [-0.103, 0.193] | **0.377 [0.217, 0.514]** | now distinguishable from the mean (v1.2 interval included 0) |
| K1 raw, XGBoost | 0.176 [-0.098, 0.283] | **0.356 [0.198, 0.476]** | same |
| K1 raw, training-mean MAE | 4.18e6 | 2.23e6 | the 15 impossible values dominated the old error scale |
| K1 signed-log10, GB / XGB | 0.204 / 0.204 | 0.171 / 0.166 [XGB -0.040, 0.315] | no gain; log version is robust to the removed values; XGB interval now includes 0 |
| Ms-volume, GB / XGB | 0.455 / 0.444 | **0.567 / 0.565** [0.47, 0.65] | clear improvement (9 rows removed) |
| Ms-mass, GB / XGB | 0.631 / 0.630 | 0.619 / 0.620 | unchanged (1 row) |

Cautions: the v1.2 and v1.4 columns describe different (cleaned) targets, not the same rows; raw-K1 and Ms-volume R2 are sensitive to a few extreme values, so the gain reflects removal of impossible values, not a better model; the linear (ridge) models still fail catastrophically on K1 and Ms-volume (R2 down to -2,900; non-finite/extreme inputs) and must not be quoted; matched-tier Stage 7 part (N 404/247/252) was not re-run and no tier claim was made before either. Stage 7 remains exploratory.
