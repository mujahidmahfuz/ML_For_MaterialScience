"""Revision refits (resumable: one parquet per unit of work; existing files are skipped).

    python final/revision/scripts/run_refits.py ordering_seeds       A1: matched ordering, XGBoost Tier 1/2/3, estimator seeds base+0..2
    python final/revision/scripts/run_refits.py a6 <target>          A6: physics variants on the matched population, 10 splits x 3 algorithms
    python final/revision/scripts/run_refits.py a5                   A5: moment per formula unit, Tier 1/2/3 + site-count control
    python final/revision/scripts/run_refits.py a12 <target>         A12: leave-chemical-system-out with matched test rows (regimes A/B)
    python final/revision/scripts/run_refits.py a8                   A8: ordering Tier 1 full population, frozen v1.3 split, saved predictions
Leave OMP_NUM_THREADS unset (XGBoost is pinned to 16 threads by phase7_validation).
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from pymatgen.core import Composition

import rev_common as rc

ALGS = ["linear", "gradient_boosting", "xgboost"]
DFT_MAG = ["magdft_moment_per_atom", "magdft_mag_site_fraction", "magdft_magnetization_vol", "magdft_is_magnetic"]


# ------------------------------------------------------------------------------------------------------------------------ A1
def ordering_seeds() -> None:
    cfg, cfg7 = rc.setup("ordering")
    frame = rc.matched_frame("ordering", cfg)
    y = rc.encode(frame["value"])
    feats = rc.p7.variant_features(cfg, cfg7)
    cat = cfg["predictor_rules"]["categorical_predictors"]
    out = rc.REV / "a1" / "ordering_xgb_seeds"
    out.mkdir(parents=True, exist_ok=True)
    for s in range(3):
        seed = cfg["random_seed"] + s
        for sid in rc.SPLITS:
            path = out / f"seed{s}__{sid}.parquet"
            if path.exists():
                continue
            labels = rc.split_labels("ordering", frame, cfg7, sid, y)
            parts = []
            for v in ("tier1", "tier2", "tier3"):
                cats = [c for c in cat if c in feats[v]] or None
                res = rc.fit_select(frame, labels, feats[v], y, "classification", "xgboost", cfg, cats, seed)
                parts.append(rc.chunk_rows(frame, labels, y, res, split_id=sid, variant=v, algorithm="xgboost", seed=seed))
            pd.concat(parts).to_parquet(path)
            print(f"[done] ordering seed{s} split {sid}", flush=True)


# ------------------------------------------------------------------------------------------------------------------------ A6
def physics_features(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    a6 = rc.REV / "a6"
    ids = pd.read_csv(a6 / "matched_mp_ids.csv").drop_duplicates("material_id").set_index("material_id")["p3_mp_material_id"]
    mag = pd.read_parquet(a6 / "magstruct_descriptors.parquet").set_index("mp_id")
    chg = pd.read_parquet(a6 / "chgnet_embedding.parquet").set_index("mp_id")
    mp = frame["material_id"].map(ids)
    add = pd.concat([mag.reindex(mp.to_numpy()).reset_index(drop=True), chg.reindex(mp.to_numpy()).reset_index(drop=True)], axis=1)
    p3 = pd.read_csv(rc.ROOT / "new_datasets/MMFD/phase3/data/phase3_master_dataset.csv",
                     usecols=["material_id", "p3_total_magnetization", "p3_nsites", "p3_num_magnetic_sites", "p3_magnetization_normalized_vol",
                              "p3_is_magnetic"]).set_index("material_id").reindex(frame["material_id"]).reset_index(drop=True)
    add["magdft_moment_per_atom"] = p3["p3_total_magnetization"] / p3["p3_nsites"]
    add["magdft_mag_site_fraction"] = p3["p3_num_magnetic_sites"] / p3["p3_nsites"]
    add["magdft_magnetization_vol"] = p3["p3_magnetization_normalized_vol"]
    add["magdft_is_magnetic"] = p3["p3_is_magnetic"].map({True: 1.0, False: 0.0, "True": 1.0, "False": 0.0})
    groups = {"magstruct": list(mag.columns), "chgnet": list(chg.columns), "magdft": DFT_MAG}
    return pd.concat([frame.reset_index(drop=True), add], axis=1), groups


def a6(target: str) -> None:
    cfg, cfg7 = rc.setup(target)
    task = "classification" if target == "ordering" else "regression"
    frame = rc.matched_frame(target, cfg)
    frame, groups = physics_features(frame)
    y = rc.encode(frame["value"]) if task == "classification" else frame["value"].to_numpy(dtype=float)
    tiers = rc.p7.variant_features(cfg, cfg7)
    variants = {"tier1": tiers["tier1"], "tier3": tiers["tier3"],
                "tier1_magstruct": tiers["tier1"] + groups["magstruct"],
                "tier3_magstruct": tiers["tier3"] + groups["magstruct"],
                "tier3_chgnet": tiers["tier3"] + groups["chgnet"]}
    if target == "curie":   # experimental Tc labels: DFT magnetic outputs are not label leakage here
        variants["tier3_magdft"] = tiers["tier3"] + groups["magdft"]
        variants["tier3_magstruct_magdft"] = tiers["tier3"] + groups["magstruct"] + groups["magdft"]
    cat = cfg["predictor_rules"]["categorical_predictors"]
    out = rc.REV / "a6" / "fits" / target
    out.mkdir(parents=True, exist_ok=True)
    coverage = {g: float(frame[cols].notna().any(axis=1).mean()) for g, cols in groups.items()}
    print(f"{target}: N={len(frame)}; feature coverage {coverage}", flush=True)
    for sid in rc.SPLITS:
        path = out / f"split__{sid}.parquet"
        if path.exists():
            continue
        labels = rc.split_labels(target, frame, cfg7, sid, y)
        parts = []
        for v, feats in variants.items():
            cats = [c for c in cat if c in feats] or None
            for alg in ALGS:
                res = rc.fit_select(frame, labels, feats, y, task, alg, cfg, cats)
                parts.append(rc.chunk_rows(frame, labels, y, res, split_id=sid, variant=v, algorithm=alg).assign(refit_seconds=res["refit_seconds"]))
        pd.concat(parts).to_parquet(path)
        print(f"[done] a6 {target} split {sid}", flush=True)


# ------------------------------------------------------------------------------------------------------------------------ A5
def a5() -> None:
    cfg, cfg7 = rc.setup("ms_moment")
    frame = rc.matched_frame("ms_moment", cfg)
    cell = pd.read_parquet(rc.ROOT / "final/work/peratom_cell_map.parquet").set_index("material_id")["cell_atoms_numerator"]
    frame["cell_atoms"] = frame["material_id"].map(cell)
    frame = frame[frame["cell_atoms"].notna() & (frame["cell_atoms"] > 0)].reset_index(drop=True)
    fu_atoms = frame["reduced_formula"].drop_duplicates()
    fu_atoms = dict(zip(fu_atoms, fu_atoms.map(lambda f: Composition(f).num_atoms)))
    frame["fu_atoms"] = frame["reduced_formula"].map(fu_atoms)
    frame["m_cell"] = frame["value"]
    frame["value"] = frame["m_cell"] * frame["fu_atoms"] / frame["cell_atoms"]
    frame[rc.p7.DERIVED_NSITES_COLUMN] = frame["p3_volume"] / frame["p3_volume_per_atom"]
    tiers = rc.p7.variant_features(cfg, cfg7)
    variants = {"tier1": tiers["tier1"], "tier2": tiers["tier2"], "tier3": tiers["tier3"],
                "tier2_sitecount": tiers["tier2"] + [rc.p7.DERIVED_NSITES_COLUMN]}
    cat = cfg["predictor_rules"]["categorical_predictors"]
    out = rc.REV / "a5" / "fits"
    out.mkdir(parents=True, exist_ok=True)
    frame[["material_id", "reduced_formula", "m_cell", "value", "fu_atoms", "cell_atoms"]].to_parquet(rc.REV / "a5" / "per_fu_target.parquet")
    print(f"moment per f.u.: N={len(frame)} (excluded {10852 - len(frame)} rows without a verified cell atom count)", flush=True)
    y = frame["value"].to_numpy(dtype=float)
    for sid in rc.SPLITS:
        labels = None
        for v, feats in variants.items():
            path = out / f"split__{sid}__{v}.parquet"      # one file per split x variant, so short runs keep their work
            if path.exists():
                continue
            labels = rc.split_labels("ms_moment", frame, cfg7, sid) if labels is None else labels
            cats = [c for c in cat if c in feats] or None
            parts = [rc.chunk_rows(frame, labels, y, rc.fit_select(frame, labels, feats, y, "regression", alg, cfg, cats),
                                   split_id=sid, variant=v, algorithm=alg) for alg in ALGS]
            pd.concat(parts).to_parquet(path)
            print(f"[done] a5 split {sid} {v}", flush=True)


# ------------------------------------------------------------------------------------------------------------------------ A12
def a12(target: str) -> None:
    import run_phase8_leave_chemsys as lc   # EDA/src is on sys.path via rev_common
    rc.p7.install_diagnostic_algorithm()
    cfg7 = rc.p7.load_phase7_config()
    cfg, task, frame, feats, y, params = lc.load(target)
    out = rc.REV / "a12" / target
    out.mkdir(parents=True, exist_ok=True)
    ms = cfg7["multisplit"]
    for i in range(10):
        path = out / f"split__{i}.parquet"
        if path.exists():
            continue
        labels = rc.p7.random_group_split(frame["chemsys"], y.astype(float), ms["fractions"], rc.p7.split_seed(cfg7, i), ms["n_strata_bins"],
                                          ms["capacity_tolerance"])
        te = labels == "test"
        test_formulas = set(frame.loc[te, "reduced_formula"])
        regimes = {"B_system_held_out": np.isin(labels, ["train", "validation"]),
                   "A_formula_held_out": (~te) & ~frame["reduced_formula"].isin(test_formulas).to_numpy()}
        parts = []
        for name, trval in regimes.items():
            model = rc.pm.fit(rc.pm.build_estimator("xgboost", task, params, cfg["random_seed"]), "xgboost", task, frame.loc[trval, feats], y[trval])
            pred = model.predict(frame.loc[te, feats])
            shares = float(frame.loc[te, "chemsys"].isin(set(frame.loc[trval, "chemsys"])).mean())
            parts.append(pd.DataFrame({"split_id": i, "regime": name, "material_id": frame.loc[te, "material_id"].to_numpy(),
                                       "reduced_formula": frame.loc[te, "reduced_formula"].to_numpy(), "chemsys": frame.loc[te, "chemsys"].to_numpy(),
                                       "y_true": y[te], "y_pred": pred, "n_trainval": int(trval.sum()), "test_share_chemsys_in_train": shares}))
        pd.concat(parts).to_parquet(path)
        print(f"[done] a12 {target} split {i}", flush=True)


# ------------------------------------------------------------------------------------------------------------------------ A8
def a8() -> None:
    cfg, _ = rc.setup("ordering")
    frame, feats = rc.pm.load_modeling_frame(cfg, "ordering", "tier1", rc.p7.split_dir("v1.3") / "split_ordering.csv")
    frame = frame.reset_index(drop=True)
    y = rc.encode(frame["value"])
    labels = frame["split"].to_numpy()
    out = rc.REV / "a8"
    out.mkdir(parents=True, exist_ok=True)
    for alg in ALGS:
        path = out / f"ordering_tier1_frozen__{alg}.parquet"
        if path.exists():
            continue
        res = rc.fit_select(frame, labels, feats, y, "classification", alg, cfg)
        rc.chunk_rows(frame, labels, y, res, algorithm=alg).assign(_source=frame.loc[labels == "test", "_source"].to_numpy()).to_parquet(path)
        print(f"[done] a8 {alg}", flush=True)


def main() -> None:
    cmd = sys.argv[1]
    if cmd == "ordering_seeds":
        ordering_seeds()
    elif cmd == "a6":
        a6(sys.argv[2])
    elif cmd == "a5":
        a5()
    elif cmd == "a12":
        a12(sys.argv[2])
    elif cmd == "a8":
        a8()
    else:
        raise SystemExit(f"unknown command {cmd}")


if __name__ == "__main__":
    main()
