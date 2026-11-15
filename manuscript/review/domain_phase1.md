# Domain Reviewer (Peer Reviewer 2) -- Phase 1 (paper-content-blind)

Contract: reviewer/reviewer_full/v1 (mode reviewer_full, baseline v3.6.2, panel_size 5)
generated_at: 2026-11-10T00:00:00Z
Metadata used: title "Accuracy is not reliability: physics descriptors, calibration and chemical generalization in machine learning of magnetic materials"; field "computational materials science / machine learning for magnetic materials"; word_count ~3,500.

## Contract Paraphrase

**D1 methodology_rigor (mandatory).** From a domain angle: are the data sources, target definitions and splits built in a way a computational-magnetism reader would accept (no leakage of the same compound across splits, targets curated with physically defensible rules, statistics reported with intervals, enough detail to reproduce)? I will not duplicate the methodology reviewer's technical audit, but I will check that the target construction and evaluation design are fit for the physical question.

**D2 domain_accuracy (mandatory).** Do the claims match current magnetism and materials-informatics evidence? Are prior ML studies on Curie temperature, magnetic ordering and moments represented correctly; are terms such as Curie vs Neel temperature, saturation magnetization vs DFT total moment, ferrimagnet vs antiferromagnet used precisely; are numbers and physical statements correct?

**D3 argumentative_coherence (mandatory).** Does the central thesis (accuracy differs from reliability; physics descriptors, calibration and generalization are distinct) follow from the evidence presented, without overgeneralising from a specific descriptor set or dataset to the field?

**D4 cross_disciplinary_relevance (high).** Can materials scientists who are not ML specialists, and ML researchers who are not magneticians, follow the definitions and implications? Are interdisciplinary claims (e.g. about materials discovery practice) substantiated?

**D5 writing_and_structure (normal).** Is the manuscript well organised, with clear figures/tables and adherence to journal conventions?

## Scoring Plan

### D1: methodology_rigor
- dimension_id: D1
- what_to_look_for: explicit, physically justified curation rules for each target (Curie vs Neel/other transitions, units, plausibility ranges); treatment of computational default labels; grouped splits by composition/chemical system; uncertainty intervals on headline comparisons; matched populations when comparing descriptor tiers; reproducibility statement and data/code availability.
- what_triggers_block: targets that mix physically distinct quantities without acknowledgement (e.g. Neel temperatures counted as Curie, experimental Ms pooled with DFT moments as if equivalent) in a way that invalidates the headline results; random (non-grouped) splits for generalization claims; no uncertainty on central comparisons.
- what_triggers_warn: curation rules present but incomplete or under-justified for a subset of labels; normalization choices (per cell / per atom / per formula unit) not fully explained; reproducibility details partly missing.

### D2: domain_accuracy
- dimension_id: D2
- what_to_look_for: correct physical definitions; correct representation of prior work (Nelson & Sanvito 2019, Court & Cole 2018/2020, NEMAD, high-throughput magnetic-ground-state DFT, GNN approaches); absence of factual errors about databases (Materials Project, JARVIS, OQMD) and their magnetic conventions; key recent references present.
- what_triggers_block: a factual error in a domain fact on which a headline conclusion rests (e.g. misinterpreting what a database's magnetic moment field measures in a way that changes the result), or misrepresentation of prior work that inflates novelty.
- what_triggers_warn: significant missing key references; imprecise terminology (e.g. "saturation magnetization" for a 0 K DFT moment) that is not decisive; conclusions about "physics descriptors" stated more generally than the descriptors tested justify.

### D3: argumentative_coherence
- dimension_id: D3
- what_to_look_for: alignment between abstract/conclusion claims and results; scope qualifiers on negative results; consistency of numbers across text/tables/figures; treatment of null results as "not shown" vs "shown absent".
- what_triggers_block: central thesis contradicted by the paper's own results, or a negative claim presented as general when the evidence covers only a narrow descriptor set and is underpowered.
- what_triggers_warn: some claims overreach scope (generalizing beyond descriptor family/dataset), or inconsistent numbers that do not change conclusions.

### D4: cross_disciplinary_relevance
- dimension_id: D4
- what_to_look_for: accessible definitions of conformal prediction/calibration for materials readers and of magnetic quantities for ML readers; practical implications for screening/discovery workflows that are supported by results.
- what_triggers_block: implications for materials discovery or practice that are asserted with no supporting evidence and are central to the framing; jargon making the main message inaccessible.
- what_triggers_warn: some terms undefined; practical guidance vague or only partly supported.

### D5: writing_and_structure
- dimension_id: D5
- what_to_look_for: logical section flow, figure legibility and labelling, table notes, length appropriate to a ~3,500-word article, consistent terminology, venue template conformance.
- what_triggers_block: manuscript so disorganised or figures so unreadable that results cannot be evaluated.
- what_triggers_warn: dense or jargon-heavy passages, figures needing better labelling, inconsistent naming of targets/tiers.

[CONTRACT-ACKNOWLEDGED]
