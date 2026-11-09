# Figures

Built by `python scripts/make_figures.py` from `../results/`. Each figure is a vector PDF (for LaTeX) plus a 300-dpi PNG. Colours follow a colour-blind-checked two-colour palette, and every series has a legend.

| Figure | File | Shows | Source |
|---|---|---|---|
| 1 | `fig1_physics_descriptors` | Tier 1→2 and Tier 1→3 effects with 95% intervals for ordering, Curie, Ms per cell and Ms per atom (RQ1) | `results/rq1_physics_descriptors` |
| 2 | `fig2_uncertainty_calibration` | Interval coverage overall vs hardest decile over 10 splits (Curie, Ms); per-class coverage of ordering prediction sets (RQ2) | `results/rq2_uncertainty` |
| 3 | `fig3_external_benchmark` | External benchmark MAE and R² per novelty subset, original vs audited (RQ3) | `external_benchmark/subset_metrics_bootstrap.csv` |
| 4 | `fig4_error_vs_distance` | Error, interval width and coverage against composition distance to the training set (RQ3) | `external_benchmark/similarity_bins.csv` |
| S1 | `figS1_blind_scatter` | Absolute error against composition distance for every truly blind record | `external_benchmark/similarity_records.csv` |

In Figure 1b the Ridge Tier 1→3 Curie result (−825 K) is an unstable fit and lies far off scale, so it is drawn as an arrow at the axis edge.
