"""Phase 8 leave-chemical-system-out test: does skill survive when whole chemical systems (sorted element sets, e.g. Fe-O) are unseen?

Formula-grouped splits (Phase 6/7) keep Fe2O3 out of the training set when Fe2O3 is in test, but Fe3O4 (same Fe-O system) may be in training. For each of the
10 Phase 7 split seeds the same size-aware, target-stratified random_group_split is run twice on the same population: (a) groups = reduced_formula
(the reference scheme), (b) groups = chemical system. XGBoost (selected hyperparameters, no tuning) is fitted on train+validation and scored on the test
partition. Paired per-split deltas (chemsys - formula) get t-intervals; a degradation is called 'stable' if the interval excludes 0 and it is worse in
>= 70% of splits (same rule family as Phase 7). Tier 1 only. Usage (from EDA/src, OMP_NUM_THREADS unset):  python run_phase8_leave_chemsys.py <curie|ordering|ms_moment>
Outputs: EDA/13_phase8_leave_chemsys/<target>/leave_chemsys_metrics.csv and leave_chemsys_summary.csv
"""
from __future__ import annotations

import ast
import sys

import numpy as np
import pandas as pd
from pymatgen.core import Composition

import phase6_common as pc
import phase6_models as pm
import phase7_validation as p7
import run_phase8_regression_uq as ru

OUT = pc.EDA_ROOT / "13_phase8_leave_chemsys"
N_SPLITS, MIN_FRACTION_WORSE = 10, 0.70
CLASSES = ["FM", "AFM", "FiM", "NM"]
LOWER_IS_BETTER = ("mae", "rmse")
SETUP = {"curie": {"version": "v1.3", "split": "split_curie.csv", "task": "regression"},
         "ordering": {"version": "v1.3", "split": "split_ordering.csv", "task": "classification"},
         "ms_moment": {"version": "v1.2", "split": "split_ms.csv", "task": "regression"}}


def chemical_system(formula: str) -> str:
    return "-".join(sorted(el.symbol for el in Composition(formula).elements))


def load(target: str):
    spec = SETUP[target]
    cfg = p7.dataset_cfg(spec["version"])
    frame, feats = pm.load_modeling_frame(cfg, target, "tier1", p7.split_dir(spec["version"]) / spec["split"])
    frame = frame.reset_index(drop=True)
    unique = frame["reduced_formula"].drop_duplicates()
    frame["chemsys"] = frame["reduced_formula"].map(dict(zip(unique, unique.map(chemical_system))))
    if spec["task"] == "classification":
        y = frame["value"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy()
        row = pd.read_csv(pc.EDA_ROOT / "10_phase7_validation/v1.3/stage5_families/general_predictions_ordering.csv", nrows=1)
        params = ast.literal_eval(row["params_xgboost"].iloc[0])
    else:
        y, params = frame["value"].to_numpy(dtype=float), ru.xgb_params(target)
    return cfg, spec["task"], frame, feats, y, params


def run_scheme(scheme: str, split_id: int, cfg, cfg7, task, frame, feats, y, params) -> dict:
    ms = cfg7["multisplit"]
    groups = frame["reduced_formula"] if scheme == "formula" else frame["chemsys"]
    labels = p7.random_group_split(groups, y.astype(float), ms["fractions"], p7.split_seed(cfg7, split_id), ms["n_strata_bins"], ms["capacity_tolerance"])
    p7.assert_formula_disjoint(groups, labels)
    trval, te = np.isin(labels, ["train", "validation"]), labels == "test"
    est = pm.build_estimator("xgboost", task, params, cfg["random_seed"])
    model = pm.fit(est, "xgboost", task, frame.loc[trval, feats], y[trval])
    pred = model.predict(frame.loc[te, feats])
    row = {"split_id": split_id, "scheme": scheme, "n_trainval": int(trval.sum()), "n_test": int(te.sum()), "test_fraction": te.mean(),
           "n_test_chemsys": int(frame.loc[te, "chemsys"].nunique()),
           "test_rows_with_chemsys_in_train": float(frame.loc[te, "chemsys"].isin(set(frame.loc[trval, "chemsys"])).mean())}
    if task == "classification":
        row.update(pm.classification_metrics(y[te], pred, list(range(len(CLASSES)))))
        row.update({f"recall_{c}": float((pred[y[te] == i] == i).mean()) if (y[te] == i).any() else np.nan for i, c in enumerate(CLASSES)})
    else:
        row.update(pm.regression_metrics(y[te], pred))
    return row


def summarise(df: pd.DataFrame, task: str) -> pd.DataFrame:
    metrics = ["macro_f1", "balanced_accuracy", "recall_AFM", "recall_FiM", "recall_FM", "recall_NM"] if task == "classification" else ["mae", "rmse", "r2"]
    ref, new = df[df.scheme == "formula"].set_index("split_id"), df[df.scheme == "chemsys"].set_index("split_id")
    out = []
    for m in metrics:
        d = (new[m] - ref[m]).dropna().to_numpy()
        lo, hi = p7.t_interval(d)
        lower_better = m in LOWER_IS_BETTER
        worse = float((d > 0).mean() if lower_better else (d < 0).mean())
        stable = bool((lo > 0 if lower_better else hi < 0) and worse >= MIN_FRACTION_WORSE)
        out.append({"metric": m, "formula_grouped_mean": ref[m].mean(), "chemsys_grouped_mean": new[m].mean(), "mean_delta": d.mean(), "ci_low": lo, "ci_high": hi,
                    "fraction_splits_worse": worse, "stable_degradation": stable, "n_splits": len(d)})
    return pd.DataFrame(out)


def main() -> None:
    target = sys.argv[1]
    p7.install_diagnostic_algorithm()
    cfg7 = p7.load_phase7_config()
    cfg, task, frame, feats, y, params = load(target)
    out = OUT / target
    out.mkdir(parents=True, exist_ok=True)
    print(f"{target}: {len(frame)} rows, {frame['reduced_formula'].nunique()} formulas, {frame['chemsys'].nunique()} chemical systems", flush=True)
    rows = []
    key = "macro_f1" if task == "classification" else "mae"
    for i in range(N_SPLITS):
        for scheme in ("formula", "chemsys"):
            rows.append(run_scheme(scheme, i, cfg, cfg7, task, frame, feats, y, params))
        print(f"split {i}: {key} formula {rows[-2][key]:.3f} vs chemsys {rows[-1][key]:.3f}; test rows sharing a system with train: "
              f"{rows[-2]['test_rows_with_chemsys_in_train']:.2f} vs {rows[-1]['test_rows_with_chemsys_in_train']:.2f}; test fraction {rows[-1]['test_fraction']:.2f}", flush=True)
        pd.DataFrame(rows).to_csv(out / "leave_chemsys_metrics.csv", index=False, encoding="utf-8")
    summary = summarise(pd.DataFrame(rows), task)
    summary.to_csv(out / "leave_chemsys_summary.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 220)
    print(summary.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
