# C. Novelty assessment against the closest literature (guide section 7)

Internal document (the guide says the table need not appear in the manuscript). Sources: the project's literature extraction
`paper/results/revision/research/prior_results_table.md` (every number there was read from the paper, with location; several
papers were read as arXiv versions, see its notes) and the verified bibliography `springer_nature/references.bib`. For the
benchmark and method papers (rows 9-12) only the scope stated in the title and abstract is used here; no numbers are claimed
for them. "n/s" = not stated in what was read.

## Comparison table (12 studies)

| # | Study | Main question | Data and property | Model / evaluation | Label provenance | Chemical novelty | Uncertainty | Principal finding (as reported) | Issue left open that this paper addresses |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Nelson & Sanvito 2019, Phys. Rev. Mater. | Predict Tc of ferromagnets from composition | ~2,500 experimental Tc (AtomWork, Springer Materials, handbook) | Composition features; RF, KRR, NN; single train/test + 3-fold CV | Single compiled source; duplicates merged by median | Qualitative traces across binaries/ternaries only | n/s | RF test MAE 57 K, R2 0.87 | No grouped or external test; no calibration; no check of what labels mean |
| 2 | Long et al. 2021, Mater. Res. Lett. | FM vs AFM classification and Tc regression | 2,805 AtomWork intermetallics (+ICSD structures) | Chemical + structural (SOAP) descriptors; RF; 90/10 + 10-fold CV | Single experimental source | None | n/s | Accuracy 86% (CHEM+STR) vs 82% (CHEM); Tc R2 0.92 vs 0.90 | Structure helps slightly on a random split; not tested on matched populations, with size controls or on new chemistry |
| 3 | Belot et al. 2023, Appl. Phys. Lett. | Predict high-Tc materials | DS1 (2,557) and DS2 (3,194) experimental Tc; 1,189 compounds overlap | Element fractions; RF, kNN; random split + external DS2 | Two compilations, overlap noted | External dataset test only | n/s | RF MAE 69 K; on DS2 90 K | External set overlaps the training set; novelty not defined by composition or system |
| 4 | Merker et al. 2022, iScience | Classify magnetic ordering and propagation vector from structure | 34,856 MP structures (DFT labels); 1,134 MAGNDATA for propagation vectors | E(3)-equivariant network; random 80/10/10, 20 repeats | DFT labels from pymatgen; experimental structures used for a different task | None | n/s | Ordering accuracy 77.8%; AFM F1 0.69 | Does not compare DFT labels with measured magnetic structures for the same compounds |
| 5 | Itani, Zhang & Zang 2025, Nat. Commun. (NEMAD) | Build an LLM-extracted experimental magnetic database and models | 67,573 entries; classification set adds 11,389 MP non-magnets | RF/XGBoost/ENN on composition; stratified random splits | Experimental FM/AFM with DFT-derived NM: source and class mixed | None quantitative | n/s | Ordering accuracy 0.90-0.91; Tc R2 0.84-0.87, MAE 56-62 K | Class depends on source; no grouped or cross-source test; no calibration |
| 6 | Abedi Orang, Alaei & Oganov 2026, Comput. Mater. Sci. | Tc regression with curated data and GNN-derived features | 2,500 curated Tc (the public table used as our external benchmark) | Many regressors incl. CatBoost; random 80/20 | Curated compilation | None | n/s | CatBoost R2 0.87-0.91 | Random split; our audit found that 80% of its records have compositions already present in our (public-source) repository |
| 7 | Court & Cole 2020, npj Comput. Mater. | Text-mined phase-transition database and family-specific models | 20,389 records from 3,668 articles | Per-family regressions | Database precision 82% (300-record audit) | Within-family predictions | n/s | Database usable for family-level predictions | Label quality measured within one source, not against other sources or measured structures |
| 8 | Horton et al. 2019, npj Comput. Mater. | High-throughput collinear magnetic ground states with DFT | Materials Project | DFT workflow enumerating orderings | DFT labels; reports that most magnetic entries are in FM configurations (93% in the survey) | n/a | n/a | Workflow recovers ground states where orderings are enumerated | Consequence of FM-initialised labels for ML training and evaluation not quantified |
| 9 | Kelly & Cole 2025, Sci. Data | Curie/Neel temperature dataset by ChemDataExtractor + Snowball | Text-mined Curie and Neel temperatures | Data resource | Text-mined | n/a | n/a | Dataset release (used as our text-mined source) | Mixed transition types in the Tc column, which our curation had to remove |
| 10 | Omee et al. 2024, npj Comput. Mater. | Benchmark structure-based models out of distribution | General materials properties | Graph networks under OOD splits | n/a | Central (OOD splits) | n/a | (scope: OOD benchmark) | Not specific to magnetic labels or to label provenance |
| 11 | Varivoda et al. 2023, Appl. Phys. Rev. | Benchmark UQ for materials property prediction | General properties | Several UQ methods | n/a | n/a | Central | (scope: UQ benchmark) | Subgroup (class, range, source) calibration for magnetic targets not studied |
| 12 | Witman & Schindler 2025, Digital Discovery (MatFold) | Standardised grouped cross-validation protocols | General | Chemistry/structure-grouped CV | n/a | Central | n/a | (scope: standardised splits) | Provides the protocol idea; not applied to magnetic labels, descriptor increments or external audits |

Related method references used in the paper but not tabulated: Meredig et al. 2018 (extrapolation), Li et al. 2024 MD-HIT
(redundancy control), Tran et al. 2020 (UQ comparison), Hu et al. 2022 (conformal prediction for interatomic potentials),
Vovk 2013 (conditional conformal), Saerens et al. 2002 (prior shift).

## What is established in general, what was known for magnetism, what is new here

**Established general machine-learning phenomena (not claimed as new):** random splits overstate extrapolation; marginal
conformal coverage does not imply subgroup coverage; balanced class weights distort probabilities; leakage and redundancy
inflate scores; feature attribution is not incremental value.

**Previously documented for magnetic data:** high-throughput DFT magnetic configurations are mostly ferromagnetic
(Horton 2019); text-mined transition databases have imperfect precision (Court & Cole 2020); composition-only models reach
56-69 K Tc errors and 78-91% ordering accuracies on random splits (rows 1-6); AFM is the weakest class (rows 4-5).

**New quantitative evidence in this paper:**
1. The scale of the disagreement between computed (Materials Project) and experimental ordering labels for the same formulas
   (28%, kappa 0.00, 949 formulas), its persistence after phase matching by space group (25%, kappa 0.01, 330 formulas;
   bulk stoichiometric 314, kappa 0.02), and the direction set by measured magnetic structures (experimental 92% vs MP 22%
   agreement with MAGNDATA), with a partial label-definition component (rare-earth FM vs FiM).
2. The limited incremental value of non-magnetic DFT descriptors on identical materials and repeated grouped splits, with
   refit-aware intervals, detectable-effect statements and a cell-size control that explains the one stable gain.
3. Calibration failures that follow the magnetic classes (AFM 57%, FiM 54% under marginal sets) and the highest Tc decile
   (65.5% for constant-width intervals), with the cost of the repair (set size 1.39 -> 1.61).
4. The decay of reliability with chemical distance on an external benchmark whose apparent independence was mostly overlap
   (80% of the records have compositions already in our repository; 465 blind records, 69 in unseen systems).

## Paragraph: distinctive scientific contribution

Prior magnetic-materials studies report accuracy on random or stratified splits of a single source, and the reliability of
labels has been examined within single sources. Applying established reliability tools to one dataset would not by itself be
a contribution. What becomes newly understandable when these analyses are taken together is that a reported accuracy for a
magnetic property is conditional on three things that are rarely stated: the labelling convention of the source (computed and
experimental ordering labels disagree at chance level even for the same crystal structure), the descriptor set (non-magnetic
DFT descriptors add no detectable information beyond composition for experimental targets, and their apparent value for the
computed moment is mostly cell size), and the chemical domain (reliability and calibration degrade with chemical distance and
in unseen systems). These conditions also interact: the classes on which the label conventions differ are those on which
calibration fails. The paper's contribution is this quantitative, magnetic-specific account, not the methods themselves.

**Caveat:** the literature search was not exhaustive (Supplementary Table 9 lists the prior results that were read). The
manuscript therefore scopes its gap statement to "the magnetic studies that we examined".
