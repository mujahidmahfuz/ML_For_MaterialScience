# Round-3 review checked against the code, data and results (2026-11-14)

The round-3 report (`review_report.md`) was written from the manuscript. At the user's request, each point was then checked against what
already exists in the project after the round-1 revision: the revision plan and its deviations log (`final/revision/PLAN.md`), the
revision outputs (`paper/results/revision/`, `final/revision/outputs/`), the final checks (`final/outputs/`), the Phase 8 follow-ups
(`EDA/14_phase8_peratom/`), the analysis configuration (`EDA/00_config/analysis_config.yaml`) and the source data.

Status codes:
- **DONE-REPORTED**: done, and the manuscript reports it; the review point is withdrawn or reduced to wording.
- **DONE-NOT-SHOWN**: the analysis exists; only the manuscript or SI needs the numbers.
- **DECIDED**: handled by an earlier documented decision; only a residual remains.
- **OPEN**: no analysis exists yet.

| Item | Status | Evidence | What is left |
|---|---|---|---|
| R1-1 small, identical grids | **OPEN** | `analysis_config.yaml` `models.grids`: gradient boosting 2 x 2 (learning rate x leaf nodes), XGBoost 2 x 2 (depth x learning rate), 500 trees/iterations. No larger-grid or tier-specific tuning run exists anywhere. | Sensitivity run for the primary Curie Tier 1 vs Tier 3 contrast. |
| R1-2 XGBoost non-determinism | **DONE-REPORTED** (reduced to wording) | `final/outputs/check3_ms_threads/`: mean absolute prediction change between thread counts = 0.448 / 0.545 / 0.522 (Tier 1/2/3); between seeds at fixed threads = 0.459 / 0.546 / 0.533, i.e. the same. HistGradientBoosting changes 0.000. So the "25% of MAE" is ordinary seed variation from XGBoost row/column subsampling (0.8), not instability. The manuscript already averages 8 realizations for Curie and the moment and marks single-realization results. | One clause in Methods: the spread equals the seed-to-seed spread caused by subsampling (the defined quantity is `mean_abs_diff_pct_of_mae`). The review's "high-variance model" concern is withdrawn. |
| R1-3 noisy join (space-group test) | **OPEN** (disclosed as dropped) | PLAN.md A6(e) and deviations log: dropped before results were seen; the manuscript says the explanation is untested. Feasibility checked now: the source schema has `space_group`; 8,840 of 29,740 valid Curie records carry one, 842 of the 4,602 matched (Tier 3) records. A spot comparison with `p3_spacegroup_number` shows agreements (I4/mcm 140, P2_1/n 14, Fm-3m 225, P2_13 198) and mismatches (Pnma vs 63, Fd3m vs 74, Im3m vs 225, Pm3m vs 225). | Feasible but small (at most 842 records before requiring a match, so roughly 60-80 test rows per split): it can show a large gain, not settle the question. Symbol parsing is needed (e.g. "Fd3m", "Im3m" written without bars). |
| R1-4 three ordering macro-F1 values | text | 0.727 (frozen split), 0.692 (10 splits, SI Table 7), 0.712 (leave-system-out setting): all in the results; the setups differ. | One explanatory sentence. |
| R1-5 end-to-end graph network | **OPEN** (judgement) | Only the frozen CHGNet embedding exists (A6). | Optional. |
| R1-6 related work on OOD protocols / materials conformal | **OPEN** | Not in `references.bib`. | Find and verify sources before citing. |
| R2-1 MAGNDATA as ordering ground truth | **OPEN** | MAGNDATA (2,208 rows, `new_datasets/magndata_magnetic.csv`) is not referenced in the A2 scripts or outputs (`final/revision/scripts/a2_provenance.py`, `paper/results/revision/a2_provenance/`). | New analysis; data in hand. |
| R2-2 per-cell moment as primary target | **DECIDED** (residuals remain) | PLAN.md A5 declared m_fu the "new primary target"; the manuscript kept m_cell primary and now justifies it (Methods: what databases report; comparisons configured in advance). Round 2 (`round2/traceability_matrix.md`, RR7) had flagged this deviation as unlogged. | (a) Log the A5 deviation in PLAN.md; (b) round-2 residuals still open: quantify "most entries were computed from ferromagnetic initial configurations"; explain why a site count helps for the intensive per-formula-unit target. |
| R2-3 C5 sensitivity numbers | **DONE-NOT-SHOWN** | `EDA/14_phase8_peratom/SUMMARY_SITECOUNT_PERATOM_C5.md` section 3: without C5 (N = 30,059) Tier 1 test MAE GB 81.2 K (76.2 with C5), XGB 72.7 K (75.4), R2 0.77-0.79 (0.78); the 42 test rows only C5 removes are not harder (XGB 54.8 K vs 72.9 K). | Put these numbers in a Supplementary table or one Methods sentence. |
| R2-4 external benchmark = ferromagnets only | partly | Methods states "2,500 ferromagnets". | One Results sentence on what the external test cannot say (ferrimagnets, Neel temperatures). |
| R2-5 sublattice descriptors on MP structure | text | A6 uses the MP structure of the same entry (Methods). | One sentence linking to the join limitation. |
| R3-1 power / equivalence | **partly DONE** | A1 computed the minimum detectable effect (`mde80`: 26.6 K clipped ridge, 39 K GB, 56 K XGB for Curie) and the manuscript reports it. No pooled or precision-weighted estimate across algorithms; no extra splits. | Pooled estimate (cheap, from saved per-split results); abstract wording. |
| R3-2 Holm family member for Curie ridge | **CONFIRMED + unlogged deviation** | `paper/results/revision/a1_tier_inference.csv`: the unclipped `linear` row (mean -825.2 K) is in family "primary (Tier 1->3)" with holm_p 1.0; `linear_clip` is "secondary". PLAN.md A1 says the clipped contrast "replaces the unstable Ridge row". The manuscript describes the implementation correctly, but the plan was not followed and the deviation is not in the deviations log. | Either recompute Holm with the clipped member, as planned (the table note already gives the result: 0.740, other eight unchanged), or log the deviation. |
| R3-3 BCa with few clusters | **DONE-REPORTED** (reduced to wording) | Supplementary Table 4 gives percentile and BCa intervals under three clusterings; the conclusions agree. | One Methods sentence that intervals with ~18 clusters are approximate. |
| R3-4 "stable" rule is a convention | text | PLAN.md defines the rule. | Wording. |
| R3-5 distance-matched comparison not displayed | **DONE-NOT-SHOWN** | `paper/results/rq3_generalization/external_benchmark/AUDIT_RESULTS.md`: seen-system blind records in the same distance range MAE 109 K, R2 0.75; R2 difference vs unseen systems -0.92 [-1.66, -0.05]; distance explains about a fifth of the MAE gap. The manuscript's numbers (R2 0.75; rho 0.28 [0.10, 0.49] for blind records) match this file. | Add to Extended Data Table 6 or Supplementary Table 3. |
| R3-6 wording-rule threshold | **DONE-REPORTED** | Disclosed in Methods (fixed after earlier subset results). | None beyond calling 0.2 a convention. |
| R4-1 reusable benchmark | **largely exists** | The reproducibility package (`paper/`) already ships the frozen datasets, grouped splits, audit flags, result files and `scripts/fetch_external_benchmark.py` (SHA-256-pinned retrieval of the external table, which cannot be redistributed). | Framing: present it as a benchmark with an evaluation entry point; licences still unresolved (SI Table 10). |
| R4-2 screening on internal sets | **OPEN** | A9 covers only the 465 blind external records. | New analysis (cheap: per-split predictions and intervals exist from A4). |
| R4-3 planned vs post hoc table | **material exists** | PLAN.md (written before A1-A13, with deviations log), Phase 7 claims register, `final/claims_revisions.md`. | Compile into one SI table. |
| R4-4 human spot check of the title screen | **OPEN (author task)** | `paper/manuscript/review/curie_spotcheck_32.csv`: 32 records prepared, `your_verdict` filled for 0 of 32. | Authors fill the 32 verdicts; then report agreement in Methods. |
| E-1 abstract intervals vs sets | **CONFIRMED** | Abstract sentence verified in `manuscript.tex`. | Rewording. |
| E-2 SI Tables 2 and 10 not cited | **CONFIRMED** | Only Tables 1, 3-9, 11, 12 are cited individually. | Two citations. |
| E-5 mandatory statements | **OPEN (by choice)** | Blank placeholder block in `manuscript.tex`. | Authors. |

## Net effect on the round-3 decision

- Withdrawn or reduced to wording: R1-2 (thread noise is seed noise and is already handled), R3-3, R3-6.
- Already done, numbers only need to appear: R2-3, R3-5; the material for R4-1 and R4-3 exists.
- New findings from this check: **R3-2 is a real, unlogged deviation from PLAN.md** (the clipped ridge contrast was meant to replace the
  unstable one in the Holm family); **the A5 deviation behind R2-2 is still not logged**; the round-2 residuals on R2-2
  (FM-initialization frequency; why a site count helps an intensive target) are still open.
- Genuinely open analyses: R2-1 (MAGNDATA), R1-1 (tuning budget), R3-1 (pooled estimate), R4-2 (internal screening), R1-3 (feasible but
  small). Author tasks: R4-4 spot check, E-5 statements.

The decision stays **Major Revision**, because R2-1 and R1-1 require new analysis, but the workload is smaller than the report alone
implies: about half of the items are wording or moving existing numbers into display items.
