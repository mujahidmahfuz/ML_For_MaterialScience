"""Phase 7 section 2.A: diagnose the unstable linear (Ridge) Tier 3 estimates on the matched Curie experiment.

1. instability_table: per split x tier, how often the Ridge predictions leave any physically possible range.
2. explain_explosions: refit the selected Ridge for each affected split and attribute every exploded prediction to the
   features that carry it (coefficient x standardised value), so the cause is a named column, not a guess.
"""
from __future__ import annotations

import ast

import numpy as np
import pandas as pd

import phase6_models as pm
import phase7_aggregate as agg
import phase7_validation as p7


def instability_table(preds: pd.DataFrame, threshold: float = agg.EXPLODE_ABS) -> pd.DataFrame:
    """One row per split x variant x linear algorithm: error and prediction-range summary."""
    sub = preds[preds["algorithm"].isin(["linear", p7.LINEAR_CLIP])]
    rows = []
    for (sid, variant, alg), g in sub.groupby(["split_id", "variant", "algorithm"], sort=False):
        err = g["y_pred"] - g["y_true"]
        bad = g["y_pred"].abs() > threshold
        rows.append({"split_id": sid, "variant": variant, "algorithm": alg, "n_test": len(g), "mae": float(err.abs().mean()),
                     "median_ae": float(err.abs().median()), "max_abs_prediction": float(g["y_pred"].abs().max()),
                     "n_exploded_predictions": int(bad.sum()), "n_exploded_formulas": int(g.loc[bad, "reduced_formula"].nunique()),
                     "exploded_beyond_k": threshold})
    out = pd.DataFrame(rows)
    out["order"] = out["split_id"].map(agg.split_order)
    return out.sort_values(["order", "variant", "algorithm"]).drop(columns="order").reset_index(drop=True)


def fit_selected_ridge(frame: pd.DataFrame, labels: np.ndarray, features: list[str], params: dict, seed: int,
                       categorical: list[str]):
    train_val = labels != "test"
    est = pm.build_estimator("linear", "regression", params, seed, categorical)
    est.fit(frame.loc[train_val, features], frame.loc[train_val, "value"].to_numpy(dtype=float))
    return est


def explain_split(est, frame: pd.DataFrame, labels: np.ndarray, features: list[str], sid: str, threshold: float,
                  top: int = 3) -> list[dict]:
    test = labels == "test"
    x_test = frame.loc[test, features]
    meta_test = frame.loc[test].reset_index(drop=True)
    pred = est.predict(x_test)
    bad = np.flatnonzero(np.abs(pred) > threshold)
    if not len(bad):
        return []
    pre, model = est.named_steps["pre"], est.named_steps["model"]
    names = np.array([n.split("__", 1)[-1] for n in pre.get_feature_names_out()])
    xt = np.asarray(pre.transform(x_test.iloc[bad]))
    contrib = xt * model.coef_
    rows = []
    for i, j in enumerate(bad):
        row = {"split_id": sid, "material_id": meta_test.loc[j, "material_id"], "reduced_formula": meta_test.loc[j, "reduced_formula"],
               "y_true": float(meta_test.loc[j, "value"]), "y_pred": float(pred[j])}
        for r, k in enumerate(np.argsort(-np.abs(contrib[i]))[:top], start=1):
            raw = float(x_test.iloc[bad[i]][names[k]]) if names[k] in x_test.columns and not isinstance(x_test.iloc[bad[i]][names[k]], str) else np.nan
            row.update({f"top{r}_feature": names[k], f"top{r}_contribution": float(contrib[i, k]),
                        f"top{r}_standardised_value": float(xt[i, k]), f"top{r}_raw_value": raw})
        rows.append(row)
    return rows


def explain_explosions(frame: pd.DataFrame, features: list[str], work_dir, sids: list[str], seed: int, categorical: list[str],
                       threshold: float = agg.EXPLODE_ABS) -> pd.DataFrame:
    rows = []
    for sid in sids:
        sel = pd.read_csv(work_dir / f"main__{sid}__selection.csv")
        params = ast.literal_eval(sel[(sel["variant"] == "tier3") & (sel["algorithm"] == "linear")].iloc[0]["best_params"])
        labels = pd.read_parquet(work_dir / f"labels__{sid}.parquet").set_index("material_id").loc[frame["material_id"], "split"].to_numpy()
        est = fit_selected_ridge(frame, labels, features, params, seed, categorical)
        rows += explain_split(est, frame, labels, features, sid, threshold)
    return pd.DataFrame(rows)


def feature_blame(explained: pd.DataFrame) -> pd.DataFrame:
    """How often each column is the single largest contributor to an exploded prediction."""
    if explained.empty:
        return pd.DataFrame(columns=["feature", "n_exploded_predictions_led", "n_splits", "median_abs_standardised_value"])
    g = explained.groupby("top1_feature")
    return pd.DataFrame({"n_exploded_predictions_led": g.size(), "n_splits": g["split_id"].nunique(),
                         "median_abs_standardised_value": g["top1_standardised_value"].apply(lambda s: float(np.median(np.abs(s))))}
                        ).sort_values("n_exploded_predictions_led", ascending=False).reset_index(names="feature")
