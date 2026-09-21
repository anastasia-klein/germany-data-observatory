#!/usr/bin/env python3
"""Safely access Destatis GENESIS with a token stored outside Git."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
RAW_DIR = ROOT / "data" / "raw" / "destatis"
METADATA_FILE = RAW_DIR / "genesis_12411LJ001_metadata.json"
DATA_FILE = RAW_DIR / "genesis_12411LJ001_population_by_state_age_sex_1991_2025.csv"
MANIFEST = ROOT / "data" / "raw" / "manifest.json"
API_ROOT = "https://genesis.destatis.de/genesisWS/rest/2020"
CUBE_CODE = "12411LJ001"


class GenesisError(RuntimeError):
    """A safe, human-readable GENESIS API error."""


def load_local_env(path: Path = ENV_FILE) -> None:
    """Load simple KEY=VALUE entries without overriding the process environment."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def api_request(method: str, token: str, parameters: dict[str, str]) -> bytes:
    request = Request(
        f"{API_ROOT}/{method}",
        data=urlencode(parameters).encode("ascii"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "username": token,
            "password": "",
            "User-Agent": "Germany-Data-Observatory/0.3",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            return response.read()
    except HTTPError as error:
        raise GenesisError(f"GENESIS returned HTTP {error.code}") from error
    except URLError as error:
        raise GenesisError(f"Could not reach GENESIS: {error.reason}") from error


def json_response(payload: bytes) -> dict:
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GenesisError("GENESIS returned an unexpected response") from error


def status_error(response: dict) -> GenesisError:
    status = response.get("Status", {})
    if isinstance(status, dict):
        code = status.get("Code", "unknown")
        detail = str(status.get("Content", "no details")).splitlines()[0]
    else:
        code, detail = "unknown", str(status)
    return GenesisError(f"GENESIS status {code}: {detail}")


def check_authentication(token: str) -> None:
    response = json_response(api_request("helloworld/logincheck", token, {"language": "de"}))
    status = response.get("Status")
    if not isinstance(status, str) or "erfolgreich" not in status.lower():
        raise status_error(response)


def download_metadata(token: str) -> None:
    response = json_response(
        api_request("metadata/cube", token, {"name": CUBE_CODE, "language": "de"})
    )
    status = response.get("Status", {})
    if not isinstance(status, dict) or str(status.get("Code")) != "0":
        raise status_error(response)
    if response.get("Object") is None:
        raise GenesisError(f"GENESIS returned no metadata for cube {CUBE_CODE}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_FILE.write_text(
        json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    update_manifest(METADATA_FILE, f"{API_ROOT}/metadata/cube", "metadata")


def download_cube(token: str) -> None:
    payload = api_request(
        "data/cubefile",
        token,
        {
            "name": CUBE_CODE,
            "area": "all",
            "compress": "true",
            "transpose": "false",
            "values": "true",
            "metadata": "true",
            "additionals": "false",
            "contents": "BEVSTD",
            "startyear": "1991",
            "endyear": "2025",
            "format": "csv",
            "language": "de",
            "job": "false",
        },
    )
    if not zipfile.is_zipfile(io.BytesIO(payload)):
        raise status_error(json_response(payload))

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(csv_names) != 1:
            raise GenesisError(f"Expected one CSV in the GENESIS archive; found {len(csv_names)}")
        csv_payload = archive.read(csv_names[0])
    if not csv_payload.strip():
        raise GenesisError("GENESIS returned an empty CSV")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_bytes(csv_payload)
    update_manifest(DATA_FILE, f"{API_ROOT}/data/cubefile", "data")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def update_manifest(path: Path, source_url: str, asset_type: str) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"files": []}
    relative_path = str(path.relative_to(ROOT))
    record = {
        "file": relative_path,
        "source_url": source_url,
        "genesis_object": CUBE_CODE,
        "asset_type": asset_type,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    manifest["files"] = [item for item in manifest["files"] if item["file"] != relative_path]
    manifest["files"].append(record)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check-auth", action="store_true", help="validate the token only")
    mode.add_argument("--metadata-only", action="store_true", help="download cube metadata only")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_local_env()
    token = os.environ.get("DESTATIS_GENESIS_TOKEN", "").strip()
    if not token:
        raise SystemExit("Missing DESTATIS_GENESIS_TOKEN. Copy .env.example to .env and add the token.")

    try:
        check_authentication(token)
        if args.check_auth:
            print("GENESIS authentication succeeded")
            return
        download_metadata(token)
        print(f"Downloaded GENESIS metadata for {CUBE_CODE}")
        if not args.metadata_only:
            download_cube(token)
            print(f"Downloaded GENESIS cube {CUBE_CODE} ({DATA_FILE.stat().st_size:,} bytes)")
    except GenesisError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
