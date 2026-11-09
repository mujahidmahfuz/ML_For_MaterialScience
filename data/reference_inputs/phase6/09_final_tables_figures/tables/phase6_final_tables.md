# Phase 6 final tables

### Table 1. Dataset description (Analysis Dataset v1.2; clean targets and Tier 3 matched N)

| Target | Role | Task | Unit | Clean N | Tier 3 matched N | Unique formulas | % experimental | Distribution |
|---|---|---|---|---|---|---|---|---|
| Magnetic ordering | primary | classification | class | 94,618 | 13,914 | 75,779 | 17.4 | FM 49,591 (52.4%); AFM 6,193 (6.5%); FiM 7,161 (7.6%); NM 31,673 (33.5%) |
| Curie temperature | primary | regression | K | 34,322 | 5,490 | 15,404 | 94.7 | median 293 [IQR 100, 521]; range 0.0004..2986 |
| Ms (moment per unit cell) | primary | regression | muB/unit-cell | 87,513 | 10,852 | 77,402 | 0.0 | median 0.869 [IQR 0.0003042, 4.864]; range 0..256.2 |
| Ms (mass magnetization) | secondary | regression | emu/g | 4,318 | 247 | 3,219 | 99.1 | median 52.24 [IQR 26.21, 73.56]; range 0.0012..257 |
| Ms (volume magnetization) | exploratory | regression | A/m | 788 | 252 | 460 | 88.8 | median 5.38e+05 [IQR 2.305e+05, 9.675e+05]; range 0..3.686e+06 |
| K1 | exploratory | regression | J/m^3 | 1,862 | 404 | 1,192 | 91.0 | median 1.53e+05 [IQR 1740, 1.6e+06]; range -7.2e+07..6.44e+08 |

### Table 2. Primary model performance - Tier 1 baselines (formula-grouped held-out test set)

| Target | Model | Test N | Primary metric | Primary (95% CI) | Secondary metric | Secondary (95% CI) | Best by validation |
|---|---|---|---|---|---|---|---|
| Magnetic ordering | Dummy reference | 14,207 | macro-F1 | 0.172 [0.1684, 0.1759] | balanced accuracy | 0.25 [0.25, 0.25] | False |
| Magnetic ordering | Linear / logistic | 14,207 | macro-F1 | 0.4351 [0.419, 0.451] | balanced accuracy | 0.5572 [0.5369, 0.5764] | False |
| Magnetic ordering | Random Forest | 14,207 | macro-F1 | 0.6742 [0.6568, 0.6905] | balanced accuracy | 0.6889 [0.6692, 0.7059] | False |
| Magnetic ordering | Gradient Boosting (hist) | 14,207 | macro-F1 | 0.6948 [0.6796, 0.7095] | balanced accuracy | 0.7116 [0.6925, 0.7275] | True |
| Magnetic ordering | XGBoost | 14,207 | macro-F1 | 0.7003 [0.6832, 0.715] | balanced accuracy | 0.7056 [0.6867, 0.7219] | False |
| Curie temperature | Dummy reference | 5,165 | MAE | 226 [211.4, 241.5] | R² | -0.0003808 [-0.01876, -5.791e-06] | False |
| Curie temperature | Linear / logistic | 5,165 | MAE | 165.2 [153.1, 177.9] | R² | 0.3622 [0.2779, 0.4337] | False |
| Curie temperature | Random Forest | 5,165 | MAE | 100.7 [90.36, 110.9] | R² | 0.633 [0.5625, 0.6893] | True |
| Curie temperature | Gradient Boosting (hist) | 5,165 | MAE | 94.53 [84.44, 105.2] | R² | 0.6354 [0.5594, 0.6982] | False |
| Curie temperature | XGBoost | 5,165 | MAE | 95.75 [85.03, 106.6] | R² | 0.6383 [0.5662, 0.6977] | False |
| Ms (moment per unit cell) | Dummy reference | 13,129 | MAE | 5.625 [5.468, 5.78] | R² | -2.252e-05 [-0.0005018, -1.429e-07] | False |
| Ms (moment per unit cell) | Linear / logistic | 13,129 | MAE | 4.58 [4.444, 4.722] | R² | 0.2697 [0.2472, 0.2936] | False |
| Ms (moment per unit cell) | Random Forest | 13,129 | MAE | 2.565 [2.459, 2.665] | R² | 0.676 [0.6299, 0.7239] | False |
| Ms (moment per unit cell) | Gradient Boosting (hist) | 13,129 | MAE | 2.577 [2.471, 2.673] | R² | 0.6989 [0.6568, 0.7414] | True |
| Ms (moment per unit cell) | XGBoost | 13,129 | MAE | 2.534 [2.428, 2.637] | R² | 0.6915 [0.644, 0.7416] | False |

### Table 3. Physics-informed ablation - matched Tier 1 vs Tier 2 vs Tier 3 (identical materials/split; improvement positive = better)

| Target | Matched N | Tier | Model | Primary metric | Primary (95% CI) | Secondary metric | Secondary (95% CI) | Δ vs Tier 1 (improvement, 95% CI) | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Magnetic ordering | 13,914 | Tier 1 | Linear / logistic | macro-F1 | 0.267 [0.2228, 0.3097] | balanced accuracy | 0.5364 [0.4626, 0.6037] |  |  |
| Magnetic ordering | 13,914 | Tier 2 | Linear / logistic | macro-F1 | 0.2679 [0.2217, 0.3125] | balanced accuracy | 0.5272 [0.4511, 0.5978] | 0.0009297 [-0.01667, 0.01672] | no stable change |
| Magnetic ordering | 13,914 | Tier 3 | Linear / logistic | macro-F1 | 0.2923 [0.251, 0.3348] | balanced accuracy | 0.5676 [0.4838, 0.6265] | 0.02529 [-0.0003596, 0.05127] | no stable change |
| Magnetic ordering | 13,914 | Tier 1 | Gradient Boosting (hist) | macro-F1 | 0.3144 [0.266, 0.3691] | balanced accuracy | 0.2985 [0.2714, 0.3384] |  |  |
| Magnetic ordering | 13,914 | Tier 2 | Gradient Boosting (hist) | macro-F1 | 0.3506 [0.3035, 0.4012] | balanced accuracy | 0.3395 [0.3009, 0.3888] | 0.03618 [0.007457, 0.07069] | stable improvement |
| Magnetic ordering | 13,914 | Tier 3 | Gradient Boosting (hist) | macro-F1 | 0.3076 [0.2546, 0.3535] | balanced accuracy | 0.2939 [0.263, 0.327] | -0.006828 [-0.04769, 0.03439] | no stable change |
| Magnetic ordering | 13,914 | Tier 1 | XGBoost | macro-F1 | 0.3945 [0.3421, 0.4493] | balanced accuracy | 0.4076 [0.3568, 0.468] |  |  |
| Magnetic ordering | 13,914 | Tier 2 | XGBoost | macro-F1 | 0.3888 [0.3317, 0.4399] | balanced accuracy | 0.3956 [0.3428, 0.4553] | -0.005692 [-0.04037, 0.02659] | no stable change |
| Magnetic ordering | 13,914 | Tier 3 | XGBoost | macro-F1 | 0.3802 [0.3269, 0.4265] | balanced accuracy | 0.3668 [0.3203, 0.4229] | -0.01433 [-0.05791, 0.02258] | no stable change |
| Curie temperature | 5,490 | Tier 1 | Linear / logistic | MAE | 255.6 [167.8, 351.7] | R² | 0.2521 [-0.7203, 0.3287] |  |  |
| Curie temperature | 5,490 | Tier 2 | Linear / logistic | MAE | 254.3 [162.5, 353] | R² | 0.2562 [-0.5518, 0.3232] | 1.297 [-10.3, 12.68] | no stable change |
| Curie temperature | 5,490 | Tier 3 | Linear / logistic | MAE | 7.647e+08 [174.1, 2.853e+09] | R² | -8.755e+14 [-7.672e+15, 0.4597] | -7.647e+08 [-2.853e+09, 47.69] | no stable change |
| Curie temperature | 5,490 | Tier 1 | Gradient Boosting (hist) | MAE | 288 [127.4, 476.9] | R² | -0.1738 [-0.9446, 0.3272] |  |  |
| Curie temperature | 5,490 | Tier 2 | Gradient Boosting (hist) | MAE | 288.4 [118.6, 479.7] | R² | -0.2184 [-0.9626, 0.2543] | -0.3871 [-36.02, 32.14] | no stable change |
| Curie temperature | 5,490 | Tier 3 | Gradient Boosting (hist) | MAE | 326.5 [171, 510.5] | R² | -0.3674 [-1.268, 0.181] | -38.52 [-110.2, 24.13] | no stable change |
| Curie temperature | 5,490 | Tier 1 | XGBoost | MAE | 273.9 [112.5, 480.2] | R² | -0.1831 [-1.089, 0.4991] |  |  |
| Curie temperature | 5,490 | Tier 2 | XGBoost | MAE | 268.4 [119.9, 452.1] | R² | -0.05577 [-0.7543, 0.394] | 5.528 [-36.93, 39.09] | no stable change |
| Curie temperature | 5,490 | Tier 3 | XGBoost | MAE | 207.4 [141.3, 276.4] | R² | 0.5034 [-0.06315, 0.5763] | 66.47 [-48.11, 206.6] | no stable change |
| Ms (moment per unit cell) | 10,852 | Tier 1 | Linear / logistic | MAE | 2.163 [1.995, 2.317] | R² | 0.184 [0.1374, 0.2559] |  |  |
| Ms (moment per unit cell) | 10,852 | Tier 2 | Linear / logistic | MAE | 2.164 [1.995, 2.306] | R² | 0.1871 [0.1394, 0.2596] | -0.001344 [-0.02427, 0.02279] | no stable change |
| Ms (moment per unit cell) | 10,852 | Tier 3 | Linear / logistic | MAE | 2.072 [1.902, 2.215] | R² | 0.2145 [0.1591, 0.3004] | 0.09047 [0.0414, 0.1478] | stable improvement |
| Ms (moment per unit cell) | 10,852 | Tier 1 | Gradient Boosting (hist) | MAE | 1.874 [1.715, 2.015] | R² | 0.2663 [0.198, 0.3797] |  |  |
| Ms (moment per unit cell) | 10,852 | Tier 2 | Gradient Boosting (hist) | MAE | 1.88 [1.722, 2.03] | R² | 0.2658 [0.197, 0.3799] | -0.006445 [-0.04287, 0.02781] | no stable change |
| Ms (moment per unit cell) | 10,852 | Tier 3 | Gradient Boosting (hist) | MAE | 1.791 [1.618, 1.935] | R² | 0.282 [0.2, 0.4011] | 0.08291 [0.006417, 0.1576] | stable improvement |
| Ms (moment per unit cell) | 10,852 | Tier 1 | XGBoost | MAE | 1.913 [1.745, 2.059] | R² | 0.2323 [0.1698, 0.3387] |  |  |
| Ms (moment per unit cell) | 10,852 | Tier 2 | XGBoost | MAE | 1.899 [1.737, 2.051] | R² | 0.2399 [0.1729, 0.3495] | 0.0137 [-0.04223, 0.08051] | no stable change |
| Ms (moment per unit cell) | 10,852 | Tier 3 | XGBoost | MAE | 1.816 [1.645, 1.97] | R² | 0.2817 [0.2141, 0.3958] | 0.0969 [0.01826, 0.1767] | stable improvement |

### Table 3b. Tier 1 -> Tier 2 oxidation-chemistry ablation on the full clean populations

| Target | Model | Metric | Tier 1 | Tier 2 | Improvement (95% CI) | Verdict |
|---|---|---|---|---|---|---|
| Magnetic ordering | Linear / logistic | macro-F1 | 0.4351 | 0.4355 | 0.0004035 [-0.00531, 0.006896] | no stable change |
| Magnetic ordering | Gradient Boosting (hist) | macro-F1 | 0.6948 | 0.6976 | 0.002837 [-0.007481, 0.01183] | no stable change |
| Magnetic ordering | XGBoost | macro-F1 | 0.7003 | 0.6913 | -0.008974 [-0.01667, -0.001502] | stable degradation |
| Curie temperature | Linear / logistic | MAE | 165.2 | 165.7 | -0.4346 [-2.414, 1.475] | no stable change |
| Curie temperature | Gradient Boosting (hist) | MAE | 94.53 | 101.3 | -6.811 [-11.04, -3.021] | stable degradation |
| Curie temperature | XGBoost | MAE | 95.75 | 100.8 | -5.023 [-8.059, -1.655] | stable degradation |
| Ms (moment per unit cell) | Linear / logistic | MAE | 4.58 | 4.586 | -0.005644 [-0.01511, 0.004941] | no stable change |
| Ms (moment per unit cell) | Gradient Boosting (hist) | MAE | 2.577 | 2.568 | 0.008981 [-0.00821, 0.02684] | no stable change |
| Ms (moment per unit cell) | XGBoost | MAE | 2.534 | 2.533 | 0.0014 [-0.02318, 0.02524] | no stable change |

### Table 4. Material-family generalization - Tier 1 XGBoost (each family's own test rows)

| Target | Family | Test N | Metric | General model on family | General model on rest | Family vs rest | Family-specific model | Specific vs general |
|---|---|---|---|---|---|---|---|---|
| Magnetic ordering | All (whole test set) | 14,207 | macro-F1 | 0.7003 [0.6832, 0.715] |  |  |  |  |
| Magnetic ordering | Transition Metal | 11,448 | macro-F1 | 0.7018 [0.6841, 0.717] | 0.6178 [0.5744, 0.6635] | better on family | 0.6926 [0.6768, 0.7087] | -0.009186 (stable degradation) |
| Magnetic ordering | Rare Earth | 3,735 | macro-F1 | 0.7405 [0.7176, 0.7617] | 0.679 [0.6518, 0.699] | better on family | 0.7415 [0.7168, 0.7642] | +0.001016 (no stable change) |
| Magnetic ordering | Oxide | 6,923 | macro-F1 | 0.6659 [0.6482, 0.6834] | 0.7387 [0.7092, 0.7631] | worse on family | 0.662 [0.6441, 0.68] | -0.003897 (no stable change) |
| Magnetic ordering | Intermetallic | 5,821 | macro-F1 | 0.7421 [0.7117, 0.7662] | 0.6726 [0.6539, 0.6903] | better on family | 0.7469 [0.7154, 0.7697] | +0.004876 (no stable change) |
| Curie temperature | All (whole test set) | 5,165 | MAE | 95.75 [85.03, 106.6] |  |  |  |  |
| Curie temperature | Transition Metal | 4,719 | MAE | 87 [78.57, 95.99] | 188.3 [138, 230.3] | better on family | 89 [79.55, 98.86] | -2.001 (no stable change) |
| Curie temperature | Rare Earth | 2,336 | MAE | 51.32 [45.48, 57.37] | 132.4 [115.5, 149.7] | better on family | 49.86 [42.63, 58.38] | +1.463 (no stable change) |
| Curie temperature | Oxide | 1,875 | MAE | 83.05 [67.9, 100.8] | 103 [90.07, 116.7] | no stable difference | 86.86 [71.2, 105.7] | -3.813 (no stable change) |
| Curie temperature | Intermetallic | 2,234 | MAE | 86.87 [78.11, 95] | 102.5 [84.27, 120.2] | no stable difference | 80.68 [70.73, 91.93] | +6.195 (stable improvement) |
| Ms (moment per unit cell) | All (whole test set) | 13,129 | MAE | 2.534 [2.428, 2.637] |  |  |  |  |
| Ms (moment per unit cell) | Transition Metal | 10,018 | MAE | 2.714 [2.599, 2.839] | 1.954 [1.781, 2.141] | worse on family | 2.698 [2.581, 2.824] | +0.01622 (no stable change) |
| Ms (moment per unit cell) | Rare Earth | 3,361 | MAE | 2.474 [2.248, 2.713] | 2.555 [2.443, 2.666] | no stable difference | 2.65 [2.432, 2.915] | -0.1764 (stable degradation) |
| Ms (moment per unit cell) | Oxide | 6,056 | MAE | 3.48 [3.303, 3.652] | 1.725 [1.623, 1.835] | worse on family | 3.515 [3.341, 3.686] | -0.0357 (no stable change) |
| Ms (moment per unit cell) | Intermetallic | 5,913 | MAE | 1.566 [1.471, 1.673] | 3.328 [3.157, 3.478] | better on family | 1.476 [1.387, 1.58] | +0.09069 (stable improvement) |

### Table S4. Family metrics, all algorithms and scopes

| target | scope | group | algorithm | n_test | test_macro_f1 | test_balanced_accuracy | test_accuracy | test_macro_f1_ci_low | test_macro_f1_ci_high | test_balanced_accuracy_ci_low | test_balanced_accuracy_ci_high | test_mae | test_rmse | test_r2 | test_median_ae | test_mae_ci_low | test_mae_ci_high | test_rmse_ci_low | test_rmse_ci_high | test_r2_ci_low | test_r2_ci_high |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ordering | general_overall | ALL | linear | 14207 | 0.43506 | 0.55723 | 0.50074 | 0.419 | 0.451 | 0.5369 | 0.57638 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_overall | ALL | gradient_boosting | 14207 | 0.69478 | 0.71159 | 0.79419 | 0.67958 | 0.70945 | 0.69246 | 0.72751 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_overall | ALL | xgboost | 14207 | 0.70029 | 0.70558 | 0.80383 | 0.68319 | 0.715 | 0.68666 | 0.72191 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_family | Transition Metal | linear | 11448 | 0.43118 | 0.55555 | 0.46488 | 0.41369 | 0.44785 | 0.53381 | 0.5756 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_family | Transition Metal | gradient_boosting | 11448 | 0.69638 | 0.7174 | 0.78258 | 0.68001 | 0.71182 | 0.69825 | 0.7338 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_family | Transition Metal | xgboost | 11448 | 0.7018 | 0.70978 | 0.79368 | 0.68406 | 0.71702 | 0.68995 | 0.72688 |  |  |  |  |  |  |  |  |  |  |
| ordering | specific_on_family | Transition Metal | linear | 11448 | 0.44985 | 0.57492 | 0.49188 | 0.4309 | 0.46713 | 0.55258 | 0.596 |  |  |  |  |  |  |  |  |  |  |
| ordering | specific_on_family | Transition Metal | gradient_boosting | 11448 | 0.69348 | 0.70173 | 0.78538 | 0.67619 | 0.70888 | 0.68157 | 0.719 |  |  |  |  |  |  |  |  |  |  |
| ordering | specific_on_family | Transition Metal | xgboost | 11448 | 0.69261 | 0.72157 | 0.77551 | 0.67684 | 0.70867 | 0.70166 | 0.73787 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Transition Metal | linear | 2759 | 0.35753 | 0.38968 | 0.64951 | 0.32618 | 0.38643 | 0.34849 | 0.43513 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Transition Metal | gradient_boosting | 2759 | 0.60194 | 0.57177 | 0.84233 | 0.55252 | 0.64533 | 0.52383 | 0.62574 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Transition Metal | xgboost | 2759 | 0.61782 | 0.59058 | 0.84596 | 0.57442 | 0.66346 | 0.54712 | 0.64428 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_family | Rare Earth | linear | 3735 | 0.39997 | 0.53039 | 0.42276 | 0.35528 | 0.44842 | 0.4922 | 0.56969 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_family | Rare Earth | gradient_boosting | 3735 | 0.72397 | 0.7456 | 0.79009 | 0.70071 | 0.74585 | 0.71795 | 0.77519 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_family | Rare Earth | xgboost | 3735 | 0.74049 | 0.75694 | 0.80428 | 0.71762 | 0.76166 | 0.72985 | 0.7835 |  |  |  |  |  |  |  |  |  |  |
| ordering | specific_on_family | Rare Earth | linear | 3735 | 0.47444 | 0.57799 | 0.51111 | 0.42867 | 0.5144 | 0.53922 | 0.61473 |  |  |  |  |  |  |  |  |  |  |
| ordering | specific_on_family | Rare Earth | gradient_boosting | 3735 | 0.7301 | 0.74611 | 0.79598 | 0.70569 | 0.75562 | 0.71895 | 0.77381 |  |  |  |  |  |  |  |  |  |  |
| ordering | specific_on_family | Rare Earth | xgboost | 3735 | 0.74151 | 0.73682 | 0.81124 | 0.7168 | 0.76424 | 0.7081 | 0.76593 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Rare Earth | linear | 10472 | 0.44402 | 0.56155 | 0.52855 | 0.42676 | 0.46236 | 0.53536 | 0.58412 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Rare Earth | gradient_boosting | 10472 | 0.67894 | 0.69401 | 0.79565 | 0.65688 | 0.69627 | 0.6702 | 0.71388 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Rare Earth | xgboost | 10472 | 0.67896 | 0.67978 | 0.80367 | 0.65182 | 0.69901 | 0.65117 | 0.70274 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_family | Oxide | linear | 6923 | 0.39133 | 0.51862 | 0.43117 | 0.37696 | 0.40573 | 0.49648 | 0.54003 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_family | Oxide | gradient_boosting | 6923 | 0.6601 | 0.6732 | 0.76181 | 0.64144 | 0.67718 | 0.65274 | 0.69166 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_family | Oxide | xgboost | 6923 | 0.66587 | 0.67131 | 0.77134 | 0.64818 | 0.68342 | 0.64967 | 0.69081 |  |  |  |  |  |  |  |  |  |  |
| ordering | specific_on_family | Oxide | linear | 6923 | 0.42702 | 0.54939 | 0.47812 | 0.4111 | 0.44281 | 0.52553 | 0.57327 |  |  |  |  |  |  |  |  |  |  |
| ordering | specific_on_family | Oxide | gradient_boosting | 6923 | 0.63266 | 0.68487 | 0.71645 | 0.61284 | 0.64948 | 0.66185 | 0.70315 |  |  |  |  |  |  |  |  |  |  |
| ordering | specific_on_family | Oxide | xgboost | 6923 | 0.66197 | 0.66677 | 0.76889 | 0.64414 | 0.68002 | 0.64646 | 0.68703 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Oxide | linear | 7284 | 0.47763 | 0.59336 | 0.56686 | 0.44506 | 0.50662 | 0.55631 | 0.62503 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Oxide | gradient_boosting | 7284 | 0.73174 | 0.75485 | 0.82496 | 0.70017 | 0.75839 | 0.72096 | 0.78223 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Oxide | xgboost | 7284 | 0.73873 | 0.74396 | 0.83471 | 0.70919 | 0.76307 | 0.70997 | 0.77211 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_family | Intermetallic | linear | 5821 | 0.46944 | 0.58818 | 0.54235 | 0.43662 | 0.50188 | 0.54996 | 0.62034 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_family | Intermetallic | gradient_boosting | 5821 | 0.73547 | 0.75876 | 0.82134 | 0.70181 | 0.76348 | 0.72331 | 0.78768 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_family | Intermetallic | xgboost | 5821 | 0.74206 | 0.74854 | 0.83027 | 0.71172 | 0.7662 | 0.713 | 0.77974 |  |  |  |  |  |  |  |  |  |  |
| ordering | specific_on_family | Intermetallic | linear | 5821 | 0.49583 | 0.62743 | 0.56056 | 0.4665 | 0.5223 | 0.59173 | 0.65386 |  |  |  |  |  |  |  |  |  |  |
| ordering | specific_on_family | Intermetallic | gradient_boosting | 5821 | 0.72715 | 0.76731 | 0.80862 | 0.69539 | 0.75091 | 0.73645 | 0.79233 |  |  |  |  |  |  |  |  |  |  |
| ordering | specific_on_family | Intermetallic | xgboost | 5821 | 0.74694 | 0.75806 | 0.82855 | 0.7154 | 0.76974 | 0.72285 | 0.78474 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Intermetallic | linear | 8386 | 0.41441 | 0.53686 | 0.47186 | 0.39597 | 0.43551 | 0.51344 | 0.56301 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Intermetallic | gradient_boosting | 8386 | 0.66715 | 0.6813 | 0.77534 | 0.64953 | 0.6841 | 0.66114 | 0.69935 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Intermetallic | xgboost | 8386 | 0.67265 | 0.67795 | 0.78548 | 0.65392 | 0.69032 | 0.65706 | 0.69758 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_slice | Experimental | linear | 2599 | 0.48102 | 0.58501 | 0.48326 | 0.41559 | 0.53809 | 0.52725 | 0.64359 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_slice | Experimental | gradient_boosting | 2599 | 0.7316 | 0.74382 | 0.78569 | 0.69295 | 0.76731 | 0.6981 | 0.77834 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_slice | Experimental | xgboost | 2599 | 0.73804 | 0.73187 | 0.79531 | 0.69826 | 0.77306 | 0.68652 | 0.76654 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Experimental | linear | 11608 | 0.37911 | 0.50486 | 0.50465 | 0.37016 | 0.38898 | 0.4851 | 0.52806 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Experimental | gradient_boosting | 11608 | 0.58036 | 0.60908 | 0.79609 | 0.5662 | 0.59603 | 0.58853 | 0.63054 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Experimental | xgboost | 11608 | 0.58748 | 0.61001 | 0.80574 | 0.57348 | 0.60188 | 0.59072 | 0.63 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_slice | Computational | linear | 11608 | 0.37911 | 0.50486 | 0.50465 | 0.37016 | 0.38898 | 0.4851 | 0.52806 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_slice | Computational | gradient_boosting | 11608 | 0.58036 | 0.60908 | 0.79609 | 0.5662 | 0.59603 | 0.58853 | 0.63054 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_slice | Computational | xgboost | 11608 | 0.58748 | 0.61001 | 0.80574 | 0.57348 | 0.60188 | 0.59072 | 0.63 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Computational | linear | 2599 | 0.48102 | 0.58501 | 0.48326 | 0.41559 | 0.53809 | 0.52725 | 0.64359 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Computational | gradient_boosting | 2599 | 0.7316 | 0.74382 | 0.78569 | 0.69295 | 0.76731 | 0.6981 | 0.77834 |  |  |  |  |  |  |  |  |  |  |
| ordering | general_on_rest | Computational | xgboost | 2599 | 0.73804 | 0.73187 | 0.79531 | 0.69826 | 0.77306 | 0.68652 | 0.76654 |  |  |  |  |  |  |  |  |  |  |
| curie | general_overall | ALL | linear | 5165 |  |  |  |  |  |  |  | 165.21825 | 223.75025 | 0.36217 | 129.85809 | 153.05447 | 177.85532 | 208.01102 | 239.04609 | 0.27792 | 0.43371 |
| curie | general_overall | ALL | gradient_boosting | 5165 |  |  |  |  |  |  |  | 94.5293 | 169.15963 | 0.63544 | 44.05878 | 84.43592 | 105.24591 | 151.58203 | 186.43003 | 0.55939 | 0.69819 |
| curie | general_overall | ALL | xgboost | 5165 |  |  |  |  |  |  |  | 95.74577 | 168.49158 | 0.63831 | 45.78867 | 85.03274 | 106.59648 | 151.59857 | 186.59669 | 0.56615 | 0.69766 |
| curie | general_on_family | Transition Metal | linear | 4719 |  |  |  |  |  |  |  | 161.08315 | 216.26846 | 0.38143 | 126.59369 | 147.98811 | 173.76545 | 200.95218 | 232.11835 | 0.289 | 0.456 |
| curie | general_on_family | Transition Metal | gradient_boosting | 4719 |  |  |  |  |  |  |  | 84.73689 | 153.54147 | 0.68822 | 40.73099 | 76.4607 | 93.3878 | 137.73478 | 170.70082 | 0.61587 | 0.74884 |
| curie | general_on_family | Transition Metal | xgboost | 4719 |  |  |  |  |  |  |  | 87.00195 | 154.53572 | 0.68417 | 42.25311 | 78.57052 | 95.98687 | 138.02001 | 171.4104 | 0.61647 | 0.74263 |
| curie | specific_on_family | Transition Metal | linear | 4719 |  |  |  |  |  |  |  | 161.16048 | 216.2089 | 0.38177 | 125.81637 | 148.38444 | 174.47106 | 200.88133 | 232.17334 | 0.28446 | 0.45545 |
| curie | specific_on_family | Transition Metal | gradient_boosting | 4719 |  |  |  |  |  |  |  | 91.73145 | 155.0136 | 0.68221 | 47.76267 | 83.14487 | 101.18984 | 139.55853 | 171.65829 | 0.61326 | 0.73961 |
| curie | specific_on_family | Transition Metal | xgboost | 4719 |  |  |  |  |  |  |  | 89.00332 | 158.88705 | 0.66613 | 38.90509 | 79.5549 | 98.85637 | 142.38092 | 175.79901 | 0.59923 | 0.7276 |
| curie | general_on_rest | Transition Metal | linear | 446 |  |  |  |  |  |  |  | 208.97065 | 291.3713 | 0.20886 | 144.58666 | 171.73091 | 249.0997 | 238.12869 | 341.0578 | 0.08505 | 0.33869 |
| curie | general_on_rest | Transition Metal | gradient_boosting | 446 |  |  |  |  |  |  |  | 198.14002 | 286.25471 | 0.2364 | 136.6975 | 146.84834 | 236.65853 | 225.96054 | 328.46971 | 0.10965 | 0.37819 |
| curie | general_on_rest | Transition Metal | xgboost | 446 |  |  |  |  |  |  |  | 188.26164 | 275.84157 | 0.29094 | 122.2772 | 137.96219 | 230.29423 | 214.48841 | 319.8436 | 0.16953 | 0.43725 |
| curie | general_on_family | Rare Earth | linear | 2336 |  |  |  |  |  |  |  | 124.59435 | 165.96286 | 0.54779 | 96.01218 | 111.26078 | 136.25123 | 152.89244 | 178.83673 | 0.45952 | 0.5985 |
| curie | general_on_family | Rare Earth | gradient_boosting | 2336 |  |  |  |  |  |  |  | 49.47754 | 95.88378 | 0.84906 | 23.27931 | 43.90135 | 55.07976 | 79.49096 | 109.75338 | 0.80637 | 0.8883 |
| curie | general_on_family | Rare Earth | xgboost | 2336 |  |  |  |  |  |  |  | 51.31943 | 96.98258 | 0.84558 | 24.51091 | 45.47804 | 57.36666 | 81.98327 | 110.62835 | 0.80569 | 0.88274 |
| curie | specific_on_family | Rare Earth | linear | 2336 |  |  |  |  |  |  |  | 112.63961 | 157.33688 | 0.59358 | 77.04218 | 99.44354 | 124.47756 | 143.70827 | 172.29265 | 0.50336 | 0.65346 |
| curie | specific_on_family | Rare Earth | gradient_boosting | 2336 |  |  |  |  |  |  |  | 52.51037 | 97.54663 | 0.84378 | 24.78562 | 47.11705 | 58.12751 | 82.89492 | 111.0114 | 0.80499 | 0.88057 |
| curie | specific_on_family | Rare Earth | xgboost | 2336 |  |  |  |  |  |  |  | 49.85654 | 96.94075 | 0.84571 | 23.4393 | 42.63163 | 58.3835 | 80.26683 | 111.65827 | 0.80523 | 0.88378 |
| curie | general_on_rest | Rare Earth | linear | 2829 |  |  |  |  |  |  |  | 198.76277 | 262.03074 | 0.22637 | 158.53482 | 181.41294 | 216.71526 | 239.23762 | 284.65006 | 0.10379 | 0.33208 |
| curie | general_on_rest | Rare Earth | gradient_boosting | 2829 |  |  |  |  |  |  |  | 131.73005 | 211.30968 | 0.49688 | 82.05497 | 114.82739 | 148.98572 | 187.11424 | 237.34501 | 0.39003 | 0.59101 |
| curie | general_on_rest | Rare Earth | xgboost | 2829 |  |  |  |  |  |  |  | 132.43009 | 209.91656 | 0.50349 | 88.36096 | 115.52977 | 149.65243 | 186.29663 | 233.47404 | 0.40144 | 0.59599 |
| curie | general_on_family | Oxide | linear | 1875 |  |  |  |  |  |  |  | 157.89965 | 222.40181 | 0.28851 | 114.98158 | 132.75098 | 185.92058 | 192.06615 | 255.22343 | 0.02377 | 0.44313 |
| curie | general_on_family | Oxide | gradient_boosting | 1875 |  |  |  |  |  |  |  | 82.97528 | 163.03331 | 0.61766 | 36.87324 | 68.62981 | 100.2775 | 132.07239 | 201.61111 | 0.43989 | 0.74034 |
| curie | general_on_family | Oxide | xgboost | 1875 |  |  |  |  |  |  |  | 83.04907 | 163.23425 | 0.61672 | 38.34675 | 67.90451 | 100.82671 | 130.76485 | 199.95086 | 0.44085 | 0.74369 |
| curie | specific_on_family | Oxide | linear | 1875 |  |  |  |  |  |  |  | 143.95299 | 218.59086 | 0.31268 | 98.10379 | 113.63387 | 177.67145 | 175.31489 | 260.60465 | 0.04221 | 0.48444 |
| curie | specific_on_family | Oxide | gradient_boosting | 1875 |  |  |  |  |  |  |  | 89.18688 | 173.56755 | 0.56666 | 33.72797 | 70.00759 | 109.54802 | 142.07069 | 208.56427 | 0.39208 | 0.69618 |
| curie | specific_on_family | Oxide | xgboost | 1875 |  |  |  |  |  |  |  | 86.86212 | 167.0842 | 0.59843 | 38.62384 | 71.19841 | 105.73445 | 136.43444 | 200.14968 | 0.42594 | 0.71778 |
| curie | general_on_rest | Oxide | linear | 3290 |  |  |  |  |  |  |  | 169.38919 | 224.51512 | 0.39656 | 136.21556 | 159.49842 | 179.15013 | 209.34716 | 240.41879 | 0.3271 | 0.45859 |
| curie | general_on_rest | Oxide | gradient_boosting | 3290 |  |  |  |  |  |  |  | 101.11404 | 172.5538 | 0.64356 | 49.27693 | 88.47869 | 114.24934 | 152.01758 | 193.08017 | 0.56442 | 0.71386 |
| curie | general_on_rest | Oxide | xgboost | 3290 |  |  |  |  |  |  |  | 102.98174 | 171.41566 | 0.64824 | 51.30914 | 90.07304 | 116.67842 | 151.22162 | 191.31212 | 0.57536 | 0.71668 |
| curie | general_on_family | Intermetallic | linear | 2234 |  |  |  |  |  |  |  | 160.62705 | 209.73681 | 0.41893 | 133.05849 | 149.92556 | 171.67854 | 194.13364 | 225.06303 | 0.34595 | 0.48402 |
| curie | general_on_family | Intermetallic | gradient_boosting | 2234 |  |  |  |  |  |  |  | 82.33258 | 139.95594 | 0.74126 | 43.01835 | 74.69161 | 90.76923 | 124.26174 | 157.38655 | 0.67998 | 0.79356 |
| curie | general_on_family | Intermetallic | xgboost | 2234 |  |  |  |  |  |  |  | 86.87181 | 142.33826 | 0.73238 | 45.50235 | 78.11294 | 95.00457 | 126.89669 | 158.19421 | 0.67166 | 0.78516 |
| curie | specific_on_family | Intermetallic | linear | 2234 |  |  |  |  |  |  |  | 152.4207 | 202.8687 | 0.45636 | 124.79255 | 142.1737 | 164.44152 | 188.63546 | 219.27776 | 0.3831 | 0.51702 |
| curie | specific_on_family | Intermetallic | gradient_boosting | 2234 |  |  |  |  |  |  |  | 78.85666 | 135.41206 | 0.75779 | 38.08589 | 70.96364 | 86.60131 | 120.25047 | 151.24086 | 0.70475 | 0.80258 |
| curie | specific_on_family | Intermetallic | xgboost | 2234 |  |  |  |  |  |  |  | 80.67646 | 139.62374 | 0.74249 | 34.97516 | 70.73256 | 91.92604 | 123.72908 | 155.60035 | 0.68472 | 0.7955 |
| curie | general_on_rest | Intermetallic | linear | 2931 |  |  |  |  |  |  |  | 168.71766 | 233.86802 | 0.2805 | 125.993 | 149.43412 | 188.95916 | 209.76018 | 259.1048 | 0.13736 | 0.37529 |
| curie | general_on_rest | Intermetallic | gradient_boosting | 2931 |  |  |  |  |  |  |  | 103.82561 | 188.40269 | 0.53305 | 44.65136 | 86.13988 | 122.14907 | 160.93911 | 213.73141 | 0.41431 | 0.63598 |
| curie | general_on_rest | Intermetallic | xgboost | 2931 |  |  |  |  |  |  |  | 102.50948 | 185.97175 | 0.54503 | 46.09042 | 84.26824 | 120.21373 | 158.23932 | 209.60564 | 0.42924 | 0.63946 |
| curie | general_on_slice | Experimental | linear | 4882 |  |  |  |  |  |  |  | 166.22317 | 224.64333 | 0.36164 | 131.37712 | 153.27116 | 179.4628 | 208.65752 | 241.27438 | 0.27382 | 0.43729 |
| curie | general_on_slice | Experimental | gradient_boosting | 4882 |  |  |  |  |  |  |  | 94.23431 | 169.01438 | 0.63865 | 43.45229 | 83.40477 | 104.96227 | 150.72476 | 186.4474 | 0.562 | 0.70452 |
| curie | general_on_slice | Experimental | xgboost | 4882 |  |  |  |  |  |  |  | 95.51088 | 168.11497 | 0.64249 | 45.78867 | 83.98811 | 106.75014 | 150.81337 | 186.58896 | 0.56981 | 0.70277 |
| curie | general_on_rest | Experimental | linear | 283 |  |  |  |  |  |  |  | 147.88251 | 207.74031 | 0.34185 | 105.70019 | 127.93738 | 170.33874 | 178.94378 | 240.99221 | 0.21162 | 0.45068 |
| curie | general_on_rest | Experimental | gradient_boosting | 283 |  |  |  |  |  |  |  | 99.61824 | 171.646 | 0.55069 | 47.9588 | 82.23116 | 119.10387 | 136.47236 | 211.50573 | 0.37345 | 0.69585 |
| curie | general_on_rest | Experimental | xgboost | 283 |  |  |  |  |  |  |  | 99.79783 | 174.86069 | 0.5337 | 43.38192 | 82.25034 | 119.52675 | 137.20144 | 215.22697 | 0.32476 | 0.68258 |
| curie | general_on_slice | Computational | linear | 283 |  |  |  |  |  |  |  | 147.88251 | 207.74031 | 0.34185 | 105.70019 | 127.93738 | 170.33874 | 178.94378 | 240.99221 | 0.21162 | 0.45068 |
| curie | general_on_slice | Computational | gradient_boosting | 283 |  |  |  |  |  |  |  | 99.61824 | 171.646 | 0.55069 | 47.9588 | 82.23116 | 119.10387 | 136.47236 | 211.50573 | 0.37345 | 0.69585 |
| curie | general_on_slice | Computational | xgboost | 283 |  |  |  |  |  |  |  | 99.79783 | 174.86069 | 0.5337 | 43.38192 | 82.25034 | 119.52675 | 137.20144 | 215.22697 | 0.32476 | 0.68258 |
| curie | general_on_rest | Computational | linear | 4882 |  |  |  |  |  |  |  | 166.22317 | 224.64333 | 0.36164 | 131.37712 | 153.27116 | 179.4628 | 208.65752 | 241.27438 | 0.27382 | 0.43729 |
| curie | general_on_rest | Computational | gradient_boosting | 4882 |  |  |  |  |  |  |  | 94.23431 | 169.01438 | 0.63865 | 43.45229 | 83.40477 | 104.96227 | 150.72476 | 186.4474 | 0.562 | 0.70452 |
| curie | general_on_rest | Computational | xgboost | 4882 |  |  |  |  |  |  |  | 95.51088 | 168.11497 | 0.64249 | 45.78867 | 83.98811 | 106.75014 | 150.81337 | 186.58896 | 0.56981 | 0.70277 |
| ms_moment | general_overall | ALL | linear | 13129 |  |  |  |  |  |  |  | 4.58007 | 9.24213 | 0.26968 | 2.69231 | 4.44382 | 4.72166 | 8.5577 | 9.89103 | 0.24717 | 0.29365 |
| ms_moment | general_overall | ALL | gradient_boosting | 13129 |  |  |  |  |  |  |  | 2.57683 | 5.93429 | 0.6989 | 1.00204 | 2.47104 | 2.673 | 5.40774 | 6.43327 | 0.65682 | 0.74138 |
| ms_moment | general_overall | ALL | xgboost | 13129 |  |  |  |  |  |  |  | 2.53431 | 6.00699 | 0.69148 | 0.95106 | 2.42805 | 2.63677 | 5.43008 | 6.58251 | 0.64396 | 0.74164 |
| ms_moment | general_on_family | Transition Metal | linear | 10018 |  |  |  |  |  |  |  | 4.90797 | 9.73395 | 0.27793 | 2.86062 | 4.75112 | 5.07337 | 9.03207 | 10.50851 | 0.25662 | 0.29946 |
| ms_moment | general_on_family | Transition Metal | gradient_boosting | 10018 |  |  |  |  |  |  |  | 2.76081 | 6.01332 | 0.72443 | 1.12918 | 2.64415 | 2.885 | 5.53136 | 6.52883 | 0.6832 | 0.76431 |
| ms_moment | general_on_family | Transition Metal | xgboost | 10018 |  |  |  |  |  |  |  | 2.71447 | 6.10338 | 0.71611 | 1.06634 | 2.59873 | 2.83859 | 5.56359 | 6.68596 | 0.67311 | 0.76018 |
| ms_moment | specific_on_family | Transition Metal | linear | 10018 |  |  |  |  |  |  |  | 4.96205 | 9.70213 | 0.28264 | 2.9395 | 4.796 | 5.13098 | 9.013 | 10.45492 | 0.25982 | 0.30466 |
| ms_moment | specific_on_family | Transition Metal | gradient_boosting | 10018 |  |  |  |  |  |  |  | 2.75198 | 6.04681 | 0.72135 | 1.10309 | 2.63817 | 2.87689 | 5.51405 | 6.61262 | 0.67565 | 0.76338 |
| ms_moment | specific_on_family | Transition Metal | xgboost | 10018 |  |  |  |  |  |  |  | 2.69825 | 6.17425 | 0.70948 | 1.03982 | 2.58093 | 2.82447 | 5.61605 | 6.80225 | 0.66359 | 0.75623 |
| ms_moment | general_on_rest | Transition Metal | linear | 3111 |  |  |  |  |  |  |  | 3.52418 | 7.44063 | 0.14922 | 2.23573 | 3.3117 | 3.75908 | 5.77498 | 9.23856 | 0.09822 | 0.21816 |
| ms_moment | general_on_rest | Transition Metal | gradient_boosting | 3111 |  |  |  |  |  |  |  | 1.9844 | 5.67229 | 0.50556 | 0.70414 | 1.80841 | 2.15768 | 4.26163 | 7.26705 | 0.41739 | 0.61958 |
| ms_moment | general_on_rest | Transition Metal | xgboost | 3111 |  |  |  |  |  |  |  | 1.95414 | 5.68551 | 0.50325 | 0.66269 | 1.78141 | 2.14096 | 4.15065 | 7.41661 | 0.39647 | 0.63109 |
| ms_moment | general_on_family | Rare Earth | linear | 3361 |  |  |  |  |  |  |  | 4.98697 | 11.05398 | 0.29279 | 2.61675 | 4.6549 | 5.33153 | 9.39523 | 12.63174 | 0.24495 | 0.34675 |
| ms_moment | general_on_family | Rare Earth | gradient_boosting | 3361 |  |  |  |  |  |  |  | 2.52509 | 7.26321 | 0.69467 | 0.82889 | 2.30569 | 2.77359 | 5.70353 | 8.66731 | 0.61524 | 0.78144 |
| ms_moment | general_on_family | Rare Earth | xgboost | 3361 |  |  |  |  |  |  |  | 2.47353 | 7.29999 | 0.69157 | 0.79705 | 2.24829 | 2.71307 | 5.65889 | 8.80363 | 0.6048 | 0.78283 |
| ms_moment | specific_on_family | Rare Earth | linear | 3361 |  |  |  |  |  |  |  | 5.21421 | 10.7214 | 0.33471 | 2.9969 | 4.91253 | 5.53312 | 9.12508 | 12.24717 | 0.27535 | 0.40016 |
| ms_moment | specific_on_family | Rare Earth | gradient_boosting | 3361 |  |  |  |  |  |  |  | 2.70278 | 7.41948 | 0.68139 | 0.95341 | 2.49155 | 2.95141 | 5.94601 | 8.74956 | 0.60728 | 0.7697 |
| ms_moment | specific_on_family | Rare Earth | xgboost | 3361 |  |  |  |  |  |  |  | 2.64989 | 7.5785 | 0.66759 | 0.89669 | 2.43231 | 2.91471 | 6.00907 | 9.1945 | 0.57455 | 0.75644 |
| ms_moment | general_on_rest | Rare Earth | linear | 9768 |  |  |  |  |  |  |  | 4.44007 | 8.53017 | 0.25543 | 2.71795 | 4.29328 | 4.57898 | 7.85191 | 9.22858 | 0.23267 | 0.27558 |
| ms_moment | general_on_rest | Rare Earth | gradient_boosting | 9768 |  |  |  |  |  |  |  | 2.59464 | 5.40195 | 0.7014 | 1.0706 | 2.48556 | 2.69272 | 5.06446 | 5.76513 | 0.65377 | 0.74288 |
| ms_moment | general_on_rest | Rare Earth | xgboost | 9768 |  |  |  |  |  |  |  | 2.55522 | 5.49215 | 0.69134 | 1.01736 | 2.4431 | 2.66645 | 5.09824 | 5.94681 | 0.64158 | 0.73789 |
| ms_moment | general_on_family | Oxide | linear | 6056 |  |  |  |  |  |  |  | 5.62682 | 10.68635 | 0.25617 | 3.55713 | 5.39739 | 5.85031 | 9.75435 | 11.58364 | 0.2329 | 0.27881 |
| ms_moment | general_on_family | Oxide | gradient_boosting | 6056 |  |  |  |  |  |  |  | 3.54057 | 6.88481 | 0.69126 | 1.59093 | 3.37868 | 3.69941 | 6.45679 | 7.36552 | 0.63965 | 0.73501 |
| ms_moment | general_on_family | Oxide | xgboost | 6056 |  |  |  |  |  |  |  | 3.47954 | 6.9876 | 0.68197 | 1.55463 | 3.30322 | 3.65241 | 6.46616 | 7.58022 | 0.62744 | 0.7315 |
| ms_moment | specific_on_family | Oxide | linear | 6056 |  |  |  |  |  |  |  | 5.61163 | 10.29395 | 0.30979 | 3.37148 | 5.38021 | 5.8303 | 9.44518 | 11.11089 | 0.27704 | 0.33691 |
| ms_moment | specific_on_family | Oxide | gradient_boosting | 6056 |  |  |  |  |  |  |  | 3.52654 | 6.91556 | 0.68849 | 1.58145 | 3.36081 | 3.68393 | 6.45173 | 7.4318 | 0.63683 | 0.7351 |
| ms_moment | specific_on_family | Oxide | xgboost | 6056 |  |  |  |  |  |  |  | 3.51524 | 7.09202 | 0.67239 | 1.54153 | 3.34052 | 3.6863 | 6.5469 | 7.67243 | 0.6147 | 0.72625 |
| ms_moment | general_on_rest | Oxide | linear | 7073 |  |  |  |  |  |  |  | 3.68383 | 7.79578 | 0.24771 | 2.06099 | 3.52331 | 3.8535 | 6.79783 | 8.84918 | 0.20095 | 0.29823 |
| ms_moment | general_on_rest | Oxide | gradient_boosting | 7073 |  |  |  |  |  |  |  | 1.75166 | 4.97825 | 0.69322 | 0.70878 | 1.65101 | 1.86031 | 3.91213 | 5.9103 | 0.61699 | 0.77108 |
| ms_moment | general_on_rest | Oxide | xgboost | 7073 |  |  |  |  |  |  |  | 1.72498 | 5.01732 | 0.68839 | 0.66188 | 1.6232 | 1.8347 | 3.90872 | 5.99672 | 0.60423 | 0.7732 |
| ms_moment | general_on_family | Intermetallic | linear | 5913 |  |  |  |  |  |  |  | 3.48172 | 6.70004 | 0.20762 | 2.0561 | 3.33954 | 3.64252 | 5.82359 | 7.60523 | 0.16002 | 0.2563 |
| ms_moment | general_on_family | Intermetallic | gradient_boosting | 5913 |  |  |  |  |  |  |  | 1.59853 | 4.27503 | 0.6774 | 0.67905 | 1.50112 | 1.71175 | 3.42072 | 5.16617 | 0.61682 | 0.74829 |
| ms_moment | general_on_family | Intermetallic | xgboost | 5913 |  |  |  |  |  |  |  | 1.56621 | 4.26894 | 0.67832 | 0.63995 | 1.47126 | 1.67271 | 3.38196 | 5.19036 | 0.61094 | 0.75483 |
| ms_moment | specific_on_family | Intermetallic | linear | 5913 |  |  |  |  |  |  |  | 2.93805 | 6.32061 | 0.29482 | 1.72629 | 2.80002 | 3.09479 | 5.31603 | 7.33732 | 0.25044 | 0.349 |
| ms_moment | specific_on_family | Intermetallic | gradient_boosting | 5913 |  |  |  |  |  |  |  | 1.54871 | 4.1515 | 0.69578 | 0.62003 | 1.45441 | 1.65887 | 3.36753 | 4.9561 | 0.64315 | 0.75019 |
| ms_moment | specific_on_family | Intermetallic | xgboost | 5913 |  |  |  |  |  |  |  | 1.47552 | 4.05855 | 0.70925 | 0.55316 | 1.38694 | 1.57961 | 3.3288 | 4.80075 | 0.66395 | 0.76099 |
| ms_moment | general_on_rest | Intermetallic | linear | 7216 |  |  |  |  |  |  |  | 5.4801 | 10.89153 | 0.26729 | 3.30435 | 5.26908 | 5.69319 | 9.96204 | 11.8455 | 0.23903 | 0.29332 |
| ms_moment | general_on_rest | Intermetallic | gradient_boosting | 7216 |  |  |  |  |  |  |  | 3.37848 | 7.00691 | 0.69674 | 1.44451 | 3.22131 | 3.52069 | 6.37086 | 7.74109 | 0.64716 | 0.74693 |
| ms_moment | general_on_rest | Intermetallic | xgboost | 7216 |  |  |  |  |  |  |  | 3.32759 | 7.12173 | 0.68672 | 1.39392 | 3.15665 | 3.47798 | 6.43114 | 7.95566 | 0.63353 | 0.74461 |
| ms_moment | general_on_slice | Computational | linear | 13129 |  |  |  |  |  |  |  | 4.58007 | 9.24213 | 0.26968 | 2.69231 | 4.44382 | 4.72166 | 8.5577 | 9.89103 | 0.24717 | 0.29365 |
| ms_moment | general_on_slice | Computational | gradient_boosting | 13129 |  |  |  |  |  |  |  | 2.57683 | 5.93429 | 0.6989 | 1.00204 | 2.47104 | 2.673 | 5.40774 | 6.43327 | 0.65682 | 0.74138 |
| ms_moment | general_on_slice | Computational | xgboost | 13129 |  |  |  |  |  |  |  | 2.53431 | 6.00699 | 0.69148 | 0.95106 | 2.42805 | 2.63677 | 5.43008 | 6.58251 | 0.64396 | 0.74164 |

### Table S1. Secondary/exploratory targets - repeated formula-grouped 5x3 CV, Tier 1

| Target | Unit | N | Model | MAE (95% CI) | R² (95% CI) | Rank corr (95% CI) |
|---|---|---|---|---|---|---|
| K1 | J/m^3 | 1,862 | Dummy reference | 4.184e+06 [3.414e+06, 5.27e+06] | -0.00195 [-0.00896, -0.00174] | -0.0144 [-0.0554, 0.0283] |
| K1 | J/m^3 | 1,862 | Linear / logistic | 1.062e+07 [4.895e+06, 2.177e+07] | -179 [-1.2e+03, -0.0263] | 0.197 [0.13, 0.257] |
| K1 | J/m^3 | 1,862 | Gradient Boosting (hist) | 4.008e+06 [3.269e+06, 5.077e+06] | 0.129 [-0.103, 0.193] | 0.345 [0.252, 0.432] |
| K1 | J/m^3 | 1,862 | XGBoost | 3.072e+06 [2.353e+06, 4.078e+06] | 0.176 [-0.0976, 0.283] | 0.558 [0.469, 0.622] |
| K1 (signed log10) | sign*log10(1+|K1|) | 1,862 | Dummy reference | 2.354 [2.234, 2.471] | -0.00335 [-0.017, -0.00108] | -0.112 [-0.251, 0.00975] |
| K1 (signed log10) | sign*log10(1+|K1|) | 1,862 | Linear / logistic | 3.18 [1.966, 5.689] | -253 [-818, 0.152] | 0.54 [0.463, 0.6] |
| K1 (signed log10) | sign*log10(1+|K1|) | 1,862 | Gradient Boosting (hist) | 1.813 [1.634, 2.049] | 0.204 [0.063, 0.308] | 0.595 [0.514, 0.658] |
| K1 (signed log10) | sign*log10(1+|K1|) | 1,862 | XGBoost | 1.769 [1.587, 2.036] | 0.204 [0.0015, 0.332] | 0.629 [0.54, 0.688] |
| Ms (mass magnetization) | emu/g | 4,318 | Dummy reference | 32.58 [31.08, 34.35] | -0.00113 [-0.00346, -0.000792] | -0.0487 [-0.0724, -0.0233] |
| Ms (mass magnetization) | emu/g | 4,318 | Linear / logistic | 24.28 [23.34, 25.55] | 0.182 [-0.28, 0.462] | 0.574 [0.543, 0.601] |
| Ms (mass magnetization) | emu/g | 4,318 | Gradient Boosting (hist) | 17.72 [16.92, 18.53] | 0.631 [0.59, 0.667] | 0.74 [0.718, 0.761] |
| Ms (mass magnetization) | emu/g | 4,318 | XGBoost | 17.61 [16.82, 18.49] | 0.63 [0.584, 0.666] | 0.747 [0.724, 0.769] |
| Ms (volume magnetization) | A/m | 788 | Dummy reference | 3.924e+05 [3.646e+05, 4.268e+05] | -0.0084 [-0.0383, -0.00468] | -0.108 [-0.19, -0.00552] |
| Ms (volume magnetization) | A/m | 788 | Linear / logistic | 2.569e+05 [2.36e+05, 2.808e+05] | 0.438 [0.324, 0.535] | 0.705 [0.643, 0.764] |
| Ms (volume magnetization) | A/m | 788 | Gradient Boosting (hist) | 2.37e+05 [2.151e+05, 2.618e+05] | 0.455 [0.315, 0.576] | 0.711 [0.641, 0.771] |
| Ms (volume magnetization) | A/m | 788 | XGBoost | 2.335e+05 [2.118e+05, 2.587e+05] | 0.444 [0.299, 0.561] | 0.709 [0.639, 0.77] |

### Table S1b. Secondary targets - exploratory matched Tier claims (plan s12 rule)

| target | from_tier | to_tier | n_algorithms_stable_improve | n_algorithms_stable_degrade | claim | claim_tree_models_only |
|---|---|---|---|---|---|---|
| K1 | tier1 | tier2 | 0 | 1 | no claim | no claim |
| K1 | tier2 | tier3 | 0 | 0 | no claim | no claim |
| K1 | tier1 | tier3 | 0 | 1 | no claim | no claim |
| K1 (signed log10) | tier1 | tier2 | 0 | 0 | no claim | no claim |
| K1 (signed log10) | tier2 | tier3 | 0 | 1 | no claim | no claim |
| K1 (signed log10) | tier1 | tier3 | 0 | 1 | no claim | no claim |
| Ms (mass magnetization) | tier1 | tier2 | 0 | 0 | no claim | no claim |
| Ms (mass magnetization) | tier2 | tier3 | 0 | 0 | no claim | no claim |
| Ms (mass magnetization) | tier1 | tier3 | 0 | 0 | no claim | no claim |
| Ms (volume magnetization) | tier1 | tier2 | 0 | 1 | no claim | no claim |
| Ms (volume magnetization) | tier2 | tier3 | 0 | 1 | no claim | no claim |
| Ms (volume magnetization) | tier1 | tier3 | 1 | 0 | no claim | no claim |

### Table S2. Top-5 descriptors by mean |SHAP| (matched test sets; XGBoost)

| Target | Tier | #1 | #2 | #3 | #4 | #5 |
|---|---|---|---|---|---|---|
| Magnetic ordering | Tier 1 | magnetic_element_fraction (0.364) | average_unpaired_electron_proxy (0.258) | group_variance (0.206) | valence_electron_concentration (0.195) | p_block_fraction (0.176) |
| Magnetic ordering | Tier 2 | magnetic_element_fraction (0.364) | average_unpaired_electron_proxy (0.243) | group_variance (0.199) | valence_electron_concentration (0.177) | average_melting_temperature (0.168) |
| Magnetic ordering | Tier 3 | p3_point_group (0.435) | magnetic_element_fraction (0.35) | p3_energy_above_hull (0.218) | p3_formation_energy_per_atom (0.194) | p3_dielectric_static (0.182) |
| Curie temperature | Tier 1 | valence_electron_concentration (89.2) | transition_metal_fraction (33) | average_unpaired_electron_proxy (31.2) | fraction_Fe (23.9) | average_atomic_mass (20.6) |
| Curie temperature | Tier 2 | valence_electron_concentration (93.3) | transition_metal_fraction (34.3) | average_unpaired_electron_proxy (28.3) | electronegativity_variance (25.8) | fraction_Fe (20.8) |
| Curie temperature | Tier 3 | p3_point_group (91.3) | p3_volume (63.6) | valence_electron_concentration (51.3) | fraction_Fe (16.8) | fraction_Co (16.4) |
| Ms (moment per unit cell) | Tier 1 | magnetic_element_fraction (0.691) | fraction_Mn (0.403) | electronegativity_variance (0.372) | average_unpaired_electron_proxy (0.329) | electronegativity_difference (0.252) |
| Ms (moment per unit cell) | Tier 2 | magnetic_element_fraction (0.739) | electronegativity_variance (0.397) | fraction_Mn (0.336) | average_unpaired_electron_proxy (0.334) | average_atomic_radius (0.232) |
| Ms (moment per unit cell) | Tier 3 | magnetic_element_fraction (0.621) | p3_volume (0.498) | fraction_Mn (0.387) | fraction_Fe (0.308) | average_unpaired_electron_proxy (0.3) |

### Table S3. Tier 3 physics-family ablation (primary metric)

| target | analysis | physics_family | n_family_features | metric | reference_value | variant_value | value_gained_by_family | ci_low | ci_high | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| ordering | add_one_to_tier2 | Thermodynamic stability | 3 | macro_f1 | 0.38881 | 0.3737 | -0.01512 | -0.04662 | 0.02849 | no stable contribution |
| ordering | drop_one_from_tier3 | Thermodynamic stability | 3 | macro_f1 | 0.38018 | 0.3645 | 0.01568 | -0.00401 | 0.03787 | no stable contribution |
| ordering | add_one_to_tier2 | Electronic structure | 6 | macro_f1 | 0.38881 | 0.41412 | 0.02531 | -0.00387 | 0.0545 | no stable contribution |
| ordering | drop_one_from_tier3 | Electronic structure | 6 | macro_f1 | 0.38018 | 0.38575 | -0.00558 | -0.03147 | 0.01531 | no stable contribution |
| ordering | add_one_to_tier2 | Symmetry | 3 | macro_f1 | 0.38881 | 0.38462 | -0.0042 | -0.04383 | 0.03321 | no stable contribution |
| ordering | drop_one_from_tier3 | Symmetry | 3 | macro_f1 | 0.38018 | 0.39185 | -0.01167 | -0.03116 | 0.00815 | no stable contribution |
| ordering | add_one_to_tier2 | Structural packing | 3 | macro_f1 | 0.38881 | 0.39632 | 0.00751 | -0.01466 | 0.03293 | no stable contribution |
| ordering | drop_one_from_tier3 | Structural packing | 3 | macro_f1 | 0.38018 | 0.3909 | -0.01072 | -0.02702 | 0.00736 | no stable contribution |
| ordering | add_one_to_tier2 | Elastic response | 4 | macro_f1 | 0.38881 | 0.40059 | 0.01177 | -0.01741 | 0.04086 | no stable contribution |
| ordering | drop_one_from_tier3 | Elastic response | 4 | macro_f1 | 0.38018 | 0.40835 | -0.02817 | -0.07649 | 0.01376 | no stable contribution |
| ordering | add_one_to_tier2 | Dielectric & optical | 5 | macro_f1 | 0.38881 | 0.37878 | -0.01003 | -0.03451 | 0.01739 | no stable contribution |
| ordering | drop_one_from_tier3 | Dielectric & optical | 5 | macro_f1 | 0.38018 | 0.4025 | -0.02233 | -0.05384 | 0.00499 | no stable contribution |
| curie | add_one_to_tier2 | Thermodynamic stability | 3 | mae | 268.38391 | 288.70185 | -20.31793 | -41.85431 | 9.48764 | no stable contribution |
| curie | drop_one_from_tier3 | Thermodynamic stability | 3 | mae | 207.44482 | 238.02069 | 30.57586 | -40.08798 | 110.48729 | no stable contribution |
| curie | add_one_to_tier2 | Electronic structure | 6 | mae | 268.38391 | 250.8365 | 17.54742 | 2.96156 | 28.56854 | stable contribution |
| curie | drop_one_from_tier3 | Electronic structure | 6 | mae | 207.44482 | 220.40132 | 12.9565 | -38.23758 | 65.18207 | no stable contribution |
| curie | add_one_to_tier2 | Symmetry | 3 | mae | 268.38391 | 210.60636 | 57.77755 | 0.26269 | 108.11492 | stable contribution |
| curie | drop_one_from_tier3 | Symmetry | 3 | mae | 207.44482 | 248.33395 | 40.88912 | -34.59774 | 139.09838 | no stable contribution |
| curie | add_one_to_tier2 | Structural packing | 3 | mae | 268.38391 | 279.84001 | -11.4561 | -62.31678 | 40.32093 | no stable contribution |
| curie | drop_one_from_tier3 | Structural packing | 3 | mae | 207.44482 | 261.65196 | 54.20713 | -24.18961 | 146.5656 | no stable contribution |
| curie | add_one_to_tier2 | Elastic response | 4 | mae | 268.38391 | 308.99857 | -40.61466 | -91.40337 | 9.05057 | no stable contribution |
| curie | drop_one_from_tier3 | Elastic response | 4 | mae | 207.44482 | 252.03286 | 44.58803 | -29.63558 | 128.20525 | no stable contribution |
| curie | add_one_to_tier2 | Dielectric & optical | 5 | mae | 268.38391 | 286.07703 | -17.69312 | -47.49093 | 21.01453 | no stable contribution |
| curie | drop_one_from_tier3 | Dielectric & optical | 5 | mae | 207.44482 | 200.26461 | -7.18021 | -33.74836 | 16.26687 | no stable contribution |
| ms_moment | add_one_to_tier2 | Thermodynamic stability | 3 | mae | 1.89912 | 1.88417 | 0.01495 | -0.04097 | 0.07449 | no stable contribution |
| ms_moment | drop_one_from_tier3 | Thermodynamic stability | 3 | mae | 1.81592 | 1.83669 | 0.02077 | -0.01908 | 0.06723 | no stable contribution |
| ms_moment | add_one_to_tier2 | Electronic structure | 6 | mae | 1.89912 | 1.88223 | 0.01689 | -0.05126 | 0.08381 | no stable contribution |
| ms_moment | drop_one_from_tier3 | Electronic structure | 6 | mae | 1.81592 | 1.79758 | -0.01834 | -0.07069 | 0.0337 | no stable contribution |
| ms_moment | add_one_to_tier2 | Symmetry | 3 | mae | 1.89912 | 1.90185 | -0.00273 | -0.06707 | 0.06577 | no stable contribution |
| ms_moment | drop_one_from_tier3 | Symmetry | 3 | mae | 1.81592 | 1.82345 | 0.00753 | -0.05285 | 0.06838 | no stable contribution |
| ms_moment | add_one_to_tier2 | Structural packing | 3 | mae | 1.89912 | 1.85448 | 0.04464 | -0.01564 | 0.10644 | no stable contribution |
| ms_moment | drop_one_from_tier3 | Structural packing | 3 | mae | 1.81592 | 1.87423 | 0.05831 | 0.00845 | 0.10969 | stable contribution |
| ms_moment | add_one_to_tier2 | Elastic response | 4 | mae | 1.89912 | 1.88881 | 0.01031 | -0.04872 | 0.07061 | no stable contribution |
| ms_moment | drop_one_from_tier3 | Elastic response | 4 | mae | 1.81592 | 1.80828 | -0.00764 | -0.04236 | 0.03066 | no stable contribution |
| ms_moment | add_one_to_tier2 | Dielectric & optical | 5 | mae | 1.89912 | 1.86233 | 0.03678 | -0.02766 | 0.09755 | no stable contribution |
| ms_moment | drop_one_from_tier3 | Dielectric & optical | 5 | mae | 1.81592 | 1.80865 | -0.00727 | -0.06431 | 0.04462 | no stable contribution |
