# Devil's Advocate Reviewer -- Phase 1 (paper-content-blind)

Contract: reviewer/reviewer_full/v1 (mode reviewer_full, stage reviewer_full_review, baseline v3.6.2, panel_size 5), used verbatim; generated_at 2026-11-09T15:29:00Z.
Paper metadata seen: title "Accuracy is not reliability: physics descriptors, calibration and chemical generalization in machine learning of magnetic materials"; field computational materials science / ML for magnetic materials; ~3,500 words. No manuscript content has been opened.

## Contract Paraphrase

**D1 methodology_rigor (mandatory).** From an adversarial stance: could the reported numbers be the product of design choices rather than of the phenomena claimed? I will test whether data handling, splitting, model selection, uncertainty estimation and reporting are fixed in advance and transparent enough that a hostile reader could not attribute the findings to analyst degrees of freedom, leakage, or an unrepresentative evaluation population, and whether the work could be reproduced.

**D2 domain_accuracy (mandatory).** Do the claims about magnetic materials, descriptors, calibration methods and prior ML work hold up against what the field knows? I will look for misrepresented prior work, physically incorrect statements (units, definitions of magnetic quantities, provenance of labels), and conclusions about "physics" that really concern a particular database artefact.

**D3 argumentative_coherence (mandatory).** This is my core dimension. Is the central thesis falsifiable and non-trivial, does each step of the evidence chain support the conclusion actually stated, and is the strength of language matched to the strength of evidence? I will hunt for definitional or trivially expected theses, overgeneralization from specific instantiations to general categories, and Discussion/Conclusion sentences that go beyond the results.

**D4 cross_disciplinary_relevance (high).** Would an ML-methods reader, a materials experimentalist, or a database curator understand and be able to use the framing, and are claims that reach into adjacent fields (statistics of conformal prediction, materials discovery practice) substantiated? I will ask the "so what?" question on behalf of these readers.

**D5 writing_and_structure (normal).** Is the manuscript organised so the argument is traceable, are tables/figures faithful to the text and readable, and are venue conventions followed? Adversarially: do presentation choices (what is shown in the main text vs supplement) steer the reader toward the thesis?

## Scoring Plan

### D1: methodology_rigor
- dimension_id: D1
- what_to_look_for: pre-registration or prespecification of hypotheses, gates and analysis choices; number of targets x algorithms x tiers x subsets x dataset versions and whether a multiplicity or forking-paths control is stated; how dataset revisions/corrections were decided (blind to outcome or not); grouped splitting and leakage checks; repeated splits and interval estimation; matched-population construction; reproducibility package; reporting of all runs, not only favoured ones.
- what_triggers_block: evidence that a headline result depends on an undisclosed or outcome-informed analytic choice, a leakage path that plausibly produces the headline numbers, or results that cannot be traced to a stated procedure; or post-hoc corrections applied selectively in the direction of the thesis.
- what_triggers_warn: many forking paths without explicit multiplicity discussion; prespecification claimed but partly post-hoc; matched populations or subsets that are small/selected so that power to detect a descriptor effect is limited and not quantified; some results reported only in the favoured direction.

### D2: domain_accuracy
- dimension_id: D2
- what_to_look_for: correct definitions of magnetic targets (ordering classes, Curie vs Neel temperatures, moment per cell vs per atom vs per formula unit); correct description of the provenance of DFT-derived descriptors (e.g. formula-level joins to a single polymorph); faithful citation of prior ML-for-magnetism and calibration/UQ literature; whether "physics descriptors" as operationalised match what domain readers would call physics descriptors.
- what_triggers_block: a factual error in a target definition or descriptor provenance that changes the interpretation of a headline result; prior work misrepresented in a way that manufactures the novelty of the thesis.
- what_triggers_warn: the label "physics descriptors" applied to a narrow, mismatched or proxy descriptor set without qualification; missing key prior work on structure-aware models or calibration in materials ML; imprecise unit/provenance statements that do not overturn conclusions.

### D3: argumentative_coherence
- dimension_id: D3
- what_to_look_for: whether the central thesis ("accuracy, physics-descriptor gains, calibration and generalization are distinct") is stated in a falsifiable form with a criterion for what would count as them NOT being distinct; whether evidence for "distinctness" is more than showing the four quantities differ numerically; overgeneralization from specific descriptors/models/populations to general categories; ranking statements (e.g. one property being "least informative") and whether they are derived from data; consistency between abstract, results, discussion, and the tables.
- what_triggers_block: a headline conclusion that does not follow from (or is contradicted by) the paper's own evidence, or a thesis that is purely definitional and presented as an empirical finding without any test.
- what_triggers_warn: thesis largely expected a priori but framed as discovery; scope of negative results stated more generally than the tested instantiation; Discussion/Conclusion sentences that rank or generalize beyond results; hedged qualifiers in Results that disappear in Abstract/Conclusion.

### D4: cross_disciplinary_relevance
- dimension_id: D4
- what_to_look_for: actionable recommendations for practitioners (what to report, how to evaluate); accessibility of calibration/conformal terminology to materials readers and of magnetism terminology to ML readers; whether implications for discovery/screening are substantiated; stakeholders (experimentalists, database curators, screening users) addressed.
- what_triggers_block: implications for adjacent fields asserted with no supporting evidence and central to the paper's claimed contribution.
- what_triggers_warn: "so what?" answer weak or generic; recommendations not tied to specific findings; key terms undefined for one of the two audiences.

### D5: writing_and_structure
- dimension_id: D5
- what_to_look_for: traceability from each claim to a table/figure; consistency of numbers between text, tables and figures; figure legibility and honest axes; organisation of a dense multi-RQ study within ~3,500 words; venue-conventional sections (data/code availability, limitations).
- what_triggers_block: numbers in the text that contradict tables/figures for headline results, or structure so compressed that the main argument cannot be followed.
- what_triggers_warn: minor number mismatches, overloaded figures, key caveats relegated to supplement, missing availability statements.

[CONTRACT-ACKNOWLEDGED]
