"""External Curie benchmark: performance before/after audit exclusions, grouped-bootstrap uncertainty, chemical similarity (PLAN.md s1-s3).

Predictions/intervals are the saved October ones (../external_predictions.csv); nothing is refit. The training reference set is
re-derived exactly as predict_candidates.fit_curie did (v1.3 Curie split, seeded 80/20 formula calibration split).
Usage (from this folder, OMP_NUM_THREADS unset): python analyze_external.py
Outputs: similarity_records.csv, subset_metrics_bootstrap.csv, subset_comparisons.csv, similarity_spearman.csv, similarity_bins.csv,
         similarity_trend.csv, similarity_unseen_system.csv, similarity_unseen_system_comparison.csv
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import rankdata

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from audit_common import (N_BOOT, SEED, cluster_bootstrap_indices, cluster_weights, doi_set, fraction_vectors, metrics,  # noqa: E402
                          nearest_tv_distance, weighted_median_ae, weighted_metrics)

CLUSTERINGS = [("paper (pre-specified: shared-DOI components)", "paper_cluster"), ("paper (first-listed DOI, Amendment 2)", "first_doi_cluster"),
               ("chemical system", "chemical_system")]

K_SENS = 5
NEAR_COPY_D = 0.01
EXPECTED_TRAIN_ROWS = 23_757
METRIC_KEYS = ["mae_k", "median_ae_k", "r2", "coverage", "mean_width_k", "share_within_50k"]
PRIMARY = "primary benchmark (A1/A2/A4/A5 removed)"
ORIGINAL = "original (all 2,500 records)"


# ----------------------------------------------------------------------------------------------------------- data
def load_records() -> pd.DataFrame:
    flags = pd.read_csv(HERE / "audit_flags.csv", keep_default_na=False, na_values=[""])
    pred = pd.read_csv(HERE.parent / "external_predictions.csv", usecols=["name", "tc_pred_k", "tc_lo_k", "tc_hi_k"], keep_default_na=False, na_values=[""])
    df = flags.merge(pred, on="name", how="left", validate="one_to_one")
    if df["tc_pred_k"].isna().any():
        raise ValueError("records without a saved prediction")
    df["abs_err_k"] = (df["tc_pred_k"] - df["tc_exp_k"]).abs()
    df["width_k"] = df["tc_hi_k"] - df["tc_lo_k"]
    df["first_doi_cluster"] = df["doi_raw"].map(first_doi)
    return df


def first_doi(raw: object) -> str:
    """Amendment 2: the first-listed DOI of a record (order as written), or the reference string when there is no DOI."""
    for part in re.split(r",\s*", str(raw).strip().strip("[]")):
        ds = doi_set(part)
        if ds:
            return next(iter(ds))
    return "ref:" + str(raw).strip().lower()


def training_reference() -> tuple[pd.DataFrame, list[str], np.ndarray]:
    """Curie modelling frame (v1.3, Tier 1) and the boolean training mask used by fit_curie (80% of formulas)."""
    import predict_candidates as pc  # noqa: PLC0415 - heavy import, only needed here
    cfg = pc.p7.dataset_cfg("v1.3")
    frame, feats = pc.pm.load_modeling_frame(cfg, "curie", "tier1", pc.p7.split_dir("v1.3") / "split_curie.csv")
    frame = frame.reset_index(drop=True)
    return frame, feats, ~pc.calibration_mask(frame["reduced_formula"])


def add_distances(df: pd.DataFrame, frame: pd.DataFrame, feats: list[str], ref_mask: np.ndarray, tag: str) -> pd.DataFrame:
    """d_comp (composition TV distance) and d_desc (z-scored Tier 1 Euclidean) to the reference formulas: nearest and mean of K_SENS nearest."""
    import features as F  # noqa: PLC0415
    ref_rows = frame[ref_mask]
    ref = ref_rows.drop_duplicates("reduced_formula")
    ext_formulas = df["reduced_formula"].tolist()
    elements = sorted({e.symbol for f in list(ref["reduced_formula"]) + ext_formulas for e in F.Composition(f).elements})
    near, mean_k, idx = nearest_tv_distance(fraction_vectors(ext_formulas, elements), fraction_vectors(ref["reduced_formula"].tolist(), elements), k=K_SENS)
    mean, std = ref_rows[feats].mean(), ref_rows[feats].std().replace(0, 1)
    tree = cKDTree(((ref[feats] - mean) / std).fillna(0).to_numpy())
    x_ext = F.feature_frame(ext_formulas)
    dd, _ = tree.query(((x_ext[feats] - mean) / std).fillna(0).to_numpy(), k=K_SENS)
    out = df.copy()
    out[f"d_comp_{tag}"], out[f"d_comp_k5_{tag}"] = near, mean_k
    out[f"nn_formula_{tag}"] = ref["reduced_formula"].to_numpy()[idx]
    out[f"d_desc_{tag}"], out[f"d_desc_k5_{tag}"] = dd[:, 0], dd.mean(axis=1)
    return out


# ----------------------------------------------------------------------------------------------------------- sets
def table_versions(df: pd.DataFrame) -> dict[str, pd.Series]:
    excl_core = df["a1_computational_label"] | df["a2_malformed"] | df["a5_not_magnetic_tc"]
    primary = ~df["excluded_primary"]
    return {
        ORIGINAL: pd.Series(True, index=df.index),
        PRIMARY: primary,
        "sensitivity: keep A4 (training-rule) records": ~excl_core,
        "sensitivity: primary minus A6 (film/nano/pressure/2D...)": primary & ~df["a6_all_sources"],
        "sensitivity: primary minus cited-in-computational-only and suspect": primary & ~df["a1c_only_computational_dois"] & ~df["a2s_suspect_extraction"],
    }


def subsets(df: pd.DataFrame, include_old: bool) -> dict[str, pd.Series]:
    blind = ~df["a7a_formula_in_repository"]
    never = ~df["a7b_doi_in_curie_any_row"]
    unseen = ~df["a7_system_seen"]
    out = {
        "all": pd.Series(True, index=df.index),
        "composition seen in training repository": ~blind,
        "seen + value identical to a value in our Curie data (copied)": ~blind & df["a7c_value_copied_any_row"],
        "seen + value not copied": ~blind & ~df["a7c_value_copied_any_row"],
        "composition NEVER seen (blind)": blind,
        "blind + not a near-copy (d_comp >= 0.01)": blind & (df["d_comp_train"] >= NEAR_COPY_D),
        "blind + paper never used (corrected DOI match)": blind & never,
        "blind + seen chemical system": blind & ~unseen,
        "blind + unseen chemical system": blind & unseen,
        "blind + paper never used + unseen system": blind & never & unseen,
    }
    if include_old:
        old_blind = ~df["a7a_string_match_october"]
        out["October definition: formula string never seen"] = old_blind
        out["October definition: string-blind + paper never used (buggy DOI match)"] = old_blind & ~df["a7_old_doi_flag_buggy_normaliser"].astype(bool)
        out["October definition: string-blind + unseen system"] = old_blind & unseen
    return out


# ----------------------------------------------------------------------------------------------------------- bootstrap
def ci(values: np.ndarray) -> tuple[float, float]:
    v = values[np.isfinite(values)]
    return (float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))) if len(v) else (np.nan, np.nan)


def boot_subset(d: pd.DataFrame, cluster_col: str, seed: int) -> dict[str, float]:
    """Point metrics + 95% percentile CIs from a cluster bootstrap over the subset's own clusters."""
    y, p, lo, hi = (d[c].to_numpy(dtype=float) for c in ["tc_exp_k", "tc_pred_k", "tc_lo_k", "tc_hi_k"])
    point = metrics(y, p, lo, hi)
    codes, w = cluster_weights(d[cluster_col].astype(str).to_numpy(), N_BOOT, seed)
    boot = weighted_metrics(codes, w, y, p, lo, hi)
    boot["median_ae_k"] = weighted_median_ae(codes, w, np.abs(p - y))
    row: dict[str, float] = {"n": len(d), "n_clusters": int(codes.max() + 1)}
    for k in METRIC_KEYS:
        row[k] = point[k]
        row[f"{k}_lo"], row[f"{k}_hi"] = ci(boot[k])
    row["share_boot_r2_below_0"] = float(np.mean(boot["r2"] < 0))
    return row


def subset_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for vname, vmask in table_versions(df).items():
        d = df[vmask]
        for sname, smask in subsets(d, include_old=vname == ORIGINAL).items():
            s = d[smask]
            if len(s) < 2:
                continue
            for cname, ccol in CLUSTERINGS:
                rows.append({"table": vname, "subset": sname, "cluster": cname, "n_papers_first_doi": s["first_doi_cluster"].nunique(),
                             "n_chemical_systems": s["chemical_system"].nunique(), **boot_subset(s, ccol, SEED)})
    return pd.DataFrame(rows)


def compare(df: pd.DataFrame, mask_a: pd.Series, mask_b: pd.Series, cluster_col: str, seed: int) -> dict[str, float]:
    """Metric(A) - metric(B), clusters of A union B resampled jointly; share of resamples in which A is worse."""
    u = df[mask_a | mask_b]
    a, b = mask_a[u.index].to_numpy(), mask_b[u.index].to_numpy()
    y, p, lo, hi = (u[c].to_numpy(dtype=float) for c in ["tc_exp_k", "tc_pred_k", "tc_lo_k", "tc_hi_k"])
    codes, w = cluster_weights(u[cluster_col].astype(str).to_numpy(), N_BOOT, seed)
    ba, bb = weighted_metrics(codes[a], w, y[a], p[a], lo[a], hi[a]), weighted_metrics(codes[b], w, y[b], p[b], lo[b], hi[b])
    pa, pb = metrics(y[a], p[a], lo[a], hi[a]), metrics(y[b], p[b], lo[b], hi[b])
    row: dict[str, float] = {"n_a": int(a.sum()), "n_b": int(b.sum()), "n_clusters_union": int(codes.max() + 1)}
    for k in ["mae_k", "r2", "coverage", "mean_width_k"]:
        diff = ba[k] - bb[k]
        row[f"{k}_a"], row[f"{k}_b"], row[f"{k}_diff"] = pa[k], pb[k], pa[k] - pb[k]
        row[f"{k}_diff_lo"], row[f"{k}_diff_hi"] = ci(diff)
        worse = diff > 0 if k in ("mae_k", "mean_width_k") else diff < 0
        row[f"{k}_share_a_worse"] = float(np.mean(worse[np.isfinite(diff)]))
    return row


def comparison_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for vname in [ORIGINAL, PRIMARY]:
        d = df[table_versions(df)[vname]]
        s = subsets(d, include_old=False)
        pairs = {"blind+unseen system vs blind+seen system": (s["blind + unseen chemical system"], s["blind + seen chemical system"]),
                 "blind vs seen formula": (s["composition NEVER seen (blind)"], s["composition seen in training repository"]),
                 "blind+never-used+unseen vs blind+never-used+seen": (s["blind + paper never used + unseen system"],
                                                                       s["blind + paper never used (corrected DOI match)"] & d["a7_system_seen"])}
        for pname, (ma, mb) in pairs.items():
            for cname, ccol in CLUSTERINGS:
                rows.append({"table": vname, "comparison": pname, "cluster": cname, **compare(d, ma, mb, ccol, SEED)})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------------------------------- similarity
def spearman(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.corrcoef(rankdata(x), rankdata(y))[0, 1])


def analysis_sets(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    primary = df[~df["excluded_primary"]]
    return {"primary": primary, "primary, blind only": primary[~primary["a7a_formula_in_repository"]]}


def spearman_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sname, d in analysis_sets(df).items():
        idx_list = list(cluster_bootstrap_indices(d["paper_cluster"].to_numpy(), N_BOOT, SEED))
        for dist in ["d_comp_train", "d_desc_train", "d_comp_k5_train", "d_desc_k5_train", "d_comp_allcurie", "d_desc_allcurie"]:
            for target in ["abs_err_k", "width_k"]:
                x, y = d[dist].to_numpy(), d[target].to_numpy()
                boot = np.array([spearman(x[i], y[i]) for i in idx_list])
                lo, hi = ci(boot)
                rows.append({"set": sname, "n": len(d), "distance": dist, "versus": target, "spearman_rho": spearman(x, y), "ci_lo": lo, "ci_hi": hi,
                             "share_boot_rho_le_0": float(np.mean(boot <= 0))})
    return pd.DataFrame(rows)


def distance_bins(d: pd.DataFrame) -> tuple[pd.Series, np.ndarray]:
    """Bin 0 = d_comp == 0 (formula used to train); others = quartiles of the non-zero d_comp (edges from distances only)."""
    dist = d["d_comp_train"]
    edges = np.quantile(dist[dist > 1e-12], [0, 0.25, 0.5, 0.75, 1.0])
    q = pd.cut(dist, bins=edges, labels=["Q1 (closest)", "Q2", "Q3", "Q4 (farthest)"], include_lowest=True).astype(str)
    return q.where(dist > 1e-12, "0: formula used in training"), edges


def bins_table(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, trend = [], []
    for sname, d in analysis_sets(df).items():
        b, edges = distance_bins(d)
        d = d.assign(d_bin=b)
        for name, g in d.groupby("d_bin"):
            rows.append({"set": sname, "bin": name, "d_comp_min": g["d_comp_train"].min(), "d_comp_max": g["d_comp_train"].max(),
                         "share_unseen_system": float((~g["a7_system_seen"]).mean()), "n_papers": g["paper_cluster"].nunique(),
                         **boot_subset(g, "paper_cluster", SEED)})
        r = compare(d, d["d_bin"].eq("Q4 (farthest)"), d["d_bin"].eq("Q1 (closest)"), "paper_cluster", SEED)
        trend.append({"set": sname, "contrast": "Q4 (farthest) minus Q1 (closest non-zero)", "quartile_edges": str(np.round(edges, 4).tolist()), **r})
    return pd.DataFrame(rows), pd.DataFrame(trend)


def unseen_system_table(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """Is the unseen-system failure explained by distance? Unseen-system blind records vs seen-system blind records in the same d_comp range."""
    d = analysis_sets(df)["primary, blind only"]
    uns, seen = d[~d["a7_system_seen"]], d[d["a7_system_seen"]]
    lo, hi = np.quantile(uns["d_comp_train"], [0.10, 0.90])
    in_range = d["a7_system_seen"] & d["d_comp_train"].between(lo, hi)
    rows = []
    for name, g in [("blind, unseen system", uns), ("blind, seen system (all)", seen),
                    (f"blind, seen system, d_comp in [{lo:.3f}, {hi:.3f}] (10-90% range of the unseen-system records)", d[in_range])]:
        rows.append({"group": name, "d_comp_median": g["d_comp_train"].median(), "d_comp_p10": g["d_comp_train"].quantile(0.1),
                     "d_comp_p90": g["d_comp_train"].quantile(0.9), "n_papers": g["paper_cluster"].nunique(), **boot_subset(g, "paper_cluster", SEED)})
    return pd.DataFrame(rows), compare(d, ~d["a7_system_seen"], in_range, "paper_cluster", SEED)


def k5_diagnostic(df: pd.DataFrame) -> pd.DataFrame:
    """POST HOC (Amendment 2): k=5 composition distance vs error, split by whether the exact formula is in the training reference."""
    rows = []
    for exact, d in analysis_sets(df)["primary"].groupby(analysis_sets(df)["primary"]["d_comp_train"] < 1e-12):
        idx_list = list(cluster_bootstrap_indices(d["paper_cluster"].to_numpy(), N_BOOT, SEED))
        x, y = d["d_comp_k5_train"].to_numpy(), d["abs_err_k"].to_numpy()
        boot = np.array([spearman(x[i], y[i]) for i in idx_list])
        q = pd.qcut(d["d_comp_k5_train"], 4, labels=False)
        rows.append({"exact_formula_in_training": bool(exact), "n": len(d), "spearman_k5_vs_abs_err": spearman(x, y), "ci_lo": ci(boot)[0], "ci_hi": ci(boot)[1],
                     "mae_by_k5_quartile": str(d.groupby(q)["abs_err_k"].mean().round(1).tolist()),
                     "share_value_copied_by_k5_quartile": str(d.groupby(q)["a7c_value_copied_any_row"].mean().round(2).tolist())})
    return pd.DataFrame(rows)


def main() -> None:
    df = load_records()
    frame, feats, train = training_reference()
    print(f"Curie frame {len(frame):,} rows; training rows {int(train.sum()):,}", flush=True)
    if int(train.sum()) != EXPECTED_TRAIN_ROWS:
        raise RuntimeError(f"training reference does not reproduce fit_curie ({EXPECTED_TRAIN_ROWS:,} rows)")
    df = add_distances(df, frame, feats, train.to_numpy() if hasattr(train, "to_numpy") else train, "train")
    df = add_distances(df, frame, feats, np.ones(len(frame), dtype=bool), "allcurie")
    leak = df[(df["d_comp_allcurie"] < 1e-9) & ~df["a7a_formula_in_repository"]]
    if len(leak):
        raise RuntimeError(f"Amendment 3 consistency check failed: {len(leak)} 'blind' records have an identical Curie composition, e.g. {leak['name'].head(3).tolist()}")
    df.to_csv(HERE / "similarity_records.csv", index=False, encoding="utf-8")
    print("distances done", flush=True)
    st = subset_table(df)
    st.to_csv(HERE / "subset_metrics_bootstrap.csv", index=False, encoding="utf-8")
    comparison_table(df).to_csv(HERE / "subset_comparisons.csv", index=False, encoding="utf-8")
    print("subset bootstrap done", flush=True)
    spearman_table(df).to_csv(HERE / "similarity_spearman.csv", index=False, encoding="utf-8")
    bt, tr = bins_table(df)
    bt.to_csv(HERE / "similarity_bins.csv", index=False, encoding="utf-8")
    tr.to_csv(HERE / "similarity_trend.csv", index=False, encoding="utf-8")
    us, us_cmp = unseen_system_table(df)
    us.to_csv(HERE / "similarity_unseen_system.csv", index=False, encoding="utf-8")
    pd.Series(us_cmp, name="value").rename_axis("item").to_csv(HERE / "similarity_unseen_system_comparison.csv", encoding="utf-8")
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_colwidth", 70)
    st[st["cluster"].str.startswith("paper (first")].to_csv(HERE / "subset_metrics_bootstrap_first_doi.csv", index=False, encoding="utf-8")
    k5_diagnostic(df).to_csv(HERE / "similarity_k5_diagnostic_posthoc.csv", index=False, encoding="utf-8")
    st = st[st["cluster"].str.startswith("paper (pre")]
    cols = ["table", "subset", "n", "n_clusters", "n_papers_first_doi", "mae_k", "mae_k_lo", "mae_k_hi", "r2", "r2_lo", "r2_hi", "coverage", "coverage_lo", "coverage_hi"]
    print(st[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
