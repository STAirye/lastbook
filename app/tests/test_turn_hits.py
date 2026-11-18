#!/usr/bin/env python3
"""fork: the first library search for a message inside a conversation (assistant.turn_hits), with hybrid() stubbed.

  python -B -m unittest app.tests.test_turn_hits [-v]

No library and no model: hybrid returns canned hits keyed by the query, and the catalogue holds one book, so the previous
answer's "(Title, p. N)" citations come back as carried pages. Every route (first, follow, noise, correct, danger), noise
never becoming the earlier message, a correction dropping the pages already shown, a new danger sign carrying nothing,
the English search words, and one-message conversations searching as before. Never packaged."""
import sys, unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT)]


def hit(doc, page):
    return {'doc_id': doc, 'page': page, 't': None, 'kind': 'pdf', 'title': doc}


CANNED = {
    'how do i purify water': [hit('water', 1), hit('water', 2), hit('boil', 3), hit('bleach', 4)],
    'and if i have no bleach?': [hit('boil', 3), hit('sun', 5), hit('filter', 6), hit('cloth', 7), hit('clay', 8)],
    'how do i purify water and if i have no bleach?': [hit('boil', 3), hit('filter', 6), hit('sand', 9)],
    'THE KITCHEN IS ON FIRE': [hit('grease', 1), hit('escape', 2), hit('exting', 3), hit('smoke', 4), hit('alarm', 5),
                               hit('kids', 6)],
    'how do i purify water THE KITCHEN IS ON FIRE': [hit('water', 1), hit('grease', 1), hit('stove', 7)],
    'burned my hand lighting the fire': [hit('burn', 1), hit('firemake', 2), hit('blister', 3)],
    "the smoke, he can't breathe": [hit('firemake', 2), hit('smokeinh', 1), hit('cpr', 4), hit('burn', 1)],
    "burned my hand lighting the fire the smoke, he can't breathe": [hit('burn', 1), hit('smokeinh', 1), hit('co', 5)],
    'my son is choking': [hit('choke', 1), hit('heimlich', 2), hit('cpr', 3)],
    "he's turning blue": [hit('cyanosis', 1)],
    "my son is choking he's turning blue": [hit('choke', 1), hit('cpr', 3), hit('blue', 4)],
    'hervir agua': [],
    'boil water': [hit('boil', 3), hit('water', 1)],
    'boil water at night': [hit('night', 1), hit('boil', 3)],
    'boil water dark': [hit('night', 1)],
    'Burn': [hit('burn', 1), hit('blister', 3)],
    'how do i purify water Burn': [hit('water', 1)],
}


class TurnHits(unittest.TestCase):
    def setUp(self):
        before = set(sys.modules)
        import assistant
        self.addCleanup(lambda: [sys.modules.pop(n, None) for n in set(sys.modules) - before])
        self.a = assistant
        self.calls = []

        def hybrid(q, k=8, kind='any', doc=None):
            self.calls.append(q)
            return [dict(h) for h in CANNED.get(q, [])][:k]
        cat = {'by_id': {'water': {'id': 'water', 'kind': 'pdf', 'title': 'Water Book'}}}
        S = mock.Mock(catalog=lambda: cat, public=lambda r: {'title': r['title'], 'publisher': '', 'year': None, 'trust': '',
                                                             'pages': 9}, page_texts=lambda r: ['page text'] * 9)
        for name, value in (('hybrid', hybrid), ('S', S)):
            p = mock.patch.object(assistant, name, value)
            p.start()
            self.addCleanup(p.stop)
        # the library's words, as _vocab() would read them from the search database
        p = mock.patch.dict(assistant._VOCAB, words={'water', 'purify', 'bleach', 'kitchen', 'fire', 'smoke', 'breathe', 'son',
                                                     'choking', 'turning', 'blue', 'burned', 'hand', 'lighting', 'boil', 'cpr',
                                                     'stop', 'bleeding', 'shivering'})
        p.start()
        self.addCleanup(p.stop)

    def convo(self, *turns):
        return [{'role': 'user' if n % 2 == 0 else 'assistant', 'content': t} for n, t in enumerate(turns)]

    def keys(self, hits):
        return [(h['doc_id'], h['page']) for h in hits]

    # ------------------------------------------------------------------ unchanged
    def test_one_message_is_its_own_search(self):
        hits, info = self.a.turn_hits(self.convo('how do i purify water'))
        self.assertEqual(self.calls, ['how do i purify water'])
        self.assertEqual(self.keys(hits), self.keys(CANNED['how do i purify water']))
        self.assertEqual((info['route'], info['buttons']), ('first', False))

    def test_one_noise_message_is_still_searched(self):
        hits, info = self.a.turn_hits(self.convo('jdjdjdk'))
        self.assertEqual((self.calls, hits, info['buttons']), (['jdjdjdk'], [], False))

    def test_followup_off_searches_the_message_alone(self):
        hits, info = self.a.turn_hits(self.convo('how do i purify water', '', 'THE KITCHEN IS ON FIRE'), followup=False)
        self.assertEqual(self.calls, ['THE KITCHEN IS ON FIRE'])
        self.assertEqual(info['route'], 'first')

    # ------------------------------------------------------------------ follow
    def test_follow_up_carries_the_cited_pages_first(self):
        hits, info = self.a.turn_hits(self.convo('how do i purify water', 'Boil it (Water Book, p. 2).', 'and if i have no bleach?'))
        self.assertEqual(info['route'], 'follow')
        self.assertEqual(self.calls, ['and if i have no bleach?', 'how do i purify water and if i have no bleach?'])
        # carried page, this message's best 4, the joined search's new ones, the rest
        self.assertEqual(self.keys(hits), [('water', 2), ('boil', 3), ('sun', 5), ('filter', 6), ('cloth', 7), ('sand', 9),
                                           ('clay', 8)])
        self.assertEqual(hits[0]['found_by'], {'earlier answer': 1})

    # ------------------------------------------------------------------ noise
    def test_noise_keeps_the_last_sensible_results_and_asks(self):
        for noise in ('jdjdjdk', 'sorry wrong chat', 'ok', '😭😭😭', 'hhhhhhh', 'ignore that'):
            self.calls.clear()
            hits, info = self.a.turn_hits(self.convo('how do i purify water', 'Boil it.', noise))
            self.assertNotIn(noise, ' '.join(self.calls), noise)
            self.assertEqual(self.keys(hits), self.keys(CANNED['how do i purify water']), noise)
            self.assertEqual((info['route'], info['buttons'], info['still']), ('noise', True, 'how do i purify water'), noise)

    def test_noise_never_becomes_the_earlier_message(self):
        hits, info = self.a.turn_hits(self.convo('my son is choking', 'Back blows.', 'sorry wrong chat', 'Okay.', "he's turning blue"))
        self.assertEqual(self.calls[-1], "my son is choking he's turning blue")
        self.assertEqual(info['still'], 'my son is choking')
        self.assertEqual(self.a.earlier_question(self.convo('my son is choking', '', 'jdjdjdk', '', 'x')), 'my son is choking')
        self.assertTrue(info['buttons'])        # its own search found 1 page

    def test_sensible_messages_are_not_noise(self):
        for msg in ("no no the smoke he cant breathe", 'what do i not do', 'it wont stop bleeding', "he's shivering",
                    '¿y si le sale una ampolla?', 'mi hijo se quemó', 'cpr'):
            self.assertFalse(self.a.is_noise(msg), msg)

    def test_without_the_library_words_it_goes_by_how_words_look(self):
        with mock.patch.dict(self.a._VOCAB, words=set()):
            for msg in ('jdjdjdk', 'asdfgh', 'kkkkk', 'jfjfjfjf'):
                self.assertTrue(self.a.is_noise(msg), msg)
            self.assertFalse(self.a.is_noise('the kitchen is on fire'))

    # ------------------------------------------------------------------ correct
    def test_correction_drops_the_pages_already_shown(self):
        hits, info = self.a.turn_hits(self.convo('burned my hand lighting the fire', 'Cool it (Water Book, p. 1).',
                                                 "no no i mean the smoke, he can't breathe"))
        self.assertEqual(info['route'], 'correct')
        self.assertIn("the smoke, he can't breathe", self.calls)          # correction words stripped
        # shown: the cited page and the earlier message's own pages (burn 1, firemake 2, blister 3); they go last
        self.assertEqual(self.keys(hits), [('smokeinh', 1), ('cpr', 4), ('co', 5), ('firemake', 2), ('burn', 1)])
        self.assertNotIn(('water', 1), self.keys(hits))                    # nothing carried

    # ------------------------------------------------------------------ danger
    def test_new_danger_sign_is_a_new_emergency(self):
        hits, info = self.a.turn_hits(self.convo('how do i purify water', 'Boil it (Water Book, p. 2).', 'THE KITCHEN IS ON FIRE'))
        self.assertEqual(info['route'], 'danger')
        self.assertEqual(self.keys(hits)[:5], self.keys(CANNED['THE KITCHEN IS ON FIRE'])[:5])
        self.assertNotIn(('water', 2), self.keys(hits))                    # the cited water page is not carried
        self.assertEqual(self.keys(hits)[5:], [('water', 1), ('stove', 7), ('kids', 6)])

    def test_a_danger_sign_already_there_is_a_follow_up(self):
        _, info = self.a.turn_hits(self.convo('my son is choking', '', 'he is still choking'))
        self.assertEqual(info['route'], 'follow')

    def test_buttons_and_a_button_label(self):
        info = {'still': 'how do i purify water', 'buttons': True}
        choices = self.a.suggest_choices(info)
        self.assertEqual(choices[0], {'label': 'Still about: how do i purify water', 'text': 'Still about: how do i purify water'})
        self.assertEqual([c['label'] for c in choices[1:]], ['Not breathing', 'Heavy bleeding', 'Burn', 'Poison', 'Fire',
                                                              'Something else'])
        self.assertEqual(choices[-1]['text'], '')
        _, info = self.a.turn_hits(self.convo('how do i purify water', '', 'Burn'))
        self.assertEqual(info['route'], 'danger')                            # a danger button is a new emergency
        self.calls.clear()
        hits, info = self.a.turn_hits(self.convo('how do i purify water', '', 'ok', '', choices[0]['text']))
        self.assertEqual(self.calls[0], 'how do i purify water')            # "Still about:" is not searched for

    # ------------------------------------------------------------------ English search words
    def test_english_words_replace_the_question(self):
        hits, _ = self.a.turn_hits(self.convo('hervir agua'), english='boil water')
        self.assertEqual((self.calls, self.keys(hits)), (['boil water'], [('boil', 3), ('water', 1)]))
        self.calls.clear()
        self.a.turn_hits(self.convo('hervir agua'), english='no results here')
        self.assertEqual(self.calls, ['no results here', 'hervir agua'])    # nothing in English: the question itself

    def test_english_follow_up_joins_the_earlier_english_words(self):
        with mock.patch.dict(self.a._ENGLISH_OF, {'hervir agua': 'boil water'}):
            hits, info = self.a.turn_hits(self.convo('hervir agua', '', '¿y de noche?'), english='dark')
        self.assertEqual(info['route'], 'follow')
        self.assertEqual(self.calls, ['dark', '¿y de noche?', 'boil water dark'])
        self.assertEqual(self.keys(hits), [('night', 1)])


if __name__ == '__main__':
    unittest.main()
