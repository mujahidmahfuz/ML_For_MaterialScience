"""Phase 7 comparison plots (Curie and Ms): per-split tier performance, paired Tier 1 -> Tier 3 forest plots and the
Tier 3 feature-group sensitivity. Everything is drawn from the saved Phase 7 CSVs (no refit)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ALGS = ["linear", "gradient_boosting", "xgboost"]
ALG_LABEL = {"linear": "Linear / Ridge", "gradient_boosting": "Gradient Boosting", "xgboost": "XGBoost", "linear_clip": "Ridge, clipped inputs"}
ALG_COLOR = {"linear": "#0072B2", "gradient_boosting": "#D55E00", "xgboost": "#009E73", "linear_clip": "#56B4E9"}
TIER_LABEL = {"tier1": "Tier 1", "tier2": "Tier 2", "tier3": "Tier 3"}
UNIT = {"curie": "K", "ms_moment": "μB / cell"}
TITLE = {"curie": "Curie temperature (matched N = 5,490; experimental)",
         "ms_moment": "Saturation moment per cell (matched N = 10,852; computational)"}
VARIANT_COLOR = {"tier": "#555555", "A_": "#E69F00", "C_": "#CC79A7", "S_": "#0072B2"}
OFF_SCALE_NOTE ="'off-scale' = value beyond the plotted range (for example a numerically exploded Ridge fit)"


def style() -> None:
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 10,
                         "axes.titleweight": "semibold", "figure.dpi": 130, "savefig.dpi": 200, "axes.grid": True,
                         "grid.alpha": 0.25, "grid.linewidth": 0.6})


def per_split_tier_figure(results: pd.DataFrame, target: str, path) -> None:
    """MAE by tier: one thin line per split and the median over splits as a bold line."""
    style()
    prim = results[(results["analysis"] == "primary_matched") & (results["split_id"] != "frozen")]
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.2))
    n_splits = prim["split_id"].nunique()
    for ax, alg in zip(axes, ALGS):
        piv = prim[prim["algorithm"] == alg].pivot(index="split_id", columns="variant", values="mae")[["tier1", "tier2", "tier3"]]
        top = float(np.nanpercentile(piv.to_numpy(), 90) * 1.35)
        for _, row in piv.iterrows():
            ax.plot(range(3), np.clip(row.to_numpy(), None, top), color="#9a9a9a", lw=0.8, alpha=0.8, marker="o", ms=3)
        ax.plot(range(3), piv.median().to_numpy(), color=ALG_COLOR[alg], lw=2.4, marker="D", ms=6, label="median over splits", zorder=5)
        ax.set_ylim(bottom=0, top=top)
        ax.set_xticks(range(3), [TIER_LABEL[t] for t in piv.columns])
        ax.set_title(ALG_LABEL[alg], loc="left")
        ax.set_ylabel(f"test MAE ({UNIT[target]})")
        clipped = int((piv.to_numpy() > top).sum())
        if clipped:
            ax.text(0.98, 0.97, f"{clipped} split-fit(s) above the axis\n(drawn at the top edge)", transform=ax.transAxes,
                    ha="right", va="top", fontsize=7.5, color="#444")
        ax.legend(loc="lower left", fontsize=8, frameon=False)
    fig.suptitle(f"{TITLE[target]}: matched Tier 1 → 2 → 3 across {n_splits} independent formula-grouped splits",
                 x=0.01, ha="left", fontsize=10.5, fontweight="semibold", y=1.02)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def forest_panel(ax, sub: pd.DataFrame, alg: str, split_ids: list[str], target: str) -> None:
    per = sub[(sub["algorithm"] == alg) & (sub["scope"] == "per_split")]
    lim = float(np.nanpercentile(np.abs(per[["improvement_ci_low", "improvement_ci_high"]].to_numpy()), 90) * 1.25)
    ypos = {s: i for i, s in enumerate(split_ids)}
    for _, r in per.iterrows():
        y = ypos[r["split_id"]]
        lo, hi, v = (float(np.clip(r[c], -lim, lim)) for c in ("improvement_ci_low", "improvement_ci_high", "improvement"))
        ax.plot([lo, hi], [y, y], color=ALG_COLOR[alg], lw=1.4, alpha=0.7)
        ax.plot(v, y, "o", color=ALG_COLOR[alg], ms=5, markeredgecolor="white")
        if abs(r["improvement"]) > lim:
            ax.annotate("off-scale", (v, y), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=6.5, color="#444")
    pool = sub[(sub["algorithm"] == alg) & (sub["scope"] == "pooled_mean")]
    if len(pool):
        p = pool.iloc[0]
        y = len(split_ids) + 0.8
        ax.plot([max(p["improvement_ci_low"], -lim), min(p["improvement_ci_high"], lim)], [y, y], color="black", lw=2.4)
        ax.plot(float(np.clip(p["improvement"], -lim, lim)), y, "D", color="black", ms=7)
        ax.text(lim * 0.98, y - 0.75, f"pooled {p['improvement']:+.3g} [{p['improvement_ci_low']:+.3g}, {p['improvement_ci_high']:+.3g}]",
                ha="right", va="center", fontsize=7.8)
    ax.axvline(0, color="#444", lw=1)
    ax.set_xlim(-lim, lim)
    ax.set_title(ALG_LABEL[alg], loc="left")


def forest_figure(paired: pd.DataFrame, target: str, path, from_v: str = "tier1", to_v: str = "tier3",
                  analysis: str = "primary_matched") -> None:
    """Paired MAE improvement (positive = deeper tier better): per-split points with 95% CIs and the pooled interval."""
    style()
    sub = paired[(paired["target"] == target) & (paired["analysis"] == analysis) & (paired["metric"] == "mae") &
                 (paired["from_variant"] == from_v) & (paired["to_variant"] == to_v)]
    split_ids = sorted(sub.loc[sub["scope"] == "per_split", "split_id"].unique(), key=int)
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.6), sharey=True)
    for ax, alg in zip(axes, ALGS):
        forest_panel(ax, sub, alg, split_ids, target)
        ax.set_xlabel(f"MAE gain ({UNIT[target]})")
    axes[0].set_yticks(list(range(len(split_ids))) + [len(split_ids) + 0.8], [f"split {s}" for s in split_ids] + ["pooled"])
    axes[0].invert_yaxis()
    fig.suptitle(f"{TITLE[target]}: paired {TIER_LABEL[from_v]} → {TIER_LABEL[to_v]} difference per split (95% formula-bootstrap CI)",
                 x=0.01, ha="left", fontsize=10.5, fontweight="semibold", y=1.02)
    fig.text(0.01, -0.03, f"MAE gain = {TIER_LABEL[from_v]} error minus {TIER_LABEL[to_v]} error; positive means the deeper tier is better. "
             + OFF_SCALE_NOTE, fontsize=7.5, color="#444")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def sensitivity_figure(robust: pd.DataFrame, target: str, path) -> None:
    """Pooled MAE improvement over Tier 1 for Tier 2, Tier 3 and every restricted / add-one feature variant."""
    style()
    sub = robust[(robust["target"] == target) & (robust["metric"] == "mae")]
    rows = sub[(sub["analysis"] == "tier3_feature_sensitivity") & (sub["from_variant"] == "tier1")]   # all bars: same splits
    if rows.empty:
        return
    names = set(rows["to_variant"])
    order = (["tier2"] + sorted(v for v in names if v.startswith("A_")) + sorted(v for v in names if v.startswith("C_")) +
             sorted(v for v in names if v.startswith("S_")) + ["tier3"])
    order = [v for v in order if v in names]
    n_splits = int(rows["n_splits"].iloc[0])
    fig, axes = plt.subplots(1, 3, figsize=(14, 0.42 * len(order) + 1.9), sharey=True)
    for ax, alg in zip(axes, ALGS):
        part = rows[rows["algorithm"] == alg].drop_duplicates("to_variant").set_index("to_variant").reindex(order)
        y = np.arange(len(order))
        imp, lo, hi = (part[f"pooled_mean_{c}"] for c in ("improvement", "ci_low", "ci_high"))
        colors = [VARIANT_COLOR[v[:2]] if v not in ("tier2", "tier3") else VARIANT_COLOR["tier"] for v in order]
        ax.barh(y, imp, color=colors, alpha=0.9, height=0.62)
        ax.errorbar(imp, y, xerr=[(imp - lo).clip(lower=0), (hi - imp).clip(lower=0)], fmt="none", ecolor="black", elinewidth=1.1, capsize=2)
        ax.axvline(0, color="#444", lw=1)
        ax.set_title(ALG_LABEL[alg], loc="left")
        ax.set_xlabel(f"pooled MAE gain over Tier 1 ({UNIT[target]})")
        ax.xaxis.set_major_locator(plt.MaxNLocator(5))
    axes[0].set_yticks(np.arange(len(order)), [o.replace("_", " ") for o in order])
    axes[0].invert_yaxis()
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in VARIANT_COLOR.values()]
    fig.legend(handles, ["Tier 2 / Tier 3", "Tier 2 + one group (A)", "Tier 2 + site-count scalar (C)", "Tier 3 minus a group (S)"],
               loc="upper left", ncol=4, frameon=False, fontsize=8.5, bbox_to_anchor=(0.01, 1.0))
    fig.suptitle(f"{TITLE[target]}: which Tier 3 feature groups carry the effect? (same {n_splits} splits for every bar)",
                 x=0.01, ha="left", fontsize=10, fontweight="semibold", y=1.09)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
