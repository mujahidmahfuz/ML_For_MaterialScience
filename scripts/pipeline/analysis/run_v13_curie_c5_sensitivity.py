"""Curie C5 sensitivity run: the v1.3 target WITHOUT the AFM-only-formula rule (keeps the rows C5 removed; N = 30,059 instead of 29,740).

The primary v1.3 Curie target removes formulas whose every ordering label is AFM (probable Neel temperatures). This run keeps them and repeats the
full-population Tier 1 / Tier 2 baselines (same estimators, grids, selection, metrics, bootstrap as run_v13_full_population.py), then reports the error on
the rows that only C5 removed, to show whether those rows behave differently from the rest.
Split = the v1.2 split assignment restricted to the sensitivity population (no re-splitting).
Usage (from EDA/src, OMP_NUM_THREADS unset):  python run_v13_curie_c5_sensitivity.py
Outputs: EDA/10_phase7_validation/v1.3/c5_sensitivity/{split_curie_C5.csv, c5_full_curie_metrics.csv, c5_tier2_deltas.csv, c5_only_rows_error.csv}
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import phase6_common as pc
import phase6_models as pm
import phase7_validation as p7
import run_v13_full_population as rf

SENS_FILE = "curie/target_curie_sensitivity_without_C5.csv"
N_BOOT = 300


def sensitivity_ids() -> tuple[set, set]:
    root = pc.EDA_ROOT / "datasets" / "v1.3" / "targets"
    sens = pd.read_csv(root / SENS_FILE, usecols=["material_id", "target_valid"], low_memory=False)
    prim = pd.read_csv(root / "curie/target_curie_clean.csv", usecols=["material_id", "target_valid"], low_memory=False)
    s, p = set(sens.loc[sens["target_valid"].astype(bool), "material_id"]), set(prim.loc[prim["target_valid"].astype(bool), "material_id"])
    return s, p


def write_split(sens: set, out: Path) -> Path:
    base = pd.read_csv(pc.EDA_ROOT / "02_splits" / "v1.2" / "split_curie.csv")
    kept = base[base["material_id"].isin(sens)]
    if len(kept) != len(sens):
        raise ValueError(f"{len(sens) - len(kept)} sensitivity materials have no v1.2 split assignment")
    path = out / "split_curie_C5.csv"
    kept.to_csv(path, index=False, encoding="utf-8")
    return path


def c5_only_error(cfg: dict, preds: dict, c5_ids: set, split_path: Path) -> pd.DataFrame:
    frame, _ = pm.load_modeling_frame(cfg, "curie", "tier1", split_path)
    test = frame[frame["split"] == "test"].reset_index(drop=True)
    flag = test["material_id"].isin(c5_ids).to_numpy()
    y, groups = test["value"].to_numpy(dtype=float), test["reduced_formula"].to_numpy()
    codes = pd.factorize(pd.Series(groups))[0]
    rng = np.random.default_rng(cfg["random_seed"])
    rows = []
    for name in ("tier1|dummy", "tier1|linear", "tier1|gradient_boosting", "tier1|xgboost"):
        err = np.abs(y - np.asarray(preds[name]))
        for label, mask in (("C5_only_rows", flag), ("all_other_rows", ~flag)):
            boots = []
            for _ in range(N_BOOT):
                w = np.bincount(rng.integers(0, codes.max() + 1, codes.max() + 1), minlength=codes.max() + 1)[codes] * mask
                boots.append(np.average(err, weights=w) if w.sum() > 0 else np.nan)
            rows.append({"model": name, "rows": label, "n_test": int(mask.sum()), "n_formulas": int(len(set(groups[mask]))), "mae_k": float(err[mask].mean()),
                         "ci_low": float(np.nanquantile(boots, 0.025)), "ci_high": float(np.nanquantile(boots, 0.975))})
    return pd.DataFrame(rows)


def main() -> None:
    cfg = p7.dataset_cfg("v1.3")
    p7.install_diagnostic_algorithm()
    out = pc.EDA_ROOT / "10_phase7_validation" / "v1.3" / "c5_sensitivity"
    out.mkdir(parents=True, exist_ok=True)
    sens, prim = sensitivity_ids()
    split_path = write_split(sens, out)
    cfg["targets"]["curie"]["file"], cfg["targets"]["curie"]["expected_n"] = SENS_FILE, len(sens)
    rf.SPLIT_FILE["curie"] = str(split_path)     # an absolute path replaces the split-directory join in run_v13_full_population
    print(f"sensitivity N {len(sens):,} (primary {len(prim):,}; C5-only rows {len(sens - prim):,})", flush=True)
    preds, info = rf.fit_all(cfg, "curie", "regression")
    metrics, deltas = rf.tables("curie", preds, info, cfg["random_seed"])
    metrics.to_csv(out / "c5_full_curie_metrics.csv", index=False, encoding="utf-8")
    deltas.to_csv(out / "c5_tier2_deltas.csv", index=False, encoding="utf-8")
    c5 = c5_only_error(cfg, preds, sens - prim, split_path)
    c5.to_csv(out / "c5_only_rows_error.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 220, "display.max_columns", 20)
    primary = pd.read_csv(out.parent / "v13_full_curie_metrics.csv")
    print("PRIMARY (v1.3, N=29,740)")
    print(primary.round(3).to_string(index=False))
    print("SENSITIVITY (C1-C4 only)")
    print(metrics.round(3).to_string(index=False))
    print(deltas.round(3).to_string(index=False))
    print(c5.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
