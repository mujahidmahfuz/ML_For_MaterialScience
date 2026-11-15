# Submission folder: Nature Article format

Self-contained: upload this whole folder to Overleaf (or compile locally) and it builds without the rest of the project.
Restructured to the Nature formatting guide on 2026-11-10 (see "Nature format check" below).

| Item | File |
|---|---|
| Main manuscript (with Methods, end notes and Extended Data): clean reading copy | `manuscript.tex` → `manuscript.pdf` |
| The same text double-spaced with line numbers, for the Nature submission system | `manuscript_submission.tex` → `manuscript_submission.pdf` |
| Supplementary Information (tables only; Nature allows no figures there) | `supplementary.tex` → `supplementary.pdf` |
| Page design shared by all three (fonts, headings, captions, table font, citations) | `nature-style.tex` |
| Bibliography (64 verified entries) | `references.bib` |
| Nature reference style | `sn-nature.bst` (`sn-jnl.cls` is no longer used) |
| Tables (LaTeX) | `tables/` |
| Figures (vector PDF for LaTeX, PNG for viewing) | `figures/` |
| Disclosures and declarations | `disclosures/DISCLOSURES.md` |
| Licence evidence per upstream data source | `disclosures/data_licences_evidence.md` |

## Which file is which display item
File names keep their package names; the manuscript numbers them as follows.

| In the manuscript | File |
|---|---|
| Table 1 | `tables/table1_dataset.tex` |
| Fig. 1-4 | `figures/fig1_...`, `fig2_...`, `fig3_...`, `fig4_...` |
| Extended Data Fig. 1 | `figures/figS1_blind_scatter.pdf` |
| Extended Data Table 1 | `tables/table2_physics_descriptors.tex` |
| Extended Data Table 2 | `tables/table3_magnetic_physics.tex` |
| Extended Data Table 3 | `tables/table4_regression_intervals.tex` |
| Extended Data Table 4 | `tables/table5_ordering_calibration.tex` |
| Extended Data Table 5 | `tables/table7_generalization_internal.tex` |
| Extended Data Table 6 | `tables/table6_external_benchmark.tex` |
| Extended Data Table 7 | `tables/table8_screening.tex` |
| Supplementary Tables 1-8, 11 | `tables/tableS1_...` to `tableS8_...`, `tableS11_...` |
| Supplementary Tables 9, 10, 12 | written inside `supplementary.tex` |

## Full rewrite (2026-11-11)
`manuscript.tex` was rewritten from the result files, not edited from the previous text. The previous version is kept in
`../review/nature_v1_2026-11-11/`. What changed in substance:
- Every number was re-read from `paper/results/` before it was written.
- The open items of the round-2 review (`../review/round2/re_review_report.md`) that the previous Nature version had not carried over are now in the text:
  - the detectable effect is given as a range (27-56 K) and the Curie gains that cannot be excluded as 5-32 K;
  - the composition distance is reported in both transfer directions, and the "label definition, not chemistry" conclusion is limited to Materials Project to experiment;
  - the normalized conformal method "came closest" (it is not best on computational-source labels, 86.6% against 90.4%);
  - the two abstention rules are not ranked;
  - the title screen gives the range 11-27% and logs the added categories;
  - single-split and single-realization numbers are marked;
  - all six dropped analyses are listed (Methods, "Planning and deviations"; Supplementary reproducibility notes);
  - the pre-registered wording rules for unseen systems and for label transfer are quoted and followed.
- New Supplementary Table 12 (4 x 4 label cross-tabulation; raw and prior-corrected transfer).
- Table notes: Holm-family composition (Extended Data Table 1), neutral column name "Second subgroup" (Extended Data Table 3).
- Fig. 3 legend now says its bars are percentile intervals (the text and Extended Data Table 6 give bias-corrected intervals).
- One reference added (CHGNet, Deng et al. 2023; checked against Crossref).
- The reference list now comes before Methods, as in the Nature section order; the Methods-only references are the last five.

## Nature format check (2026-11-11, against the formatting guide on nature.com)
| Requirement | Now |
|---|---|
| Title at most 75 characters, no punctuation or acronyms | 69 characters |
| Summary paragraph at most 200 words, referenced, few numbers, "Here we show" | 200 words, 9 references, no numbers |
| Main text (summary + body) | about 3,430 words (guide: 2,500 for 6 pages, 4,300 for 8 pages) |
| Main display items 4 to 6 | 5 (Figs 1-4, Table 1) |
| Subheadings at most 40 characters | longest 38 |
| Continuous prose, no bullet lists | no lists |
| References at most about 50 in the main text | 50 main, 5 Methods-only |
| Methods at most about 3,000 words | about 3,040 words |
| Figure legends under 300 words, title first, error bars defined | 43 to 116 words |
| Extended Data at most 10 items | 8 (1 figure, 7 tables) |
| Section order | main text, references, Methods (with Data and Code availability), end notes, Extended Data |
| Spelling | Oxford (British with -ize) |
| Double spacing and line numbers | `manuscript_submission.pdf` only (the reading copy has neither) |
| Figures 180 mm wide, Arial 5-7 pt, no notes inside figures, one legend position | built by `paper/scripts/make_figures.py` |
| Tables at full text width, one font, no overflow | built by `paper/scripts/make_tables.py` |

Checked on 2026-11-11: all three PDFs build without errors or overfull boxes and were inspected page by page
(reading copy 18 pages, submission copy 23 pages, supplementary 6 pages).

## Compile
With tectonic (installed in the Anaconda environment): `tectonic manuscript.tex`, `tectonic manuscript_submission.tex`, `tectonic supplementary.tex`.
On Overleaf (pdfLaTeX): compile the same three files; `nature-style.tex` picks the right fonts for pdfLaTeX or XeLaTeX.
Nature takes a single PDF at first submission (upload `manuscript_submission.pdf`); the LaTeX source is only requested after acceptance.
Edit text only in `manuscript.tex`; `manuscript_submission.tex` just switches on the submission layout.

## Keep tables and figures current
The tables and figures here are copies. They are generated in the reproducibility package (`paper/`) from `paper/results/`. After any rebuild (inside `paper/`: `python scripts/make_tables.py` and `python scripts/make_figures.py`), refresh them here with:

    python refresh_from_package.py

## Not in this folder (on purpose)
- **Review history** (simulated rounds 1 and 2, response to reviewers, the Curie spot-check sheet) is in `../review/`. It is not part of a journal submission. It refers to the old table numbers (Tables 1-8).
- **Research notes** (prior-results table, verified new references) are in `../revision/`.
- **The template's example files** (`sn-article.tex`, `user-manual.pdf`, ...) stay in `../`.

## Before submission
Open items are the red `\todo{}` markers in `manuscript.tex` and the **TODO** lines in `disclosures/DISCLOSURES.md`:
- funding and acknowledgements;
- author contributions (confirm the wording);
- repository DOI and URL;
- the authors' confirmation of their checks in "Use of large language models";
- the data-licence decisions;
- the Curie spot check.
