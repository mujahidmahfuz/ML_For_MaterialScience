# Phase 8 — repeated-split coverage check (10 Phase 7 split seeds, 90% nominal; 2026-10-18)

Code: `src/run_phase8_uq_repeated.py`. Per split: calibration = 20% of that split's train formulas, test = its test partition; same hyperparameters and methods as the frozen-split runs. Curie v1.3 (full population), Ms v1.2, ordering v1.3 (class-code stratification, as in the XAI-stability extension). Tables: `<target>/repeated_split_coverage.csv`, `repeated_split_summary.csv`.

## Ordering (sets on prior-corrected + temperature-scaled probabilities; T = 1.66-1.79)
- **Class-conditional sets: stable.** Marginal coverage 90.2% (range 89.6-90.9), per class FM 90.3 / AFM 91.1 / FiM 90.3 / NM 89.9 (every split 88.8-93.7); mean set size 1.60.
- **Marginal LAC sets: overall 90.0% (89.1-91.5) in every split, but the AFM/FiM failure is stable:** AFM 57.2% (45.1-61.1), FiM 54.8% (50.5-58.0), while FM 96.3 and NM 97.8. The frozen-split finding is confirmed.

## Curie (v1.3)
| Method | Marginal mean (SD; range) | Splits within ±2 pts | Hardest decile | Highest-Tc third | Text-mined source |
|---|---|---|---|---|---|
| Split conformal | 89.3% (6.0; 82.2-98.7) | 1/10 | 56% | 78% | 78% |
| Normalized | 90.3% (2.5; 86.9-94.3) | 5/10 | 90% (range 59-100) | 87% | 86% |
| CQR | 89.4% (5.8; 81.7-97.3) | 0/10 | 63% | 80% | 79% |
- Mean marginal coverage is near 90% for every method, but **split-to-split variation is large for Curie** (SD 2.5 to 6 points): a single split can land anywhere from 82% to 99%. Normalized conformal is the most reliable (SD 2.5) yet is within the ±2-point rule in only half of the splits; the frozen-split 91.7% was a representative, not a guaranteed, outcome.
- Under-coverage of the hardest decile, the highest-Tc third and the text-mined source is **systematic**: flagged in 60-90% of splits for split conformal and CQR, 20-40% for normalized. Normalized conformal still under-covers text-mined rows (86%) and high-Tc rows (87%).

## Ms per cell (v1.2)
| Method | Marginal | Splits within ±2 pts | Hardest decile | Highest-moment third | Oxide |
|---|---|---|---|---|---|
| Split conformal | 90.0% (SD 0.4) | 10/10 | 49.7% | 72.3% | 84.0% (flagged 8/10) |
| Normalized | 90.0% (SD 0.5) | 10/10 | 88.8% | 86.7% | 91.0% |
| CQR | 90.1% (SD 0.4) | 10/10 | 78.9% (flagged 10/10) | 83.4% (flagged 10/10) | 89.5% |
- Marginal coverage is highly reproducible for Ms. The frozen-split subgroup findings are **confirmed**: split conformal fails on the hardest decile, high-moment rows and Oxides; CQR under-covers the hardest decile and high-moment third in every split; normalized conformal is never flagged.
- The rare source `magnetic_anisotropy_materials` appears in 8 splits with few formulas (coverage 0.5-1.0), too small to judge.

## Conclusions
1. Ordering and Ms UQ conclusions generalise across splits.
2. For Curie, the frozen split understated the variability; report coverage with a range over splits and do not claim a guaranteed ±2-point marginal coverage.
3. Normalized conformal remains the best regression choice; no method fixes the Curie text-mined / high-Tc under-coverage.

Caveat: the 10 splits resample the same data, so their variability understates population-level uncertainty. The ordering split set is an extension (Phase 7 had none).
