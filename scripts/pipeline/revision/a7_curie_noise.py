"""A7 (SR2): residual label noise in the curated Curie target (v1.3, target_valid rows only).

(1) Within-formula spread: for formulas with >= 2 retained records, SD and MAD of Tc, overall and by source.
(2) Title audit: stratified random sample of 200 retained records (strata = source x Tc tercile, seed 20261110, proportional allocation,
    >= 1 per non-empty stratum), source-paper titles from Crossref, keyword pre-flags; the adjudication itself is recorded by hand in
    a7_title_audit_adjudicated.csv (rubric: magnetic_curie / other_transition / sample_form_factor / unclear / no_title).
Usage: python a7_curie_noise.py spread | sample
Outputs: final/revision/outputs/a7/{within_formula_spread.csv, within_formula_by_source.csv, title_audit_sample.csv}
"""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "final/revision/outputs/a7"
SEED, N_SAMPLE = 20261110, 200
OTHER = ["supercond", "ferroelectric", "antiferro", "néel", "neel", "spin glass", "spin-glass", "metal-insulator", "charge order",
         "structural transition", "martensit", "piezo", "dielectric", "multiferroic", "spin-state", "spin crossover"]
FORM = ["thin film", "films", "nanoparticle", "nanocrystal", "nanowire", "monolayer", "pressure", "ribbon", "amorphous", "glass", "quantum dot"]


def load() -> pd.DataFrame:
    t = pd.read_csv(ROOT / "EDA/datasets/v1.3/targets/curie/target_curie_clean.csv", low_memory=False)
    t = t[t["target_valid"].astype(str) == "True"].copy()
    t["source"] = t["_source"].str.split(" | ").str[0].str.replace("_reformatted", "").str.replace(".csv", "", regex=False)
    return t


def spread(t: pd.DataFrame) -> None:
    g = t.groupby("reduced_formula")["TC_K_clean"]
    stats = pd.DataFrame({"n": g.size(), "sd": g.std(ddof=1), "mad": g.apply(lambda s: float(np.median(np.abs(s - s.median())))),
                          "range": g.max() - g.min()})
    multi = stats[stats["n"] >= 2]
    rows = [{"scope": "all formulas with >=2 records", "n_formulas": len(multi), "n_records": int(multi["n"].sum()),
             "share_of_records": float(multi["n"].sum() / len(t)), "median_sd_k": multi["sd"].median(), "median_mad_k": multi["mad"].median(),
             "mean_sd_k": multi["sd"].mean(), "share_sd_gt_50k": float((multi["sd"] > 50).mean()), "share_sd_gt_100k": float((multi["sd"] > 100).mean()),
             "median_range_k": multi["range"].median()}]
    pd.DataFrame(rows).to_csv(OUT / "within_formula_spread.csv", index=False)
    by = []
    for src, d in t.groupby("source"):
        g = d.groupby("reduced_formula")["TC_K_clean"]
        s = pd.DataFrame({"n": g.size(), "sd": g.std(ddof=1)})
        s = s[s["n"] >= 2]
        by.append({"source": src, "n_records": len(d), "n_formulas_multi": len(s), "median_sd_k": s["sd"].median() if len(s) else np.nan})
    pd.DataFrame(by).to_csv(OUT / "within_formula_by_source.csv", index=False)
    print(pd.DataFrame(rows).round(2).T.to_string(), "\n", pd.DataFrame(by).round(1).to_string(index=False))


def crossref_title(doi: str) -> str:
    doi = str(doi).replace("https://doi.org/", "").replace("http://dx.doi.org/", "").strip()
    if not doi or doi == "nan":
        return ""
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/")
    try:
        r = subprocess.run(["curl", "-s", "-m", "20", "-A", "citation-check-script/1.0", url], capture_output=True, timeout=30)
        msg = json.loads(r.stdout.decode("utf-8", "replace"))["message"]
        return (msg.get("title") or [""])[0]
    except Exception:
        return ""


def sample(t: pd.DataFrame) -> None:
    t = t.copy()
    t["tercile"] = pd.qcut(t["TC_K_clean"].rank(method="first"), 3, labels=["low", "mid", "high"])
    strata = t.groupby(["source", "tercile"], observed=True)
    sizes = strata.size()
    alloc = np.maximum(1, np.floor(N_SAMPLE * sizes / sizes.sum())).astype(int)
    while alloc.sum() < N_SAMPLE:
        alloc[(N_SAMPLE * sizes / sizes.sum() - alloc).idxmax()] += 1
    rng = np.random.default_rng(SEED)
    picks = [g.iloc[rng.choice(len(g), min(alloc[k], len(g)), replace=False)] for k, g in strata]
    s = pd.concat(picks).reset_index(drop=True)
    s["title"] = [crossref_title(d) for d in s["DOI"]]
    low = s["title"].str.lower()
    s["flag_other_transition"] = low.apply(lambda x: any(k in x for k in OTHER))
    s["flag_form_factor"] = low.apply(lambda x: any(k in x for k in FORM))
    cols = ["material_id", "reduced_formula", "source", "tercile", "TC_K_clean", "DOI", "title", "flag_other_transition", "flag_form_factor"]
    s[cols].to_csv(OUT / "title_audit_sample.csv", index=False)
    print(f"sampled {len(s)}; with title {int((s['title'] != '').sum())}; flagged other {int(s['flag_other_transition'].sum())}, "
          f"form factor {int(s['flag_form_factor'].sum())}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t = load()
    {"spread": spread, "sample": sample}[sys.argv[1]](t)


if __name__ == "__main__":
    main()
