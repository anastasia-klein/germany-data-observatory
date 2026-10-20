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

    def test_state_map_matches_state_dimension(self):
        with (PROCESSED / "dim_state.csv").open(encoding="utf-8", newline="") as source:
            expected = {row["state_code"] for row in csv.DictReader(source)}
        resource = "germany_states_2024.topojson"
        report = ROOT / "powerbi/GermanyDataObservatory.Report"
        data = json.loads((report / "StaticResources/RegisteredResources" / resource).read_text())
        geometries = data["objects"]["germany_states_2024"]["geometries"]
        self.assertEqual(16, len(geometries))
        self.assertEqual(expected, {geometry["properties"]["state_code"] for geometry in geometries})
        self.assertTrue(all(set(geometry["properties"]) == {"state_code"} for geometry in geometries))
        self.assertTrue(data["arcs"])

    def test_state_map_is_registered_in_report(self):
        report = ROOT / "powerbi/GermanyDataObservatory.Report"
        definition = json.loads((report / "definition/report.json").read_text())
        registered = next(package for package in definition["resourcePackages"] if package["name"] == "RegisteredResources")
        self.assertIn(
            {"name": "germany_states_2024.topojson", "path": "germany_states_2024.topojson", "type": "ShapeMap"},
            registered["items"],
        )


if __name__ == "__main__":
    unittest.main()
