# Manuscript draft notes (first draft 2026-11-09)

Files: `manuscript.tex` (main text, sn-jnl / sn-nature), `references.bib`. Tables and figures are pulled in from `../tables/*.tex` and
`../figures/*.pdf`, so they always match the package. `sn-article.tex` / `sn-bibliography.bib` are the untouched template examples.
`final/scripts/build_paper_package.py` does not touch this folder, so a package rebuild will not overwrite the draft.

Build: `pdflatex manuscript && bibtex manuscript && pdflatex manuscript && pdflatex manuscript` (no LaTeX on this PC yet, so the draft
has **not been compiled**. Install MiKTeX or upload the folder plus ../tables and ../figures to Overleaf).

## Open items for the authors (red \todo{} in the PDF)
1. Mujahidul Islam: affiliation (department, institution, city, country); confirm the corresponding e-mail.
2. Gayan P. Hettiarachchi: department and postal address at Tokyo International University; e-mail if needed.
3. Target journal (template is set to Nature Portfolio style; npj Computational Materials or Digital Discovery fit the content). Check word limits.
4. Funding, acknowledgements, competing interests, CRediT author contributions.
5. AI-use disclosure (the pipeline, analyses and draft were produced with an AI assistant). Use `/ars-disclosure` for the chosen venue.
6. Data/code availability: repository + DOI, a code licence, and **upstream data licences** (unverified; three result files contain the
   external malaei table's values).
7. Supplementary Information document (Tables S1-S3, Fig. S1, secondary targets, families, bias, claims register): not yet written.

## Citations
Checked 2026-11-10 (36 entries): see `CITATION_CHECK.md`. 5 bibliography errors and 3 citation contexts fixed; abediorang2026curie added.
The Introduction has no literature review yet beyond the core citations.

## Number checks done while drafting
- Every number in the text was taken from `../tables`, `../results/claims/` or `final/Research_Story_Compilation.docx`.
- Two small inconsistencies between sources: the per-atom XGBoost gain is +2.8% in Table 2 and +2.7% in claims_revisions_final.md / README;
  leave-chemical-system-out ordering is -0.028 [-0.041, -0.016] in Table 6 and -0.029 [-0.041, -0.017] in the claims register. The text uses
  the table values. Resolve at source (rounding?) and rebuild the package.
- Methods details checked in code: ECE 15 bins (phase8_uq.py), CQR = XGBoost quantile 5%/95%, normalized conformal = sigma model fitted
  on cross-fitted absolute residuals (run_phase8_regression_uq.py), grids and selection rule (analysis_config.yaml).
