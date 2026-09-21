#!/usr/bin/env python3
"""Download the first Germany Data Observatory source files."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "bundeswahlleiterin"
MANIFEST = ROOT / "data" / "raw" / "manifest.json"

SOURCES = {
    "btw25_kerg2.csv": (
        "https://www.bundeswahlleiterin.de/dam/jcr/"
        "f49a47a1-735b-4e9b-b4e1-4c73cad2292e/btw25_kerg2.csv"
    ),
    "btw2025_strukturdaten.csv": (
        "https://www.bundeswahlleiterin.de/dam/jcr/"
        "181f9e38-38db-4f64-991c-8141dfa0f2cb/btw2025_strukturdaten.csv"
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    request = Request(url, headers={"User-Agent": "Germany-Data-Observatory/0.1"})
    with urlopen(request, timeout=90) as response:
        payload = response.read()
        content_type = response.headers.get_content_type()
    if content_type not in {"text/csv", "text/plain", "application/octet-stream"}:
        raise ValueError(f"Unexpected content type for {url}: {content_type}")
    if b";" not in payload[:4096]:
        raise ValueError(f"Downloaded file does not look like semicolon-delimited CSV: {url}")
    destination.write_bytes(payload)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for filename, url in SOURCES.items():
        destination = RAW_DIR / filename
        download(url, destination)
        records.append(
            {
                "file": str(destination.relative_to(ROOT)),
                "source_url": url,
                "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                "bytes": destination.stat().st_size,
                "sha256": sha256(destination),
            }
        )
        print(f"Downloaded {filename} ({destination.stat().st_size:,} bytes)")
    MANIFEST.write_text(json.dumps({"files": records}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

