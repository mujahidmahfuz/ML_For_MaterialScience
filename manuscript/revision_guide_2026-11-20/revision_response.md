# E. Revision response (point by point)

Guide: `paper/Revision Guide for the Paper.docx` (2026-11-20). Revised files: `paper/manuscript/springer_nature/manuscript.tex`
(+ PDF, review PDF) and `supplementary.tex` (+ PDF); figures from `make_figures_sn.py`. Target journal changed to
**Nature Communications** as the guide recommends (format rules applied: title 13 words <= 15; abstract 185 words <= 200 with no
references; main text 4,999 words <= 5,000; 8 display items <= 10; 59 references <= 70; Discussion without subheadings; no
Extended Data). Numbers were not changed except where a new analysis (A23) adds them.

| Guide item | What was done | Where |
|---|---|---|
| 1.1 Move beyond "accuracy is insufficient" | Thesis rewritten: reliability depends on (i) label consistency/provenance, (ii) genuinely incremental descriptor information, (iii) chemical domain; stated as a synthesis, not one mechanism | Abstract, Introduction last paragraph, Discussion first and last paragraphs |
| 1.2 Four connected findings | Results reorganised into A provenance, B descriptors, C uncertainty, D novelty, plus screening; Discussion links them (calibration fails on exactly the classes where label conventions differ) | Results 1-5; Discussion paragraph 1 |
| 1.3 Define novelty precisely | Discussion paragraph separates general ML phenomena, previously documented magnetic issues, and new quantitative evidence | Discussion paragraph 5; `novelty_assessment.md` |
| 2.1 Physical difficulty of magnetism | New first paragraph: competing FM/AFM/FiM/NM states, exchange set by electronic structure and local geometry, structural phase, 0 K DFT vs finite-temperature samples, doping/disorder/films | Introduction paragraph 1 |
| 2.2 Opportunity and three conflated questions | Paragraph 2 states the three questions and why answering the first does not answer the others | Introduction paragraph 2 |
| 2.3 Specific gap | Gap scoped to "the magnetic studies that we examined"; label reliability so far studied within single sources | Introduction paragraph 3 |
| 2.4 End with contribution; no errors in Introduction | Last paragraph states question, framework, four dimensions, central insight; the sentence about our own earlier errors was removed from the Introduction (errors stay in Methods) | Introduction paragraph 4 |
| 3.1 Provenance section | New first Results section with dataset, source composition, label disagreement, phase-matched check, MAGNDATA, transfer, implication for pooled scores; curation details kept short | Results "Computed and experimental labels describe magnetic order differently"; Fig. 1 |
| 3.2 Descriptors | Matched comparisons, identical populations/splits, three targets, site-count control (now also for m_cell), power statement, "no detectable gain" | Results section 2; Fig. 2; Table 2 |
| 3.3 Calibration | Subgroups (AFM, FiM, highest Tc, text-mined source, oxides), costs (widths, set sizes), exchangeability | Results section 3; Fig. 3 |
| 3.4 Chemical novelty | Leave-system-out and external benchmark combined; formula vs system vs paper novelty; overlap with repository; why the composition-based audit is more credible than the formula-string test; distance analysis | Results section 4; Fig. 4; Table 3 |
| 3.5 Screening | Abstention (distance vs width), interval decisions at 300 K, internal vs external, worked examples; claim limited to first-stage filtering | Results section 5; Fig. 5 |
| 3 General writing rules | Each section opens with the question, gives the central number, the meaning, the limit and a bridge to the next; finding-driven headings | All Results sections |
| 4.1 Physical vs predictive information | Supported explanations (redundancy, size proxy) separated from hypotheses (polymorph mismatch, missing exchange information, label noise); null scoped to tested descriptors/models | Discussion paragraph 2 |
| 4.2 Physical meaning of label disagreement | What is established vs what needs phase-matched (magnetic-structure) validation; consequence for model building | Discussion paragraph 3 |
| 4.3 Chemical novelty and interpolation | Role and limits of the distance measure; correlation is not mechanism; small n | Discussion paragraph 4 |
| 4.4 Screening implications | When to act, when to compute/measure, when to abstain; intervals do not guarantee reliability under shift | Discussion paragraph 6 |
| 4.5 Limitations and future work | All six listed limitations; closing paragraph states what is established and what is open; First/Second/Third future work | Discussion paragraphs 7-8 |
| 5.1 Label comparability check | **New analysis A23** (plan + claim rule before the run): phase-matched agreement 25%, kappa 0.01 (330 formulas); disagreement persists; rare-earth naming component; representative sample of 30 formulas | Results section 1; Methods "Phase-matched comparison of ordering labels"; Supplementary Table 17; `scientific_validation_note.md` |
| 5.2 External benchmark verification | Definitions (composition normalisation, DOI overlap, exclusions, records vs compositions vs clusters, unseen-system uncertainty) checked; text states that only the blind subset is independent | Results section 4; Methods; Table 3 |
| 5.3 Moment normalisation | Per-atom values verified against the corrected-pairing file; four quantities defined in Methods | Methods "Targets and curation" |
| 5.4 Descriptor availability | New Methods paragraph and Results paragraph | Methods "Descriptors and their availability"; Results section 2 |
| 5.5 UQ assumptions, reproducibility | Exchangeable unit = formula group; design effect; thread-count and single-realization results listed | Methods "Uncertainty quantification", "Splits, models and selection"; figure legends |
| 6 Figure redesign | Five figures following the proposed architecture: Fig. 1 provenance (new), Fig. 2 descriptors with size control, Fig. 3 UQ with widths/set sizes, Fig. 4 novelty (two old figures merged), Fig. 5 screening (new); one-sentence takeaways | `figure_plan.md` |
| 7 Novelty vs literature | 12-study comparison table and contribution paragraph | `novelty_assessment.md` |
| 8.1 Finding-driven writing | Headings are findings (e.g. "Marginal calibration conceals material-dependent failures"); fewer "We next asked" openings | Results |
| 8.2 Transitions | Each Results section ends with a bridge to the next question | Results |
| 8.3 Precision | "No detectable gain", "much weaker, with wide uncertainty", "transfers poorly", agreement is not correctness, attribution is not incremental value, nominal coverage is not a guarantee under shift | Throughout; figure legends |
| 8.4 Procedural detail | Curation details, model settings, tuning and planning history kept in Methods/SI; main text keeps what is needed to read the results | Methods; SI |
| 8.5 Terminology | Ordering classes, Tc, DFT moment per cell / per formula unit / per atom, physical descriptors (Tier 1-3), blind / unseen system / new paper used consistently | Throughout |
| 9.1 Title | New title chosen after the novelty assessment: "Label provenance, physical descriptors and chemical novelty constrain machine-learning predictions of magnetic materials" (13 words) | Title |
| 9.2 Abstract | Problem, gap, approach, three findings, implication; 185 words | Abstract |
| 9.3 Conclusion | Final Discussion paragraph says what the study changes (how a reported accuracy must be read) and what remains unresolved | Discussion last paragraph |
| 10 Journal positioning | Formatted for Nature Communications; npj Computational Materials remains the fallback if the contribution is judged methodological; no speculative physics added | Formatting; this note |
| 11 Sequence | Contribution -> novelty -> verification (A23) -> reorganisation -> figures -> Discussion -> writing -> title/abstract/conclusion -> claim-figure-table-reference audit (build: no overfull boxes, no undefined references; every page inspected) | Build logs; `springer_nature/png/` |

## Recommendations not adopted, or adopted partly

- **"Figure 1 ... distribution of target properties across sources":** shown as source composition and ordering class shares;
  continuous Tc / moment distributions by source were not added, to keep one message per figure (the frozen Phase 6
  EDA outputs in the package hold them).
- **"Prediction interval width ... as a function of chemical distance" (Fig. 4):** shown as numbers inside panel d instead of a
  separate panel, to avoid a dual axis and a crowded figure.
- **"Examine a representative sample ... using original source records":** done at the level of the harmonised source records
  (DOI, space group, material type, crystal structure) and MP entries; the original papers were not re-read.
- **Methods length:** about 4,400 words, above the "typically less than 3,000" of Nature Communications; kept because the guide
  asks to keep methodological information needed to interpret the results. It can be shortened (planning history and error log
  to the SI) if the editor asks.
- **Nature Materials:** not targeted, as the guide advises.
- **Author names, affiliations, Declarations and the human Curie spot check (0/32):** still open; they need the authors.
