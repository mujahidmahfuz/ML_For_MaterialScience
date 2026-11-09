"""Phase 7 driver for the Tier 3 feature audit (2.C) and the supporting checks (3): writes CSVs into the Phase 7 folder.

Run from EDA/src:  python phase7_run_audit.py
"""
from __future__ import annotations

import phase6_common as pc
import phase7_checks as checks
import phase7_feature_audit as audit
import phase7_validation as p7

SCRIPT = "src/phase7_run_audit.py"


def main() -> None:
    cfg, cfg7 = pc.load_config(), p7.load_phase7_config()
    out = p7.output_dir(cfg7)
    out.mkdir(parents=True, exist_ok=True)
    feature_audit, excluded = audit.build_feature_audit(cfg)
    feature_audit.to_csv(out / "phase7_tier3_feature_audit_static.csv", index=False, encoding="utf-8")
    excluded.to_csv(out / "phase7_tier3_excluded_columns.csv", index=False, encoding="utf-8")
    min_formulas = cfg7["decision_gate"]["small_subgroup_distinct_formulas_test"]
    results, tables = checks.run_all(cfg, min_formulas)
    results.to_csv(out / "phase7_reconciliation_checks.csv", index=False, encoding="utf-8")
    for name, table in tables.items():
        table.to_csv(out / f"phase7_{name}.csv", index=False, encoding="utf-8")
    for name in ["phase7_tier3_feature_audit_static.csv", "phase7_tier3_excluded_columns.csv", "phase7_reconciliation_checks.csv"]:
        pc.log_run(cfg, SCRIPT, "phase7_audit", "all", "tier3", "all", 0, (out / name).relative_to(pc.EDA_ROOT.parent))
    counts = results["status"].value_counts().to_dict()
    print(f"checks: {counts}")
    print(results[results["status"] != "PASS"].to_string(index=False))


if __name__ == "__main__":
    main()
