"""A7: hand adjudication of the 200-record Curie title audit (adjudicated 2026-11-10 from Crossref titles + compound + value plausibility).

Categories (a record can carry one primary category):
  other_transition   title/compound show the value is a non-Curie transition (superconducting, ferroelectric, Neel, charge order)
  value_implausible  value clearly inconsistent with the known bulk Tc of that compound (extraction error)
  computational      source paper is computational/theoretical (value may be predicted, not measured)
  compound_mismatch  the paper studies a different compound; the value is a cited/reference value (often plausible)
  form_factor        film, nano, ribbon, amorphous, multilayer or doped-semiconductor sample (value may differ from bulk)
  unclear / no_title
  consistent         everything else
"Likely wrong label" = other_transition + value_implausible + computational.
"""
from pathlib import Path
import numpy as np, pandas as pd
from statsmodels.stats.proportion import proportion_confint
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "final/revision/outputs/a7"
CAT = {
 "other_transition": [2, 33, 44, 55, 71, 77, 120],
 "value_implausible": [6, 15, 50, 82, 113, 166, 171],
 "computational": [0, 11, 30, 46, 60, 84, 173, 179],
 "compound_mismatch": [14, 16, 18, 19, 23, 24, 26, 34, 38, 51, 95, 96, 97, 103, 107, 108, 115, 119, 121, 123, 132, 137, 143, 147, 148, 149,
                       150, 163, 164, 167, 172, 193],
 "form_factor": [10, 25, 31, 41, 42, 43, 54, 56, 58, 59, 67, 68, 73, 81, 102, 124, 129, 135, 156, 157, 165, 178, 192, 196, 198],
 "unclear": [28, 92, 105, 122, 185],
 "no_title": [118, 141],
}
s = pd.read_csv(OUT / "title_audit_sample.csv")
s["category"] = "consistent"
for c, idx in CAT.items():
    assert not set(idx) & set(s.index[s["category"] != "consistent"]), c
    s.loc[idx, "category"] = c
s.to_csv(OUT / "title_audit_adjudicated.csv", index=False)
rows = []
for name, cats in [("likely wrong label (other transition + implausible value + computational)", ["other_transition", "value_implausible", "computational"]),
                   ("non-Curie transition", ["other_transition"]), ("implausible value", ["value_implausible"]), ("computational source", ["computational"]),
                   ("paper about a different compound", ["compound_mismatch"]), ("film/nano/amorphous sample", ["form_factor"]),
                   ("unclear or no title", ["unclear", "no_title"])]:
    k = int(s["category"].isin(cats).sum())
    lo, hi = proportion_confint(k, len(s), method="wilson")
    rows.append({"category": name, "count": k, "n": len(s), "rate": k / len(s), "wilson_lo": lo, "wilson_hi": hi})
by_src = s.assign(wrong=s["category"].isin(["other_transition", "value_implausible", "computational"])).groupby("source")["wrong"].agg(["sum", "size"])
pd.DataFrame(rows).to_csv(OUT / "title_audit_rates.csv", index=False)
by_src.to_csv(OUT / "title_audit_by_source.csv")
print(pd.DataFrame(rows).round(3).to_string(index=False)); print(by_src)
