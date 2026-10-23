"""Validate explanatory content against the committed model snapshot, not Power BI runtime."""

import csv
import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "powerbi/GermanyDataObservatory.Report/definition/pages"
PAGE_ID = "787a52b0aa67d5bef449"


class MethodologyReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.visuals = [json.loads(p.read_text()) for p in (PAGES / PAGE_ID / "visuals").glob("*/visual.json")
                       if json.loads(p.read_text())["position"]["y"] > 76]
        cls.text = "\n".join(
            run["value"]
            for visual in cls.visuals
            for general in visual["visual"].get("objects", {}).get("general", [])
            for paragraph in general["properties"]["paragraphs"]
            for run in paragraph["textRuns"]
        )
        cls.model = json.loads((ROOT / "data/processed/clustering_model_metadata.json").read_text())

    def test_model_quality_values_match_current_snapshot(self):
        self.assertIn(f'{100 * self.model["pca_explained_variance"]:.1f}% of their variance', self.text)
        self.assertEqual(4, self.model['pca_components'])
        for score in self.model["robustness_adjusted_rand"].values():
            self.assertIn(f"{score:.3f}", self.text)
        self.assertEqual(4, self.model["chosen_k"])
        self.assertEqual(20, self.model["minimum_cluster_size"])
        self.assertEqual(0.01, self.model["silhouette_tolerance"])
        with (ROOT / "data/processed/clustering_diagnostics.csv").open() as source:
            diagnostics = list(csv.DictReader(source))
        for row in diagnostics:
            if row["k"] in ("3", "4"):
                self.assertIn(f'{float(row["silhouette_score"]):.3f}', self.text)

    def test_coverage_and_feature_counts_match_current_snapshot(self):
        with (ROOT / "data/processed/dim_district_feature.csv").open() as source:
            features = list(csv.DictReader(source))
        self.assertEqual(14, len(features))
        self.assertEqual(11, sum(row["included_in_clustering"] == "True" for row in features))
        self.assertEqual({"2022", "2023", "2024", "2025"}, {row["reference_year"] for row in features})
        with (ROOT / "data/processed/fact_district_features.csv").open() as source:
            facts = list(csv.DictReader(source))
        self.assertEqual({400}, set(Counter(row["feature_id"] for row in facts).values()))
        self.assertTrue(all(row["value"] != "" for row in facts))
        with (ROOT / "data/processed/fact_cluster_assignment.csv").open() as source:
            counts = Counter(row["cluster_id"] for row in csv.DictReader(source))
        self.assertEqual([35, 64, 67, 234], sorted(counts.values()))

    def test_all_navigation_menus_expose_methodology_once(self):
        count = 0
        for path in PAGES.glob("*/visuals/*/visual.json"):
            visual = json.loads(path.read_text()).get("visual", {})
            if visual.get("visualType") != "pageNavigator":
                continue
            entries = [entry for entry in visual["objects"]["pages"] if entry.get("selector", {}).get("id") == PAGE_ID]
            self.assertEqual(1, len(entries), str(path))
            self.assertEqual("true", entries[0]["properties"]["showPage"]["expr"]["Literal"]["Value"])
            count += 1
        self.assertGreaterEqual(count, 9)

    def test_three_sections_and_sources_inside_first_section(self):
        for heading in ("1. Where the data come from", "2. Structural clusters", "3. Outcomes"):
            self.assertIn(heading, self.text)
        linked = [v for v in self.visuals if any(
            run.get("url")
            for group in v["visual"].get("objects", {}).get("general", [])
            for paragraph in group["properties"]["paragraphs"]
            for run in paragraph["textRuns"]
        )]
        self.assertEqual(1, len(linked))
        self.assertLess(linked[0]["position"]["x"], 276)
        self.assertLess(linked[0]["position"]["y"] + linked[0]["position"]["height"], 432)
        plates = [v["position"] for v in self.visuals if v["visual"]["visualType"] == "shape"]
        self.assertEqual([260, 388, 576], [p["width"] for p in sorted(plates, key=lambda p: p["x"])])
        self.assertEqual({(84, 598)}, {(p["y"], p["height"]) for p in plates})

    def test_outcome_claims_match_election_snapshot(self):
        with (ROOT / "data/processed/fact_district_election_results.csv").open() as source:
            rows = list(csv.DictReader(source))
        votes = {(r["district_id"], r["party_group_id"], r["election_year"]): float(r["second_vote_share_percent"])
                 for r in rows if r["second_vote_share_percent"]}
        districts = {r["district_id"] for r in rows}
        for party, direction in (("afd", 1), ("spd", -1), ("fdp", -1)):
            self.assertEqual(400, sum(direction * (votes[d, "party_group_" + party, "2025"] -
                                                  votes[d, "party_group_" + party, "2021"]) > 0
                                      for d in districts))
        self.assertEqual(380, sum(votes[d, "party_group_cdu_csu", "2025"] >
                                  votes[d, "party_group_cdu_csu", "2021"] for d in districts))
        for year, expected in (("2021", "25.7%"), ("2025", "15.7%")):
            mean = sum(votes[d, "party_group_spd", year] for d in districts) / len(districts)
            self.assertEqual(expected, f"{mean:.1f}%")
            self.assertIn(expected, self.text)
        with (ROOT / "data/processed/fact_district_election_turnout.csv").open() as source:
            turnout = list(csv.DictReader(source))
        for year, expected in (("2017", "75.8%"), ("2025", "82.4%")):
            values = [float(r["turnout_percent"]) for r in turnout if r["election_year"] == year]
            self.assertEqual(expected, f"{sum(values) / len(values):.1f}%")
            self.assertIn(expected, self.text)
        for party in ("CDU/CSU", "SPD", "GRÜNE", "FDP", "Die Linke", "AfD"):
            self.assertIn(party + " —", self.text)

    def test_explanations_do_not_depend_on_data_queries_or_slicers(self):
        self.assertEqual(19, len(self.visuals))
        for visual in self.visuals:
            self.assertNotIn("query", visual["visual"])
            position = visual["position"]
            self.assertLessEqual(position["x"] + position["width"], 1280)
            self.assertLessEqual(position["y"] + position["height"], 720)
        self.assertIn("Associations do not establish causes", self.text)
        self.assertIn("not the official vote-weighted national result", self.text)
        self.assertIn("not the share within that cluster", self.text)
        self.assertIn("Political results do not define the clusters", self.text)
        self.assertNotIn("Volt", self.text)
        self.assertNotIn("data/raw/", self.text)


if __name__ == "__main__":
    unittest.main()
