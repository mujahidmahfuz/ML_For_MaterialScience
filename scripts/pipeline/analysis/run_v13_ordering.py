"""Ordering experiments on Analysis Dataset v1.3 (Phase 7 review item R2): corrected baseline, provenance slices,
cross-provenance transfer, and the matched Tier 1/2/3 + 'same-calculation' leakage test over repeated formula-grouped splits.

Run from EDA/src (leave OMP_NUM_THREADS unset):
    python run_v13_ordering.py baseline | slices | transfer | matched --splits frozen 0 1 ... [--variants ...]
Outputs: EDA/10_phase7_validation/v1.3/ordering_*.csv and work/ordering/*.parquet
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

import phase6_models as pm
import phase7_validation as p7

CLASSES = ["FM", "AFM", "FiM", "NM"]
LABELS = list(range(len(CLASSES)))
ALGS = ["linear", "gradient_boosting", "xgboost"]
MATCHED_KEY_VARIANTS = ["tier1", "tier2", "tier3", "S_no_same_calculation_outputs", "S_no_symmetry", "A_T2_plus_same_calculation_outputs",
                        "A_T2_plus_symmetry"]
VERSION = "v1.3"


def setup():
    cfg, cfg7 = p7.dataset_cfg(VERSION), p7.load_phase7_config()
    p7.install_diagnostic_algorithm()   # also pins XGBoost to p7.XGB_N_JOBS threads (thread-count-dependent results)
    out = p7.output_dir(cfg7, VERSION)
    (out / "work" / "ordering").mkdir(parents=True, exist_ok=True)
    return cfg, cfg7, out


def encode(frame: pd.DataFrame) -> np.ndarray:
    return frame["value"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy()


def fit_predict(frame: pd.DataFrame, labels: np.ndarray, features: list[str], alg: str, cfg: dict, y: np.ndarray,
                categorical: list[str] | None = None) -> np.ndarray:
    """Grid on train -> best validation macro-F1 -> refit train+validation -> test predictions (Phase 6 selection rule)."""
    res = pm.run_algorithm(frame.assign(split=labels), features, y, "classification", alg, cfg, labels=LABELS, categorical=categorical)
    return np.asarray(res["test_pred"])


def baseline(cfg: dict, out) -> None:
    """Full v1.3 ordering population, Tier 1, frozen v1.3 split; dummy + the three reduced algorithms."""
    frame, feats = pm.load_modeling_frame(cfg, "ordering", "tier1", p7.split_dir(VERSION) / "split_ordering.csv")
    y = encode(frame)
    te = (frame["split"] == "test").to_numpy()
    preds = {a: fit_predict(frame, frame["split"].to_numpy(), feats, a, cfg, y) for a in ["dummy"] + ALGS}
    fn = lambda yy, pp, w: pm.classification_metrics(yy, pp, LABELS, w)   # noqa: E731
    cis, _ = pm.paired_group_bootstrap(y[te], preds, frame.loc[te, "reduced_formula"].to_numpy(), fn, ["macro_f1", "balanced_accuracy"], 500,
                                       cfg["random_seed"])
    rows = [{"algorithm": a, "n_test": int(te.sum()), **pm.classification_metrics(y[te], p, LABELS),
             "macro_f1_ci_low": cis[a]["macro_f1"][0], "macro_f1_ci_high": cis[a]["macro_f1"][1]} for a, p in preds.items()]
    pd.DataFrame(rows).to_csv(out / "ordering_v13_baseline_metrics.csv", index=False, encoding="utf-8")
    pd.concat([pm.per_class_table(y[te], p, LABELS, CLASSES).assign(algorithm=a) for a, p in preds.items()]).to_csv(
        out / "ordering_v13_baseline_per_class.csv", index=False, encoding="utf-8")
    print(pd.DataFrame(rows).round(3).to_string(index=False))


def provenance(frame: pd.DataFrame) -> np.ndarray:
    return np.where(frame["_source"].astype(str).str.startswith("mp_reformatted"), "computational_MP", "experimental")


def slices(cfg: dict, out) -> None:
    """Separate models trained and tested inside each provenance slice (frozen v1.3 split restricted to the slice)."""
    frame, feats = pm.load_modeling_frame(cfg, "ordering", "tier1", p7.split_dir(VERSION) / "split_ordering.csv")
    prov = provenance(frame)
    rows = []
    for name in ("computational_MP", "experimental"):
        sub = frame[prov == name].reset_index(drop=True)
        ys = encode(sub)
        te = (sub["split"] == "test").to_numpy()
        present = sorted(set(ys[te]))
        for a in ALGS:
            p = fit_predict(sub, sub["split"].to_numpy(), feats, a, cfg, ys)
            rows.append({"slice": name, "algorithm": a, "n_rows": len(sub), "n_test": int(te.sum()), "classes_in_test": "/".join(CLASSES[i] for i in present),
                         **{f"class_{c}_n": int((sub["value"] == c).sum()) for c in CLASSES}, **pm.classification_metrics(ys[te], p, present)})
    pd.DataFrame(rows).to_csv(out / "ordering_v13_provenance_slices.csv", index=False, encoding="utf-8")
    print(pd.DataFrame(rows).round(3).to_string(index=False))


def transfer(cfg: dict, out) -> None:
    """Train on one provenance, test on the other; training formulas that occur in the test rows are removed (no leakage)."""
    frame, feats = pm.load_modeling_frame(cfg, "ordering", "tier1", p7.split_dir(VERSION) / "split_ordering.csv")
    y, prov = encode(frame), provenance(frame)
    rows = []
    for src, dst in (("computational_MP", "experimental"), ("experimental", "computational_MP")):
        test_mask = (prov == dst) & (frame["split"] == "test").to_numpy()
        train_mask = (prov == src) & ~frame["reduced_formula"].isin(set(frame.loc[test_mask, "reduced_formula"])).to_numpy()
        val_mask = train_mask & (frame["split"] == "validation").to_numpy()
        counts = np.bincount(y[train_mask], minlength=len(CLASSES))
        seen = {i for i in LABELS if counts[i] >= 100}   # a class with < 100 training rows (e.g. 5 NM rows in the experimental data) is 'unseen'
        dropped = int((test_mask & ~np.isin(y, list(seen))).sum())   # test rows of a class absent from training cannot be predicted: not scored
        test_mask = test_mask & np.isin(y, list(seen))
        labels = np.where(test_mask, "test", np.where(val_mask, "validation", np.where(train_mask, "train", "unused")))
        keep = labels != "unused"
        sub, lab, ys = frame[keep].reset_index(drop=True), labels[keep], y[keep]
        present = sorted(set(ys[lab == "test"]))
        for a in ["dummy"] + ALGS:
            p = fit_predict(sub, lab, feats, a, cfg, ys)
            rows.append({"train_on": src, "test_on": dst, "algorithm": a, "n_train": int((lab == "train").sum()), "n_test": int((lab == "test").sum()),
                         "n_test_rows_dropped_class_unseen_in_training": dropped, "classes_scored": "/".join(CLASSES[i] for i in present),
                         **pm.classification_metrics(ys[lab == "test"], p, present)})
    pd.DataFrame(rows).to_csv(out / "ordering_v13_cross_provenance_transfer.csv", index=False, encoding="utf-8")
    print(pd.DataFrame(rows).round(3).to_string(index=False))


def matched(cfg: dict, cfg7: dict, out, split_ids: list[str], variants: list[str] | None) -> None:
    """Matched Tier 1/2/3 (+ same-calculation tests) on the v1.3 matched ordering population, one parquet per split."""
    categorical = cfg["predictor_rules"]["categorical_predictors"]
    frame, _, _ = pm.load_matched_frame(cfg, "ordering", "tier3", p7.split_dir(VERSION) / "matched_split_ordering.csv", categorical)
    y = encode(frame)
    allv = p7.variant_features(cfg, cfg7)
    use = {v: allv[v] for v in (variants or MATCHED_KEY_VARIANTS)}
    ms = cfg7["multisplit"]
    for sid in split_ids:
        path = out / "work" / "ordering" / f"matched__{sid}.parquet"
        if path.exists():
            continue
        labels = frame["split"].to_numpy() if sid == "frozen" else p7.random_group_split(
            frame["reduced_formula"], y, ms["fractions"], p7.split_seed(cfg7, int(sid)), ms["n_strata_bins"], ms["capacity_tolerance"])
        p7.assert_formula_disjoint(frame["reduced_formula"], labels)
        te = labels == "test"
        rows = []
        for v, feats in use.items():
            cats = [c for c in categorical if c in feats] or None
            for a in ALGS:
                rows.append(pd.DataFrame({"split_id": sid, "variant": v, "algorithm": a, "material_id": frame.loc[te, "material_id"].to_numpy(),
                                          "reduced_formula": frame.loc[te, "reduced_formula"].to_numpy(), "y_true": y[te],
                                          "y_pred": fit_predict(frame, labels, feats, a, cfg, y, cats)}))
        pd.concat(rows).to_parquet(path)
        print(f"[done] ordering matched split={sid}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("task", choices=["baseline", "slices", "transfer", "matched"])
    ap.add_argument("--splits", nargs="+", default=["frozen"])
    ap.add_argument("--variants", nargs="+", default=None)
    args = ap.parse_args()
    cfg, cfg7, out = setup()
    if args.task == "baseline":
        baseline(cfg, out)
    elif args.task == "slices":
        slices(cfg, out)
    elif args.task == "transfer":
        transfer(cfg, out)
    else:
        matched(cfg, cfg7, out, args.splits, args.variants)


if __name__ == "__main__":
    main()
