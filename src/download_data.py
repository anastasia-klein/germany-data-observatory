#!/usr/bin/env python3
"""Download the first Germany Data Observatory source files."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "raw" / "manifest.json"

SOURCES = (
    {
        "path": "bundeswahlleiterin/btw25_kerg2.csv",
        "url": (
            "https://www.bundeswahlleiterin.de/dam/jcr/"
            "f49a47a1-735b-4e9b-b4e1-4c73cad2292e/btw25_kerg2.csv"
        ),
        "marker": b"Wahlart;Wahltag;Gebietsart",
    },
    {
        "path": "bundeswahlleiterin/btw2025_strukturdaten.csv",
        "url": (
            "https://www.bundeswahlleiterin.de/dam/jcr/"
            "181f9e38-38db-4f64-991c-8141dfa0f2cb/btw2025_strukturdaten.csv"
        ),
        "marker": "Strukturdaten für die Wahlkreise".encode("utf-8"),
    },
    {
        "path": "destatis/population_by_nationality_2025.html",
        "url": (
            "https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/"
            "Bevoelkerungsstand/Tabellen/bevoelkerung-nichtdeutsch-laender-basis-2022.html"
        ),
        "marker": "Bevölkerung am 31.12.2025 nach Nationalität".encode("utf-8"),
    },
    {
        "path": "destatis/foreign_population_by_state_2018_2025.html",
        "url": (
            "https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/"
            "Migration-Integration/Tabellen/auslaendische-bevoelkerung-bundeslaender-jahre.html"
        ),
        "marker": b"2018 bis 2025",
    },
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, destination: Path, marker: bytes) -> None:
    request = Request(url, headers={"User-Agent": "Germany-Data-Observatory/0.1"})
    with urlopen(request, timeout=90) as response:
        payload = response.read()
        content_type = response.headers.get_content_type()
    if content_type not in {"text/csv", "text/plain", "text/html", "application/octet-stream"}:
        raise ValueError(f"Unexpected content type for {url}: {content_type}")
    if marker not in payload:
        raise ValueError(f"Downloaded file does not contain its expected table marker: {url}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for source in SOURCES:
        destination = RAW_DIR / source["path"]
        download(source["url"], destination, source["marker"])
        records.append(
            {
                "file": str(destination.relative_to(ROOT)),
                "source_url": source["url"],
                "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                "bytes": destination.stat().st_size,
                "sha256": sha256(destination),
            }
        )
        print(f"Downloaded {source['path']} ({destination.stat().st_size:,} bytes)")
    MANIFEST.write_text(json.dumps({"files": records}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
