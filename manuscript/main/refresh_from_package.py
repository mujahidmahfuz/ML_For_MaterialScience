"""Refresh the submission folder's tables/ and figures/ from the reproducibility package.

The package builders write to paper/tables and paper/figures (python scripts/make_tables.py / make_figures.py, run inside paper/).
This folder keeps copies so that it compiles on its own (e.g. uploaded to Overleaf). Run this after any rebuild:
    python refresh_from_package.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]          # paper/


def main() -> None:
    copied = 0
    for src_dir, dst_dir, patterns in ((PKG / "tables", HERE / "tables", ("*.tex",)), (PKG / "figures", HERE / "figures", ("*.pdf", "*.png"))):
        dst_dir.mkdir(exist_ok=True)
        for pattern in patterns:
            for f in src_dir.glob(pattern):
                shutil.copy2(f, dst_dir / f.name)
                copied += 1
    print(f"copied {copied} files from {PKG} into {HERE}")


if __name__ == "__main__":
    main()
