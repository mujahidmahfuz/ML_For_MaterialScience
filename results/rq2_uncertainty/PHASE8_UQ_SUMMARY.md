# Phase 8 — Uncertainty quantification and explanation stability: results (2026-10-18)

Design and criteria: `PLAN.md` (fixed before any model was fit). Code: `src/phase8_uq.py` (12 unit tests), `run_phase8_regression_uq.py`, `run_phase8_ordering_uq.py`, `run_phase8_xai_stability.py`. Nominal level 90%; calibration = 20% of train formulas; test touched once.

## UQ-R (regression)
| Target (test N) | Split conformal | Normalized | CQR |
|---|---|---|---|
| Curie v1.3 (4,541) | 95.1% [93.9, 96.1], width 552 K | **91.7%** [90.4, 92.9], 366 K | 92.5%, 438 K |
| Ms moment (13,129) | 90.4%, width 12.8 | 90.3%, 11.6 | 89.4%, 9.8 |

- Curie: only normalized conformal is within ±2 points of 90%. Constant-width intervals cover the hardest decile at 79%.
- Ms: all three are within ±2 points marginally, but split conformal under-covers the hardest decile (49%), the highest-moment third (74%) and Oxides (84.8%). Normalized/CQR remove most of this (flagged: decile 01 at 80.9%, and for CQR the hardest decile 78% and highest third 83%).
- Source shift (Curie, curated → text-mined): split −13 points (76.9%), CQR 80.3%, normalized 85.1%. Shift is a result, not a failure of the study.
- **Ms CQR JARVIS→MP coverage of 35% is real, not a bug** (reproduced from saved arrays). 37.8% of MP test rows have moment exactly 0 and the lower quantile sits at about −0.001, so a negative CQR correction (−0.21, from JARVIS calibration) excludes nearly all of them (coverage among exact zeros 65% → 0.5%). Limitation: CQR with a negative correction is fragile when the target has a point mass at a boundary. Split/normalized stay about 88%.

## UQ-C (ordering, v1.3 Tier 1, test N = 11,902)
- Probabilities (ECE, 95% formula-bootstrap CI): raw balanced-weight 0.058 [0.051, 0.068]; prior-corrected 0.093 [0.083, 0.102] (worse); prior-corrected + temperature (T = 1.65, fitted on calibration only) **0.016 [0.012, 0.027]**, Brier 0.309, NLL 0.557 (raw 0.570).
- Marginal LAC sets: coverage 89.3% but per class FM 95.2 / NM 97.3 / **AFM 58.1 / FiM 52.8** — the headline hides the weak classes. Class-conditional sets: 89–92% per class, mean size 1.34 → 1.58.
- Source shift (prior-corrected): MP-calibrated → experimental test: marginal 83.5%, class-conditional 97.1% (over-covers, sets 1.83). Experimental-calibrated → MP: marginal 93.7% but AFM 37.5%. Experimental test rows contain no NM; experimental calibration lacks ≥100 NM rows, so NM is excluded there.

## XAI-stability (10 Phase 7 splits, refit + TreeSHAP per split; hyperparameters not re-tuned)
Ordering has no Phase 7 split set: same seeds/rule, formula-mean class code used for stratification (documented extension). Ms uses v1.2 (inputs unchanged).
| Target / tier | mean pairwise Spearman (min) | mean top-10 overlap (min) | top-1 feature (splits) |
|---|---|---|---|
| Ordering T1 | 0.983 (0.972) | 8.7 (7) | magnetic_element_fraction (10/10) |
| Ms T1 | 0.978 (0.953) | 8.7 (8) | magnetic_element_fraction (10/10) |
| Curie T1 | 0.938 (0.897) | 7.0 (5) | group_variance (5/10) – unstable |
| Curie T3 | 0.908 (0.829) | 5.9 (3) | group_variance (5/10) |

- Ordering and Ms: rankings and family order are stable (Tier 3 family-rank ranges ≤ 1–2 places; magnetic-element content #2 ordering, #1 Ms; Ms Structural packing #3 in every split).
- **Curie: global rank correlation is high but the leading features and family order are not.** Atomic-size (23% ± 8) and Magnetic-element (20% ± 8) trade ranks 1–3; transition_metal_fraction, group_variance, valence_electron_concentration, unpaired-electron proxy and fraction_Fe all move by several places. Statements such as "X is the top Curie driver" are not supportable; only family-level statements with intervals (`xai_stability/xai_family_share_stability.csv`) are. Stable for Curie: Light-element content last (12/12 splits), Structural packing 3rd–5th, d/f-valence 2nd–4th.
- Files: `xai_stability/xai_stability_summary.csv`, `xai_family_share_stability.csv`, `xai_top_feature_rank_stability.csv`.

## Caveats
Single frozen split for UQ (no repeated-split coverage); conformal guarantee is marginal and approximate under formula grouping; bootstrap CIs over formulas, SHAP intervals over 10 splits (not bootstrap). Bias-reduction, leave-system-out and R10 remain open.
