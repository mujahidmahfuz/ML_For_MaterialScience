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
# Nature figure style: 180 mm double-column width, Arial 5-7 pt at final size, editable text in the PDF, notes in the legend not the figure.
WIDTH_IN = 180 / 25.4
TOP_RECT = (0, 0, 1, 0.93)      # leaves room for the legend above the panels
plt.rcParams.update({"font.family": "Arial", "font.size": 7, "axes.titlesize": 7, "axes.titleweight": "bold", "axes.labelsize": 7,
                     "legend.fontsize": 6, "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
                     "xtick.major.size": 2.5, "ytick.major.size": 2.5, "pdf.fonttype": 42, "ps.fonttype": 42})


def style(ax: plt.Axes, grid_axis: str = "x") -> None:
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=6)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(OUT / f"{name}.pdf", facecolor=SURFACE, metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(OUT / f"{name}.png", dpi=300, facecolor=SURFACE, metadata={"Software": None})
    plt.close(fig)


def top_legend(ax: plt.Axes, handles: list | None = None, labels: list | None = None, ncol: int = 2) -> None:
    """One legend position for every figure: above the panel, right-aligned, so that it never covers data."""
    args = (handles, labels) if handles is not None else ()
    legend = ax.legend(*args, frameon=False, fontsize=6, loc="lower right", bbox_to_anchor=(1.0, 1.13), ncol=ncol, borderaxespad=0,
                       handletextpad=0.4, columnspacing=1.4)
    legend.set_in_layout(False)      # the layout reserves the strip above the panels instead (TOP_RECT)


def errbar(ax: plt.Axes, x: float, y: float, lo: float, hi: float, color: str, label: str | None = None, horizontal: bool = True) -> None:
    kw = dict(fmt="o", ms=3.8, color=color, ecolor=color, elinewidth=1.2, capsize=0, markeredgecolor=SURFACE, markeredgewidth=0.6, label=label)
    if horizontal:
        ax.errorbar(x, y, xerr=[[x - lo], [hi - x]], **kw)
    else:
        ax.errorbar(x, y, yerr=[[y - lo], [hi - y]], **kw)


# --------------------------------------------------------------------------------------------------------- Figure 1
def fig1_physics() -> None:
    t = pd.read_csv(RES / "revision/a1_tier_inference.csv")
    fu = pd.read_csv(RES / "revision/a5_moment_per_fu/per_fu_tier_effects.csv").query("subset == 'all'")
    alg_map = {"ordering": {"linear": "linear", "gradient_boosting": "gradient_boosting", "xgboost": "xgboost"},
               "curie": {"linear": "linear_clip", "gradient_boosting": "gradient_boosting", "xgboost": "xgboost_seedmean"},
               "ms_moment": {"linear": "linear", "gradient_boosting": "gradient_boosting", "xgboost": "xgboost_seedmean"}}
    panels = [("a  Magnetic ordering", "Change in macro-F1", "ordering", (-0.11, 0.08)),
              ("b  Curie temperature", "Reduction in MAE (K)", "curie", (-55, 40)),
              ("c  Moment per cell", "Reduction in MAE (μB/cell)", "ms_moment", (-0.03, 0.14)),
              ("d  Moment per formula unit", "Reduction in MAE (μB/f.u.)", "per_fu", (-0.03, 0.08))]
    fig, axes = plt.subplots(1, 4, figsize=(WIDTH_IN, 2.4), sharey=True)
    y = np.arange(len(ALG))[::-1]
    for ax, (title, xlabel, tgt, xlim) in zip(axes, panels):
        style(ax)
        ax.axvline(0, color=INK2, lw=0.7, ls="--")
        for i, (alg, _) in enumerate(ALG):
            d = fu[fu["algorithm"] == alg] if tgt == "per_fu" else t[(t["target"] == tgt) & (t["algorithm"] == alg_map[tgt][alg])]
            r = d.set_index(["from", "to"])
            pairs = [(("tier1", "tier2"), 0.18, BLUE, "Tier 1 → Tier 2"), (("tier1", "tier3"), 0.0, ORANGE, "Tier 1 → Tier 3")]
            if tgt == "per_fu":
                pairs.append((("tier2_sitecount", "tier3"), -0.18, INK2, "Tier 3 beyond site count"))
            for (fv, tv), off, color, lab in pairs:
                row = r.loc[(fv, tv)]
                errbar(ax, row["mean_improvement"], y[i] + off, row["nb_ci_low"], row["nb_ci_high"], color, lab if i == 0 else None)
        ax.set_xlim(*xlim)
        ax.set_title(title, loc="left")
        ax.set_xlabel(xlabel, color=INK2)
    axes[0].set_yticks(y, [lab for _, lab in ALG])
    handles, labels = [], []
    for ax in axes:
        for hh, ll in zip(*ax.get_legend_handles_labels()):
            if ll not in labels:
                handles.append(hh)
                labels.append(ll)
    top_legend(axes[-1], handles, labels, ncol=3)
    fig.tight_layout(rect=TOP_RECT)
    save(fig, "fig1_physics_descriptors")


# --------------------------------------------------------------------------------------------------------- Figure 2
def fig2_uncertainty() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(WIDTH_IN, 2.4))
    methods = [("split_conformal", "Split"), ("normalized_conformal", "Normalized"), ("cqr", "CQR")]
    sources = {"curie": (pd.read_csv(RES / "revision/a4_uq/curie_subgroup_coverage.csv"), "top decile of predicted value", "Highest predictions"),
               "ms_moment": (pd.read_csv(R2 / "repeated_splits/ms_moment/repeated_split_summary.csv"), "predicted_value:highest_third", "Highest predictions")}
    for ax, (tgt, title) in zip(axes[:2], [("curie", "a  Curie temperature"), ("ms_moment", "b  Moment per cell")]):
        style(ax, "y")
        ax.grid(axis="x", visible=False)
        rp, hi_group, hi_label = sources[tgt]
        x = np.arange(len(methods))
        for off, group, color, lab in [(-0.13, "all", BLUE, "All test materials"), (0.13, hi_group, ORANGE, hi_label)]:
            for i, (meth, _) in enumerate(methods):
                r = rp[(rp["method"] == meth) & (rp["group"] == group)].iloc[0]
                errbar(ax, x[i] + off, 100 * r["mean_coverage"], 100 * (r["mean_coverage"] - r["sd_coverage"]), 100 * (r["mean_coverage"] + r["sd_coverage"]),
                       color, lab if i == 0 else None, horizontal=False)
        ax.axhline(90, color=INK2, lw=0.7, ls="--")
        ax.set_xticks(x, [mm for _, mm in methods])
        ax.set_ylim(20, 102)
        ax.set_ylabel("Coverage (%)", color=INK2)
        ax.set_title(title, loc="left")
    top_legend(axes[1])
    ax = axes[2]
    style(ax, "y")
    ax.grid(axis="x", visible=False)
    sets = pd.read_csv(RES / "revision/a4_uq/ordering_calibration_split_summary.csv")
    sets = sets[sets["calibration"].str.startswith("split")].set_index("sets")
    classes = ["FM", "NM", "AFM", "FiM"]
    x = np.arange(len(classes))
    for off, meth, color, lab in [(-0.13, "marginal", BLUE, "Marginal sets"), (0.13, "class-conditional", ORANGE, "Class-conditional sets")]:
        ax.scatter(x + off, [100 * sets.loc[meth, f"coverage_{k}"] for k in classes], s=18, color=color, edgecolor=SURFACE, linewidth=0.6, label=lab, zorder=3)
    ax.axhline(90, color=INK2, lw=0.7, ls="--")
    ax.set_xticks(x, classes)
    ax.set_ylim(20, 102)
    ax.set_ylabel("Coverage (%)", color=INK2)
    ax.set_title("c  Ordering sets", loc="left")
    top_legend(ax)
    fig.tight_layout(rect=TOP_RECT)
    save(fig, "fig2_uncertainty_calibration")


# --------------------------------------------------------------------------------------------------------- Figure 3/4
SUBSETS = [("all", "All records"), ("composition seen in training repository", "Composition seen in training"),
           ("composition NEVER seen (blind)", "Composition never seen (blind)"), ("blind + paper never used (corrected DOI match)", "Blind + paper never used"),
           ("blind + seen chemical system", "Blind + seen chemical system"), ("blind + unseen chemical system", "Blind + unseen chemical system"),
           ("blind + paper never used + unseen system", "Blind + never used + unseen system")]


def fig3_external() -> None:
    st = pd.read_csv(R3 / "external_benchmark/subset_metrics_bootstrap.csv")
    st = st[st["cluster"] == PRE]
    tables = [("original (all 2,500 records)", "Before audit", BLUE, -0.17), ("primary benchmark (A1/A2/A4/A5 removed)", "After audit", ORANGE, 0.17)]
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH_IN, 2.9), sharey=True)
    y = np.arange(len(SUBSETS))[::-1]
    keys = [k for k, _ in SUBSETS]
    for ax, metric, title, xlabel in [(axes[0], "mae_k", "a  Error", "MAE (K)"), (axes[1], "r2", "b  Variance explained", "R²")]:
        style(ax)
        ax.set_xlabel(xlabel, color=INK2)
        for tname, tlabel, color, off in tables:
            d = st[st["table"] == tname].set_index("subset").loc[keys]
            lo = np.maximum(d[f"{metric}_lo"], -1.5) if metric == "r2" else d[f"{metric}_lo"]
            ax.errorbar(d[metric], y + off, xerr=[d[metric] - lo, d[f"{metric}_hi"] - d[metric]], fmt="o", ms=3.8, color=color, ecolor=color, elinewidth=1.2,
                        capsize=0, label=tlabel, markeredgecolor=SURFACE, markeredgewidth=0.6)
        if metric == "r2":
            ax.axvline(0, color=INK2, lw=0.7, ls="--")
            ax.set_xlim(-1.5, 1.0)
        ax.set_title(title, loc="left")
    n = st[st["table"] == tables[1][0]].set_index("subset")["n"]
    axes[0].set_yticks(y, [f"{lab} (n={int(n[k]):,})" for k, lab in SUBSETS])
    top_legend(axes[1])
    fig.tight_layout(rect=TOP_RECT)
    save(fig, "fig3_external_benchmark")


def fig4_distance() -> None:
    b = pd.read_csv(R3 / "external_benchmark/similarity_bins.csv")
    order = ["0: formula used in training", "Q1 (closest)", "Q2", "Q3", "Q4 (farthest)"]
    labels = ["0\n(exact)", "Q1", "Q2", "Q3", "Q4\n(farthest)"]
    fig, axes = plt.subplots(1, 3, figsize=(WIDTH_IN, 2.4))
    x = np.arange(len(order))
    for ax, metric, title, ylabel, scale in [(axes[0], "mae_k", "a  Error", "MAE (K)", 1),
                                             (axes[1], "mean_width_k", "b  Interval width", "Mean width of 90% interval (K)", 1),
                                             (axes[2], "coverage", "c  Interval coverage", "Coverage (%)", 100)]:
        style(ax, "y")
        ax.set_ylabel(ylabel, color=INK2)
        ax.grid(axis="x", visible=False)
        for sname, lab, color, off in [("primary", "All records after audit", BLUE, -0.1), ("primary, blind only", "Blind records", ORANGE, 0.1)]:
            d = b[b["set"] == sname].set_index("bin").reindex(order)
            ok = d[metric].notna().to_numpy()
            ax.errorbar((x + off)[ok], scale * d[metric][ok], yerr=[scale * (d[metric] - d[f"{metric}_lo"])[ok], scale * (d[f"{metric}_hi"] - d[metric])[ok]],
                        fmt="o-", ms=3.8, lw=1.1, color=color, elinewidth=1.2, capsize=0, label=lab, markeredgecolor=SURFACE, markeredgewidth=0.6)
        if metric == "coverage":
            ax.axhline(90, color=INK2, lw=0.7, ls="--")
        ax.set_xticks(x, labels)
        ax.set_title(title, loc="left")
    top_legend(axes[2])
    fig.supxlabel("Composition distance to the nearest training formula", fontsize=7, color=INK2)
    fig.tight_layout(rect=TOP_RECT)
    save(fig, "fig4_error_vs_distance")


def figS1_scatter() -> None:
    d = pd.read_csv(R3 / "external_benchmark/similarity_records.csv", keep_default_na=False, na_values=[""])
    d = d[~d["excluded_primary"] & ~d["a7a_formula_in_repository"]]
    fig, ax = plt.subplots(figsize=(120 / 25.4, 2.9))
    style(ax, "y")
    for mask, lab, color, front in [(d["a7_system_seen"], "Seen chemical system", BLUE, False), (~d["a7_system_seen"], "Unseen chemical system", ORANGE, True)]:
        ax.scatter(d.loc[mask, "d_comp_train"], d.loc[mask, "abs_err_k"], s=11 if front else 6, color=color, alpha=0.9 if front else 0.45,
                   edgecolor=SURFACE, linewidth=0.5, label=f"{lab} (n={int(mask.sum())})", zorder=3 if front else 2)
    ax.set_xscale("log")
    ax.set_xlabel("Composition distance to the nearest training formula (log scale)", color=INK2)
    ax.set_ylabel("Absolute error (K)", color=INK2)
    top_legend(ax)
    fig.tight_layout(rect=TOP_RECT)
    save(fig, "figS1_blind_scatter")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for f in (fig1_physics, fig2_uncertainty, fig3_external, fig4_distance, figS1_scatter):
        f()
    print("figures written:", ", ".join(sorted(p.name for p in OUT.glob("*.pdf"))))


if __name__ == "__main__":
    main()
