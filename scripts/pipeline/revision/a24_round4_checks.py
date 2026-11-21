"""A24-A28 (round-4 review, 2026-11-20): analyses for the required revision items R1-R5. Specification: final/revision/PLAN.md, items A24-A28,
written before these runs. Nothing is refitted.

Subcommands (repository root):
  python final/revision/scripts/a24_round4_checks.py provenance   # A24  lineage of the experimental compilations; Experimental flag; per-source agreement
  MP_API_KEY=... python final/revision/scripts/a24_round4_checks.py fetch   # A25 input: MP magnetism documents of the A23 entries (cached)
  python final/revision/scripts/a24_round4_checks.py decomp       # A25  decomposition of the MP-experiment disagreement
  python final/revision/scripts/a24_round4_checks.py curie        # A26  robustness of the Curie descriptor null; matched baselines; ordering by provenance
  python final/revision/scripts/a24_round4_checks.py clusters     # A27  cluster robustness of the external novelty results
  python final/revision/scripts/a24_round4_checks.py rescore      # A28  pooled ordering model scored against MAGNDATA-derived labels
Outputs: final/revision/outputs/a24_round4/*.csv
"""
from __future__ import annotations

import ast
import glob
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "new_materials_finding" / "external_audit"))

from audit_common import composition_key, doi_set  # noqa: E402

OUT = ROOT / "final/revision/outputs/a24_round4"
A23 = ROOT / "final/revision/outputs/a23_label_comparability"
A16 = ROOT / "final/revision/outputs/a16_magndata_anchor"
CLASSES = ["FM", "AFM", "FiM", "NM"]
LIGHT_RE = {"La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu"}
HEAVY_RE = {"Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"}
N_BOOT, SEED = 1000, 20261120
SPLITS = [str(i) for i in range(10)]


def save(df: pd.DataFrame, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / name, index=False)
    print(f"--- {name}\n{df.to_string(max_rows=60)}", flush=True)


def kappa(a: np.ndarray, b: np.ndarray) -> float:
    labs = sorted(set(a) | set(b))
    cm = np.array([[np.sum((a == i) & (b == j)) for j in labs] for i in labs], dtype=float)
    n = cm.sum()
    po, pe = np.trace(cm) / n, (cm.sum(0) * cm.sum(1)).sum() / n ** 2
    return float((po - pe) / (1 - pe)) if pe < 1 else float("nan")


def agree_boot(a: np.ndarray, b: np.ndarray) -> dict:
    rng = np.random.default_rng(SEED)
    bs = np.array([(np.mean(a[i] == b[i]), kappa(a[i], b[i])) for i in (rng.integers(0, len(a), len(a)) for _ in range(N_BOOT))])
    return {"n": len(a), "agreement": float(np.mean(a == b)), "agreement_lo": np.nanquantile(bs[:, 0], .025),
            "agreement_hi": np.nanquantile(bs[:, 0], .975), "kappa": kappa(a, b), "kappa_lo": np.nanquantile(bs[:, 1], .025),
            "kappa_hi": np.nanquantile(bs[:, 1], .975)}


# ------------------------------------------------------------------------------------------------ shared loaders
def ordering_target() -> pd.DataFrame:
    t = pd.read_csv(ROOT / "EDA/datasets/v1.3/targets/ordering/target_ordering_clean.csv", low_memory=False)
    t = t[t["ordering_valid"] == True].copy()  # noqa: E712
    t["prov"] = np.where(t["_source"].astype(str).str.startswith("mp_reformatted"), "MP", "experimental")
    t["value"] = t["magnetic_ordering_clean"]
    t["key"] = t["reduced_formula"].map(composition_key)
    return t


def modal(s: pd.Series) -> str:
    return s.value_counts().index[0]


def is_tied(s: pd.Series) -> bool:
    vc = s.value_counts()
    return len(vc) > 1 and vc.iloc[0] == vc.iloc[1]


def magndata_labels() -> pd.Series:
    a = pd.read_csv(A16 / "anchor_by_composition.csv")
    return a.set_index("key")["anchor"]


# ------------------------------------------------------------------------------------------------ A24 provenance
def tc_value(cell: object) -> float:
    if cell is None or (isinstance(cell, float) and np.isnan(cell)):
        return np.nan
    s = str(cell)
    if s.startswith("{"):
        try:
            s = str(ast.literal_eval(s).get("Value", ""))
        except (ValueError, SyntaxError):
            return np.nan
    m = re.search(r"-?\d[\d,]*\.?\d*", s)
    try:
        return float(m.group(0).replace(",", "")) if m else np.nan
    except ValueError:
        return np.nan


def pairs(df: pd.DataFrame, name_col: str, tc_col: str) -> pd.DataFrame:
    out = pd.DataFrame({"dois": df["DOI"].map(doi_set), "key": df[name_col].map(composition_key), "tc": df[tc_col].map(tc_value)})
    out = out[out["key"].notna() & out["dois"].map(len).gt(0)].explode("dois")
    return out.rename(columns={"dois": "doi"})


def provenance() -> None:
    nemad = pd.concat([pd.read_csv(ROOT / f, low_memory=False) for f in
                       ("new_datasets/nemad_magnetic.csv", "new_datasets/github_datasets_magnetic.csv")], ignore_index=True)
    ref = pairs(nemad, "Material_Name", "Curie(TC)")
    ref_pairs = set(zip(ref["doi"], ref["key"]))
    ref_dois = set(ref["doi"])
    ref_tc = ref.dropna(subset=["tc"]).groupby(["doi", "key"])["tc"].apply(list)
    rows = []
    for fname, name_col, tc_col in (("magnetic_materials.csv", "Material_Name", "Curie"),
                                    ("magnetic_anisotropy_materials.csv", "Material_Name", "Curie(TC)")):
        raw = pd.read_csv(ROOT / fname, low_memory=False)
        p = pairs(raw, name_col, tc_col)
        uniq = p.drop_duplicates(["doi", "key"])
        hit = uniq.apply(lambda r: (r["doi"], r["key"]) in ref_pairs, axis=1)
        both = p.dropna(subset=["tc"])
        both = both[both.apply(lambda r: (r["doi"], r["key"]) in ref_tc.index, axis=1)]
        close = [min(abs(t - x) for x in ref_tc[(d, k)]) <= 1.0 for d, k, t in zip(both["doi"], both["key"], both["tc"])]
        # The NEMAD copies we hold carry no per-paper DOIs (deviation logged in PLAN.md), so composition + value is the usable test:
        # share of compilation compositions present in NEMAD, and for compositions with a Curie value in both, the share within 1 K.
        ref_key_tc = ref.dropna(subset=["tc"]).groupby("key")["tc"].apply(list)
        comp = raw[name_col].map(composition_key).dropna()
        ck = pd.DataFrame({"key": raw[name_col].map(composition_key), "tc": raw[tc_col].map(tc_value)}).dropna()
        ck = ck[ck["key"].isin(ref_key_tc.index)]
        kclose = [min(abs(t - x) for x in ref_key_tc[k]) <= 1.0 for k, t in zip(ck["key"], ck["tc"])]
        rows.append({"file": fname, "rows": len(raw), "compositions": int(comp.nunique()),
                     "composition_share_in_nemad": float(comp.drop_duplicates().isin(set(ref["key"])).mean()),
                     "tc_rows_compared_by_composition": len(ck), "tc_within_1K_share_by_composition": float(np.mean(kclose)) if kclose else np.nan,
                     "rows_with_doi_and_formula": int(p.index.nunique()),
                     "doi_formula_pairs": len(uniq), "pairs_in_nemad": int(hit.sum()), "pair_share_in_nemad": float(hit.mean()),
                     "dois": int(uniq["doi"].nunique()), "doi_share_in_nemad": float(uniq["doi"].isin(ref_dois).mean()),
                     "tc_pairs_compared": len(both), "tc_within_1K_share": float(np.mean(close)) if close else np.nan,
                     "experimental_false_rows": int((raw["Experimental"].astype(str) == "False").sum())})
    lin = pd.DataFrame(rows)
    lin["verdict"] = np.where((lin["composition_share_in_nemad"] >= .5) & (lin["tc_within_1K_share_by_composition"] >= .8),
                              "consistent with NEMAD lineage", "lineage not established")
    save(lin, "a24_lineage.csv")

    t = ordering_target()
    exp = t[t["prov"] == "experimental"]
    save(exp.groupby(["_source", "Experimental"]).size().rename("rows").reset_index(), "a24_experimental_flag_counts.csv")
    anchor = magndata_labels()
    res = []
    for name, sub in (("all experimental rows", exp), ("Experimental flag True only", exp[exp["Experimental"].astype(str) == "True"])):
        e_mod = sub.groupby("reduced_formula")["value"].agg(modal)
        mp_mod = t[t["prov"] == "MP"].groupby("reduced_formula")["value"].agg(modal)
        both = pd.DataFrame({"e": e_mod, "m": mp_mod}).dropna()
        res.append({"comparison": "MP vs experimental", "experimental_rows": name, **agree_boot(both["e"].to_numpy(), both["m"].to_numpy())})
        ek = sub.groupby("key")["value"].agg(modal)
        ek = ek[ek.index.isin(anchor.index) & ek.isin(["FM", "AFM", "FiM", "NM"])]
        a = anchor.reindex(ek.index)
        res.append({"comparison": "experimental vs MAGNDATA", "experimental_rows": name, **agree_boot(ek.to_numpy(), a.to_numpy())})
        res.append({"comparison": "constant-AFM labeller vs MAGNDATA", "experimental_rows": name, "n": len(a),
                    "agreement": float(np.mean(a.to_numpy() == "AFM"))})
    save(pd.DataFrame(res), "a24_flag_sensitivity.csv")


# ------------------------------------------------------------------------------------------------ A25 decomposition
def fetch() -> None:
    from mp_api.client import MPRester
    ids = sorted(pd.read_csv(A23 / "mp_entries.csv")["material_id"].unique())
    rows = []
    with MPRester(os.environ["MP_API_KEY"]) as mpr:
        for i in range(0, len(ids), 500):
            for d in mpr.materials.magnetism.search(material_ids=ids[i:i + 500],
                                                    fields=["material_id", "ordering", "num_magnetic_sites", "nsites", "magmoms",
                                                            "types_of_magnetic_species"]):
                rows.append({"material_id": str(d.material_id), "ordering_magnetism": str(d.ordering), "num_magnetic_sites": d.num_magnetic_sites,
                             "nsites": d.nsites, "magmoms": json.dumps([float(x) for x in (d.magmoms or [])]),
                             "magnetic_species": ";".join(str(x) for x in (d.types_of_magnetic_species or []))})
    save(pd.DataFrame(rows).head(3), "a25_mp_magnetism_head.csv")
    pd.DataFrame(rows).to_csv(OUT / "a25_mp_magnetism.csv", index=False)


def recount(magmoms: str, label: str, thr: float = 0.5) -> str:
    m = np.array(json.loads(magmoms)) if isinstance(magmoms, str) else np.array([])
    big = m[np.abs(m) >= thr]
    if label != "FiM" or len(big) == 0:
        return label
    return "FM" if (np.all(big > 0) or np.all(big < 0)) else "FiM"


def k_vectors() -> pd.DataFrame:
    rows = []
    for f in glob.glob(str(ROOT / "new_datasets/magndata_official/mcifs/*.mcif")):
        name = os.path.basename(f)
        if name.startswith("._"):
            continue
        text = Path(f).read_text(encoding="utf-8", errors="ignore")
        ks = re.findall(r"^\s*k\d+\s+\[([^\]]*)\]", text, flags=re.M)
        nonzero = any(any(x not in ("0", "0.0") for x in k.split()) for k in ks)
        rows.append({"file": name, "n_k": len(ks), "k_nonzero": bool(nonzero)})
    return pd.DataFrame(rows)


def ent_label(e: pd.DataFrame) -> pd.DataFrame:
    """Representative MP entry per formula: lowest energy above hull among entries with a known ordering."""
    e = e[e["ordering"].isin(CLASSES)].sort_values("e_above_hull")
    return e.drop_duplicates("reduced_formula").set_index("reduced_formula")


def decomp() -> None:
    sys.path.insert(0, str(HERE))
    from a19_same_spacegroup import parse_sg
    t = ordering_target()
    entries = pd.read_csv(A23 / "mp_entries.csv").merge(pd.read_csv(OUT / "a25_mp_magnetism.csv"), on="material_id", how="left")
    exp, mp = t[t["prov"] == "experimental"], t[t["prov"] == "MP"]
    e_mod, m_mod = exp.groupby("reduced_formula")["value"].agg(modal), mp.groupby("reduced_formula")["value"].agg(modal)
    both = pd.DataFrame({"exp": e_mod, "mp": m_mod}).dropna()
    rep = ent_label(entries).reindex(both.index)
    both["mp_rep"] = rep["ordering"]
    both["n_mag_sites"] = rep["num_magnetic_sites"]
    both["mp_rep_recount"] = [recount(mm, lab) if isinstance(lab, str) else np.nan for mm, lab in zip(rep["magmoms"], rep["ordering"])]

    # association statistics on the modal labels (as in A2/A23)
    a, b = both["exp"].to_numpy(), both["mp"].to_numpy()
    ct = pd.crosstab(a, b)
    n = ct.values.sum()
    pr, pc = ct.sum(1) / n, ct.sum(0) / n
    labs = sorted(set(a) | set(b))
    prr, pcc = pr.reindex(labs, fill_value=0), pc.reindex(labs, fill_value=0)
    pe = float((prr * pcc).sum())
    kmax = (float(np.minimum(prr, pcc).sum()) - pe) / (1 - pe)
    po = float(np.mean(a == b))
    chi2 = stats.chi2_contingency(ct.values)[0]
    cramer = np.sqrt(chi2 / (n * (min(ct.shape) - 1)))
    cond = pd.crosstab(both["mp"], both["exp"], normalize="index").round(3)
    ties = {"exp_modal_ties": int(exp.groupby("reduced_formula")["value"].agg(is_tied).reindex(both.index).sum()),
            "mp_modal_ties": int(mp.groupby("reduced_formula")["value"].agg(is_tied).reindex(both.index).sum())}
    save(pd.DataFrame([{"n": int(n), "agreement": po, "kappa": kappa(a, b), "kappa_max": kmax, "pabak": (len(labs) * po - 1) / (len(labs) - 1),
                        "cramers_v": float(cramer), "chi2_p": float(stats.chi2_contingency(ct.values)[1]), **ties}]), "a25_association.csv")
    save(cond.reset_index(), "a25_p_exp_given_mp.csv")

    # strata
    rows = []
    rb = both.dropna(subset=["mp_rep"])
    rows.append({"stratum": "all, representative MP entry", **agree_boot(rb["exp"].to_numpy(), rb["mp_rep"].to_numpy()),
                 "exp_AFM_called_FM": float(np.mean(rb.loc[rb["exp"] == "AFM", "mp_rep"] == "FM"))})
    for lab, mask in (("one magnetic site in MP cell", rb["n_mag_sites"] == 1), ("two or more magnetic sites", rb["n_mag_sites"] >= 2),
                      ("no magnetic site (NM/unknown moment)", rb["n_mag_sites"].fillna(0) == 0)):
        s = rb[mask]
        if len(s) >= 10:
            rows.append({"stratum": lab, **agree_boot(s["exp"].to_numpy(), s["mp_rep"].to_numpy()),
                         "exp_AFM_called_FM": float(np.mean(s.loc[s["exp"] == "AFM", "mp_rep"] == "FM")) if (s["exp"] == "AFM").any() else np.nan,
                         "exp_AFM_n": int((s["exp"] == "AFM").sum())})
    rr = rb.dropna(subset=["mp_rep_recount"])
    rows.append({"stratum": "MP FiM recounted with |m| >= 0.5 muB", **agree_boot(rr["exp"].to_numpy(), rr["mp_rep_recount"].to_numpy()),
                 "mp_FiM_before": int((rr["mp_rep"] == "FiM").sum()), "mp_FiM_after": int((rr["mp_rep_recount"] == "FiM").sum())})
    save(pd.DataFrame(rows), "a25_strata.csv")

    # rare earths among exp-FM / MP-FiM
    def re_class(f: str) -> str:
        from pymatgen.core import Composition
        el = {str(e) for e in Composition(f).elements}
        lt, hv = bool(el & LIGHT_RE), bool(el & HEAVY_RE)
        return "light and heavy" if lt and hv else "light (La-Eu)" if lt else "heavy (Gd-Lu)" if hv else "no rare earth"
    ff = both[(both["exp"] == "FM") & (both["mp"] == "FiM")]
    re_tab = ff.index.to_series().map(re_class).value_counts().rename_axis("rare_earth").rename("exp_FM_mp_FiM_formulas").reset_index()
    ff_rep = rb[(rb["exp"] == "FM") & (rb["mp_rep"] == "FiM")]
    re_tab["note"] = f"of {len(ff_rep)} such formulas (representative entry), {int((ff_rep['mp_rep_recount'] == 'FM').sum())} become FM when only |m| >= 0.5 muB count"
    save(re_tab, "a25_rare_earth.csv")

    # phase-matched vs phase-mismatched
    exp2 = exp[exp["reduced_formula"].isin(both.index)].copy()
    meta = pd.read_csv(ROOT / "new_datasets/MMFD/data/metadata.csv", usecols=["material_id", "space_group"], low_memory=False)
    exp2 = exp2.merge(meta.drop_duplicates("material_id"), on="material_id", how="left")
    exp2["sg"] = [parse_sg(v)[0] for v in exp2["space_group"]]
    mp_sg = entries.groupby("reduced_formula")["sg_number"].apply(set)
    sg = exp2.dropna(subset=["sg"]).groupby("reduced_formula")["sg"].apply(set)
    matched = [f for f in sg.index if sg[f] & mp_sg.get(f, set())]
    mismatched = [f for f in sg.index if not (sg[f] & mp_sg.get(f, set()))]
    rng = np.random.default_rng(SEED)
    out = []
    for lab, fs in (("phase-matched (space group equal)", matched), ("phase-mismatched (space group differs)", mismatched)):
        s = both.loc[fs]
        out.append({"subset": lab, **agree_boot(s["exp"].to_numpy(), s["mp"].to_numpy()),
                    "exp_AFM_called_FM": float(np.mean(s.loc[s["exp"] == "AFM", "mp"] == "FM")), "exp_AFM_n": int((s["exp"] == "AFM").sum())})
    sm, sx = both.loc[matched], both.loc[mismatched]
    diff = [np.mean((x := sm.iloc[rng.integers(0, len(sm), len(sm))])["exp"] == x["mp"]) -
            np.mean((y := sx.iloc[rng.integers(0, len(sx), len(sx))])["exp"] == y["mp"]) for _ in range(N_BOOT)]
    out.append({"subset": "difference in agreement (matched minus mismatched)", "n": len(sm) + len(sx),
                "agreement": float(np.mean(sm["exp"] == sm["mp"]) - np.mean(sx["exp"] == sx["mp"])),
                "agreement_lo": float(np.quantile(diff, .025)), "agreement_hi": float(np.quantile(diff, .975))})
    save(pd.DataFrame(out), "a25_matched_vs_mismatched.csv")

    # MAGNDATA propagation vector strata
    kv = k_vectors()
    ent = pd.read_csv(A16 / "magndata_entries.csv").merge(kv, on="file", how="left")
    ent = ent[ent["ordering"].isin(["FM", "AFM", "FiM"])]
    kkey = ent.groupby("key")["k_nonzero"].agg(lambda s: bool(s.mean() >= .5))
    anchor = magndata_labels()
    rows = []
    for prov, sub in (("MP", mp), ("experimental", exp)):
        lab = sub.groupby("key")["value"].agg(modal)
        lab = lab[lab.index.isin(anchor.index)]
        for kname, kmask in (("k = 0 (fits the crystal cell)", False), ("k != 0 (needs a magnetic supercell)", True)):
            keys = [k for k in lab.index if k in kkey.index and bool(kkey[k]) == kmask]
            if len(keys) >= 10:
                rows.append({"source": prov, "magndata_k": kname, **agree_boot(lab.loc[keys].to_numpy(), anchor.loc[keys].to_numpy())})
    save(pd.DataFrame(rows), "a25_magndata_k.csv")
    save(pd.DataFrame([{"entries_parsed": len(kv), "entries_k_nonzero": int(kv["k_nonzero"].sum())}]), "a25_k_parse_counts.csv")


# ------------------------------------------------------------------------------------------------ A26 Curie null robustness
def nb(x: np.ndarray, ratio: float) -> tuple[float, float, float]:
    j = len(x)
    se = np.sqrt((1 / j + ratio) * np.var(x, ddof=1))
    t = stats.t.ppf(.975, j - 1)
    return float(x.mean()), float(x.mean() - t * se), float(x.mean() + t * se)


def curie() -> None:
    import a1_tier_inference as a1
    tier = pd.read_csv(ROOT / "paper/results/revision/a1_tier_inference.csv")
    rows, conc = [], []
    for target in ("curie", "ms_moment"):
        df, _ = a1.regression_predictions(target)
        ratio = float(tier.loc[tier["target"] == target, "test_over_train"].iloc[0])
        one = df[(df["split_id"] == "0") & (df["variant"] == "tier1") & (df["algorithm"] == "gradient_boosting")]
        full = pd.read_csv(ROOT / "EDA/02_splits/v1.3/matched_split_curie.csv") if target == "curie" else None
        if full is not None:
            vc = full["reduced_formula"].value_counts()
            conc.append({"target": target, "records": len(full), "formulas": len(vc), "largest_formula_records": int(vc.iloc[0]),
                         "top5_share": float(vc.iloc[:5].sum() / len(full))})
        for alg in ("gradient_boosting", "xgboost_seedmean", "linear_clip" if target == "curie" else "linear"):
            d = df[df["algorithm"] == alg]
            per = []
            for s in SPLITS:
                ds = d[d["split_id"] == s]
                m = {}
                for v in ("tier1", "tier3"):
                    dv = ds[ds["variant"] == v].assign(ae=lambda x: (x["y_true"] - x["y_pred"]).abs())
                    m[v] = (dv["ae"].mean(), dv.groupby("reduced_formula")["ae"].mean().mean(),
                            1 - ((dv["y_true"] - dv["y_pred"]) ** 2).sum() / ((dv["y_true"] - dv["y_true"].mean()) ** 2).sum())
                per.append((m["tier1"][0] - m["tier3"][0], m["tier1"][1] - m["tier3"][1], m["tier1"][0], m["tier1"][2], m["tier1"][1]))
            per = np.array(per)
            r_mae, r_mac = nb(per[:, 0], ratio), nb(per[:, 1], ratio)
            rows.append({"target": target, "algorithm": alg, "tier1_mae": per[:, 2].mean(), "tier1_r2": per[:, 3].mean(),
                         "tier1_formula_macro_mae": per[:, 4].mean(),
                         "gain_record_mae": r_mae[0], "gain_record_lo": r_mae[1], "gain_record_hi": r_mae[2],
                         "gain_formula_macro": r_mac[0], "gain_formula_macro_lo": r_mac[1], "gain_formula_macro_hi": r_mac[2]})
        if target == "curie":
            ceil = []
            gb = df[(df["algorithm"] == "gradient_boosting") & (df["variant"] == "tier1")]
            for s in SPLITS:
                ds = gb[gb["split_id"] == s]
                g = ds.groupby("reduced_formula")["y_true"]
                multi = ds[g.transform("size") >= 2]
                loo = [np.median(np.delete(v.to_numpy(), i)) for _, v in multi.groupby("reduced_formula")["y_true"] for i in range(len(v))]
                yt = [x for _, v in multi.groupby("reduced_formula")["y_true"] for x in v.to_numpy()]
                yp = [x for _, v in multi.groupby("reduced_formula")["y_pred"] for x in v.to_numpy()]
                ceil.append((np.mean(np.abs(np.array(yt) - np.array(loo))), np.mean(np.abs(np.array(yt) - np.array(yp))), len(yt)))
            ceil = np.array(ceil)
            save(pd.DataFrame([{"rows_in_repeated_formulas_per_split": ceil[:, 2].mean(), "loo_median_mae": ceil[:, 0].mean(),
                                "tier1_gb_mae_same_rows": ceil[:, 1].mean()}]), "a26_curie_noise_ceiling.csv")
    save(pd.DataFrame(conc), "a26_curie_concentration.csv")
    save(pd.DataFrame(rows), "a26_tier_contrasts_record_vs_formula.csv")

    # ordering: matched baselines and Tier 1 -> 3 by label provenance
    from sklearn.metrics import f1_score
    od, _ = a1.ordering_predictions()
    t = ordering_target()
    prov = t.set_index("material_id")["prov"]
    od["prov"] = od["material_id"].map(prov)
    out = []
    for alg in ("gradient_boosting", "xgboost"):
        for p in ("all", "MP", "experimental"):
            vals = []
            for s in SPLITS:
                ds = od[(od["algorithm"] == alg) & (od["split_id"] == s)]
                if p != "all":
                    ds = ds[ds["prov"] == p]
                f = {v: f1_score(ds.loc[ds["variant"] == v, "y_true"], ds.loc[ds["variant"] == v, "y_pred"], average="macro") for v in ("tier1", "tier3")}
                vals.append((f["tier1"], f["tier3"] - f["tier1"], int((ds["variant"] == "tier1").sum())))
            v = np.array(vals)
            out.append({"algorithm": alg, "label_provenance": p, "tier1_macro_f1": v[:, 0].mean(), "tier3_minus_tier1": v[:, 1].mean(),
                        "sd_across_splits": v[:, 1].std(ddof=1), "splits_better": int((v[:, 1] > 0).sum()), "test_rows_per_split": v[:, 2].mean()})
    save(pd.DataFrame(out), "a26_ordering_by_provenance.csv")


# ------------------------------------------------------------------------------------------------ A27 cluster robustness
def r2(y: np.ndarray, p: np.ndarray) -> float:
    return float(1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def clusters() -> None:
    d = pd.read_csv(ROOT / "paper/results/rq3_generalization/external_benchmark/similarity_records.csv", keep_default_na=False, na_values=[""])
    b = d[~d["excluded_primary"] & ~d["a7a_formula_in_repository"]].copy()
    b["err"] = b["tc_pred_k"] - b["tc_exp_k"]
    rows = []
    for lab, sub in (("unseen system", b[~b["a7_system_seen"]]), ("seen system", b[b["a7_system_seen"]])):
        jk = []
        for c in sub["paper_cluster"].unique():
            s = sub[sub["paper_cluster"] != c]
            jk.append((c, s["err"].abs().mean(), r2(s["tc_exp_k"].to_numpy(), s["tc_pred_k"].to_numpy())))
        jk = pd.DataFrame(jk, columns=["cluster", "mae", "r2"])
        big = sub["paper_cluster"].value_counts()
        rows.append({"subset": lab, "records": len(sub), "clusters": sub["paper_cluster"].nunique(),
                     "mae": sub["err"].abs().mean(), "r2": r2(sub["tc_exp_k"].to_numpy(), sub["tc_pred_k"].to_numpy()),
                     "jackknife_mae_min": jk["mae"].min(), "jackknife_mae_max": jk["mae"].max(),
                     "jackknife_r2_min": jk["r2"].min(), "jackknife_r2_max": jk["r2"].max(),
                     "largest_cluster_records": int(big.iloc[0]), "largest_cluster_examples": "; ".join(sub.loc[sub["paper_cluster"] == big.index[0], "name"].head(4))})
    save(pd.DataFrame(rows), "a27_jackknife.csv")
    rho_all = stats.spearmanr(b["d_comp_train"], b["err"].abs())[0]
    rd = b.groupby("paper_cluster")["d_comp_train"].rank() - b.groupby("paper_cluster")["d_comp_train"].transform(lambda s: s.rank().mean())
    re_ = b.groupby("paper_cluster")["err"].transform(lambda s: s.abs().rank()) - b.groupby("paper_cluster")["err"].transform(lambda s: s.abs().rank().mean())
    within = np.corrcoef(rd, re_)[0, 1]
    cl = b.groupby("paper_cluster").agg(d=("d_comp_train", "mean"), e=("err", lambda s: s.abs().mean()))
    save(pd.DataFrame([{"rho_records": rho_all, "rho_within_cluster": within, "rho_cluster_level": stats.spearmanr(cl["d"], cl["e"])[0],
                        "clusters": len(cl)}]), "a27_distance_rho.csv")


# ------------------------------------------------------------------------------------------------ A28 rescore against MAGNDATA
def rescore() -> None:
    anchor = magndata_labels()
    rows = []
    for s in SPLITS:
        z = np.load(ROOT / f"final/revision/outputs/a4/ordering/proba__{s}.npz", allow_pickle=True)
        df = pd.DataFrame({"f": z["f_te"], "src": z["src_te"], "y": [CLASSES[i] for i in z["y_te"]],
                           "pred": [CLASSES[i] for i in z["p_te"].argmax(1)]})
        df["key"] = df["f"].map(composition_key)
        df = df[df["key"].isin(anchor.index)]
        df["anchor"] = df["key"].map(anchor)
        df["prov"] = np.where(df["src"].astype(str).str.startswith("mp_reformatted"), "MP", "experimental")
        for p in ("all", "MP", "experimental"):
            x = df if p == "all" else df[df["prov"] == p]
            if len(x):
                rows.append({"split": s, "label_provenance": p, "rows": len(x), "acc_vs_dataset_label": float(np.mean(x["pred"] == x["y"])),
                             "acc_vs_magndata": float(np.mean(x["pred"] == x["anchor"])), "dataset_label_vs_magndata": float(np.mean(x["y"] == x["anchor"]))})
    r = pd.DataFrame(rows)
    save(r.groupby("label_provenance").agg(rows_per_split=("rows", "mean"), acc_vs_dataset_label=("acc_vs_dataset_label", "mean"),
                                           acc_vs_magndata=("acc_vs_magndata", "mean"), dataset_label_vs_magndata=("dataset_label_vs_magndata", "mean"),
                                           acc_vs_dataset_sd=("acc_vs_dataset_label", "std"), acc_vs_magndata_sd=("acc_vs_magndata", "std")).reset_index(),
         "a28_rescore_magndata.csv")


if __name__ == "__main__":
    {"provenance": provenance, "fetch": fetch, "decomp": decomp, "curie": curie, "clusters": clusters, "rescore": rescore}[sys.argv[1]]()
