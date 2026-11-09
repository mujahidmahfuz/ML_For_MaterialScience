"""Build a run workspace for the pipeline code in scripts/pipeline/.

The pipeline code is the exact code that produced the results (see scripts/pipeline/PATCHES.md). It expects the project layout
below, so this script recreates that layout from the package. Data files are hard-linked when possible (no extra disk space),
otherwise copied. The package itself is never modified.

    <workspace>/EDA/src            <- scripts/pipeline/analysis
    <workspace>/EDA/tests          <- scripts/pipeline/tests
    <workspace>/EDA/00_config      <- scripts/pipeline/config   (project_root set to <workspace>)
    <workspace>/EDA/datasets/v1.x  <- data/analysis_dataset/v1.x
    <workspace>/EDA/02_splits/v1.x <- data/splits/v1.x
    <workspace>/EDA/0[3-9]_*       <- data/reference_inputs/phase6   (frozen Phase 6 outputs read by later stages)
    <workspace>/final/scripts      <- scripts/pipeline/final_checks
    <workspace>/new_materials_finding/                 <- scripts/pipeline/external_benchmark
    <workspace>/new_materials_finding/external_audit/  <- scripts/pipeline/external_benchmark/audit + data/external_benchmark/*.csv

Usage:  python scripts/setup_workspace.py --workspace ../pi_ai_mm_workspace
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
PIPE = PKG / "scripts" / "pipeline"
DATA = PKG / "data"

DIR_MAP = {  # workspace dir -> package dir
    "EDA/src": PIPE / "analysis",
    "EDA/tests": PIPE / "tests",
    "EDA/00_config": PIPE / "config",
    "EDA/datasets/v1.2": DATA / "analysis_dataset/v1.2",
    "EDA/datasets/v1.3": DATA / "analysis_dataset/v1.3",
    "EDA/datasets/v1.4": DATA / "analysis_dataset/v1.4",
    "EDA/02_splits/v1.2": DATA / "splits/v1.2",
    "EDA/02_splits/v1.3": DATA / "splits/v1.3",
    "EDA/02_splits/v1.4": DATA / "splits/v1.4",
    "final/scripts": PIPE / "final_checks",
    **{f"EDA/{d}": DATA / "reference_inputs/phase6" / d for d in (
        "03_baseline_tier1/v1.2", "04_tier2_ablation/v1.2", "05_matched_tier_physics/v1.2", "06_material_groups/v1.2",
        "07_interpretability/v1.2", "08_secondary/v1.2", "09_final_tables_figures")},
    "new_materials_finding/external_audit": PIPE / "external_benchmark/audit",
}
FILE_MAP = {  # workspace file -> package file
    **{f"new_materials_finding/{n}": PIPE / "external_benchmark" / n for n in ("features.py", "predict_candidates.py", "predict_external.py")},
    **{f"new_materials_finding/external_audit/{n}": DATA / "external_benchmark" / n
       for n in ("crossref_metadata.csv", "adjudication_papers.csv", "adjudication_records.csv")},
    "final/work/peratom_cell_map.parquet": DATA / "reference_inputs/peratom_cell_map.parquet",
    **{f"final/work/prior_5split/{n}": DATA / "reference_inputs/prior_5split" / n for n in (
        "ordering_v13_matched_results.csv", "ordering_v13_matched_robustness.csv", "ordering_v13_matched_paired_differences.csv")},
    **{f"EDA/10_phase7_validation/v1.3/stage5_families/general_predictions_{t}.csv": DATA / f"reference_inputs/stage5_general/general_predictions_{t}.csv"
       for t in ("curie", "ordering")},
}
EMPTY_DIRS = ["EDA/logs", "final/outputs"]


def place(src: Path, dst: Path) -> str:
    """Hard-link src to dst (copy if linking is not possible). Returns 'link' or 'copy'."""
    if not src.is_file():
        raise FileNotFoundError(f"package file missing: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
        return "link"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


def build(workspace: Path) -> dict[str, int]:
    counts = {"link": 0, "copy": 0}
    for rel, src_dir in DIR_MAP.items():
        for src in src_dir.rglob("*"):
            if src.is_file() and "__pycache__" not in src.parts:
                counts[place(src, workspace / rel / src.relative_to(src_dir))] += 1
    for rel, src in FILE_MAP.items():
        counts[place(src, workspace / rel)] += 1
    for rel in EMPTY_DIRS:
        (workspace / rel).mkdir(parents=True, exist_ok=True)
    cfg = workspace / "EDA/00_config/analysis_config.yaml"
    text = cfg.read_text(encoding="utf-8")
    if "SET_BY_setup_workspace.py" not in text:
        raise ValueError("analysis_config.yaml placeholder not found")
    cfg.unlink()  # it was hard-linked to the package copy: write a fresh file instead of editing the package
    cfg.write_text(text.replace("SET_BY_setup_workspace.py", workspace.as_posix()), encoding="utf-8")
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workspace", required=True, type=Path, help="folder to create (outside the package)")
    ws = ap.parse_args().workspace.resolve()
    if PKG in ws.parents or ws == PKG:
        raise SystemExit("choose a workspace outside the package folder")
    counts = build(ws)
    print(f"workspace ready: {ws}  ({counts['link']} hard-linked, {counts['copy']} copied files)")
    print(f"for the external benchmark (RQ3) also run: python scripts/fetch_external_benchmark.py --workspace {ws}")
    print(f"next: cd {ws / 'EDA' / 'src'}  and follow scripts/README.md (leave OMP_NUM_THREADS unset)")


if __name__ == "__main__":
    main()
