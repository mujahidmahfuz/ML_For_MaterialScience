"""Verify every data and result file against CHECKSUMS.sha256 (SHA-256). Usage:  python scripts/verify_checksums.py"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]


def main() -> None:
    lines = (PKG / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines()
    bad = []
    for line in lines:
        expected, rel = line.split("  ", 1)
        path = PKG / rel
        if not path.is_file():
            bad.append(f"missing: {rel}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            bad.append(f"changed: {rel}")
    if bad:
        sys.exit(f"{len(bad)} of {len(lines)} files failed:\n" + "\n".join(bad))
    print(f"all {len(lines)} files match CHECKSUMS.sha256")


if __name__ == "__main__":
    main()
