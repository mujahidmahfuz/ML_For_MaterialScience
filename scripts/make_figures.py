"""Build every paper figure from results/ (no model is fit). Each figure is written as vector PDF (for LaTeX) and 300-dpi PNG.
Usage (package root):  python scripts/make_figures.py
Figures: fig1 physics descriptors (RQ1), fig2 uncertainty calibration (RQ2), fig3 external benchmark subsets (RQ3),
fig4 error vs chemical distance (RQ3), figS1 blind-record scatter.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

PKG = Path(__file__).resolve().parents[1]
RES, OUT = PKG / "results", PKG / "figures"
R1, R2, R3 = RES / "rq1_physics_descriptors", RES / "rq2_uncertainty", RES / "rq3_generalization"
BLUE, ORANGE, INK, INK2, GRID, SURFACE = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
ALG = [("linear", "Ridge / logistic"), ("gradient_boosting", "Gradient boosting"), ("xgboost", "XGBoost")]
PRE = "paper (pre-specified: shared-DOI components)"
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold", "font.family": "DejaVu Sans"})


def style(ax: plt.Axes, grid_axis: str = "x") -> None:
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8.5)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(OUT / f"{name}.pdf", facecolor=SURFACE, metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(OUT / f"{name}.png", dpi=300, facecolor=SURFACE, metadata={"Software": None})
    plt.close(fig)


def errbar(ax: plt.Axes, x: float, y: float, lo: float, hi: float, color: str, label: str | None = None, horizontal: bool = True) -> None:
    kw = dict(fmt="o", ms=5.5, color=color, ecolor=color, elinewidth=2, capsize=0, markeredgecolor=SURFACE, markeredgewidth=1.2, label=label)
    if horizontal:
        ax.errorbar(x, y, xerr=[[x - lo], [hi - x]], **kw)
    else:
        ax.errorbar(x, y, yerr=[[y - lo], [hi - y]], **kw)


# --------------------------------------------------------------------------------------------------------- Figure 1
def fig1_physics() -> None:
    o = pd.read_csv(R1 / "matched_tiers/ordering_10split_robustness.csv").query("metric == 'macro_f1'")
    c = pd.read_csv(R1 / "matched_tiers/curie_inference_table.csv").query("analysis == 'primary_matched' and metric == 'mae'")
    m = pd.read_csv(R1 / "matched_tiers/robustness_summary_curie_ms_v1.2.csv").query("target == 'ms_moment' and analysis == 'primary_matched' and metric == 'mae'")
    a = pd.read_csv(R1 / "ms_per_atom/peratom_corrected_tier_effect.csv").query("target == 'per_atom' and population == 'corrected'")
    panels = [("a  Magnetic ordering", "Change in macro-F1", o, ("pooled_concat_improvement", "pooled_concat_ci_low", "pooled_concat_ci_high"), (-0.09, 0.07)),
              ("b  Curie temperature", "Reduction in MAE (K)", c, ("improvement", "ci95_low", "ci95_high"), (-45, 25)),
              ("c  Ms per unit cell", "Reduction in MAE (μB/cell)", m, ("pooled_concat_improvement", "pooled_concat_ci_low", "pooled_concat_ci_high"), (-0.04, 0.13))]
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.4), sharey=True)
    y = np.arange(len(ALG))[::-1]
    for ax, (title, xlabel, d, (e, lo, hi), xlim) in zip(axes, panels):
        style(ax)
        ax.axvline(0, color=INK2, lw=1, ls="--")
        for i, (alg, _) in enumerate(ALG):
            r = d[d["algorithm"] == alg].set_index(["from_variant", "to_variant"])
            for (fv, tv), off, color, lab in [(("tier1", "tier2"), 0.14, BLUE, "Tier 1 → Tier 2"), (("tier1", "tier3"), -0.14, ORANGE, "Tier 1 → Tier 3")]:
                row = r.loc[(fv, tv)]
                v, l, h = row[e], row[lo], row[hi]
                if l < xlim[0]:   # numerically unstable fit far off scale: mark at the edge, keep the value in the label
                    ax.annotate(f"{v:.0f} (unstable fit)", xy=(xlim[0], y[i] + off), xytext=(xlim[0] + 0.05 * (xlim[1] - xlim[0]), y[i] + off),
                                va="center", fontsize=7.5, color=color, arrowprops=dict(arrowstyle="<-", color=color, lw=1.5))
                    continue
                errbar(ax, v, y[i] + off, l, h, color, lab if i == 0 else None)
        ax.set_xlim(*xlim)
        ax.set_title(title, loc="left")
        ax.set_xlabel(xlabel, color=INK2)
    ax = axes[3]
    style(ax)
    ax.axvline(0, color=INK2, lw=1, ls="--")
    for i, (alg, _) in enumerate(ALG):
        r = a[a["algorithm"] == alg].iloc[0]
        errbar(ax, 100 * r["mean_relative_mae_gain"], y[i] - 0.14, 100 * r["ci_low"], 100 * r["ci_high"], ORANGE)
    ax.set_xlim(-2, 8)
    ax.set_title("d  Ms per atom", loc="left")
    ax.set_xlabel("Relative MAE reduction (%)", color=INK2)
    axes[0].set_yticks(y, [lab for _, lab in ALG])
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, loc="upper right", ncol=2, fontsize=8.5)
    fig.text(0.01, 0.01, "Positive = better. Matched populations, 10 repeated formula-grouped splits, 95% intervals.", fontsize=7.5, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig1_physics_descriptors")


# --------------------------------------------------------------------------------------------------------- Figure 2
def fig2_uncertainty() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
    methods = [("split_conformal", "Split"), ("normalized_conformal", "Normalized"), ("cqr", "CQR")]
    for ax, (tgt, title) in zip(axes[:2], [("curie", "a  Curie temperature intervals"), ("ms_moment", "b  Ms per-cell intervals")]):
        style(ax, "y")
        ax.grid(axis="x", visible=False)
        rp = pd.read_csv(R2 / "repeated_splits" / tgt / "repeated_split_summary.csv")
        x = np.arange(len(methods))
        for off, group, color, lab in [(-0.13, "all", BLUE, "All test rows"), (0.13, "difficulty_decile:10", ORANGE, "Hardest decile")]:
            for i, (meth, _) in enumerate(methods):
                r = rp[(rp["method"] == meth) & (rp["group"] == group)].iloc[0]
                errbar(ax, x[i] + off, 100 * r["mean_coverage"], 100 * r["min_coverage"], 100 * r["max_coverage"], color, lab if i == 0 else None, horizontal=False)
        ax.axhline(90, color=INK2, lw=1, ls="--")
        ax.set_xticks(x, [mm for _, mm in methods])
        ax.set_ylim(20, 102)
        ax.set_ylabel("Coverage (%)", color=INK2)
        ax.set_title(title, loc="left")
    axes[0].legend(frameon=False, fontsize=8, loc="lower left")
    axes[0].text(2.45, 91, "nominal 90%", fontsize=7.5, color=INK2, ha="right", va="bottom")
    ax = axes[2]
    style(ax, "y")
    ax.grid(axis="x", visible=False)
    sets = pd.read_csv(R2 / "ordering/uq_conformal_sets.csv").query("probabilities == 'prior-corrected + temperature'").set_index("method")
    classes = ["FM", "NM", "AFM", "FiM"]
    x = np.arange(len(classes))
    for off, meth, color, lab in [(-0.13, "marginal_LAC", BLUE, "Marginal sets"), (0.13, "class_conditional", ORANGE, "Class-conditional sets")]:
        ax.scatter(x + off, [100 * sets.loc[meth, f"coverage_{k}"] for k in classes], s=42, color=color, edgecolor=SURFACE, linewidth=1.2, label=lab, zorder=3)
    ax.axhline(90, color=INK2, lw=1, ls="--")
    ax.set_xticks(x, classes)
    ax.set_ylim(20, 102)
    ax.set_ylabel("Set coverage (%)", color=INK2)
    ax.set_title("c  Ordering prediction sets, per class", loc="left")
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    fig.text(0.01, 0.01, "a, b: mean over 10 repeated splits, bars = range across splits. c: frozen test split (N = 11,902). Nominal 90%.", fontsize=7.5, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    save(fig, "fig2_uncertainty_calibration")


# --------------------------------------------------------------------------------------------------------- Figure 3/4
SUBSETS = [("all", "All records"), ("composition seen in training repository", "Composition seen in training"),
           ("composition NEVER seen (blind)", "Composition never seen (blind)"), ("blind + paper never used (corrected DOI match)", "Blind + paper never used"),
           ("blind + seen chemical system", "Blind + seen chemical system"), ("blind + unseen chemical system", "Blind + unseen chemical system"),
           ("blind + paper never used + unseen system", "Blind + never used + unseen system")]


def fig3_external() -> None:
    st = pd.read_csv(R3 / "external_benchmark/subset_metrics_bootstrap.csv")
    st = st[st["cluster"] == PRE]
    tables = [("original (all 2,500 records)", "Original table", BLUE, -0.17), ("primary benchmark (A1/A2/A4/A5 removed)", "After audit (primary)", ORANGE, 0.17)]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
    y = np.arange(len(SUBSETS))[::-1]
    keys = [k for k, _ in SUBSETS]
    for ax, metric, title in [(axes[0], "mae_k", "a  Mean absolute error (K)"), (axes[1], "r2", "b  R²")]:
        style(ax)
        for tname, tlabel, color, off in tables:
            d = st[st["table"] == tname].set_index("subset").loc[keys]
            lo = np.maximum(d[f"{metric}_lo"], -1.5) if metric == "r2" else d[f"{metric}_lo"]
            ax.errorbar(d[metric], y + off, xerr=[d[metric] - lo, d[f"{metric}_hi"] - d[metric]], fmt="o", ms=5.5, color=color, ecolor=color, elinewidth=2,
                        capsize=0, label=tlabel, markeredgecolor=SURFACE, markeredgewidth=1.2)
        if metric == "r2":
            ax.axvline(0, color=INK2, lw=1, ls="--")
            ax.set_xlim(-1.5, 1.0)
        ax.set_title(title, loc="left")
    n = st[st["table"] == tables[1][0]].set_index("subset")["n"]
    axes[0].set_yticks(y, [f"{lab} (n={int(n[k]):,})" for k, lab in SUBSETS])
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, loc="upper right", ncol=2, fontsize=8.5)
    fig.text(0.01, 0.01, "95% intervals: cluster bootstrap over source papers (10,000 resamples). n = primary benchmark. R² lower limits below -1.5 cut off.",
             fontsize=7.5, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    save(fig, "fig3_external_benchmark")


def fig4_distance() -> None:
    b = pd.read_csv(R3 / "external_benchmark/similarity_bins.csv")
    order = ["0: formula used in training", "Q1 (closest)", "Q2", "Q3", "Q4 (farthest)"]
    labels = ["0\n(exact)", "Q1", "Q2", "Q3", "Q4\n(farthest)"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    x = np.arange(len(order))
    for ax, metric, title, scale in [(axes[0], "mae_k", "a  Mean absolute error (K)", 1), (axes[1], "mean_width_k", "b  Mean 90% interval width (K)", 1),
                                     (axes[2], "coverage", "c  90% interval coverage (%)", 100)]:
        style(ax, "y")
        ax.grid(axis="x", visible=False)
        for sname, lab, color, off in [("primary", "All primary records", BLUE, -0.1), ("primary, blind only", "Truly blind records", ORANGE, 0.1)]:
            d = b[b["set"] == sname].set_index("bin").reindex(order)
            ok = d[metric].notna().to_numpy()
            ax.errorbar((x + off)[ok], scale * d[metric][ok], yerr=[scale * (d[metric] - d[f"{metric}_lo"])[ok], scale * (d[f"{metric}_hi"] - d[metric])[ok]],
                        fmt="o-", ms=5.5, lw=1.8, color=color, elinewidth=2, capsize=0, label=lab, markeredgecolor=SURFACE, markeredgewidth=1.2)
        if metric == "coverage":
            ax.axhline(90, color=INK2, lw=1, ls="--")
        ax.set_xticks(x, labels)
        ax.set_title(title, loc="left")
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.supxlabel("Composition distance to the nearest training formula (bin 0 = identical composition; Q1-Q4 = quartiles of non-zero distances)",
                  fontsize=8.5, color=INK2)
    fig.tight_layout()
    save(fig, "fig4_error_vs_distance")


def figS1_scatter() -> None:
    d = pd.read_csv(R3 / "external_benchmark/similarity_records.csv", keep_default_na=False, na_values=[""])
    d = d[~d["excluded_primary"] & ~d["a7a_formula_in_repository"]]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    style(ax, "y")
    for mask, lab, color, front in [(d["a7_system_seen"], "Seen chemical system", BLUE, False), (~d["a7_system_seen"], "Unseen chemical system", ORANGE, True)]:
        ax.scatter(d.loc[mask, "d_comp_train"], d.loc[mask, "abs_err_k"], s=24 if front else 13, color=color, alpha=0.9 if front else 0.45,
                   edgecolor=SURFACE, linewidth=0.5, label=f"{lab} (n={int(mask.sum())})", zorder=3 if front else 2)
    ax.set_xscale("log")
    ax.set_xlabel("Composition distance to the nearest training formula (log scale)", color=INK2)
    ax.set_ylabel("Absolute error (K)", color=INK2)
    ax.set_title("Truly blind external records: error against chemical distance", loc="left")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout()
    save(fig, "figS1_blind_scatter")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for f in (fig1_physics, fig2_uncertainty, fig3_external, fig4_distance, figS1_scatter):
        f()
    print("figures written:", ", ".join(sorted(p.name for p in OUT.glob("*.pdf"))))


if __name__ == "__main__":
    main()
