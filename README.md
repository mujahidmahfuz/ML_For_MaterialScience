# physics-informed machine learning for magnetic materials

Data, code, results, tables and figures behind the paper. It answers three questions about models that predict magnetic ordering, Curie temperature (Tc) and saturation magnetization (Ms) of inorganic materials:

| Research question | Evidence | Answer in one line |
|---|---|---|
| **RQ1.** Do additional physics descriptors improve prediction? | Matched Tier 1/2/3 experiments (identical rows at every tier, 10 repeated splits); Ms cell-size control; per-atom Ms | Mostly no. Ordering and Tc show no practical gain. Ms gains a little, mostly through cell size and same-calculation DFT outputs. |
| **RQ2.** Are predictions reliable and calibrated? | Split / normalized / CQR conformal intervals; probability calibration; class-conditional prediction sets; subgroup and source-shift coverage | Marginal 90% coverage is achievable with the right method. Hard cases, minority classes, shifted label sources and chemically distant materials are under-covered. |
| **RQ3.** Do predictions generalize to unfamiliar materials? | Leave-chemical-system-out splits; audited external benchmark of 2,500 experimental Tc values; chemical-similarity analysis; paper-clustered bootstrap | New compositions in known chemistry: MAE ≈ 100 K. In unseen chemical systems accuracy is much weaker (R² −0.17, 95% CI −0.93 to 0.66), with wide uncertainty. |

**Overarching finding:** predictive accuracy, gains from physics descriptors, uncertainty calibration and chemical generalization are distinct properties of a model. Strong performance on one does not guarantee strong performance on the others.

## Layout
```
paper/
├── README.md               this file
├── CHECKSUMS.sha256        SHA-256 of every file in data/ and results/
├── data/                   frozen inputs: analysis dataset v1.2-v1.4, splits, external-benchmark adjudications, reference inputs  (data/README.md)
├── scripts/                table/figure builders, workspace + fetch + checksum tools, and pipeline/ (the analysis code)  (scripts/README.md)
├── results/                saved outputs, organised by research question  (results/README.md)
├── tables/                 Tables 1-6 and S1-S3 as CSV + LaTeX  (tables/README.md)
├── figures/                Figures 1-4 and S1 as PDF + PNG  (figures/README.md)
└── manuscript/             Springer Nature LaTeX template (sn-jnl.cls, option sn-nature) for the manuscript
```

## Quick start
```
pip install -r scripts/requirements.txt          # Python 3.12
python scripts/verify_checksums.py                # data and results are intact
python scripts/make_tables.py                     # rebuilds tables/  (seconds)
python scripts/make_figures.py                    # rebuilds figures/ (seconds)
```
To re-run the analyses themselves, follow `scripts/README.md`. It sets up a workspace with `scripts/setup_workspace.py`, then gives the steps per research question, each with the results file to compare against.

## Where each claim comes from
| Claim | Table / figure | Results file |
|---|---|---|
| Tier 3 physics gives no practical Tc gain (GB upper 95% limit +3.8 K) and no stable ordering gain | Table 2, Fig. 1a-b | `results/rq1_physics_descriptors/matched_tiers/curie_inference_table.csv`, `ordering_10split_robustness.csv` |
| Ms per-cell Tier 3 gain is small and recovered by one site-count scalar | Table 2, Fig. 1c | `matched_tiers/robustness_summary_curie_ms_v1.2.csv`, `ms_cell_size_control/` |
| Ms per-atom gain is modest (GB +2.9%, XGB +2.7%, Ridge +6.0%) | Table 2, Fig. 1d | `ms_per_atom/peratom_corrected_tier_effect.csv` |
| Normalized conformal is the only Tc interval method near nominal; the hardest decile is under-covered | Table 3, Fig. 2a | `results/rq2_uncertainty/repeated_splits/curie/` |
| Marginal ordering sets miss AFM/FiM (about 57% / 55%); class-conditional sets cover about 90% for every class (89.9-91.1% over 10 splits) | Table 4, Fig. 2c | `results/rq2_uncertainty/ordering/uq_conformal_sets.csv`, `REPEATED_SPLIT_COVERAGE.md` |
| Ordering degrades on unseen chemical systems (−0.028 macro-F1, 10/10 splits) and does not transfer across label provenance | Table 6 | `results/rq3_generalization/leave_chemical_system_out/`, `label_provenance/` |
| External benchmark: blind compositions MAE 102.7 K [79, 154]; unseen systems R² −0.17 [−0.93, 0.66] | Table 5, Fig. 3 | `results/rq3_generalization/external_benchmark/subset_metrics_bootstrap.csv` |
| Error grows with composition distance (ρ = 0.28 [0.10, 0.49]); coverage falls from 0.95 to 0.85 | Table S3, Fig. 4 | `external_benchmark/similarity_spearman.csv`, `similarity_bins.csv` |
| Audit: 105 of 2,500 external records excluded for stated reasons; 80% of compositions already in our data | Table S1 | `external_benchmark/audit_counts.csv`, `AUDIT_RESULTS.md` |

All claims, with their status after review and the final robustness checks: `results/claims/`.

## Verification of this package
Checked on 2026-11-09 (Windows 11, Python 3.12.3, versions in `scripts/requirements.txt`):
- `verify_checksums.py`: all 355 data and result files match `CHECKSUMS.sha256`.
- `make_tables.py` and `make_figures.py` rebuild every table and figure from `results/`.
- A fresh workspace from `setup_workspace.py`, with a different Python hash seed (`PYTHONHASHSEED=12345`): the analysis test suite passes (62 tests), and so do the external-benchmark tests (11).
- The complete external-benchmark chain (blind prediction → audit → similarity and paper-clustered bootstrap) re-run from the packaged inputs reproduces **all 13 output files byte for byte**.
- **Not re-run for this package:** the multi-hour model fits of RQ1, RQ2 and the supplementary analyses (10 repeated splits × 3 algorithms × 3 tiers). Their code, frozen inputs and exact commands are included, and `results/supplementary/reproducibility_checks/` documents earlier exact reproductions of those runs.

## Data availability and licences
- **Analysis dataset** (`data/analysis_dataset/`): derived from Materials Project, OQMD, JARVIS-DFT, NEMAD, the ChemDataExtractor Curie/Néel database, MAGNDATA and two experimental literature compilations. Each provider has its own terms, and **redistribution licences have not yet been verified**: check them before public deposit.
- **External benchmark** (malaei/Magnetic_data): no stated licence, so it is **not included**. `scripts/fetch_external_benchmark.py` downloads the exact analysed version (SHA-256 checked). Three result files contain its compound names and values (listed in `results/README.md`): clear the licence or remove those columns before deposit.
- **Crossref metadata** (`data/external_benchmark/crossref_metadata.csv`): public bibliographic metadata.
- No credentials are included; the one script that queries Materials Project reads `MP_API_KEY` from the environment.

## Reproducibility notes
- Seeds are fixed in `scripts/pipeline/config/`. XGBoost results also depend on the thread count, so leave `OMP_NUM_THREADS` unset (16 threads were used). Claims are stated across splits and seeds, not single fits.
- About 0.6% of Curie and 1.3% of ordering test rows share a composition, spelled differently, with a training row (see `data/README.md`).
- Before release, choose a licence for the code and add a citation file.
