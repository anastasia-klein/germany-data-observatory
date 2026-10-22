"""Regression checks for the shared report shell and page-specific layout fixes."""

import hashlib
import json
import unittest
from urllib.parse import unquote
from xml.etree import ElementTree
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "powerbi/GermanyDataObservatory.Report/definition/pages"
OV = "d50e4cc4ff4929c40fd5"
IN = "b7e9c2d4f6a81035c1e7"
AT = "129c813b87abfac15531"
PL = "e5cf30606a74c999b189"
PP = "f46b5f7f784039f934d3"
CH = "4e80b8dca4d62d9a56d6"
VO = "f4e8945e19de5cff3010"
DE = "ef5ad154745a2ca69b9a"
ME = "787a52b0aa67d5bef449"
PUBLIC = [OV, IN, AT, PL, PP, CH, DE, ME]
REMOVED = ["dae73f753a4b3d97a94c", "4f3295cf081f68adc10a", "661b6c8f56eb1ba037c5"]


def visual(page, vid):
    return json.loads((PAGES / page / "visuals" / vid / "visual.json").read_text())


def all_visuals(page):
    return [json.loads(path.read_text()) for path in (PAGES / page / "visuals").glob("*/visual.json")]


def identifier(page, vid, purpose):
    return hashlib.sha1((page + vid + purpose).encode()).hexdigest()[:20]


def value(expr):
    return expr["expr"]["Literal"]["Value"]


class ReportDesignTest(unittest.TestCase):
    def test_stacked_overview_is_the_public_landing_page(self):
        metadata = json.loads((PAGES / "pages.json").read_text())
        self.assertEqual(PUBLIC, metadata["pageOrder"][:8])
        self.assertEqual(OV, metadata["activePageName"])
        page = json.loads((PAGES / OV / "page.json").read_text())
        self.assertEqual("Overview", page["displayName"])
        self.assertNotIn("visibility", page)
        for pid in REMOVED:
            self.assertNotIn(pid, metadata["pageOrder"])
            self.assertFalse((PAGES / pid / "page.json").exists())
        self.assertFalse((PAGES / OV / "visuals/4a2047c1fc6e3cbab766/visual.json").exists())

    def test_volt_is_retained_but_hidden(self):
        page = json.loads((PAGES / VO / "page.json").read_text())
        self.assertEqual("HiddenInViewMode", page["visibility"])
        self.assertTrue(any(v["visual"]["visualType"] == "shapeMap" for v in all_visuals(VO)))

    def test_shared_navigation_is_centered_rounded_and_has_eight_public_pages(self):
        count = 0
        for page in PUBLIC + [VO]:
            navs = [v for v in all_visuals(page) if v["visual"]["visualType"] == "pageNavigator"]
            self.assertEqual(1, len(navs))
            nav = navs[0]
            entries = nav["visual"]["objects"]["pages"]
            self.assertEqual(PUBLIC, [e["selector"]["id"] for e in entries if "selector" in e])
            self.assertGreaterEqual(nav["position"]["width"] / 8, 99)
            for entry in nav["visual"]["objects"]["text"]:
                self.assertEqual("'center'", value(entry["properties"]["horizontalAlignment"]))
                self.assertEqual("'middle'", value(entry["properties"]["verticalAlignment"]))
            for entry in nav["visual"]["objects"]["shape"]:
                self.assertEqual("'rectangleRounded'", value(entry["properties"]["tileShape"]))
            count += 1
        self.assertEqual(9, count)

    def test_every_page_has_the_same_footer_baseline_and_type(self):
        for page in PUBLIC + [VO]:
            footers = [v for v in all_visuals(page) if v["visual"]["visualType"] == "textbox" and v["position"]["y"] == 692]
            self.assertEqual(1, len(footers), page)
            footer = footers[0]
            self.assertEqual((20, 1240, 24), tuple(footer["position"][k] for k in ("x", "width", "height")))
            for para in footer["visual"]["objects"]["general"][0]["properties"]["paragraphs"]:
                for run in para["textRuns"]:
                    self.assertEqual("8pt", run["textStyle"]["fontSize"])
                    self.assertEqual("#68727D", run["textStyle"]["color"])

    def test_context_cards_use_padded_headings_and_no_internal_frame(self):
        for page, vid in [(PL,"pl000000000000000003"),(PP,"pp000000000000000003"),(CH,"ch000000000000000004"),(DE,"de000000000000000003")]:
            card = visual(page, vid)
            plate = visual(page, identifier(page, vid, "backplate"))
            heading = visual(page, identifier(page, vid, "heading"))
            self.assertEqual((80,72), tuple(plate["position"][k] for k in ("y","height")))
            self.assertEqual(plate["position"]["x"] + 12, heading["position"]["x"])
            self.assertEqual(86, heading["position"]["y"])
            self.assertEqual(112, card["position"]["y"])
            for key in ("border","background"):
                self.assertEqual("false", value(card["visual"]["visualContainerObjects"][key][0]["properties"]["show"]))
            self.assertEqual("false", value(card["visual"]["objects"]["outline"][0]["properties"]["show"]))

    def test_indicator_benchmark_is_not_repeated_on_charts(self):
        cards = [v for v in all_visuals(IN) if v["visual"]["visualType"] == "cardVisual"]
        self.assertEqual(1, len(cards))
        self.assertGreater(cards[0]["position"]["x"], 920)
        for vid in ("5bbff1cd52b45de836f9", "950e44b0b57d31277ab4"):
            self.assertNotIn("xAxisReferenceLine", visual(IN,vid)["visual"]["objects"])

    def test_cluster_markers_are_exact_colours_not_emojis(self):
        table = visual(OV,"d81e4a5fa35f182c8d46")["visual"]
        self.assertEqual("tableEx", table["visualType"])
        projections = table["query"]["queryState"]["Values"]["projections"]
        self.assertEqual("Cluster colour marker", projections[0]["field"]["Measure"]["Property"])
        self.assertEqual("cluster_name", projections[1]["field"]["Column"]["Property"])
        measures = (ROOT / "powerbi/GermanyDataObservatory.SemanticModel/definition/tables/_Measures.tmdl").read_text()
        marker = measures.split("measure 'Cluster colour marker' =",1)[1].split("\n\tmeasure ",1)[0]
        self.assertIn("SELECTEDVALUE ( dim_cluster[cluster_color_hex] )", marker)
        self.assertIn("dataCategory: ImageUrl", marker)
        self.assertIn("<circle", marker)
        # Inspect the resulting display asset independently of the DAX engine.
        prefix = marker.split('"data:image/svg+xml;utf8,', 1)[1].split('"', 1)[0]
        suffix = marker.split('& "', 1)[1].split('"', 1)[0]
        for colour in ("#FF6B57", "#11B89A", "#7357E8", "#F9C642"):
            svg = ElementTree.fromstring(unquote(prefix + colour.replace("#", "%23") + suffix))
            self.assertEqual(colour, svg.find("{http://www.w3.org/2000/svg}circle").attrib["fill"])

    def test_party_legends_fit_in_two_rows_inside_their_panel(self):
        for page, vid, n, height in [(PL,"pl000000000000000006",7,270),(DE,"de000000000000000012",6,244)]:
            plate = visual(page, identifier(page,vid,"backplate"))["position"]
            chart = visual(page,vid)
            self.assertEqual(height,plate["height"])
            self.assertEqual(688,plate["y"]+plate["height"])
            self.assertEqual("false",value(chart["visual"]["objects"]["legend"][0]["properties"]["show"]))
            rows=set()
            for i in range(n):
                p=visual(page,identifier(page,vid,"legend"+str(i)))["position"]
                rows.add(p["y"])
                self.assertGreaterEqual(p["y"],chart["position"]["y"]+chart["position"]["height"])
                self.assertLessEqual(p["y"]+p["height"],688)
            self.assertEqual(2,len(rows))
        self.assertEqual(244,visual(DE,"de000000000000000013")["position"]["height"])

    def test_change_cluster_bars_are_solid_and_borderless(self):
        for entry in visual(CH,"ch000000000000000020")["visual"]["objects"]["dataPoint"]:
            self.assertEqual("0D",value(entry["properties"]["fillTransparency"]))
            self.assertEqual("false",value(entry["properties"]["borderShow"]))

    def test_methodology_links_sources_without_internal_paths_or_volt(self):
        runs=[run for v in all_visuals(ME) for obj in v["visual"].get("objects",{}).get("general",[]) for p in obj.get("properties",{}).get("paragraphs",[]) for run in p["textRuns"]]
        body=" ".join(run["value"] for run in runs)
        self.assertNotIn("Volt",body)
        self.assertNotIn("data/raw/",body)
        self.assertNotIn("manifest.json",body)
        urls=[run["url"] for run in runs if "url" in run]
        self.assertEqual(4,len(urls))
        self.assertTrue(all(url.startswith("https://") for url in urls))

    def test_interaction_ids_and_visual_bounds_remain_valid(self):
        for page in PUBLIC + [VO]:
            visuals=all_visuals(page)
            ids={v["name"] for v in visuals}
            definition=json.loads((PAGES/page/"page.json").read_text())
            for interaction in definition.get("visualInteractions",[]):
                self.assertIn(interaction["source"],ids)
                self.assertIn(interaction["target"],ids)
            for v in visuals:
                p=v["position"]
                self.assertLessEqual(p["x"]+p["width"],1280)
                self.assertLessEqual(p["y"]+p["height"],720)


if __name__ == "__main__":
    unittest.main()
