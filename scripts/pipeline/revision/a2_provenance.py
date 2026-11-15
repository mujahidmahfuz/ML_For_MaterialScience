"""A2 (RR3): cross-provenance ordering, re-done on the shared label space with an appropriate reference.

(a) label agreement on formulas labelled by BOTH Materials Project (computed) and an experimental source: modal label per provenance,
    confusion matrix, raw agreement, Cohen's kappa (formula bootstrap CI).
(b) transfer on the shared FM/AFM/FiM label space (NM rows dropped everywhere): train on one provenance (training formulas that occur in the
    other provenance's test partition removed), select hyperparameters on that provenance's validation rows, test on the other
    provenance's test rows. Also the within-provenance reference (same model, own test rows). Raw and prior-corrected probabilities: the
    classifiers use balanced class weights, so the effective training prior is uniform; prior correction multiplies by the target domain's
    class prior estimated from its TRAINING partition (never its test set). Formula-cluster bootstrap CIs (1,000).
    Null: 20 refits with permuted training labels (best hyperparameters held fixed) -> empirical null of balanced accuracy.
(c) covariate shift: composition (TV) distance of each test formula to the nearest training formula, cross- vs within-provenance.
Claim rule (PLAN.md): "does not transfer" only if the upper balanced-accuracy limit is below the permutation null's 97.5th percentile.
Outputs: final/revision/outputs/a2/{label_agreement.csv, label_confusion.csv, transfer.csv, transfer_null.csv, distance_shift.csv}
"""
from __future__ import annotations

import ast
import sys

import numpy as np
import pandas as pd
from pymatgen.core import Composition
from sklearn.metrics import balanced_accuracy_score, f1_score

import rev_common as rc

sys.path.insert(0, str(rc.ROOT / "new_materials_finding" / "external_audit"))
from audit_common import fraction_vectors, nearest_tv_distance  # noqa: E402

OUT = rc.REV / "a2"
K3 = [0, 1, 2]           # FM, AFM, FiM
N_BOOT, N_PERM, SEED = 1000, 20, 20261110
DIRECTIONS = (("MP", "experimental"), ("experimental", "MP"), ("MP", "MP"), ("experimental", "experimental"))


def load():
    cfg, _ = rc.setup("ordering")
    frame, feats = rc.pm.load_modeling_frame(cfg, "ordering", "tier1", rc.p7.split_dir("v1.3") / "split_ordering.csv")
    frame = frame.reset_index(drop=True)
    frame["prov"] = np.where(frame["_source"].astype(str).str.startswith("mp_reformatted"), "MP", "experimental")
    return cfg, frame, feats, rc.encode(frame["value"])


def kappa(a: np.ndarray, b: np.ndarray) -> float:
    labs = sorted(set(a) | set(b))
    cm = np.array([[np.sum((a == i) & (b == j)) for j in labs] for i in labs], dtype=float)
    n = cm.sum()
    po, pe = np.trace(cm) / n, (cm.sum(0) * cm.sum(1)).sum() / n ** 2
    return float((po - pe) / (1 - pe))


def agreement(frame: pd.DataFrame) -> None:
    modal = frame.groupby(["reduced_formula", "prov"])["value"].agg(lambda s: s.value_counts().index[0]).unstack()
    both = modal.dropna()
    a, b = both["experimental"].to_numpy(), both["MP"].to_numpy()
    rng = np.random.default_rng(SEED)
    boots = np.array([(np.mean(a[ix] == b[ix]), kappa(a[ix], b[ix])) for ix in (rng.integers(0, len(a), len(a)) for _ in range(N_BOOT))])
    pd.DataFrame([{"n_formulas_both": len(both), "agreement": float(np.mean(a == b)), "agreement_lo": np.quantile(boots[:, 0], .025),
                   "agreement_hi": np.quantile(boots[:, 0], .975), "kappa": kappa(a, b), "kappa_lo": np.quantile(boots[:, 1], .025),
                   "kappa_hi": np.quantile(boots[:, 1], .975)}]).to_csv(OUT / "label_agreement.csv", index=False)
    ct = pd.crosstab(both["experimental"].rename("experimental label"), both["MP"].rename("MP label"))
    ct.to_csv(OUT / "label_confusion.csv")
    print(f"agreement on {len(both)} formulas: {np.mean(a == b):.3f}; kappa {kappa(a, b):.3f}\n{ct.to_string()}", flush=True)


def masks(frame: pd.DataFrame, y: np.ndarray, src: str, dst: str) -> tuple[np.ndarray, np.ndarray]:
    """Split labels for a src-trained model scored on dst test rows (NM removed everywhere)."""
    no_nm = y != 3
    test = (frame["prov"] == dst).to_numpy() & (frame["split"] == "test").to_numpy() & no_nm
    excl = frame["reduced_formula"].isin(set(frame.loc[test, "reduced_formula"])).to_numpy()
    in_src = (frame["prov"] == src).to_numpy() & no_nm & ~excl
    labels = np.where(test, "test", np.where(in_src & (frame["split"] == "validation").to_numpy(), "validation",
                                             np.where(in_src & (frame["split"] == "train").to_numpy(), "train", "unused")))
    return labels, test


def scores(y: np.ndarray, proba: np.ndarray, formulas: np.ndarray, prior: np.ndarray | None, seed: int) -> dict:
    p = proba[:, K3] if prior is None else proba[:, K3] * prior
    pred = np.array(K3)[p.argmax(1)]
    codes, uniq = pd.factorize(formulas)
    rng = np.random.default_rng(seed)
    ba_b, f1_b = [], []
    for _ in range(N_BOOT):
        w = np.bincount(rng.integers(0, len(uniq), len(uniq)), minlength=len(uniq))[codes]
        ba_b.append(balanced_accuracy_score(y, pred, sample_weight=w))
        f1_b.append(f1_score(y, pred, labels=K3, average="macro", sample_weight=w, zero_division=0))
    return {"balanced_accuracy": balanced_accuracy_score(y, pred), "ba_lo": np.quantile(ba_b, .025), "ba_hi": np.quantile(ba_b, .975),
            "macro_f1": f1_score(y, pred, labels=K3, average="macro", zero_division=0), "f1_lo": np.quantile(f1_b, .025),
            "f1_hi": np.quantile(f1_b, .975), **{f"recall_{c}": float((pred[y == k] == k).mean()) for k, c in zip(K3, ["FM", "AFM", "FiM"])}}


def permutation_null(cfg, sub, feats, ys, lab, params, src, dst) -> list[dict]:
    rng = np.random.default_rng(SEED)
    tr, te = np.isin(lab, ["train", "validation"]), lab == "test"
    out = []
    for k in range(N_PERM):
        yp = ys.copy()
        yp[tr] = rng.permutation(ys[tr])
        est = rc.pm.fit(rc.pm.build_estimator("xgboost", "classification", params, cfg["random_seed"]), "xgboost", "classification",
                        sub.loc[tr, feats], yp[tr])
        pr = np.zeros((int(te.sum()), 4))
        pr[:, np.asarray(est.classes_, dtype=int)] = est.predict_proba(sub.loc[te, feats])
        pred = np.array(K3)[pr[:, K3].argmax(1)]
        out.append({"train_on": src, "test_on": dst, "perm": k, "balanced_accuracy": balanced_accuracy_score(ys[te], pred),
                    "macro_f1": f1_score(ys[te], pred, labels=K3, average="macro", zero_division=0)})
    return out


def transfer(cfg: dict, frame: pd.DataFrame, feats: list[str], y: np.ndarray) -> None:
    rows, nulls = [], []
    for src, dst in DIRECTIONS:
        labels, _ = masks(frame, y, src, dst)
        keep = labels != "unused"
        sub, lab, ys = frame[keep].reset_index(drop=True), labels[keep], y[keep]
        dst_train = (frame["prov"] == dst).to_numpy() & (frame["split"] == "train").to_numpy() & (y != 3)
        prior = np.bincount(y[dst_train], minlength=4)[K3].astype(float)
        prior /= prior.sum()
        te = lab == "test"
        for alg in ("xgboost", "gradient_boosting"):
            res = rc.fit_select(sub, lab, feats, ys, "classification", alg, cfg)
            for name, pr in (("raw", None), ("prior-corrected", prior)):
                rows.append({"train_on": src, "test_on": dst, "algorithm": alg, "probabilities": name, "n_train": int((lab == "train").sum()),
                             "n_test": int(te.sum()), "target_prior_FM_AFM_FiM": "/".join(f"{v:.3f}" for v in prior),
                             **scores(ys[te], res["test_proba"], sub.loc[te, "reduced_formula"].to_numpy(), pr, SEED)})
            print(f"{src}->{dst} {alg}: BA raw {rows[-2]['balanced_accuracy']:.3f}, prior {rows[-1]['balanced_accuracy']:.3f}", flush=True)
            if alg == "xgboost" and src != dst:
                nulls += permutation_null(cfg, sub, feats, ys, lab, ast.literal_eval(res["best_params"]), src, dst)
                print("  permutation null done", flush=True)
        pd.DataFrame(rows).to_csv(OUT / "transfer.csv", index=False)
        pd.DataFrame(nulls).to_csv(OUT / "transfer_null.csv", index=False)


def distance_shift(frame: pd.DataFrame, y: np.ndarray) -> None:
    rows = []
    for src, dst in DIRECTIONS:
        labels, test = masks(frame, y, src, dst)
        tr_f = frame.loc[np.isin(labels, ["train", "validation"]), "reduced_formula"].unique()
        te_f = frame.loc[test, "reduced_formula"].unique()
        elements = sorted({el.symbol for f in np.concatenate([tr_f, te_f]) for el in Composition(f).elements})
        d, _, _ = nearest_tv_distance(fraction_vectors(te_f, elements), fraction_vectors(tr_f, elements))
        d = np.asarray(d).ravel()
        rows.append({"train_on": src, "test_on": dst, "n_test_formulas": len(te_f), "distance_median": float(np.median(d)),
                     "distance_mean": float(np.mean(d)), "distance_p90": float(np.quantile(d, .9))})
    pd.DataFrame(rows).to_csv(OUT / "distance_shift.csv", index=False)
    print(pd.DataFrame(rows).round(3).to_string(index=False), flush=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg, frame, feats, y = load()
    agreement(frame)
    distance_shift(frame, y)
    transfer(cfg, frame, feats, y)


if __name__ == "__main__":
    main()
