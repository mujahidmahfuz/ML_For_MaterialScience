"""Freeze the reduced_formula-grouped train/validation/test splits for the current dataset version (decision D4).

One split per target over its full clean population, plus, for the primary targets, a Tier 3 matched split
stratified on the matched population itself (plan s9 compares Tier 1/2/3 only inside that population).
Size-balanced group assignment is used instead of StratifiedGroupKFold because Tier 3 Curie is dominated by
a few heavily repeated formulas (Fe 436, Mn 349, Co 331, Ni 250, BaTiO3 226 rows), which left fold-based
splits at 86/5/9. Pseudo-formula materials (open decision D7) are kept and flagged; because splitting is
grouped by formula, dropping them later leaves every other assignment unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

import phase6_common as pc

SCRIPT = "src/make_splits.py"
STAGE = "split_freeze"
FILE_NAMES = {"ordering": "split_ordering.csv", "curie": "split_curie.csv", "ms_moment": "split_ms.csv",
              "ms_mass": "split_ms_mass.csv", "ms_volume": "split_ms_volume.csv", "k1": "split_k1.csv"}
MATCHED_NAMES = {"ordering": "matched_split_ordering.csv", "curie": "matched_split_curie.csv",
                 "ms_moment": "matched_split_ms.csv"}
D1_COLS = ["average_unpaired_electron_proxy", "average_d_electron_count", "average_f_electron_count",
           "valence_electron_concentration"]


SPLITS = ("train", "validation", "test")


def group_strata(df: pd.DataFrame, groups: pd.Series, task: str) -> pd.Series:
    """One stratum per formula group: majority class (classification) or quantile bin of the group mean."""
    by_group = df["value"].groupby(groups)
    if task == "classification":
        return by_group.agg(lambda s: s.value_counts().idxmax()).astype(str)
    means = by_group.mean()
    n_bins = 10 if len(means) >= 2000 else 5
    return pd.qcut(means.rank(method="first"), q=n_bins, labels=False).astype(str)


def assign_splits(df: pd.DataFrame, task: str, cfg: dict) -> pd.DataFrame:
    """Size-balanced stratified group assignment: within each stratum, largest groups first, each to the split
    furthest below its target fraction. Whole formula groups stay together; seeded shuffle breaks ties."""
    fractions = np.array([cfg["splits"]["fractions"][s] for s in SPLITS], dtype=float)
    groups = df["reduced_formula"].fillna("__id__" + df["material_id"])
    sizes = groups.value_counts()
    strata = group_strata(df, groups, task)
    rng = np.random.default_rng(cfg["random_seed"])
    split_of_group = {}
    for _, members in strata.groupby(strata):
        names = members.index.to_numpy()
        rng.shuffle(names)
        ordered = sizes.loc[names].sort_values(ascending=False, kind="stable")
        target = fractions * ordered.sum()
        filled = np.zeros(len(SPLITS))
        for name, size in ordered.items():
            k = int(np.argmin(filled / target))
            split_of_group[name] = SPLITS[k]
            filled[k] += size
    return df.assign(group=groups.to_numpy(), stratum=groups.map(strata).to_numpy(),
                     split=groups.map(split_of_group).to_numpy())


def assert_no_group_leakage(frame: pd.DataFrame, name: str) -> None:
    per_group = frame.groupby("group")["split"].nunique()
    if (per_group > 1).any():
        raise AssertionError(f"{name}: {int((per_group > 1).sum())} reduced_formula groups span more than one split")


def balance_rows(frame: pd.DataFrame, target: str, population: str, task: str, classes: list) -> list[dict]:
    rows = []
    p99_all = frame["value"].quantile(0.99) if task == "regression" else None
    for split in ("train", "validation", "test"):
        part = frame[frame["split"] == split]
        row = {"target": target, "population": population, "split": split, "N": len(part),
               "pct_of_population": round(100 * len(part) / len(frame), 2), "n_formula_groups": part["group"].nunique(),
               "n_experimental": int(part["Experimental"].sum()), "n_pseudo_formula": int(part["pseudo_formula"].sum())}
        if task == "classification":
            vc = part["value"].value_counts()
            row.update({f"n_{c}": int(vc.get(c, 0)) for c in classes})
            row.update({f"pct_{c}": round(100 * vc.get(c, 0) / len(part), 2) if len(part) else np.nan for c in classes})
        else:
            v = part["value"]
            row.update({"mean": v.mean(), "median": v.median(), "p99": v.quantile(0.99), "max": v.max(),
                        "n_above_population_p99": int((v > p99_all).sum())})
        rows.append(row)
    return rows


def derive_from_previous(cfg: dict) -> None:
    """New dataset version that only removes materials: drop them from the frozen splits, keep every other
    assignment. Fails if any material would be added or if a dropped material is not in the D7 quarantine."""
    root = Path(cfg["paths"]["project_root"])
    prev_dir, out_dir = root / cfg["splits"]["derived_from_dir"], root / cfg["splits"]["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    quarantined = set(pd.read_csv(pc.project_path(cfg, "d7_quarantine"), usecols=["material_id"])["material_id"])
    tier3_ids = set(pd.read_parquet(pc.tier_path(cfg, "tier3"), columns=["material_id"])["material_id"])
    classes = cfg["targets"]["ordering"]["classes"]
    jobs = [(n, f, False) for n, f in FILE_NAMES.items()] + [(n, f, True) for n, f in MATCHED_NAMES.items()]
    summary, derivation = [], []
    for name, fname, matched in jobs:
        spec = cfg["targets"][name]
        prev = pd.read_csv(prev_dir / fname)
        current = pc.load_target(cfg, name)
        if matched:
            current = current[current["material_id"].isin(tier3_ids)]
        cur_ids, prev_ids = set(current["material_id"]), set(prev["material_id"])
        added, dropped = cur_ids - prev_ids, prev_ids - cur_ids
        if added or not dropped <= quarantined:
            raise AssertionError(f"{fname}: {len(added)} added, {len(dropped - quarantined)} dropped outside the quarantine")
        kept = prev[prev["material_id"].isin(cur_ids)].assign(pseudo_formula=False)
        kept.to_csv(out_dir / fname, index=False, encoding="utf-8")
        tier_label, group_label = ("tier1/2/3 matched", "Physics-complete") if matched else ("tier1/tier2", "All")
        pc.log_run(cfg, SCRIPT, STAGE, name, tier_label, group_label, len(kept), (out_dir / fname).relative_to(pc.EDA_ROOT))
        dropped_by_split = prev.loc[prev["material_id"].isin(dropped), "split"].value_counts()
        derivation.append({"file": fname, "n_previous": len(prev), "n_dropped_D7": len(dropped), "n_kept": len(kept),
                           **{f"dropped_{s}": int(dropped_by_split.get(s, 0)) for s in SPLITS}})
        frame = kept.merge(current[["material_id", "value"]], on="material_id")
        frame["group"] = frame["reduced_formula"].fillna("__id__" + frame["material_id"])
        assert_no_group_leakage(frame, fname)
        summary += balance_rows(frame, name, "tier3_matched" if matched else "full", spec["task"], classes)
    pd.DataFrame(summary).to_csv(out_dir / "split_summary.csv", index=False, encoding="utf-8")
    pd.DataFrame(derivation).to_csv(out_dir / "split_derivation_log.csv", index=False, encoding="utf-8")
    for fname in ("split_summary.csv", "split_derivation_log.csv"):
        pc.log_run(cfg, SCRIPT, STAGE, "all", "n/a", "all", 0, (out_dir / fname).relative_to(pc.EDA_ROOT))
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(f"Analysis Dataset {cfg['analysis_dataset_version']}: splits derived from {prev_dir} -> {out_dir}")
        print(pd.DataFrame(derivation).to_string(index=False))
        print(pd.DataFrame(summary).round(2).to_string(index=False))


def main() -> None:
    cfg = pc.load_config()
    if "--derive" in sys.argv:
        derive_from_previous(cfg)
        return
    version = cfg["analysis_dataset_version"]
    out_dir = Path(cfg["paths"]["project_root"]) / cfg["splits"]["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    repo = pc.load_feature_repository(cfg, columns=["material_id"] + D1_COLS)
    pseudo_ids = set(repo.loc[repo[D1_COLS].isna().all(axis=1), "material_id"])
    tier3_ids = set(pd.read_parquet(pc.tier_path(cfg, "tier3"), columns=["material_id"])["material_id"])
    classes = cfg["targets"]["ordering"]["classes"]

    summary = []
    keep_cols = ["material_id", "reduced_formula", "split", "stratum", "tier3", "pseudo_formula", "Experimental"]
    for name, fname in FILE_NAMES.items():
        spec = cfg["targets"][name]
        df = pc.load_target(cfg, name)
        df["tier3"] = df["material_id"].isin(tier3_ids)
        df["pseudo_formula"] = df["material_id"].isin(pseudo_ids)
        frame = assign_splits(df, spec["task"], cfg)
        assert_no_group_leakage(frame, name)
        frame[keep_cols].to_csv(out_dir / fname, index=False, encoding="utf-8")
        pc.log_run(cfg, SCRIPT, STAGE, name, "tier1/tier2", "All", len(frame), (out_dir / fname).relative_to(pc.EDA_ROOT))
        summary += balance_rows(frame, name, "full", spec["task"], classes)
        if name in MATCHED_NAMES:
            matched = assign_splits(df[df["tier3"]].reset_index(drop=True), spec["task"], cfg)
            assert_no_group_leakage(matched, f"{name} matched")
            path = out_dir / MATCHED_NAMES[name]
            matched[keep_cols].to_csv(path, index=False, encoding="utf-8")
            pc.log_run(cfg, SCRIPT, STAGE, name, "tier1/2/3 matched", "Physics-complete", len(matched),
                       path.relative_to(pc.EDA_ROOT))
            summary += balance_rows(matched, name, "tier3_matched", spec["task"], classes)

    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(out_dir / "split_summary.csv", index=False, encoding="utf-8")
    pc.log_run(cfg, SCRIPT, STAGE, "all", "n/a", "all", len(summary_df), (out_dir / "split_summary.csv").relative_to(pc.EDA_ROOT))
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(f"Analysis Dataset {version}: splits written to {out_dir}")
        print(summary_df.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
