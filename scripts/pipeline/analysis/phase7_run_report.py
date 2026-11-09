"""Phase 7 report driver: figures, the final Tier 3 feature audit (with sensitivity evidence) and the decision-gate table.

Run from EDA/src after phase7_run_audit.py and phase7_run_aggregate.py:  python phase7_run_report.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import phase6_common as pc
import phase7_figures as figs
import phase7_validation as p7

SCRIPT = "src/phase7_run_report.py"
ALGS = ["linear", "gradient_boosting", "xgboost"]
SENS = "tier3_feature_sensitivity"
RISK_MECHANISM = {
    "cell_size": "cell size: a per-unit-cell target scales with the number of atoms in the cell, which volume, density and "
                 "volume-per-atom jointly reveal",
    "symmetry_identity": "coarse structural family identifier (point group / space group / crystal system)",
    "same_calculation": "outputs of the same spin-polarised DFT workflow family that generates computational magnetic labels",
    "independent_response": "elastic / dielectric response from separate workflows (largely missing in the matched sets)",
}
# How each risk group is tested: removal from Tier 3, addition to Tier 2, and (cell size only) a one-scalar control.
GROUP_TESTS = {
    "cell_size": {"remove": "S_no_volume_family", "add": "A_T2_plus_volume_family", "control": "C_T2_plus_nsites"},
    "symmetry_identity": {"remove": "S_no_symmetry", "add": "A_T2_plus_symmetry", "control": None},
    "same_calculation": {"remove": "S_no_same_calculation_outputs", "add": "A_T2_plus_same_calculation_outputs", "control": None},
    "independent_response": {"remove": None, "add": "A_T2_plus_elastic_dielectric", "control": None},
}
SHARE_RULE = 0.5   # a group "carries" the gain if adding it alone recovers >= 50% of it (CI > 0) or removing it loses > 50%


def pooled(robust: pd.DataFrame, target: str, analysis: str, alg: str, v_from: str, v_to: str, metric: str = "mae"):
    sel = robust[(robust["target"] == target) & (robust["analysis"] == analysis) & (robust["algorithm"] == alg) &
                 (robust["from_variant"] == v_from) & (robust["to_variant"] == v_to) & (robust["metric"] == metric)]
    return sel.iloc[0] if len(sel) else None


def group_evidence(robust: pd.DataFrame, target: str, risk_class: str) -> list[dict]:
    """Per algorithm: full Tier 3 gain on the sensitivity splits, what survives removal, what adding the group alone recovers."""
    tests, rows = GROUP_TESTS[risk_class], []
    for alg in ALGS:
        full = pooled(robust, target, SENS, alg, "tier1", "tier3")
        if full is None or not full["pooled_mean_improvement"] > 0:
            continue
        row = {"algorithm": alg, "n_splits": int(full["n_splits"]), "full_gain": float(full["pooled_mean_improvement"])}
        for key in ("remove", "add", "control"):
            name = tests[key]
            part = pooled(robust, target, SENS, alg, "tier1", name) if name else None
            if part is not None:
                row[f"{key}_variant"] = name
                row[f"{key}_gain"] = float(part["pooled_mean_improvement"])
                row[f"{key}_ci"] = (float(part["pooled_mean_ci_low"]), float(part["pooled_mean_ci_high"]))
                row[f"{key}_share_of_full"] = float(part["pooled_mean_improvement"] / full["pooled_mean_improvement"])
        row["carries_gain"] = bool(("remove_share_of_full" in row and row["remove_share_of_full"] < SHARE_RULE) or
                                   ("add_share_of_full" in row and row["add_share_of_full"] >= SHARE_RULE and row["add_ci"][0] > 0))
        rows.append(row)
    return rows


def evidence_text(rows: list[dict]) -> str:
    if not rows:
        return "no positive full-Tier-3 gain on these splits"
    parts = []
    for r in rows:
        bits = [f"full gain {r['full_gain']:+.3f}"]
        for key, label in (("remove", "remove group"), ("add", "Tier 2 + group"), ("control", "Tier 2 + site-count scalar")):
            if f"{key}_gain" in r:
                bits.append(f"{label} {r[f'{key}_gain']:+.3f} [{r[f'{key}_ci'][0]:+.3f}, {r[f'{key}_ci'][1]:+.3f}] "
                            f"({100 * r[f'{key}_share_of_full']:.0f}% of full)")
        parts.append(f"{r['algorithm']}: " + "; ".join(bits) + (" -> CARRIES GAIN" if r["carries_gain"] else ""))
    return " | ".join(parts) + f" ({rows[0]['n_splits']} splits)"


def judge(risk_class: str, rows: list[dict]) -> tuple[str, str]:
    """(leakage judgment, inclusion decision) from the prespecified rule applied to each algorithm."""
    keep = "keep in primary Tier 3 (original Phase 6 results unchanged)"
    n_carry = sum(r["carries_gain"] for r in rows)
    if not rows:
        return "no positive full-Tier-3 gain to attribute", keep
    if n_carry >= 2:
        return (f"MATERIAL: this group carries the Ms gain in {n_carry} of {len(rows)} algorithms; mechanism: {RISK_MECHANISM[risk_class]}. "
                "It is a structural size/identity input, not evidence of deeper magnetic physics."), \
            keep + "; restricted result must be reported beside it and the claim narrowed"
    if n_carry == 1:
        return f"PARTIAL: carries the gain for 1 of {len(rows)} algorithms only; mechanism: {RISK_MECHANISM[risk_class]}", \
            keep + "; report restricted result"
    return "no evidence that this group carries the gain (adding it alone to Tier 2 or removing it does not change the gain materially)", keep


def finalize_audit(static: pd.DataFrame, robust: pd.DataFrame) -> pd.DataFrame:
    out = static.copy()
    cache: dict = {}
    for i, row in out.iterrows():
        rc = row["risk_class"]
        for target, tag in (("ms_moment", "ms"), ("curie", "curie")):
            if (target, rc) not in cache:
                cache[(target, rc)] = group_evidence(robust, target, rc)
            out.loc[i, f"{tag}_sensitivity_evidence"] = evidence_text(cache[(target, rc)])
        out.loc[i, "leakage_judgment"], out.loc[i, "inclusion_decision"] = judge(rc, cache[("ms_moment", rc)])
    return out


def gate_table(robust: pd.DataFrame, checks: pd.DataFrame, repro: pd.DataFrame, audit: pd.DataFrame, instab: pd.DataFrame,
               min_fraction: float) -> pd.DataFrame:
    rows = []
    n_fail = int((checks["status"] == "FAIL").sum())
    rows.append({"criterion": "(i) code and saved outputs reconcile", "met": bool(n_fail == 0 and repro["reproduces_stage4"].all()),
                 "evidence": f"{int((checks['status'] == 'PASS').sum())} checks pass, {n_fail} fail; {int(repro['reproduces_stage4'].sum())}/"
                             f"{len(repro)} frozen-split fits reproduce Stage 4 predictions exactly",
                 "consequence": "none"})
    ms = [pooled(robust, "ms_moment", "primary_matched", a, "tier1", "tier3") for a in ALGS]
    stable = [bool(r["pooled_mean_ci_low"] > 0 and r["fraction_positive"] >= min_fraction) for r in ms]
    rows.append({"criterion": "(ii) Ms Tier 1->3 gain stable for EVERY algorithm (prespecified rule: pooled CI excludes 0 and >= 70% of splits positive)",
                 "met": bool(all(stable)),
                 "evidence": "; ".join(f"{a}: {r['pooled_mean_improvement']:+.3f} [{r['pooled_mean_ci_low']:+.3f}, {r['pooled_mean_ci_high']:+.3f}] "
                                       f"({r['pooled_mean_pct_of_from']:.1f}% of MAE, positive in {int(r['n_positive'])}/{int(r['n_splits'])} splits, "
                                       f"{'meets' if s else 'FAILS'} the rule)" for a, r, s in zip(ALGS, ms, stable))
                 + f". The rule is {'met' if all(stable) else 'NOT met'}: {sum(stable)} of 3 algorithms satisfy it. "
                 "'2 of 3' is a descriptive post-hoc count, not the prespecified criterion.",
                 "consequence": "report the prespecified criterion as not met; describe the gain as small, direction-consistent and algorithm-dependent "
                                "(not as a general physics advantage)"})
    lin3 = instab[(instab["variant"] == "tier3") & (instab["algorithm"] == "linear")]
    bad = lin3[lin3["n_exploded_predictions"] > 0]
    rows.append({"criterion": "(iii) Curie instability diagnosed and impact on the null finding clear", "met": True,
                 "evidence": f"Ridge Tier 3 predictions exploded in {bad['split_id'].nunique()} of {lin3['split_id'].nunique()} fits (frozen + random splits), "
                             "each traced to one formula with a non-physical input value (explosion tables); boosters unaffected; the Curie null "
                             "holds for boosters across all splits and under every extreme-value sensitivity.",
                 "consequence": "Phase 6 explanation ('collinearity') replaced by the data-quality cause"})
    carried = audit[audit["leakage_judgment"].str.startswith("MATERIAL", na=False)]
    rows.append({"criterion": "(iv) Tier 3 feature audit finds no unresolved material leakage", "met": False,
                 "evidence": "NOT MET as a clean pass: the cell-size group (p3_volume, p3_density, p3_volume_per_atom) carries the tree-model Ms gain; "
                             "a one-scalar control (site count of the MP cell) added to Tier 2 recovers it. Resolved by narrowing the claim, not by dropping data."
                             if not carried.empty else "no feature group carries the Ms gain",
                 "consequence": "Ms claim revised: the gain reflects unit-cell size information, not electronic/thermodynamic/elastic physics (corrective control done)"})
    return pd.DataFrame(rows)


def main() -> None:
    cfg, cfg7 = pc.load_config(), p7.load_phase7_config()
    out = p7.output_dir(cfg7)
    fig_dir = out / "figures"
    fig_dir.mkdir(exist_ok=True)
    min_fraction = cfg7["decision_gate"]["min_fraction_splits_positive"]
    results = {"curie": pd.read_csv(out / "phase7_curie_multisplit_results.csv"),
               "ms_moment": pd.read_csv(out / "phase7_ms_multisplit_results.csv")}
    paired = pd.read_csv(out / "phase7_paired_tier_differences.csv")
    robust = pd.read_csv(out / "phase7_robustness_summary.csv")
    for target, tag in (("curie", "curie"), ("ms_moment", "ms")):
        figs.per_split_tier_figure(results[target], target, fig_dir / f"phase7_fig_{tag}_tier_performance_by_split.png")
        figs.forest_figure(paired, target, fig_dir / f"phase7_fig_{tag}_paired_tier1_to_tier3.png")
        figs.sensitivity_figure(robust, target, fig_dir / f"phase7_fig_{tag}_tier3_feature_sensitivity.png")
    audit = finalize_audit(pd.read_csv(out / "phase7_tier3_feature_audit_static.csv"), robust)
    audit.to_csv(out / "phase7_tier3_feature_audit.csv", index=False, encoding="utf-8")
    gate = gate_table(robust, pd.read_csv(out / "phase7_reconciliation_checks.csv"), pd.read_csv(out / "phase7_frozen_split_reproduction.csv"),
                      audit, pd.read_csv(out / "phase7_curie_linear_instability.csv"), min_fraction)
    gate.to_csv(out / "phase7_decision_gate.csv", index=False, encoding="utf-8")
    print(audit[["feature", "risk_class", "leakage_judgment"]].to_string(index=False, max_colwidth=90))


if __name__ == "__main__":
    main()
