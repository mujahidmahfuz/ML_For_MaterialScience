# Results

Saved outputs of the analyses, organised by research question. Every number in the tables and figures is read from these files. They are covered by `../CHECKSUMS.sha256`; the script that produced each folder is listed in `../scripts/README.md`.

**Conventions:** 95% intervals unless stated otherwise. "Improvement" columns are signed so that positive = better. "Stable" means the 95% interval excludes zero and the direction holds in at least 70% of the repeated splits.

## `claims/`
| File | Content |
|---|---|
| `claims_register_v1.3.md` | Register of every headline claim after the Phase 7 review (v1.3 dataset), with status and source file |
| `claims_revisions_final.md` | Final revisions after the four robustness checks; supersedes the matching register rows |

## `rq1_physics_descriptors/`: do physics descriptors improve prediction?
| Folder | Content |
|---|---|
| `baselines/` | Tier 1 (composition-only) test metrics for ordering, Curie and Ms |
| `tier2_full_population/` | Tier 1 → Tier 2 differences on the full target populations, plus the Curie AFM-only (C5) sensitivity |
| `matched_tiers/` | Matched Tier 1/2/3 comparisons over 10 repeated splits: ordering (`ordering_10split_*`), Curie (`curie_inference_table.csv`, equivalence margins), Ms per cell (`robustness_summary_curie_ms_v1.2.csv`), and XGBoost thread/seed sensitivity |
| `ms_cell_size_control/` | Ms per cell: Tier 2 + site count against Tier 3 (does cell size explain the gain?) |
| `ms_per_atom/` | Ms per atom after the denominator correction: tier effect, add-one physics families, normalization audit |
| `interpretation/` | SHAP share of physics descriptors, family contributions, and ranking stability over 10 splits |

## `rq2_uncertainty/`: are predictions calibrated?
| Path | Content |
|---|---|
| `PHASE8_UQ_PLAN.md`, `PHASE8_UQ_SUMMARY.md`, `REPEATED_SPLIT_COVERAGE.md` | Pre-specified plan and written results |
| `curie/`, `ms_moment/` | Split, normalized and CQR conformal intervals: summary, coverage by subgroup, coverage curve, label-source shift |
| `ordering/` | Probability calibration (ECE, Brier, NLL) and marginal vs class-conditional prediction sets |
| `repeated_splits/` | The same coverage analyses over 10 repeated splits |

## `rq3_generalization/`: do predictions generalize?
| Path | Content |
|---|---|
| `leave_chemical_system_out/` | Formula-grouped vs chemical-system-grouped splits (10 paired splits) |
| `label_provenance/` | Ordering trained on computed labels and tested on experimental ones, and the reverse |
| `external_benchmark/PLAN.md` | Pre-registered audit / similarity / bootstrap plan with three dated amendments |
| `external_benchmark/AUDIT_RESULTS.md` | Written results of the audit, chemical-similarity and grouped-bootstrap analyses |
| `external_benchmark/audit_flags.csv`, `audit_counts.csv` | Per-record audit flags (A1-A8) and counts |
| `external_benchmark/subset_metrics_bootstrap*.csv`, `subset_comparisons.csv` | Subset metrics and comparisons with paper-, first-DOI- and chemical-system-cluster bootstrap intervals |
| `external_benchmark/similarity_*.csv` | Composition and descriptor distances to the training set; Spearman correlations, distance bins, trends |
| `external_benchmark/external_predictions.csv` | Blind predictions and 90% intervals for the 2,500 external records |

The third-party external table has no stated licence. `audit_flags.csv`, `similarity_records.csv` and `external_predictions.csv` contain its compound names and Curie values: clear the licence before public deposit, or remove those columns.

## `supplementary/`
| Folder | Content |
|---|---|
| `bias/` | Subgroup gaps (AFM/FiM recall, text-mined Curie labels) and the reweighting attempts |
| `material_families/` | Family-specific vs general models (transition metal, rare earth, oxide, intermetallic) |
| `secondary_targets/` | Mass/volume magnetization and K1 (exploratory) |
| `reproducibility_checks/` | Exact-reproduction checks of earlier runs and XGBoost thread-count effects |
