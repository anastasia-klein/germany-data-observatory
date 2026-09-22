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

    def test_election_dimensions_have_unique_keys_and_no_orphans(self):
        elections = rows("dim_election.csv")
        parties = rows("dim_party.csv")
        party_facts = rows("fact_election_party_results.csv")
        turnout_facts = rows("fact_election_turnout.csv")

        self.assertEqual(6, len(elections))
        self.assertEqual(6, len({row["election_id"] for row in elections}))
        self.assertEqual(6, len({row["election_date"] for row in elections}))
        election_ids = {row["election_id"] for row in elections}
        self.assertEqual(election_ids, {row["election_id"] for row in party_facts})
        self.assertEqual(election_ids, {row["election_id"] for row in turnout_facts})

        self.assertEqual(81, len(parties))
        self.assertEqual(81, len({row["party_id"] for row in parties}))
        self.assertEqual(81, len({row["party_name"] for row in parties}))
        party_ids = {row["party_id"] for row in parties}
        self.assertEqual(party_ids, {row["party_id"] for row in party_facts})
        self.assertTrue(all(row["party_id"].startswith("party_") for row in parties))

        for party in parties:
            observed_years = {
                int(row["election_date"][:4])
                for row in party_facts
                if row["party_id"] == party["party_id"]
            }
            self.assertEqual(min(observed_years), int(party["first_election_year"]))
            self.assertEqual(max(observed_years), int(party["last_election_year"]))
            self.assertEqual(len(observed_years), int(party["election_count"]))

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
        expected_states = {f"{code:02d}" for code in range(1, 17)}
        expected_dates = {
            "2005-09-18",
            "2009-09-27",
            "2013-09-22",
            "2017-09-24",
            "2021-09-26",
            "2025-02-23",
        }
        self.assertEqual(expected_dates, {row["election_date"] for row in party_data})
        self.assertEqual(expected_dates, {row["election_date"] for row in turnout_data})
        for election_date in expected_dates:
            election_parties = [row for row in party_data if row["election_date"] == election_date]
            election_turnout = [row for row in turnout_data if row["election_date"] == election_date]
            self.assertEqual(expected_states, {row["state_code"] for row in election_parties})
            self.assertEqual(expected_states, {row["state_code"] for row in election_turnout})
            self.assertEqual(32, len(election_turnout))
            self.assertEqual(
                expected_states,
                {row["state_code"] for row in election_parties if row["party"] == "SPD"},
            )
        self.assertTrue(all(row["source_party"] for row in party_data))
        self.assertTrue(all(row["votes"] and row["vote_share_percent"] for row in party_data))

    def test_election_turnout_reconciles_to_official_national_totals(self):
        turnout_data = rows("fact_election_turnout.csv")
        expected = {
            "2005-09-18": {"eligible_voters": 61_870_711, "voters": 48_044_134},
            "2009-09-27": {"eligible_voters": 62_168_489, "voters": 44_005_575},
            "2013-09-22": {"eligible_voters": 61_946_900, "voters": 44_309_925},
            "2017-09-24": {"eligible_voters": 61_688_485, "voters": 46_976_341},
            "2021-09-26": {"eligible_voters": 61_172_771, "voters": 46_707_343},
            "2025-02-23": {"eligible_voters": 60_510_631, "voters": 49_928_653},
        }
        for election_date, controls in expected.items():
            for measure, control in controls.items():
                state_sum = sum(
                    int(row["value"])
                    for row in turnout_data
                    if row["election_date"] == election_date and row["measure"] == measure
                )
                self.assertEqual(control, state_sum)

    def test_spd_second_votes_reconcile_to_official_national_totals(self):
        party_data = rows("fact_election_party_results.csv")
        expected = {
            "2005-09-18": 16_194_665,
            "2009-09-27": 9_990_488,
            "2013-09-22": 11_252_215,
            "2017-09-24": 9_539_381,
            "2021-09-26": 11_901_558,
            "2025-02-23": 8_149_124,
        }
        for election_date, control in expected.items():
            state_sum = sum(
                int(row["votes"])
                for row in party_data
                if row["election_date"] == election_date and row["party"] == "SPD"
            )
            self.assertEqual(control, state_sum)

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
