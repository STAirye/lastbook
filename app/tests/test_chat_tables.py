"""Chat shows a markdown table the model copied from a source. A table is marked as linked to a source only when a key
is in it or on the line just before it; a key never carries over to a later table. Cells are the model's words and reach
the page escaped. A row whose width differs from the header is shown as the lines the model wrote, not as a table.

Runs chat.js's md with app.js's esc under Node. Needs Node on PATH; skipped without it. Never packaged."""
import json, re, shutil, subprocess, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NODE = shutil.which('node')
RUN = r"""
const fs = require('fs');
const chat = fs.readFileSync(process.argv[1], 'utf8'), app = fs.readFileSync(process.argv[2], 'utf8');
const esc = app.split('\n').find(l => /^const esc\s*=/.test(l));
const i = chat.indexOf('function md('), j = chat.indexOf('\n  function wire(');
const md = new Function(esc + '\n' + chat.slice(i, j) + '\nreturn md;')();
const m = { sources: [{ key: 'S1' }, { key: 'S2' }] };
process.stdout.write(JSON.stringify(JSON.parse(process.argv[3]).map(t => md(t, m))));
"""


@unittest.skipUnless(NODE, 'needs Node')
class Tables(unittest.TestCase):
    def html(self, *texts):
        r = subprocess.run([NODE, '-e', RUN, str(ROOT / 'web/chat.js'), str(ROOT / 'web/app.js'), json.dumps(texts)],
                           capture_output=True, text=True, check=True)
        out = json.loads(r.stdout)
        return out[0] if len(out) == 1 else out

    @staticmethod
    def tables(h):
        return re.findall(r'<div class="ans-table([^"]*)"', h)

    def test_key_on_line_before_marks_table_as_sourced(self):
        h = self.html('Water per person per day [S1]:\n| Use | Litres |\n|---|---|\n| Drinking | 2 |\n| Cooking | 2 |')
        self.assertEqual(self.tables(h), [''])
        self.assertIn('<th>Use</th><th>Litres</th>', h)
        self.assertIn('<td>Drinking</td><td>2</td>', h)
        self.assertNotIn('|', h)

    def test_key_inside_table_marks_it_as_sourced(self):
        h = self.html('Amounts:\n| Use | Litres |\n|---|---|\n| Drinking | 2 [S2] |')
        self.assertEqual(self.tables(h), [''])

    def test_table_with_no_key_is_marked_own_wording(self):
        h = self.html('Rough amounts:\n| Use | Litres |\n|---|---|\n| Drinking | 2 |')
        self.assertEqual(self.tables(h), [' uncited'])
        self.assertIn('title="Not linked to a source"', h)

    def test_key_does_not_carry_to_a_second_table(self):
        two = ('Water per day [S1]:\n| Use | Litres |\n|---|---|\n| Drinking | 2 |\n'
               '| Day | Tins |\n|---|---|\n| 1 | 3 |')
        self.assertEqual(self.tables(self.html(two.replace('|\n| Day', '|\n\n| Day'))), ['', ' uncited'])
        self.assertEqual(self.tables(self.html('Water per day [S1]:\n| A | B |\n|---|---|\n| 1 | 2 |\n\nFood:\n\n| Day | Tins |\n|---|---|\n| 1 | 3 |')),
                         ['', ' uncited'])

    def test_key_does_not_carry_past_a_blank_line(self):
        h = self.html('Water per day [S1].\n\n| Use | Litres |\n|---|---|\n| Drinking | 2 |')
        self.assertEqual(self.tables(h), [' uncited'])

    def test_escaped_pipe_stays_in_its_cell(self):
        h = self.html('From the chart [S1]:\n| Item | Note |\n|---|---|\n| A \\| B | 5 |')
        self.assertEqual(self.tables(h), [''])
        self.assertIn('<td>A | B</td><td>5</td>', h)

    def test_row_of_wrong_width_shows_the_lines_as_written(self):
        for bad in ('| 1 | 2 | 3 |', '| 1 |'):
            h = self.html(f'Doses [S1]:\n| Age | Dose |\n|---|---|\n| Adult | 2 |\n{bad}')
            self.assertEqual(self.tables(h), [])
            self.assertIn('<p class="ans-raw">', h)
            self.assertIn('| Age | Dose |<br>|---|---|<br>| Adult | 2 |<br>' + bad, h)
        h = self.html('Doses:\n| Age | Dose |\n|---|---|\n| Adult | 2 | 9 |')
        self.assertIn('<p class="ans-raw uncited" title="Not linked to a source">', h)

    def test_cells_are_escaped(self):
        h = self.html('Data [S1]:\n| <img src=x onerror=alert(1)> | "><svg onload=alert(1)> |\n|---|---|\n| <b>x</b> | & |',
                      'Data:\n| <script>alert(1)</script> | x |\n| 1 |')
        for x in h:
            self.assertNotIn('<img', x)
            self.assertNotIn('<svg', x)
            self.assertNotIn('<script', x)
            self.assertNotIn('<b>', x)
        self.assertIn('<th>&lt;img src=x onerror=alert(1)&gt;</th>', h[0])
        self.assertIn('<td>&amp;</td>', h[0])


if __name__ == '__main__':
    unittest.main()
