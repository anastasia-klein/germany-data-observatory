#!/usr/bin/env python3
"""Dissolve the committed district topology into a 16-state Power BI map.

Uses mapshaper 0.6.113, the same version as build_district_geometry.py.
No new geographic download is required.
"""

import argparse
import csv
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "powerbi/GermanyDataObservatory.Report/StaticResources/RegisteredResources/germany_states_2024.topojson"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mapshaper", default="mapshaper")
    parser.add_argument("--node", help="Optional Node executable for running a mapshaper JavaScript CLI.")
    args = parser.parse_args()
    executable = shutil.which(args.mapshaper) or args.mapshaper
    command = [args.node, executable] if args.node else [executable]
    command += [
        str(ROOT / "data/processed/germany_districts_2024.topojson"),
        "-each", "state_code=district_id.slice(0,2)",
        "-dissolve", "state_code",
        "-rename-layers", "germany_states_2024",
        "-o", "format=topojson", str(OUTPUT),
    ]
    subprocess.run(command, check=True)
    data = json.loads(OUTPUT.read_text())
    geometries = data["objects"]["germany_states_2024"]["geometries"]
    with (ROOT / "data/processed/dim_state.csv").open() as source:
        expected = {row["state_code"] for row in csv.DictReader(source)}
    actual = {geometry["properties"]["state_code"] for geometry in geometries}
    if len(geometries) != 16 or actual != expected:
        raise ValueError("State geometry does not match the 16-state dimension.")
    print("Validated all 16 state keys.")


if __name__ == "__main__":
    main()
