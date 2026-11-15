# Upstream data licences: evidence for the data-availability statement

Compiled 2026-11-10 from primary sources (provider licence pages, repository records via their APIs, data papers via Europe PMC full text). Web pages were fetched with `curl -A "license-check-script/1.0"`. This file reports what the terms say. It is **not legal advice**. Items marked **needs the authors' decision** are ambiguous or depend on facts not recorded in the project.

## Summary table

| # | Source (as used in this project) | Licence / terms | URL where stated | Redistribution of derived values allowed? | Attribution required | Other conditions |
|---|---|---|---|---|---|---|
| 1 | Materials Project (mp_api, ~100k entries + summary properties) | Creative Commons Attribution 4.0 (CC BY 4.0), via MP Terms of Use | https://materialsproject.org/about/terms (current page; 403 to scripts). Text read from https://legacy.materialsproject.org/terms (Wayback snapshot 2026-10-05). AWS Open Data registry names the same terms page as the licence | **yes** | yes: "proper attribution is given to the Materials Project" (cite Jain et al. 2013, APL Mater. 1, 011002, plus the MP API paper if used) | No NC, no SA. Terms also say "You agree to not scrape the website directly" (we used the API, which the terms allow) |
| 2 | OQMD (via jarvis-tools Figshare cache `oqmd_3d_no_cfid`) | CC BY 4.0 (OQMD). The Figshare mirror (10.6084/m9.figshare.14206169, K. Choudhary) is also CC BY 4.0 | https://oqmd.org/download/ (footer on every oqmd.org page); https://doi.org/10.6084/m9.figshare.14206169 | **yes** | yes: Saal et al. JOM 65, 1501 (2013); Kirklin et al. npj Comput. Mater. 1, 15010 (2015); cite the JARVIS Figshare record too | none beyond CC BY |
| 3 | JARVIS-DFT `dft_3d` (jarvis-tools, Figshare) | CC BY 4.0 (Figshare record 10.6084/m9.figshare.6815699). jarvis-tools *software* is a NIST public-domain-style notice, which does not cover the data | https://doi.org/10.6084/m9.figshare.6815699 (licence field); https://github.com/usnistgov/jarvis/blob/master/LICENSE.rst (software) | **yes** | yes: Choudhary et al. npj Comput. Mater. 6, 173 (2020) and the Figshare record | none beyond CC BY |
| 4 | AFLOW (AFLUX API; AGL/AEL properties) | AFLOW repository licence: free for scientific, academic and non-commercial purposes only, "Any other use is prohibited" | https://aflowlib.org/API/aflux/ (LICENSE line in the AFLUX help output) | **unclear**: non-commercial use is allowed. Redistribution is not addressed explicitly. **Needs the authors' decision** | not stated in the licence line. AFLUX output gives references: Curtarolo et al. Comput. Mater. Sci. 58, 218 (2012); Rose et al. Comput. Mater. Sci. 137, 362 (2017) (AFLUX); Toher et al. PRB 90, 174107 (2014) (AGL); Toher et al. PRM 1, 015401 (2017) (AEL) | **Non-commercial only.** Not compatible with releasing these values under CC BY |
| 5 | NEMAD (Itani, Zhang, Zang, Nat. Commun. 16, 9415, 2025): GitHub `sumanitani/NEMAD-MagneticML` + Zenodo 10.5281/zenodo.17042814; nemad.org | Zenodo record (snapshot of the GitHub repo incl. `Dataset/*.csv`): **CC BY 4.0**. GitHub repo: **no LICENSE file** (API 404). nemad.org: **no licence statement could be read** (JavaScript-only page). Article: CC BY-NC-ND 4.0 (covers the article text, not the data) | https://zenodo.org/records/17042814 (metadata `license: cc-by-4.0`); https://api.github.com/repos/sumanitani/NEMAD-MagneticML/license (404) | **yes** for files taken from the Zenodo v1.0 record. **Unclear** for anything taken from nemad.org or the unlicensed GitHub head. **Needs the authors' decision** (route recorded for `nemad_magnetic.csv` is not known) | yes: cite Itani et al. 2025 and the Zenodo record | none on Zenodo beyond CC BY |
| 6 | ChemDataExtractor Curie/Néel database: **the data actually collected are Kelly & Cole 2025, not Court & Cole 2018** | Kelly & Cole 2025 (Figshare 10.6084/m9.figshare.29559686.v2): **CC BY 4.0**. (Court & Cole 2018, Figshare 10.6084/m9.figshare.5702740: CC0, not used) | https://doi.org/10.6084/m9.figshare.29559686.v2; data-availability statement of Kelly & Cole, Sci. Data 12, 2000 (2025), doi:10.1038/s41597-025-06244-6 | **yes** | yes: Kelly & Cole 2025 + Figshare record. **The manuscript citation must be corrected** from Court & Cole 2018 | none beyond CC BY |
| 7 | MAGNDATA (Bilbao Crystallographic Server; web-scraped) | **No public licence found.** Bulk download needs an approved academic account and agreement to "our conditions regarding the usage of the database", which are not public | https://cryst.ehu.es/magndata/magndata_download.html | **unclear / not granted publicly**. The data were scraped, not downloaded under the usage conditions. **Needs the authors' decision** (ask administrador.bcs@ehu.eus) | yes: Gallego et al. J. Appl. Cryst. 49, 1750 (2016) and 49, 1941 (2016), as the BCS "How to cite" page asks | download restricted to educational/academic institutions |
| 8 | malaei/Magnetic_data, FM folder (2,500 Curie temperatures; external benchmark only) | **No licence.** `GET /repos/malaei/Magnetic_data/license` returns 404 "Not Found" and the repo metadata has `license: null` (checked 2026-11-10) | https://api.github.com/repos/malaei/Magnetic_data/license; README https://github.com/malaei/Magnetic_data | **no permission is granted** (no licence). The current practice is fetch-only, and it should stay that way | yes: README asks for a citation of Abedi Orang, Alaei, Oganov, arXiv:2509.17464 | none stated |
| 9 | `magnetic_materials.csv` (33,668 rows; experimental compilation) | **Origin not established.** Most likely an export of the NEMAD / GPTArticleExtractor pipeline (see section 9), but no published file with this schema was found | none found | **unclear. Needs the authors' decision** | if confirmed as NEMAD: Itani et al. 2025; Zhang et al. JMMM 597, 172001 (2024) | unknown |
| 10 | `magnetic_anisotropy_materials.csv` (33,916 rows; experimental anisotropy compilation) | **Origin not established.** Same likely lineage as #9 | none found | **unclear. Needs the authors' decision** | as #9 if confirmed | unknown |

**Sources that block, or may block, redistribution:**
- **AFLOW** is non-commercial only.
- **MAGNDATA** has no public licence, its access is conditional, and the data were scraped.
- **malaei/Magnetic_data** has no licence.
- **#9 and #10** have unknown origin.
- **NEMAD** data obtained other than from the Zenodo record may be unlicensed.

**Free to redistribute with attribution (CC BY 4.0):** Materials Project, OQMD, JARVIS-DFT, Kelly & Cole 2025, and the NEMAD Zenodo files.

---

## 1. Materials Project

- Evidence (MP Terms of Use, read from the Wayback copy of https://legacy.materialsproject.org/terms dated 2026-10-05. The live next-gen page returns HTTP 403 to scripted requests, and the legacy host returned 503):
  > "By downloading Content from Materials Project, User agrees to accept the Creative Commons Attribution 4.0 License implying that the Content may be copied, distributed, transmitted, and adapted, without obtaining specific permission from the Materials Project, provided proper attribution is given to the Materials Project."
  > "You agree to not scrape the website directly. You may collect large fractions of the database for analysis via the Materials Project API and to present processed results with proper attribution."
- The AWS Open Data registry entry (`awslabs/open-data-registry/datasets/materials-project.yaml`) gives `License: "[Materials Project Terms of Use](https://materialsproject.org/about/terms)"`.
- The `materialsproject/api` GitHub LICENSE covers the *client code* (GitHub reports NOASSERTION), not the data.
- Caveat: the current `materialsproject.org/about/terms` text could not be read directly. **Needs the authors' decision:** open that page in a browser and confirm it still says CC BY 4.0 before submission.
- **Deposit plan: ship derived values** (material IDs, formulas, ordering, magnetic moments, p3_* summary properties), with the MP citation and a CC BY 4.0 notice that lists our changes.

## 2. OQMD

- Evidence (footer on https://oqmd.org/download/ and other oqmd.org pages):
  > "The data in OQMD is licensed under CC-BY 4.0 If you are using any results from this website, please reference this work as shown here"
- The publications page asks for Saal et al. 2013 (JOM 65, 1501) and Kirklin et al. 2015 (npj Comput. Mater. 1, 15010).
- The copy we used came through jarvis-tools `oqmd_3d_no_cfid` → Figshare 10.6084/m9.figshare.14206169 ("oqmd_without_cfid", K. Choudhary, 2021). The Figshare API licence field is `CC BY 4.0`.
- **Deposit plan: ship derived values**, citing both OQMD papers and the Figshare record.

## 3. JARVIS-DFT

- Evidence (Figshare API, article 6815699, "JARVIS-DFT 3D dataset (jdft_3d.json)", v11, author Kamal Choudhary): `"license": {"name": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/"}`.
- jarvis-tools 2026.4.2 resolves `dft_3d` to this record (`figshare.py`: "# https://doi.org/10.6084/m9.figshare.6815699").
- The jarvis-tools LICENSE.rst is a software notice: "works of NIST employees are not subject to copyright protection in the United States … Permission … to use, copy, modify, create derivative works, and distribute this software …". It covers the software, not the data.
- **Deposit plan: ship derived values**, citing Choudhary et al. 2020 and the Figshare record.

## 4. AFLOW (AFLUX; AGL/AEL)

- Evidence (text returned by https://aflowlib.org/API/aflux/):
  > "LICENSE. The data included within the aflow.org repository is free for scientific, academic and non-commercial purposes. Any other use is prohibited."
- AFLUX also gives its references: "Aflux Reference: https://doi.org/10.1016/j.commatsci.2017.04.036", "Aflow REST API: https://doi.org/10.1016/j.commatsci.2014.05.014".
- The terms do not say whether redistribution is allowed. They do restrict use to non-commercial purposes, so values redistributed under CC BY (which allows commercial use) would go beyond the AFLOW terms.
- In this project AFLOW supplies the Phase 3 thermal (AGL) and some elastic (AEL) `p3_*` columns, which are used in the Tier 3 predictors.
- **Deposit plan: ship identifiers + fetch script only** (AFLOW `auid`/`aurl` and the AFLUX query), or ship the AFLOW columns separately under a non-commercial notice. **Needs the authors' decision.** It also affects which licence the authors can put on the deposited Tier 3 feature table.

## 5. NEMAD

- Zenodo (API record 17042814): title "sumanitani/NEMAD-MagneticML: First stable release of NEMAD-MagneticML", creator Suman Itani, published 2025-09-03, `license: {"id": "cc-by-4.0"}`, access open. The record's single file, `sumanitani/NEMAD-MagneticML-v1.0.zip`, is a GitHub release snapshot. It includes `Dataset/FM_with_curie.csv`, `AFM_with_Neel.csv` and `Classification_FM_AFM_NM.csv`.
- GitHub: `GET /repos/sumanitani/NEMAD-MagneticML/license` returns "Not Found", and the repo metadata has `license: null`. The README contains no licence or terms text.
- Paper (Nat. Commun. 16, 9415, 2025; Europe PMC PMC12552508), Data availability:
  > "The full Northeast Materials Database (NEMAD), including all curated magnetic compounds and their associated properties, is publicly accessible at https://www.nemad.org."
  > Code availability: "All source code used for the machine learning analysis, together with the processed datasets employed to train and evaluate the models, is available at https://github.com/sumanitani/NEMAD-MagneticML and has been archived on Zenodo (10.5281/zenodo.17042814)."
  - Article licence: "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License". This covers the article, not the database.
- nemad.org returns only a JavaScript shell ("NEMAD doesn't work properly without JavaScript enabled"). No licence or terms text was readable.
- Project files:
  - `new_datasets/github_datasets_magnetic.csv` (35,037 rows) came from the GitHub `Dataset/` CSVs. The same files are in the CC BY 4.0 Zenodo snapshot.
  - `new_datasets/nemad_magnetic.csv` (58,507 rows): `scripts/collect_nemad.py` tries, in order, the nemad.org API, Zenodo, and the nemad.org download page. The route that actually succeeded was not recorded, and `raw_data/_nemad_tmp/` is empty.
- **Deposit plan:**
  - Values that trace to the Zenodo v1.0 files: **ship derived values** under CC BY 4.0, citing Itani et al. 2025 and the Zenodo record.
  - Values from nemad.org: **ship identifiers (composition + DOI) + fetch script only**, unless the authors confirm terms from nemad.org or from the NEMAD authors. **Needs the authors' decision.**

## 6. ChemDataExtractor Curie/Néel database

- **Discrepancy:** the task names Court & Cole, Sci. Data 5, 180111 (2018). The project actually downloaded Kelly & Cole 2025.
  - `scripts/collect_chemdata_curie_neel.py` points to `https://doi.org/10.6084/m9.figshare.29559686.v2` and GitHub `C-R-Kelly/Curie-Neel-temperature-dataset`.
  - `raw_data/_chemdata_tmp/` holds `curie_neel_database_processed.csv` and `curie_neel_database_data_processed.json`, which are the files of that Figshare record.
- Figshare API (29559686): title "A Dataset of Curie and Neel Temperatures auto-generated with ChemDataExtractor and the Snowball Algorithm", authors Charles Kelly, Jacqueline Cole, licence `CC BY 4.0`.
- Paper (Kelly & Cole, Sci. Data 12, 2000 (2025), doi:10.1038/s41597-025-06244-6; PMC12738733), Data availability:
  > "The dataset for this study is available on Figshare, released under the CC-BY-4.0 license and can be found at 10.6084/m9.figshare.29559686.v2."
- GitHub LICENSE (C-R-Kelly): "The Curie-Néel temperature database is released under the CC by 4.0 license … Copyright (c) 2025 Charles R. Kelly".
- For reference, the 2018 Court & Cole data (Figshare 10.6084/m9.figshare.5702740, collection c.3954418) is licensed `CC0`.
- **Deposit plan: ship derived values**, citing Kelly & Cole 2025 + Figshare. **Correct the manuscript reference** (needs the authors' decision on whether Court & Cole 2018 is also cited as the method's origin).

## 7. MAGNDATA (Bilbao Crystallographic Server)

- Evidence (https://cryst.ehu.es/magndata/magndata_download.html):
  > "In order to download the MAGNDATA database, you'll first need to create a user account … (at the moment, only educational/academic institutions are accepted) … By agreeing to our conditions regarding the usage of the database, you'll be directed to the download page."
- The conditions themselves are shown only after login. No licence, terms-of-use or copyright page was found on cryst.ehu.es, the MAGNDATA front page, or the BCS wiki "About" page, which says the server offers its programs "free of charge".
- Citation requested (BCS wiki, "How to cite the Bilbao Crystallographic Server" → MAGNDATA): Gallego et al., J. Appl. Cryst. 49, 1750–1776 (2016) and 49, 1941–1956 (2016).
- Project fact: `scripts/collect_magndata.py` scraped the `index.php?index=X.Y` entry pages (2,208 rows). It did not use the registered bulk download.
- **Deposit plan: exclude MAGNDATA values. Ship identifiers only** (MAGNDATA entry labels such as "0.1", with the original-paper DOIs) plus the citation. **Needs the authors' decision.** They may want to contact administrador.bcs@ehu.eus, and to decide whether the scraped values can be used at all under the server's conditions.

## 8. malaei/Magnetic_data (FM folder)

- Evidence:
  - `curl https://api.github.com/repos/malaei/Magnetic_data/license` returns `{"message": "Not Found"}`.
  - Repo metadata: `license: null`, last push 2026-02-03.
  - The repository contents are `FM/`, `INS_SW_MC/` and `README.md`. There is no LICENSE file.
- README:
  > "**FM**: Curie temperature data for 2,500 ferromagnetic compounds, carefully curated by **Akram Abedi**. … If you use this dataset, please cite: Akram Abedi Orang, Mojtaba Alaei, Artem R. Oganov, *Predicting the Curie Temperature of Magnetic Materials with Machine Learning: Descriptor Engineering, Graph Neural Networks, and the Role of Curated Data*, arXiv:2509.17464"
- **Deposit plan: ship identifiers + fetch script only**, which is already the paper/ practice: `fetch_external_benchmark.py` with a SHA-256 check. The predictions and residuals the authors computed can be shipped keyed by row index/composition. Whether to include the published Tc column next to them **needs the authors' decision**. Cite arXiv:2509.17464.

## 9 and 10. `magnetic_materials.csv` and `magnetic_anisotropy_materials.csv` (origin not established)

- **Local record:**
  - `llm-wiki.md` lists both only as "Experimental literature; 25-col schema" among the user's "ORIGINAL DATASETS (do not modify)".
  - `cleaning.ipynb` calls them "Your originals". `Untitled.ipynb` reads `magnetic_materials.csv` without recording a source.
  - `scripts/` holds no download code for either file (`merge_all_datasets.py` and `reformat_existing.py` read them from the project root).
  - File timestamps are 2026-06-16, the same day as `raw_MP_magnetic_materials.csv`.
  - **No provenance is recorded anywhere in the project.**
- **Header and first rows read:**
  - Both files carry a `DOI` column, mostly `10.1016/j.jmmm.*` (J. Magn. Magn. Mater., Elsevier), and an `Experimental` boolean.
  - `magnetic_anisotropy_materials.csv` stores values as `{'Value':…,'Units':…,'Temperature':…}` dicts.
  - `magnetic_materials.csv` keeps raw strings (`Curie(Tc)` "42±1 K") next to parsed numbers (`Curie` 42) and a normalised composition (`New_Column_Concatenated` "Si11.0Gd3.0Pt23.0").
- **Evidence pointing to the NEMAD / GPTArticleExtractor pipeline (circumstantial):**
  - The NEMAD paper's Table 1 (arXiv 2409.15675) lists these fields: Material, Curie, Néel, Curie Weiss, crystal structure, lattice structure, lattice parameters, Space Group, Coercivity, Magnetization, Magnetic Moment, Remanence, Susceptibility, DOI, Experimental (Boolean). That is the same field set as `magnetic_materials.csv`.
  - GPTArticleExtractor (Zhang et al., JMMM 597, 172001, 2024; arXiv:2401.05875, CC BY 4.0 preprint) was applied to "22,120 articles in the Journal of Magnetism and Magnetic Materials", which matches the JMMM-dominated DOIs. It says: "A database covering various magnetic materials is available on our website (https://MagneticMaterials.org)". That domain now serves the NEMAD web app.
  - The project's own `collect_nemad.py` uses exactly the 25-column schema of `magnetic_anisotropy_materials.csv` as its NEMAD column list.
- **Searches that found nothing:** web searches for `"New_Column_Concatenated" "Curie_Weiss"` and for `"Remanence_Magnetization" "Saturation_Magnetization" "Anisotropy Constant K1" "Magnet_type"`. No Kaggle, Hugging Face, Zenodo or GitHub dataset with these columns was found. Unauthenticated GitHub code search is not available (`gh` is not installed), so GitHub code was not searched exhaustively.
- **Conclusion:** the origin **cannot be established** from primary sources. The NEMAD/GPTArticleExtractor lineage is likely but not proven. If the files came from MagneticMaterials.org/nemad.org, no licence for that site could be read (section 5).
- **Deposit plan: exclude the values. Ship identifiers only** (source DOI + material name/composition per row), plus a note that the values can be recovered from the cited papers or from NEMAD. **Needs the authors' decision**:
  1. ask whoever supplied the files where they came from (the NEMAD authors at UNH if the guess is right);
  2. then apply the licence of the confirmed source.
- Note that #9/#10 supply many experimental Curie, Ms and K1 target rows. Excluding them means the deposited target files cannot be complete. The data-availability statement should say so.

## Implications for the deposit licence (reporting only)

- The CC BY 4.0 sources (MP, OQMD, JARVIS, Kelly & Cole, NEMAD-Zenodo) can be combined in a deposit under CC BY 4.0. The deposit must keep per-source attribution and indicate changes.
- AFLOW's non-commercial condition does not fit a CC BY deposit. MAGNDATA, malaei and #9/#10 have no usable public grant.
- One option is a split deposit:
  - (a) CC BY 4.0 table of values from sources 1, 2, 3, 6 and 5-Zenodo;
  - (b) identifier lists + fetch scripts for 4, 7, 8, 9, 10 (and nemad.org-derived rows).
- The split and the licence to declare on (a) **need the authors' decision**.
- `paper/` is rebuilt by `final/scripts/build_paper_package.py`. This file sits in `paper/manuscript/revision/`, which that script does not manage. Add it to the build list if it should survive in the package.
