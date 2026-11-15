# Domain Review Report -- Peer Reviewer 2 (Domain)

Contract: reviewer/reviewer_full/v1 (Phase 1 commitment: `domain_phase1.md`, same folder)
Manuscript: "Accuracy is not reliability: physics descriptors, calibration and chemical generalization in machine learning of magnetic materials" (first full draft, sn-jnl / sn-nature template)
Review date: 2026-11-10 · Round 1
Reviewer identity: computational magnetism researcher (DFT magnetic ground states, experimental Curie-temperature data, ML for magnetic ordering and T_C).
Files read: manuscript.tex, references.bib, tables 1-6 (.csv + notes), figs 1 and 3 (PNG), EDA/00_config/v1_3_curation_rules.yaml, tier3_predictors.txt.

No Scoring Plan Dissent: the Phase 1 triggers are applied as written.

## Dimension Scores

### D1: methodology_rigor
**Score: warn**
Evidence: the domain parts of the design are mostly sound. Curie rules C1-C5 are written down, remove rows only, and come with known false positives (Methods "Target definitions"; v1_3_curation_rules.yaml). The JARVIS constant-FM labels are quarantined (rule O1). Splits are grouped by formula and by chemical system, and tier comparisons use matched rows and paired bootstraps. None of the Phase 1 block triggers fires: Néel temperatures are screened rather than silently pooled, the DFT moment is kept separate from experimental magnetization, and no random split is used for a generalization claim. The warn triggers do fire, because some target-construction choices are incomplete or under-justified for a magnetism reader:
(a) The size of the residual non-Curie contamination is not reported. C5 catches Néel temperatures only for formulas that carry an AFM-only ordering label. A text-mined "T_C" for a formula with no ordering label passes, and so does a compensation temperature of a ferrimagnet.
(b) The four-class ordering target includes 31,673 NM records. Many contain no magnetism-capable element, which makes the NM class close to trivial. Its share of the headline macro-F1 0.73 is not separated out.
(c) The moment target is extensive (per cell) and, for collinear AFM ground states, is approximately zero, the same as NM. The per-formula-unit normalization that is standard in the field is not used. The paper says up front that per-cell scaling explains the Tier 3 gain, but it never justifies per-cell as the primary target.
(d) Within-formula T_C dispersion is not reported. Doped, thin-film and off-stoichiometric records sharing one reduced formula set a label-noise floor on the 76 K MAE.

### D2: domain_accuracy
**Score: warn**
Evidence:
(a) Terminology. Table 1, Table 2 and Fig. 1 (panels c, d) label the 0 K DFT total moment per cell as "Ms". Saturation magnetization is a measured, temperature-dependent bulk quantity in A/m or emu/g. The text itself says correctly that the quantity is the "DFT total moment per unit cell at 0 K" (Methods), so the labels contradict it. (Phase 1 warn trigger: imprecise terminology.)
(b) The "physics descriptor" conclusion is stated more generally than the descriptors support. Tier 3 (tier3_predictors.txt) contains energetics, band edges, symmetry labels, volume/density, elastic, dielectric and piezoelectric scalars. All DFT magnetic quantities were removed on purpose. There are no exchange parameters, local moments, magnetic-ion coordination, magnetic-ion bond lengths or angles (relevant to superexchange and Goodenough-Kanamori rules), and no magnetic-sublattice dimensionality. These are the quantities that magnetism theory links to T_C and to the type of order. The Limitations sentence ("apply to the descriptors we tested") is correct, but the title, the abstract ("Adding DFT descriptors ... gave no practical gain") and the Discussion heading "Why physics descriptors did not help" read as general claims.
(c) Prior work is cited (Nelson & Sanvito 2019; Belot 2023; Abedi Orang 2026; Court & Cole 2018; NEMAD; Horton 2019; Frey 2020) but not engaged with. No prior T_C or ordering metric is compared with the ones reported here. Several directly relevant papers are missing; see the missing-references list.
(d) The provenance-transfer result is not interpreted with the known Materials Project behaviour. Most MP calculations start from a ferromagnetic high-spin configuration, and only a subset went through the ordering-enumeration workflow of Horton et al. This biases MP labels toward FM and is a domain explanation for the 0.284 macro-F1 that the paper does not give.
None of these errors overturns a headline result, so the score is warn, not block.

### D3: argumentative_coherence
**Score: warn**
Evidence: the central thesis (accuracy, physics enrichment, calibration and generalization are distinct properties) follows from the results. The authors are careful about how they word null results: "no practical improvement (below 10 K), not equivalence", and "much weaker, with wide uncertainty" rather than "no skill". The warn trigger fires on two points. First, the RQ1 conclusion is generalized beyond the descriptor family tested (see D2b). The same overreach appears in the Conclusion ("DFT physics descriptors added little once comparisons were matched and controlled") and in the Discussion claim that a model with R² 0.78 "had a negative point estimate of R² in unseen chemical systems", which rests on n = 69 records from 26 papers. Second, small numerical inconsistencies. The abstract gives marginal-set coverage of AFM 57% and FiM 55% (10-split means). The Results text gives 57.7% and 52.7% (frozen split, Table 4) directly after a 10-split overall figure, without saying which split each number refers to. Neither inconsistency changes a conclusion.

### D4: cross_disciplinary_relevance
**Score: pass**
Evidence: conformal prediction, normalized scores, CQR, Mondrian sets, ECE and temperature scaling are each introduced in a sentence that a materials reader can follow. The six practical recommendations (Discussion) follow from the results and carry over to other property-prediction tasks. The audit of the external benchmark (string vs composition novelty, duplicated labels) is a useful lesson for readers outside magnetism. A minor point: "chemical system" and "provenance" deserve a one-line definition at first use in the main text. The Fig. 3 caption already defines "chemical system".

### D5: writing_and_structure
**Score: warn**
Evidence: the paper is well organized around RQ1-RQ3. Tables carry notes and figures are legible; in Fig. 1 the off-scale Ridge estimate is handled honestly. The warn trigger fires on three points. Unresolved \todo{} markers remain in the affiliations, the declarations, the Supplementary Information and the bib entry for the external data. Naming is inconsistent: "Ms" in the tables and figures, "moment" in the text. The main text is about 5,100 words of LaTeX source against a ~3,500-word target.

## Failure Condition Checks

### F1 (severity 90): any mandatory dimension scores 'block'
fired: false. D1, D2 and D3 all score warn; no mandatory dimension is block.

### F2 (severity 70): two or more mandatory dimensions score 'warn' or worse
fired: true. Three mandatory dimensions score warn: D1, D2 and D3. Action: editorial_decision = major_revision.

### F3 (severity 60): any high-priority dimension scores 'block'
fired: false. D4, the only high-priority dimension, scores pass.

### F0 (severity 10): every mandatory dimension scores 'pass'
fired: false.

Precedence: F2 (severity 70) is the highest condition that fired, so the decision is Major Revision.

## Review Body

### Summary assessment
The manuscript assembles a multi-source magnetic-materials dataset with provenance: ordering 79,125 records, T_C 29,740, DFT moment per cell 87,513. It asks three questions: do DFT descriptors help beyond composition, are conformal and probabilistic uncertainties calibrated, and do predictions generalize to unseen chemistry? Each question is tested with matched rows, ten repeated grouped splits and cluster bootstraps. The findings are that composition-only gradient boosting is already strong, that the tested DFT descriptors add nothing practical for ordering or T_C, and that the per-cell moment gain is explained by cell size. Marginal conformal coverage hides poor coverage of AFM and FiM and of the hardest materials. On an audited external T_C table, accuracy collapses in unseen chemical systems.

From a domain standpoint the most valuable parts are the honest target curation (above all the discovery that every JARVIS ordering label was a collector default) and the external-benchmark audit, which exposes heavy overlap with upstream compilations. Both are lessons the magnetic-ML community needs. The main weaknesses are domain framing, not statistics. The "physics descriptors" tested omit everything magnetism theory ties to T_C and ordering (exchange, local moments, magnetic-ion geometry), so the RQ1 conclusion is narrower than the title implies. The moment target is extensive and does not distinguish AFM from NM, and it is mislabelled "Ms". The NM class probably inflates the ordering headline. Engagement with prior T_C and ordering ML results is thin. These problems can be fixed and do not require new large-scale experiments, but together they change how the paper should be framed. Hence Major Revision.

Confidence: 4/5. I am less expert on the conformal-prediction details, which were flagged in advance as a possible blind spot.

### Strengths
**S1: Physically motivated, transparent curation of T_C.** Rules C1-C5 (Methods; Results "A curated multi-source dataset") target real contaminants of text-mined "Curie temperature" columns: superconducting T_c, ferroelectric Curie points and Néel temperatures. The C4 bound is tied to Co (~1388 K). The rules remove rows only, and their known false positives (Ti3+ ferromagnets such as YTiO3; multiferroics) are stated. Few T_C ML papers are this explicit.

**S2: Discovery and quarantine of the JARVIS default-FM labels.** All 15,493 JARVIS ordering labels were found to be a collector constant (rule O1). The authors also show that an earlier Tier 2 gain did not replicate once these labels were removed. This is a concrete, transferable warning for anyone who merges magnetic databases.

**S3: Separating the extensive moment from physics.** The site-count control (RQ1 "Magnetic moment") shows that the per-cell Tier 3 gain is recovered by a single cell-size scalar. The per-atom gain is reported only after the authors corrected a denominator taken from a different cell (25.4% of rows). This is a careful physical deconstruction of an apparent "physics-informed" gain.

**S4: Composition-level audit of an external T_C benchmark.** 80% of the external table's compositions were already in the training repository and 48% of its values duplicated training labels. Results are split by blind / seen system / unseen system with paper-cluster intervals (Table 5, Fig. 3). This changes how earlier "blind" T_C validations should be read.

**S5: Calibrated wording of null results.** Examples are "no practical improvement (below 10 K), not equivalence" and the pre-registered rule that "no skill" requires an upper R² limit of at most 0.2. Both are good practice and rarely seen in the field.

### Weaknesses

**W1: The RQ1 conclusion is drawn from a Tier 3 set that omits the magnetically relevant physics.**
*Problem.* Tier 3 (Results "A curated multi-source dataset"; tier3_predictors.txt) contains formation energy, hull distance, band gap and edges, Fermi level, symmetry labels, volume/density, elastic, dielectric and piezoelectric quantities. DFT magnetic outputs were excluded, and the Methods do not say so explicitly. Nothing describes the magnetic sublattice: magnetic-ion density, magnetic-ion to magnetic-ion distances, cation-anion-cation bond angles, coordination of the magnetic ion, or the dimensionality of the magnetic network. There are no exchange constants J_ij, no spin-polarization energy, and no local moments. Mean-field and RPA estimates of T_C scale with exchange and coordination (e.g. Liechtenstein et al. 1987). The FM/AFM competition in insulators is governed by superexchange geometry.
*Why it matters.* The title and abstract will be read as "physics does not help ML of magnetism", but what was shown is "generic non-magnetic DFT scalars from the lowest-energy polymorph do not help tree models". Long et al. (2021) report that structural descriptors improved T_C and ordering models beyond composition.
*Suggestion.* (i) Rename RQ1 and the Results heading, e.g. "generic DFT descriptors add little beyond composition". In the abstract, the Discussion and the Conclusion, state explicitly that magnetic and exchange descriptors were excluded and why (leakage for the moment target). (ii) Preferably, add a small "magnetic-structure" tier computed from the existing MP structures with pymatgen: magnetic-ion number density, nearest magnetic-ion distance, mean M-X-M angle, magnetic-ion coordination number. Even on the matched T_C and ordering populations, this would test the hypothesis a magnetician would actually pose. (iii) Note also the structure mismatch: experimental T_C may refer to a doped or thin-film sample, while the descriptors describe the most stable bulk polymorph. The authors mention this in passing (Discussion), but it should qualify the RQ1 claim directly.
*Severity:* Major.

**W2: The moment target is mislabelled and its physics is under-specified.**
*Problem.* Tables 1-2 and Fig. 1c,d call the target "Ms", yet Methods correctly define it as the MP DFT total moment per unit cell at 0 K. Saturation magnetization is an experimental, finite-temperature quantity. In addition: (a) the target is extensive, which is why cell size explains the Tier 3 gain; (b) for collinear AFM ground states the per-cell total is approximately zero, the same as NM, and 38% of MP rows are exactly zero (RQ2 text); (c) the MP values mix GGA and GGA+U functionals, and many entries were computed only from FM initialization, so the "ground-state moment" is often the FM moment.
*Why it matters.* Readers will compare these MAEs with experimental Ms, which is not valid. The headline "Tier 3 helps the moment" is partly an artefact of target extensivity, as the authors show, and that makes per-cell a poor primary target.
*Suggestion.* Rename the target throughout (e.g. "m_DFT, total moment per cell", in μB/cell) and remove "Ms" from all tables and figures. Make μB per formula unit (or per magnetic atom) the primary target, with per-cell as secondary. State the functional mix and how often MP used FM initialization, and consider analysing only magnetic (m > 0) entries, or a hurdle model separating zero from non-zero moments.
*Severity:* Major.

**W3: The ordering target and its interpretation need domain decomposition.**
*Problem.* (a) The NM class (31,673 of 79,125) includes many compounds with no magnetism-capable element, which are easy to classify, so macro-F1 0.73 partly measures "contains Fe/Mn/Co/rare earth". (b) FiM recall is low throughout: in the matched results files, per-split FiM recall is about 0.1-0.47. (c) The provenance-transfer failure (macro-F1 0.284; balanced accuracy 0.323, Table 6) is attributed generically to "labelling convention". The domain explanation is that MP labels are biased toward FM by FM-initialized calculations and limited AFM enumeration (Horton et al. 2019). Experimental and MP populations also differ chemically, which confounds label convention with covariate shift. (d) The table note says "three-class chance", but the target has four classes, and the paper does not explain why the experimental set has three.
*Why it matters.* Without these points, readers cannot tell whether ordering models fail because of chemistry, because of label physics, or both.
*Suggestion.* Report ordering metrics also on the subset that contains at least one magnetism-capable element (the C1 list). Report per-class recall in the main text. In the provenance analysis, compare covariate shift (e.g. composition-distance distributions) with label disagreement on formulas present in both provenances: how often is an experimental AFM or FiM labelled FM in MP? Explain the three-class chance level.
*Severity:* Major.

**W4: The size of residual contamination in the T_C target is not reported.**
*Problem.* C5 removes Néel-like values only for formulas whose ordering labels are all AFM. Formulas without ordering labels, weak ferromagnets and canted AFMs (e.g. orthoferrites, which the external audit excluded under A4), and ferrimagnets for which a compensation temperature was text-mined all pass. C3 (<1 K) also removes some genuine low-T_C dipolar ferromagnets. Within-formula dispersion is not reported. Text-mined compilations are known to give a single formula (including elemental Ni) T_C values that differ by orders of magnitude, and values between 1 and 1400 K survive C1-C5.
*Why it matters.* The noise floor bounds every T_C MAE in the paper and limits the "no tier gain" conclusion: a 10 K practical margin may be below the label noise.
*Suggestion.* Hand-audit a stratified random sample of about 200 retained T_C records (by source and by T_C range), report the estimated contamination rate, and report the within-formula standard deviation or MAD of T_C as a label-noise floor. Compare that floor with the 10 K margin and the 76 K MAE.
*Severity:* Major.

**W5: Thin positioning against prior magnetic ML and high-throughput magnetism work.**
*Problem.* The Introduction cites Nelson & Sanvito 2019, Belot 2023 and Abedi Orang 2026 in one clause. Their reported T_C errors, datasets and descriptor findings are never compared with the 76 K MAE and R² 0.78 reported here. Abedi Orang et al. compare descriptor engineering with GNNs on the same 2,500-compound table that is used here as the external benchmark. Their in-distribution results are the natural reference point, and the overlap the audit found bears directly on how those results should be read. Structure-based and graph-based work is mentioned only under Limitations, and the most relevant studies of magnetic classifiers and Curie temperature are missing (see below).
*Why it matters.* The claimed contribution, "these properties are rarely measured together", is plausible, but readers need to see where the accuracy sits relative to the field and which earlier claims the audit qualifies.
*Suggestion.* Add a short paragraph and a table of prior T_C and ordering results: dataset, N, split type, MAE/R² or accuracy, descriptors. Discuss explicitly the implication of the 80% composition overlap for earlier results on the malaei/Abedi Orang table, while staying factual and not attributing leakage to work that used different splits.
*Severity:* Minor-to-Major.

### Missing key references (each existence confirmed)
1. Long, T., Fortunato, N. M., Zhang, Y., Gutfleisch, O., & Zhang, H. (2021). An accelerating approach of designing ferromagnetic materials via machine learning modeling of magnetic ground state and Curie temperature. *Materials Research Letters*, 9(4), 169-174. https://doi.org/10.1080/21663831.2020.1863876. Joint FM/AFM classification and T_C regression; reports that structural descriptors add to composition, a direct counterpoint to RQ1.
2. Merker, H. A., Heiberger, H., Nguyen, L., et al. (2022). Machine learning magnetism classifiers from atomic coordinates. *iScience*, 25, 105192. https://doi.org/10.1016/j.isci.2022.105192. Structure-based (equivariant GNN) FM/AFM/NM classification; the graph-network alternative named in Limitations.
3. Court, C. J., & Cole, J. M. (2020). Magnetic and superconducting phase diagrams and transition temperatures predicted using text mining and machine learning. *npj Computational Materials*, 6, 18. https://doi.org/10.1038/s41524-020-0287-8. ML on the same text-mined database, which also mixes superconducting and magnetic transitions; relevant to C1-C5.
4. Sanvito, S., Oses, C., Xue, J., et al. (2017). Accelerated discovery of new magnets in the Heusler alloy family. *Science Advances*, 3(4), e1602241. https://doi.org/10.1126/sciadv.1602241. A high-throughput DFT + T_C-model discovery that was confirmed by synthesis (Co2MnTi); a benchmark for the discovery framing of the Conclusion.
5. Liechtenstein, A. I., Katsnelson, M. I., Antropov, V. P., & Gubanov, V. A. (1987). Local spin density functional approach to the theory of exchange interactions in ferromagnetic metals and alloys. *Journal of Magnetism and Magnetic Materials*, 67(1), 65-74. The standard route from DFT to exchange constants and T_C; needed to define what a "physics descriptor" for T_C would be.
6. Choudhary, K., & DeCost, B. (2021). Atomistic Line Graph Neural Network for improved materials property predictions. *npj Computational Materials*, 7, 185. https://doi.org/10.1038/s41524-021-00650-1. A GNN baseline trained on JARVIS data, including magnetic-moment tasks.
7. Omee, S. S., Fu, N., Dong, R., Hu, M., & Hu, J. (2024). Structure-based out-of-distribution (OOD) materials property prediction: a benchmark study. *npj Computational Materials*, 10. (arXiv:2401.08032). OOD benchmark directly relevant to RQ3.
8. Varivoda, D., Dong, R., Omee, S. S., & Hu, J. (2023). Materials property prediction with uncertainty quantification: A benchmark study. *Applied Physics Reviews*, 10, 021409. https://doi.org/10.1063/5.0133528. A materials-UQ benchmark; positions RQ2 beyond Tran et al. 2020.

### Questions to authors
1. Which DFT magnetic quantities were excluded from Tier 3, and was the exclusion applied to the ordering and T_C targets as well as the moment? Would per-site magnetic moments (not the total) count as leakage for T_C?
2. What fraction of the NM class contains at least one magnetism-capable element, and what is macro-F1 on that subset?
3. For formulas labelled both in MP and experimentally, what is the confusion matrix of MP label against experimental label? In particular, how often is an experimental AFM or FiM labelled FM in MP?
4. What is the within-formula spread of T_C after C1-C5, and how many retained records are thin films, nanoparticles, or doped or off-stoichiometric samples collapsed onto one reduced formula?
5. Why was per-cell, rather than per-formula-unit, chosen as the primary moment target, and does the RQ1 conclusion for the moment change under per-formula-unit normalization?
6. In the provenance test, why is chance level three-class (Table 6 note)? Which class is absent from one provenance?
7. Are T_C test metrics weighted per record or per formula? Formulas with many records (Fe, Ni, Co) could dominate either way.

### Minor issues
- Abstract (AFM 57%/FiM 55%, 10-split means) vs Results (57.7%/52.7%, frozen split): label which split each number refers to.
- The Methods should state the excluded magnetic Tier 3 columns explicitly (see W1).
- Compensated ferrimagnets were folded into FiM. Note this, because it matters for the moment target, where compensated FiM have a net moment near zero.
- The C1 list includes Cu and the 4d/5d metals but excludes Ti and Mo. Briefly justify these choices (Cu2+ magnets are an obvious case).
- The highest known ferromagnetic T_C: Co at about 1388-1400 K. Cite a source (e.g. Coey 2010) at the point where the C4 threshold is introduced.
- Resolve all \todo{} markers and the TODO in the malaei bib entry (commit hash).
- Introduction: "complementing high-throughput DFT predictions of magnetic order" cites Horton and Frey. Note there that these predictions are collinear and FM-biased in initialization, which is relevant later (W3).

### Rubric scores (0-100)
| Dimension | Score | Descriptor |
|---|---|---|
| Originality | 70 | Adequate-strong: the joint accuracy/physics/calibration/generalization assessment and the benchmark audit are new for magnetism; the individual methods are established |
| Methodological rigor | 72 | Adequate-strong: excellent statistical design; domain target-construction gaps (W2-W4) |
| Evidence sufficiency | 70 | Adequate: claims supported within scope; ~38 references but key magnetism-ML and OOD/UQ works missing |
| Argument coherence | 70 | Adequate: thesis follows; RQ1 generalization overreaches |
| Writing quality | 72 | Clear prose; terminology ("Ms") and TODOs |
| Literature integration (R2 optional) | 60 | Gaps in magnetic ML, GNN, OOD/UQ; prior results not engaged |
| Weighted (0.20/0.25/0.25/0.15/0.15) | 70.9 | |

The rubric average (about 71) would map to Minor Revision. Under the sprint contract, however, the editorial decision is set by the failure conditions (F2 fired), so the contract-governed decision below takes precedence.

## Editorial Decision
**Major Revision.** F2 fired: three mandatory dimensions (D1, D2, D3) score warn. No block fired. Required for re-review:
- Narrow and justify the RQ1 framing (W1), and preferably test magnetic-structure descriptors.
- Rename and renormalize the moment target (W2).
- Decompose the ordering results by magnetic-element presence and by MP-vs-experiment label physics (W3).
- Quantify the residual noise in the T_C labels (W4).
- Position the results against prior magnetic ML studies (W5).
