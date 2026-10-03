import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


class DistrictGeometryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (PROCESSED / "dim_district.csv").open(encoding="utf-8", newline="") as source:
            cls.expected_ids = {row["district_id"] for row in csv.DictReader(source)}

    def test_geojson_matches_district_dimension(self):
        data = json.loads((PROCESSED / "germany_districts_2024.geojson").read_text())
        features = data["features"]
        actual_ids = {feature["properties"]["district_id"] for feature in features}
        self.assertEqual(400, len(features))
        self.assertEqual(400, len(actual_ids))
        self.assertEqual(self.expected_ids, actual_ids)
        self.assertTrue(
            all(
                set(feature["properties"]) == {"district_id", "district_name"}
                for feature in features
            )
        )

    def test_topojson_is_shape_map_ready(self):
        data = json.loads((PROCESSED / "germany_districts_2024.topojson").read_text())
        layer = data["objects"]["germany_districts_2024"]
        geometries = layer["geometries"]
        actual_ids = {geometry["properties"]["district_id"] for geometry in geometries}
        self.assertEqual("Topology", data["type"])
        self.assertEqual(400, len(geometries))
        self.assertEqual(self.expected_ids, actual_ids)
        self.assertTrue(data["arcs"])


if __name__ == "__main__":
    unittest.main()
