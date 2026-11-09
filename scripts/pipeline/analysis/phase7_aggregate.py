"""Phase 7 aggregation: per-split metrics, paired tier differences with uncertainty, pooled and robustness summaries.

Statistics follow the protocol: every comparison uses identical test materials and the same formula-resampling draws
for both sides (paired). Three levels are reported: per split, pooled mean over splits (bootstrap over formulas), and
pooled over the concatenated test predictions; plus across-split robustness (sign counts, spread, descriptive t interval).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

import phase6_common as pc
import phase7_validation as p7

METRICS = ("mae", "rmse", "r2", "mae_formula_macro")
PRIMARY_COMPARISONS = (("tier1", "tier2"), ("tier2", "tier3"), ("tier1", "tier3"))
EXPLODE_ABS = 1.0e4   # a Curie prediction beyond +-10,000 K (observed values span 0-2,057 K) counts as numerically exploded


def split_order(sid: str) -> int:
    return -1 if sid == "frozen" else int(sid)


@dataclass
class Population:
    """Matched population of one target: ids, formulas, target values and the formula index shared by every statistic."""
    target: str
    frame: pd.DataFrame
    formulas: np.ndarray
    code_of: dict

    @classmethod
    def load(cls, cfg: dict, cfg7: dict, target: str, version: str = "v1.2") -> "Population":
        spec = cfg7["multisplit"]["targets"][target]
        split = pd.read_csv(pc.EDA_ROOT / "02_splits" / version / spec["frozen_split"], usecols=["material_id", "reduced_formula"])
        y = pc.load_target(cfg, target)[["material_id", "value"]]
        frame = split.merge(y, on="material_id", validate="one_to_one")
        formulas = np.array(sorted(frame["reduced_formula"].unique()))
        return cls(target, frame, formulas, {f: i for i, f in enumerate(formulas)})

    def codes(self, series: pd.Series) -> np.ndarray:
        return series.map(self.code_of).to_numpy()


def load_kind(work_dir, kind: str) -> pd.DataFrame:
    parts = [pd.read_parquet(p) for p in sorted(work_dir.glob(f"{kind}__*.parquet"))]
    if not parts:
        return pd.DataFrame()
    out = pd.concat(parts, ignore_index=True)
    out["split_id"] = out["split_id"].astype(str)
    return out


def load_selection(work_dir, kind: str) -> pd.DataFrame:
    parts = [pd.read_csv(p) for p in sorted(work_dir.glob(f"{kind}__*__selection.csv"))]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def keyed_stats(preds: pd.DataFrame, pop: Population, extreme_k: float | None = None) -> dict:
    """{(split_id, variant, algorithm): per-formula sufficient statistics} for the test rows of each fit."""
    out = {}
    for (sid, variant, alg), g in preds.groupby(["split_id", "variant", "algorithm"], sort=False):
        if extreme_k is not None:
            g = g[g["y_true"] <= extreme_k]
        out[(sid, variant, alg)] = p7.formula_stats(pop.codes(g["reduced_formula"]), g["y_true"].to_numpy(),
                                                    g["y_pred"].to_numpy(), len(pop.formulas))
    return out


def split_weights(stats: dict, sid: str, n_boot: int, seed: int) -> np.ndarray:
    """B x G formula-count matrix that resamples only the formulas present in this split's test set."""
    members = [v for k, v in stats.items() if k[0] == sid]
    cols = np.flatnonzero(sum(v["n"] for v in members) > 0)
    w = np.zeros((n_boot, len(members[0]["n"])))
    w[:, cols] = p7.bootstrap_weights(len(cols), n_boot, seed)
    return w


def metric_draws(st: dict, w: np.ndarray) -> tuple[dict, dict]:
    """(point estimates under unit weights, B-draw arrays under w)."""
    point = {k: float(v[0]) for k, v in p7.metrics_from_stats(st, np.ones((1, len(st["n"])))).items()}
    return point, p7.metrics_from_stats(st, w)


def per_split_rows(stats: dict, pop: Population, cfg7: dict, analysis: str, selection: pd.DataFrame,
                   counts: pd.DataFrame) -> pd.DataFrame:
    boot = cfg7["multisplit"]["bootstrap"]
    rows = []
    for si, sid in enumerate(sorted({k[0] for k in stats}, key=split_order)):
        w = split_weights(stats, sid, boot["n_resamples"], boot["seed"] + 101 * si)
        for (s, variant, alg), st in stats.items():
            if s != sid:
                continue
            point, draws = metric_draws(st, w)
            row = {"target": pop.target, "analysis": analysis, "split_id": sid, "variant": variant, "algorithm": alg,
                   "n_test": int(st["n"].sum()), "n_test_formulas": int((st["n"] > 0).sum())}
            for m in METRICS:
                lo, hi = p7.ci(draws[m], boot["ci"])
                row.update({m: point[m], f"{m}_ci_low": lo, f"{m}_ci_high": hi})
            rows.append(row)
    out = pd.DataFrame(rows).merge(counts, on="split_id", how="left")
    if not selection.empty:
        sel = selection.assign(split_id=selection["split_id"].astype(str))[["split_id", "variant", "algorithm", "val_rmse", "best_params"]]
        out = out.merge(sel, on=["split_id", "variant", "algorithm"], how="left")
    return out


def sum_stats(items: list[dict]) -> dict:
    total = items[0]
    for extra in items[1:]:
        total = p7.add_stats(total, extra)
    return total


def pooled_draws(lists: dict, metric: str, w: np.ndarray) -> dict:
    """Improvement (point, draws, from_value, to_value) for the pooled-mean-of-splits and concatenated statistics."""
    unit = np.ones((1, w.shape[1]))
    mean_draw = {n: np.mean([p7.metrics_from_stats(s, w)[metric] for s in lst], axis=0) for n, lst in lists.items()}
    mean_point = {n: float(np.mean([p7.metrics_from_stats(s, unit)[metric][0] for s in lst])) for n, lst in lists.items()}
    sums = {n: sum_stats(lst) for n, lst in lists.items()}
    cat_point = {n: float(p7.metrics_from_stats(sums[n], unit)[metric][0]) for n in sums}
    cat_draw = {n: p7.metrics_from_stats(sums[n], w)[metric] for n in sums}
    return {"pooled_mean": (p7.improvement(metric, mean_point["from"], mean_point["to"]),
                            p7.improvement(metric, mean_draw["from"], mean_draw["to"]), mean_point["from"], mean_point["to"]),
            "pooled_concat": (p7.improvement(metric, cat_point["from"], cat_point["to"]),
                              p7.improvement(metric, cat_draw["from"], cat_draw["to"]), cat_point["from"], cat_point["to"])}


def paired_row(target, analysis, scope, sid, alg, v_from, v_to, metric, from_value, to_value, imp, lo, hi, draws) -> dict:
    return {"target": target, "analysis": analysis, "scope": scope, "split_id": sid, "algorithm": alg, "from_variant": v_from,
            "to_variant": v_to, "metric": metric, "from_value": from_value, "to_value": to_value, "improvement": imp,
            "improvement_ci_low": lo, "improvement_ci_high": hi, "p_improved": float((draws > 0).mean()),
            "pct_improvement_of_from": 100 * imp / abs(from_value) if from_value else np.nan,
            "verdict": "stable improvement" if lo > 0 else ("stable degradation" if hi < 0 else "no stable change")}


def per_split_pairs(stats: dict, pop: Population, cfg7: dict, analysis: str, comparisons: list[tuple], algorithms: list[str],
                    sids: list[str]) -> list[dict]:
    boot = cfg7["multisplit"]["bootstrap"]
    rows = []
    for si, sid in enumerate(sids):
        w = split_weights(stats, sid, boot["n_resamples"], boot["seed"] + 101 * (si + 1))
        for alg in algorithms:
            for v_from, v_to in comparisons:
                if (sid, v_from, alg) not in stats or (sid, v_to, alg) not in stats:
                    continue
                pf, df_ = metric_draws(stats[(sid, v_from, alg)], w)
                pt, dt = metric_draws(stats[(sid, v_to, alg)], w)
                for m in METRICS:
                    draws = p7.improvement(m, df_[m], dt[m])
                    lo, hi = p7.ci(draws, boot["ci"])
                    rows.append(paired_row(pop.target, analysis, "per_split", sid, alg, v_from, v_to, m, pf[m], pt[m],
                                           p7.improvement(m, pf[m], pt[m]), lo, hi, draws))
    return rows


def paired_rows(stats: dict, pop: Population, cfg7: dict, analysis: str, comparisons: list[tuple], algorithms: list[str]) -> pd.DataFrame:
    """Per-split, pooled-mean and pooled-concatenated paired differences with CIs (long format); frozen split excluded."""
    boot = cfg7["multisplit"]["bootstrap"]
    sids = sorted({k[0] for k in stats if k[0] != "frozen"}, key=split_order)
    rows = per_split_pairs(stats, pop, cfg7, analysis, comparisons, algorithms, sids)
    members = [v for k, v in stats.items() if k[0] != "frozen"]
    union_cols = np.flatnonzero(sum(v["n"] for v in members) > 0)
    w_union = np.zeros((boot["n_resamples"], len(pop.formulas)))
    w_union[:, union_cols] = p7.bootstrap_weights(len(union_cols), boot["n_resamples"], boot["seed"] + 7)
    for alg in algorithms:
        for v_from, v_to in comparisons:
            lists = {"from": [stats[(s, v_from, alg)] for s in sids if (s, v_from, alg) in stats],
                     "to": [stats[(s, v_to, alg)] for s in sids if (s, v_to, alg) in stats]}
            if not lists["from"] or len(lists["from"]) != len(lists["to"]):
                continue
            for m in METRICS:
                for scope, (imp, draws, mf, mt) in pooled_draws(lists, m, w_union).items():
                    lo, hi = p7.ci(draws, boot["ci"])
                    rows.append(paired_row(pop.target, analysis, scope, "all", alg, v_from, v_to, m, mf, mt, imp, lo, hi, draws))
    return pd.DataFrame(rows)


def robustness_summary(paired: pd.DataFrame, min_fraction_positive: float) -> pd.DataFrame:
    """Across-split behaviour of the per-split improvements next to the pooled CIs (one row per comparison and metric)."""
    keys = ["target", "analysis", "algorithm", "from_variant", "to_variant", "metric"]
    pooled = {scope: paired[paired["scope"] == scope].set_index(keys) for scope in ("pooled_mean", "pooled_concat")}
    rows = []
    for key, g in paired[paired["scope"] == "per_split"].groupby(keys, sort=False):
        v = g["improvement"].to_numpy()
        lo_t, hi_t = p7.t_interval(v)
        row = dict(zip(keys, key))
        row.update({"n_splits": len(v), "mean_improvement": v.mean(), "median_improvement": float(np.median(v)),
                    "sd": float(v.std(ddof=1)) if len(v) > 1 else np.nan, "min": v.min(), "max": v.max(),
                    "n_positive": int((v > 0).sum()), "fraction_positive": float((v > 0).mean()),
                    "sign_test_p": p7.sign_test_p(int((v > 0).sum()), len(v)), "t_interval_low": lo_t, "t_interval_high": hi_t,
                    "n_splits_ci_positive": int((g["improvement_ci_low"] > 0).sum()),
                    "n_splits_ci_negative": int((g["improvement_ci_high"] < 0).sum())})
        for scope, table in pooled.items():
            if key in table.index:
                s = table.loc[key]
                row.update({f"{scope}_improvement": s["improvement"], f"{scope}_ci_low": s["improvement_ci_low"],
                            f"{scope}_ci_high": s["improvement_ci_high"], f"{scope}_pct_of_from": s["pct_improvement_of_from"],
                            f"{scope}_from_value": s["from_value"]})
        positive = row.get("pooled_mean_ci_low", -1) > 0 and row["fraction_positive"] >= min_fraction_positive
        negative = row.get("pooled_mean_ci_high", 1) < 0 and row["fraction_positive"] <= 1 - min_fraction_positive
        row["robust_verdict"] = "stable improvement" if positive else ("stable degradation" if negative else "not stable")
        rows.append(row)
    return pd.DataFrame(rows)


def split_composition_table(pop: Population, work_dir, extreme_k: float | None) -> pd.DataFrame:
    """Rows, distinct formulas and target distribution per partition for every split (section 2.A diagnostics)."""
    rows = []
    for path in sorted(work_dir.glob("labels__*.parquet")):
        sid = path.stem.split("__")[1]
        df = pop.frame.merge(pd.read_parquet(path), on="material_id", validate="one_to_one")
        rows.extend(p7.split_composition(df, df["split"].to_numpy(), sid, extreme_k))
    out = pd.DataFrame(rows)
    out["split_order"] = out["split_id"].map(split_order)
    return out.sort_values(["split_order", "partition"]).drop(columns="split_order").reset_index(drop=True)


def count_columns(comp: pd.DataFrame) -> pd.DataFrame:
    wide = comp.pivot(index="split_id", columns="partition", values=["n_rows", "n_distinct_formulas"])
    wide.columns = [f"population_{'n_rows' if a == 'n_rows' else 'n_formulas'}_{b}" for a, b in wide.columns]
    return wide.reset_index()
