# Data

Frozen inputs of every analysis in the paper. All files are covered by `../CHECKSUMS.sha256` (verify with `python scripts/verify_checksums.py`).

## Contents

| Folder | What it is | Size |
|---|---|---|
| `analysis_dataset/v1.2/` | Analysis dataset v1.2 (frozen 2026-09-28): feature repository (473,720 materials × 127 columns), Tier 1/2/3 predictor tables, group membership, data dictionary, clean targets, quarantined pseudo-formula records, `MANIFEST_v1.2.json` | 340 MB |
| `analysis_dataset/v1.3/` | v1.2 + curation rules R1 (Curie) and R2 (ordering): clean Curie and ordering targets, removed rows with reasons in `excluded/`, `MANIFEST_v1.3.json` | 197 MB |
| `analysis_dataset/v1.4/` | v1.3 + rule R10 (physically impossible K1 / Ms-mass / Ms-volume values removed); **current version** | 171 MB |
| `splits/v1.2`, `v1.3`, `v1.4` | Formula-grouped 70/15/15 train/validation/test assignments per target, plus matched Tier 1/2/3 splits | 37 MB |
| `external_benchmark/` | Inputs of the external-benchmark audit that are not the third-party table itself: Crossref metadata of all 834 source DOIs, and the hand adjudications (papers and records) | 1 MB |
| `reference_inputs/` | Frozen earlier outputs that later scripts read as fixed inputs (selected hyperparameters) or for comparison (see below) | 70 MB |

## How the dataset was formed

1. **Collection (Phase 0):** nine source files from six providers were merged into one 25-column schema with provenance (`_source`) and deduplicated on material name + DOI (507,828 rows). The providers are Materials Project, OQMD, JARVIS-DFT, NEMAD (four files: two releases of its classification sets and its two literature tables of magnetic and of anisotropy properties, `magnetic_materials.csv` and `magnetic_anisotropy_materials.csv`, called the *experimental compilations* in the paper), the ChemDataExtractor text-mined Curie/Néel database and MAGNDATA.
2. **Enrichment (Phases 1–2):** composition, elemental, electronic and oxidation-state descriptors (475,660 rows).
3. **Physics properties (Phase 3):** 47 harmonized DFT properties (Materials Project primary; JARVIS and AFLOW for elastic, dielectric and thermal properties; OQMD as backup), joined by reduced formula.
4. **Feature repository and tiers (Phases 4–5):** 127 approved columns.
   - Tier 1: 65 composition descriptors.
   - Tier 2: Tier 1 plus 8 oxidation-chemistry descriptors (73).
   - Tier 3: Tier 2 plus DFT physics descriptors (97), for the 28,512 materials that have the core DFT properties.
   - Lists: `../scripts/pipeline/config/tier{1,2,3}_predictors.txt`.
5. **Target harmonization and curation (v1.0 → v1.4):** unit normalization and label mapping, then rule-based exclusions only (values are never edited). Every removed row is kept in an `excluded/` folder with its reason code, and the rules are in `../scripts/pipeline/config/v1_3_curation_rules.yaml` and `v1_4_curation_rules.yaml`.
   - v1.2 quarantined 1,940 pseudo-formula records.
   - v1.3 removed superconducting, ferroelectric, Néel and out-of-range "Curie" values, and the 15,493 JARVIS rows whose "FM" label was a collector default.
   - v1.4 removed impossible K1 and Ms values.

Steps 1–3 used raw downloads (several GB) that are not part of this package. The package starts from the frozen v1.2 analysis dataset, from which `build_analysis_dataset_v1_3.py` and `v1_4.py` regenerate v1.3 and v1.4.

## Targets (v1.4)

| Target | File | Value column (validity flag) | Valid rows |
|---|---|---|---|
| Magnetic ordering (FM 34,098 · NM 31,673 · FiM 7,161 · AFM 6,193) | `targets/ordering/target_ordering_clean.csv` | `magnetic_ordering_clean` (`ordering_valid`) | 79,125 |
| Curie temperature, K | `targets/curie/target_curie_clean.csv` | `TC_K_clean` (`target_valid`) | 29,740 |
| DFT total magnetic moment per unit cell, μB/cell | `targets/ms/target_ms_clean.csv` | `Ms_momentPerUnitCell_clean` | 87,513 |
| Mass / volume magnetization (secondary) | `targets/ms/target_ms_clean.csv` | `Ms_massMagnetization_clean`, `Ms_volumeMagnetization_clean` | 4,317 / 779 |
| Anisotropy constant K1, J/m³ (secondary) | `targets/k1/target_k1_clean.csv` | see file | 1,847 |

Rows join on `material_id`. Splits are grouped by `reduced_formula`; the split files list exactly the valid rows of each target.

## NEMAD literature tables (private repository)

The two NEMAD literature tables were downloaded from [nemad.org](https://www.nemad.org), whose terms of use allow academic and research use but **not redistribution**. This repository is private and contains their values (rows whose `_source` contains `magnetic_materials.csv` or `magnetic_anisotropy_materials.csv`). **Before the repository or any copy of `data/` and `results/` is made public**, rebuild the package with `python final/scripts/build_paper_package.py --redact-nemad`: it blanks the measured values of those rows (raw property columns, `target_raw` / `value_raw` / `unit_raw`, `TC_K_clean`, `magnetic_ordering_clean`, `Ms_*_clean`, `K1_clean`, and `y_true` and error columns in prediction files) and keeps their identifiers (`material_id`, formula, `DOI`, `_source`, `Experimental`, validity flags) and our computed descriptors. Fig. 1 reads aggregate counts (`results/revision/a2_provenance/target_source_counts.csv`), so every figure is unaffected.

Work that uses these values must cite Itani, Zhang & Zang, *Nat. Commun.* **16**, 9415 (2025) and Zhang *et al.*, *J. Magn. Magn. Mater.* **597**, 172001 (2024), as the NEMAD terms require.

**Known limitation:** about 0.6% of Curie test rows and 1.3% of ordering test rows share their composition with a training row that is spelled differently (fractional vs integer formula string). Ms is unaffected.

## External benchmark (RQ3)
The third-party table of 2,500 experimental Curie temperatures (malaei/Magnetic_data) has **no stated licence and is not included**. `../scripts/fetch_external_benchmark.py` downloads the exact analysed version (SHA-256 checked) into a run workspace, never into this folder. Three derived result files contain its compound names and values:
- `../results/rq3_generalization/external_benchmark/audit_flags.csv`
- `../results/rq3_generalization/external_benchmark/similarity_records.csv`
- `../results/rq3_generalization/external_benchmark/external_predictions.csv`

Clear the licence before public deposit, or remove those columns.

## Reference inputs
| File | Read by | Why |
|---|---|---|
| `peratom_cell_map.parquet` | `final_checks/check4_peratom_rerun.py` | Cell-size map for the per-atom Ms correction. It was built by `check4_normalization_audit.py` from raw Materials Project / JARVIS files that are not included. |
| `prior_5split/*.csv` | `final_checks/check2_ordering_10split.py` | Archived 5-split ordering results, compared against the 10-split re-run |
| `stage5_general/general_predictions_{curie,ordering}.csv` | Phase 8 scripts, `external_benchmark/predict_*.py` | Selected XGBoost hyperparameters of the general Tier 1 models (column `params_xgboost`). These are fixed, not re-tuned, in all later stages. |
| `phase6/03_…09_*` | Phase 7 validation, Phase 8 scripts, `run_v14_secondary.py` | Frozen Phase 6 outputs: selected hyperparameters (Stage 2 and Stage 4 JSON), the frozen-split predictions that Phase 7 reproduces exactly, and earlier tables used for comparison |

## Licences
Each provider has its own terms; they are quoted, with their URLs, in `../results/revision/research/data_licences.md` and summarised in Supplementary Table 10. Materials Project, OQMD, JARVIS-DFT, the ChemDataExtractor database and the NEMAD Zenodo release are CC BY 4.0. AFLOW-derived Tier 3 columns are for non-commercial use. MAGNDATA structure files are not redistributed (derived labels only, with the citations its conditions ask for). The NEMAD website tables may not be redistributed (see above).
