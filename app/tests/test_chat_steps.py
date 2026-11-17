"""Chat's "How it searched" list shows the model's own tool calls. They are the model's words, not ours: everything in a
step must reach the page escaped, whatever shape the model sent (a list, a single value, text with markup in it).

Runs chat.js's stepText with app.js's esc under Node. Needs Node on PATH; skipped without it. Never packaged."""
import json, re, shutil, subprocess, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NODE = shutil.which('node')
RUN = r"""
const fs = require('fs');
const chat = fs.readFileSync(process.argv[1], 'utf8'), app = fs.readFileSync(process.argv[2], 'utf8');
const esc = app.split('\n').find(l => /^const esc\s*=/.test(l));
const i = chat.indexOf('function stepText('), j = chat.indexOf('\n  function srcHref');
const stepText = new Function(esc + '\n' + chat.slice(i, j) + '\nreturn stepText;')();
const out = JSON.parse(process.argv[3]).map(s => { try { return stepText(s) } catch (e) { return 'THROW ' + e.message } });
process.stdout.write(JSON.stringify(out));
"""


MD = r"""
const fs = require('fs');
const chat = fs.readFileSync(process.argv[1], 'utf8').replace(/\r/g, ''), app = fs.readFileSync(process.argv[2], 'utf8');
const esc = app.split('\n').find(l => /^const esc\s*=/.test(l));
const i = chat.indexOf('function md('), j = chat.indexOf('\n  }\n', i) + 4;     // its closing brace (a Windows checkout has CRLF)
const md = new Function(esc + '\n' + chat.slice(i, j) + '\nreturn md;')();
process.stdout.write(JSON.stringify(md(process.argv[3], {sources: [{key: 'S1'}], cited: [{key: 'S1'}]})));
"""


@unittest.skipUnless(NODE, 'needs Node')
class SpanishAnswers(unittest.TestCase):
    """fork: an answer in Spanish (docs/FORK.md, 3i). Its special headings may come translated, and its sentences start with
    ¿, ¡ or capitals like É and Ñ."""

    def html(self, text):
        r = subprocess.run([NODE, '-e', MD, str(ROOT / 'web/chat.js'), str(ROOT / 'web/app.js'), text],
                           capture_output=True, text=True, encoding='utf-8', check=True)
        return json.loads(r.stdout)

    def test_translated_headings_are_the_special_sections(self):
        for head, sec in (('**No encontrado en la biblioteca:**', 'missing'), ('## NO SE ENCONTRÓ EN LA BIBLIOTECA', 'missing'),
                          ('**Si la biblioteca no cubre algo que necesitas:**', 'missing'),
                          ('**Información que falta en la biblioteca**', 'missing'),
                          ('### Las fuentes no coinciden', 'disagree'), ('**Desacuerdo entre las fuentes:**', 'disagree'),
                          ('**Mi propio razonamiento (no de la biblioteca):**', 'reasoning'),
                          ('**Not found in the library:**', 'missing')):
            got = self.html(f'Hierve el agua [S1].\n\n{head}\nNada sobre el yodo ni la pastilla de cloro.')
            self.assertIn(f'<div class="sec-{sec}">', got, head)
            if sec != 'missing' or 'biblioteca' in head:
                self.assertNotIn(head.strip('*#: '), got)       # replaced by Chat's own title
            self.assertIn('Nada sobre el yodo ni la pastilla de cloro.', got)

    def test_body_lines_and_other_headings_stay(self):
        got = self.html('**Pasos para el niño**\nNo hay luz en la biblioteca del pueblo [S1].\n\n'
                        '**Lo que dice la biblioteca:**\nÑandú, pingüino, güemul: agüita hervida [S1].')
        self.assertNotIn('sec-', got)
        for t in ('Pasos para el niño', 'Lo que dice la biblioteca', 'No hay luz en la biblioteca del pueblo',
                  'Ñandú, pingüino, güemul: agüita hervida'):
            self.assertIn(t, got)

    def test_uncited_sentences_after_spanish_punctuation(self):
        got = self.html('Hierve el agua un minuto [S1]. ¿Está turbia? Fíltrala con un paño limpio antes de hervirla. '
                        'Él dice que sí [S1]. ¡Ojo con el vapor caliente en la cara del niño! Ñuble queda lejos de aquí, a dos horas.')
        uncited = re.findall(r'<span class="uncited"[^>]*>(.*?)</span>', got)
        self.assertIn('¡Ojo con el vapor caliente en la cara del niño!', uncited)
        self.assertIn('Ñuble queda lejos de aquí, a dos horas.', uncited)
        self.assertIn('Fíltrala con un paño limpio antes de hervirla.', uncited)   # "¿Está turbia?" is too short to mark
        self.assertFalse(any('[S1]' in u or 'cite' in u for u in uncited))
        self.assertNotIn('Él dice que sí', ' '.join(uncited))     # cited, so not marked


@unittest.skipUnless(NODE, 'needs Node')
class Steps(unittest.TestCase):
    def text(self, steps):
        r = subprocess.run([NODE, '-e', RUN, str(ROOT / 'web/chat.js'), str(ROOT / 'web/app.js'), json.dumps(steps)],
                           capture_output=True, text=True, encoding='utf-8', check=True)   # Node writes UTF-8; Windows would read cp1252
        return json.loads(r.stdout)

    def test_read_pages_is_escaped_whatever_the_model_sent(self):
        got = self.text([
            {'name': 'read_pages', 'args': {'doc_id': 'x', 'pages': [3, 4]}, 'summary': {'title': 'FEMA'}},
            {'name': 'read_pages', 'args': {'doc_id': 'x', 'pages': ['<img src=x onerror=alert(1)>']}, 'summary': {'title': 'T'}},
            {'name': 'read_pages', 'args': {'doc_id': 'x', 'pages': '"><svg onload=alert(1)>'}, 'summary': {'title': 'T'}},
            {'name': 'read_pages', 'args': {'doc_id': 'x', 'pages': 7}, 'summary': {'title': 'T'}},
        ])
        self.assertEqual(got[0], 'Read FEMA, pages 3, 4')
        self.assertEqual(got[1], 'Read T, page &lt;img src=x onerror=alert(1)&gt;')
        self.assertEqual(got[2], 'Read T, page &quot;&gt;&lt;svg onload=alert(1)&gt;')
        self.assertEqual(got[3], 'Read T, page 7')
        for t in got:
            self.assertNotIn('<', t)

    def test_odd_shapes_neither_throw_nor_leak(self):
        # JSON can carry objects whose toString is not a function; converting them would throw and blank the answer.
        odd = [{'toString': 'x'}, {'a': 1}, [1, 2], None, True]
        got = self.text([
            {'name': 'read_pages', 'args': {'doc_id': 'x', 'pages': odd + [5, '6']}, 'summary': {'title': 'T'}},
            {'name': 'read_pages', 'args': {'doc_id': 'x', 'pages': {'toString': 'x'}}, 'summary': {'title': 'T'}},
            {'name': 'lookup_place', 'args': {'query': 'clinic', 'pages': {'toString': 'x'}}, 'summary': {}},
            {'name': 'search_library', 'args': {'query': 'water', 'pages': {'toString': 'x'}}, 'summary': {'count': 1}},
            {'name': 'view_page', 'args': {'doc_id': 'x', 'page': 3, 'pages': {'toString': 'x'}}, 'summary': {'title': 'T'}},
        ])
        for t in got:
            self.assertFalse(t.startswith('THROW'), t)
            self.assertNotIn('<', t)
        self.assertEqual(got[0], 'Read T, pages 5, 6')
        self.assertEqual(got[1], 'Read T, page ')
        self.assertEqual(got[2], 'Looked up “clinic” on the offline map')
        self.assertEqual(got[3], 'Searched “water” — 1 passage')
        self.assertEqual(got[4], 'Looked at the picture of T, page 3')

    def test_odd_values_in_other_arguments(self):
        bad = {'toString': 'x'}
        got = self.text([
            {'name': 'search_library', 'args': {'query': bad, 'kind': bad}, 'summary': {'count': 2}},
            {'name': 'lookup_place', 'args': {'query': bad}, 'summary': {}},
            {'name': 'view_page', 'args': {'doc_id': bad, 'page': bad}, 'summary': {'title': 'T'}},
            {'name': 'read_pages', 'args': {'doc_id': bad, 'pages': [2]}, 'summary': {}},
            {'name': 'search_library', 'args': 'not an object', 'summary': {'count': 0}},
            {'name': 'search_library', 'args': {'query': '<b>x</b>', 'kind': 'video'}, 'summary': {'count': 1}},
        ])
        for t in got:
            self.assertFalse(t.startswith('THROW'), t)
            self.assertNotIn('<', t)
        self.assertEqual(got[0], 'Searched “” — 2 passages')
        self.assertEqual(got[2], 'Looked at the picture of T, page ')
        self.assertEqual(got[3], 'Read , page 2')
        self.assertEqual(got[5], 'Searched “&lt;b&gt;x&lt;/b&gt;” (videos) — 1 passage')


if __name__ == '__main__':
    unittest.main()
