#!/usr/bin/env python3
"""Build Power BI map geometry for Germany's 2024 district geography."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DISTRICTS = PROCESSED / "dim_district.csv"
GEOJSON = PROCESSED / "germany_districts_2024.geojson"
TOPOJSON = PROCESSED / "germany_districts_2024.topojson"
WFS_URL = (
    "https://sgx.geodatenzentrum.de/wfs_vg250"
    "?service=WFS&version=2.0.0&request=GetFeature"
    "&typeNames=vg250:vg250_krs&outputFormat=application/json"
    "&srsName=EPSG:4326"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        help="Use a previously downloaded VG250 Kreis GeoJSON instead of the WFS.",
    )
    parser.add_argument(
        "--mapshaper",
        default="mapshaper",
        help="Mapshaper executable (version 0.6.113 is used for committed outputs).",
    )
    return parser.parse_args()


def download() -> bytes:
    request = Request(WFS_URL, headers={"User-Agent": "Germany-Data-Observatory/0.5"})
    with urlopen(request, timeout=180) as response:
        return response.read()


def expected_district_ids() -> set[str]:
    with DISTRICTS.open(encoding="utf-8", newline="") as source:
        return {row["district_id"] for row in csv.DictReader(source)}


def filter_and_validate(payload: bytes) -> dict[str, object]:
    source = json.loads(payload)
    features = []
    for feature in source.get("features", []):
        properties = feature.get("properties", {})
        if str(properties.get("gf")) != "4":
            continue
        district_id = str(properties["ags"]).zfill(5)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "district_id": district_id,
                    "district_name": properties["gen"],
                },
                "geometry": feature["geometry"],
            }
        )

    actual = {feature["properties"]["district_id"] for feature in features}
    expected = expected_district_ids()
    if len(features) != 400 or len(actual) != 400:
        raise ValueError(f"Expected 400 unique land districts; got {len(features)} rows/{len(actual)} IDs")
    if actual != expected:
        raise ValueError(
            f"Geometry/dimension key mismatch: missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )
    return {"type": "FeatureCollection", "features": features}


def run_mapshaper(executable: str, source: Path) -> None:
    resolved = shutil.which(executable) if not Path(executable).exists() else executable
    if not resolved:
        raise RuntimeError(
            "Mapshaper was not found. Install mapshaper 0.6.113 or pass "
            "--mapshaper /path/to/mapshaper."
        )
    subprocess.run(
        [
            str(resolved),
            str(source),
            "-clean",
            "-simplify",
            "12%",
            "weighted",
            "keep-shapes",
            "-rename-layers",
            "germany_districts_2024",
            "-o",
            f"format=geojson",
            str(GEOJSON),
            "-o",
            "format=topojson",
            str(TOPOJSON),
        ],
        check=True,
    )


def main() -> None:
    args = parse_args()
    payload = args.input.read_bytes() if args.input else download()
    filtered = filter_and_validate(payload)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="gdo-geometry-") as temp_dir:
        intermediate = Path(temp_dir) / "germany_districts_2024_full.geojson"
        intermediate.write_text(
            json.dumps(filtered, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        run_mapshaper(args.mapshaper, intermediate)
    print(f"Built {GEOJSON.relative_to(ROOT)} and {TOPOJSON.relative_to(ROOT)} (400 districts)")


if __name__ == "__main__":
    main()
