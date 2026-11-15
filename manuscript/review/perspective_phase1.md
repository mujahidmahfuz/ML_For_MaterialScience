# Peer Reviewer 3 (Perspective) — Phase 1 (paper-content-blind)

contract_id: reviewer/reviewer_full/v1 · mode: reviewer_full · generated_at: 2026-11-09T17:12:01Z
Metadata used: title "Accuracy is not reliability: physics descriptors, calibration and chemical generalization in machine learning of magnetic materials"; field "computational materials science / machine learning for magnetic materials"; word_count ~3,500.

## Contract Paraphrase

**D1 methodology_rigor (mandatory).** From a practitioner's standpoint, rigor means a discovery team could trust the evaluation design enough to reuse it: data are handled with explicit provenance, splits reflect how the model would actually be deployed (new compositions / chemical systems, not random rows), uncertainty is reported, and the code/data package lets an outside group rerun the analysis. Reproducibility affordances (licensing, access, environment) count here, not only statistics.

**D2 domain_accuracy (mandatory).** Claims about magnetic materials, the data sources used, and adjacent ML concepts (calibration, conformal prediction, distribution shift) must be stated correctly, and prior work — in materials informatics and the general-ML reliability literature — must be represented fairly rather than strawmanned.

**D3 argumentative_coherence (mandatory).** The thesis implied by the title (accuracy and reliability are separable) must actually follow from the evidence, and the practical recommendations should be derivable from results rather than appended opinion; claims must not outrun the evidence (e.g. discovery claims from interpolation results).

**D4 cross_disciplinary_relevance (high).** Readers from self-driving labs, data infrastructure, and general ML should be able to understand the definitions and act on the implications; claims that the lessons generalize beyond magnetism ("physics-informed" in other property domains, screening/active learning practice) must be substantiated or appropriately hedged.

**D5 writing_and_structure (normal).** Organisation, clarity, figure/table usability, and venue conventions; whether a busy practitioner can extract the key messages and recommendations quickly.

## Scoring Plan

### D1: methodology_rigor
- dimension_id: D1
- what_to_look_for: grouped/out-of-distribution splits (formula-, chemical-system-level); repeated splits or intervals; explicit provenance tracking of labels (experimental vs computed vs text-mined); external benchmark with leakage/overlap audit; a reproducibility package with documented run path, pinned environment, data access route and licence status.
- what_triggers_block: headline results evaluated only on random splits with known train/test leakage left unaddressed; or no way for an outside group to obtain the data/code needed to reproduce headline numbers; or external benchmark overlap with training unmeasured while being used to claim generalization.
- what_triggers_warn: leakage/overlap measured and disclosed but incompletely resolved; reproducibility package exists but has gaps (unverified upstream licences, external data not redistributable, nondeterminism undocumented); uncertainty on some but not all headline claims.

### D2: domain_accuracy
- dimension_id: D2
- what_to_look_for: correct description of sources (MP, OQMD, JARVIS, text-mined compilations etc.) and of targets (Curie vs Néel, per-cell vs per-atom moments); correct use of calibration/conformal terminology; fair citation of materials-ML benchmarking work (e.g. leave-cluster-out, Matbench-type evaluation) and general-ML distribution-shift literature.
- what_triggers_block: factual errors that change the interpretation of a headline result (e.g. mislabelled physical quantity driving a claim) or misrepresentation of prior work as having not done what it did.
- what_triggers_warn: missing key adjacent literature (OOD benchmarks in materials ML, selective prediction, active-learning use of UQ) or imprecise terminology that a domain reader could misread, without changing conclusions.

### D3: argumentative_coherence
- dimension_id: D3
- what_to_look_for: mapping from each result to each conclusion/recommendation; hedging calibrated to interval widths; no conflation of "no stable gain" with "no effect"; recommendations traceable to evidence.
- what_triggers_block: central thesis contradicted by the paper's own results, or recommendations that require evidence the paper does not present.
- what_triggers_warn: some recommendations only loosely supported or generic; occasional overreach in abstract/discussion relative to results.

### D4: cross_disciplinary_relevance
- dimension_id: D4
- what_to_look_for: definitions of calibration, coverage, chemical-system generalization accessible to non-specialists; explicit connection to screening, active learning and selective prediction workflows; discussion of the data-provenance problem as field-wide (shared upstream compilations, text mining, FAIR, licences); bounded claims about other property domains.
- what_triggers_block: the paper's practical framing (e.g. recommendations for discovery) is unsupported or misleading for practitioners, or broad cross-domain claims are made with no supporting argument.
- what_triggers_warn: implications stated but not operationalized (no concrete workflow, threshold, or decision rule); weak links to general-ML reliability literature; provenance issue treated as a local quirk rather than field-wide.

### D5: writing_and_structure
- dimension_id: D5
- what_to_look_for: clear abstract with numbers; figures readable and self-contained; tables with units and N; recommendations easy to find; length appropriate for venue (~3,500 words); consistent terminology.
- what_triggers_block: manuscript cannot be followed without supplementary material, or key figures/tables missing or unreadable.
- what_triggers_warn: dense or jargon-heavy passages, overloaded figures, inconsistent naming, or recommendations buried.

[CONTRACT-ACKNOWLEDGED]
