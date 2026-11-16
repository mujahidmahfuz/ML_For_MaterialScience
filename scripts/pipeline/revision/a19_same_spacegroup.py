"""A19 (round-3 review R1-3; plan item A6(e)): does the DFT descriptor join matter? Tier 1 -> Tier 3 on records whose source space group equals the
computed polymorph's.

The Tier 3 descriptors come from the most stable computed polymorph of each reduced formula. A measured Curie temperature may belong to another
structure, so a noisy join could hide a real descriptor effect. Test: score the saved per-split test predictions (A1; nothing is refitted) separately on
  (a) 'same'      : source space group parsed and equal to the polymorph's space-group number (the join is right);
  (b) 'different' : source space group parsed and different (the join is wrong);
  (c) 'none'      : no source space group reported; 'unresolved': reported but not parsable (both kept out of (a) and (b)).
Pooled Tier 1 -> Tier 3 improvement over the three algorithms (A14 definition) on (a), on (b), and the paired difference (a) - (b), per split with at
least MIN_ROWS test rows in each subset; refit-aware interval (Nadeau-Bengio) and formula bootstrap as in A1.

Claim rule, fixed before any result was seen:
  * if the pooled improvement on 'same' is a stable gain (A1 rule) and larger than on 'different', the noisy-join explanation is supported;
  * if it is indistinguishable from zero, report 'no detectable gain even where the join is correct' together with the minimum detectable effect,
    which weakens the explanation only for effects as large as that;
  * a positive point estimate whose interval includes zero is reported as inconclusive. The test is small by construction and can show only a large effect.

Parsing of source symbols (rules in order): (1) a number in brackets or 'No. n'; (2) a bare integer 1-230; (3) Strukturbericht names L2_1, D0_3, C15, B20 (fixed map);
(4) the international symbol via pymatgen (spaces, underscores and combining macrons normalised; a missing bar in cubic symbols such as Fd3m restored);
(5) a short alias list of non-standard settings (Pbnm, Pnam, P21/n, P21/a). Everything else is 'unresolved'.
Usage (repository root):  python final/revision/scripts/a19_same_spacegroup.py parse | run
Outputs: final/revision/outputs/a19_same_spacegroup/{sg_assignment.csv, category_counts.csv, same_spacegroup_tier13.csv}
"""
from __future__ import annotations

import re
import sys
import unicodedata
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "final/revision/outputs/a19_same_spacegroup"
MIN_ROWS = 5
STRUKTUR = {"L21": 225, "L2_1": 225, "D03": 225, "D0_3": 225, "C15": 227, "B20": 198}
ALIAS = {"Pbnm": 62, "Pnam": 62, "P21/n": 14, "P21/a": 14, "P21/c": 14, "P2_1/n": 14, "P2_1/a": 14, "P2_1/c": 14}


def _symbol_number(sym: str) -> int | None:
    from pymatgen.symmetry.groups import SpaceGroup
    warnings.filterwarnings("ignore")
    try:
        return int(SpaceGroup(sym).int_number)
    except Exception:  # noqa: BLE001 - not a valid symbol
        return None


def parse_sg(raw: object) -> tuple[int | None, str]:
    if raw is None or (isinstance(raw, float) and np.isnan(raw)) or str(raw).strip() == "":
        return None, "none"
    s = str(raw).strip()
    m = re.search(r"\((?:No\.?\s*)?(\d{1,3})\)", s) or re.search(r"\bNo\.?\s*(\d{1,3})\b", s)
    if m and 1 <= int(m.group(1)) <= 230:
        return int(m.group(1)), "number in text"
    if re.fullmatch(r"\d{1,3}", s) and 1 <= int(s) <= 230:
        return int(s), "integer"
    key = re.sub(r"[\s_]", "", s)
    proto = {k.replace("_", ""): v for k, v in STRUKTUR.items()}
    if key in proto:
        return proto[key], "prototype"
    t = unicodedata.normalize("NFD", s).replace("̅", "̄")
    t = re.sub(r"(\d)̄", r"-\1", t)
    t = re.sub(r"[̀-ͯ]", "", t)
    sym = re.sub(r"\s+", "", t).replace("_", "")
    sym = re.sub(r"\(.*?\)", "", sym)
    if sym in ALIAS:
        return ALIAS[sym], "alias"
    n = _symbol_number(sym)
    if n is not None:
        return n, "symbol"
    if "-" not in sym and "3" in sym:
        n = _symbol_number(sym.replace("3", "-3", 1))
        if n is not None:
            return n, "symbol, bar restored"
    return None, "unresolved"


def assignment() -> pd.DataFrame:
    cur = pd.read_csv(ROOT / "EDA/datasets/v1.4/targets/curie/target_curie_clean.csv", usecols=["material_id", "target_valid"], low_memory=False)
    cur = cur[cur["target_valid"] == True]  # noqa: E712
    meta = pd.read_csv(ROOT / "new_datasets/MMFD/data/metadata.csv", usecols=["material_id", "space_group"], low_memory=False)
    t3 = pd.read_parquet(ROOT / "EDA/datasets/v1.2/tiers/tier3_physics_v1.2.parquet", columns=["material_id", "p3_spacegroup_number"])
    d = t3.merge(cur[["material_id"]], on="material_id").merge(meta.drop_duplicates("material_id"), on="material_id", how="left")
    parsed = d["space_group"].map(parse_sg)
    d["source_sg_number"], d["parse_method"] = [p[0] for p in parsed], [p[1] for p in parsed]
    d["category"] = np.select(
        [d["parse_method"] == "none", d["parse_method"] == "unresolved", d["source_sg_number"] == d["p3_spacegroup_number"]],
        ["none", "unresolved", "same"], default="different")
    return d


def interval(d: np.ndarray, n_test: float, n_train: float) -> tuple[float, float, float, float]:
    J, mean = len(d), float(d.mean())
    se = float(d.std(ddof=1) * np.sqrt(1.0 / J + n_test / n_train))
    t = stats.t.ppf(0.975, J - 1)
    return mean, mean - t * se, mean + t * se, float((t + stats.t.ppf(0.80, J - 1)) * se)


def run() -> None:
    import a1_tier_inference as a1
    assign = assignment()
    assign.to_csv(OUT / "sg_assignment.csv", index=False)
    counts = assign["category"].value_counts().rename_axis("category").reset_index(name="rows")
    counts.to_csv(OUT / "category_counts.csv", index=False)
    cat = assign.set_index("material_id")["category"]
    df, _ = a1.regression_predictions("curie")
    algs = ["linear_clip", "gradient_boosting", "xgboost_seedmean"]
    df = df[df["algorithm"].isin(algs) & df["variant"].isin(["tier1", "tier3"])].copy()
    df["cat"] = df["material_id"].map(cat)
    n_all = a1.n_total("curie")
    rng = np.random.default_rng(a1.SEED + 9000)
    forms = pd.Index(sorted(df["reduced_formula"].unique()))
    counts_b = np.vstack([np.bincount(rng.integers(0, len(forms), len(forms)), minlength=len(forms)) for _ in range(a1.N_BOOT)])

    def per_split(cat_name: str) -> dict[str, tuple[float, np.ndarray, int]]:
        out = {}
        for s in a1.SPLITS:
            imps, boots, n_sub = [], [], 0
            for alg in algs:
                sub = df[(df["algorithm"] == alg) & (df["split_id"] == s) & (df["cat"] == cat_name)]
                a, b = sub[sub["variant"] == "tier1"].set_index("material_id"), sub[sub["variant"] == "tier3"].set_index("material_id")
                n_sub = len(a)
                if n_sub < MIN_ROWS:
                    imps = []
                    break
                b = b.loc[a.index]
                w = counts_b[:, forms.get_indexer(a["reduced_formula"])].astype(float)
                y, pa, pb = a["y_true"].to_numpy(), a["y_pred"].to_numpy(), b["y_pred"].to_numpy()
                imps.append(a1.improvement("regression", a1.metric_point(a, "regression"), a1.metric_point(b, "regression")))
                boots.append(a1.improvement("regression", a1.weighted_metric(y, pa, w, "regression"), a1.weighted_metric(y, pb, w, "regression")))
            if imps:
                out[s] = (float(np.mean(imps)), np.mean(boots, axis=0), int(n_sub))
        return out

    n_test_full = np.mean([df[(df["algorithm"] == algs[0]) & (df["split_id"] == s) & (df["variant"] == "tier1")].shape[0] for s in a1.SPLITS])
    n_train = n_all - n_test_full
    res = {c: per_split(c) for c in ("same", "different")}
    rows = []
    for c, r in res.items():
        if len(r) < 3:
            rows.append({"subset": c, "splits_used": len(r)})
            continue
        d = np.array([v[0] for v in r.values()])
        boot = np.mean([v[1] for v in r.values()], axis=0)
        n_rows = float(np.mean([v[2] for v in r.values()]))
        mean, lo, hi, mde = interval(d, n_rows, n_train)
        rows.append({"subset": c, "splits_used": len(r), "mean_test_rows_per_split": n_rows, "mean_improvement_K": mean, "nb_ci_low": lo, "nb_ci_high": hi,
                     "boot_ci_low": float(np.quantile(boot, .025)), "boot_ci_high": float(np.quantile(boot, .975)), "n_splits_positive": int((d > 0).sum()), "mde80_K": mde})
    common = sorted(set(res["same"]) & set(res["different"]))
    if len(common) >= 3:
        d = np.array([res["same"][s][0] - res["different"][s][0] for s in common])
        boot = np.mean([res["same"][s][1] - res["different"][s][1] for s in common], axis=0)
        mean, lo, hi, mde = interval(d, float(np.mean([res["same"][s][2] for s in common])), n_train)
        rows.append({"subset": "same minus different", "splits_used": len(common), "mean_improvement_K": mean, "nb_ci_low": lo, "nb_ci_high": hi,
                     "boot_ci_low": float(np.quantile(boot, .025)), "boot_ci_high": float(np.quantile(boot, .975)), "n_splits_positive": int((d > 0).sum()), "mde80_K": mde})
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "same_spacegroup_tier13.csv", index=False)
    pd.set_option("display.width", 220)
    print(counts.to_string(index=False))
    print(table.round(2).to_string(index=False))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == "parse":
        a = assignment()
        a.to_csv(OUT / "sg_assignment.csv", index=False)
        print(a["category"].value_counts().to_string())
        print(a["parse_method"].value_counts().to_string())
        un = a[a["parse_method"] == "unresolved"]["space_group"].astype(str).value_counts()
        print("unresolved symbols:", un.head(25).to_dict())
    else:
        run()
