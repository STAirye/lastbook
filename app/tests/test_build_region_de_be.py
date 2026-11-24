#!/usr/bin/env python3
"""Offline Berlin builder regressions: python3 -B -m unittest app.tests.test_build_region_de_be."""
import ast
import json
import sqlite3
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import tools.build_region_de_be as builder
from tools.build_region_de_be import NORM, REGION, gpkg_middle, house, normalize_de

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = json.loads((ROOT / 'app' / 'tests' / 'fixtures' / 'de_be_queries.json').read_text(encoding='utf-8'))


def build_map_functions():
    """wkb_parts, gpkg_parts and bbox from tools/build_map.py, which runs its build on import, so only these are loaded."""
    tree = ast.parse((ROOT / 'tools' / 'build_map.py').read_text(encoding='utf-8'))
    wanted = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ('wkb_parts', 'gpkg_parts', 'bbox')]
    namespace = {'struct': struct}
    exec(compile(ast.Module(body=wanted, type_ignores=[]), 'tools/build_map.py', 'exec'), namespace)
    return namespace


def gpkg(wkb, envelope=b'', code=0):
    """A GeoPackage geometry blob: magic, version, flags (little-endian header, envelope code), SRS 4326, envelope, WKB."""
    return b'GP' + bytes([0, (code << 1) | 1]) + struct.pack('<i', 4326) + envelope + wkb


def point(x, y, order='<'):
    return bytes([1 if order == '<' else 0]) + struct.pack(order + 'Idd', 1, x, y)


def polygon(*rings):
    out = struct.pack('<BII', 1, 3, len(rings))
    for ring in rings:
        out += struct.pack('<I', len(ring)) + b''.join(struct.pack('<dd', *xy) for xy in ring)
    return out


class SchemeTests(unittest.TestCase):
    def test_fixture_and_builder_name_the_same_scheme(self):
        """The index records meta norm = de-1; a runtime reads that key to choose the rule, so both must agree."""
        self.assertEqual((FIXTURE['norm'], FIXTURE['region']), (NORM, REGION))
        self.assertEqual(FIXTURE['index_contract']['meta']['norm'], NORM)

    def test_spellings_people_type_meet_in_one_key(self):
        """ß, ss, ü, ue, upper case and 'Str.' are typed interchangeably; each must fold to the key the index stores."""
        for example in FIXTURE['normalization_examples']:
            with self.subTest(text=example['input']):
                self.assertEqual(normalize_de(example['input']), example['expected'])
        self.assertEqual(normalize_de('Müllerstraße'), 'muellerstr')
        self.assertEqual(normalize_de('Straße des 17. Juni'), 'str des 17 juni')   # the 17 stays in the street
        self.assertEqual(normalize_de('Müllerstraße'), 'muellerstr')        # a decomposed ü, as macOS can give it


class HouseNumberTests(unittest.TestCase):
    def test_house_numbers_are_stored_one_way(self):
        """'12a', '12 A' and '012A' must meet one stored form, or an exact search would miss the house."""
        self.assertEqual(house({'hausnr': '012', 'hausnrz': 'a'}), '12A')
        self.assertEqual(house({'hausnr': ' 5 ', 'hausnrz': None}), '5')
        self.assertEqual(house({'hausnr': '', 'hausnrz': 'a'}), '')       # no number, no address row


class FixtureContractTests(unittest.TestCase):
    """Each expected answer must follow from the fixture rows by the rule the fixture states, so a runtime that fails
    one of them has a real gap, not an impossible expectation."""

    rows = {row['id']: row for row in FIXTURE['address_rows']}

    @staticmethod
    def place_matches(prefix, row):
        places = (normalize_de(row['city']), normalize_de(row['district']), normalize_de(f"{row['city']} {row['district']}"))
        return any(place.startswith(prefix) for place in places)

    def answer(self, case):
        lookup, wanted = case['lookup'], case.get('filter', {})
        return [key for key, row in self.rows.items()
                if row['norm'] == lookup['norm'] and row['num'] == lookup['num']
                and row['zip'] == wanted.get('zip', row['zip'])
                and (not wanted.get('place_prefix') or self.place_matches(wanted['place_prefix'], row))]

    def test_rows_follow_the_index_contract(self):
        for row in self.rows.values():
            with self.subTest(row=row['id']):
                self.assertEqual(row['norm'], normalize_de(row['street']))
                self.assertEqual((row['state'], row['city']), (REGION, 'Berlin'))
                self.assertRegex(row['num'], r'^[1-9][0-9]*[A-Z]?$')       # the form house() stores

    def test_lookups_name_the_query_in_the_index_spelling(self):
        """A query's street folds to its lookup key, so the expectation is reachable through normalize_de."""
        for case in FIXTURE['address_queries']:
            with self.subTest(query=case['query']):
                self.assertIn(case['lookup']['norm'], normalize_de(case['query']))

    def test_expected_houses_follow_from_the_rows(self):
        for case in FIXTURE['address_queries'] + FIXTURE['no_house_queries']:
            with self.subTest(query=case['query']):
                self.assertEqual(self.answer(case), case['expected_fixture_ids'])
                for key in case['expected_fixture_ids']:
                    row = self.rows[key]
                    if 'expected_name' in case:
                        self.assertEqual(case['expected_name'], f"{row['street']} {row['num']}")
                    if 'expected_detail' in case:
                        self.assertEqual(case['expected_detail'], f"{row['zip']} {row['city']}-{row['district']}")


class WellPlacementTests(unittest.TestCase):
    """build_map.py drops the water_well class, so the builder places Berlin's pumps itself; they must land exactly
    where build_map.py puts any point (the middle of its box), or pumps would sit beside their OpenStreetMap position."""

    def test_pumps_land_where_build_map_puts_a_point(self):
        bm = build_map_functions()
        ring = [(13.40, 52.50), (13.42, 52.50), (13.42, 52.53), (13.40, 52.53), (13.40, 52.50)]
        hole = [(13.405, 52.51), (13.41, 52.51), (13.41, 52.52), (13.405, 52.51)]
        multi = struct.pack('<BII', 1, 6, 2) + polygon(ring) + polygon([(13.5, 52.4), (13.6, 52.4), (13.6, 52.45), (13.5, 52.4)])
        blobs = {
            'point': gpkg(point(13.3777, 52.5163)),
            'big-endian point': gpkg(point(13.3777, 52.5163, '>')),
            'point with envelope': gpkg(point(13.1, 52.4), struct.pack('<4d', 13.1, 13.1, 52.4, 52.4), code=1),
            'polygon with a hole': gpkg(polygon(ring, hole)),
            'multipolygon': gpkg(multi),
        }
        for label, blob in blobs.items():
            with self.subTest(geometry=label):
                minx, maxx, miny, maxy = bm['bbox'](bm['gpkg_parts'](blob))
                self.assertEqual(gpkg_middle(blob), ((minx + maxx) / 2, (miny + maxy) / 2))


def geojson_point(lon, lat, **properties):
    return {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [lon, lat]}, 'properties': properties}


class PlaceSourceTests(unittest.TestCase):
    """build_map puts the Geoportal's hospitals, pharmacies, fire stations and police into national.sqlite in place of
    OpenStreetMap's, so the place finder must not label everything it finds there as OpenStreetMap."""

    def test_each_place_names_the_source_it_came_from(self):
        layers = {'hospitals_plan': [geojson_point(13.3777, 52.5255, kkh_standort='Campus Charité Mitte')],
                  'police': [geojson_point(13.41, 52.52, langbezeichnung='Abschnitt 32')]}
        with tempfile.TemporaryDirectory() as tmp:
            geo = Path(tmp)
            national = sqlite3.connect(geo / 'national.sqlite')
            national.executescript('CREATE TABLE poi(id INTEGER PRIMARY KEY, cls TEXT, name TEXT, lon REAL, lat REAL);'
                                   'CREATE TABLE feat(id INTEGER PRIMARY KEY, layer TEXT, cls TEXT, name TEXT, minz INTEGER, geom BLOB);')
            national.executemany('INSERT INTO poi(cls,name,lon,lat) VALUES (?,?,?,?)', [   # as build_map leaves it
                ('hospital', 'Campus Charité Mitte', 13.3777, 52.5255), ('police', 'Polizei Abschnitt 32', 13.41, 52.52),
                ('water_well', 'Plumpe', 13.40, 52.51), ('cafe', 'Café Einstein', 13.35, 52.50)])
            national.commit()
            national.close()
            with mock.patch.object(builder, 'features', lambda key: layers.get(key, [])):
                builder.build_places({}, geo)
            db = sqlite3.connect(geo / 'places.sqlite')
            found = db.execute('SELECT name,kind,detail,source FROM place ORDER BY name').fetchall()
            db.close()
        self.assertEqual(found, [
            ('Café Einstein', 'cafe', 'Berlin (OpenStreetMap)', 'OpenStreetMap'),
            ('Campus Charité Mitte', 'hospital', 'Berlin (Geoportal)', 'Geoportal Berlin'),     # once, from its record
            ('Plumpe', 'water well', 'Berlin (OpenStreetMap)', 'OpenStreetMap'),
            ('Polizei Abschnitt 32', 'police', 'Berlin (Geoportal)', 'Geoportal Berlin'),
        ])


class RebuildTests(unittest.TestCase):
    """A rebuild runs beside the last good output: until the new one passes check, data/ and its build.json stay as
    they were, so a failed download, a full disk or a bad source never leaves Berlin without a map."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        (self.base / 'source').mkdir()
        (self.base / 'source' / 'fetched.json').write_text('{}', encoding='utf-8')
        self.old = {'derived/geo/national.sqlite': 'last good map', 'build.json': '{"built": "before"}'}
        for rel, text in self.old.items():
            (self.base / 'data' / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.base / 'data' / rel).write_text(text, encoding='utf-8')
        for name, value in (('BASE', self.base), ('SOURCE', self.base / 'source'), ('log', lambda *args: None),
                            ('build_addresses', lambda fetched, geo: {}), ('build_places', lambda fetched, geo: {})):
            patcher = mock.patch.object(builder, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def files(self, folder):
        return {f.relative_to(folder).as_posix(): f.read_text(encoding='utf-8') for f in folder.rglob('*') if f.is_file()}

    @staticmethod
    def new_map(fetched, geo):
        (geo / 'national.sqlite').write_text('new map', encoding='utf-8')
        return {}

    def test_a_step_that_fails_leaves_the_previous_output(self):
        def broken(fetched, geo):
            (geo / 'national.sqlite').write_text('half a map', encoding='utf-8')
            raise RuntimeError('injected failure')
        with mock.patch.object(builder, 'build_map', broken), self.assertRaises(RuntimeError):
            builder.build()
        self.assertEqual(self.files(self.base / 'data'), self.old)

    def test_a_build_that_fails_its_checks_leaves_the_previous_output(self):
        with mock.patch.object(builder, 'build_map', self.new_map), \
                mock.patch.object(builder, 'check', lambda data: ['injected check failure']), self.assertRaises(SystemExit):
            builder.build()
        self.assertEqual(self.files(self.base / 'data'), self.old)
        self.assertEqual(self.files(self.base / 'data.new')['derived/geo/national.sqlite'], 'new map')   # kept to look at

    def test_a_stop_between_the_final_renames_is_repaired_by_the_next_build(self):
        (self.base / 'data').rename(self.base / 'data.old')
        with mock.patch.object(builder, 'build_map', self.new_map), \
                mock.patch.object(builder, 'check', lambda data: ['injected check failure']), self.assertRaises(SystemExit):
            builder.build()
        self.assertEqual(self.files(self.base / 'data'), self.old)

    def test_a_build_that_passes_replaces_the_previous_output(self):
        checked = []
        with mock.patch.object(builder, 'build_map', self.new_map), \
                mock.patch.object(builder, 'check', lambda data: checked.append(data) or []):
            builder.build()
        self.assertEqual(checked, [self.base / 'data.new'])           # checked before it was put in place
        new = self.files(self.base / 'data')
        self.assertEqual(new['derived/geo/national.sqlite'], 'new map')
        self.assertEqual(json.loads(new['build.json'])['outputs'].keys(), {'derived/geo/national.sqlite', 'map-set.json'})
        self.assertFalse((self.base / 'data.new').exists() or (self.base / 'data.old').exists())


if __name__ == '__main__':
    unittest.main()
