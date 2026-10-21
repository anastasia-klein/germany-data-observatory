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
        cls.visuals = [json.loads(p.read_text()) for p in (PAGES / PAGE_ID / "visuals").glob("me*/visual.json")]
        cls.text = "\n".join(
            run["value"]
            for visual in cls.visuals
            for general in visual["visual"].get("objects", {}).get("general", [])
            for paragraph in general["properties"]["paragraphs"]
            for run in paragraph["textRuns"]
        )
        cls.model = json.loads((ROOT / "data/processed/clustering_model_metadata.json").read_text())

    def test_model_quality_values_match_current_snapshot(self):
        self.assertIn(f'{self.model["pca_components"]} components retain {100 * self.model["pca_explained_variance"]:.1f}%', self.text)
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

    def test_explanations_do_not_depend_on_data_queries_or_slicers(self):
        self.assertEqual(15, len(self.visuals))
        for visual in self.visuals:
            self.assertNotIn("query", visual["visual"])
            position = visual["position"]
            self.assertLessEqual(position["x"] + position["width"], 1280)
            self.assertLessEqual(position["y"] + position["height"], 720)
        self.assertIn("not causes or individual voter profiles", self.text)
        self.assertIn("not the official national vote-weighted result", self.text)
        self.assertIn("not % within the cluster", self.text)
        self.assertIn("Political variables never enter", self.text)


if __name__ == "__main__":
    unittest.main()
