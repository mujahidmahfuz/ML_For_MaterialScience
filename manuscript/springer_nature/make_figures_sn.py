"""Figures for the Springer Nature (sn-jnl) manuscript, drawn at the class text width (372 pt = 131 mm).

Reads the same result files as paper/scripts/make_figures.py (no model is fitted, no number is changed); only the
layout differs: 131 mm wide so that 7 pt text stays 7 pt in the PDF, one legend per figure that never covers data,
row labels that fit, and visible markers where an interval is cut off.
Output: fig1.pdf ... fig4.pdf and edfig1.pdf next to this script (the template forbids image subfolders), plus PNG
previews in png/ (not used by LaTeX).
Usage:  python make_figures_sn.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]  # paper/
RES = PKG / "results"
R2, R3 = RES / "rq2_uncertainty", RES / "rq3_generalization"
PNG = HERE / "png"

BLUE, ORANGE, GREY = "#2a78d6", "#e8622c", "#55544f"
INK2, GRID, SURFACE = "#3d3c39", "#e4e3df", "#ffffff"
WIDTH_IN = 131 / 25.4
ALG = (("linear", "Ridge / logistic"), ("gradient_boosting", "Gradient boosting"), ("xgboost", "XGBoost"))
PRE = "paper (pre-specified: shared-DOI components)"
MARKER = dict(ms=4.0, markeredgecolor=SURFACE, markeredgewidth=0.6)

plt.rcParams.update({
    "font.family": "Arial", "font.size": 7, "axes.titlesize": 7.5, "axes.titleweight": "bold", "axes.labelsize": 7,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "pdf.fonttype": 42, "ps.fonttype": 42, "axes.titlepad": 6,
})


def style(ax: plt.Axes, grid_axis: str = "x") -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK2)
    ax.tick_params(colors=INK2)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)


def handle(color: str, line: bool = False, marker: str = "o") -> Line2D:
    """Legend key: a marker on a short line, without the dotted error-bar stub matplotlib draws by default."""
    return Line2D([], [], color=color, marker=marker, lw=1.2 if line else 0, **MARKER)


def errbar(ax: plt.Axes, x: float, y: float, lo: float, hi: float, color: str, horizontal: bool = True) -> None:
    err = [[x - lo], [hi - x]] if horizontal else [[y - lo], [hi - y]]
    kw = {"xerr": err} if horizontal else {"yerr": err}
    ax.errorbar(x, y, fmt="o", color=color, ecolor=color, elinewidth=1.2, capsize=0, **MARKER, **kw)


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(HERE / f"{name}.pdf", facecolor=SURFACE, metadata={"CreationDate": None, "ModDate": None})
    PNG.mkdir(exist_ok=True)
    fig.savefig(PNG / f"{name}.png", dpi=300, facecolor=SURFACE)
    plt.close(fig)


# ------------------------------------------------------------------------------------------------ Figure 1 (2 x 2)
def fig1() -> None:
    t = pd.read_csv(RES / "revision/a1_tier_inference.csv")
    fu = pd.read_csv(RES / "revision/a5_moment_per_fu/per_fu_tier_effects.csv").query("subset == 'all'")
    alg_map = {"ordering": {"linear": "linear", "gradient_boosting": "gradient_boosting", "xgboost": "xgboost"},
               "curie": {"linear": "linear_clip", "gradient_boosting": "gradient_boosting", "xgboost": "xgboost_seedmean"},
               "ms_moment": {"linear": "linear", "gradient_boosting": "gradient_boosting", "xgboost": "xgboost_seedmean"}}
    panels = (("a   Magnetic ordering", "Change in macro-F1", "ordering", (-0.11, 0.08)),
              ("b   Curie temperature", "Reduction in MAE (K)", "curie", (-55, 40)),
              ("c   DFT moment per cell", "Reduction in MAE (μB per cell)", "ms_moment", (-0.03, 0.14)),
              ("d   DFT moment per formula unit", "Reduction in MAE (μB per formula unit)", "per_fu", (-0.03, 0.08)))
    contrasts = ((("tier1", "tier2"), 0.22, BLUE, "Tier 1 → Tier 2"), (("tier1", "tier3"), 0.0, ORANGE, "Tier 1 → Tier 3"),
                 (("tier2_sitecount", "tier3"), -0.22, GREY, "Tier 3 beyond site count"))
    fig, axes = plt.subplots(2, 2, figsize=(WIDTH_IN, 3.9), sharey=True)
    y = np.arange(len(ALG))[::-1].astype(float)
    for ax, (title, xlabel, tgt, xlim) in zip(axes.flat, panels):
        style(ax)
        ax.axvline(0, color=INK2, lw=0.7, ls="--")
        for i, (alg, _) in enumerate(ALG):
            d = fu[fu["algorithm"] == alg] if tgt == "per_fu" else t[(t["target"] == tgt) & (t["algorithm"] == alg_map[tgt][alg])]
            r = d.set_index(["from", "to"])
            for key, off, color, _ in contrasts:
                if key not in r.index:
                    continue
                row = r.loc[key]
                errbar(ax, row["mean_improvement"], y[i] + off, row["nb_ci_low"], row["nb_ci_high"], color)
        ax.set_xlim(*xlim)
        ax.set_ylim(-0.5, 2.5)
        ax.set_title(title, loc="left")
        ax.set_xlabel(xlabel, color=INK2)
    for ax in axes[:, 0]:
        ax.set_yticks(y, [lab for _, lab in ALG])
    fig.legend([handle(c) for *_, c, _ in contrasts], [lab for *_, lab in contrasts], loc="upper center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 1.0), handletextpad=0.3, columnspacing=1.6)
    fig.tight_layout(rect=(0, 0, 1, 0.94), h_pad=1.6, w_pad=1.2)
    save(fig, "fig1")


# ------------------------------------------------------------------------------------------------ Figure 2
def fig2() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(WIDTH_IN, 2.45))
    methods = (("split_conformal", "Split"), ("normalized_conformal", "Normalized"), ("cqr", "CQR"))
    sources = {"curie": (pd.read_csv(RES / "revision/a4_uq/curie_subgroup_coverage.csv"), "top decile of predicted value"),
               "ms_moment": (pd.read_csv(R2 / "repeated_splits/ms_moment/repeated_split_summary.csv"), "predicted_value:highest_third")}
    for ax, (tgt, title) in zip(axes[:2], (("curie", "a   Curie temperature"), ("ms_moment", "b   DFT moment per cell"))):
        style(ax, "y")
        rp, hi_group = sources[tgt]
        x = np.arange(len(methods))
        for off, group, color in ((-0.14, "all", BLUE), (0.14, hi_group, ORANGE)):
            for i, (meth, _) in enumerate(methods):
                r = rp[(rp["method"] == meth) & (rp["group"] == group)].iloc[0]
                m, sd = 100 * r["mean_coverage"], 100 * r["sd_coverage"]
                errbar(ax, x[i] + off, m, m - sd, m + sd, color, horizontal=False)
        ax.axhline(90, color=INK2, lw=0.7, ls="--")
        ax.set_xticks(x, [lab for _, lab in methods])
        ax.set_xlim(-0.5, 2.5)
        ax.set_ylim(30, 101)
        ax.set_title(title, loc="left")
    axes[0].set_ylabel("Coverage (%)", color=INK2)
    axes[1].legend([handle(BLUE), handle(ORANGE)], ["All test materials", "Highest predictions"], loc="lower left", frameon=False,
                   handletextpad=0.3, borderaxespad=0.2)
    ax = axes[2]
    style(ax, "y")
    sets = pd.read_csv(RES / "revision/a4_uq/ordering_calibration_split_summary.csv")
    sets = sets[sets["calibration"].str.startswith("split")].set_index("sets")
    classes = ("FM", "NM", "AFM", "FiM")
    x = np.arange(len(classes))
    for off, meth, color, mk in ((-0.14, "marginal", BLUE, "s"), (0.14, "class-conditional", ORANGE, "D")):
        ax.plot(x + off, [100 * sets.loc[meth, f"coverage_{k}"] for k in classes], ls="none", marker=mk, color=color, zorder=3, **MARKER)
    ax.axhline(90, color=INK2, lw=0.7, ls="--")
    ax.set_xticks(x, classes)
    ax.set_xlim(-0.5, 3.5)
    ax.set_ylim(30, 101)
    ax.set_title("c   Ordering prediction sets", loc="left")
    ax.legend([handle(BLUE, marker="s"), handle(ORANGE, marker="D")], ["Marginal", "Class-conditional"], loc="lower left", frameon=False,
              handletextpad=0.3, borderaxespad=0.2)
    fig.tight_layout(w_pad=1.0)
    save(fig, "fig2")


# ------------------------------------------------------------------------------------------------ Figures 3 and 4
SUBSETS = (("all", "All records"), ("composition seen in training repository", "Seen composition"),
           ("composition NEVER seen (blind)", "Blind"), ("blind + paper never used (corrected DOI match)", "Blind, new paper"),
           ("blind + seen chemical system", "Blind, seen system"), ("blind + unseen chemical system", "Blind, unseen system"),
           ("blind + paper never used + unseen system", "Blind, new paper, unseen system"))
R2_FLOOR = -1.5


def fig3() -> None:
    st = pd.read_csv(R3 / "external_benchmark/subset_metrics_bootstrap.csv")
    st = st[st["cluster"] == PRE]
    tables = (("original (all 2,500 records)", "Before audit", BLUE, 0.16), ("primary benchmark (A1/A2/A4/A5 removed)", "After audit", ORANGE, -0.16))
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH_IN, 2.9), sharey=True, gridspec_kw={"width_ratios": (1.15, 1)})
    y = np.arange(len(SUBSETS))[::-1].astype(float)
    keys = [k for k, _ in SUBSETS]
    for ax, metric, title, xlabel in ((axes[0], "mae_k", "a   Error", "MAE (K)"), (axes[1], "r2", "b   Variance explained", "R²")):
        style(ax)
        for tname, _, color, off in tables:
            d = st[st["table"] == tname].set_index("subset").loc[keys]
            lo = d[f"{metric}_lo"].to_numpy()
            if metric == "r2":
                clipped = lo < R2_FLOOR
                lo = np.where(clipped, R2_FLOOR, lo)
                ax.plot(np.full(clipped.sum(), R2_FLOOR + 0.02), (y + off)[clipped], ls="none", marker="<", ms=3.5, color=color, clip_on=False)
            ax.errorbar(d[metric], y + off, xerr=[d[metric] - lo, d[f"{metric}_hi"] - d[metric]], fmt="o", color=color, ecolor=color,
                        elinewidth=1.2, capsize=0, **MARKER)
        if metric == "r2":
            ax.axvline(0, color=INK2, lw=0.7, ls="--")
            ax.set_xlim(R2_FLOOR, 1.0)
        ax.set_ylim(-0.6, len(SUBSETS) - 0.4)
        ax.set_title(title, loc="left")
        ax.set_xlabel(xlabel, color=INK2)
    n = st[st["table"] == tables[1][0]].set_index("subset")["n"]
    axes[0].set_yticks(y, [f"{lab} ({int(n[k]):,})" for k, lab in SUBSETS])
    fig.legend([handle(c) for _, _, c, _ in tables], [lab for _, lab, _, _ in tables], loc="upper right", ncol=2, frameon=False,
               bbox_to_anchor=(1.0, 1.0), handletextpad=0.3, columnspacing=1.6)
    fig.tight_layout(rect=(0, 0, 1, 0.93), w_pad=1.0)
    save(fig, "fig3")


def fig4() -> None:
    b = pd.read_csv(R3 / "external_benchmark/similarity_bins.csv")
    order = ("0: formula used in training", "Q1 (closest)", "Q2", "Q3", "Q4 (farthest)")
    fig, axes = plt.subplots(1, 3, figsize=(WIDTH_IN, 2.35))
    x = np.arange(len(order))
    sets = (("primary", "All records after audit", BLUE, -0.1), ("primary, blind only", "Blind records", ORANGE, 0.1))
    for ax, metric, title, ylabel, scale in ((axes[0], "mae_k", "a   Error", "MAE (K)", 1),
                                             (axes[1], "mean_width_k", "b   Interval width", "Mean width of 90% interval (K)", 1),
                                             (axes[2], "coverage", "c   Interval coverage", "Coverage (%)", 100)):
        style(ax, "y")
        for sname, _, color, off in sets:
            d = b[b["set"] == sname].set_index("bin").reindex(list(order))
            ok = d[metric].notna().to_numpy()
            ax.errorbar((x + off)[ok], scale * d[metric][ok], yerr=[scale * (d[metric] - d[f"{metric}_lo"])[ok], scale * (d[f"{metric}_hi"] - d[metric])[ok]],
                        fmt="o-", lw=1.1, color=color, elinewidth=1.2, capsize=0, **MARKER)
        if metric == "coverage":
            ax.axhline(90, color=INK2, lw=0.7, ls="--")
        ax.set_xticks(x, ["0", "Q1", "Q2", "Q3", "Q4"])
        ax.set_xlim(-0.5, 4.5)
        ax.set_ylabel(ylabel, color=INK2)
        ax.set_xlabel("Distance bin", color=INK2)
        ax.set_title(title, loc="left")
    fig.legend([handle(c, line=True) for _, _, c, _ in sets], [lab for _, lab, _, _ in sets], loc="upper right", ncol=2, frameon=False,
               bbox_to_anchor=(1.0, 1.0), handletextpad=0.3, columnspacing=1.6)
    fig.tight_layout(rect=(0, 0, 1, 0.92), w_pad=1.0)
    save(fig, "fig4")


def edfig1() -> None:
    d = pd.read_csv(R3 / "external_benchmark/similarity_records.csv", keep_default_na=False, na_values=[""])
    d = d[~d["excluded_primary"] & ~d["a7a_formula_in_repository"]]
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 2.7))
    style(ax, "y")
    groups = ((d["a7_system_seen"], "Seen chemical system", BLUE, False), (~d["a7_system_seen"], "Unseen chemical system", ORANGE, True))
    for mask, lab, color, front in groups:
        ax.scatter(d.loc[mask, "d_comp_train"], d.loc[mask, "abs_err_k"], s=12 if front else 7, color=color, alpha=0.95 if front else 0.5,
                   edgecolor=SURFACE, linewidth=0.4, label=f"{lab} (n = {int(mask.sum())})", zorder=3 if front else 2)
    ax.set_xscale("log")
    ax.set_xlim(1e-4, 1.0)
    ax.set_ylim(-15, 640)
    ax.set_xlabel("Composition distance to the nearest training formula", color=INK2)
    ax.set_ylabel("Absolute error (K)", color=INK2)
    ax.legend(loc="upper left", frameon=False, handletextpad=0.2, markerscale=1.4)
    fig.tight_layout()
    save(fig, "edfig1")


def main() -> None:
    for build in (fig1, fig2, fig3, fig4, edfig1):
        build()
    print("written:", ", ".join(sorted(p.name for p in HERE.glob("*.pdf"))))


if __name__ == "__main__":
    main()
