import csv
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def rows(filename: str):
    with (PROCESSED / filename).open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / "src" / "transform_data.py")], check=True)

    def test_dimension_contains_all_16_states(self):
        data = rows("dim_state.csv")
        self.assertEqual(16, len(data))
        self.assertEqual(16, len({row["state_code"] for row in data}))
        self.assertEqual(16, len({row["nuts1_code"] for row in data}))

    def test_raw_files_match_download_manifest(self):
        manifest = json.loads((ROOT / "data" / "raw" / "manifest.json").read_text())
        for record in manifest["files"]:
            path = ROOT / record["file"]
            self.assertTrue(path.is_file(), record["file"])
            self.assertEqual(record["bytes"], path.stat().st_size)
            self.assertEqual(record["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_each_indicator_covers_all_states(self):
        data = rows("fact_state_indicators.csv")
        by_indicator = {}
        for row in data:
            by_indicator.setdefault(row["indicator"], set()).add(row["state_code"])
            self.assertNotEqual("", row["value"])
        self.assertEqual(14, len(by_indicator))
        self.assertTrue(all(len(state_codes) == 16 for state_codes in by_indicator.values()))

    def test_election_tables_cover_all_states(self):
        party_data = rows("fact_election_party_results.csv")
        turnout_data = rows("fact_election_turnout.csv")
        expected = {f"{code:02d}" for code in range(1, 17)}
        self.assertEqual(expected, {row["state_code"] for row in party_data})
        self.assertEqual(expected, {row["state_code"] for row in turnout_data})
        self.assertEqual(32, len(turnout_data))

    def test_destatis_nationality_table_has_four_groups_per_state(self):
        data = rows("fact_population_nationality.csv")
        expected_groups = {"total", "german", "non_german", "eu_member_country"}
        self.assertEqual(64, len(data))
        for code in {f"{value:02d}" for value in range(1, 17)}:
            groups = {row["population_group"] for row in data if row["state_code"] == code}
            self.assertEqual(expected_groups, groups)
        self.assertTrue(all(int(row["population_count"]) > 0 for row in data))
        national_controls = {
            "total": 83_467_117,
            "german": 71_036_222,
            "non_german": 12_430_895,
            "eu_member_country": 4_269_389,
        }
        for group, control in national_controls.items():
            state_sum = sum(
                int(row["population_count"])
                for row in data
                if row["population_group"] == group
            )
            self.assertEqual(control, state_sum)

    def test_destatis_foreign_population_has_eight_years_per_state(self):
        data = rows("fact_foreign_population.csv")
        expected_years = {str(year) for year in range(2018, 2026)}
        self.assertEqual(128, len(data))
        for code in {f"{value:02d}" for value in range(1, 17)}:
            years = {row["year"] for row in data if row["state_code"] == code}
            self.assertEqual(expected_years, years)
        self.assertTrue(all(int(row["foreign_population_count"]) > 0 for row in data))
        national_controls = {
            "2018": 10_915_455,
            "2019": 11_228_300,
            "2020": 11_432_460,
            "2021": 11_817_790,
            "2022": 13_383_910,
            "2023": 13_895_865,
            "2024": 14_061_640,
            "2025": 14_070_225,
        }
        for year, control in national_controls.items():
            state_sum = sum(
                int(row["foreign_population_count"])
                for row in data
                if row["year"] == year
            )
            # State values are published rounded to five people in some years.
            self.assertLessEqual(abs(control - state_sum), 20)


if __name__ == "__main__":
    unittest.main()
