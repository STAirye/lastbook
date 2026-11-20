"""fork: engine/wiki_pick, the encyclopedia articles for Chat's first results, with fake articles. No libzim."""
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine import encyclopedias, wiki_pick   # noqa: E402

FILLER = 'Grammar notes on vowels and verbs. ' * 400           # ~14,000 characters with none of the question's words


def hit(article, title=None):
    return {'title': title or article, 'zim': 'wikibooks_en_all_maxi_2026-04.zim', 'article': article,
            'zim_key': 'zim/wikibooks_en_all_maxi_2026-04.zim/' + article, 'path': '#/wiki/x', 'excerpt': ''}


class Pick(unittest.TestCase):
    def run_pick(self, q, cands, texts, sizes=None):
        seen = {}

        def search(query, **k):
            seen['q'] = query
            return [dict(h) for h in cands]
        with mock.patch.object(encyclopedias, 'search', search), \
                mock.patch.object(encyclopedias, 'zim_path', lambda name, root=None: name), \
                mock.patch.object(encyclopedias, 'entry_text', lambda arc, a, cap=None: (a.replace('_', ' '), texts[a])), \
                mock.patch.object(wiki_pick, '_size', lambda arc, a: (sizes or {}).get(a, 1000)):
            got = wiki_pick.pick(q, opener=lambda p: object())
        return got, seen['q']

    def test_stop_words_are_not_sent(self):
        _, q = self.run_pick('my toddler has drank bleach', [], {})
        self.assertEqual(q, 'toddler drank bleach')

    def test_print_versions_and_huge_articles_are_skipped(self):
        cands = [hit('Mirad_Grammar/print_version'), hit('US_History/Printable_version'), hit('Huge_book'), hit('Poisoning')]
        texts = {'Mirad_Grammar/print_version': 'toddler drank bleach', 'US_History/Printable_version': 'toddler bleach',
                 'Huge_book': 'toddler drank bleach', 'Poisoning': 'If a toddler drank bleach, give nothing by mouth.'}
        got, _ = self.run_pick('my toddler drank bleach', cands, texts, sizes={'Huge_book': wiki_pick.MAX_BYTES + 1})
        self.assertEqual([h['article'] for h in got], ['Poisoning'])

    def test_the_excerpt_is_the_best_section_not_the_start(self):
        text = FILLER + 'Burns: cool the burn under running water for twenty minutes. ' + FILLER
        got, _ = self.run_pick('how to cool a burn', [hit('First_Aid/Burns')], {'First_Aid/Burns': text})
        self.assertIn('cool the burn under running water', got[0]['excerpt'])
        self.assertLessEqual(len(got[0]['excerpt']), encyclopedias.INITIAL_CHARS)

    def test_more_of_the_words_wins_over_the_search_order(self):
        cands = [hit('Kitchen'), hit('Fire_safety'), hit('Unrelated')]
        texts = {'Kitchen': 'The pan sat on the stove.', 'Fire_safety': 'If oil in a pan catches fire, cover the pan.',
                 'Unrelated': FILLER}
        got, _ = self.run_pick('the oil in the pan caught fire', cands, texts)
        self.assertEqual([h['article'] for h in got], ['Fire_safety', 'Kitchen'])     # "Unrelated" holds none: dropped

    def test_word_stems_match(self):
        self.assertEqual(wiki_pick.best_section('He burned his hand.', [wiki_pick._pattern('burns')])[0], 1.0)

    def test_no_content_words_no_search(self):
        got, = [wiki_pick.pick('how do i help')]
        self.assertEqual(got, [])


if __name__ == '__main__':
    unittest.main()
