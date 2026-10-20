"""Static checks for Explorer bindings; these do not execute Power BI queries."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "powerbi/GermanyDataObservatory.Report/definition/pages/ef5ad154745a2ca69b9a"


class ExplorerReportTest(unittest.TestCase):
    def setUp(self):
        path = PAGE / "visuals/de000000000000000011/visual.json"
        self.visual = json.loads(path.read_text())["visual"]
        self.query = self.visual["query"]["queryState"]

    def test_pca_query_has_unique_native_projection_names(self):
        # Category and tooltip used to both be named District in the query.
        projections = [p for role in self.query.values() for p in role["projections"]]
        for key in ("nativeQueryRef", "queryRef"):
            names = [projection[key] for projection in projections]
            self.assertEqual(len(names), len(set(names)), key)

    def test_pca_points_have_unique_readable_district_labels(self):
        category = self.query["Category"]["projections"]
        self.assertEqual(1, len(category))
        self.assertEqual("District label", category[0]["field"]["Column"]["Property"])
        self.assertEqual("dim_district", category[0]["field"]["Column"]["Expression"]["SourceRef"]["Entity"])
        # This label includes the district code, so repeated place names do not merge.
        model = (ROOT / "powerbi/GermanyDataObservatory.SemanticModel/definition/tables/dim_district.tmdl").read_text()
        self.assertIn('dim_district[district_name] & " [" & dim_district[district_id] & "]"', model)

    def test_pca_coordinates_size_and_peer_tooltips_are_preserved(self):
        for role, measure in (("X", "Explorer PCA X"), ("Y", "Explorer PCA Y"), ("Size", "Explorer PCA Point Size")):
            self.assertEqual(measure, self.query[role]["projections"][0]["field"]["Measure"]["Property"])
        self.assertEqual(
            ["Explorer Peer Rank", "Explorer Peer Distance"],
            [p["field"]["Measure"]["Property"] for p in self.query["Tooltips"]["projections"]],
        )


if __name__ == "__main__":
    unittest.main()
