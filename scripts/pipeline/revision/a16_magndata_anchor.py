"""A16 (round-3 review R2-1): MAGNDATA as an independent anchor for the ordering labels of Materials Project (MP) and of the experimental sources.

Why: MP and the experimental sources agree on 28% of 949 formulas (kappa 0.00), but nothing says which side is wrong. MAGNDATA holds
neutron-determined magnetic structures. Here each structure is labelled FM / AFM / FiM from its own moments (never from page text), and both
sources are scored against that label on the formulas they share.

Input: a folder of MAGNDATA .mcif files obtained through the official repository download (registered academic account, usage conditions
accepted by the user; see magndata_download.html on cryst.ehu.es). The script itself downloads nothing.

Labelling (per file, pymatgen): formula = composition of the file's structure; moments = the file's magnetic moment vectors.
  * incommensurate entries (modulated structures) -> label 'incommensurate' (not used);
  * non-collinear (moment vectors not all parallel/antiparallel, sine of the angle > 0.02) -> 'noncollinear' (not used);
  * collinear -> pymatgen CollinearMagneticStructureAnalyzer.ordering -> FM / AFM / FiM (NM / unknown -> 'other', not used);
  * disordered (partial occupancy; pymatgen refuses) -> 'disordered' (not used); other failures -> 'unparseable' (not used, error recorded).
Files named '._*' (macOS AppleDouble metadata stubs inside the official archive) are skipped, not parsed.
Anchor per composition: the modal label of its collinear entries (conflicting entries are counted and reported).
Source labels: the A2 definition (modal ordering label per provenance, NM kept as a fourth label), matched by COMPOSITION KEY, not by string
(the formula-string trap, project memory).

Outputs (final/revision/outputs/a16_magndata_anchor/): magndata_entries.csv, anchor_by_composition.csv, anchor_agreement.csv,
anchor_confusion_MP.csv, anchor_confusion_experimental.csv, three_way.csv
Run (repository root):  python final/revision/scripts/a16_magndata_anchor.py <folder with .mcif files> [--parse-only]
"""
from __future__ import annotations

import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import rev_common as rc

sys.path.insert(0, str(rc.ROOT / "new_materials_finding" / "external_audit"))
from audit_common import composition_key  # noqa: E402

OUT = rc.REV / "a16_magndata_anchor"
N_BOOT, SEED = 1000, 20261110
COLLINEAR_SINE, MIN_MOMENT = 0.02, 0.05
NAMES = np.array(["FM", "AFM", "FiM", "NM"])
USED = ("FM", "AFM", "FiM")


def moment_vectors(structure) -> np.ndarray:
    out = []
    for m in structure.site_properties.get("magmom") or []:
        out.append(np.asarray(m.moment if hasattr(m, "moment") else [0.0, 0.0, float(m)], dtype=float))
    return np.array(out).reshape(-1, 3)


def signed_scalars(vectors: np.ndarray) -> np.ndarray | None:
    """Signed moments along the common axis if all moment vectors are collinear, else None."""
    norms = np.linalg.norm(vectors, axis=1)
    big = norms > MIN_MOMENT
    if not big.any():
        return np.zeros(len(vectors))
    ref = vectors[np.argmax(norms)] / norms.max()
    cross = np.linalg.norm(np.cross(vectors[big], ref), axis=1) / norms[big]
    return vectors @ ref if (cross < COLLINEAR_SINE).all() else None


def entry_id(text: str, path: Path) -> str:
    m = re.search(r"Database entry:\s*(\S+)", text) or re.match(r"(\d+\.\d+)", path.name)
    return m.group(1) if m else path.stem


def label_file(path: Path) -> dict:
    from pymatgen.analysis.magnetism.analyzer import CollinearMagneticStructureAnalyzer
    from pymatgen.core import Structure

    text = path.read_text(encoding="utf-8", errors="replace")
    row = {"file": path.name, "entry": entry_id(text, path), "formula": None, "key": None, "ordering": "unparseable", "net_moment_muB": np.nan}
    incommensurate = bool(re.search(r"_cell_modulation_dimension\s+[1-9]", text))
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            s = Structure.from_file(str(path))
        row["formula"], row["key"] = s.composition.reduced_formula, composition_key(s.composition.reduced_formula)
        if incommensurate:
            row["ordering"] = "incommensurate"
            return row
        scalars = signed_scalars(moment_vectors(s))
        if scalars is None:
            row["ordering"] = "noncollinear"
            return row
        s2 = s.copy()
        s2.add_site_property("magmom", list(scalars))
        row["net_moment_muB"] = float(scalars.sum())
        row["ordering"] = {"FM": "FM", "AFM": "AFM", "FiM": "FiM"}.get(CollinearMagneticStructureAnalyzer(s2).ordering.name, "other")
    except Exception as exc:  # noqa: BLE001 - recorded in the output, not hidden
        row["error"] = f"{type(exc).__name__}: {str(exc)[:100]}"
        if incommensurate:
            row["ordering"] = "incommensurate"
        elif "isordered" in str(exc):
            row["ordering"] = "disordered"   # partial occupancy: pymatgen cannot label it; reported, not used
    return row


def anchor_table(entries: pd.DataFrame) -> pd.DataFrame:
    ok = entries[entries["ordering"].isin(USED) & entries["key"].notna()]
    g = ok.groupby("key")["ordering"]
    out = pd.DataFrame({"anchor": g.agg(lambda s: s.value_counts().index[0]), "n_entries": g.size(), "n_labels": g.nunique()})
    return out.reset_index().assign(conflict=lambda d: d["n_labels"] > 1)


def source_labels() -> pd.DataFrame:
    import a2_provenance as a2
    _, frame, _, y = a2.load()
    frame = frame.assign(label=NAMES[y], key=[composition_key(f) for f in frame["reduced_formula"]]).dropna(subset=["key"])
    return frame.groupby(["key", "prov"])["label"].agg(lambda s: s.value_counts().index[0]).unstack()


def kappa(a: np.ndarray, b: np.ndarray) -> float:
    labs = sorted(set(a) | set(b))
    cm = np.array([[np.sum((a == i) & (b == j)) for j in labs] for i in labs], dtype=float)
    n = cm.sum()
    pe = (cm.sum(0) * cm.sum(1)).sum() / n ** 2
    return float((np.trace(cm) / n - pe) / (1 - pe)) if pe < 1 else float("nan")


def agreement_rows(joined: pd.DataFrame) -> tuple[list[dict], dict]:
    rng, rows, tables = np.random.default_rng(SEED), [], {}
    for prov in ("MP", "experimental"):
        d = joined.dropna(subset=[prov])
        a, b = d["anchor"].to_numpy(), d[prov].to_numpy()
        row = {"source": prov, "n_compositions": len(d), "agreement": float(np.mean(a == b)) if len(d) else np.nan,
               "kappa": kappa(a, b) if len(d) > 1 else np.nan}
        if len(d) >= 20:
            boots = np.array([(np.mean(a[i] == b[i]), kappa(a[i], b[i])) for i in (rng.integers(0, len(a), len(a)) for _ in range(N_BOOT))])
            row.update(agreement_lo=np.nanquantile(boots[:, 0], .025), agreement_hi=np.nanquantile(boots[:, 0], .975),
                       kappa_lo=np.nanquantile(boots[:, 1], .025), kappa_hi=np.nanquantile(boots[:, 1], .975))
        for c in USED:
            m = a == c
            row[f"recall_{c}"] = float(np.mean(b[m] == c)) if m.any() else np.nan
            row[f"n_anchor_{c}"] = int(m.sum())
        rows.append(row)
        tables[prov] = pd.crosstab(d["anchor"].rename("MAGNDATA label"), d[prov].rename(f"{prov} label"))
    return rows, tables


def three_way(joined: pd.DataFrame) -> pd.DataFrame:
    d = joined.dropna(subset=["MP", "experimental"]).copy()
    d["MP_right"], d["exp_right"] = d["MP"] == d["anchor"], d["experimental"] == d["anchor"]
    d["MP_vs_exp_agree"] = d["MP"] == d["experimental"]
    return d.groupby(["MP_vs_exp_agree", "MP_right", "exp_right"]).size().rename("n_compositions").reset_index()


def main() -> None:
    folder = Path(sys.argv[1])
    all_files = sorted(folder.rglob("*.mcif"))
    files = [f for f in all_files if not f.name.startswith("._")]   # '._*' = macOS AppleDouble metadata stubs from the archive, not structures
    print(f"{len(all_files)} .mcif paths; {len(all_files) - len(files)} AppleDouble '._' stubs skipped; {len(files)} structure files", flush=True)
    if not files:
        raise SystemExit(f"no .mcif files under {folder}")
    OUT.mkdir(parents=True, exist_ok=True)
    entries = pd.DataFrame([label_file(f) for f in files])
    entries.to_csv(OUT / "magndata_entries.csv", index=False)
    print(f"{len(entries)} files; labels:\n{entries['ordering'].value_counts().to_string()}", flush=True)
    anchor = anchor_table(entries)
    anchor.to_csv(OUT / "anchor_by_composition.csv", index=False)
    print(f"{len(anchor)} compositions with a collinear FM/AFM/FiM label; {int(anchor['conflict'].sum())} with conflicting entries", flush=True)
    if "--parse-only" in sys.argv:
        return
    src = source_labels()
    joined = anchor.merge(src, left_on="key", right_index=True, how="left")
    rows, tables = agreement_rows(joined)
    pd.DataFrame(rows).to_csv(OUT / "anchor_agreement.csv", index=False)
    for prov, t in tables.items():
        t.to_csv(OUT / f"anchor_confusion_{prov}.csv")
        print(f"\nMAGNDATA vs {prov}:\n{t.to_string()}")
    tw = three_way(joined)
    tw.to_csv(OUT / "three_way.csv", index=False)
    pd.set_option("display.width", 200)
    print("\n", pd.DataFrame(rows).round(3).to_string(index=False), "\n\nthree-way (MP vs experimental vs MAGNDATA):\n", tw.to_string(index=False))


if __name__ == "__main__":
    main()
