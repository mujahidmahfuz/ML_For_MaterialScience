"""Fetch Crossref metadata (title, journal, type, year, abstract) for every DOI in the external Curie table (audit checks A1/A5/A6).

Public metadata only; the response JSON is treated as untrusted data (parsed fields only). Resumable: DOIs already fetched are skipped.
Usage (from this folder): python fetch_crossref.py
Output: crossref_metadata.csv (doi, status, title, container, type, year, abstract)
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from audit_common import EXTERNAL_CSV, doi_set  # noqa: E402

OUT = HERE / "crossref_metadata.csv"
HEADERS = {"User-Agent": "PI-AI-MM-benchmark-audit/1.0 (research metadata lookup)"}
MAX_WORKERS, RETRIES = 6, 4


def fetch(doi: str) -> dict:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/()")
    last = ""
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as resp:
                msg = json.loads(resp.read().decode("utf-8"))["message"]
            abstract = re.sub(r"<[^>]+>", " ", msg.get("abstract", "") or "")
            year = (msg.get("issued", {}).get("date-parts") or [[None]])[0][0]
            return {"doi": doi, "status": "ok", "title": " ".join(msg.get("title") or []), "container": " ".join(msg.get("container-title") or []),
                    "type": msg.get("type", ""), "year": year, "abstract": " ".join(abstract.split())[:4000]}
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return {"doi": doi, "status": "not_found"}
            last = f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
            last = repr(exc)
        time.sleep(2 ** attempt)
    return {"doi": doi, "status": f"failed: {last}"}


def main() -> None:
    ext = pd.read_csv(EXTERNAL_CSV, keep_default_na=False, na_values=[""])
    dois = sorted(set().union(*ext["DOI"].map(doi_set)))
    done = pd.read_csv(OUT, keep_default_na=False) if OUT.exists() else pd.DataFrame(columns=["doi", "status"])
    finished = set(done.loc[done["status"].isin(["ok", "not_found"]), "doi"])
    todo = [d for d in dois if d not in finished]
    print(f"DOIs: {len(dois)}; to fetch: {len(todo)}", flush=True)
    with ThreadPoolExecutor(MAX_WORKERS) as pool:
        rows = list(pool.map(fetch, todo))
    out = pd.concat([done[done["doi"].isin(finished)], pd.DataFrame(rows)], ignore_index=True).sort_values("doi")
    out.to_csv(OUT, index=False, encoding="utf-8")
    print(out["status"].value_counts().to_string())


if __name__ == "__main__":
    main()
