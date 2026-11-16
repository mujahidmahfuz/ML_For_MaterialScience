"""A20 step 3 (base env): score the end-to-end graph-network predictions against the saved baselines. Specification and claim rule: PLAN.md, entry A20.

Callers: none (final step). Inputs: outputs/a20_gnn/preds/*.parquet (a20_gnn_train.py), the saved A1 test predictions (a1.regression_predictions('curie')), and
a20_gnn_prepare.py's parquet for the target values. Outputs: outputs/a20_gnn/{variant_mae.csv, gnn_contrasts.csv, seed_counts.csv}.
Seeds are averaged in prediction space per (variant, split, record). A contrast is the change in MAE (K) from the reference to the candidate (positive = the
candidate is better), per split, with the refit-aware interval (Nadeau-Bengio, as in A1/A19) and a formula-cluster bootstrap.
Run (repository root):  python final/revision/scripts/a20_gnn_analysis.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a1_tier_inference as a1  # noqa: E402
from a19_same_spacegroup import interval  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "outputs/a20_gnn"
GNN = ["mlp_t1", "gnn_t1", "gnn_only"]
# (name, reference, candidate)
CONTRASTS = [
    ("C1 PRIMARY: MLP Tier 1 -> graph network + Tier 1", "mlp_t1", "gnn_t1"),
    ("S1: boosting Tier 1 -> graph network + Tier 1 (gradient boosting)", "gb_t1", "gnn_t1"),
    ("S2: boosting Tier 1 -> graph network + Tier 1 (XGBoost)", "xgb_t1", "gnn_t1"),
    ("S3: boosting Tier 3 -> graph network + Tier 1 (gradient boosting)", "gb_t3", "gnn_t1"),
    ("S4: boosting Tier 3 -> graph network + Tier 1 (XGBoost)", "xgb_t3", "gnn_t1"),
    ("S5: boosting Tier 1 -> graph network alone (gradient boosting)", "gb_t1", "gnn_only"),
    ("S6: boosting Tier 1 -> graph network alone (XGBoost)", "xgb_t1", "gnn_only"),
    ("check: boosting Tier 1 -> MLP Tier 1 (gradient boosting)", "gb_t1", "mlp_t1"),
]


def load_gnn() -> tuple[pd.DataFrame, pd.DataFrame]:
    inputs = pd.read_parquet(OUT / "matched_curie_inputs.parquet", columns=["material_id", "reduced_formula", "y"])
    rows = []
    for f in sorted((OUT / "preds").glob("*.parquet")):
        variant, split, seed = f.stem.split("__")
        d = pd.read_parquet(f, columns=["material_id", "y_pred"])
        d["variant"], d["split_id"], d["seed"] = variant, split[1:], int(seed[4:])
        rows.append(d)
    allp = pd.concat(rows, ignore_index=True)
    counts = allp.groupby(["variant", "split_id"])["seed"].nunique().rename("n_seeds").reset_index()
    mean = allp.groupby(["variant", "split_id", "material_id"], as_index=False)["y_pred"].mean()
    mean = mean.merge(inputs, on="material_id", how="left").rename(columns={"y": "y_true", "variant": "variant_name"})
    return mean, counts


def baselines() -> pd.DataFrame:
    df, _ = a1.regression_predictions("curie")
    keep = {("gradient_boosting", "tier1"): "gb_t1", ("xgboost_seedmean", "tier1"): "xgb_t1", ("gradient_boosting", "tier3"): "gb_t3", ("xgboost_seedmean", "tier3"): "xgb_t3"}
    df["variant_name"] = [keep.get(k) for k in zip(df["algorithm"], df["variant"])]
    return df.dropna(subset=["variant_name"])[["variant_name", "split_id", "material_id", "reduced_formula", "y_true", "y_pred"]]


def main() -> None:
    gnn, counts = load_gnn()
    counts.to_csv(OUT / "seed_counts.csv", index=False)
    cols = ["variant_name", "split_id", "material_id", "reduced_formula", "y_true", "y_pred"]
    allv = pd.concat([gnn[cols], baselines()], ignore_index=True)
    allv["split_id"] = allv["split_id"].astype(str)
    complete = [s for s in a1.SPLITS if all(((counts["variant"] == v) & (counts["split_id"] == s)).any() for v in GNN)]
    mae = (allv[allv["split_id"].isin(complete)].assign(err=lambda d: (d["y_pred"] - d["y_true"]).abs())
           .groupby(["variant_name", "split_id"])["err"].mean().unstack("variant_name"))
    mae.to_csv(OUT / "variant_mae.csv")
    n_train = a1.n_total("curie") - allv[(allv["variant_name"] == "gb_t1") & (allv["split_id"] == complete[0])].shape[0]
    forms = pd.Index(sorted(allv["reduced_formula"].unique()))
    rng = np.random.default_rng(a1.SEED + 20000)
    w_all = np.vstack([np.bincount(rng.integers(0, len(forms), len(forms)), minlength=len(forms)) for _ in range(a1.N_BOOT)])
    rows = []
    for name, ref, cand in CONTRASTS:
        d_split, boots, n_test = [], [], []
        for s in complete:
            a = allv[(allv["variant_name"] == ref) & (allv["split_id"] == s)].set_index("material_id")
            b = allv[(allv["variant_name"] == cand) & (allv["split_id"] == s)].set_index("material_id")
            if set(a.index) != set(b.index):
                raise ValueError(f"{name} split {s}: test rows differ ({len(a)} vs {len(b)})")
            b = b.loc[a.index]
            y, pa, pb = a["y_true"].to_numpy(), a["y_pred"].to_numpy(), b["y_pred"].to_numpy()
            w = w_all[:, forms.get_indexer(a["reduced_formula"])].astype(float)
            d_split.append(a1.improvement("regression", float(np.abs(pa - y).mean()), float(np.abs(pb - y).mean())))
            boots.append(a1.improvement("regression", a1.weighted_metric(y, pa, w, "regression"), a1.weighted_metric(y, pb, w, "regression")))
            n_test.append(len(a))
        d, boot = np.asarray(d_split), np.mean(boots, axis=0)
        mean, lo, hi, mde = interval(d, float(np.mean(n_test)), n_train)
        rows.append({"contrast": name, "reference": ref, "candidate": cand, "splits": len(complete), "mean_improvement_K": mean, "nb_ci_low": lo, "nb_ci_high": hi,
                     "boot_ci_low": float(np.quantile(boot, .025)), "boot_ci_high": float(np.quantile(boot, .975)), "splits_better": int((d > 0).sum()), "mde80_K": mde})
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "gnn_contrasts.csv", index=False)
    pd.set_option("display.width", 250, "display.max_colwidth", 70)
    print("splits complete:", complete, "| seeds per (variant, split):", counts["n_seeds"].min(), "-", counts["n_seeds"].max())
    print(mae.mean().round(1).to_string())
    print(table.drop(columns=["reference", "candidate"]).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
