"""Independent public Volt edition; structural and optional font-metric QA.

Font-metric checks use a locally installed Trebuchet MS, never a substitute.
They check text budgets, not Power BI's runtime rendering or auto-sizing.
"""
import csv
import json
import os
from functools import lru_cache
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
POWERBI = ROOT / 'powerbi'
NAME = 'GermanyDataObservatoryTrebuchet'
REPORT = POWERBI / (NAME + '.Report')
MODEL = POWERBI / (NAME + '.SemanticModel')
PAGES = REPORT / 'definition/pages'
VOLT = 'f4e8945e19de5cff3010'
PUBLIC_NAMES = ['Overview', 'Indicators', 'Cluster Atlas', 'Party Landscape',
                'Party Portrait', 'Change', 'Volt', 'District Explorer', 'Methodology']


def read(path):
    return json.loads(path.read_text())


def literal(obj, default=''):
    return obj.get('expr', {}).get('Literal', {}).get('Value', default)


def visuals():
    for path in PAGES.glob('*/visuals/*/visual.json'):
        yield path, read(path)


class TrebuchetEditionTest(unittest.TestCase):
    def test_independent_project_and_model(self):
        project = read(POWERBI / (NAME + '.pbip'))
        self.assertEqual(NAME + '.Report', project['artifacts'][0]['report']['path'])
        self.assertEqual('../' + NAME + '.SemanticModel',
                         read(REPORT / 'definition.pbir')['datasetReference']['byPath']['path'])
        for suffix in ('.Report', '.SemanticModel'):
            new = read(POWERBI / (NAME + suffix) / '.platform')
            old = read(POWERBI / ('GermanyDataObservatory' + suffix) / '.platform')
            self.assertNotEqual(new['config']['logicalId'], old['config']['logicalId'])
            self.assertEqual(NAME, new['metadata']['displayName'])
        self.assertFalse(list(REPORT.rglob('.pbi')))
        self.assertFalse(list(MODEL.rglob('.pbi')))
        # No analytics or data-source changes in this presentation-only edition.
        original = POWERBI / 'GermanyDataObservatory.SemanticModel/definition'
        for path in original.rglob('*'):
            if path.is_file():
                self.assertEqual(path.read_bytes(), (MODEL / 'definition' / path.relative_to(original)).read_bytes())

    def test_volt_is_public_and_navigable_on_every_public_page(self):
        order = read(PAGES / 'pages.json')['pageOrder']
        names = [read(PAGES / pid / 'page.json')['displayName'] for pid in order[:9]]
        self.assertEqual(PUBLIC_NAMES, names)
        for pid in order[:9]:
            self.assertNotIn('visibility', read(PAGES / pid / 'page.json'))
            navs = [v for p, v in visuals() if p.parents[2].name == pid
                    and v['visual']['visualType'] == 'pageNavigator']
            self.assertEqual(1, len(navs))
            selectors = [p['selector']['id'] for p in navs[0]['visual']['objects']['pages'] if 'selector' in p]
            self.assertEqual(set(order[:9]), set(selectors))
            self.assertEqual(9, len(selectors))
            self.assertEqual(816, navs[0]['position']['width'])
        self.assertEqual('HiddenInViewMode', read(POWERBI / 'GermanyDataObservatory.Report/definition/pages' / VOLT / 'page.json')['visibility'])

    def test_all_explicit_fonts_and_text_runs_use_trebuchet(self):
        def check(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ('fontFamily', 'fontFace', 'detailFontFamily', 'valueFontFamily'):
                        self.assertEqual('Trebuchet MS', value if isinstance(value, str) else literal(value).strip("'"))
                    check(value)
            elif isinstance(obj, list):
                for value in obj:
                    check(value)
        for path in REPORT.rglob('*.json'):
            check(read(path))
        for path, obj in visuals():
            for para in obj['visual'].get('objects', {}).get('general', [{}])[0].get('properties', {}).get('paragraphs', []):
                for run in para.get('textRuns', []):
                    self.assertEqual('Trebuchet MS', run['textStyle']['fontFamily'], str(path))
        custom = next(REPORT.glob('CustomVisuals/*/resources/*.pbiviz.json'))
        self.assertIn('font-family:"Trebuchet MS"!important', read(custom)['content']['css'])

    def test_visuals_stay_inside_their_page(self):
        for path, obj in visuals():
            page = read(path.parents[2] / 'page.json')
            p = obj['position']
            self.assertGreaterEqual(p['x'], 0, str(path))
            self.assertGreaterEqual(p['y'], 0, str(path))
            self.assertLessEqual(p['x'] + p['width'], page['width'] + 0.01, str(path))
            self.assertLessEqual(p['y'] + p['height'], page['height'] + 0.01, str(path))


try:
    from PIL import ImageFont
except ImportError:
    ImageFont = None

FONT_CANDIDATES = [Path('/System/Library/Fonts/Supplemental/Trebuchet MS.ttf'),
                   Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/trebuc.ttf']
FONT = next((p for p in FONT_CANDIDATES if p.exists()), None)


@unittest.skipUnless(ImageFont and FONT, 'Requires Pillow and installed Trebuchet MS for real font metrics')
class TrebuchetTextBudgetTest(unittest.TestCase):
    @staticmethod
    @lru_cache(maxsize=None)
    def font(pt, bold=False):
        path = FONT
        if bold:
            path = FONT.with_name('Trebuchet MS Bold.ttf' if FONT.name == 'Trebuchet MS.ttf' else 'trebucbd.ttf')
        return ImageFont.truetype(str(path), round(pt * 4 / 3 * 6))

    def width(self, text, pt, bold=False):
        return self.font(pt, bold).getlength(text) / 6

    def wrap(self, text, available, pt, bold=False):
        result = []
        for hard_line in text.split('\n'):
            line = ''
            for word in hard_line.split():
                trial = (line + ' ' + word).strip()
                if line and self.width(trial, pt, bold) > available:
                    result.append(line)
                    line = word
                else:
                    line = trial
            result.append(line)
        return result

    def test_static_text_and_navigation_budgets(self):
        for path, obj in visuals():
            v, p = obj['visual'], obj['position']
            paragraphs = v.get('objects', {}).get('general', [{}])[0].get('properties', {}).get('paragraphs', [])
            height = 0
            for paragraph in paragraphs:
                runs = paragraph.get('textRuns', [])
                if not runs:
                    continue
                pt = max(float(r.get('textStyle', {}).get('fontSize', '9pt').replace('pt', '')) for r in runs)
                bold = any(r.get('textStyle', {}).get('fontWeight') == 'bold' for r in runs)
                lines = self.wrap(''.join(r.get('value', '') for r in runs), p['width'] - 8, pt, bold)
                height += len(lines) * pt * 4 / 3 * 1.2 + 3
                self.assertTrue(all(self.width(line, pt, bold) <= p['width'] - 8 for line in lines), str(path))
            if paragraphs:
                self.assertLessEqual(height, p['height'] - 4, str(path))
            for kind in ('title', 'subTitle'):
                props = v.get('visualContainerObjects', {}).get(kind, [{}])[0].get('properties', {})
                text = literal(props.get('text', {})).strip("'")
                if text and literal(props.get('show', {}), 'true') != 'false':
                    pt = float(re.sub('[DL]$', '', literal(props.get('fontSize', {}), '11D' if kind == 'title' else '9D')))
                    self.assertLessEqual(self.width(text, pt), p['width'] - 24, f'{path}: {text}')
            if v['visualType'] == 'pageNavigator':
                for name in PUBLIC_NAMES:
                    self.assertLessEqual(self.width(name, 8), p['width'] / 9 - 8, name)

    def test_all_400_district_context_and_tooltip_names(self):
        def rows(name):
            with (ROOT / 'data/processed' / name).open() as stream:
                return list(csv.DictReader(stream))
        clusters = {r['cluster_id']: r['cluster_short_name'] for r in rows('dim_cluster.csv')}
        assignments = {r['district_id']: r['cluster_id'] for r in rows('fact_cluster_assignment.csv')}
        districts = rows('dim_district.csv')
        self.assertEqual(400, len(districts))
        for row in districts:
            name = row['district_name']
            cluster = clusters[assignments[row['district_id']]]
            # List tooltip: 264px text values, 16px safety allowance.
            for text in (name, row['state_name']):
                self.assertLessEqual(self.width(text, 10, True), 248, text)
            # Peer table: retain complete district names AND five-digit codes.
            peer_label = name + ' [' + row['district_id'] + ']'
            self.assertLessEqual(self.width(peer_label, 8), 208, peer_label)
            # Compact tooltip: 416px header, 12pt bold.
            self.assertLessEqual(self.width(name + ' · ' + cluster, 12, True), 400, name)
            # Explorer context may wrap to two lines in the 40px value card.
            text = name + ' · ' + row['state_name'] + ' · ' + cluster
            self.assertLessEqual(len(self.wrap(text, 462, 11)) * 17.6 + 4, 40, text)


if __name__ == '__main__':
    unittest.main()
