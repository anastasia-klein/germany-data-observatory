import json
import subprocess
import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


class DistrictAnalysisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(
            [sys.executable, str(ROOT / "src" / "build_district_analysis.py")],
            check=True,
        )

    def test_district_dimension_has_400_unique_current_districts(self):
        districts = pd.read_csv(PROCESSED / "dim_district.csv", dtype={"district_id": str, "state_code": str})
        self.assertEqual(400, len(districts))
        self.assertEqual(400, districts["district_id"].nunique())
        self.assertEqual(16, districts["state_code"].nunique())
        self.assertTrue(districts["district_id"].str.fullmatch(r"\d{5}").all())
        self.assertTrue(districts["state_name"].notna().all())

    def test_feature_catalog_separates_model_inputs_from_correlated_features(self):
        catalog = pd.read_csv(PROCESSED / "dim_district_feature.csv")
        facts = pd.read_csv(PROCESSED / "fact_district_features.csv", dtype={"district_id": str})
        included = catalog[catalog["included_in_clustering"]]["feature_id"]
        excluded = catalog[~catalog["included_in_clustering"]]
        self.assertEqual(14, len(catalog))
        self.assertEqual(11, len(included))
        self.assertEqual(5600, len(facts))
        self.assertFalse(facts["value"].isna().any())
        self.assertTrue((facts.groupby("feature_id")["district_id"].nunique() == 400).all())
        self.assertTrue(excluded["exclusion_reason"].notna().all())

    def test_political_data_are_not_cluster_features(self):
        metadata = json.loads((PROCESSED / "clustering_model_metadata.json").read_text())
        catalog = pd.read_csv(PROCESSED / "dim_district_feature.csv")
        self.assertTrue(metadata["excluded_political_features"])
        self.assertFalse(any("vote" in feature or "turnout" in feature for feature in metadata["features"]))
        self.assertFalse(catalog["feature_id"].str.contains("vote|turnout", case=False).any())

    def test_cluster_selection_and_assignment_are_complete(self):
        assignments = pd.read_csv(PROCESSED / "fact_cluster_assignment.csv", dtype={"district_id": str})
        diagnostics = pd.read_csv(PROCESSED / "clustering_diagnostics.csv")
        metadata = json.loads((PROCESSED / "clustering_model_metadata.json").read_text())
        selected = diagnostics[diagnostics["selected"]]
        eligible = diagnostics[diagnostics["passes_minimum_size"]]
        self.assertEqual(400, len(assignments))
        self.assertEqual(400, assignments["district_id"].nunique())
        self.assertEqual(1, len(selected))
        self.assertEqual(metadata["chosen_k"], assignments["cluster_id"].nunique())
        self.assertEqual(4, metadata["chosen_k"])
        self.assertGreaterEqual(
            selected.iloc[0]["silhouette_score"],
            eligible["silhouette_score"].max() - metadata["silhouette_tolerance"],
        )
        self.assertGreaterEqual(assignments["cluster_id"].value_counts().min(), 20)
        self.assertGreater(metadata["robustness_adjusted_rand"]["direct_scaled_vs_primary"], 0.75)
        self.assertGreater(metadata["robustness_adjusted_rand"]["robust_scaled_pca_vs_primary"], 0.75)
        clusters = pd.read_csv(PROCESSED / "dim_cluster.csv")
        self.assertEqual(4, clusters["cluster_color_hex"].nunique())
        self.assertTrue(clusters["cluster_color_hex"].str.fullmatch(r"#[0-9A-F]{6}").all())

    def test_pca_reaches_variance_target(self):
        variance = pd.read_csv(PROCESSED / "pca_explained_variance.csv")
        scores = pd.read_csv(PROCESSED / "district_pca.csv", dtype={"district_id": str})
        self.assertGreaterEqual(variance.iloc[-1]["cumulative_explained_variance_ratio"], 0.8)
        self.assertEqual(400, len(scores))
        self.assertEqual(len(variance) + 1, len(scores.columns))

    def test_district_election_tables_cover_three_elections(self):
        results = pd.read_csv(PROCESSED / "fact_district_election_results.csv", dtype={"district_id": str})
        turnout = pd.read_csv(PROCESSED / "fact_district_election_turnout.csv", dtype={"district_id": str})
        self.assertEqual({2017, 2021, 2025}, set(results["election_year"]))
        self.assertEqual(7200, len(results))
        self.assertEqual(1200, len(turnout))
        self.assertTrue((results.groupby(["election_year", "party_group_id"])["district_id"].nunique() == 400).all())
        self.assertTrue((turnout.groupby("election_year")["district_id"].nunique() == 400).all())
        reported = results[results["value_status"] == "reported"]
        unavailable = results[results["value_status"] == "not_available"]
        self.assertTrue(reported["second_vote_share_percent"].between(0, 100).all())
        self.assertEqual(6, len(unavailable))
        self.assertTrue(unavailable["second_vote_share_percent"].isna().all())
        self.assertTrue(turnout["turnout_percent"].between(0, 100).all())


if __name__ == "__main__":
    unittest.main()
