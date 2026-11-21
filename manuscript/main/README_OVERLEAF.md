# Overleaf test copy

Everything needed to compile the paper on Overleaf, and nothing else. It is a copy of the files in `../` (the working
sources, built locally with `../build.py`); edit there and copy again, or edit here and copy back.

## Upload

1. Overleaf → **New Project → Upload Project** → choose `main_overleaf.zip` (in the folder above this one).
2. **Menu → Settings:** Compiler **pdfLaTeX**, TeX Live version **2024 or later**, Main document **manuscript.tex**.
3. **Recompile.** Expected: 34 pages, no errors.

To compile the other documents, change *Main document* to `supplementary.tex` (24 pages) or `manuscript_review.tex`
(peer-review copy with double spacing and line numbers, 49 pages).

## Files

| File | What it is |
|---|---|
| `manuscript.tex` | Main paper (Springer Nature template `sn-jnl`, option `sn-nature`) |
| `supplementary.tex` | Supplementary Information |
| `manuscript_review.tex` | Same text as `manuscript.tex` with the class options `referee,lineno` |
| `fig1.pdf` … `fig6.pdf`, `sfig1.pdf` | Figures (the template expects them next to the `.tex` files) |
| `sn-jnl.cls`, `sn-nature.bst` | Template class and reference style |
| `references.bib` | Bibliography source. The reference lists are already pasted into the `.tex` files, so Overleaf needs no BibTeX run |
| `manuscript.pdf`, `supplementary.pdf`, `manuscript_review.pdf` | The PDFs built locally, for comparison |

Checked on 2026-11-21: this folder compiles on its own (manuscript 34 pages, Supplementary Information 24, review copy 49), with no
overfull boxes and no undefined references. The sources are plain ASCII and use the template's `pdflatex` option.

If a citation is added or changed, edit `references.bib` in `../` and run `python ../inline_references.py`, then copy the `.tex`
files here again (Overleaf would otherwise need the pasted list replaced by `\bibliography{references}`).
