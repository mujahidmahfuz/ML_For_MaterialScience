"""Phase 8b repeated-split check of the AFM recall gain (ordering, dataset v1.3, Tier 1, full population).

Criterion fixed before running (see EDA/12_phase8_bias/PLAN.md, addendum): over the 10 Phase 7 split seeds (class-code stratification, as in the
XAI-stability extension), an intervention's AFM-recall gain is 'stable' if the t-interval of the per-split mean delta vs baseline excludes 0 AND
the delta is > 0 in at least 70% of splits. The overall macro-F1 and FiM-recall deltas are reported with the same statistics; offsets are fitted
on each split's own validation partition, test partitions are scored once.
Usage (from EDA/src, OMP_NUM_THREADS unset):  python run_phase8_bias_repeated.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import binomtest

import phase6_models as pm
import phase7_validation as p7
import run_phase8_bias as rb

CLASSES, N_SPLITS, MIN_FRACTION_POSITIVE = rb.CLASSES, 10, 0.70
OUT = rb.OUT / "ordering"
VARIANTS = ["baseline", "I2_provenance_weights", "I3_class_offsets", "I4_formula_weights+offsets"]


def one_split(split_id: int, cfg, cfg7, frame, feats, params, y) -> list[dict]:
    probe = pd.DataFrame({"reduced_formula": frame["reduced_formula"].to_numpy(), "value": y.astype(float)})
    labels = p7.split_labels_for(probe, cfg7, split_id)
    p7.assert_formula_disjoint(frame["reduced_formula"], labels)
    tr, va, te = labels == "train", labels == "validation", labels == "test"
    base_w = pm.compute_sample_weight("balanced", y[tr])
    weights = {"baseline": base_w, "I1": base_w * rb.formula_weights(frame.loc[tr, "reduced_formula"]),
               "I2_provenance_weights": base_w * rb.provenance_weights(frame.loc[tr, "provenance"].to_numpy())}
    p_va, p_te = {}, {}
    for name, w in weights.items():
        est = pm.build_estimator("xgboost", "classification", params, cfg["random_seed"])
        m = est.fit(frame.loc[tr, feats], y[tr], sample_weight=w * len(w) / w.sum())
        p_va[name], p_te[name] = m.predict_proba(frame.loc[va, feats]), m.predict_proba(frame.loc[te, feats])
    pred = {"baseline": p_te["baseline"].argmax(1), "I2_provenance_weights": p_te["I2_provenance_weights"].argmax(1)}
    for src, label in (("baseline", "I3_class_offsets"), ("I1", "I4_formula_weights+offsets")):
        off = rb.class_offsets(np.log(np.clip(p_va[src], 1e-9, 1)), y[va])
        pred[label] = (np.log(np.clip(p_te[src], 1e-9, 1)) + off).argmax(1)
    y_te, rows = y[te], []
    for v in VARIANTS:
        row = {"split_id": split_id, "variant": v, "n_test": int(te.sum()),
               "overall_macro_f1": pm.classification_metrics(y_te, pred[v], list(range(len(CLASSES))))["macro_f1"]}
        row.update({f"recall_{c}": float((pred[v][y_te == i] == i).mean()) if (y_te == i).any() else np.nan for i, c in enumerate(CLASSES)})
        rows.append(row)
    print(f"split {split_id}: AFM recall " + ", ".join(f"{r['variant'].split('_')[0]} {r['recall_AFM']:.3f}" for r in rows), flush=True)
    return rows


def summarise(metrics: pd.DataFrame) -> pd.DataFrame:
    base = metrics[metrics.variant == "baseline"].set_index("split_id")
    out = []
    for v in VARIANTS[1:]:
        cur = metrics[metrics.variant == v].set_index("split_id")
        for col in ["recall_AFM", "recall_FiM", "recall_FM", "recall_NM", "overall_macro_f1"]:
            d = (cur[col] - base[col]).dropna().to_numpy()
            lo, hi = p7.t_interval(d)
            pos = int((d > 0).sum())
            out.append({"variant": v, "metric": col, "n_splits": len(d), "mean_delta": d.mean(), "ci_low": lo, "ci_high": hi,
                        "fraction_splits_positive": pos / len(d), "sign_test_p": binomtest(pos, len(d), 0.5).pvalue,
                        "stable_gain": bool(lo > 0 and pos / len(d) >= MIN_FRACTION_POSITIVE)})
    return pd.DataFrame(out)


def main() -> None:
    cfg, frame, feats, params = rb.load("ordering")
    cfg7 = p7.load_phase7_config()
    y = frame["value"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(N_SPLITS):
        rows += one_split(i, cfg, cfg7, frame, feats, params, y)
        pd.DataFrame(rows).to_csv(OUT / "repeated_split_metrics.csv", index=False, encoding="utf-8")
    summary = summarise(pd.DataFrame(rows))
    summary.to_csv(OUT / "repeated_split_summary.csv", index=False, encoding="utf-8")
    pd.set_option("display.width", 220)
    print(summary.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
