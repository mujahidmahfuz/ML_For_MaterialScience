# Phase 8 — Uncertainty quantification and explanation stability (plan, written before any Phase 8 model was fit)

Inputs: Analysis Dataset v1.3 (ordering, Curie) and the unchanged Ms target; frozen formula-grouped splits; Tier 1/2/3 predictors; the Phase 6/7 estimators. Nothing in Phase 6/7 or the dataset folders is modified. Outputs go to `EDA/11_phase8_xai_uq/`.

## Questions
1. **UQ-R (regression: Curie, Ms).** Do prediction intervals reach their nominal coverage on formulas the model has never seen, and do they keep it for subgroups (material family, label source, target range) and under a change of data source?
2. **UQ-C (classification: ordering).** Are the predicted probabilities calibrated, and do conformal prediction sets reach their coverage, including for the weak classes (AFM, FiM) and across label provenance?
3. **XAI-stability.** Are SHAP rankings and family shares stable across repeated formula-grouped splits and model seeds, so that a statement like 'symmetry is the 2nd most important family' carries an uncertainty?

## Design (fixed in advance)
- **Calibration data.** Whole formulas are carved out of the *training* partition (20% of train formulas, seeded) as a calibration set; the model is fit on the remaining 80%; the validation partition keeps its Phase 6 role (hyperparameter selection already done there) and the test partition is touched once. Calibration, proper-train and test share no formula.
- **Hyperparameters:** the Phase 6/v1.3 selected XGBoost settings per target (no new tuning).
- **Nominal level:** 90% (alpha = 0.10); coverage-vs-nominal curves for alpha 0.05–0.50.
- **Regression methods:** (a) split conformal, constant width; (b) normalized conformal, width scaled by a cross-fitted difficulty model; (c) conformalized quantile regression (CQR, XGBoost quantile objective). Reported: marginal coverage, mean/median width, interval (Winkler) score.
- **Classification methods:** (a) raw vs temperature-scaled probabilities (ECE, Brier, NLL); (b) conformal prediction sets (LAC), with per-class coverage and set size.
- **Conditional checks:** coverage by material family (Transition Metal, Rare Earth, Oxide, Intermetallic), by label source / provenance, and by predicted-difficulty decile.
- **Shift tests:** calibrate on one label source, test on another (Curie: text-mined vs curated experimental; ordering: computed vs experimental). Coverage loss under shift is a *result*, not a failure of the study.
- **Explanation stability:** TreeSHAP for the XGBoost model on each of the 10 prespecified Phase 7 splits (matched sets), then Spearman/top-k stability of mean |SHAP| and of family shares, with bootstrap intervals over splits.

## Prespecified criteria
- In-distribution (formula-held-out) marginal coverage is judged adequate if within ±2 percentage points of 90% on the test set; the 95% bootstrap interval of coverage (resampling formulas) must be reported.
- A subgroup is flagged under-covered if its coverage is more than 5 points below nominal with at least 30 distinct test formulas.
- ECE is reported with a bootstrap interval; no recalibration claim without a held-out comparison.
- Explanation-stability claims need the rank correlation across splits, not a single split.

## Not in scope (stated so nobody assumes otherwise)
New algorithms, new features, further target cleaning (roadmap R10 stays open), deep-ensemble/Bayesian UQ (compared only if conformal results warrant it), counterfactual explanations, and the bias-reduction work (a separate step that depends on these results).

## Order of work
1. UQ-R pilot on Curie (v1.3) and Ms: conformal module + unit tests, then runs.
2. UQ-C on ordering.
3. Shift and conditional-coverage analysis.
4. XAI-stability over the 10 splits.
5. Summary document and claims-register addendum.

## Known risks
- Conformal guarantees assume exchangeability; formula-grouped calibration is exchangeable with a formula-grouped test only approximately, and not at all under source shift — the shift tests measure exactly that gap.
- Curie has few distinct formulas per family (e.g. Rare Earth test n small), so conditional coverage intervals will be wide.
- XGBoost results depend on thread count; Phase 7's pinned 16 threads is kept.
