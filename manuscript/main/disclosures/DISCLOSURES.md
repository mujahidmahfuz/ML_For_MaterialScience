# Disclosures and declarations

Manuscript: "Reliability beyond accuracy in machine learning of magnetic materials" (Nature Article format; text rewritten 2026-11-11)

Authors: Mujahidul Islam (corresponding) and Gayan P. Hettiarachchi, Digital Business and Innovation, Tokyo International University,
4-42-31 Higashi-Ikebukuro, Tokyo 170-0013, Japan.

Each statement below matches the Declarations section of `../manuscript.tex`. Items marked **TODO** need the authors.

---

## 1. Use of AI tools (generative AI disclosure)
**Statement for the manuscript.** The data pipeline, analyses and manuscript were developed with substantial assistance from an AI assistant
(Claude, Anthropic), which wrote code, ran analyses and drafted text under the authors' direction. The authors checked the analyses and take
full responsibility for the content.

**Details to give the journal if asked:**
- **Tasks done by the AI assistant:**
  - writing the data-collection, curation and analysis code;
  - running the analyses;
  - drafting the manuscript, Supplementary Information and response letter;
  - literature and licence searches;
  - reference verification against Crossref and publisher records;
  - two rounds of simulated peer review.
- **AI-made judgements that a person has not yet verified:**
  - The **title-based screen of 200 Curie-temperature labels** (the "about 11% likely wrong" estimate). It was classified by the AI assistant from paper titles, not full texts. A spot-check sheet for the authors is in `../../review/curie_spotcheck_32.csv` (**TODO:** complete it, then fill in the number checked and disagreements in Methods). An AI-assisted abstract-level re-check of the same 32 records (not independent of the first screen, not a human check) is in `../../review/curie_spotcheck_32_claude_check.csv`: 29 of 32 agree with the title-screen call, 1 disagrees, 2 unclear; reported in Methods and Supplementary Table 17; it does not replace the authors' check.
  - The adjudications in the external-benchmark audit (A1/A2/A5).
- **Not done by AI:** no AI-generated images; all figures are plots of computed results.
- **TODO:** adapt the wording to the target journal's policy (Springer Nature: disclose in Methods/Acknowledgements; AI is not listed as an author).

## 2. Competing interests
The authors declare no competing interests. (**TODO:** both authors confirm.)

## 3. Funding
**TODO:** state funding sources and grant numbers, or "This research received no external funding."

## 4. Author contributions (CRediT)
**TODO: both authors confirm.** Draft:
- M.I.: conceptualization, data curation, methodology, software, formal analysis, writing (original draft).
- G.P.H.: supervision, methodology, writing (review and editing).

## 5. Data availability
The reproducibility package contains the curated analysis dataset (versions 1.2-1.4), frozen splits, external-benchmark adjudications, title-screen labels and all result files. **TODO:** add the repository URL and DOI.

Redistribution follows the upstream terms (full evidence in `data_licences_evidence.md`; summary in Supplementary Table S10):

| Source | Terms | Plan |
|---|---|---|
| Materials Project, OQMD, JARVIS-DFT, Kelly & Cole 2025, NEMAD (Zenodo) | CC BY 4.0 | release derived values with attribution |
| AFLOW | scientific, non-commercial use only | **TODO decide:** identifiers + script, or non-commercial release |
| MAGNDATA | no public licence; conditional access | **TODO decide:** identifiers + script, or ask permission |
| Two experimental compilations (`magnetic_materials.csv`, `magnetic_anisotropy_materials.csv`) | origin undocumented | **TODO:** identify the origin; until then, identifiers only |
| External benchmark (malaei/Magnetic_data) | no licence | not redistributed; retrieval script with SHA-256 check. **TODO:** remove its names and values from the 3 result files that contain them |

## 6. Code availability
All analysis code, configurations with fixed seeds, table and figure builders and tests are in the reproducibility package, released under the MIT licence. **TODO:** repository URL; add the LICENSE file and a CITATION.cff when the repository is created.

Reproducibility caveat: XGBoost results reproduce exactly only at the same thread count (16).

## 7. Ethics, consent, human or animal subjects
Not applicable: the study uses published materials data only.

## 8. Prior dissemination and preprints
**TODO:** state any preprint (e.g. arXiv) or conference presentation, or "none".

## 9. Analyses dropped or changed (transparency)
Disclosed in the manuscript (Methods, Limitations) and in `paper/results/revision/PLAN.md`:
- Dropped for run time before their results were seen (all six are listed in Methods, "Planning and deviations"):
  - the magnetic-physics test for ordering and the moment;
  - the structure-matched Curie comparison;
  - the matched leave-chemical-system-out comparison;
  - seed averaging for ordering XGBoost;
  - the rerun of the moment intervals with per-row output;
  - the refit for the ordering decomposition.
- The categories of the title-based screen were extended during classification (stated in Methods).
- Rules and plans written after earlier results were known:
  - the v1.3 curation rules;
  - the external audit plan;
  - Amendment 2.
- Corrections to earlier analyses are listed in Methods, "Errors found and corrected during the study".
