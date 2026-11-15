# EIC Phase 1 — Paper-content-blind pre-commitment

Contract: `reviewer/reviewer_full/v1` (mode reviewer_full, stage reviewer_full_review, baseline v3.6.2, panel_size 5), used verbatim; generated_at: 2026-11-09T17:11:59Z.
Paper metadata only: title "Accuracy is not reliability: physics descriptors, calibration and chemical generalization in machine learning of magnetic materials"; field "computational materials science / machine learning for magnetic materials"; word_count ~3,500 (main text + methods, excluding tables).
Reviewer: Editor-in-Chief (Associate Editor, npj Computational Materials).

## Contract Paraphrase

**D1 methodology_rigor (mandatory).** From the editorial chair, I need to be confident that the study design would survive a specialist methods referee at this journal: data curation and splitting are described well enough that leakage and selection effects can be judged; uncertainty around headline numbers is reported; comparisons are pre-specified rather than chosen after seeing results; and code/data/configuration are available so the numbers can be regenerated. I will not redo the statistics (Reviewer 1's job), but I will check that the methods are reported to the field's bar.

**D2 domain_accuracy (mandatory).** The paper must describe magnetism and materials-ML correctly: ordering classes, Curie temperature, saturation magnetization and their units/conventions; the databases it draws on; and, centrally for me, the prior literature on benchmarks, uncertainty quantification and out-of-distribution generalization in materials ML. Claims of novelty or of "first" must survive comparison with that literature.

**D3 argumentative_coherence (mandatory).** The thesis implied by the title — that accuracy and reliability are separable — must be stated clearly, supported by the evidence presented, and not overreach it. Abstract, results, discussion and conclusion must say the same thing; null and negative results must be reported with the same weight as positive ones; and the central claim must be more than a restatement of a known lesson.

**D4 cross_disciplinary_relevance (high).** The paper should be readable by materials scientists who are not ML specialists and by ML researchers who are not magneticians: terms such as calibration, conformal coverage, grouped splits or "physics descriptors" need definitions, and the implications for practitioners (e.g., how to use the models or the checks) should be stated and justified.

**D5 writing_and_structure (normal).** Organisation, prose clarity, figure and table quality, and compliance with venue conventions (length, structure, data/code availability statements, reference format) for an npj Computational Materials article.

## Scoring Plan

### D1: methodology_rigor
- dimension_id: D1
- what_to_look_for: explicit description of data sources, cleaning/exclusion rules and their counts; split strategy (grouped by formula/chemical system or random) and justification; whether comparisons (e.g., with/without physics descriptors) are matched on identical samples; uncertainty intervals and repeated splits/seeds for headline metrics; pre-specification of hypotheses or decision rules; calibration/UQ methods named and evaluated at subgroup level; external test set and its independence from training data; data/code availability statement and a reproducible package.
- what_triggers_block: headline conclusions rest on a design flaw that could reverse them (e.g., evident train–test leakage in the generalization test, unmatched comparisons used to claim a descriptor effect, or a single split/seed with no uncertainty presented as a definitive result), OR no means to reproduce the numbers (no data/code or method detail sufficient to rerun).
- what_triggers_warn: design is sound but reporting is incomplete — some headline numbers without intervals, under-justified exclusion rules, a known leakage or label-provenance issue acknowledged but not quantified, hyperparameter/threshold choices not explained, or small subgroup N used for strong statements.

### D2: domain_accuracy
- dimension_id: D2
- what_to_look_for: correct physics terminology and units for magnetic targets; correct description of source databases and their label provenance (DFT vs experiment vs text-mined); positioning against prior materials-ML work on benchmarks (e.g., Matbench-type), UQ/conformal prediction, OOD/leave-cluster-out generalization and magnetic-property ML; whether cited works are represented fairly and whether novelty claims hold.
- what_triggers_block: factual physics or data errors that alter conclusions (e.g., mixing incompatible quantities as one target), misrepresentation of prior work, or a central novelty claim that is clearly contradicted by well-known existing literature that the paper omits.
- what_triggers_warn: literature positioning is thin or misses key adjacent work on UQ/OOD in materials ML so that the contribution's novelty is overstated or unclear; minor terminology or unit imprecision; some claims about physical mechanism stated more strongly than the evidence shows.

### D3: argumentative_coherence
- dimension_id: D3
- what_to_look_for: a clearly stated thesis and research questions; a one-to-one mapping from each question to evidence; consistency of numbers and qualifiers across abstract, results, discussion and conclusions; honest handling of null results; whether the "distinct properties" framing is demonstrated (e.g., cases where one property is good and another is poor) rather than asserted; whether the take-home message adds something beyond known lessons.
- what_triggers_block: the central claim does not follow from the evidence (e.g., conclusions contradict reported results, or the thesis depends on results not shown), or abstract/conclusion claims materially stronger findings than the results support.
- what_triggers_warn: the thesis is supported but framed as more novel or more general than the single-domain evidence warrants; some sections are disconnected from the research questions; occasional inconsistency of numbers or wording between sections; the main message risks reading as a restatement of known lessons without a sharpened, specific contribution.

### D4: cross_disciplinary_relevance
- dimension_id: D4
- what_to_look_for: definitions of ML/UQ terms for materials readers and of magnetic quantities for ML readers; clear statement of practical implications (what a practitioner should do differently); whether general claims beyond magnetism are substantiated or flagged as hypotheses; accessibility of figures.
- what_triggers_block: the paper is unreadable outside a narrow specialist group, or makes broad cross-field claims (e.g., about all materials ML) with no supporting evidence.
- what_triggers_warn: key terms undefined or jargon-heavy; practical recommendations missing or vague; generalization beyond magnetic materials asserted without being clearly labelled as conjecture.

### D5: writing_and_structure
- dimension_id: D5
- what_to_look_for: logical section order; concise prose; informative titles and captions; figures/tables legible and consistent with text; compliance with npj Computational Materials conventions (length, Methods placement, data/code availability, references); absence of internal jargon, project-internal labels or version codes that a reader cannot interpret.
- what_triggers_block: manuscript structurally unfit for review (missing sections, broken or absent figures/tables, unreadable text).
- what_triggers_warn: dense or jargon-laden passages, internal labels leaking into the text, figure/table inconsistencies with the text, captions that do not stand alone, or venue-convention gaps.

[CONTRACT-ACKNOWLEDGED]
