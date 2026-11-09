# Tables

Built by `python scripts/make_tables.py` from `../data/` and `../results/`. Each table has three files:
- `<name>.csv`: the values;
- `<name>.tex`: a booktabs fragment for the sn-jnl manuscript, included with `\input{../tables/<name>.tex}`;
- `<name>.notes.txt`: the table footnote.

| Table | File | Content | Source |
|---|---|---|---|
| 1 | `table1_dataset` | Targets, records, formulas, split sizes, matched Tier 1/2/3 populations | `data/splits/v1.4`, `data/analysis_dataset/v1.4` |
| 2 | `table2_physics_descriptors` | Tier 1→2 and Tier 1→3 effects on matched populations, per target and algorithm (RQ1) | `results/rq1_physics_descriptors/matched_tiers`, `ms_per_atom` |
| 3 | `table3_regression_intervals` | Coverage and width of 90% intervals for Curie and Ms: frozen split and 10 splits (RQ2) | `results/rq2_uncertainty/{curie,ms_moment,repeated_splits}` |
| 4 | `table4_ordering_calibration` | ECE of ordering probabilities; marginal vs class-conditional set coverage per class (RQ2) | `results/rq2_uncertainty/ordering`, `repeated_splits/ordering` |
| 5 | `table5_external_benchmark` | External Curie benchmark by novelty subset, after the audit (RQ3) | `results/rq3_generalization/external_benchmark` |
| 6 | `table6_generalization_internal` | Leave chemical system out; ordering across label provenance (RQ3) | `results/rq3_generalization/{leave_chemical_system_out,label_provenance}` |
| S1 | `tableS1_benchmark_audit` | Audit checks A1-A8 and the number of records affected | `external_benchmark/audit_counts.csv` |
| S2 | `tableS2_subset_comparisons` | Grouped-bootstrap differences between subsets under three clusterings | `external_benchmark/subset_comparisons.csv` |
| S3 | `tableS3_error_vs_distance` | Error, width and coverage by composition-distance quartile (blind records) | `external_benchmark/similarity_bins.csv` |
