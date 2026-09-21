import csv
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


if __name__ == "__main__":
    unittest.main()

