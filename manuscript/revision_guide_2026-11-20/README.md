# Revision following `paper/Revision Guide for the Paper.docx` (2026-11-20)

The guide asks for five deliverables. Where each one is:

| Deliverable | File |
|---|---|
| A. Revised manuscript | `../springer_nature/manuscript.tex` -> `manuscript.pdf` (reading copy, 31 pp) and `manuscript_review.pdf` (double-spaced, line numbers, 46 pp); `../springer_nature/supplementary.tex` -> `supplementary.pdf` (22 pp). Submission copy: `../main/submission/` |
| B. Revised figure package | `figure_plan.md`; figures `../springer_nature/fig1.pdf` ... `fig5.pdf`, `sfig1.pdf`, `sfig2.pdf` (script `make_figures_sn.py`) |
| C. Novelty assessment | `novelty_assessment.md` |
| D. Scientific-validation note | `scientific_validation_note.md` (includes the new phase-matched label check, A23) |
| E. Revision response | `revision_response.md` |

New analysis: A23, `final/revision/scripts/a23_label_comparability.py` (specification and claim rule in
`final/revision/PLAN.md`, written before the run); results shipped in `paper/results/revision/a23_label_comparability/`.

Target journal: Nature Communications (title <= 15 words, abstract <= 200 words, main text <= 5,000 words, <= 10 display items,
<= 70 references, no Extended Data). The former Extended Data items are Supplementary Figures 1-2 and Supplementary Tables 18-24;
the tier-effect and external-benchmark tables became main Tables 2 and 3.

Still for the authors: names and affiliations, Declarations, the human spot check of the Curie title screen.
