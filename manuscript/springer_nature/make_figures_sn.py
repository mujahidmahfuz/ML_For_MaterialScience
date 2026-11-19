"""Figures for the Springer Nature (sn-jnl) manuscript, drawn at the class text width (372 pt = 131 mm).

Five main figures, one scientific message each (revision of 2026-11-20, following the figure plan of the revision guide):
  fig1  Magnetic data provenance and label consistency
  fig2  Incremental predictive value of physical descriptors (with the cell-size control)
  fig3  Reliability of predictive uncertainty (coverage overall and in subgroups, with interval widths and set sizes)
  fig4  Chemical novelty and predictive generalization (external benchmark by novelty subset and by distance)
  fig5  Reliability-aware screening (abstention curves and interval-based decisions)
Supplementary Figures: sfig1 (error against distance for every blind external record), sfig2 (summary schematic).
Reads the saved result files in paper/results and the frozen target files in paper/data (no model is fitted, no number is changed).
Output: PDFs next to this script (the template forbids image subfolders) and PNG previews in png/ (not used by LaTeX).
Usage:  python make_figures_sn.py
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Patch  # noqa: E402
from scipy import stats  # noqa: E402

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]  # paper/
RES, DATA = PKG / "results", PKG / "data"
R2, R3, RV = RES / "rq2_uncertainty", RES / "rq3_generalization", RES / "revision"
PNG = HERE / "png"

# Categorical slots 1-4 of the validated reference order (blue, orange, aqua, yellow); identity is also carried by legends and labels.
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GREY, INK, INK2, GRID, SURFACE = "#8a8984", "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
BLUE_RAMP = ("#f4f8fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b")
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
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)


def handle(color: str, line: bool = False, marker: str = "o") -> Line2D:
    """Legend key: a marker on a short line, without the dotted error-bar stub matplotlib draws by default."""
    return Line2D([], [], color=color, marker=marker, lw=1.2 if line else 0, **MARKER)


def errbar(ax: plt.Axes, x: float, y: float, lo: float, hi: float, color: str, horizontal: bool = True, marker: str = "o") -> None:
    err = [[x - lo], [hi - x]] if horizontal else [[y - lo], [hi - y]]
    kw = {"xerr": err} if horizontal else {"yerr": err}
    ax.errorbar(x, y, fmt=marker, color=color, ecolor=color, elinewidth=1.2, capsize=0, **MARKER, **kw)


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(HERE / f"{name}.pdf", facecolor=SURFACE, metadata={"CreationDate": None, "ModDate": None})
    PNG.mkdir(exist_ok=True)
    fig.savefig(PNG / f"{name}.png", dpi=300, facecolor=SURFACE)
    plt.close(fig)


def nb_interval(x: np.ndarray, test_over_train: float) -> tuple[float, float, float]:
    """Nadeau-Bengio corrected resampled-t 95% interval of the mean over J splits (as in the A1 tier inference)."""
    j = len(x)
    se = np.sqrt((1 / j + test_over_train) * np.var(x, ddof=1))
    t = stats.t.ppf(0.975, j - 1)
    return float(x.mean()), float(x.mean() - t * se), float(x.mean() + t * se)


# ------------------------------------------------------------------------------------------------ Figure 1: provenance
SOURCE_GROUPS = (("Materials Project (DFT)", BLUE), ("JARVIS-DFT", AQUA), ("Experimental compilations", ORANGE), ("Text-mined literature", YELLOW))
CLASS_COLORS = (("FM", BLUE), ("AFM", ORANGE), ("FiM", AQUA), ("NM", YELLOW))


def source_group(src: str) -> str:
    s = str(src)
    if s.startswith("mp_reformatted"):
        return "Materials Project (DFT)"
    if s.startswith("jarvis"):
        return "JARVIS-DFT"
    if s.startswith("chemdata"):
        return "Text-mined literature"
    return "Experimental compilations"


def target_sources() -> tuple[pd.DataFrame, pd.DataFrame]:
    tdir = DATA / "analysis_dataset/v1.4/targets"
    o = pd.read_csv(tdir / "ordering/target_ordering_clean.csv", usecols=["_source", "magnetic_ordering_clean", "ordering_valid"], low_memory=False)
    o = o[o["ordering_valid"] == True]  # noqa: E712 - boolean column
    c = pd.read_csv(tdir / "curie/target_curie_clean.csv", usecols=["_source", "target_valid"], low_memory=False)
    c = c[c["target_valid"] == True]  # noqa: E712
    m = pd.read_csv(tdir / "ms/target_ms_clean.csv", usecols=["_source", "Ms_momentPerUnitCell_clean"], low_memory=False)
    m = m[m["Ms_momentPerUnitCell_clean"].notna()]
    counts = pd.DataFrame({name: d["_source"].map(source_group).value_counts() for name, d in
                           (("Magnetic ordering", o), ("Curie temperature", c), ("DFT moment per cell", m))}).T.fillna(0)
    o = o.assign(prov=np.where(o["_source"].astype(str).str.startswith("mp_reformatted"), "Materials Project", "Experimental"))
    classes = pd.crosstab(o["prov"], o["magnetic_ordering_clean"])
    return counts, classes


def stacked_rows(ax: plt.Axes, table: pd.DataFrame, keys: tuple, label_min: float) -> None:
    y = np.arange(len(table))[::-1]
    shares = table.div(table.sum(axis=1), axis=0)
    left = np.zeros(len(table))
    for key, color in keys:
        if key not in shares:
            continue
        w = shares[key].to_numpy()
        ax.barh(y, w, left=left, height=0.62, color=color, edgecolor=SURFACE, linewidth=1.0)
        for yi, li, wi in zip(y, left, w):
            if wi >= label_min:
                ax.text(li + wi / 2, yi, f"{100 * wi:.0f}%", ha="center", va="center", fontsize=6, color=INK)
        left = left + w
    totals = table.sum(axis=1).astype(int).to_numpy()
    ax.set_yticks(y, [f"{n}\n(n = {t:,})" for n, t in zip(table.index, totals)])
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.5, 1], ["0", "50", "100"])
    ax.tick_params(axis="y", length=0)


def fig1() -> None:
    counts, classes = target_sources()
    conf = pd.read_csv(RV / "a2_provenance/label_confusion.csv", index_col=0)
    comp = pd.read_csv(RV / "a23_label_comparability/comparability_agreement.csv").set_index("subset")
    anchor = pd.read_csv(RV / "a16_magndata_anchor/anchor_agreement.csv").set_index("source")

    fig = plt.figure(figsize=(WIDTH_IN, 4.6))
    gs = fig.add_gridspec(2, 2, height_ratios=(1.0, 1.2), hspace=0.75, wspace=1.2)
    ax = fig.add_subplot(gs[0, 0])
    style(ax, "")
    stacked_rows(ax, counts[[k for k, _ in SOURCE_GROUPS if k in counts]], SOURCE_GROUPS, 0.07)
    ax.set_xlabel("Share of records (%)", color=INK2)
    ax.set_title("a   Sources of each target", loc="left")
    ax.legend([Patch(color=c) for _, c in SOURCE_GROUPS], [k for k, _ in SOURCE_GROUPS], loc="upper center", bbox_to_anchor=(0.35, -0.3),
              ncol=2, frameon=False, handlelength=1.0, columnspacing=1.0, handletextpad=0.4)

    ax = fig.add_subplot(gs[0, 1])
    style(ax, "")
    stacked_rows(ax, classes.loc[["Materials Project", "Experimental"]], CLASS_COLORS, 0.12)
    ax.set_xlabel("Share of ordering labels (%)", color=INK2)
    ax.set_title("b   Ordering classes by provenance", loc="left")
    ax.legend([Patch(color=c) for _, c in CLASS_COLORS], [k for k, _ in CLASS_COLORS], loc="upper center", bbox_to_anchor=(0.4, -0.3),
              ncol=4, frameon=False, handlelength=1.0, columnspacing=1.0, handletextpad=0.4)

    ax = fig.add_subplot(gs[1, 0])
    order, rows_shown = ["FM", "AFM", "FiM", "NM"], ["FM", "AFM", "FiM"]   # one formula with an experimental NM label is not shown
    m = conf.reindex(index=rows_shown, columns=order).fillna(0)
    share = m.div(m.sum(axis=1).replace(0, np.nan), axis=0).fillna(0).to_numpy()
    cmap = LinearSegmentedColormap.from_list("blue_ramp", BLUE_RAMP)
    ax.imshow(share, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i in range(len(rows_shown)):
        for j in range(4):
            ax.text(j, i, f"{int(m.iat[i, j])}", ha="center", va="center", fontsize=6.5, color=SURFACE if share[i, j] > 0.55 else INK)
    ax.set_xticks(range(4), order)
    ax.set_yticks(range(len(rows_shown)), [f"{k} ({int(m.loc[k].sum())})" for k in rows_shown])
    ax.set_xlabel("Materials Project label", color=INK2)
    ax.set_ylabel("Experimental label (formulas)", color=INK2)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.tick_params(length=0, colors=INK2)
    ax.set_title("c   Same formula, two sources (949)", loc="left")

    ax = fig.add_subplot(gs[1, 1])
    style(ax)
    rows = (("MP–exp., all", comp.loc["all"], "n_formulas", BLUE),
            ("MP–exp., bulk", comp.loc["bulk"], "n_formulas", BLUE),
            ("MP–exp., same s.g.", comp.loc["phase"], "n_formulas", BLUE),
            ("MP–exp., same s.g., stoich.", comp.loc["phase_stoich_bulk"], "n_formulas", BLUE),
            ("Exp.–MAGNDATA", anchor.loc["experimental"], "n_compositions", ORANGE),
            ("MP–MAGNDATA", anchor.loc["MP"], "n_compositions", AQUA))
    y = np.arange(len(rows))[::-1].astype(float)
    for yi, (_, r, ncol, color) in zip(y, rows):
        errbar(ax, r["kappa"], yi, r["kappa_lo"], r["kappa_hi"], color)
        ax.text(1.06, yi, f"{100 * r['agreement']:.0f}% ({int(r[ncol])})", va="center", ha="left", fontsize=6, color=INK2,
                transform=ax.get_yaxis_transform(), clip_on=False)
    ax.axvline(0, color=INK2, lw=0.7, ls="--")
    ax.set_yticks(y, [lab for lab, *_ in rows])
    ax.set_xlim(-0.1, 1.0)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel("Cohen's κ (95% interval)", color=INK2)
    ax.text(1.06, len(rows) - 0.45, "Agree (n)", ha="left", va="bottom", fontsize=6, color=INK2, fontweight="bold",
            transform=ax.get_yaxis_transform(), clip_on=False)
    ax.set_title("d   Agreement of labels", loc="left")
    fig.subplots_adjust(left=0.2, right=0.86, top=0.95, bottom=0.08)
    save(fig, "fig1")


# ------------------------------------------------------------------------------------------------ Figure 2: descriptors
def sitecount_mcell() -> pd.DataFrame:
    """Tier 3 beyond a single site-count descriptor for the per-cell moment, refit-aware interval as in A1 (one XGBoost realization)."""
    p = pd.read_csv(RES / "rq1_physics_descriptors/ms_cell_size_control/sitecount_control_10splits_paired.csv")
    p = p[(p["scope"] == "per_split") & (p["metric"] == "mae") & (p["from_variant"] == "C_T2_plus_nsites") & (p["to_variant"] == "tier3")]
    ratio = pd.read_csv(RV / "a1_tier_inference.csv").query("target == 'ms_moment'")["test_over_train"].iloc[0]
    rows = []
    for alg, g in p.groupby("algorithm"):
        mean, lo, hi = nb_interval(g["improvement"].to_numpy(), ratio)
        rows.append({"algorithm": alg, "from": "tier2_sitecount", "to": "tier3", "mean_improvement": mean, "nb_ci_low": lo, "nb_ci_high": hi})
    return pd.DataFrame(rows)


def fig2() -> None:
    t = pd.read_csv(RV / "a1_tier_inference.csv")
    fu = pd.read_csv(RV / "a5_moment_per_fu/per_fu_tier_effects.csv").query("subset == 'all'")
    sc = sitecount_mcell()
    alg_map = {"ordering": {"linear": "linear", "gradient_boosting": "gradient_boosting", "xgboost": "xgboost"},
               "curie": {"linear": "linear_clip", "gradient_boosting": "gradient_boosting", "xgboost": "xgboost_seedmean"},
               "ms_moment": {"linear": "linear", "gradient_boosting": "gradient_boosting", "xgboost": "xgboost_seedmean"}}
    panels = (("a   Magnetic ordering", "Change in macro-F1", "ordering", (-0.11, 0.08)),
              ("b   Curie temperature", "Reduction in MAE (K)", "curie", (-55, 40)),
              ("c   DFT moment per cell", "Reduction in MAE (μB per cell)", "ms_moment", (-0.09, 0.14)),
              ("d   DFT moment per formula unit", "Reduction in MAE (μB per formula unit)", "per_fu", (-0.03, 0.08)))
    contrasts = ((("tier1", "tier2"), 0.22, BLUE, "Tier 1 → Tier 2"), (("tier1", "tier3"), 0.0, ORANGE, "Tier 1 → Tier 3"),
                 (("tier2_sitecount", "tier3"), -0.22, GREY, "Tier 3 beyond site count"))
    fig, axes = plt.subplots(2, 2, figsize=(WIDTH_IN, 3.9), sharey=True)
    y = np.arange(len(ALG))[::-1].astype(float)
    for ax, (title, xlabel, tgt, xlim) in zip(axes.flat, panels):
        style(ax)
        ax.axvline(0, color=INK2, lw=0.7, ls="--")
        for i, (alg, _) in enumerate(ALG):
            if tgt == "per_fu":
                d = fu[fu["algorithm"] == alg]
            else:
                d = t[(t["target"] == tgt) & (t["algorithm"] == alg_map[tgt][alg])]
                if tgt == "ms_moment":
                    d = pd.concat([d, sc[sc["algorithm"] == alg]])
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
    save(fig, "fig2")


# ------------------------------------------------------------------------------------------------ Figure 3: uncertainty
def fig3() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(WIDTH_IN, 2.8), gridspec_kw={"width_ratios": (1, 1, 1.05)})
    methods = (("split_conformal", "Split"), ("normalized_conformal", "Normalized"), ("cqr", "CQR"))
    cur = pd.read_csv(RV / "a4_uq/curie_subgroup_coverage.csv")
    ms = pd.read_csv(R2 / "repeated_splits/ms_moment/repeated_split_summary.csv")
    specs = (("a   Curie temperature", cur, (("all", "All test materials", BLUE), ("top decile of predicted value", "Highest predictions", ORANGE),
                                              ("source: chemdata_curie_neel", "Text-mined labels", AQUA)), "K", 0),
             ("b   DFT moment per cell", ms, (("all", "All test materials", BLUE), ("predicted_value:highest_third", "Highest predictions", ORANGE),
                                              ("family:Oxide", "Oxides", AQUA)), "μB", 1))
    for ax, (title, rp, groups, unit, nd) in zip(axes[:2], specs):
        style(ax, "y")
        x = np.arange(len(methods))
        for k, (group, _, color) in enumerate(groups):
            off = (k - 1) * 0.2
            for i, (meth, _) in enumerate(methods):
                r = rp[(rp["method"] == meth) & (rp["group"] == group)].iloc[0]
                m, sd = 100 * r["mean_coverage"], 100 * r["sd_coverage"]
                errbar(ax, x[i] + off, m, m - sd, m + sd, color, horizontal=False)
        widths = [rp[(rp["method"] == meth) & (rp["group"] == "all")]["mean_width"].iloc[0] for meth, _ in methods]
        ax.axhline(90, color=INK2, lw=0.7, ls="--")
        ax.set_xticks(x, [f"{lab}\n{w:.{nd}f} {unit}" for (_, lab), w in zip(methods, widths)])
        ax.set_xlim(-0.5, 2.5)
        ax.set_ylim(40, 101)
        ax.set_title(title, loc="left")
        ax.legend([handle(c) for *_, c in groups], [lab for _, lab, _ in groups], loc="lower left", frameon=False,
                  handletextpad=0.3, borderaxespad=0.2)
    axes[0].set_ylabel("Coverage of 90% intervals (%)", color=INK2)
    ax = axes[2]
    style(ax, "y")
    sets = pd.read_csv(RV / "a4_uq/ordering_calibration_split_summary.csv")
    sets = sets[sets["calibration"].str.startswith("split")].set_index("sets")
    classes = ("FM", "NM", "AFM", "FiM")
    x = np.arange(len(classes))
    for off, meth, color, mk in ((-0.14, "marginal", BLUE, "s"), (0.14, "class-conditional", ORANGE, "D")):
        ax.plot(x + off, [100 * sets.loc[meth, f"coverage_{k}"] for k in classes], ls="none", marker=mk, color=color, zorder=3, **MARKER)
    ax.axhline(90, color=INK2, lw=0.7, ls="--")
    ax.set_xticks(x, classes)
    ax.set_xlim(-0.5, 3.5)
    ax.set_ylim(45, 101)
    ax.set_title("c   Ordering prediction sets", loc="left")
    ax.legend([handle(BLUE, marker="s"), handle(ORANGE, marker="D")],
              [f"Marginal (mean size {sets.loc['marginal', 'set_size']:.2f})",
               f"Class-conditional ({sets.loc['class-conditional', 'set_size']:.2f})"],
              loc="lower left", frameon=False, handletextpad=0.3, borderaxespad=0.2)
    ax.set_xlabel("Ordering class", color=INK2)
    fig.tight_layout(w_pad=1.0)
    save(fig, "fig3")


# ------------------------------------------------------------------------------------------------ Figure 4: chemical novelty
SUBSETS = (("all", "All records"), ("composition seen in training repository", "Seen composition"),
           ("composition NEVER seen (blind)", "Blind"), ("blind + paper never used (corrected DOI match)", "Blind, new paper"),
           ("blind + seen chemical system", "Blind, seen system"), ("blind + unseen chemical system", "Blind, unseen system"),
           ("blind + paper never used + unseen system", "Blind, new paper, unseen system"))
R2_FLOOR = -1.5
DIST_ORDER = ("0: formula used in training", "Q1 (closest)", "Q2", "Q3", "Q4 (farthest)")


def novelty_panels(fig: plt.Figure, ax_mae: plt.Axes, ax_r2: plt.Axes) -> None:
    st = pd.read_csv(R3 / "external_benchmark/subset_metrics_bootstrap.csv")
    st = st[st["cluster"] == PRE]
    tables = (("original (all 2,500 records)", "Before audit", BLUE, 0.16), ("primary benchmark (A1/A2/A4/A5 removed)", "After audit", ORANGE, -0.16))
    y = np.arange(len(SUBSETS))[::-1].astype(float)
    keys = [k for k, _ in SUBSETS]
    for ax, metric, title, xlabel in ((ax_mae, "mae_k", "a   Error by novelty subset", "MAE (K)"), (ax_r2, "r2", "b   Variance explained", "R²")):
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
            ax.set_yticks(y, [""] * len(y))
        ax.set_ylim(-0.6, len(SUBSETS) - 0.4)
        ax.set_title(title, loc="left")
        ax.set_xlabel(xlabel, color=INK2)
    n = st[st["table"] == tables[1][0]].set_index("subset")["n"]
    ax_mae.set_yticks(y, [f"{lab} ({int(n[k]):,})" for k, lab in SUBSETS])
    ax_r2.legend([handle(c) for _, _, c, _ in tables], [lab for _, lab, _, _ in tables], loc="upper left", frameon=False,
                 handletextpad=0.3, borderaxespad=0.2)


def fig4() -> None:
    fig = plt.figure(figsize=(WIDTH_IN, 5.0))
    ax_mae = fig.add_axes((0.355, 0.58, 0.335, 0.37))
    ax_r2 = fig.add_axes((0.71, 0.58, 0.27, 0.37))
    novelty_panels(fig, ax_mae, ax_r2)
    b = pd.read_csv(R3 / "external_benchmark/similarity_bins.csv")
    sets = (("primary", "All records after audit", BLUE, -0.1), ("primary, blind only", "Blind records", ORANGE, 0.1))
    x = np.arange(len(DIST_ORDER))
    bottom = (fig.add_axes((0.09, 0.09, 0.37, 0.33)), fig.add_axes((0.6, 0.09, 0.37, 0.33)))
    for ax, metric, title, ylabel, scale in ((bottom[0], "mae_k", "c   Error by distance to training data", "MAE (K)", 1),
                                             (bottom[1], "coverage", "d   Coverage and width of 90% intervals", "Coverage (%)", 100)):
        style(ax, "y")
        for sname, _, color, off in sets:
            d = b[b["set"] == sname].set_index("bin").reindex(list(DIST_ORDER))
            ok = d[metric].notna().to_numpy()
            ax.errorbar((x + off)[ok], scale * d[metric][ok], yerr=[scale * (d[metric] - d[f"{metric}_lo"])[ok], scale * (d[f"{metric}_hi"] - d[metric])[ok]],
                        fmt="o-", lw=1.1, color=color, elinewidth=1.2, capsize=0, **MARKER)
            if metric == "coverage" and sname == "primary, blind only":
                for xi, w in zip((x + off)[ok], d["mean_width_k"][ok]):
                    ax.text(xi, 58.5, f"{w:.0f}", ha="center", va="center", fontsize=5.8, color=INK2)
                ax.text(0.0, 58.5, "Width (K):", ha="center", va="center", fontsize=5.8, color=INK2)
        if metric == "coverage":
            ax.axhline(90, color=INK2, lw=0.7, ls="--")
            ax.set_ylim(55, 101)
        ax.set_xticks(x, ["0", "Q1", "Q2", "Q3", "Q4"])
        ax.set_xlim(-0.5, 4.5)
        ax.set_ylabel(ylabel, color=INK2)
        ax.set_xlabel("Distance bin (0 = same composition)", color=INK2, fontsize=6.2)
        ax.set_title(title, loc="left")
    bottom[0].legend([handle(c, line=True) for _, _, c, _ in sets], [lab for _, lab, _, _ in sets], loc="upper left", frameon=False,
                     handletextpad=0.3, borderaxespad=0.2)
    save(fig, "fig4")


# ------------------------------------------------------------------------------------------------ Figure 5: screening
def external_curves() -> pd.DataFrame:
    """Full risk-coverage curves on the 465 blind external records (descriptive; the bootstrapped points come from A9)."""
    d = pd.read_csv(R3 / "external_benchmark/similarity_records.csv", keep_default_na=False, na_values=[""])
    d = d[~d["excluded_primary"] & ~d["a7a_formula_in_repository"]].copy()
    d["covered"] = (d["tc_exp_k"] >= d["tc_lo_k"]) & (d["tc_exp_k"] <= d["tc_hi_k"])
    rows = []
    for rule, col in (("composition distance", "d_comp_train"), ("interval width", "width_k")):
        s = d.sort_values(col, kind="mergesort")
        k = np.arange(1, len(s) + 1)
        rows.append(pd.DataFrame({"abstain_on": rule, "retained": k / len(s), "mae": np.cumsum(s["abs_err_k"].to_numpy()) / k,
                                  "coverage": np.cumsum(s["covered"].to_numpy()) / k}))
    return pd.concat(rows, ignore_index=True)


def threshold_values() -> tuple[pd.DataFrame, pd.DataFrame]:
    ext = pd.read_csv(RV / "a9_screening/threshold_task.csv").set_index("quantity")
    per = pd.read_csv(RV / "a15_internal_screening/threshold_task_per_split.csv")
    return ext, per


def fig5() -> None:
    ext = pd.read_csv(RV / "a9_screening/risk_coverage.csv")
    internal = pd.read_csv(RV / "a15_internal_screening/risk_coverage.csv")
    curves = external_curves()
    rules = (("composition distance", "Abstain on distance", BLUE, "o", -0.015), ("interval width", "Abstain on interval width", ORANGE, "s", 0.015))
    fig, axes = plt.subplots(1, 3, figsize=(WIDTH_IN, 2.7))
    ax = axes[0]
    style(ax, "y")
    for rule, _, color, mk, dx in rules:
        c = curves[(curves["abstain_on"] == rule) & (curves["retained"] >= 0.2)]
        ax.plot(c["retained"], c["mae"], color=color, lw=1.0, alpha=0.55)
        for _, r in ext[ext["abstain_on"] == rule].iterrows():
            errbar(ax, r["retained_fraction"] + dx, r["mae_k"], r["mae_lo"], r["mae_hi"], color, horizontal=False, marker=mk)
    ax.set_xlim(1.05, 0.05)
    ax.set_ylim(0, 170)
    ax.set_xlabel("Share of records kept", color=INK2)
    ax.set_ylabel("MAE of kept records (K)", color=INK2)
    ax.set_title("a   External blind (465)", loc="left")
    ax.legend([handle(c, line=True, marker=mk) for _, _, c, mk, _ in rules], ["Abstain on distance", "Abstain on width"], loc="lower left",
              frameon=False, handletextpad=0.3, borderaxespad=0.2)

    ax = axes[1]
    style(ax, "y")
    for rule, _, color, mk, dx in rules:
        d = internal[internal["abstain_on"] == rule].sort_values("retained_share_mean")
        ax.plot(d["retained_share_mean"] + dx, d["mae_k_mean"], color=color, lw=1.0, alpha=0.55)
        for _, r in d.iterrows():
            errbar(ax, r["retained_share_mean"] + dx, r["mae_k_mean"], r["mae_k_mean"] - r["mae_k_sd"], r["mae_k_mean"] + r["mae_k_sd"], color,
                   horizontal=False, marker=mk)
    ax.set_xlim(1.05, 0.05)
    ax.set_ylim(0, 170)
    ax.set_xlabel("Share of records kept", color=INK2)
    ax.set_title("b   Internal tests (10 splits)", loc="left")

    ax = axes[2]
    style(ax, "y")
    tt_ext, per = threshold_values()
    bars = (("Point\naccuracy", "point accuracy", "point_accuracy"), ("Share\ndecided", "interval decision rate", "interval_decision_rate"),
            ("Accuracy of\ndecisions", "accuracy of interval decisions", "interval_decision_accuracy"))
    x = np.arange(len(bars))
    for i, (_, q, col) in enumerate(bars):
        r = tt_ext.loc[q]
        errbar(ax, x[i] - 0.14, 100 * r["value"], 100 * r["lo"], 100 * r["hi"], BLUE, horizontal=False)
        v = per[col].to_numpy(dtype=float)
        errbar(ax, x[i] + 0.14, 100 * v.mean(), 100 * (v.mean() - v.std(ddof=1)), 100 * (v.mean() + v.std(ddof=1)), ORANGE,
               horizontal=False, marker="s")
    ax.set_xticks(x, [lab for lab, *_ in bars])
    ax.set_xlim(-0.5, 2.5)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Percentage", color=INK2)
    ax.set_title(r"c   Is $T_\mathrm{C}$ > 300 K?", loc="left")
    ax.legend([handle(BLUE), handle(ORANGE, marker="s")], ["External blind", "Internal"], loc="lower left", frameon=False,
              handletextpad=0.3, borderaxespad=0.2)
    fig.tight_layout(w_pad=1.0)
    save(fig, "fig5")


# ------------------------------------------------------------------------------------------------ Supplementary figures
def sfig1() -> None:
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
    save(fig, "sfig1")


SUMMARY_ROWS = (
    ("Label provenance",
     "Computed and experimental ordering labels agreed for 28% of shared formulas (κ 0.00), and for 25% when both referred to the same space group.",
     "The two sources label magnetic order by different conventions.",
     "Compare labels across sources and with measured magnetic structures before pooling them."),
    ("Added physics",
     "Non-magnetic DFT descriptors gave no detectable gain for ordering or the Curie temperature; the moment gain mostly reflected cell size.",
     "A descriptor can be physically meaningful and still add little predictive information.",
     "Compare descriptor sets on identical rows, with a size control."),
    ("Calibration",
     "Coverage was near 90% overall but 65.5% in the top Curie-temperature decile (constant-width intervals) and 54-57% for two ordering classes.",
     "Average coverage hides failures in physically important subgroups.",
     "Report subgroup coverage; use normalized or class-conditional sets."),
    ("Chemical novelty",
     "Error grew with chemical distance, and in unseen chemical systems performance was much weaker, with wide uncertainty.",
     "New compositions in known chemistry and new chemical systems are different tasks.",
     "Define novelty by chemical system; abstain on distance and on wide intervals."),
)


def sfig2() -> None:
    """Closing summary: for each finding, what was observed, what it means and what follows (text only; numbers as in Results)."""
    height_mm, row_h, gap = 86.0, 18.0, 2.2
    fig, ax = plt.subplots(figsize=(WIDTH_IN, height_mm / 25.4))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set_xlim(-1, 132)
    ax.set_ylim(-1, height_mm)
    ax.axis("off")
    cols = ((0.0, 52.0, "Observation", "#eaf2fc", BLUE, 40), (58.0, 34.0, "Interpretation", "#f3f3f1", INK2, 23),
            (98.0, 33.0, "Practice", "#fdeee7", ORANGE, 23))
    for x0, w, head, _fc, _ec, _wrap in cols:
        ax.text(x0 + w / 2, height_mm - 2.0, head, ha="center", va="center", fontsize=7.5, fontweight="bold", color=INK2)
    top = height_mm - 6.0
    for r, (name, obs, interp, strat) in enumerate(SUMMARY_ROWS):
        y = top - r * (row_h + gap) - row_h
        for (x0, w, _head, fc, ec, wrap), body in zip(cols, (obs, interp, strat)):
            ax.add_patch(FancyBboxPatch((x0, y), w, row_h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec=ec, lw=0.7))
            ytxt = y + row_h - 1.8
            if x0 == 0.0:
                ax.text(x0 + 2.2, ytxt, name, ha="left", va="top", fontsize=6.9, fontweight="bold", color=INK2)
                ytxt -= 3.6
            ax.text(x0 + 2.2, ytxt, textwrap.fill(body, wrap), ha="left", va="top", fontsize=6.3, color=INK2, linespacing=1.25)
        for x_from, x_to in ((52.0, 58.0), (92.0, 98.0)):
            ax.annotate("", xy=(x_to - 0.4, y + row_h / 2), xytext=(x_from + 0.4, y + row_h / 2),
                        arrowprops=dict(arrowstyle="-|>", color=INK2, lw=0.8, mutation_scale=6))
    save(fig, "sfig2")


def main() -> None:
    for build in (fig1, fig2, fig3, fig4, fig5, sfig1, sfig2):
        build()
    print("written:", ", ".join(sorted(p.name for p in HERE.glob("*.pdf"))))


if __name__ == "__main__":
    main()
