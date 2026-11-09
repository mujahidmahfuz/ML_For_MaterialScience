"""Build every paper table from data/ and results/ (no model is fit). Each table is written as CSV and as a LaTeX booktabs
fragment for the sn-jnl manuscript (\\input{../tables/<name>.tex}). Usage (package root):  python scripts/make_tables.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

PKG = Path(__file__).resolve().parents[1]
DATA, RES, OUT = PKG / "data", PKG / "results", PKG / "tables"
R1, R2, R3 = RES / "rq1_physics_descriptors", RES / "rq2_uncertainty", RES / "rq3_generalization"
ALG = {"linear": "Ridge / logistic", "gradient_boosting": "Gradient boosting", "xgboost": "XGBoost"}
PRE = "paper (pre-specified: shared-DOI components)"


# --------------------------------------------------------------------------------------------------------- helpers
def ci(est: float, lo: float, hi: float, d: int = 1, signed: bool = False) -> str:
    f = f"{{:{'+' if signed else ''}.{d}f}}"
    return f"{f.format(est)} [{f.format(lo)}, {f.format(hi)}]"


def tex_escape(s: str) -> str:
    for a, b in [("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#"), ("±", "$\\pm$"), ("≥", "$\\geq$"),
                 ("≤", "$\\leq$"), ("μB", "$\\mu_\\mathrm{B}$"), ("→", "$\\rightarrow$"), ("−", "$-$"), ("²", "$^2$"), ("³", "$^3$")]:
        s = s.replace(a, b)
    return s


def save(df: pd.DataFrame, name: str, caption: str, notes: str = "") -> None:
    df.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8")
    cols = "l" * len(df.columns)
    lines = ["\\begin{table}[h]", f"\\caption{{{tex_escape(caption)}}}", f"\\label{{tab:{name}}}", "\\begin{tabular*}{\\textwidth}{@{\\extracolsep\\fill}" + cols + "}",
             "\\toprule", " & ".join(tex_escape(str(c)) for c in df.columns) + " \\\\", "\\midrule"]
    lines += [" & ".join(tex_escape(str(v)) for v in row) + " \\\\" for row in df.itertuples(index=False)]
    lines += ["\\botrule", "\\end{tabular*}"]
    if notes:
        lines += ["\\footnotetext{" + tex_escape(notes) + "}"]
    lines += ["\\end{table}"]
    (OUT / f"{name}.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if notes:
        (OUT / f"{name}.notes.txt").write_text(notes + "\n", encoding="utf-8")


# --------------------------------------------------------------------------------------------------------- Table 1
def table1_dataset() -> None:
    sp = DATA / "splits" / "v1.4"
    spec = [("Magnetic ordering (FM/AFM/FiM/NM)", "class", "split_ordering.csv", "matched_split_ordering.csv"),
            ("Curie temperature", "K", "split_curie.csv", "matched_split_curie.csv"),
            ("DFT total magnetic moment per unit cell (Ms)", "μB/cell", "split_ms.csv", "matched_split_ms.csv"),
            ("Mass magnetization (secondary)", "emu/g", "split_ms_mass.csv", None),
            ("Volume magnetization (secondary)", "A/m", "split_ms_volume.csv", None),
            ("Anisotropy constant K1 (secondary)", "J/m³", "split_k1.csv", None)]
    rows = []
    for name, unit, f, matched in spec:
        s = pd.read_csv(sp / f, usecols=["reduced_formula", "split", "tier3"])
        m = len(pd.read_csv(sp / matched, usecols=["material_id"])) if matched else None
        rows.append({"Target": name, "Unit": unit, "Records": f"{len(s):,}", "Formulas": f"{s['reduced_formula'].nunique():,}",
                     "Train / validation / test": "/".join(f"{(s['split'] == k).sum():,}" for k in ("train", "validation", "test")),
                     "Matched Tier 1/2/3 records": f"{m:,}" if m else "-"})
    o = pd.read_csv(DATA / "analysis_dataset/v1.4/targets/ordering/target_ordering_clean.csv", usecols=["magnetic_ordering_clean", "ordering_valid"], low_memory=False)
    counts = o[o["ordering_valid"].astype(bool)]["magnetic_ordering_clean"].value_counts()
    notes = ("Analysis dataset v1.4 (frozen); formula-grouped 70/15/15 splits. Ordering classes: " + ", ".join(f"{k} {v:,}" for k, v in counts.items()) +
             ". Tier 1 = 65 composition descriptors; Tier 2 = Tier 1 + 8 oxidation-chemistry descriptors; Tier 3 = Tier 2 + DFT physics descriptors (97 in total).")
    save(pd.DataFrame(rows), "table1_dataset", "Prediction targets of the curated analysis dataset", notes)


# --------------------------------------------------------------------------------------------------------- Table 2
def table2_tiers() -> None:
    rows = []
    o = pd.read_csv(R1 / "matched_tiers/ordering_10split_robustness.csv").query("metric == 'macro_f1'")
    c = pd.read_csv(R1 / "matched_tiers/curie_inference_table.csv").query("analysis == 'primary_matched' and metric == 'mae'")
    m = pd.read_csv(R1 / "matched_tiers/robustness_summary_curie_ms_v1.2.csv").query("target == 'ms_moment' and analysis == 'primary_matched' and metric == 'mae'")
    a = pd.read_csv(R1 / "ms_per_atom/peratom_corrected_tier_effect.csv").query("target == 'per_atom' and population == 'corrected'")
    for alg in ALG:
        for label, d, est, lo, hi, verdict, dig in [
            ("Ordering, macro-F1", o, "pooled_concat_improvement", "pooled_concat_ci_low", "pooled_concat_ci_high", "pooled_concat_verdict", 3),
            ("Curie temperature, MAE (K)", c, "improvement", "ci95_low", "ci95_high", "verdict_margin_10K", 1),
            ("Ms per cell, MAE (μB/cell)", m, "pooled_concat_improvement", "pooled_concat_ci_low", "pooled_concat_ci_high", "robust_verdict", 3)]:
            r = d[d["algorithm"] == alg].set_index(["from_variant", "to_variant"])
            t12, t13 = r.loc[("tier1", "tier2")], r.loc[("tier1", "tier3")]
            rows.append({"Target, metric": label, "Algorithm": ALG[alg], "Tier 1→2": ci(t12[est], t12[lo], t12[hi], dig, True),
                         "Tier 1→3": ci(t13[est], t13[lo], t13[hi], dig, True), "Tier 1→3 verdict": str(t13[verdict]).split(" (")[0]})
        r = a[a["algorithm"] == alg].iloc[0]
        rows.append({"Target, metric": "Ms per atom, relative MAE gain (%)", "Algorithm": ALG[alg], "Tier 1→2": "-",
                     "Tier 1→3": ci(100 * r["mean_relative_mae_gain"], 100 * r["ci_low"], 100 * r["ci_high"], 1, True),
                     "Tier 1→3 verdict": "stable gain" if r["stable_gain"] else "not stable"})
    df = pd.DataFrame(rows).sort_values(["Target, metric", "Algorithm"], kind="stable")
    notes = ("Improvement = Tier k minus Tier 1 performance, positive = better; identical rows, splits, grids and metrics at every tier; 10 repeated "
             "formula-grouped splits; 95% intervals. Matched N: ordering 6,061, Curie 4,602, Ms 10,852 (per atom 10,821 after the denominator correction). "
             "Curie verdict uses a 10 K margin. Ridge Curie Tier 3 fits are numerically unstable (exploded predictions on a few rows). XGBoost results depend on the "
             "thread count; across thread/seed realisations the Ms per-cell XGBoost Tier 1→3 gain ranges from +0.026 to +0.062 μB/cell.")
    save(df, "table2_physics_descriptors", "Effect of oxidation-chemistry (Tier 2) and DFT physics (Tier 3) descriptors on matched populations", notes)


# --------------------------------------------------------------------------------------------------------- Table 3/4
def table3_intervals() -> None:
    rows = []
    for tgt, label, unit_d in [("curie", "Curie temperature", 0), ("ms_moment", "Ms per cell", 1)]:
        fz = pd.read_csv(R2 / tgt / "uq_summary.csv").set_index("method")
        rp = pd.read_csv(R2 / "repeated_splits" / tgt / "repeated_split_summary.csv")
        for meth, mname in [("split_conformal", "Split conformal"), ("normalized_conformal", "Normalized conformal"), ("cqr", "CQR")]:
            f, all_ = fz.loc[meth], rp[(rp["method"] == meth) & (rp["group"] == "all")].iloc[0]
            hard = rp[(rp["method"] == meth) & (rp["group"] == "difficulty_decile:10")].iloc[0]
            rows.append({"Target": label, "Method": mname, "Coverage, frozen split": ci(100 * f["coverage"], 100 * f["coverage_ci_low"], 100 * f["coverage_ci_high"], 1),
                         "Mean width": f"{f['mean_width']:.{unit_d}f}",
                         "Coverage, 10 splits: mean (SD)": f"{100 * all_['mean_coverage']:.1f} ({100 * all_['sd_coverage']:.1f})",
                         "Splits within ±2 points": f"{round(10 * all_['fraction_splits_within_2pt'])}/10",
                         "Hardest decile, 10 splits": f"{100 * hard['mean_coverage']:.1f}"})
    notes = "Nominal coverage 90%; calibration on 20% of training formulas; coverage in %; widths in K (Curie) or μB/cell (Ms). Hardest decile = test rows with the largest model-estimated difficulty."
    save(pd.DataFrame(rows), "table3_regression_intervals", "Coverage of 90% prediction intervals for the regression targets", notes)


def table4_ordering_calibration() -> None:
    cal = pd.read_csv(R2 / "ordering/uq_calibration_metrics.csv")
    sets = pd.read_csv(R2 / "ordering/uq_conformal_sets.csv")
    rep = pd.read_csv(R2 / "repeated_splits/ordering/repeated_split_summary.csv").set_index("method")
    rows = [{"Probabilities / prediction sets": r["probabilities"], "ECE": ci(r["ece"], r["ece_ci_low"], r["ece_ci_high"], 3), "Overall coverage (%)": "-",
             "FM": "-", "AFM": "-", "FiM": "-", "NM": "-", "Mean set size": "-"} for _, r in cal.iterrows()]
    for _, r in sets[sets["probabilities"] == "prior-corrected + temperature"].iterrows():
        name = "Marginal sets" if r["method"] == "marginal_LAC" else "Class-conditional sets"
        rows.append({"Probabilities / prediction sets": f"{name} (prior-corrected + temperature)", "ECE": "-",
                     "Overall coverage (%)": f"{100 * r['coverage']:.1f} (10 splits: {100 * rep.loc[r['method'], 'mean_coverage']:.1f})",
                     **{k: f"{100 * r[f'coverage_{k}']:.1f}" for k in ("FM", "AFM", "FiM", "NM")}, "Mean set size": f"{r['mean_set_size']:.2f}"})
    notes = ("Test N = 11,902; 90% nominal sets; ECE with 95% formula-bootstrap interval. Per-class columns are set coverage (%) on the frozen split; "
             "over 10 repeated splits the marginal sets cover AFM 57.2% and FiM 54.8%, the class-conditional sets 89.9-91.1% for every class.")
    save(pd.DataFrame(rows), "table4_ordering_calibration", "Calibration of magnetic-ordering probabilities and prediction sets", notes)


# --------------------------------------------------------------------------------------------------------- Table 5/6
def table5_external() -> None:
    s = pd.read_csv(R3 / "external_benchmark/subset_metrics_bootstrap.csv")
    s = s[s["cluster"] == PRE]
    order = [("all", "All records"), ("composition seen in training repository", "Composition seen in training"),
             ("seen + value not copied", "  seen, value not copied"), ("composition NEVER seen (blind)", "Composition never seen (blind)"),
             ("blind + paper never used (corrected DOI match)", "Blind + source paper never used"), ("blind + seen chemical system", "Blind + seen chemical system"),
             ("blind + unseen chemical system", "Blind + unseen chemical system"), ("blind + paper never used + unseen system", "Blind + never used + unseen system")]
    prim = s[s["table"].str.startswith("primary")].set_index("subset")
    orig = s[s["table"].str.startswith("original")].set_index("subset")
    first = pd.read_csv(R3 / "external_benchmark/subset_metrics_bootstrap_first_doi.csv")
    papers = first[first["table"].str.startswith("primary")].set_index("subset")["n_papers_first_doi"]
    rows = [{"Subset": lab, "n (papers)": f"{int(prim.loc[k, 'n']):,} ({int(papers.loc[k])})", "MAE, K": ci(prim.loc[k, "mae_k"], prim.loc[k, "mae_k_lo"], prim.loc[k, "mae_k_hi"]),
             "R²": ci(prim.loc[k, "r2"], prim.loc[k, "r2_lo"], prim.loc[k, "r2_hi"], 2), "90% coverage": f"{prim.loc[k, 'coverage']:.3f}",
             "MAE before audit, K": f"{orig.loc[k, 'mae_k']:.1f} (n={int(orig.loc[k, 'n']):,})"} for k, lab in order]
    notes = ("Primary benchmark after the audit (2,395 of 2,500 records). Seen/blind by composition identity against the training repository. 95% intervals "
             "from a cluster bootstrap over source papers (10,000 resamples); papers = first-listed DOIs. Model and intervals unchanged from the blind test.")
    save(pd.DataFrame(rows), "table5_external_benchmark", "Independent experimental Curie benchmark by novelty subset", notes)


def table6_generalization() -> None:
    rows = []
    for tgt, label, metric, d in [("ordering", "Ordering", "macro_f1", 3), ("curie", "Curie temperature", "mae", 1), ("ms_moment", "Ms per cell", "mae", 3)]:
        r = pd.read_csv(R3 / "leave_chemical_system_out" / tgt / "leave_chemsys_summary.csv").set_index("metric").loc[metric]
        rows.append({"Test": "Leave chemical system out (10 paired splits)", "Target": label, "Metric": "macro-F1" if metric == "macro_f1" else "MAE",
                     "Familiar → unfamiliar": f"{r['formula_grouped_mean']:.{d}f} → {r['chemsys_grouped_mean']:.{d}f}",
                     "Change [95% CI]": ci(r["mean_delta"], r["ci_low"], r["ci_high"], d, True), "Splits worse": f"{round(10 * r['fraction_splits_worse'])}/10"})
    t = pd.read_csv(R3 / "label_provenance/ordering_cross_provenance_transfer.csv").query("algorithm == 'xgboost'")
    for _, r in t.iterrows():
        rows.append({"Test": f"Label provenance: train {r['train_on']} → test {r['test_on']}", "Target": "Ordering", "Metric": "macro-F1 / balanced accuracy",
                     "Familiar → unfamiliar": f"{r['macro_f1']:.3f} / {r['balanced_accuracy']:.3f}", "Change [95% CI]": "-", "Splits worse": "-"})
    notes = "Three-class chance balanced accuracy = 0.333. Within-provenance macro-F1: computed (MP) 0.637, experimental 0.784."
    save(pd.DataFrame(rows), "table6_generalization_internal", "Generalization to unfamiliar chemical systems and label provenance", notes)


# --------------------------------------------------------------------------------------------------------- Supplementary
def tables_supplementary() -> None:
    c = pd.read_csv(R3 / "external_benchmark/audit_counts.csv").set_index("item")["count"]
    audit = [("A1", "Computational label (source paper reports no measurement)", "a1_computational_label", "excluded"),
             ("A2", "Malformed composition (mixed-scale, impossible ionic, shorthand)", "a2_malformed", "excluded"),
             ("A3", "Duplicate records (exact or same composition)", "a3b_same_formula_merged", "merged"),
             ("A4", "Outside the training target definition (rules C1-C5)", "a4_training_rule", "excluded"),
             ("A5", "Transition not a magnetic Curie point (from title)", "a5_not_magnetic_tc", "excluded"),
             ("A6", "Possibly not directly comparable (film, nano, pressure, 2D...)", "a6_any_source", "flagged"),
             ("A7", "Composition already in training repository", "a7a_formula_in_repository", "defines subsets"),
             ("A7", "Value identical to a value in our Curie data", "a7c_value_copied_any_row", "defines subsets"),
             ("A8", "No DOI (book reference)", "a8_no_doi", "flagged")]
    save(pd.DataFrame([{"Code": k, "Check": t, "Records": f"{int(c[col]):,}", "Action": a} for k, t, col, a in audit]),
         "tableS1_benchmark_audit", "Audit of the external Curie benchmark (2,500 records; 105 excluded in total)")
    cmp_ = pd.read_csv(R3 / "external_benchmark/subset_comparisons.csv")
    cmp_ = cmp_[cmp_["table"].str.startswith("primary")]
    save(pd.DataFrame([{"Comparison": r["comparison"].replace("seen formula", "seen composition"), "Clusters": r["cluster"].split(" (")[0] + (" (first DOI)" if "first" in r["cluster"] else ""),
                        "MAE difference, K": ci(r["mae_k_diff"], r["mae_k_diff_lo"], r["mae_k_diff_hi"], 0, True),
                        "Share worse (MAE)": f"{r['mae_k_share_a_worse']:.2f}", "R² difference": ci(r["r2_diff"], r["r2_diff_lo"], r["r2_diff_hi"], 2, True),
                        "Share worse (R²)": f"{r['r2_share_a_worse']:.2f}"} for _, r in cmp_.iterrows()]),
         "tableS2_subset_comparisons", "Grouped-bootstrap comparisons between external-benchmark subsets (first minus second subset)")
    b = pd.read_csv(R3 / "external_benchmark/similarity_bins.csv")
    b = b[b["set"] == "primary, blind only"]
    save(pd.DataFrame([{"Distance quartile": r["bin"], "Composition distance": f"{r['d_comp_min']:.3f}-{r['d_comp_max']:.3f}", "n (papers)": f"{r['n']} ({r['n_papers']})",
                        "MAE, K": ci(r["mae_k"], r["mae_k_lo"], r["mae_k_hi"]), "Mean width, K": f"{r['mean_width_k']:.0f}",
                        "Coverage": ci(r["coverage"], r["coverage_lo"], r["coverage_hi"], 2), "Unseen-system share": f"{r['share_unseen_system']:.2f}"}
                       for _, r in b.iterrows()]),
         "tableS3_error_vs_distance", "Error and interval behaviour by composition distance to the training set (truly blind records)")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for f in (table1_dataset, table2_tiers, table3_intervals, table4_ordering_calibration, table5_external, table6_generalization, tables_supplementary):
        f()
    print("tables written:", ", ".join(sorted(p.stem for p in OUT.glob("*.csv"))))


if __name__ == "__main__":
    main()
