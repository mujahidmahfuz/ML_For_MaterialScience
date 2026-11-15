"""A6(b): magnetic-sublattice descriptors from the MP structure of each matched material (pymatgen).

Magnetic ion M = an element of the C1 magnetism-capable list (v1_3_curation_rules.yaml). Bridging anion X = O, S, Se, Te, N, P, As,
F, Cl, Br, I. Per structure (NaN where undefined, e.g. no M or no bridging anion):
  ms_mag_site_fraction     fraction of sites that are M
  ms_mag_number_density    M sites per A^3
  ms_mm_dmin               shortest M-M distance (A)
  ms_mm_dnn_mean           mean over M sites of the distance to the nearest other M site
  ms_mm_n_near             mean number of M neighbours within 1.15 x that site's nearest M-M distance (sublattice connectivity)
  ms_mx_dmean              mean nearest M-X distance (A)
  ms_mx_coordination       mean number of X within 1.2 x the site's nearest M-X distance
  ms_mxm_angle_mean        mean M-X-M angle (deg) over pairs of M bonded to the same X (bond = within 1.2 x that M's nearest M-X distance)
  ms_mxm_frac_linear       fraction of those angles in [150, 180] deg (strong antiferromagnetic superexchange geometry)
  ms_mxm_frac_right        fraction in [80, 100] deg (weak / ferromagnetic superexchange geometry, Goodenough-Kanamori)
Usage: python final/revision/scripts/a6_descriptors.py   ->  final/revision/outputs/a6/magstruct_descriptors.parquet (one row per mp_id)
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from pymatgen.core import Structure

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "final/revision/outputs/a6"
ANIONS = {"O", "S", "Se", "Te", "N", "P", "As", "F", "Cl", "Br", "I"}
RADIUS = 6.0          # neighbour search radius (A); larger than any M-M or M-X distance used below
NEAR_MM, NEAR_MX = 1.15, 1.20
COLUMNS = ["ms_mag_site_fraction", "ms_mag_number_density", "ms_mm_dmin", "ms_mm_dnn_mean", "ms_mm_n_near", "ms_mx_dmean",
           "ms_mx_coordination", "ms_mxm_angle_mean", "ms_mxm_frac_linear", "ms_mxm_frac_right"]


def magnetic_elements() -> set[str]:
    rules = yaml.safe_load((ROOT / "EDA/00_config/v1_3_curation_rules.yaml").read_text(encoding="utf-8"))
    # YAML reads the bare symbol `No` (nobelium) as boolean False; restore it
    return {"No" if e is False else str(e) for e in rules["curie"]["magnetism_capable_elements"]}


def angle(a: np.ndarray, center: np.ndarray, b: np.ndarray) -> float:
    u, v = a - center, b - center
    c = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))
    return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))


def describe(s: Structure, mag: set[str]) -> dict:
    out = dict.fromkeys(COLUMNS, np.nan)
    species = [site.specie.symbol for site in s]
    m_idx = [i for i, e in enumerate(species) if e in mag]
    out["ms_mag_site_fraction"] = len(m_idx) / len(s)
    out["ms_mag_number_density"] = len(m_idx) / s.volume
    if not m_idx:
        return out
    neigh = s.get_all_neighbors(RADIUS)
    dnn, nnear, mxd, mxc = [], [], [], []
    for i in m_idx:
        mm = sorted(n.nn_distance for n in neigh[i] if n.specie.symbol in mag)
        if mm:
            dnn.append(mm[0])
            nnear.append(sum(d <= NEAR_MM * mm[0] for d in mm))
        mx = [n.nn_distance for n in neigh[i] if n.specie.symbol in ANIONS]
        if mx:
            mxd.append(min(mx))
            mxc.append(sum(d <= NEAR_MX * min(mx) for d in mx))
    if dnn:
        out["ms_mm_dmin"], out["ms_mm_dnn_mean"], out["ms_mm_n_near"] = min(dnn), float(np.mean(dnn)), float(np.mean(nnear))
    if mxd:
        out["ms_mx_dmean"], out["ms_mx_coordination"] = float(np.mean(mxd)), float(np.mean(mxc))
    # M-X-M angles are measured around every anion site in the cell, over its bonded M neighbours (periodic images included),
    # bond = within 1.2 x that anion's nearest M-X distance
    angles = []
    for j, e in enumerate(species):
        if e not in ANIONS:
            continue
        ms_ = [n for n in neigh[j] if n.specie.symbol in mag]
        if len(ms_) < 2:
            continue
        dmin = min(n.nn_distance for n in ms_)
        bonded = [n.coords for n in ms_ if n.nn_distance <= NEAR_MX * dmin]
        for a in range(len(bonded)):
            for b in range(a + 1, len(bonded)):
                angles.append(angle(bonded[a], s[j].coords, bonded[b]))
    if angles:
        ang = np.array(angles)
        out["ms_mxm_angle_mean"] = float(ang.mean())
        out["ms_mxm_frac_linear"] = float(((ang >= 150) & (ang <= 180)).mean())
        out["ms_mxm_frac_right"] = float(((ang >= 80) & (ang <= 100)).mean())
    return out


def main() -> None:
    mag = magnetic_elements()
    with gzip.open(OUT / "mp_structures.json.gz", "rt", encoding="utf-8") as f:
        structures = json.load(f)
    rows = []
    for k, (mid, d) in enumerate(structures.items()):
        rows.append({"mp_id": mid, **describe(Structure.from_dict(d), mag)})
        if (k + 1) % 500 == 0:
            print(f"{k + 1}/{len(structures)}", flush=True)
    df = pd.DataFrame(rows)
    df.to_parquet(OUT / "magstruct_descriptors.parquet", index=False)
    print(df[COLUMNS].describe().T.round(3).to_string())


if __name__ == "__main__":
    main()
