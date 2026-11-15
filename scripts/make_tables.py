"""Build every paper table from data/ and results/ (no model is fit). Each table is written as CSV and as a LaTeX booktabs
fragment for the sn-jnl manuscript (\\input{../tables/<name>.tex}). Usage (package root):  python scripts/make_tables.py
Revision round 1 (2026-11-10): tier tables use the refit-aware rule of results/revision/a1_tier_inference.csv; interval tables use subgroups
not defined by any method's own difficulty score; the provenance test is on the shared FM/AFM/FiM label space; new tables for the
magnetic-physics test, the moment per formula unit, screening, label noise, external-benchmark inference and design effects.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

PKG = Path(__file__).resolve().parents[1]
DATA, RES, OUT = PKG / "data", PKG / "results", PKG / "tables"
R1, R2, R3, RV = RES / "rq1_physics_descriptors", RES / "rq2_uncertainty", RES / "rq3_generalization", RES / "revision"
ALG = {"linear": "Ridge / logistic", "linear_clip": "Ridge (clipped inputs)", "gradient_boosting": "Gradient boosting", "xgboost": "XGBoost",
       "xgboost_seedmean": "XGBoost"}
PRE = "paper (pre-specified: shared-DOI components)"
TARGET = {"ordering": "Ordering, macro-F1", "curie": "Curie temperature, MAE (K)", "ms_moment": "Moment per cell, MAE (μB/cell)"}


# --------------------------------------------------------------------------------------------------------- helpers
def ci(est: float, lo: float, hi: float, d: int = 1, signed: bool = False) -> str:
    f = f"{{:{'+' if signed else ''}.{d}f}}"
    return f"{f.format(est)} [{f.format(lo)}, {f.format(hi)}]"


def tex_escape(s: str) -> str:
    s = s.replace("->", "→").replace("<=", "≤").replace(">=", "≥")
    s = re.sub(r"(?<![\w.$])-(?=\d)", "−", s)          # typographic minus before a number
    s = re.sub(r"(?<=\d)-(?=\d)", "--", s)              # en dash in numeric ranges
    for a, b in [("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#"), ("±", "$\\pm$"), ("≥", "$\\geq$"),
                 ("≤", "$\\leq$"), ("μB", "$\\mu_\\mathrm{B}$"), ("→", "$\\rightarrow$"), ("−", "$-$"), ("²", "$^2$"), ("³", "$^3$"), ("κ", "$\\kappa$")]:
        s = s.replace(a, b)
    for a, b in [("m\\_cell x ", "$m_\\mathrm{cell}\\times$ "), ("m\\_cell", "$m_\\mathrm{cell}$"), ("m\\_fu", "$m_\\mathrm{fu}$")]:
        s = s.replace(a, b)
    s = re.sub(r"\bTc\b", r"$T_\\mathrm{C}$", s)
    return re.sub(r"\bK1\b", r"$K_1$", s)


def tex_cell(v: object) -> str:
    s = str(v)
    if s.strip() == "-":
        return "--"
    return ("\\quad " if s.startswith("  ") else "") + tex_escape(s.strip())


# Layout per table: column specification (X = wrapping text column filling the width, l/r/c = natural width) and whether repeated
# values in the first column are blanked and the groups separated. Tables are set at full text width in one font (\tablefont, defined
# in the manuscript preamble) so that every table in the paper has the same look.
LAYOUT = {"table1_dataset": ("Xlrrlr", False), "table2_physics_descriptors": ("Xlllrl", True), "table3_magnetic_physics": ("Xrllll", True),
          "table4_regression_intervals": ("Xlllll", True), "table5_ordering_calibration": ("Xrrrrrrrr", False),
          "table6_external_benchmark": ("Xrlllr", False), "table7_generalization_internal": ("XlllX", True),
          "table8_screening": ("Xrl", False), "tableS1_benchmark_audit": ("lXrl", False), "tableS2_subset_comparisons": ("Xlrlr", True),
          "tableS3_error_vs_distance": ("Xlrlrlr", False), "tableS4_external_clusterings": ("Xrllll", True), "tableS5_curie_label_noise": ("Xl", False),
          "tableS6_design_effect_distance_conformal": ("Xrrrrrr", False), "tableS7_ordering_decomposition": ("Xr", False),
          "tableS8_moment_per_fu": ("Xllrl", True), "tableS11_curie_subgroups": ("Xrrrr", False)}
RAGGED_X = ">{\\raggedright\\arraybackslash}X"


def save(df: pd.DataFrame, name: str, caption: str, notes: str = "") -> None:
    df.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8")
    spec, grouped = LAYOUT.get(name, ("X" + "l" * (len(df.columns) - 1), False))
    shown = list(df.columns[1:]) if grouped else list(df.columns)      # grouped: the first column becomes a heading row per group
    if len(spec) != len(shown):
        raise ValueError(f"{name}: layout {spec!r} does not match {len(shown)} printed columns")
    cols = "@{}" + "".join(RAGGED_X if c == "X" else c for c in spec) + "@{}"
    lines = ["\\begin{table}", f"\\caption{{{tex_escape(caption)}}}", f"\\label{{tab:{name}}}", "\\tablefont",
             "\\begin{tabularx}{\\textwidth}{" + cols + "}", "\\toprule",
             " & ".join("\\textbf{" + tex_escape(str(c)) + "}" for c in shown) + " \\\\", "\\midrule"]
    previous = None
    if grouped:      # keep the rows of one group together, groups in order of first appearance
        order = {g: i for i, g in enumerate(dict.fromkeys(df.iloc[:, 0]))}
        df = df.iloc[sorted(range(len(df)), key=lambda i: order[df.iloc[i, 0]])]
    for row in df.itertuples(index=False):
        cells = [tex_cell(v) for v in row]
        if grouped:
            if cells[0] != previous:
                if previous is not None:
                    lines.append("\\addlinespace")
                lines.append(f"\\multicolumn{{{len(shown)}}}{{@{{}}l@{{}}}}{{\\textit{{{cells[0]}}}}} \\\\")
                previous = cells[0]
            cells = ["\\quad " + cells[1]] + cells[2:]
        lines.append(" & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabularx}"]
    if notes:
        lines += ["\\par\\vspace{4pt}\\raggedright\\noindent " + tex_escape(notes)]
    lines += ["\\end{table}"]
    (OUT / f"{name}.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if notes:
        (OUT / f"{name}.notes.txt").write_text(notes + "\n", encoding="utf-8")


def verdict(v: str) -> str:
    """Short verdict for table cells; 'none' = no stable change (explained in the table notes)."""
    return v if v in ("stable gain", "stable loss", "borderline gain", "borderline loss") else "none"


# --------------------------------------------------------------------------------------------------------- Table 1
def table1_dataset() -> None:
    sp = DATA / "splits" / "v1.4"
    spec = [("Magnetic ordering (FM/AFM/FiM/NM)", "class", "split_ordering.csv", "matched_split_ordering.csv"),
            ("Curie temperature", "K", "split_curie.csv", "matched_split_curie.csv"),
            ("DFT total magnetic moment, per cell (m_cell)", "μB/cell", "split_ms.csv", "matched_split_ms.csv"),
            ("Mass magnetization (secondary)", "emu/g", "split_ms_mass.csv", None),
            ("Volume magnetization (secondary)", "A/m", "split_ms_volume.csv", None),
            ("Anisotropy constant K1 (secondary)", "J/m³", "split_k1.csv", None)]
    rows = []
    for name, unit, f, matched in spec:
        s = pd.read_csv(sp / f, usecols=["reduced_formula", "split", "tier3"])
        m = len(pd.read_csv(sp / matched, usecols=["material_id"])) if matched else None
        rows.append({"Target": name, "Unit": unit, "Records": f"{len(s):,}", "Formulas": f"{s['reduced_formula'].nunique():,}",
                     "Train / validation / test": "/".join(f"{(s['split'] == k).sum():,}" for k in ("train", "validation", "test")),
                     "Matched records": f"{m:,}" if m else "-"})
    o = pd.read_csv(DATA / "analysis_dataset/v1.4/targets/ordering/target_ordering_clean.csv", usecols=["magnetic_ordering_clean", "ordering_valid"], low_memory=False)
    counts = o[o["ordering_valid"].astype(bool)]["magnetic_ordering_clean"].value_counts()
    notes = ("Analysis dataset v1.4 (frozen); formula-grouped 70/15/15 splits. Matched records = materials with complete Tier 3 descriptors, used at "
             "every tier. Ordering classes: " + ", ".join(f"{k} {v:,}" for k, v in counts.items()) +
             ". The DFT moment is the Materials Project/JARVIS total moment of the computed cell at 0 K (not an experimental saturation magnetization); "
             "the moment per formula unit (m_fu = m_cell x atoms per formula unit / atoms in the cell, 10,821 matched rows) is analysed alongside. "
             "Tier 1 = 65 composition descriptors; Tier 2 = Tier 1 + 8 oxidation-state descriptors; Tier 3 = Tier 2 + 24 non-magnetic DFT descriptors (97).")
    save(pd.DataFrame(rows), "table1_dataset", "Prediction targets of the curated analysis dataset", notes)


# --------------------------------------------------------------------------------------------------------- Table 2
def table2_tiers() -> None:
    t = pd.read_csv(RV / "a1_tier_inference.csv")
    rows = []
    for tgt in ("ordering", "curie", "ms_moment"):
        d = 3 if tgt != "curie" else 1
        algs = ["linear", "gradient_boosting", "xgboost"] if tgt == "ordering" else (
            ["linear_clip", "gradient_boosting", "xgboost_seedmean"] if tgt == "curie" else ["linear", "gradient_boosting", "xgboost_seedmean"])
        for alg in algs:
            r = t[(t["target"] == tgt) & (t["algorithm"] == alg)].set_index(["from", "to"])
            a, b = r.loc[("tier1", "tier2")], r.loc[("tier1", "tier3")]
            holm = t[(t["target"] == tgt) & (t["algorithm"] == ("linear" if alg == "linear_clip" else alg)) & (t["from"] == "tier1") & (t["to"] == "tier3")]["holm_p"]
            rows.append({"Target, metric": TARGET[tgt], "Algorithm": ALG[alg], "Tier 1→2": ci(a["mean_improvement"], a["nb_ci_low"], a["nb_ci_high"], d, True),
                         "Tier 1→3": ci(b["mean_improvement"], b["nb_ci_low"], b["nb_ci_high"], d, True), "Verdict (1→3)": verdict(b["verdict"]),
                         "Holm p": f"{holm.iloc[0]:.3f}" if alg != "linear_clip" and len(holm) and pd.notna(holm.iloc[0]) else "-",
                         "Tier 3 beyond site count": "-"})
    fu = pd.read_csv(RV / "a5_moment_per_fu/per_fu_tier_effects.csv").query("subset == 'all'")
    for alg in ("linear", "gradient_boosting", "xgboost"):
        r = fu[fu["algorithm"] == alg].set_index(["from", "to"])
        a, b, c = r.loc[("tier1", "tier2")], r.loc[("tier1", "tier3")], r.loc[("tier2_sitecount", "tier3")]
        rows.append({"Target, metric": "Moment per formula unit, MAE (μB/f.u.)", "Algorithm": ALG[alg],
                     "Tier 1→2": ci(a["mean_improvement"], a["nb_ci_low"], a["nb_ci_high"], 3, True),
                     "Tier 1→3": ci(b["mean_improvement"], b["nb_ci_low"], b["nb_ci_high"], 3, True),
                     "Verdict (1→3)": verdict(b["verdict"]), "Holm p": "-",
                     "Tier 3 beyond site count": ci(c["mean_improvement"], c["nb_ci_low"], c["nb_ci_high"], 3, True)})
    notes = ("Improvement = deeper tier minus Tier 1 performance, positive = better; identical matched rows, splits, grids and metrics at every tier; 10 "
             "prespecified formula-grouped splits. Intervals: Nadeau-Bengio corrected resampled-t 95% (refit-aware). Stable = this interval AND the pooled "
             "formula-bootstrap interval exclude 0 AND at least 7 of 10 splits share the sign; borderline = only one of the two intervals excludes 0; "
             "none = no stable change. Holm p over "
             "the primary family (9 Tier 1->3 contrasts: ordering, Curie, moment per cell x 3 algorithms). XGBoost = mean over 8 thread/seed realizations "
             "(Curie, moment per cell); single realization for ordering and the moment per formula unit. Curie Ridge uses train-fold 1st/99th-percentile "
             "clipping; unclipped Ridge is numerically unstable (-825 K) and is not interpretable. The Curie Ridge member of the Holm family is the "
             "unclipped contrast (adjusted p = 1.000); using the clipped contrast instead gives 0.740 for that contrast and leaves the other eight unchanged. The ordering "
             "gradient-boosting Tier 1->2 change is a borderline loss (the bootstrap interval excludes 0, the refit-aware interval does not). "
             "Moment per formula unit: 10,821 rows; 'beyond site count' "
             "= Tier 3 vs Tier 2 + the number of sites in the DFT cell.")
    save(pd.DataFrame(rows), "table2_physics_descriptors", "Effect of oxidation-state (Tier 2) and DFT (Tier 3) descriptors on matched populations", notes)


# --------------------------------------------------------------------------------------------------------- Table 3 (new)
def table3_magnetic_physics() -> None:
    c = pd.read_csv(RV / "a6_magnetic_physics/curie_physics_contrasts.csv")
    mae = pd.read_csv(RV / "a6_magnetic_physics/curie_variant_mae.csv").set_index("variant")
    names = {"tier1_magstruct": "Tier 1 + magnetic-sublattice geometry (10)", "tier3_magstruct": "Tier 3 + magnetic-sublattice geometry",
             "tier3_magdft": "Tier 3 + DFT magnetic outputs (4)", "tier3_magstruct_magdft": "Tier 3 + geometry + DFT magnetic outputs",
             "tier3_chgnet": "Tier 3 + CHGNet crystal embedding (64)"}
    rows = []
    for v, label in names.items():
        for alg in ("gradient_boosting", "xgboost"):
            vs1 = c[(c["algorithm"] == alg) & (c["from"] == "tier1") & (c["to"] == v)]
            vs3 = c[(c["algorithm"] == alg) & (c["from"] == "tier3") & (c["to"] == v)]
            rows.append({"Descriptor set": label, "Algorithm": ALG[alg], "MAE (K)": f"{mae.loc[v, alg]:.1f}",
                         "vs Tier 1": ci(vs1["mean_improvement"].iloc[0], vs1["nb_ci_low"].iloc[0], vs1["nb_ci_high"].iloc[0], 1, True) if len(vs1) else "-",
                         "Verdict vs Tier 1": verdict(vs1["verdict"].iloc[0]) if len(vs1) else "-",
                         "vs Tier 3": ci(vs3["mean_improvement"].iloc[0], vs3["nb_ci_low"].iloc[0], vs3["nb_ci_high"].iloc[0], 1, True) if len(vs3) else "-",
                         "Verdict vs Tier 3": verdict(vs3["verdict"].iloc[0]) if len(vs3) else "-"})
    notes = (f"Matched Curie population (4,602 records), same 10 splits as Extended Data Table 1; MAE of Tier 1 / Tier 3: gradient boosting {mae.loc['tier1', 'gradient_boosting']:.1f} / "
             f"{mae.loc['tier3', 'gradient_boosting']:.1f} K, XGBoost {mae.loc['tier1', 'xgboost']:.1f} / {mae.loc['tier3', 'xgboost']:.1f} K. Geometry: magnetic-ion site fraction and "
             "density, nearest and mean M-M distance, M-M connectivity, M-X distance and coordination, mean M-X-M angle and the fractions of angles in [150, 180] "
             "and [80, 100] degrees, from the Materials Project structure of the same entry. DFT magnetic outputs (moment per atom, magnetic-site fraction, "
             "magnetization per volume, magnetic flag) are not label leakage for experimental Curie temperatures. CHGNet = frozen 64-d crystal feature of the "
             "pretrained universal potential. Improvement in K, positive = better; Nadeau-Bengio 95% intervals; verdict 'none' = no stable change; "
             "XGBoost single realization.")
    save(pd.DataFrame(rows), "table3_magnetic_physics", "Magnetic and structure-aware physics for the Curie temperature", notes)


# --------------------------------------------------------------------------------------------------------- Table 4/5
def table4_intervals() -> None:
    c = pd.read_csv(RV / "a4_uq/curie_subgroup_coverage.csv")
    m = pd.read_csv(R2 / "repeated_splits/ms_moment/repeated_split_summary.csv")
    rows = []
    methods = [("split_conformal", "Split conformal"), ("normalized_conformal", "Normalized conformal"), ("cqr", "CQR")]
    for meth, name in methods:
        g = c[c["method"] == meth].set_index("group")
        al = g.loc["all"]
        rows.append({"Target": "Curie temperature", "Method": name, "All, mean (SD)": f"{100 * al['mean_coverage']:.1f} ({100 * al['sd_coverage']:.1f})",
                     "Mean width": f"{al['mean_width']:.0f} K", "High predictions": f"top decile {100 * g.loc['top decile of predicted value', 'mean_coverage']:.1f}",
                     "Second subgroup": f"text-mined {100 * g.loc['source: chemdata_curie_neel', 'mean_coverage']:.1f}",
                     "Farthest distance decile": f"{100 * g.loc['farthest distance decile', 'mean_coverage']:.1f}"})
    for meth, name in methods:
        g = m[m["method"] == meth].set_index("group")
        al = g.loc["all"]
        rows.append({"Target": "Moment per cell", "Method": name, "All, mean (SD)": f"{100 * al['mean_coverage']:.1f} ({100 * al['sd_coverage']:.1f})",
                     "Mean width": f"{al['mean_width']:.1f} μB/cell", "High predictions": f"top third {100 * g.loc['predicted_value:highest_third', 'mean_coverage']:.1f}",
                     "Second subgroup": f"oxides {100 * g.loc['family:Oxide', 'mean_coverage']:.1f}", "Farthest distance decile": "-"})
    circ = c[c["group"].str.startswith("hardest sigma")].set_index("method")["mean_coverage"]
    notes = ("Nominal 90%; 10 prespecified formula-grouped splits; calibration on 20% of training formulas; coverage in %. Subgroups are defined without any "
             "method's own difficulty score: top decile of the point prediction (Curie) or highest predicted third (moment), the text-mined label source "
             "(Curie) or oxides (moment), and the farthest decile of composition distance to the proper-training formulas. For comparison, on the decile defined "
             f"by the normalized method's own difficulty scale (a circular definition used in an earlier analysis) coverage is {100 * circ['split_conformal']:.0f}/"
             f"{100 * circ['normalized_conformal']:.0f}/{100 * circ['cqr']:.0f}% for split/normalized/CQR (Curie).")
    save(pd.DataFrame(rows), "table4_regression_intervals", "Coverage of 90% conformal prediction intervals, overall and in subgroups", notes)


def table5_ordering_calibration() -> None:
    s = pd.read_csv(RV / "a4_uq/ordering_calibration_split_summary.csv")
    e = pd.read_csv(RV / "a4_uq/ordering_ece_summary.csv", index_col=0)
    rows = [{"Probabilities / sets": lab, "Top-label ECE": f"{e.loc['mean', a]:.3f}", "Classwise ECE": f"{e.loc['mean', b]:.3f}", "Coverage (%)": "-",
             "FM": "-", "AFM": "-", "FiM": "-", "NM": "-", "Set size": "-"}
            for lab, a, b in [("raw (balanced-weight) probabilities", "top_label_ece_raw", "classwise_ece_raw"),
                              ("prior-corrected", "top_label_ece_prior", "classwise_ece_prior"),
                              ("prior-corrected + temperature", "top_label_ece_prior_temp", "classwise_ece_prior_temp")]]
    for _, r in s[s["calibration"].str.startswith("split")].iterrows():
        rows.append({"Probabilities / sets": f"{r['sets'].capitalize()} sets", "Top-label ECE": "-", "Classwise ECE": "-",
                     "Coverage (%)": f"{100 * r['coverage']:.1f} ({100 * r['sd_coverage']:.1f})",
                     **{k: f"{100 * r[f'coverage_{k}']:.1f}" for k in ("FM", "AFM", "FiM", "NM")}, "Set size": f"{r['set_size']:.2f}"})
    notes = ("Mean over 10 prespecified splits (Tier 1 XGBoost, full ordering population); 15 equal-width bins. Sets at 90% nominal on prior-corrected, "
             "temperature-scaled probabilities, with the temperature fitted on half of the calibration formulas and the conformal thresholds on the other "
             "half (re-using one calibration set gives the same coverage to within 0.3 points). Coverage = mean (SD).")
    save(pd.DataFrame(rows), "table5_ordering_calibration", "Calibration of magnetic-ordering probabilities and prediction sets", notes)


# --------------------------------------------------------------------------------------------------------- Table 6/7/8
EXT = [("all", "All records"), ("composition seen in training repository", "Composition seen in training"),
       ("seen + value not copied", "  seen, value not copied"), ("composition NEVER seen (blind)", "Composition never seen (blind)"),
       ("blind + paper never used (corrected DOI match)", "Blind + source paper never used"), ("blind + seen chemical system", "Blind + seen chemical system"),
       ("blind + unseen chemical system", "Blind + unseen chemical system"), ("blind + paper never used + unseen system", "Blind + never used + unseen system")]


def table6_external() -> None:
    a = pd.read_csv(RV / "a3_external_inference.csv")
    ref = a["train_mean_reference_k"].iloc[0]
    a = a[a["clustering"] == PRE].set_index("subset")
    s = pd.read_csv(R3 / "external_benchmark/subset_metrics_bootstrap.csv")
    s = s[(s["cluster"] == PRE) & s["table"].str.startswith("primary")].set_index("subset")
    rows = [{"Subset": lab, "n (clusters)": f"{int(a.loc[k, 'n']):,} ({int(a.loc[k, 'n_clusters'])})", "MAE, K": ci(a.loc[k, "mae"], a.loc[k, "mae_bca_lo"], a.loc[k, "mae_bca_hi"]),
             "R²": ci(a.loc[k, "r2"], a.loc[k, "r2_bca_lo"], a.loc[k, "r2_bca_hi"], 2),
             "Skill vs training mean": ci(a.loc[k, "skill_vs_train_mean"], a.loc[k, "skill_vs_train_mean_bca_lo"], a.loc[k, "skill_vs_train_mean_bca_hi"], 2),
             "90% coverage": f"{s.loc[k, 'coverage']:.3f}"} for k, lab in EXT]
    notes = ("Primary benchmark after the audit (2,395 of 2,500 records); seen/blind by composition identity. Clusters = source-paper components (records "
             "linked by any shared DOI), the resampling unit; 95% BCa cluster-bootstrap intervals (10,000 resamples). Skill = 1 - MSE / MSE of a constant "
             f"prediction equal to the training mean ({ref:.0f} K), a fixed reference across subsets. Results under first-DOI and chemical-system "
             "clustering are in Supplementary Table 4.")
    save(pd.DataFrame(rows), "table6_external_benchmark", "Independent experimental Curie benchmark by novelty subset", notes)


def table7_generalization() -> None:
    rows = []
    for tgt, label, metric, d in [("ordering", "Ordering", "macro_f1", 3), ("curie", "Curie temperature", "mae", 1), ("ms_moment", "Moment per cell", "mae", 3)]:
        r = pd.read_csv(R3 / "leave_chemical_system_out" / tgt / "leave_chemsys_summary.csv").set_index("metric").loc[metric]
        rows.append({"Test": "Leave chemical system out (10 paired splits)", "Target": label, "Metric": "macro-F1" if metric == "macro_f1" else "MAE",
                     "Familiar → unfamiliar": f"{r['formula_grouped_mean']:.{d}f} → {r['chemsys_grouped_mean']:.{d}f}",
                     "Change [95% CI]": ci(r["mean_delta"], r["ci_low"], r["ci_high"], d, True), "Reference": f"{round(10 * r['fraction_splits_worse'])}/10 splits worse"})
    ag = pd.read_csv(RV / "a2_provenance/label_agreement.csv").iloc[0]
    rows.append({"Test": f"Label agreement, MP vs experimental ({int(ag['n_formulas_both'])} shared formulas)", "Target": "Ordering", "Metric": "agreement / κ",
                 "Familiar → unfamiliar": f"{ag['agreement']:.2f} / {ag['kappa']:.2f}", "Change [95% CI]": f"κ [{ag['kappa_lo']:.2f}, {ag['kappa_hi']:.2f}]",
                 "Reference": "κ = 0: chance agreement"})
    t = pd.read_csv(RV / "a2_provenance/transfer.csv").query("algorithm == 'xgboost' and probabilities == 'raw'").set_index(["train_on", "test_on"])
    null = pd.read_csv(RV / "a2_provenance/transfer_null.csv").groupby(["train_on", "test_on"])["balanced_accuracy"].quantile(0.975)
    for src, dst in (("MP", "experimental"), ("experimental", "MP")):
        r, w = t.loc[(src, dst)], t.loc[(dst, dst)]
        rows.append({"Test": f"Label provenance: train {src} → test {dst} (FM/AFM/FiM)", "Target": "Ordering", "Metric": "balanced accuracy",
                     "Familiar → unfamiliar": f"{w['balanced_accuracy']:.3f} → {r['balanced_accuracy']:.3f}",
                     "Change [95% CI]": ci(r["balanced_accuracy"], r["ba_lo"], r["ba_hi"], 3),
                     "Reference": f"shuffled-label null, 97.5th pct {null.loc[(src, dst)]:.3f}"})
    notes = ("Leave chemical system out: the test sets differ between the two schemes (formula- vs chemical-system-grouped), so the change mixes novelty with "
             "test-set composition. Provenance: NM removed on both sides (the experimental labels contain 5 NM rows); training formulas present in the target "
             "test set removed; 'familiar' = the same model trained and tested within the target provenance; null = 20 refits with permuted training labels; "
             "formula-cluster bootstrap 95% intervals.")
    save(pd.DataFrame(rows), "table7_generalization_internal", "Generalization to unfamiliar chemical systems and to another label provenance", notes)


def table8_screening() -> None:
    rc = pd.read_csv(RV / "a9_screening/risk_coverage.csv")
    th = pd.read_csv(RV / "a9_screening/threshold_task.csv").set_index("quantity")
    rows = [{"Use": f"Abstain on {r['abstain_on']}, keep {int(100 * r['retained_fraction'])}%", "n (papers)": f"{r['n']} ({r['n_papers']})",
             "Result": f"MAE {ci(r['mae_k'], r['mae_lo'], r['mae_hi'], 0)} K; coverage {ci(r['coverage'], r['coverage_lo'], r['coverage_hi'], 2)}"}
            for _, r in rc[rc["retained_fraction"].isin([1.0, 0.5])].iterrows() if not (r["abstain_on"] == "interval width" and r["retained_fraction"] == 1.0)]
    for q, lab in [("point accuracy", "Tc > 300 K from the point prediction: accuracy"), ("point recall", "  recall"), ("point precision", "  precision"),
                   ("interval decision rate", "Decide only when the 90% interval excludes 300 K: share decided"),
                   ("accuracy of interval decisions", "  accuracy of those decisions")]:
        rows.append({"Use": lab, "n (papers)": "465 (81)", "Result": ci(th.loc[q, "value"], th.loc[q, "lo"], th.loc[q, "hi"], 3)})
    notes = (f"The 465 truly blind external records; base rate of Tc > 300 K = {th.loc['base rate Tc > 300 K', 'value']:.2f}. Paper-cluster bootstrap 95% intervals "
             "(10,000 resamples). Distance = composition (total-variation) distance to the nearest training formula; width = width of the normalized-conformal interval.")
    save(pd.DataFrame(rows), "table8_screening", "What the predictions support in a screening setting (blind external compositions)", notes)


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
    a = pd.read_csv(RV / "a3_external_inference.csv")
    keep = a["subset"].isin(["composition NEVER seen (blind)", "blind + seen chemical system", "blind + unseen chemical system"])
    save(pd.DataFrame([{"Subset": r["subset"].replace("composition NEVER seen (blind)", "blind"),
                        "Clustering": r["clustering"].split(" (")[0] + (" (first DOI)" if "first" in r["clustering"] else ""),
                        "n (clusters)": f"{r['n']} ({r['n_clusters']})", "R², percentile": ci(r["r2"], r["r2_pct_lo"], r["r2_pct_hi"], 2),
                        "R², BCa": ci(r["r2"], r["r2_bca_lo"], r["r2_bca_hi"], 2),
                        "Skill vs training mean, BCa": ci(r["skill_vs_train_mean"], r["skill_vs_train_mean_bca_lo"], r["skill_vs_train_mean_bca_hi"], 2),
                        "Upper limit <= 0.2?": "yes (R² or skill)" if min(r["r2_pct_hi"], r["r2_bca_hi"], r["skill_vs_train_mean_bca_hi"]) <= 0.2 else "no"}
                       for _, r in a[keep].iterrows()]),
         "tableS4_external_clusterings", "External benchmark under three resampling units and two interval types")
    rates = pd.read_csv(RV / "a7_curie_label_noise/title_audit_rates.csv")
    spread = pd.read_csv(RV / "a7_curie_label_noise/within_formula_spread.csv").iloc[0]
    rows = [{"Quantity": r["category"], "Value": f"{r['count']}/{r['n']} = {100 * r['rate']:.1f}% [{100 * r['wilson_lo']:.1f}, {100 * r['wilson_hi']:.1f}]"}
            for _, r in rates.iterrows()]
    rows += [{"Quantity": "formulas with >= 2 retained records", "Value": f"{int(spread['n_formulas']):,} ({100 * spread['share_of_records']:.0f}% of records)"},
             {"Quantity": "median within-formula SD of Tc", "Value": f"{spread['median_sd_k']:.1f} K"},
             {"Quantity": "share of those formulas with SD > 50 K / > 100 K", "Value": f"{100 * spread['share_sd_gt_50k']:.0f}% / {100 * spread['share_sd_gt_100k']:.0f}%"}]
    save(pd.DataFrame(rows), "tableS5_curie_label_noise", "Residual label noise in the curated Curie target",
         "Title-based screen, not a full-text audit: stratified random sample of 200 retained records (source x Tc tercile, seed 20261110), each "
         "classified by the AI assistant from the Crossref title, the compound and the plausibility of the value; Wilson 95% intervals. Per-record "
         "labels for checking: results/revision/a7_curie_label_noise/title_audit_adjudicated.csv.")
    de = pd.read_csv(RV / "a4_uq/curie_design_effect.csv")
    da = pd.read_csv(RV / "a4_uq/curie_distance_aware_marginal.csv").set_index("variant")
    dd = pd.read_csv(RV / "a4_uq/curie_distance_aware_by_decile.csv")
    method_label = {"split_conformal": "Split conformal", "normalized_conformal": "Normalized conformal", "cqr": "CQR"}
    rows = [{"Method / variant": method_label.get(r["method"], r["method"].replace("_", " ")), "Design effect": f"{r['design_effect']:.1f}",
             "Effective size": f"{r['effective_calibration_size']:.0f}",
             "Implied SD": f"{100 * r['sd_implied_iid_rows']:.1f} / {100 * r['sd_implied_effective']:.1f}",
             "Observed SD": f"{100 * r['observed_sd_marginal_coverage']:.1f}", "Mean coverage": "-", "Farthest decile": "-"} for _, r in de.iterrows()]
    variant_label = {"normalized (plain)": "Normalized, plain", "Mondrian by distance quartile": "Normalized, calibrated per distance quartile",
                     "weighted (covariate shift)": "Normalized, weighted for covariate shift"}
    for v, label in variant_label.items():
        far = dd[(dd["variant"] == v) & (dd["distance_decile"] == 10)].iloc[0]
        rows.append({"Method / variant": label, "Design effect": "-", "Effective size": "-", "Implied SD": "-",
                     "Observed SD": f"{100 * da.loc[v, 'sd']:.1f}", "Mean coverage": f"{100 * da.loc[v, 'coverage']:.1f}",
                     "Farthest decile": f"{100 * far['coverage']:.1f}"})
    save(pd.DataFrame(rows), "tableS6_design_effect_distance_conformal", "Why Curie interval coverage varies between splits, and distance-aware conformal variants",
         "Design effect from the within-formula intraclass correlation of the calibration exceedance indicator. Effective size = effective number of "
         "independent calibration units. Implied SD of training-conditional coverage: for exchangeable rows / for the effective size. Observed SD across "
         "10 splits. SD and coverage in percentage points; farthest decile = coverage in the farthest decile of composition distance.")
    d = pd.read_csv(RV / "a4_uq/ordering_decomposition_10splits.csv").mean(numeric_only=True).drop(labels=["split"], errors="ignore")

    def quantity(k: str) -> str:
        subset = " (compounds with a magnetism-capable element)" if k.endswith("_magel") or k.endswith("_magnetic_element") else ""
        k = k.replace("_magel", "").replace("_magnetic_element", "").replace("_all", "")
        for a, b in [("macro_f1_FM_AFM_FiM", "Macro-F1 over FM, AFM and FiM"), ("macro_f1", "Macro-F1"), ("recall_", "Recall, "),
                     ("share_test_with_mag_element", "Share of test rows with a magnetism-capable element"),
                     ("share_NM_with_mag_element", "Share of non-magnetic rows with a magnetism-capable element")]:
            k = k.replace(a, b)
        return k.replace("_", " ") + subset

    save(pd.DataFrame([{"Quantity": quantity(k), "Mean over 10 splits": f"{v:.3f}"} for k, v in d.items()]),
         "tableS7_ordering_decomposition", "Magnetic-ordering performance with and without compounds lacking a magnetism-capable element",
         "Tier 1 XGBoost on the full ordering population, 10 prespecified splits; magnetism-capable element = curation rule C1 list.")
    fu = pd.read_csv(RV / "a5_moment_per_fu/per_fu_tier_effects.csv")
    lab = {"tier1": "Tier 1", "tier2": "Tier 2", "tier3": "Tier 3", "tier2_sitecount": "Tier 2 + site count"}
    rows = [{"Target / subset": f"per formula unit, {r['subset']}", "Algorithm": ALG[r["algorithm"]], "Contrast": f"{lab[r['from']]} → {lab[r['to']]}",
             "Improvement": ci(r["mean_improvement"], r["nb_ci_low"], r["nb_ci_high"], 3, True) + " μB/f.u.", "Splits better": f"{int(r['n_positive'])}/10",
             "Verdict": verdict(r["verdict"])} for _, r in fu.iterrows()]
    pa = pd.read_csv(R1 / "ms_per_atom/peratom_corrected_tier_effect.csv").query("target == 'per_atom' and population == 'corrected'")
    rows += [{"Target / subset": "per atom (moment / sites), all rows", "Algorithm": ALG[r["algorithm"]], "Contrast": "Tier 1 → Tier 3",
              "Improvement": ci(100 * r["mean_relative_mae_gain"], 100 * r["ci_low"], 100 * r["ci_high"], 1, True) + " % of MAE",
              "Splits better": f"{round(10 * r['fraction_splits_positive'])}/10", "Verdict": "stable gain" if r["stable_gain"] else "no stable change"}
             for _, r in pa.iterrows()]
    save(pd.DataFrame(rows), "tableS8_moment_per_fu", "Tier effects for the DFT moment per formula unit and per atom",
         "Per formula unit: Nadeau-Bengio 95% intervals, all rows and non-zero moments only. Per atom (same 10,821 rows and splits, earlier "
         "analysis with the corrected same-calculation atom count): relative MAE gain with a descriptive across-split t interval.")
    sg = pd.read_csv(RV / "a4_uq/curie_subgroup_coverage.csv")
    sg = sg[~sg["group"].str.contains("Tier1-descriptor|Computational|Experimental", regex=True)]
    wide = sg.pivot_table(index="group", columns="method", values="mean_coverage")
    n = sg.groupby("group")["median_formulas"].first()
    pretty = {"all": "All test materials", "farthest distance decile": "Farthest distance decile", "top decile of predicted value": "Top decile of predicted value",
              "source: chemdata_curie_neel": "Source: text-mined database", "source: magnetic_anisotropy_materials": "Source: curated compilation (anisotropy)",
              "source: magnetic_materials_reformatted": "Source: curated compilation (magnetic materials)"}

    def subgroup(g: str) -> str:
        g = pretty.get(g, g.replace("group: ", "Family: ").replace(" (circular, first submission)", " (defined by the normalized method itself)"))
        return g[0].upper() + g[1:]

    save(pd.DataFrame([{"Subgroup": subgroup(g),
                        "Median formulas": f"{int(n[g]):,}", "Split": f"{100 * wide.loc[g, 'split_conformal']:.1f}",
                        "Normalized": f"{100 * wide.loc[g, 'normalized_conformal']:.1f}", "CQR": f"{100 * wide.loc[g, 'cqr']:.1f}"} for g in wide.index]),
         "tableS11_curie_subgroups", "Coverage (%) of 90% Curie-temperature intervals in every subgroup evaluated",
         "Mean over 10 prespecified splits. Constant-width methods over-cover several families (rare earth, actinide, intermetallic) because their "
         "intervals are wide everywhere; normalized conformal stays within about 2 points of nominal except for text-mined labels and physics-complete materials.")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*"):
        old.unlink()
    for f in (table1_dataset, table2_tiers, table3_magnetic_physics, table4_intervals, table5_ordering_calibration, table6_external,
              table7_generalization, table8_screening, tables_supplementary):
        f()
    print("tables written:", ", ".join(sorted(p.stem for p in OUT.glob("*.csv"))))


if __name__ == "__main__":
    main()
