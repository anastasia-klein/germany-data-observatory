#!/usr/bin/env python3
"""Package the validated analytical snapshot for a server-free GitHub Pages app.

No analytical model is retrained here. Source district IDs remain strings and
the exported vote shares retain their percent (not fraction) units.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/processed'
OUT = ROOT / 'web/data'
YEARS = [2017, 2021, 2025]
FEATURE_ORDER = ['age_65_plus_share', 'age_under_18_share',
                 'population_change_per_10000', 'migration_balance_per_10000',
                 'foreign_population_share', 'population_density',
                 'unemployment_rate', 'manufacturing_employment_share',
                 'workplace_density', 'gdp_per_capita', 'disposable_income_per_capita',
                 'natural_balance_per_10000', 'minimum_security_rate', 'services_employment_share']


def rows(name):
    with (SOURCE / (name + '.csv')).open(encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def project(point):
    lon, lat = point[:2]
    return lon * math.pi / 180, math.log(math.tan(math.pi / 4 + lat * math.pi / 360))


def geometry_path(geometry, bounds):
    left, bottom, right, top = bounds
    scale = min(390 / (right-left), 540 / (top-bottom))
    dx = (400 - (right-left)*scale)/2
    dy = (550 - (top-bottom)*scale)/2
    polygons = geometry['coordinates'] if geometry['type'] == 'MultiPolygon' else [geometry['coordinates']]
    result = []
    for polygon in polygons:
        for ring in polygon:
            commands = []
            for point in ring:
                x, y = project(point)
                xy = (round(dx+(x-left)*scale, 2), round(dy+(top-y)*scale, 2))
                # Remove repeated points introduced by display-precision rounding.
                if not commands or xy != commands[-1]:
                    commands.append(xy)
            if len(commands) >= 3:
                result.append('M'+'L'.join(f'{x:g},{y:g}' for x,y in commands)+'Z')
    return ''.join(result)


def state_geometries():
    path = ROOT / 'powerbi/GermanyDataObservatory.Report/StaticResources/RegisteredResources/germany_states_2024.topojson'
    topology = json.loads(path.read_text())
    scale, translate = topology['transform']['scale'], topology['transform']['translate']
    arcs = []
    for arc in topology['arcs']:
        x = y = 0
        points = []
        for dx, dy in arc:
            x += dx
            y += dy
            points.append([x*scale[0]+translate[0], y*scale[1]+translate[1]])
        arcs.append(points)
    def ring(indices):
        points = []
        for index in indices:
            part = arcs[index] if index >= 0 else list(reversed(arcs[~index]))
            points.extend(part if not points else part[1:])
        return points
    result = {}
    for item in next(iter(topology['objects'].values()))['geometries']:
        polys = item['arcs'] if item['type'] == 'MultiPolygon' else [item['arcs']]
        result[item['properties']['state_code']] = {'type':'MultiPolygon',
            'coordinates': [[ring(indices) for indices in polygon] for polygon in polys]}
    return result


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    features_by_id = {r['feature_id']:r for r in rows('dim_district_feature')}
    features = [features_by_id[f] for f in FEATURE_ORDER]
    parties = sorted(rows('dim_party_group'), key=lambda r:int(r['party_display_order']))
    feature_index = {r['feature_id']:i for i,r in enumerate(features)}
    party_index = {r['party_group_id']:i for i,r in enumerate(parties)}
    assignment = {r['district_id']:r['cluster_id'] for r in rows('fact_cluster_assignment')}
    pca = {r['district_id']:[float(r[f'pc{i}']) for i in range(1,5)] for r in rows('district_pca')}
    districts = []
    for r in rows('dim_district'):
        districts.append({'id':r['district_id'], 'name':r['district_name'],
            'state':r['state_code'], 'type':r['district_type'], 'cluster':assignment[r['district_id']],
            'features':[None]*len(features), 'votes':[[None]*6 for _ in YEARS],
            'turnout':[None]*3, 'pca':pca[r['district_id']]})
    lookup = {d['id']:d for d in districts}
    for r in rows('fact_district_features'):
        lookup[r['district_id']]['features'][feature_index[r['feature_id']]] = float(r['value'])
    for r in rows('fact_district_election_results'):
        y = YEARS.index(int(r['election_year']))
        lookup[r['district_id']]['votes'][y][party_index[r['party_group_id']]] = float(r['second_vote_share_percent']) if r['second_vote_share_percent'] else None
    for r in rows('fact_district_election_turnout'):
        lookup[r['district_id']]['turnout'][YEARS.index(int(r['election_year']))] = float(r['turnout_percent'])
    for i, feature in enumerate(features):
        raw = [d['features'][i] for d in districts]
        values = [math.log1p(v) if feature['transform']=='log1p' else v for v in raw]
        feature.update(mean=round(statistics.mean(raw),10), sd=round(statistics.pstdev(raw),10),
                       modelMean=round(statistics.mean(values),10), modelSD=round(statistics.pstdev(values),10))
    clusters = rows('dim_cluster')
    profiles = rows('cluster_profiles')
    for c in clusters:
        c['raw'] = {r['feature_id']:float(r['mean_raw_value']) for r in profiles if r['cluster_id']==c['cluster_id']}
        c['z'] = {r['feature_id']:float(r['mean_z_score']) for r in profiles if r['cluster_id']==c['cluster_id']}
    volt = {str(y):{} for y in [2021,2025]}
    for r in rows('fact_election_party_results'):
        y = r['election_id'].replace('BTW','')
        if y in volt:
            state = volt[y].setdefault(r['state_code'], {'votes':0, 'valid':0})
            state['valid'] += int(r['votes'])
            if r['party_id']=='party_volt':
                state['votes'] += int(r['votes'])
    geography = json.loads((SOURCE/'germany_districts_2024.geojson').read_text())
    points = []
    for f in geography['features']:
        polys = f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']]
        points.extend(project(p) for poly in polys for ring in poly for p in ring)
    bounds = min(x for x,y in points), min(y for x,y in points), max(x for x,y in points), max(y for x,y in points)
    paths = {f['properties']['district_id']:geometry_path(f['geometry'],bounds) for f in geography['features']}
    state_paths = {code:geometry_path(g,bounds) for code,g in state_geometries().items()}
    assert len(districts)==400 and set(paths)==set(lookup)
    assert all(None not in d['features'] for d in districts)
    metadata = json.loads((SOURCE/'clustering_model_metadata.json').read_text())
    # Hashes make the exact underlying snapshot identifiable without embedding timestamps.
    hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCE.glob('*.csv'))}
    payload = dict(years=YEARS, features=features, parties=parties, districts=districts,
                   clusters=clusters, states=rows('dim_state'), volt=volt, model=metadata, sourceHashes=hashes)
    for name,data in [('snapshot',payload),('geometry',{'districts':paths,'states':state_paths})]:
        (OUT/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')
    print(f'Packaged {len(districts)} districts, {len(features)} indicators and {len(state_paths)} states for GitHub Pages.')


if __name__ == '__main__':
    build()
