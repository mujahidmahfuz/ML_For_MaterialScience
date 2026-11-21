"""Paste the formatted reference list into a .tex file, as the Springer Nature template manual asks for Nature Portfolio
journals ("Do not upload a bibliography file. Instead include the references within the manuscript file itself").

The block between the lines '%%% BEGIN REFERENCES' and '%%% END REFERENCES' is replaced. To regenerate it after a citation
or references.bib changes, the script first compiles a temporary copy whose block holds \\bibliography{references}
(tectonic runs BibTeX with sn-nature.bst), then pastes the resulting .bbl into the real file.

Usage:  python inline_references.py [manuscript.tex supplementary.tex ...]   (default: both)
"""
from __future__ import annotations

import shutil
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TECTONIC = Path(os.environ.get("TECTONIC") or shutil.which("tectonic") or "tectonic")
BEGIN, END = "%%% BEGIN REFERENCES", "%%% END REFERENCES"
SUPPORT = ("sn-jnl.cls", "sn-nature.bst", "references.bib")


def split_block(text: str) -> tuple[str, str, str]:
    start, stop = text.index(BEGIN), text.index(END)
    head = text[: start + len(BEGIN)]
    return head, text[start + len(BEGIN): stop], text[stop:]


def make_bbl(tex: Path) -> str:
    head, _, tail = split_block(tex.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for name in SUPPORT:
            shutil.copy2(HERE / name, work / name)
        for pdf in HERE.glob("*.pdf"):
            shutil.copy2(pdf, work / pdf.name)
        (work / tex.name).write_text(head + "\n\\bibliography{references}\n" + tail, encoding="utf-8")
        run = subprocess.run([str(TECTONIC), "--keep-intermediates", tex.name], cwd=work, capture_output=True, text=True)
        if run.returncode != 0:
            raise SystemExit(f"{tex.name}: tectonic failed\n{run.stderr[-2000:]}")
        return (work / tex.with_suffix(".bbl").name).read_text(encoding="utf-8").strip()


def inline(tex: Path) -> None:
    bbl = make_bbl(tex)
    head, _, tail = split_block(tex.read_text(encoding="utf-8"))
    tex.write_text(head + "\n" + bbl + "\n" + tail, encoding="utf-8")
    print(f"{tex.name}: pasted {bbl.count(chr(92) + 'bibitem')} references")


def main() -> None:
    names = sys.argv[1:] or ["manuscript.tex", "supplementary.tex"]
    for name in names:
        path = HERE / name
        if path.exists():
            inline(path)


if __name__ == "__main__":
    main()
