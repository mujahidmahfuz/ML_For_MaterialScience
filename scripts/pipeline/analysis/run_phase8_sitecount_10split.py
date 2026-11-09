"""Site-count control for the Ms-per-cell Tier 3 gain, aggregated over ALL 10 Phase 7 splits (Phase 7 had it on splits 0-4 only).

Control fit = Tier 2 + ONE derived scalar, the number of sites in the Materials Project cell (p3_volume / p3_volume_per_atom). If the scalar recovers the
Tier 3 gain on every algorithm over 10 splits, the earlier "cell-size explains it" conclusion stands on the full prespecified split set.
Run after: python run_phase7_multisplit.py --target ms_moment --splits 5 6 7 8 9 --kinds control
Usage (from EDA/src):  python run_phase8_sitecount_10split.py
Outputs: EDA/10_phase7_validation/v1.2/phase8_sitecount_control_10splits_{paired,robustness}.csv
"""
from __future__ import annotations

import pandas as pd

import phase7_aggregate as agg
import phase7_validation as p7

CONTROL = "C_T2_plus_nsites"
COMPARISONS = [("tier1", "tier3"), ("tier2", "tier3"), ("tier1", "tier2"), ("tier2", CONTROL), ("tier1", CONTROL), (CONTROL, "tier3")]


def main() -> None:
    cfg, cfg7 = p7.dataset_cfg("v1.2"), p7.load_phase7_config()
    out = p7.output_dir(cfg7, "v1.2")
    work = out / "work" / "ms_moment"
    pop = agg.Population.load(cfg, cfg7, "ms_moment", "v1.2")
    main_preds, control = agg.load_kind(work, "main"), agg.load_kind(work, "control")
    ids = sorted(set(control["split_id"]) & set(main_preds["split_id"]), key=agg.split_order)
    print(f"splits with the control: {ids}", flush=True)
    both = pd.concat([main_preds[main_preds["split_id"].isin(ids)], control[control["split_id"].isin(ids)]], ignore_index=True)
    stats = agg.keyed_stats(both, pop)
    algorithms = cfg7["multisplit"]["algorithms"]
    paired = agg.paired_rows(stats, pop, cfg7, "sitecount_control_all_splits", COMPARISONS, algorithms)
    robust = agg.robustness_summary(paired, cfg7["decision_gate"]["min_fraction_splits_positive"])
    paired.to_csv(out / "phase8_sitecount_control_10splits_paired.csv", index=False, encoding="utf-8")
    robust.to_csv(out / "phase8_sitecount_control_10splits_robustness.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 230, "display.max_columns", 30)
    print(robust.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
