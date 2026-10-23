"""Regression checks for the shared report shell and page-specific layout fixes."""

import hashlib
import csv
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

    def test_overview_footer_explains_clusters_and_links_to_methodology(self):
        footer = visual(OV, "683144ac3ec29f734857")
        runs = footer["visual"]["objects"]["general"][0]["properties"]["paragraphs"][0]["textRuns"]
        text = "".join(r["value"] for r in runs)
        self.assertIn("11 indicators, PCA and Ward clustering", text)
        self.assertIn("Methodology →", text)
        action = visual(OV, "ovmethodology00000001")
        props = action["visual"]["visualContainerObjects"]["visualLink"][0]["properties"]
        self.assertEqual("'PageNavigation'", value(props["type"]))
        self.assertEqual("'" + ME + "'", value(props["navigationSection"]))
        for key in ("x", "y", "width", "height"):
            self.assertEqual(footer["position"][key], action["position"][key])

    def test_explorer_peer_columns_fill_the_available_width(self):
        table = visual(DE, "de000000000000000013")
        widths = table["visual"]["objects"]["columnWidth"]
        self.assertEqual([164, 68, 100], [int(value(c["properties"]["value"])[:-1]) for c in widths])
        self.assertEqual([p["queryRef"] for p in table["visual"]["query"]["queryState"]["Values"]["projections"]],
                         [c["selector"]["metadata"] for c in widths])
        self.assertEqual("false", value(table["visual"]["objects"]["columnHeaders"][0]["properties"]["autoSizeColumnWidth"]))
        self.assertLess(sum(int(value(c["properties"]["value"])[:-1]) for c in widths), table["position"]["width"] - 24)

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
            style=heading["visual"]["objects"]["general"][0]["properties"]["paragraphs"][0]["textRuns"][0]["textStyle"]
            self.assertEqual("Segoe UI Semibold",style["fontFamily"])
            self.assertEqual("normal",style["fontWeight"])
            self.assertEqual(112, card["position"]["y"])
            for key in ("border","background"):
                self.assertEqual("false", value(card["visual"]["visualContainerObjects"][key][0]["properties"]["show"]))
            self.assertEqual("false", value(card["visual"]["objects"]["outline"][0]["properties"]["show"]))

    def test_indicator_benchmark_is_not_repeated_on_charts(self):
        cards = [v for v in all_visuals(IN) if v["visual"]["visualType"] == "cardVisual"]
        self.assertEqual(1, len(cards))
        benchmark=cards[0]["position"]
        map_panel=visual(IN,"7bcd0ffefd893e879503")["position"]
        self.assertGreater(benchmark["x"], map_panel["x"])
        self.assertGreater(benchmark["y"], map_panel["y"])
        self.assertLessEqual(benchmark["x"]+benchmark["width"], map_panel["x"]+map_panel["width"])
        self.assertLessEqual(benchmark["y"]+benchmark["height"], map_panel["y"]+map_panel["height"])
        self.assertFalse((PAGES/IN/"visuals"/identifier(IN,cards[0]["name"],"backplate")/"visual.json").exists())
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

    def test_party_legends_fit_in_one_row_with_full_size_circles(self):
        for page, vid, n, height in [(PL,"pl000000000000000006",7,270),(DE,"de000000000000000012",6,244)]:
            plate = visual(page, identifier(page,vid,"backplate"))["position"]
            chart = visual(page,vid)
            self.assertEqual(height,plate["height"])
            self.assertEqual(688,plate["y"]+plate["height"])
            self.assertEqual("false",value(chart["visual"]["objects"]["legend"][0]["properties"]["show"]))
            rows=set()
            previous_right=None
            for i in range(n):
                p=visual(page,identifier(page,vid,"legend"+str(i)))["position"]
                marker=visual(page,identifier(page,vid,"legend-marker"+str(i)))
                dot=marker["position"]
                self.assertEqual((10,10),(dot["width"],dot["height"]))
                self.assertEqual(p["y"]+4.5,dot["y"])
                self.assertEqual("'oval'",value(marker["visual"]["objects"]["shape"][0]["properties"]["tileShape"]))
                self.assertEqual(dot["x"]+10,p["x"])
                if previous_right is not None:self.assertAlmostEqual(6,dot["x"]-previous_right,places=2)
                previous_right=p["x"]+p["width"]
                rows.add(p["y"])
                self.assertGreaterEqual(p["y"],chart["position"]["y"]+chart["position"]["height"])
                self.assertLessEqual(p["y"]+p["height"],688)
                self.assertLessEqual(previous_right,plate["x"]+plate["width"]-16)
            self.assertEqual(1,len(rows))
        self.assertEqual(244,visual(DE,"de000000000000000013")["position"]["height"])

    def test_card_measure_labels_are_hidden_at_each_bound_measure(self):
        for page in PUBLIC + [VO]:
            for a in all_visuals(page):
                v=a["visual"]
                if v["visualType"]!="cardVisual":continue
                labels=v["objects"]["label"]
                for label in labels:
                    self.assertEqual("false",value(label["properties"]["show"]))
                    self.assertEqual("''",value(label["properties"]["text"]))
                refs=[p["queryRef"] for role in v["query"]["queryState"].values() for p in role["projections"]]
                for ref in refs:self.assertTrue(any(label.get("selector")=={"metadata":ref} for label in labels))

    def test_overview_uses_aligned_single_top_row_and_two_body_columns(self):
        top=[visual(OV,identifier(OV,vid,"backplate"))["position"] for vid in
             ("cb0f5f6e69c98788371b","f12f32ac68e31f15fc38","8136bd3d582d4f58c120")]
        top += [visual(OV,vid)["position"] for vid in ("cb59366453ce7440ce15","04bccb98ebfb77513903")]
        self.assertEqual(12,top[0]["x"])
        self.assertEqual(1268,top[-1]["x"]+top[-1]["width"])
        for p in top:self.assertEqual((80,72),(p["y"],p["height"]))
        for left,right in zip(top,top[1:]):self.assertEqual(12,right["x"]-left["x"]-left["width"])
        table=visual(OV,"d81e4a5fa35f182c8d46")["position"]
        map_panel=visual(OV,"2edf0fd369be317800ba")["position"]
        chart=visual(OV,"26e2f76b44cd9795acae")["position"]
        self.assertEqual((table["x"],table["width"]),(map_panel["x"],map_panel["width"]))
        self.assertEqual(12,map_panel["y"]-table["y"]-table["height"])
        self.assertEqual(12,chart["x"]-table["x"]-table["width"])
        self.assertEqual(table["y"],chart["y"])
        self.assertGreaterEqual(table["height"],208)
        self.assertEqual(688,map_panel["y"]+map_panel["height"])
        self.assertEqual(688,chart["y"]+chart["height"])
        self.assertFalse((PAGES/OV/"visuals/fd880518a4b84b064355/visual.json").exists())

    def test_indicators_use_equal_gutters_with_the_benchmark_inside_the_map(self):
        selector=visual(IN,"1a8841997b26741bfd3d")["position"]
        ranking=visual(IN,"950e44b0b57d31277ab4")["position"]
        clusters=visual(IN,"5bbff1cd52b45de836f9")["position"]
        map_panel=visual(IN,"7bcd0ffefd893e879503")["position"]
        self.assertEqual(selector["y"],clusters["y"])
        self.assertEqual((selector["x"],selector["width"]),(ranking["x"],ranking["width"]))
        self.assertEqual((clusters["x"],clusters["width"]),(map_panel["x"],map_panel["width"]))
        self.assertEqual(12,ranking["y"]-selector["y"]-selector["height"])
        self.assertEqual(12,map_panel["y"]-clusters["y"]-clusters["height"])
        self.assertEqual(12,clusters["x"]-selector["x"]-selector["width"])
        self.assertEqual(688,ranking["y"]+ranking["height"])
        self.assertEqual(688,map_panel["y"]+map_panel["height"])

    def test_change_cluster_bars_are_solid_and_borderless(self):
        for entry in visual(CH,"ch000000000000000020")["visual"]["objects"]["dataPoint"]:
            self.assertEqual("0D",value(entry["properties"]["fillTransparency"]))
            self.assertEqual("false",value(entry["properties"]["borderShow"]))

    def test_district_ranking_has_readable_value_labels(self):
        labels=visual(IN,"950e44b0b57d31277ab4")["visual"]["objects"]["labels"][0]["properties"]
        self.assertEqual("true",value(labels["show"]))
        self.assertEqual("1D",value(labels["labelDisplayUnits"]))
        self.assertEqual("0L",value(labels["labelPrecision"]))
        self.assertEqual("'#68727D'",value(labels["color"]["solid"]["color"]))

    def test_tooltip_cards_have_no_inner_or_outer_frames(self):
        for page in ("6c91e7d2a4f8503bc126","84e5e44efabd2fd66fc5"):
            for a in all_visuals(page):
                v=a["visual"]
                if v["visualType"]!="cardVisual":continue
                for key in ("outline",):
                    for entry in v["objects"][key]:
                        self.assertEqual("false",value(entry["properties"]["show"]))
                self.assertEqual("false",value(v["visualContainerObjects"]["border"][0]["properties"]["show"]))

    def test_packaged_map_names_match_the_district_dimension(self):
        with (ROOT/"data/processed/dim_district.csv").open() as stream:
            districts=list(csv.DictReader(stream))
        names={r["district_name"] for r in districts}
        self.assertEqual(400,len(names))
        topology=json.loads((ROOT/"powerbi/GermanyDataObservatory.Report/StaticResources/RegisteredResources/germany_districts_20248077705754270155.topojson").read_text())
        shapes=topology["objects"]["germany_districts_2024"]["geometries"]
        self.assertEqual(names,{g["properties"]["district_name"] for g in shapes})
    def test_map_queries_use_id_keys_and_scalar_tooltip_values(self):
        for page,vid in ((OV,"2edf0fd369be317800ba"),(AT,"ca000000000000000002")):
            q=visual(page,vid)["visual"]["query"]["queryState"]
            self.assertEqual("district_id",q["Category"]["projections"][0]["field"]["Column"]["Property"])
            for projection in q["Tooltips"]["projections"]:
                self.assertIn(next(iter(projection["field"])),("Measure","Aggregation"))
            self.assertEqual(6,len(q["Tooltips"]["projections"]))

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
