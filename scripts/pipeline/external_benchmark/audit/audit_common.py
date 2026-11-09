"""Shared helpers for the external Curie benchmark audit (PLAN.md in this folder)."""
from __future__ import annotations

import re
from collections.abc import Iterator, Sequence
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
NMF = HERE.parent                                   # new_materials_finding/
ROOT = NMF.parent                                   # project root
EXTERNAL_CSV = NMF / "external_data" / "malaei_Magnetic_data" / "curie_temperature_of_ferromagnetic_materials.csv"
SEED, N_BOOT = 20261109, 10_000

_DOI_PREFIX = re.compile(r"^(https?://)?(dx\.)?doi\.org/")


def doi_set(value: object) -> frozenset[str]:
    """All DOIs in a cell, normalised: lower case, no URL prefix, no 'doi:' tag, no brackets or trailing dot.
    '[10.1/a, 10.2/b]' gives two DOIs; a book reference ('Magnetism and Magnetic Materials (Coey)') gives none."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return frozenset()
    out = set()
    for part in re.split(r",\s*", str(value).lower().strip().strip("[]")):
        part = re.sub(r"^doi:\s*", "", _DOI_PREFIX.sub("", part.strip())).strip().rstrip(".")
        if part.startswith("10."):
            out.add(part)
    return frozenset(out)


def composition_key(formula: str) -> str | None:
    """Spelling-independent composition identity: sorted element:atomic-fraction pairs, fractions rounded to 6 decimals.
    'Ca0.33La0.57Mn1O3' and 'Ca33La57Mn100O300' give the same key. Unparseable strings give None."""
    from pymatgen.core import Composition
    try:
        frac = Composition(formula).fractional_composition.get_el_amt_dict()
    except (ValueError, KeyError, TypeError, AttributeError):
        return None
    return ";".join(f"{e}:{round(v, 6):.6f}" for e, v in sorted(frac.items()))


def paper_clusters(dois: Sequence[frozenset[str]], references: Sequence[str]) -> np.ndarray:
    """Cluster id per record: records sharing any DOI are linked (union-find); a record with no DOI is clustered by its reference string."""
    parent = list(range(len(dois)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    owner: dict[str, int] = {}
    for i, (ds, ref) in enumerate(zip(dois, references)):
        keys = ds if ds else {"ref:" + str(ref).strip().lower()}
        for k in keys:
            if k in owner:
                parent[find(i)] = find(owner[k])
            else:
                owner[k] = i
    roots = [find(i) for i in range(len(dois))]
    # canonical labels: clusters numbered by first appearance in record order, so the labels (and therefore the seeded bootstrap)
    # do not depend on set iteration order, which changes with Python's per-process hash seed
    first_seen: dict[int, int] = {}
    return np.array([first_seen.setdefault(r, len(first_seen)) for r in roots])


def fraction_vectors(formulas: Sequence[str], elements: Sequence[str]) -> np.ndarray:
    """Element-fraction matrix (rows sum to 1) over a fixed element list."""
    from pymatgen.core import Composition
    index = {e: i for i, e in enumerate(elements)}
    out = np.zeros((len(formulas), len(elements)))
    for r, f in enumerate(formulas):
        for el, amt in Composition(f).fractional_composition.items():
            out[r, index[el.symbol]] = amt
    return out


def nearest_tv_distance(query: np.ndarray, reference: np.ndarray, k: int = 1, chunk: int = 256) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Total-variation distance 0.5*sum|p-q| = 1 - sum min(p, q) (rows sum to 1) from each query row to the reference rows.
    Only elements present in a query chunk can contribute to the overlap, so memory stays at chunk x n_reference.
    Returns (distance to the nearest, mean distance to the k nearest, index of the nearest reference row)."""
    nearest, mean_k, idx = np.empty(len(query)), np.empty(len(query)), np.empty(len(query), dtype=int)
    kk = min(k, len(reference))
    ref = reference.astype(np.float64)
    for s in range(0, len(query), chunk):
        q = query[s:s + chunk]
        overlap = np.zeros((len(q), len(ref)))
        for e in np.flatnonzero(q.any(axis=0)):
            overlap += np.minimum(q[:, e:e + 1], ref[:, e])
        d = np.clip(1.0 - overlap, 0.0, 1.0)
        part = np.partition(d, kth=kk - 1, axis=1)[:, :kk]
        nearest[s:s + chunk] = part.min(axis=1)
        mean_k[s:s + chunk] = part.mean(axis=1)
        idx[s:s + chunk] = d.argmin(axis=1)
    return nearest, mean_k, idx


def cluster_weights(clusters: np.ndarray, n_boot: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Cluster bootstrap as multinomial weights: returns (cluster code per row, n_boot x n_clusters weight matrix).
    Drawing K clusters with replacement == each cluster's draw count ~ Multinomial(K, 1/K)."""
    _, codes = np.unique(clusters, return_inverse=True)
    k = codes.max() + 1
    weights = np.random.default_rng(seed).multinomial(k, np.full(k, 1.0 / k), size=n_boot).astype(float)
    return codes, weights


def weighted_metrics(codes: np.ndarray, weights: np.ndarray, y: np.ndarray, pred: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> dict[str, np.ndarray]:
    """MAE, R2, coverage and mean width for every bootstrap replicate, from cluster-level sums (exact for a cluster bootstrap)."""
    k = weights.shape[1]

    def csum(v: np.ndarray) -> np.ndarray:
        return np.bincount(codes, weights=v, minlength=k)

    n = weights @ csum(np.ones_like(y))
    err = np.abs(pred - y)
    sy, syy, sres = weights @ csum(y), weights @ csum(y * y), weights @ csum((y - pred) ** 2)
    with np.errstate(invalid="ignore", divide="ignore"):
        ss_tot = syy - sy ** 2 / n
        return {"mae_k": weights @ csum(err) / n, "r2": 1 - sres / ss_tot,
                "coverage": weights @ csum(((y >= lo) & (y <= hi)).astype(float)) / n,
                "mean_width_k": weights @ csum(hi - lo) / n, "share_within_50k": weights @ csum((err <= 50).astype(float)) / n}


def weighted_median_ae(codes: np.ndarray, weights: np.ndarray, err: np.ndarray, block: int = 1000) -> np.ndarray:
    """Median absolute error for every replicate: lower weighted median of the row errors with row weight = its cluster's draw count."""
    order = np.argsort(err)
    e_sorted, c_sorted = err[order], codes[order]
    out = np.empty(weights.shape[0])
    for s in range(0, weights.shape[0], block):
        w = weights[s:s + block][:, c_sorted]
        cum = np.cumsum(w, axis=1)
        half = cum[:, -1:] / 2.0
        out[s:s + block] = e_sorted[np.argmax(cum >= half, axis=1)]
    return out


def metrics(y: np.ndarray, pred: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> dict[str, float]:
    """MAE, median AE, R2 (against the sample's own mean), interval coverage, mean width, share within 50 K."""
    err = np.abs(pred - y)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return {"n": len(y), "mae_k": float(err.mean()), "median_ae_k": float(np.median(err)),
            "r2": 1 - float(((y - pred) ** 2).sum()) / ss_tot if ss_tot > 0 else np.nan,
            "coverage": float(((y >= lo) & (y <= hi)).mean()), "mean_width_k": float((hi - lo).mean()),
            "share_within_50k": float((err <= 50).mean())}


def cluster_bootstrap_indices(clusters: np.ndarray, n_boot: int, seed: int) -> Iterator[np.ndarray]:
    """Row-index arrays for a cluster bootstrap: draw as many clusters as exist, with replacement, keep all rows of each."""
    uniq = np.unique(clusters)
    members = {c: np.flatnonzero(clusters == c) for c in uniq}
    rng = np.random.default_rng(seed)
    for _ in range(n_boot):
        yield np.concatenate([members[c] for c in rng.choice(uniq, size=len(uniq), replace=True)])
