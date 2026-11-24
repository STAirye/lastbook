#!/usr/bin/env python3
"""Offline Madeira builder regressions: python3 -B -m unittest app.tests.test_build_region_pt_30."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import tools.build_region_pt_30 as builder
from tools.build_region_pt_30 import REGION, normalize_pt


class NormalisationTests(unittest.TestCase):
    def test_spellings_people_type_meet_in_one_key(self):
        """Case, accents, the abbreviated street type and name abbreviations share the one stored key."""
        for typed, stored in (
                ('R DE SANTA MARIA', 'rua de santa maria'),
                ('Rua de Santa Maria', 'rua de santa maria'),
                ('r de santa maria', 'rua de santa maria'),
                ('CAM S JOSE', 'caminho sao jose'),
                ('Caminho São José', 'caminho sao jose'),
                ('ER 222', 'estrada regional 222'),
        ):
            with self.subTest(text=typed):
                self.assertEqual(normalize_pt(typed), stored)


class RebuildRecoveryTests(unittest.TestCase):
    """A build stages into data.new/ and replaces data/ only after check passes, so a failure anywhere
    leaves the last good output and its report untouched — the recovery the #420 review asked for.
    The fixture holds a minimal but structurally complete output (real SQLite schemas, empty tables),
    enough for the real check to run end to end and fail only on its content expectations."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp())
        for name, value in (('BASE', self.base), ('SOURCE', self.base / 'source')):
            patcher = mock.patch.object(builder, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        source = self.base / 'source'
        source.mkdir()
        (source / 'fetched.json').write_text(json.dumps({'fetched': '', 'files': {}}), encoding='utf-8')
        self.data = self.base / 'data'
        self.write_minimal_output(self.data)
        self.old = self.files(self.data)
        for step in ('cut_map', 'build_addresses', 'build_places'):
            patcher = mock.patch.object(builder, step, lambda *args: {})
            patcher.start()
            self.addCleanup(patcher.stop)

    def write_minimal_output(self, root):
        """An output the real check can walk: correct schemas, no rows."""
        geo = root / 'derived' / 'geo'
        geo.mkdir(parents=True, exist_ok=True)
        nat = sqlite3.connect(geo / 'national.sqlite')
        nat.executescript('CREATE TABLE feat(id INTEGER PRIMARY KEY, layer TEXT, cls TEXT, name TEXT, minz INTEGER, geom BLOB);'
                          'CREATE TABLE poi(id INTEGER PRIMARY KEY, cls TEXT, name TEXT, lon REAL, lat REAL);')
        nat.close()
        (geo / 'addresses').mkdir()
        addr = sqlite3.connect(geo / 'addresses' / f'{REGION}.sqlite')
        addr.executescript('CREATE TABLE addr(num TEXT, street TEXT, norm TEXT, city TEXT, state TEXT, zip TEXT, lat REAL, lon REAL, district TEXT);'
                           'CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);')
        addr.close()
        places = sqlite3.connect(geo / 'places.sqlite')
        places.executescript("CREATE TABLE place(id INTEGER PRIMARY KEY, name TEXT, kind TEXT, detail TEXT, lat REAL, lon REAL, rank INTEGER, source TEXT);"
                             "CREATE VIRTUAL TABLE place_fts USING fts5(name, detail, content='place', content_rowid='id', tokenize='unicode61');")
        places.close()
        (root / 'map-set.json').write_text(json.dumps({'name': REGION, 'files': {}}), encoding='utf-8')

    def legacy_report(self):
        """The previous builder's report: beside data/, describing exactly the files this output has."""
        outputs = {'map-set.json': {'bytes': (self.data / 'map-set.json').stat().st_size,
                                    'sha256': builder.sha256(self.data / 'map-set.json')}}
        return {'region': REGION, 'built': 'earlier', 'counts': {'kept': 0, 'skipped_without_number': 0},
                'outputs': outputs}

    def files(self, root):
        return {p.relative_to(root).as_posix(): p.read_text(encoding='utf-8', errors='replace')
                for p in sorted(root.rglob('*')) if p.is_file()}

    def new_map(self, fetched, geo):
        (geo / 'national.sqlite').write_text('new map', encoding='utf-8')
        return {}

    def test_a_step_that_fails_leaves_the_previous_output(self):
        def broken(fetched, geo):
            (geo / 'national.sqlite').write_text('half a map', encoding='utf-8')
            raise RuntimeError('injected failure')
        with mock.patch.object(builder, 'build_map', broken), self.assertRaises(RuntimeError):
            builder.build()
        self.assertEqual(self.files(self.data), self.old)

    def test_a_build_that_fails_its_checks_leaves_the_previous_output(self):
        with mock.patch.object(builder, 'build_map', self.new_map), \
                mock.patch.object(builder, 'check', lambda root=None: ['injected check failure']), \
                self.assertRaises(SystemExit):
            builder.build()
        self.assertEqual(self.files(self.data), self.old)
        self.assertEqual(self.files(self.base / 'data.new')['derived/geo/national.sqlite'], 'new map')   # kept to look at

    def test_a_stop_between_the_final_renames_is_repaired_by_the_next_build(self):
        self.data.rename(self.base / 'data.old')
        with mock.patch.object(builder, 'build_map', self.new_map), \
                mock.patch.object(builder, 'check', lambda root=None: ['injected check failure']), \
                self.assertRaises(SystemExit):
            builder.build()
        self.assertEqual(self.files(self.data), self.old)

    def test_a_build_that_passes_replaces_the_previous_output(self):
        checked = []

        def check_records(root=None):
            checked.append(root)
            return []
        with mock.patch.object(builder, 'build_map', self.new_map), \
                mock.patch.object(builder, 'check', check_records):
            builder.build()
        self.assertEqual(checked, [self.base / 'data.new'])           # checked before it was put in place
        new = self.files(self.data)
        self.assertEqual(new['derived/geo/national.sqlite'], 'new map')
        self.assertEqual(json.loads(new['build.json'])['outputs'].keys(), {'derived/geo/national.sqlite', 'map-set.json'})
        self.assertFalse((self.base / 'data.new').exists() or (self.base / 'data.old').exists())


class LegacyLayoutMigrationTests(RebuildRecoveryTests):
    """An output kept by the previous builder carries its report beside data/, not inside it; after a
    failed rebuild, check must read that legacy report instead of giving up on the preserved map."""

    def test_a_failed_rebuild_leaves_an_old_layout_output_checkable(self):
        (self.base / 'build.json').write_text(json.dumps(self.legacy_report()), encoding='utf-8')

        def broken(fetched, geo):
            raise RuntimeError('injected failure')
        with mock.patch.object(builder, 'build_map', broken), self.assertRaises(RuntimeError):
            builder.build()
        self.assertEqual(self.files(self.data), self.old)             # the old output survived the failed rebuild
        self.assertFalse((self.data / 'build.json').exists())         # old layout: the report is only beside data/
        failures = builder.check(self.data)                           # must not stop at a missing report
        joined = ' | '.join(failures)
        self.assertTrue(failures)                                     # the empty fixture fails its content checks, as expected
        self.assertIn('+ 0 without a number', joined)                 # ...judged by the LEGACY report's counts
        self.assertNotIn('no build.json', joined)

    def test_check_prefers_the_report_inside_data_when_both_exist(self):
        (self.base / 'build.json').write_text(json.dumps(self.legacy_report()), encoding='utf-8')
        inside = {'region': REGION, 'built': 'now', 'counts': {'kept': 0, 'skipped_without_number': 3}, 'outputs': {}}
        (self.data / 'build.json').write_text(json.dumps(inside), encoding='utf-8')
        failures = builder.check(self.data)
        joined = ' | '.join(failures)
        self.assertIn('+ 3 without a number', joined)                 # the in-data report drove the address check
        self.assertNotIn('+ 0 without a number', joined)              # not the legacy one beside it

    def test_checking_a_staging_folder_without_its_report_reports_it_missing(self):
        """The legacy fallback belongs to the live data/ folder only: a staging folder without its own
        report must be told as missing, never validated against the live map's report."""
        (self.base / 'build.json').write_text(json.dumps(self.legacy_report()), encoding='utf-8')
        staging = self.base / 'data.new'
        self.write_minimal_output(staging)
        with self.assertRaises(SystemExit) as caught:
            builder.check(staging)
        self.assertIn('no build.json', str(caught.exception))
        self.assertIn('data.new', str(caught.exception))
        # its own report, however slim, is enough
        (staging / 'build.json').write_text(json.dumps(
            {'region': REGION, 'built': 'staged', 'counts': {'kept': 0, 'skipped_without_number': 1}, 'outputs': {}}),
            encoding='utf-8')
        failures = builder.check(staging)
        joined = ' | '.join(failures)
        self.assertIn('+ 1 without a number', joined)                 # judged by the staging's own report


if __name__ == '__main__':
    unittest.main()
