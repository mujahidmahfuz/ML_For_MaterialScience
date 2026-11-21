# Manuscript

**Label provenance, physical descriptors and chemical novelty constrain machine-learning predictions of magnetic materials**

Prepared for *Nature Communications* in the Springer Nature LaTeX template (`sn-jnl.cls`, version 3.1, December 2024, option `sn-nature`).

| File | What it is |
|---|---|
| [`manuscript.pdf`](manuscript.pdf) | Reading copy, 31 pages; each figure and table follows its first mention |
| [`supplementary.pdf`](supplementary.pdf) | Supplementary Information: Supplementary Figure 1, Supplementary Tables 1–29 and reproducibility notes, 24 pages |
| [`manuscript_review.pdf`](manuscript_review.pdf) | Peer-review copy (double-spaced, line numbers), 46 pages |
| `manuscript.tex`, `supplementary.tex` | Sources: one file each, every table inline and the reference list pasted in, as the template requires |
| `references.bib` | Bibliography; every entry checked against Crossref or the publisher's record |
| `fig1.pdf` … `fig6.pdf`, `sfig1.pdf` | Figures, next to the sources (the template forbids image subfolders); PNG previews in `png/` |
| `make_figures.py` | Draws every figure from the saved results in `../results/` (no model is fitted) |
| `inline_references.py` | Runs BibTeX and pastes the reference list into the `.tex` files |
| `build.py` | Compiles the three PDFs with tectonic and reports every layout warning |
| `sn-jnl.cls`, `sn-nature.bst` | Template class and Nature Portfolio reference style, unchanged |
| [`main/`](main) and `main_overleaf.zip` | Self-contained copy for Overleaf (upload the ZIP; steps in [`main/README_OVERLEAF.md`](main/README_OVERLEAF.md)) |

## Build

```bash
python make_figures.py        # only after a result file changes
python inline_references.py   # only after a citation or references.bib changes
python build.py               # manuscript.pdf, supplementary.pdf, manuscript_review.pdf
```

`build.py` finds tectonic through the `TECTONIC` environment variable or on `PATH`.

## Structure

| Section | Content |
|---|---|
| Results 1 | Computed and experimental labels describe magnetic order differently (Fig. 1) |
| Results 2 | Structural and electronic DFT descriptors add little information beyond composition (Fig. 2, Table 2) |
| Results 3 | Marginal calibration conceals material-dependent failures (Fig. 3) |
| Results 4 | Reliability decays with chemical novelty (Fig. 4, Table 3) |
| Results 5 | Selective prediction supports first-stage screening (Fig. 5) |
| Discussion | Interpretation, limitations and future work; summary schematic (Fig. 6) |
| Methods | Data, descriptors, curation, splits and models, statistics, uncertainty, external audit |

## Journal limits

| Rule | Limit | This manuscript |
|---|---|---|
| Title | ≤ 15 words | 13 |
| Abstract | ≤ 200 words, no references | 197 |
| Main text | about 5,000 words | about 5,100 |
| Display items | ≤ 10 | 9 (Tables 1–3, Figs 1–6) |
| References | ≤ 70 | 61 |

Author names, affiliations and the Declarations (funding, competing interests, data and code availability, author contributions)
are added at submission; their places are marked by comments after `\title` and after `\backmatter`.
