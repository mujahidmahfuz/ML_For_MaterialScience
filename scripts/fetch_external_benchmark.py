"""Download the third-party external Curie-temperature table used in RQ3 into a run workspace and verify it byte-for-byte.

The table (malaei/Magnetic_data, folder FM/, 2,500 ferromagnets with source DOIs) has no stated licence, so it is NOT part of
this package. This script fetches the exact version that was analysed (SHA-256 below) straight into the workspace created by
setup_workspace.py, so the package itself never contains it.
Usage:  python scripts/fetch_external_benchmark.py --workspace ../pi_ai_mm_workspace
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/malaei/Magnetic_data/main/FM/curie_temperature_of_ferromagnetic_materials.csv"
SHA256 = "84d713235116ea90dd8317718cd35bd84fa1b5d1c1ba1825159b8df188596bc6"
REL = Path("new_materials_finding/external_data/malaei_Magnetic_data/curie_temperature_of_ferromagnetic_materials.csv")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workspace", required=True, type=Path, help="workspace created by setup_workspace.py")
    ws = ap.parse_args().workspace.resolve()
    if not (ws / "EDA" / "src").is_dir():
        sys.exit(f"{ws} is not a workspace; run scripts/setup_workspace.py first")
    req = urllib.request.Request(URL, headers={"User-Agent": "reproducibility-package/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != SHA256:
        sys.exit(f"checksum mismatch: got {digest}, expected {SHA256}. The upstream file has changed; the results refer to the expected version.")
    out = ws / REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(f"saved and verified: {out}")


if __name__ == "__main__":
    main()
