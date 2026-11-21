# Scripts

## Layout
| Path | What it is |
|---|---|
| `verify_checksums.py` | Checks all data and result files against `../CHECKSUMS.sha256`. |
| `setup_workspace.py` | Creates a run workspace for the pipeline code (hard links, no extra disk space). |
| `fetch_external_benchmark.py` | Downloads the third-party external Curie table into a workspace and verifies its SHA-256. |
| `requirements.txt` | Pinned Python environment. |
| `pipeline/analysis/` | Analysis code: dataset builders, splits, models, Phase 7 validation, Phase 8 uncertainty / interpretation / generalization. |
| `pipeline/final_checks/` | The four final robustness checks (Curie inference, ordering 10 splits, XGBoost threads, per-atom Ms). |
| `pipeline/external_benchmark/` | Tier 1 descriptor calculator, blind prediction of the external table, and `audit/` (audit, similarity and grouped bootstrap). |
| `pipeline/config/` | Analysis settings, curation rules, Tier 1/2/3 predictor lists. |
| `pipeline/tests/` | Unit tests of the analysis code (the audit tests are in `pipeline/external_benchmark/audit/`). |
| `pipeline/PATCHES.md` | The only differences from the code that produced the results (absolute paths, API-key lookup). |

## 1. Rebuild the figures and the paper (minutes, no model fitting)
From the repository root:
```
pip install -r scripts/requirements.txt
python scripts/verify_checksums.py
cd manuscript
python make_figures.py     # figures from ../results
python build.py            # manuscript, supplementary and review PDFs (needs tectonic)
```

## 2. Re-run the analyses (hours)
The pipeline code expects the original project layout, so it runs in a workspace outside the package:
```
python scripts/setup_workspace.py --workspace ../pi_ai_mm_workspace
python scripts/fetch_external_benchmark.py --workspace ../pi_ai_mm_workspace     # needed for RQ3 only
cd ../pi_ai_mm_workspace/EDA/src
python -m pytest ../tests -q
```
**Leave `OMP_NUM_THREADS` unset.** XGBoost results depend on the thread count, which acts like a random seed (mean prediction change about 25% of the MAE). The published runs used 16 threads (`phase7_validation.XGB_N_JOBS`); Ridge and HistGradientBoosting do not depend on it. Conclusions in the paper are stated across splits and seeds.

Unless a different folder is given, commands run from `<workspace>/EDA/src` with `python -X utf8`. Outputs go into the workspace; the right-hand column names the package copy to compare with. Hyperparameters are never re-tuned: every stage reads the selections frozen in `data/reference_inputs/`.

**NEMAD values:** this private repository includes the values of the two NEMAD literature tables, so every step can be re-run. They may not be redistributed; see `../data/README.md` before making anything public.

### Dataset (optional; the frozen versions are in `data/`)
| Step | Command | Compare with |
|---|---|---|
| v1.3 from v1.2 | `python build_analysis_dataset_v1_3.py` | `data/analysis_dataset/v1.3`, `data/splits/v1.3` |
| v1.4 from v1.3 | `python build_analysis_dataset_v1_4.py` | `data/analysis_dataset/v1.4`, `data/splits/v1.4` |

### RQ1: physics descriptors (`results/rq1_physics_descriptors/…`)
| Step | Command | Compare with |
|---|---|---|
| Tier 1 baselines and Tier 1→2, full populations | `python run_v13_full_population.py curie`; `python run_v13_full_population.py ordering` | `baselines/`, `tier2_full_population/` |
| Curie C5 sensitivity | `python run_v13_curie_c5_sensitivity.py` | `tier2_full_population/curie_c5_*` |
| Matched tiers, Curie (10 splits) | `python run_phase7_multisplit.py --dataset v1.3 --target curie --splits frozen 0 1 2 3 4 5 6 7 8 9 --kinds main diag`; then `python phase7_run_aggregate.py --dataset v1.3 --targets curie` | `matched_tiers/robustness_summary_curie_v1.3.csv` |
| Matched tiers, Ms (10 splits) | `python run_phase7_multisplit.py --target ms_moment --splits frozen 0 1 2 3 4 5 6 7 8 9 --kinds main`; `python run_phase7_multisplit.py --target ms_moment --splits 0 1 2 3 4 5 6 7 8 9 --kinds diag restricted addone`; then `python phase7_run_aggregate.py` | `matched_tiers/robustness_summary_curie_ms_v1.2.csv` |
| Matched tiers, ordering; label provenance | `python run_v13_ordering.py baseline`; `… slices`; `… transfer`; `… matched --splits frozen 0 1 2 3 4`; `… matched --splits 5 6 7 8 9 --variants tier1 tier2 tier3`; `python agg_v13_ordering.py` | `matched_tiers/ordering_*`, `../rq3_generalization/label_provenance/` |
| Final check 1: Curie inference, thread noise | `python ../../final/scripts/check1_curie_inference.py`; `python ../../final/scripts/check1_curie_xgb_noise.py` | `matched_tiers/curie_*` |
| Final check 2: ordering, 10 splits | `python ../../final/scripts/check2_ordering_10split.py` | `matched_tiers/ordering_10split_*` |
| Final check 3: XGBoost threads, Ms | `python ../../final/scripts/check3_ms_threads_fit.py --mode refit --threads 16 4 1 --splits frozen 0 1 2 3 4 5 6 7 8 9`; also `--mode select …`, `--mode refit --threads 16 --seed-offsets 1 2 3 4 5 …`, `--mode hgb_refit --threads 16 4 1 --splits frozen 0 1 2 3`; then `python ../../final/scripts/check3_ms_threads_analysis.py` | `matched_tiers/ms_moment_*` |
| Ms cell-size control | `python run_phase7_multisplit.py --target ms_moment --splits 5 6 7 8 9 --kinds control`; `python run_phase8_sitecount_10split.py` | `ms_cell_size_control/` |
| Ms per atom (corrected) | `python run_phase8_peratom_ms.py`; `python run_phase8_peratom_ms.py addone`; `python ../../final/scripts/check4_peratom_rerun.py --populations orig_check A B C --kinds main`; `… --populations A C --kinds addone`; `… --populations A B C --summarise` | `ms_per_atom/` |
| Interpretation | `python run_v13_stage6.py`; `python run_phase8_xai_stability.py ordering` (also `curie`, `ms_moment`) | `interpretation/` |

`final_checks/check4_normalization_audit.py` rebuilds `data/reference_inputs/peratom_cell_map.parquet`. It needs raw Materials Project / JARVIS files that are not in the package, plus your own `MP_API_KEY`; its outputs are in `ms_per_atom/`.

### RQ2: uncertainty and calibration (`results/rq2_uncertainty/…`)
| Step | Command | Compare with |
|---|---|---|
| Regression intervals, frozen split | `python run_phase8_regression_uq.py curie`; `python run_phase8_regression_uq.py ms_moment` | `curie/`, `ms_moment/` |
| Ordering probabilities and prediction sets | `python run_phase8_ordering_uq.py` | `ordering/` |
| Repeated splits | `python run_phase8_uq_repeated.py curie` (also `ms_moment`, `ordering`) | `repeated_splits/` |

### RQ3: generalization (`results/rq3_generalization/…`)
| Step | Folder | Command | Compare with |
|---|---|---|---|
| Leave chemical system out | `EDA/src` | `python run_phase8_leave_chemsys.py ordering` (also `curie`, `ms_moment`) | `leave_chemical_system_out/` |
| Blind prediction of the external table | `new_materials_finding` | `python predict_external.py` | `external_benchmark/external_predictions.csv` |
| Audit (loads no prediction) | `new_materials_finding/external_audit` | `python audit_external.py` | `external_benchmark/audit_*` |
| Similarity and grouped bootstrap | `new_materials_finding/external_audit` | `python analyze_external.py`; tests: `python -m pytest -q test_external_audit.py` | `external_benchmark/subset_*`, `similarity_*` |

`fetch_crossref.py` re-downloads the Crossref metadata; the version analysed is `data/external_benchmark/crossref_metadata.csv`.

### Supplementary (`results/supplementary/…`)
| Step | Command | Compare with |
|---|---|---|
| Material families | `python run_v13_stage5.py --fit <ordering or curie> <general, "Transition Metal", "Rare Earth", Oxide or Intermetallic>` (one process each), then `python run_v13_stage5.py` | `material_families/` |
| Bias audit | `python run_phase8_bias.py ordering`; `python run_phase8_bias.py curie`; `python run_phase8_bias_repeated.py` | `bias/` |
| Secondary targets | `OMP_NUM_THREADS=4 python run_v14_secondary.py` (the thread setting of the original run) | `secondary_targets/` |

Hardware used: Intel i7-13620H (10 cores / 16 logical), 15.7 GB RAM, Windows 11. The Stage 5 and per-atom runs need several GB of free memory; run one fit per process as shown.
