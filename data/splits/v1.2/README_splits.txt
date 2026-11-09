FROZEN SPLITS - Analysis Dataset v1.2 (decisions D4 + D7)
Derived by EDA/src/make_splits.py --derive from the frozen v1.1 splits (EDA/02_splits/v1.1/, see its README
for the split rule: reduced_formula-grouped, size-balanced stratified group assignment, 70/15/15, seed 20260925).

What changed from v1.1
- Only the D7 pseudo-formula materials were dropped. Every other material keeps exactly its v1.1
  train/validation/test assignment. The script asserts that no material is added and that every dropped
  material is in EDA/datasets/v1.2/excluded/D7_pseudo_formula_materials.csv.
- Rows dropped per file are in split_derivation_log.csv (split_ordering -689, split_curie -928, split_ms_mass -234,
  split_ms_volume -64, split_k1 -114; split_ms and the three matched_split_* files are unchanged).
- Proportions remain about 70/15/15, and ordering class shares stay within about 1 point across splits
  (split_summary.csv).

Files (columns: material_id, reduced_formula, split, stratum, tier3, pseudo_formula [always False in v1.2], Experimental)
- split_ordering.csv 94,618 | split_curie.csv 34,322 | split_ms.csv 87,513
- split_ms_mass.csv 4,318 | split_ms_volume.csv 788 | split_k1.csv 1,862
- matched_split_ordering.csv 13,914 | matched_split_curie.csv 5,490 | matched_split_ms.csv 10,852

Use notes (unchanged from v1.1): Experimental is an evaluation slice only (D5). Report bootstrap CIs for the
matched Curie split, whose validation set holds most of the extreme high-TC values.
