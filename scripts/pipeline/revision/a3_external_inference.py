"""A3 (RR5): external-benchmark inference with few-cluster-aware intervals, a fixed-reference skill score and the wording rule
evaluated under every clustering.

Input: new_materials_finding/external_audit/similarity_records.csv (primary benchmark rows = ~excluded_primary; subsets exactly as in
analyze_external.subsets). For each subset x clustering (paper/shared-DOI, first-listed DOI, chemical system):
  - number of resampling clusters
  - MAE and R2: percentile and BCa cluster-bootstrap 95% intervals (10,000 resamples; acceleration from the cluster jackknife)
  - skill score vs a FIXED reference = 1 - MSE / MSE(training-mean predictor), training mean = mean Tc of the v1.3 train+validation rows
  - target SD of the subset
  - wording-rule verdict: 'no skill beyond the mean' only if the upper R2 limit <= 0.2
Output: final/revision/outputs/a3/external_inference.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
AUD = ROOT / "new_materials_finding/external_audit"
sys.path.insert(0, str(AUD))
sys.path.insert(0, str(AUD.parent))
from analyze_external import CLUSTERINGS, subsets  # noqa: E402

OUT = ROOT / "final/revision/outputs/a3"
N_BOOT, SEED, RULE = 10_000, 20261110, 0.2
KEEP = ["all", "composition seen in training repository", "seen + value not copied", "composition NEVER seen (blind)",
        "blind + paper never used (corrected DOI match)", "blind + seen chemical system", "blind + unseen chemical system",
        "blind + paper never used + unseen system"]


def training_mean() -> float:
    """Mean Tc over the v1.3 Curie train+validation rows of the frozen split (the reference predictor a reader would use)."""
    sys.path.insert(0, str(ROOT / "EDA" / "src"))
    import phase6_common as pc
    import phase7_validation as p7
    cfg = p7.dataset_cfg("v1.3")
    y = pc.load_target(cfg, "curie")[["material_id", "value"]]
    s = pd.read_csv(ROOT / "EDA/02_splits/v1.3/split_curie.csv", usecols=["material_id", "split"])
    d = y.merge(s, on="material_id")
    return float(d.loc[d["split"].isin(["train", "validation"]), "value"].mean())


def stat_fns(y: np.ndarray, p: np.ndarray, ref: float):
    def mae(idx):
        return np.abs(p[idx] - y[idx]).mean()

    def r2(idx):
        yy = y[idx]
        return 1 - ((yy - p[idx]) ** 2).sum() / ((yy - yy.mean()) ** 2).sum()

    def skill(idx):
        yy = y[idx]
        return 1 - ((yy - p[idx]) ** 2).mean() / ((yy - ref) ** 2).mean()
    return {"mae": mae, "r2": r2, "skill_vs_train_mean": skill}


def bca(theta_hat: float, boot: np.ndarray, jack: np.ndarray, level: float = 0.95) -> tuple[float, float]:
    boot = boot[np.isfinite(boot)]
    prop = np.clip(np.mean(boot < theta_hat), 1e-6, 1 - 1e-6)
    z0 = stats.norm.ppf(prop)
    jm = jack.mean()
    num, den = ((jm - jack) ** 3).sum(), 6 * (((jm - jack) ** 2).sum() ** 1.5)
    a = num / den if den > 0 else 0.0
    out = []
    for q in ((1 - level) / 2, 1 - (1 - level) / 2):
        z = stats.norm.ppf(q)
        adj = stats.norm.cdf(z0 + (z0 + z) / (1 - a * (z0 + z)))
        out.append(float(np.quantile(boot, np.clip(adj, 0, 1))))
    return out[0], out[1]


def analyse(d: pd.DataFrame, cluster_col: str, ref: float, seed: int) -> dict:
    y, p = d["tc_exp_k"].to_numpy(float), d["tc_pred_k"].to_numpy(float)
    codes = pd.factorize(d[cluster_col].astype(str))[0]
    k = codes.max() + 1
    members = [np.flatnonzero(codes == c) for c in range(k)]
    fns = stat_fns(y, p, ref)
    rng = np.random.default_rng(seed)
    draws = [np.concatenate([members[c] for c in rng.integers(0, k, k)]) for _ in range(N_BOOT)]
    row = {"n": len(d), "n_clusters": k, "target_sd_k": float(y.std(ddof=1))}
    for name, fn in fns.items():
        theta = fn(np.arange(len(y)))
        boot = np.array([fn(ix) for ix in draws])
        jack = np.array([fn(np.concatenate([members[c] for c in range(k) if c != j])) for j in range(k)])
        lo, hi = np.quantile(boot[np.isfinite(boot)], [0.025, 0.975])
        blo, bhi = bca(theta, boot, jack)
        row.update({name: theta, f"{name}_pct_lo": lo, f"{name}_pct_hi": hi, f"{name}_bca_lo": blo, f"{name}_bca_hi": bhi})
    row["rule_pct"] = "no skill beyond the mean" if row["r2_pct_hi"] <= RULE else "much weaker / wide uncertainty"
    row["rule_bca"] = "no skill beyond the mean" if row["r2_bca_hi"] <= RULE else "much weaker / wide uncertainty"
    return row


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(AUD / "similarity_records.csv", keep_default_na=False, na_values=[""])
    prim = df[~df["excluded_primary"].astype(bool)].reset_index(drop=True)
    ref = training_mean()
    print(f"training-mean reference: {ref:.1f} K", flush=True)
    rows = []
    masks = subsets(prim, include_old=False)
    for i, sname in enumerate(KEEP):
        s = prim[masks[sname].to_numpy()]
        for j, (cname, ccol) in enumerate(CLUSTERINGS):
            rows.append({"subset": sname, "clustering": cname, "train_mean_reference_k": ref, **analyse(s, ccol, ref, SEED + 10 * i + j)})
        print(f"{sname}: done", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "external_inference.csv", index=False)
    pd.set_option("display.width", 250)
    cols = ["subset", "clustering", "n", "n_clusters", "target_sd_k", "mae", "mae_bca_lo", "mae_bca_hi", "r2", "r2_pct_lo", "r2_pct_hi", "r2_bca_lo",
            "r2_bca_hi", "skill_vs_train_mean", "skill_vs_train_mean_bca_lo", "skill_vs_train_mean_bca_hi", "rule_pct", "rule_bca"]
    print(out[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
