"""Stage 5 (material-family analytics) re-run on Analysis Dataset v1.3 for ORDERING and CURIE.

Ported from Notebook/phase6_stage5_material_families.ipynb: same Tier 1 predictors, algorithms/grids/selection rule, eligibility rules,
paired formula-grouped bootstrap, and the two views (general model on the family vs the rest; family-specific vs general).
The general model is refit on the v1.3 full population (the v1.2 Stage 2 predictions belong to the old targets). Ms is not recomputed:
its inputs are identical, so the v1.2 Ms rows stand. Outputs: EDA/10_phase7_validation/v1.3/stage5_families/ (resumable per fit).
Run from EDA/src with OMP_NUM_THREADS unset:  python run_v13_stage5.py
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy.stats import norm

import phase6_common as pc
import phase6_models as pm
import phase7_checks as checks
import phase7_validation as p7

VERSION = "v1.3"
TARGETS = ["ordering", "curie"]
CLASSES = ["FM", "AFM", "FiM", "NM"]
LABELS = list(range(len(CLASSES)))
PRIMARY = {"classification": ["macro_f1", "balanced_accuracy"], "regression": ["mae", "rmse", "r2"]}
HIGHER = {"macro_f1", "balanced_accuracy", "accuracy", "r2"}
REF_ALG = "xgboost"
SPLIT_FILE = {"ordering": "split_ordering.csv", "curie": "split_curie.csv"}


class Ctx:
    def __init__(self):
        self.cfg = p7.dataset_cfg(VERSION)
        p7.install_diagnostic_algorithm()
        self.s5 = self.cfg["stage5"]
        self.out = p7.output_dir(p7.load_phase7_config(), VERSION) / "stage5_families"
        self.out.mkdir(parents=True, exist_ok=True)
        self.algs = self.cfg["models"]["reduced_algorithms"]
        self.families, self.slices = self.s5["families"], self.s5["provenance_slices"]
        self.task = {t: self.cfg["targets"][t]["task"] for t in TARGETS}
        self.group_ids = pc.load_group_ids(self.cfg)
        self.feats = pc.read_predictor_list(self.cfg, self.s5["tier"])
        self.seed, self.n_boot = self.cfg["random_seed"], self.cfg["models"]["bootstrap"]["n_resamples"]

    def encode(self, t: str, frame: pd.DataFrame) -> np.ndarray:
        if self.task[t] == "classification":
            return frame["value"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy()
        return frame["value"].to_numpy(dtype=float)

    def load_frame(self, t: str) -> pd.DataFrame:
        frame, feats = pm.load_modeling_frame(self.cfg, t, self.s5["tier"], p7.split_dir(VERSION) / SPLIT_FILE[t])
        assert feats == self.feats
        return frame

    def labels(self, t: str):
        return LABELS if self.task[t] == "classification" else None


def fit_set(ctx: Ctx, t: str, frame: pd.DataFrame, path) -> pd.DataFrame:
    """Fit every algorithm on `frame` (grid on train -> validation -> refit train+val); test predictions, resumable from `path`."""
    if path.exists():
        return pd.read_csv(path)
    y = ctx.encode(t, frame)
    te = (frame["split"] == "test").to_numpy()
    out = frame.loc[te, ["material_id", "reduced_formula", "Experimental", "_source"]].reset_index(drop=True).assign(y_true=y[te])
    for a in ctx.algs:
        res = pm.run_algorithm(frame, ctx.feats, y, ctx.task[t], a, ctx.cfg, labels=ctx.labels(t))
        out[f"pred_{a}"] = np.asarray(res["test_pred"])
        out[f"params_{a}"] = str(res["best_params"])
        print(f"   {t} {path.stem}: {a} best {res['best_params']}", flush=True)
    out.to_csv(path, index=False, encoding="utf-8")
    return out


def eligibility(ctx: Ctx) -> pd.DataFrame:
    rows = []
    for t in TARGETS:
        split = pd.read_csv(p7.split_dir(VERSION) / SPLIT_FILE[t], usecols=["material_id", "split"])
        pop = split.merge(pc.load_target(ctx.cfg, t)[["material_id", "value"]], on="material_id", validate="one_to_one")
        for fam in ctx.families + ctx.slices:
            sub = pop[pop["material_id"].isin(ctx.group_ids[fam])]
            row = {"target": t, "group": fam, "kind": "family" if fam in ctx.families else "provenance_slice", "n_total": len(sub),
                   **{f"n_{s}": int((sub["split"] == s).sum()) for s in pm.SPLITS}}
            if t == "ordering":
                counts = sub["value"].value_counts().reindex(CLASSES, fill_value=0)
                tc = sub[sub["split"] == "test"]["value"].value_counts().reindex(CLASSES, fill_value=0)
                row.update({f"n_{c}": int(counts[c]) for c in CLASSES})
                row.update({f"test_n_{c}": int(tc[c]) for c in CLASSES})
                row["smallest_class_n"], row["smallest_test_class_n"] = int(counts.min()), int(tc.min())
                row["separate_model_supported"] = bool(fam in ctx.families and len(sub) >= ctx.s5["min_total_n"] and counts.min() >= ctx.s5["min_class_n"]
                                                       and tc.min() >= ctx.s5["min_test_n_per_class"])
            else:
                row["separate_model_supported"] = bool(fam in ctx.families and len(sub) >= ctx.s5["min_total_n"])
            rows.append(row)
    return pd.DataFrame(rows)


def labels_present(y: np.ndarray) -> list[int]:
    return [c for c in LABELS if (y == c).any()]


def make_fn(task: str, y: np.ndarray, mask: np.ndarray):
    if task == "classification":
        labels = labels_present(y[mask])
        return lambda a, b, w: pm.classification_metrics(a[mask], b[mask], labels, w[mask])
    return lambda a, b, w: pm.regression_metrics(a[mask], b[mask], w[mask])


def evaluate_target(ctx: Ctx, t: str, general: pd.DataFrame, fam_preds: dict) -> tuple[list, list, list, list]:
    task, y = ctx.task[t], general["y_true"].to_numpy()
    groups, keys = general["reduced_formula"].to_numpy(), PRIMARY[task]
    ones = np.ones(len(general))
    gen = {a: general[f"pred_{a}"].to_numpy() for a in ctx.algs}
    cis_all, _ = pm.paired_group_bootstrap(y, gen, groups, make_fn(task, y, np.ones(len(general), dtype=bool)), keys, ctx.n_boot, ctx.seed)
    metrics = [{"target": t, "scope": "general_overall", "group": "ALL", "algorithm": a, "n_test": len(general),
                **{f"test_{k}": v for k, v in pm.score(task, y, gen[a], LABELS).items()},
                **{f"test_{k}_ci_{s}": cis_all[a][k][i] for k in keys for i, s in enumerate(("low", "high"))}} for a in ctx.algs]
    deltas, gaps, per_class = [], [], []
    for fam in ctx.families + ctx.slices:
        mask = general["material_id"].isin(ctx.group_ids[fam]).to_numpy()
        rest = ~mask
        if mask.sum() < 30:
            continue
        fn_in, fn_out = make_fn(task, y, mask), make_fn(task, y, rest)
        preds_in = {f"general|{a}": gen[a] for a in ctx.algs}
        spec = fam_preds.get((t, fam))
        if spec is not None:
            sp = spec.set_index("material_id")
            for a in ctx.algs:
                col = np.zeros(len(general), dtype=gen[a].dtype)
                col[mask] = sp.loc[general.loc[mask, "material_id"], f"pred_{a}"].to_numpy()
                preds_in[f"specific|{a}"] = col
        cis_in, samp_in = pm.paired_group_bootstrap(y, preds_in, groups, fn_in, keys, ctx.n_boot, ctx.seed)
        has_rest = rest.sum() >= 30
        if has_rest:
            cis_out, samp_out = pm.paired_group_bootstrap(y, gen, groups, fn_out, keys, ctx.n_boot, ctx.seed)
        for key, pred in preds_in.items():
            scope, a = key.split("|")
            metrics.append({"target": t, "scope": f"{scope}_on_" + ("family" if fam in ctx.families else "slice"), "group": fam, "algorithm": a,
                            "n_test": int(mask.sum()), **{f"test_{k}": v for k, v in fn_in(y, pred, ones).items()},
                            **{f"test_{k}_ci_{s}": cis_in[key][k][i] for k in keys for i, s in enumerate(("low", "high"))}})
        for a in ctx.algs:
            m_in = fn_in(y, gen[a], ones)
            if has_rest:
                m_out = fn_out(y, gen[a], ones)
                for k in keys:
                    sign = 1 if k in HIGHER else -1
                    s = sign * (np.array(samp_out[a][k]) - np.array(samp_in[f"general|{a}"][k]))
                    lo, hi = float(np.quantile(s, 0.025)), float(np.quantile(s, 0.975))
                    gaps.append({"target": t, "group": fam, "algorithm": a, "metric": k, "family_value": m_in[k], "rest_value": m_out[k],
                                 "gap_worse_on_family": sign * (m_out[k] - m_in[k]), "gap_ci_low": lo, "gap_ci_high": hi,
                                 "verdict": "worse on family" if lo > 0 else ("better on family" if hi < 0 else "no stable difference")})
            if spec is not None:
                m_sp = fn_in(y, preds_in[f"specific|{a}"], ones)
                for k in keys:
                    sign = 1 if k in HIGHER else -1
                    imp = sign * (np.array(samp_in[f"specific|{a}"][k]) - np.array(samp_in[f"general|{a}"][k]))
                    lo, hi = float(np.quantile(imp, 0.025)), float(np.quantile(imp, 0.975))
                    deltas.append({"target": t, "group": fam, "algorithm": a, "metric": k, "general_value": m_in[k], "specific_value": m_sp[k],
                                   "improvement": sign * (m_sp[k] - m_in[k]), "improvement_ci_low": lo, "improvement_ci_high": hi,
                                   "p_improved": float((imp > 0).mean()),
                                   "verdict": "stable improvement" if lo > 0 else ("stable degradation" if hi < 0 else "no stable change")})
        if task == "classification":
            for scope in ["general"] + (["specific"] if spec is not None else []):
                per_class.append(pm.per_class_table(y[mask], preds_in[f"{scope}|{REF_ALG}"][mask], LABELS, CLASSES).assign(scope=scope, group=fam, target=t))
        print(f"{t:<9} {fam:<17} test N {int(mask.sum()):>6} | separate model: {spec is not None}", flush=True)
    return metrics, deltas, gaps, per_class


def multiplicity(deltas: pd.DataFrame) -> pd.DataFrame:
    d = deltas[deltas["metric"] == deltas["target"].map(lambda t: "macro_f1" if t == "ordering" else "mae")].copy()
    se = ((d["improvement_ci_high"] - d["improvement_ci_low"]) / (2 * 1.96)).clip(lower=1e-12)
    d["approx_p_two_sided"] = np.clip(2 * norm.sf(np.abs(d["improvement"] / se)), 1e-12, 1.0)
    d = pd.concat([d, checks.holm_and_bh(d["approx_p_two_sided"])], axis=1)
    d["stable_unadjusted"] = d["verdict"] != "no stable change"
    d["stable_after_holm_005"], d["stable_after_bh_005"] = d["p_holm"] < 0.05, d["q_bh"] < 0.05
    return d


def comparison_with_v12(deltas: pd.DataFrame, out) -> pd.DataFrame:
    old = pd.read_csv(pc.EDA_ROOT / "06_material_groups/v1.2/family_specific_vs_general_deltas.csv")
    pick = lambda d, t: d[(d["target"] == t) & (d["algorithm"] == REF_ALG) & (d["metric"] == ("macro_f1" if t == "ordering" else "mae"))].set_index("group")   # noqa: E731
    rows = []
    for t in TARGETS:
        o, n = pick(old, t), pick(deltas, t)
        for g in n.index:
            rows.append({"target": t, "group": g, "improvement_v12": o["improvement"].get(g, np.nan), "verdict_v12": o["verdict"].get(g, "n/a"),
                         "improvement_v13": n.loc[g, "improvement"], "verdict_v13": n.loc[g, "verdict"]})
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "family_v12_vs_v13_comparison.csv", index=False, encoding="utf-8")
    return tab


def fit_one(ctx: Ctx, target: str, group: str) -> None:
    """Low-memory mode: fit ONE prediction set (the general model or one family) in this process, save it, exit."""
    frame = ctx.load_frame(target)
    if group == "general":
        fit_set(ctx, target, frame, ctx.out / f"general_predictions_{target}.csv")
    else:
        sub = frame[frame["material_id"].isin(ctx.group_ids[group])].reset_index(drop=True)
        fit_set(ctx, target, sub, ctx.out / f"family_predictions_{target}_{group.replace(' ', '_')}.csv")
    print(f"[done] {target} / {group}", flush=True)


def main() -> None:
    ctx = Ctx()
    if "--fit" in sys.argv:   # python run_v13_stage5.py --fit ordering "Rare Earth"
        i = sys.argv.index("--fit")
        fit_one(ctx, sys.argv[i + 1], sys.argv[i + 2])
        return
    elig = eligibility(ctx)
    elig.to_csv(ctx.out / "family_eligibility.csv", index=False, encoding="utf-8")
    general, fam_preds = {}, {}
    for t in TARGETS:
        frame = ctx.load_frame(t)
        general[t] = fit_set(ctx, t, frame, ctx.out / f"general_predictions_{t}.csv")
        for fam in ctx.families:
            ok = bool(elig[(elig["target"] == t) & (elig["group"] == fam)]["separate_model_supported"].iloc[0])
            if not ok:
                print(f"{t:<9} {fam:<17} separate model NOT supported -> general model evaluated on this family", flush=True)
                continue
            sub = frame[frame["material_id"].isin(ctx.group_ids[fam])].reset_index(drop=True)
            fam_preds[(t, fam)] = fit_set(ctx, t, sub, ctx.out / f"family_predictions_{t}_{fam.replace(' ', '_')}.csv")
        del frame
    metrics, deltas, gaps, per_class = [], [], [], []
    for t in TARGETS:
        m, d, g, p = evaluate_target(ctx, t, general[t], fam_preds)
        metrics += m
        deltas += d
        gaps += g
        per_class += p
    pd.DataFrame(metrics).to_csv(ctx.out / "family_metrics.csv", index=False, encoding="utf-8")
    dl = pd.DataFrame(deltas)
    dl.to_csv(ctx.out / "family_specific_vs_general_deltas.csv", index=False, encoding="utf-8")
    pd.DataFrame(gaps).to_csv(ctx.out / "family_vs_rest_gap.csv", index=False, encoding="utf-8")
    pd.concat(per_class, ignore_index=True).to_csv(ctx.out / "family_ordering_per_class.csv", index=False, encoding="utf-8")
    mult = multiplicity(dl)
    mult.to_csv(ctx.out / "family_multiplicity.csv", index=False, encoding="utf-8")
    cmp_ = comparison_with_v12(dl, ctx.out)
    pd.set_option("display.width", 220)
    print(cmp_.round(3).to_string(index=False))
    print(f"multiplicity (primary metric, ordering+curie): {len(mult)} comparisons; stable unadjusted {int(mult['stable_unadjusted'].sum())}, "
          f"Holm {int(mult['stable_after_holm_005'].sum())}, BH {int(mult['stable_after_bh_005'].sum())}")


if __name__ == "__main__":
    main()
