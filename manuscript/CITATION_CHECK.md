# Citation check: manuscript.tex / references.bib (2026-11-10)

Method: every entry with a DOI was fetched from the Crossref API and compared field by field (authors, title, journal, volume,
issue/pages, year, DOI). Entries without a DOI were checked against the publisher or proceedings listing (JMLR, PMLR,
NeurIPS via mlanthology, Cambridge Core) or found through Crossref search. In-text use was read sentence by sentence.
Result: 36 cited keys = 36 bibliography entries; no missing or unused keys.

## Errors corrected
| Key | Problem | Fix |
|---|---|---|
| itani2025nemad | Wrong title; volume, article number and DOI missing | "The northeast materials database for magnetic materials", Nat. Commun. 16, 9415 (2025), doi:10.1038/s41467-025-64458-z |
| belot2023curie | Wrong author first name ("Valérie" Taufour) | Valentin Taufour; added issue 4 and doi:10.1063/5.0156377 |
| malaei_magnetic_data | No real authors; the maintainers ask users to cite a paper | Authors Akram Abedi Orang and Mojtaba Alaei (repo README); added the requested paper as `abediorang2026curie` (Comput. Mater. Sci. 269, 114663 (2026), doi:10.1016/j.commatsci.2026.114663; arXiv:2509.17464) |
| romano2019cqr | Pages missing | pp. 3543-3553 |
| coey2010magnetism | DOI missing | doi:10.1017/CBO9780511845000 |

## Citation contexts corrected in manuscript.tex
1. Introduction: `horton2019ordering` and `frey2020oxides` were cited as ML models; both are high-throughput DFT studies. They are now
   cited as "high-throughput DFT predictions of magnetic order", and the ML sentence cites nelson2019curie, belot2023curie and abediorang2026curie.
2. Introduction: `dunn2020matbench` was cited for "properties can diverge", which Matbench does not argue. The sentence now cites Matbench for
   standardized accuracy comparison and tran2020uq / kapoor2023leakage / li2023critical for "accuracy alone can mislead".
3. Results (external benchmark) and Methods: the benchmark now cites its source study (abediorang2026curie) as well as the repository.

## Verified with no change (31)
jain2013materials, saal2013oqmd, kirklin2015oqmd, choudhary2020jarvis, curtarolo2012aflow, court2018curie, gallego2016magndata,
ong2013pymatgen, ward2016magpie, chen2016xgboost, lundberg2020treeshap, lei2018distribution, papadopoulos2011normalized,
angelopoulos2023gentle, vovk2013conditional, saerens2002adjusting, meredig2018extrapolation, li2023critical, dunn2020matbench,
kapoor2023leakage, tran2020uq, nelson2019curie, horton2019ordering, frey2020oxides, gutfleisch2011magnetic (all via Crossref DOI);
pedregosa2011sklearn (JMLR 12, 2825-2830), guo2017calibration (PMLR 70, 1321-1330), ke2017lightgbm (NIPS 30, 3146-3154),
romano2019cqr (venue), vovk2005algorithmic (Springer 2005, 1st ed.; a 2nd edition appeared in 2022, doi:10.1007/978-3-031-06649-8), coey2010magnetism.

## Remaining caveats
- lundberg2017shap: venue and authors confirmed (NIPS 30); pages 4765-4774 are the commonly cited range but were not seen on an official page.
- vovk2005algorithmic: consider citing the 2022 second edition.
- malaei_magnetic_data: add the commit hash of the analysed file.
- Context worth adding to the Discussion: Abedi Orang et al. train Tc models on the same curated table that we use as our external benchmark.
  Our finding that 80% of its compositions are already in our sources is relevant to how that table is used for evaluation.
- Citations are numbered (sn-nature style); format errors can only be confirmed once the document is compiled.
