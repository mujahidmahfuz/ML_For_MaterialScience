"""Stage 6 (SHAP interpretability + Tier 3 physics-family ablation) re-run on Analysis Dataset v1.3 for ORDERING and CURIE.

Ported from Notebook/phase6_stage6_interpretability.ipynb with the same estimator, TreeSHAP method, family map, ablation design and
paired formula bootstrap. Differences, all forced by the v1.3 target repair: populations are the v1.3 matched sets (ordering 6,061;
Curie 4,602), hyperparameters are re-selected on the frozen v1.3 matched split (Phase 6 selections belonged to the old populations),
and Ms is not recomputed (its inputs are identical; v1.2 Ms results are used only where a cross-target comparison needs them).
Outputs: EDA/10_phase7_validation/v1.3/stage6_shap/.  Run from EDA/src with OMP_NUM_THREADS unset:  python run_v13_stage6.py
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import xgboost as xgb  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

import phase6_common as pc  # noqa: E402
import phase6_interp as pi  # noqa: E402
import phase6_models as pm  # noqa: E402
import phase7_validation as p7  # noqa: E402

VERSION = "v1.3"
TARGETS = ["ordering", "curie"]
TIERS = ["tier1", "tier2", "tier3"]
MODEL = "xgboost"
CLASSES = ["FM", "AFM", "FiM", "NM"]
LABELS = list(range(len(CLASSES)))
DEP_CLASS = 0   # FM, as in Stage 6
PRIMARY = {"classification": ["macro_f1", "balanced_accuracy"], "regression": ["mae", "rmse", "r2"]}
HIGHER = {"macro_f1", "balanced_accuracy", "accuracy", "r2"}
SPLIT_FILE = {"ordering": "matched_split_ordering.csv", "curie": "matched_split_curie.csv"}
N_BOOT = 500


def short(name: str) -> str:
    return name.replace("basic_comp__", "").replace("magnetic_prior__", "")


class Run:
    """State of one v1.3 Stage 6 run (frames, selected hyperparameters, refit models)."""

    def __init__(self):
        self.cfg, self.cfg7 = p7.dataset_cfg(VERSION), p7.load_phase7_config()
        p7.install_diagnostic_algorithm()
        self.out = p7.output_dir(self.cfg7, VERSION) / "stage6_shap"
        for t in TARGETS:
            (self.out / t).mkdir(parents=True, exist_ok=True)
        self.task = {t: self.cfg["targets"][t]["task"] for t in TARGETS}
        self.cat = self.cfg["predictor_rules"]["categorical_predictors"]
        self.feats = {tr: pc.read_predictor_list(self.cfg, tr) for tr in TIERS}
        self.physics = [c for c in self.feats["tier3"] if c not in self.feats["tier2"]]
        self.fam_of = pi.family_map(self.feats["tier3"])
        self.frames, self.y, self.params, self.selection_test_pred = {}, {}, {}, {}

    def encode(self, t: str, frame: pd.DataFrame) -> np.ndarray:
        if self.task[t] == "classification":
            return frame["value"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy()
        return frame["value"].to_numpy(dtype=float)

    def load(self) -> None:
        for t in TARGETS:
            self.frames[t] = {}
            for tr in TIERS:
                cat = [c for c in self.cat if c in self.feats[tr]]
                self.frames[t][tr], _, _ = pm.load_matched_frame(self.cfg, t, tr, p7.split_dir(VERSION) / SPLIT_FILE[t], categorical=cat)
            ref = self.frames[t]["tier1"]["material_id"].to_numpy()
            assert all(np.array_equal(self.frames[t][tr]["material_id"].to_numpy(), ref) for tr in TIERS)
            self.y[t] = self.encode(t, self.frames[t]["tier1"])

    def test_idx(self, t: str) -> np.ndarray:
        return (self.frames[t]["tier1"]["split"] == "test").to_numpy()

    def select_params(self) -> None:
        """XGBoost grid per target/tier on the frozen v1.3 matched split (Phase 6 selection rule); stored for transparency."""
        rec = {}
        for t in TARGETS:
            self.params[t], rec[t] = {}, {}
            for tr in TIERS:
                cat = [c for c in self.cat if c in self.feats[tr]] or None
                res = pm.run_algorithm(self.frames[t][tr], self.feats[tr], self.y[t], self.task[t], MODEL, self.cfg,
                                       labels=LABELS if self.task[t] == "classification" else None, categorical=cat)
                self.params[t][tr] = res["best_params"]
                self.selection_test_pred[(t, tr)] = np.asarray(res["test_pred"])
                rec[t][tr] = {"selected_hyperparameters": res["best_params"], "validation_score": res["val_score"], "selection_metric": res["selection_metric"]}
        (self.out / "selected_hyperparameters_v13.json").write_text(json.dumps(rec, indent=2, default=str), encoding="utf-8")

    def fit_model(self, t: str, tier_frame: pd.DataFrame, feats: list[str], params: dict):
        cat = [c for c in self.cat if c in feats]
        tv = tier_frame["split"].isin(["train", "validation"]).to_numpy()
        est = pm.build_estimator(MODEL, self.task[t], params, self.cfg["random_seed"], categorical=cat)
        return pm.fit(est, MODEL, self.task[t], tier_frame.loc[tv, feats], self.y[t][tv])


def refit_and_shap(r: Run) -> tuple[dict, dict, dict, pd.DataFrame]:
    shap_vals, shap_bias, test_pred, rows = {}, {}, {}, []
    for t in TARGETS:
        te = r.test_idx(t)
        for tr in TIERS:
            feats = r.feats[tr]
            model = r.fit_model(t, r.frames[t][tr], feats, r.params[t][tr])
            x_te = r.frames[t][tr].loc[te, feats]
            test_pred[(t, tr)] = model.predict(x_te)
            shap_vals[(t, tr)], shap_bias[(t, tr)] = pi.tree_shap(model, x_te)
            margin = model.get_booster().predict(xgb.DMatrix(x_te, enable_categorical=True), output_margin=True)
            rows.append({"target": t, "tier": tr, "refit_equals_selection_run": bool(np.allclose(test_pred[(t, tr)], r.selection_test_pred[(t, tr)])),
                         "max_abs_shap_additivity_error": float(np.abs(shap_vals[(t, tr)].sum(axis=-1) + shap_bias[(t, tr)] - margin).max())})
            print(f"{t:<9} {tr}: additivity {rows[-1]['max_abs_shap_additivity_error']:.1e}; refit==selection {rows[-1]['refit_equals_selection_run']}", flush=True)
    return shap_vals, shap_bias, test_pred, pd.DataFrame(rows)


def importance_tables(r: Run, shap_vals: dict) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    importance, imp_rows, fam_rows = {}, [], []
    for t in TARGETS:
        for tr in TIERS:
            feats = r.feats[tr]
            imp = pi.global_importance(shap_vals[(t, tr)], feats)
            importance[(t, tr)] = imp
            rank = imp.rank(ascending=False, method="min").astype(int)
            imp_rows += [{"target": t, "tier": tr, "feature": f, "family": r.fam_of[f], "mean_abs_shap": imp[f], "share_of_total": imp[f] / imp.sum(),
                          "rank": int(rank[f])} for f in feats]
            share = pi.family_share(imp)
            fam_rows += [{"target": t, "tier": tr, "family": fam, "share": share[fam]} for fam in share.index]
    return importance, pd.DataFrame(imp_rows), pd.DataFrame(fam_rows)


def cross_target(importance: dict, out) -> pd.DataFrame:
    """Ordering vs Curie agreement on v1.3; Ms mean |SHAP| from the (unchanged) v1.2 Ms run is added for completeness."""
    ms = pd.read_csv(pc.EDA_ROOT / "07_interpretability/v1.2/ms/shap_global_importance_ms_moment.csv").set_index("feature")
    rows = []
    for tr in TIERS:
        imp = {"ordering": importance[("ordering", tr)], "curie": importance[("curie", tr)], "ms_moment_v12": ms[f"mean_abs_shap_{tr}"].dropna()}
        for a, b in [("ordering", "curie"), ("ordering", "ms_moment_v12"), ("curie", "ms_moment_v12")]:
            common = imp[a].index.intersection(imp[b].index)
            rows.append({"tier": tr, "target_a": a, "target_b": b, "n_features": len(common),
                         "spearman_importance": spearmanr(imp[a][common], imp[b][common]).statistic,
                         "top10_overlap": len(set(imp[a].nlargest(10).index) & set(imp[b].nlargest(10).index))})
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "cross_target_importance_agreement.csv", index=False, encoding="utf-8")
    return tab


def ablation(r: Run, test_pred: dict) -> pd.DataFrame:
    rows = []
    for t in TARGETS:
        te, task = r.test_idx(t), r.task[t]
        y_te, groups = r.y[t][te], r.frames[t]["tier1"].loc[te, "reduced_formula"].to_numpy()
        keys = PRIMARY[task]
        fn = (lambda a, b, w: pm.classification_metrics(a, b, LABELS, w)) if task == "classification" else (lambda a, b, w: pm.regression_metrics(a, b, w))
        preds, variants = {"tier2": test_pred[(t, "tier2")], "tier3": test_pred[(t, "tier3")]}, {}
        for fam in pi.PHYSICS_FAMILIES:
            cols = [c for c in r.physics if r.fam_of[c] == fam]
            variants[f"add|{fam}"] = r.feats["tier2"] + cols
            variants[f"drop|{fam}"] = [c for c in r.feats["tier3"] if c not in cols]
        for key, feats in variants.items():
            preds[key] = r.fit_model(t, r.frames[t]["tier3"], feats, r.params[t]["tier3"]).predict(r.frames[t]["tier3"].loc[te, feats])
            print(f"{t:<9} {key}", flush=True)
        _, samples = pm.paired_group_bootstrap(y_te, preds, groups, fn, keys, N_BOOT, r.cfg["random_seed"])
        for key in variants:
            kind, fam = key.split("|")
            ref = "tier2" if kind == "add" else "tier3"
            m_var, m_ref = pm.score(task, y_te, preds[key], LABELS), pm.score(task, y_te, preds[ref], LABELS)
            for k in keys:
                sign, direction = (1 if k in HIGHER else -1), (1 if kind == "add" else -1)
                diff = direction * sign * (np.array(samples[key][k]) - np.array(samples[ref][k]))
                lo, hi = float(np.quantile(diff, 0.025)), float(np.quantile(diff, 0.975))
                rows.append({"target": t, "analysis": "add_one_to_tier2" if kind == "add" else "drop_one_from_tier3", "physics_family": fam, "metric": k,
                             "reference_value": m_ref[k], "variant_value": m_var[k], "value_gained_by_family": direction * sign * (m_var[k] - m_ref[k]),
                             "ci_low": lo, "ci_high": hi,
                             "verdict": "stable contribution" if lo > 0 else ("stable harm" if hi < 0 else "no stable contribution")})
    return pd.DataFrame(rows)


def stability(r: Run, shap_vals: dict, importance: dict) -> pd.DataFrame:
    groups = pc.load_group_ids(r.cfg)
    cfg_s6 = pc.load_config()["stage6"]
    rows = []
    for t in TARGETS:
        te = r.test_idx(t)
        ids = r.frames[t]["tier1"].loc[te, "material_id"]
        for tr in TIERS:
            feats, vals = r.feats[tr], shap_vals[(t, tr)]
            v2 = vals[:, DEP_CLASS, :] if vals.ndim == 3 else vals
            xte = r.frames[t][tr].loc[te, feats].reset_index(drop=True)
            overall = importance[(t, tr)]
            top = list(overall[[f for f in feats if f not in r.cat]].nlargest(10).index)
            rho_all = {f: spearmanr(xte[f], v2[:, feats.index(f)], nan_policy="omit").statistic for f in top}
            for g in cfg_s6["family_groups"]:
                mask = ids.isin(groups[g]).to_numpy()
                if mask.sum() < cfg_s6["min_group_test_n"]:
                    rows.append({"target": t, "tier": tr, "group": g, "n_test": int(mask.sum()), "note": "below min_group_test_n"})
                    continue
                gi = pi.global_importance(vals[mask], feats)
                signs = []
                for f in top:
                    rr = spearmanr(xte.loc[mask, f], v2[mask, feats.index(f)], nan_policy="omit").statistic
                    if np.isfinite(rr) and np.isfinite(rho_all[f]) and abs(rho_all[f]) >= 0.1 and abs(rr) >= 0.1:
                        signs.append(np.sign(rr) == np.sign(rho_all[f]))
                rows.append({"target": t, "tier": tr, "group": g, "n_test": int(mask.sum()),
                             "importance_rank_corr_vs_all": spearmanr(gi.to_numpy(), overall.reindex(gi.index).to_numpy()).statistic,
                             "top10_overlap_with_all": len(set(gi.nlargest(10).index) & set(overall.nlargest(10).index)),
                             "top5_features": "; ".join(short(x) for x in gi.nlargest(5).index), "n_directional_features_compared": len(signs),
                             "direction_sign_agreement": float(np.mean(signs)) if signs else np.nan, "note": ""})
    return pd.DataFrame(rows)


def figures(r: Run, fam_tbl: pd.DataFrame, importance: dict, abl: pd.DataFrame) -> None:
    colors = dict(zip(pi.FAMILY_ORDER, ["#2a78d6", "#eb6834", "#7b4fc4", "#1f9d8a", "#c9a227", "#d94f8a", "#4c8c2b", "#00a3c4", "#8a5a44", "#6b7a8f", "#b3412e", "#9aa5b1"]))
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 3.6), sharex=True)
    for ax, t in zip(axes, TARGETS):
        part = fam_tbl[fam_tbl["target"] == t].pivot(index="tier", columns="family", values="share").reindex(TIERS)
        left = np.zeros(len(TIERS))
        for fam in pi.FAMILY_ORDER:
            if fam in part.columns:
                v = part[fam].fillna(0).to_numpy()
                ax.barh(range(len(TIERS)), v, left=left, color=colors[fam], label=fam, height=0.62, edgecolor="white", linewidth=0.6)
                left += v
        ax.set_yticks(range(len(TIERS)), ["Tier 1", "Tier 2", "Tier 3"])
        ax.invert_yaxis()
        ax.set_xlim(0, 1)
        ax.set_title(f"{t} (v1.3)", loc="left")
        ax.set_xlabel("share of total mean |SHAP|")
    uniq = {}
    for ax in axes:
        for h, lab in zip(*ax.get_legend_handles_labels()):
            uniq.setdefault(lab, h)
    fig.legend(list(uniq.values()), list(uniq.keys()), loc="lower center", ncol=4, fontsize=8, bbox_to_anchor=(0.5, -0.25), frameon=False)
    fig.savefig(r.out / "fig_shap_family_contribution_v13.png", bbox_inches="tight", dpi=200)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
    for ax, t in zip(axes, TARGETS):
        imp = importance[(t, "tier3")].nlargest(12)[::-1]
        ax.barh([short(f) for f in imp.index], imp.to_numpy(), color=[colors[r.fam_of[f]] for f in imp.index], height=0.7)
        ax.set_title(f"{t} · Tier 3 (v1.3)", loc="left")
        ax.set_xlabel("mean |SHAP|")
    fig.tight_layout()
    fig.savefig(r.out / "fig_shap_top_features_tier3_v13.png", bbox_inches="tight", dpi=200)
    plt.close(fig)
    pk = {"ordering": "macro_f1", "curie": "mae"}
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 6.0))
    for c, t in enumerate(TARGETS):
        for rr, kind in enumerate(["add_one_to_tier2", "drop_one_from_tier3"]):
            part = abl[(abl["target"] == t) & (abl["analysis"] == kind) & (abl["metric"] == pk[t])].set_index("physics_family").reindex(pi.PHYSICS_FAMILIES)
            y = np.arange(len(part))
            axes[rr, c].errorbar(part["value_gained_by_family"], y, xerr=[part["value_gained_by_family"] - part["ci_low"], part["ci_high"] - part["value_gained_by_family"]],
                                 fmt="o", ms=5, color="#2a78d6", elinewidth=1.5, capsize=3)
            axes[rr, c].axvline(0, color="#52514e", lw=0.9)
            axes[rr, c].set_yticks(y, [f.replace(" & ", " &\n") for f in part.index], fontsize=8)
            axes[rr, c].invert_yaxis()
            axes[rr, c].set_xlabel(f"{pk[t]} gained (positive = family helps)")
            axes[rr, c].set_title(f"{t} · " + ("Tier 2 + family" if rr == 0 else "Tier 3 minus family"), loc="left", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(r.out / "fig_tier3_physics_family_ablation_v13.png", bbox_inches="tight", dpi=200)
    plt.close(fig)


def comparison_with_v12(importance: dict, fam_tbl: pd.DataFrame, out) -> pd.DataFrame:
    """Top-5 descriptors and physics SHAP share, v1.2 (Phase 6) vs v1.3, for ordering and Curie."""
    v12_top = pd.read_csv(pc.EDA_ROOT / "07_interpretability/v1.2/shap_top10_features_by_target_tier.csv")
    v12_share = pd.read_csv(pc.EDA_ROOT / "07_interpretability/v1.2/tier3_physics_shap_share.csv").set_index("target")["ALL_PHYSICS"]
    rows = []
    for t in TARGETS:
        old = v12_top[(v12_top["target"] == t) & (v12_top["tier"] == "tier3") & (v12_top["rank"] <= 5)].sort_values("rank")["feature"].map(short).tolist()
        new = [short(f) for f in importance[(t, "tier3")].nlargest(5).index]
        ph = fam_tbl[(fam_tbl["target"] == t) & (fam_tbl["tier"] == "tier3") & fam_tbl["family"].isin(pi.PHYSICS_FAMILIES)]["share"].sum()
        rows.append({"target": t, "tier3_top5_v12": "; ".join(old), "tier3_top5_v13": "; ".join(new), "top5_overlap": len(set(old) & set(new)),
                     "physics_shap_share_v12": float(v12_share[t]), "physics_shap_share_v13": float(ph)})
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "shap_v12_vs_v13_comparison.csv", index=False, encoding="utf-8")
    return tab


def main() -> None:
    r = Run()
    r.load()
    r.select_params()
    shap_vals, shap_bias, test_pred, repro = refit_and_shap(r)
    repro.to_csv(r.out / "refit_and_additivity_check.csv", index=False, encoding="utf-8")
    for t in TARGETS:
        te = r.test_idx(t)
        r.frames[t]["tier1"].loc[te, ["material_id", "reduced_formula"]].to_csv(r.out / t / f"shap_test_material_ids_{t}.csv", index=False)
        for tr in TIERS:
            np.savez_compressed(r.out / t / f"shap_values_{t}_{tr}.npz", values=shap_vals[(t, tr)].astype(np.float32),
                                bias=np.asarray(shap_bias[(t, tr)], dtype=np.float32), features=np.array(r.feats[tr]))
    importance, imp_long, fam_tbl = importance_tables(r, shap_vals)
    imp_long.to_csv(r.out / "shap_global_importance_long.csv", index=False, encoding="utf-8")
    fam_tbl.to_csv(r.out / "shap_family_contribution_by_tier.csv", index=False, encoding="utf-8")
    cross_target(importance, r.out)
    abl = ablation(r, test_pred)
    abl.to_csv(r.out / "tier3_physics_family_ablation.csv", index=False, encoding="utf-8")
    phys = fam_tbl[(fam_tbl["tier"] == "tier3") & fam_tbl["family"].isin(pi.PHYSICS_FAMILIES)].pivot(index="target", columns="family", values="share")
    phys["ALL_PHYSICS"] = phys.sum(axis=1)
    phys.reset_index().to_csv(r.out / "tier3_physics_shap_share.csv", index=False, encoding="utf-8")
    stability(r, shap_vals, importance).to_csv(r.out / "effect_stability_across_families.csv", index=False, encoding="utf-8")
    cmp_ = comparison_with_v12(importance, fam_tbl, r.out)
    figures(r, fam_tbl, importance, abl)
    pd.set_option("display.width", 220, "display.max_colwidth", 120)
    print(cmp_.to_string(index=False))
    print(abl[abl["metric"].isin(["macro_f1", "mae"])][["target", "analysis", "physics_family", "value_gained_by_family", "ci_low", "ci_high", "verdict"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
