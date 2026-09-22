#!/usr/bin/env python3
"""Download Kreis-level Regionalatlas data from the official ArcGIS service."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "district_sources.json"
RAW_DIR = ROOT / "data" / "raw" / "regionalatlas"
MANIFEST = ROOT / "data" / "raw" / "manifest.json"
CATALOG_URL = "https://regionalatlas.statistikportal.de/taskrunner/services.json"
QUERY_URL = (
    "https://www.gis-idmz.nrw.de/arcgis/rest/services/stba/"
    "regionalatlas/MapServer/dynamicLayer/query"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dataset_table(dataset: str) -> str:
    return dataset.lower().replace("-", "_")


def fetch(url: str, parameters: Optional[dict[str, str]] = None) -> bytes:
    if parameters:
        url = f"{url}?{urlencode(parameters)}"
    request = Request(url, headers={"User-Agent": "Germany-Data-Observatory/0.4"})
    with urlopen(request, timeout=120) as response:
        return response.read()


def query_districts(dataset: str, data_year: int, geography_year: int) -> bytes:
    table = dataset_table(dataset)
    sql = (
        "SELECT * FROM verwaltungsgrenzen_gesamt "
        f"LEFT OUTER JOIN {table} ON ags = ags2 "
        f"WHERE typ = 3 AND jahr = {geography_year} AND jahr2 = {data_year}"
    )
    layer = {
        "source": {
            "type": "dataLayer",
            "dataSource": {
                "type": "queryTable",
                "workspaceId": "gdb",
                "query": sql,
                "spatialReference": {"wkid": 25832},
                "geometryType": "esriGeometryPolygon",
                "oidFields": "id",
            },
        }
    }
    payload = fetch(
        QUERY_URL,
        {
            "f": "json",
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "false",
            "orderByFields": "ags",
            "layer": json.dumps(layer, separators=(",", ":")),
        },
    )
    parsed = json.loads(payload)
    if parsed.get("error"):
        raise RuntimeError(f"Regionalatlas error for {dataset}/{data_year}: {parsed['error']}")
    features = parsed.get("features", [])
    if len(features) != 400:
        raise ValueError(
            f"Expected 400 Kreis-level rows for {dataset}/{data_year}; got {len(features)}"
        )
    return json.dumps(parsed, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"


def record(path: Path, source_url: str, **extra: object) -> dict[str, object]:
    return {
        "file": str(path.relative_to(ROOT)),
        "source_url": source_url,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        **extra,
    }


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []

    catalog_path = RAW_DIR / "services.json"
    catalog_payload = fetch(CATALOG_URL)
    json.loads(catalog_payload)
    catalog_path.write_bytes(catalog_payload)
    records.append(record(catalog_path, CATALOG_URL))
    print(f"Downloaded Regionalatlas catalog ({catalog_path.stat().st_size:,} bytes)")

    for source in config["sources"]:
        dataset = source["dataset"]
        year = int(source["year"])
        destination = RAW_DIR / f"{dataset.lower().replace('-', '_')}_{year}.json"
        destination.write_bytes(query_districts(dataset, year, config["geography_year"]))
        records.append(
            record(
                destination,
                QUERY_URL,
                dataset=dataset,
                reference_year=year,
                geography_year=config["geography_year"],
                geography_level="Kreise and kreisfreie Staedte",
            )
        )
        print(f"Downloaded {dataset}/{year}: 400 districts")

    previous = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"files": []}
    refreshed = {item["file"] for item in records}
    preserved = [item for item in previous["files"] if item["file"] not in refreshed]
    MANIFEST.write_text(
        json.dumps({"files": preserved + records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
