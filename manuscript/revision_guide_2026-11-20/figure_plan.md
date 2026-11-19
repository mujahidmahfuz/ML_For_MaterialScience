# B. Revised figure package (guide section 6)

Built by `paper/manuscript/springer_nature/make_figures_sn.py` from the saved result files (no model refitted, no number changed).
PDFs sit next to `manuscript.tex`; PNG previews in `springer_nature/png/`. Width 131 mm (class text width), Arial 7 pt,
categorical colours = slots 1-4 of a validated colour-blind-safe order; every series also has a legend or a direct label.

Nature Communications allows 10 display items. The paper uses 8: Tables 1-3 and Figs 1-5. Nature Communications has no
Extended Data, so the former Extended Data items moved to the Supplementary Information.

| Figure | Content (panels) | One-sentence scientific takeaway |
|---|---|---|
| **Fig. 1** Magnetic data provenance and label consistency (NEW) | a, sources of each target; b, ordering classes by provenance; c, confusion matrix of Materials Project vs experimental labels (949 formulas); d, Cohen's kappa and agreement for all shared formulas, bulk only, same space group, same space group + stoichiometric + bulk, and each source against MAGNDATA structures | Computed and experimental ordering labels describe magnetic order by different conventions, even for the same crystal structure, so a pooled ordering accuracy cannot be read without its provenance. |
| **Fig. 2** Incremental predictive value of physical descriptors (was Fig. 1) | a-d, Tier 1 to 2 and Tier 1 to 3 changes with refit-aware intervals for ordering, Curie temperature, moment per cell, moment per formula unit; grey = Tier 3 beyond a single site-count descriptor (now also in c) | Non-magnetic DFT descriptors add no detectable information for ordering or Curie temperature, and their small gain for the computed moment is largely a cell-size effect. |
| **Fig. 3** Reliability of predictive uncertainty (was Fig. 2) | a,b, coverage of 90% intervals under three conformal methods for all materials, highest predictions and one source/chemistry subgroup, with mean interval widths under the axis; c, coverage per ordering class for marginal vs class-conditional sets with mean set sizes | Calibration that holds on average fails for antiferromagnets, ferrimagnets and the highest Curie temperatures, and the methods that repair it trade informativeness (set size, interval width) for subgroup coverage. |
| **Fig. 4** Chemical novelty and predictive generalization (old Figs 3 + 4 merged) | a,b, MAE and R2 by nested novelty subset before/after the audit (with n); c, MAE by composition-distance bin; d, coverage by distance bin with mean interval widths | Predictive reliability decays with chemical novelty, and uncertainty intervals widen too little to keep up; in unseen chemical systems performance is much weaker, with wide uncertainty (69 records, 18 clusters). |
| **Fig. 5** Reliability-aware screening (NEW) | a, risk-coverage curves on the 465 blind external records (distance vs interval-width abstention; curves descriptive, points with cluster-bootstrap intervals); b, the same rules on the ten internal test sets; c, Tc > 300 K screen: point accuracy, share decided by the interval rule, accuracy of those decisions | Selective prediction improves the reliability of what is kept and supports first-stage filtering, at the cost of leaving many candidates undecided. |

Supplementary Figures: Supplementary Fig. 1 = old Extended Data Fig. 1 (error against distance for every blind record);
Supplementary Fig. 2 = old Extended Data Fig. 2 (summary schematic), its rows renamed to the four findings of the revised paper
(label provenance, added physics, calibration, chemical novelty).

Checks done: every figure was rendered and inspected as PNG and inside the compiled PDF; no label collisions or clipped text;
measured results only (the schematic is the only illustrative item and is in the SI). Legends state n, metrics, units,
interval type and the main qualification (agreement is not correctness; a null with a wide interval is not absence;
coverage is guaranteed only over exchangeable formula groups; unseen-system subsets are small).
