# D. Scientific-validation note (guide section 5)

Which central claims are fully supported, which need qualification, and whether new analysis was essential. One targeted
analysis was run (A23, item 5.1); everything else was checked against the saved result files. No broad new modelling.

## 5.1 Computed versus experimental ordering labels (headline result) -> SUPPORTED, now phase-checked

**Check run (A23, `final/revision/scripts/a23_label_comparability.py`; plan and claim rule written in
`final/revision/PLAN.md` before the run; outputs `paper/results/revision/a23_label_comparability/`).**
- For the 949 shared formulas, all 1,940 Materials Project (MP) entries of the same composition were taken from the raw file
  used for training (entry-level ordering of every polymorph); space groups and energies above hull were fetched from the MP
  API. The recorded orderings equal those served by the API for every entry (no database-version drift).
- Experimental space groups were parsed with the unchanged A19 rules; 682 of 949 formulas report one.

| Subset | Formulas | Agreement [95% CI] | kappa [95% CI] | Exp. AFM called FM by MP |
|---|---|---|---|---|
| All shared formulas | 949 | 0.28 [0.25, 0.31] | 0.00 [-0.03, 0.03] | 66% |
| Bulk records only | 908 | 0.27 [0.24, 0.30] | 0.00 [-0.03, 0.03] | 66% |
| Same space group (phase-matched) | 330 | 0.25 [0.21, 0.30] | 0.01 [-0.03, 0.06] | 71% |
| Same s.g., stoichiometric, bulk | 314 | 0.25 [0.20, 0.30] | 0.02 [-0.02, 0.06] | 70% |

- Claim rule outcome: phase-matched n >= 30 and kappa upper limit < 0.40 -> "disagreement persists among phase-matched records".
- Label definitions: of 29 phase-matched formulas FM in experiment and FiM in MP, 18 contain a rare earth (antiparallel
  sublattices often called "ferromagnetic" experimentally) -> part of the disagreement is definitional; stated in Results.
- 103 of 949 formulas have MP polymorphs with different labels; 84 MP entries have "Unknown" ordering (not used as labels).
- Representative sample: a seeded random sample of 30 shared formulas with their source fields (material type, space group,
  crystal structure, DOI, MP entries with ordering, space group, energy above hull) is in
  `final/revision/outputs/a23_label_comparability/shared_formula_sample.csv` (kept local: it carries source fields of
  compilations of undocumented origin, as for A19). The sample shows the three kinds of case: the same space group with
  different magnetic labels (CeMnAsO: AFM in experiment, FiM in MP, both P4/nmm), polymorph mismatch (BaFe2Se3: AFM in
  experiment for Pnma-type records, FM in MP for a Cmcm entry) and rare-earth naming (Tb2Fe17: FM in experiment, FiM in MP,
  both P6_3/mmc).
- Reading of original papers was not done; the comparison is at the level of source records and space groups.

**Wording in the paper:** reported as disagreement between source-specific labelling conventions; which side matches
measured order is judged only from MAGNDATA structures (experimental 92% vs MP 22% agreement, collinear compounds only);
the text states explicitly that this does not show a given DFT calculation is wrong, and that a space group fixes neither the
magnetic cell nor the sample composition.

## 5.2 External Curie benchmark -> SUPPORTED, definitions documented

Checked in Methods ("External benchmark and audit"), Results (section "Reliability decays with chemical novelty"), Table 3 and
Supplementary Tables 1-4:
- composition normalisation (spelling-independent element fractions) and duplicate identification; DOI normalisation incl.
  URL prefixes; exclusion of 60 computational labels, 18 malformed compositions, 35 out-of-definition values (105 total);
- records vs unique compositions vs source-paper clusters are reported separately (e.g. 465 blind records from 81 clusters;
  69 unseen-system records from 18 clusters);
- uncertainty for the 69 unseen-system records: BCa and percentile cluster-bootstrap intervals, three clustering units,
  prespecified wording rule ("no skill" only if the R2 upper limit <= 0.2; it is 0.64 / 0.21) -> "much weaker, with wide
  uncertainty"; skill neither established nor excluded;
- the text now says explicitly: "The table as a whole is therefore not an independent validation; only this blind subset is."

## 5.3 Moment normalisation -> SUPPORTED

- Per-atom values in the paper (gradient boosting 2.9%, XGBoost 2.8%, ridge 6.0%; intervals 1.5-4.4, 1.6-3.9, 5.1-6.8%)
  equal the corrected-pairing file `paper/results/rq1_physics_descriptors/ms_per_atom/peratom_corrected_tier_effect.csv`
  (population "corrected", 10,821 rows); the withdrawn 14/9/6% values appear nowhere in the manuscript.
- Methods now has a paragraph that defines the four quantities and states they are never interchanged: DFT moment per cell
  (primary), per formula unit (same-calculation atom count), per atom (same-calculation atom count; earlier 25.4% mismatch
  corrected), experimental saturation magnetization (secondary, not analysed).

## 5.4 Descriptor availability and phase matching -> QUALIFIED in the text

New Methods paragraph ("Descriptors and their availability") and a Results paragraph: Tier 1/2 are available for any
composition; Tier 3 exists only after a DFT calculation, describes the computed lowest-energy polymorph (not necessarily the
measured phase) for the experimental targets, and comes from the same database and often the same calculation as the label
for the moment. The same-space-group test (536 records) is cited as partial evidence only (18% of records report a space group).

## 5.5 Uncertainty and reproducibility claims -> QUALIFIED in the text

- Exchangeability: Methods now states that the exchangeable unit is the formula group (calibration and test drawn by formula),
  that the guarantee concerns formulas drawn like the calibration formulas, and that it does not extend to another source,
  unseen systems or the external table (observed coverage reported there). Results 3.3 says the same in one sentence.
- Repeated measurements: design effect 12-17; ~4,200 calibration rows behave like 250-340 independent ones (Results + SI 6).
- XGBoost thread count: documented in Methods (thread count acts as a seed; 8 realizations for Tc and m_cell tier results;
  single realization for ordering, m_fu, the site-count control and the magnetic-physics test), and in figure legends.

## Claims that are fully supported vs qualified

| Claim | Status |
|---|---|
| Computed and experimental ordering labels disagree (chance-level), also when phase-matched by space group | Supported (A2, A23) |
| Experimental labels agree with measured magnetic structures far more than MP labels | Supported for ordered collinear compounds (A16); not independent literature |
| DFT descriptors give no detectable gain for ordering and Tc | Supported as "no detectable gain"; detectable effects 27-56 K / 0.04-0.09 stated |
| Moment gain is mostly cell size | Supported for per-cell and per-f.u. tree models; per-atom modest gain remains (secondary) |
| Marginal calibration hides AFM/FiM and high-Tc failures | Supported (10 splits) |
| Error grows with chemical distance; unseen systems much weaker | Supported with wide uncertainty (69 records, 18 clusters) |
| Abstention supports first-stage screening | Supported for filtering only; no ranking or discovery claim |

## Is any further analysis essential?

No. The one check that could have changed the headline (phase matching of the ordering labels) was run and left it intact.
Analyses that would strengthen the paper but are not essential: magnetic-structure-level matching (beyond space group),
DFT re-enumeration of AFM configurations for a sample of disagreeing compounds, and end-to-end structure models under the
matched design. These are named as limitations / future work in the Discussion.
