#!/usr/bin/env python3
"""fork: how likely a search's first page is right (engine/confidence.py), and what the chat does with it (assistant).

  python -B -m unittest app.tests.test_confidence [-v]

No library and no model: the library's words are given, hybrid() is a stand-in that fills the trace as the real one does,
and chat() runs with a stand-in model round. Checked: the signals and the probability (plain numbers, strong searches
above weak ones), the thresholds and their environment overrides, the switch, turn_hits' confidence (the better of its
own and the joined search; noise keeps the earlier one's; none from a stand-in without a trace), and the chat: sure
answers as before, unsure offers buttons, very unsure asks for more words without the model and without the pages,
except when the question may be urgent, when the pages are given too, and when it names a body sign ("he has no puls",
"mybbyisntbreathing"), when the model answers from the pages, with buttons. Everyday questions (not urgent): buttons only
below the much lower everyday cut, the same buttons drawn smaller (style 'compact'), and the request to say more never
above that cut. Never packaged."""
import os, sys, unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT)]

from engine import confidence  # noqa: E402

V = {'the': 100000, 'water': 3000, 'purify': 200, 'boil': 900, 'chlorine': 400, 'tomato': 150, 'plants': 2000,
     'cellar': 60, 'root': 800, 'build': 5000, 'zebra': 5}


def hit(doc, title, excerpt, kind='html', found_by=None):
    return {'doc_id': doc, 'page': 1, 't': None, 'kind': kind, 'title': title, 'excerpt': excerpt,
            'found_by': found_by or {'keyword': 1}}


STRONG = ([hit('w1', 'Purify Water', 'To purify water, boil it for one minute.')] +
          [hit(f'd{i}', f'Book {i}', 'water') for i in range(7)],
          {'groups': [['purify', 'purification'], ['water']], 'strict': 60, 'any_word': False, 'bm25': [-14.0, -12.0, -11.0],
           'semantic': False})
WEAK = ([hit('z1', 'Tools and Their Uses', 'a hammer and a saw')],
        {'groups': [['zebra'], ['cellar'], ['tomato']], 'strict': 0, 'any_word': True, 'bm25': [-1.5], 'semantic': False})


class Signals(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(confidence, '_words', lambda: (V, max(V.values())))
        p.start()
        self.addCleanup(p.stop)
        for k in ('LASTBOOK_CONF', 'LASTBOOK_CONF_BUTTONS', 'LASTBOOK_CONF_UNSURE', 'LASTBOOK_CONF_BUTTONS_EVERYDAY'):
            self.addCleanup(os.environ.pop, k, None)
            os.environ.pop(k, None)

    def test_signals_are_plain_numbers_and_the_models_use_only_them(self):
        f = confidence.features(*STRONG)
        self.assertTrue(all(isinstance(v, float) for v in f.values()), f)
        self.assertEqual((f['cover1'], f['all1'], f['title1']), (1.0, 1.0, 1.0))
        hy = confidence.features(STRONG[0], dict(STRONG[1], semantic=True, cos=[0.8, 0.75, 0.7], kw_keys=[('w1', 1, None)],
                                                 sem_keys=[['w1', 1, None]]))
        self.assertEqual(hy['overlap'], 1 / 8)                       # keys from JSON (lists) and from hybrid (tuples) alike
        for name, model in confidence.MODELS.items():
            self.assertTrue(all(isinstance(w, float) for w in model.values()), name)
            self.assertLessEqual(set(model) - {'bias'}, set(hy), name)

    def test_a_strong_search_is_surer_than_a_weak_one(self):
        strong, weak = confidence.estimate(*STRONG), confidence.estimate(*WEAK)
        self.assertEqual((strong['mode'], weak['mode']), ('keyword', 'keyword'))
        self.assertGreater(strong['p'], confidence.BUTTONS)
        self.assertLess(weak['p'], confidence.UNSURE)
        self.assertEqual((strong['level'], weak['level']), ('sure', 'unsure'))
        self.assertEqual(confidence.estimate([], {'groups': [], 'semantic': False})['level'], 'unsure')   # nothing found

    def test_hybrid_uses_its_own_coefficients(self):
        tr = dict(STRONG[1], semantic=True, cos=[0.86] + [0.8] * 7, kw_keys=[('w1', 1, None)], sem_keys=[('w1', 1, None)])
        est = confidence.estimate(STRONG[0], tr)
        self.assertEqual(est['mode'], 'hybrid')
        self.assertAlmostEqual(est['p'], confidence.probability(confidence.features(STRONG[0], tr), confidence.MODELS['hybrid']), 3)

    def test_thresholds_from_the_environment(self):
        self.assertEqual(confidence.thresholds(), (0.6, 0.25))
        self.assertEqual((confidence.BUTTONS, confidence.UNSURE), (0.6, 0.25))
        os.environ.update(LASTBOOK_CONF_BUTTONS='0.75', LASTBOOK_CONF_UNSURE='0.1')
        self.assertEqual(confidence.thresholds(), (0.75, 0.1))
        os.environ.update(LASTBOOK_CONF_BUTTONS='lots', LASTBOOK_CONF_UNSURE='7')    # not a share: the default
        self.assertEqual(confidence.thresholds(), (0.6, 0.25))
        os.environ['LASTBOOK_CONF_UNSURE'] = '0'
        self.assertEqual(confidence.estimate(*WEAK)['level'], 'buttons')      # 0: never "please say more"

    def test_between_the_old_and_new_buttons_cut_is_sure(self):
        with mock.patch.object(confidence, 'probability', lambda f, m: 0.7):
            self.assertEqual(confidence.estimate(*STRONG)['level'], 'sure')     # 0.60 by default (was 0.75)
            os.environ['LASTBOOK_CONF_BUTTONS'] = '0.75'
            self.assertEqual(confidence.estimate(*STRONG)['level'], 'buttons')
        with mock.patch.object(confidence, 'probability', lambda f, m: 0.59):
            os.environ.pop('LASTBOOK_CONF_BUTTONS')
            self.assertEqual(confidence.estimate(*STRONG)['level'], 'buttons')

    def test_everyday_cut_and_its_override(self):
        self.assertEqual((confidence.EVERYDAY_BUTTONS, confidence.everyday_cut()), (0.3, 0.3))
        self.assertLess(confidence.EVERYDAY_BUTTONS, confidence.BUTTONS)
        self.assertEqual([confidence.everyday_level(p) for p in (0.1, 0.24, 0.25, 0.29, 0.3, 0.5, 0.59, 0.9)],
                         ['unsure', 'unsure', 'buttons', 'buttons', 'sure', 'sure', 'sure', 'sure'])
        os.environ['LASTBOOK_CONF_BUTTONS_EVERYDAY'] = '0.15'
        self.assertEqual(confidence.everyday_cut(), 0.15)
        # below the unsure cut: the request to say more only where there are buttons too, never above them
        self.assertEqual([confidence.everyday_level(p) for p in (0.1, 0.15, 0.2)], ['unsure', 'sure', 'sure'])
        os.environ['LASTBOOK_CONF_BUTTONS_EVERYDAY'] = '0.6'
        self.assertEqual([confidence.everyday_level(p) for p in (0.2, 0.5)], ['unsure', 'buttons'])
        os.environ['LASTBOOK_CONF_BUTTONS_EVERYDAY'] = 'many'
        self.assertEqual(confidence.everyday_cut(), 0.3)                       # not a share: the default
        os.environ['LASTBOOK_CONF_BUTTONS_EVERYDAY'] = '0'
        self.assertEqual(confidence.everyday_level(0.01), 'sure')              # 0: never buttons on an everyday question
        self.assertEqual(confidence.thresholds(), (0.6, 0.25))                 # the urgent cuts are untouched

    def test_unknown_words(self):
        self.addCleanup(os.environ.pop, 'LASTBOOK_CONF_UNKNOWN', None)
        for q in ('jdjdk', 'asdfgh', 'heschuokinghelkp', 'zebra jdjdk qqqq', 'help', 'how do i', 'ok', "he's"):
            self.assertTrue(confidence.unknown_words(q), q)      # most content words unknown, or no content word
        for q in ('how do i purify water', 'purify jdjdk', 'boil the water please', 'EU2200i wont start', 'hervir agua',
                  '', None):
            self.assertFalse(confidence.unknown_words(q), q)     # half known is not most; digits; another language
        os.environ['LASTBOOK_CONF_UNKNOWN'] = '0'
        self.assertFalse(confidence.unknown_words('jdjdk'))
        os.environ.pop('LASTBOOK_CONF_UNKNOWN')
        with mock.patch.object(confidence, '_words', lambda: ({}, 0)):
            self.assertFalse(confidence.unknown_words('jdjdk'))   # no library words: nothing to tell by

    def test_unknown_words_make_the_search_unsure_whatever_p(self):
        tr = dict(STRONG[1], q='jdjdk')                           # a strong-looking search for keyboard mash
        est = confidence.estimate(STRONG[0], tr)
        self.assertGreater(est['p_fitted'], confidence.BUTTONS)
        self.assertTrue(est['unknown_words'])
        self.assertEqual(est['level'], 'unsure')
        self.assertLess(est['p'], min(confidence.UNSURE, confidence.everyday_cut()))
        self.assertEqual(confidence.everyday_level(est['p']), 'unsure')        # an everyday question too
        sure = confidence.estimate(STRONG[0], dict(STRONG[1], q='how do i purify water'))
        self.assertEqual((sure['level'], 'unknown_words' in sure), ('sure', False))
        self.assertEqual(confidence.estimate(*STRONG)['level'], 'sure')        # no question in the trace: as before
        os.environ['LASTBOOK_CONF_UNSURE'] = '0'                               # never "please say more": buttons only
        self.assertEqual(confidence.estimate(STRONG[0], tr)['level'], 'buttons')

    def test_urgent_words(self):
        for q in ("my son isn't breathing", 'she cant breath wheezing bad', 'fell off the roof cant move legs',
                  "her face is drooping can't speak", 'chainsaw cut his leg', 'the outlet is sparking and smoking',
                  'i do not want to live anymore', 'water broke i can see the head'):
            self.assertTrue(confidence.urgent(q), q)
        for q in ('how to build a root cellar', 'how do i purify water', 'best way to store rice'):
            self.assertFalse(confidence.urgent(q), q)


class BodySigns(unittest.TestCase):
    """fork: body signs (confidence.body_signs): named exactly, one or two slips away on a word the library has on fewer
    than BODY_COMMON pages, or inside a glued run; they count as urgent. LASTBOOK_BODY_SIGNS=0 turns them off."""
    BV = dict(V, puls=24, pulse=1577, pulses=560, bloom=259, breeding=581, chore=16, chose=359, bleating=12, fit=900)

    def setUp(self):
        p = mock.patch.object(confidence, '_words', lambda: (self.BV, max(self.BV.values())))
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(os.environ.pop, 'LASTBOOK_BODY_SIGNS', None)
        os.environ.pop('LASTBOOK_BODY_SIGNS', None)

    def test_named_and_misspelled(self):
        for q, want in [('he has no puls what do i do', {'pulse'}), ('he has no pulse', {'pulse'}),
                        ('mybbyisntbreathing', {'breathing'}), ('hescolapsednotbreathin', {'breathing', 'unconscious'}),
                        ('his lips are blue', {'blue'}), ('mybabyisblue', {'blue'}), ('she is unconsious', {'unconscious'}),
                        ('he passed out', {'unconscious'}), ('bledding from the leg', {'bleeding'}),
                        ('chokin on food', {'choking'}), ('she is having a fit', {'seizure'}),
                        ('chest hurts and he is sweating', {'chest pain'}), ('the baby is limp and not moving', {'not moving'}),
                        ('the child is cold and wet', {'cold and clammy'}), ('no heartbeet', {'pulse'})]:
            self.assertEqual(confidence.body_signs(q), want, q)
            self.assertTrue(confidence.urgent(q), q)
        self.assertEqual(confidence.body_signs('', None, 'his lips are blue'), {'blue'})     # any of the texts

    def test_words_of_their_own(self):
        for q in ('how to cook pulses', 'how to make flowers bloom', 'chicken breeding', 'household chore list',
                  'she chose the red one', 'how to fit a pipe', 'the sky is blue', 'how to build a root cellar',
                  'plus size', 'pause'):
            self.assertEqual(confidence.body_signs(q), set(), q)
        self.assertFalse(confidence.urgent('how to build a root cellar'))

    def test_switch(self):
        self.assertTrue(confidence.urgent('he has no puls'))
        os.environ['LASTBOOK_BODY_SIGNS'] = '0'
        self.assertEqual(confidence.body_signs('he has no puls', 'mybbyisntbreathing'), set())
        self.assertFalse(confidence.urgent('he has no puls'))          # URGENT has pulse, not "puls"
        self.assertTrue(confidence.urgent('he has no pulse'))


class TurnHitsConfidence(unittest.TestCase):
    """assistant.turn_hits with a hybrid stand-in that fills its trace."""

    def setUp(self):
        before = set(sys.modules)
        import assistant
        self.addCleanup(lambda: [sys.modules.pop(n, None) for n in set(sys.modules) - before])
        self.a = assistant
        self.canned = {'how do i purify water': STRONG, 'zebra cellar tomato': WEAK,
                       'how do i purify water zebra cellar tomato': WEAK}

        def hybrid(q, k=8, kind='any', doc=None, trace=None):
            hits, tr = self.canned.get(q, ([], {'groups': [], 'semantic': False}))
            if trace is not None:
                trace.update(tr)
            return [dict(h) for h in hits][:k]
        S = mock.Mock(catalog=lambda: {'by_id': {}})
        for obj, name, value in ((assistant, 'hybrid', hybrid), (assistant, 'S', S),
                                 (confidence, '_words', lambda: (V, max(V.values())))):
            p = mock.patch.object(obj, name, value)
            p.start()
            self.addCleanup(p.stop)
        p = mock.patch.dict(assistant._VOCAB, words={'water', 'purify', 'zebra', 'cellar', 'tomato'})
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(os.environ.pop, 'LASTBOOK_CONF', None)

    def convo(self, *turns):
        return [{'role': 'user' if n % 2 == 0 else 'assistant', 'content': t} for n, t in enumerate(turns)]

    def test_one_message(self):
        _, info = self.a.turn_hits(self.convo('how do i purify water'))
        self.assertEqual(info['confidence']['level'], 'sure')
        self.assertFalse(info['danger'])
        _, info = self.a.turn_hits(self.convo('zebra cellar tomato'))
        self.assertEqual(info['confidence']['level'], 'unsure')

    def test_the_better_of_own_and_joined(self):
        _, info = self.a.turn_hits(self.convo('zebra cellar tomato', '', 'how do i purify water'))
        self.assertEqual(info['route'], 'follow')
        self.assertEqual(info['confidence']['level'], 'sure')               # own search strong, joined weak

    def test_unknown_words_in_a_first_message(self):
        self.canned['qqzx wwvb'] = (STRONG[0], dict(STRONG[1], q='qqzx wwvb'))    # hits that look right, for mash
        _, info = self.a.turn_hits(self.convo('qqzx wwvb'))
        self.assertEqual(info['route'], 'first')
        self.assertEqual(info['confidence']['level'], 'unsure')             # the chat asks for more words, with buttons
        self.assertTrue(info['confidence']['unknown_words'])

    def test_noise_keeps_the_earlier_message_confidence(self):
        _, info = self.a.turn_hits(self.convo('how do i purify water', '', 'jdjdjdk'))
        self.assertEqual((info['route'], info['confidence']['level']), ('noise', 'sure'))

    def test_off_and_without_a_trace(self):
        os.environ['LASTBOOK_CONF'] = '0'
        self.assertIsNone(self.a.turn_hits(self.convo('how do i purify water'))[1]['confidence'])
        os.environ.pop('LASTBOOK_CONF')
        with mock.patch.object(self.a, 'hybrid', lambda q, k=8, kind='any', doc=None: list(STRONG[0])):
            self.assertIsNone(self.a.turn_hits(self.convo('how do i purify water'))[1]['confidence'])

    def test_body_signs(self):
        """fork: "he has no puls" (the library's word, not corrected) and a glued "mybbyisntbreathing": urgent, the body
        sign in info['body'], and chat_level answers with buttons, never only "help me help you"."""
        self.addCleanup(os.environ.pop, 'LASTBOOK_BODY_SIGNS', None)
        for q, sign in (('he has no puls what do i do', 'pulse'), ('mybbyisntbreathing', 'breathing')):
            self.canned[q] = WEAK
            _, info = self.a.turn_hits(self.convo(q))
            self.assertEqual((info['route'], info['danger'], info['body']), ('first', True, [sign]), q)
            self.assertEqual(info['confidence']['level'], 'unsure', q)
            level, conf, everyday = self.a.chat_level(info)
            self.assertEqual((level, conf['body'], everyday), ('buttons', True, False), q)
        _, info = self.a.turn_hits(self.convo('how do i purify water', '', 'mybbyisntbreathing'))
        self.assertNotEqual(info['route'], 'noise')                         # a body sign is never noise
        self.assertFalse(self.a.is_noise('mybbyisntbreathing'))
        self.assertTrue(self.a.is_noise('jdjdjdk'))
        os.environ['LASTBOOK_BODY_SIGNS'] = '0'
        _, info = self.a.turn_hits(self.convo('he has no puls what do i do'))
        self.assertEqual((info['danger'], info['body']), (False, []))
        self.assertEqual(self.a.chat_level(info)[0], 'unsure')             # as before: the bare "help me help you"

    def test_danger_covers_the_earlier_message(self):
        _, info = self.a.turn_hits(self.convo('he is bleeding a lot', '', 'what do i not do'))
        self.assertTrue(info['danger'])
        self.assertTrue(self.a.is_danger('Poison'))                          # a danger button


class ChatConfidence(unittest.TestCase):
    """assistant.chat with turn_hits and the model round stood in for: which events the browser gets."""

    def setUp(self):
        before = set(sys.modules)
        import assistant
        self.addCleanup(lambda: [sys.modules.pop(n, None) for n in set(sys.modules) - before])
        self.a = assistant
        self.rounds = []
        cat = {'by_id': {'w1': {'id': 'w1', 'kind': 'html', 'title': 'Purify Water'}}}
        S = mock.Mock(catalog=lambda: cat)

        def model_round(msgs, tools, cancelled, wrote, set_state):
            self.rounds.append(msgs)
            wrote('Boil it [S1].')
            return 'Boil it [S1].', {}
        for name, value in (('S', S), ('LOCAL', None), ('_http_round', model_round)):
            p = mock.patch.object(assistant, name, value)
            p.start()
            self.addCleanup(p.stop)
        self.hits = [hit('w1', 'Purify Water', 'boil it')]

    def run_chat(self, question, level, route='first', danger=False, p=None, still='', body=()):
        p = {'sure': 0.9, 'buttons': 0.5, 'unsure': 0.1}[level] if p is None else p
        info = {'route': route, 'buttons': route == 'noise', 'still': still, 'danger': danger,
                'confidence': {'p': p, 'mode': 'keyword', 'level': level}, 'body': list(body)}
        events = []
        with mock.patch.object(self.a, 'turn_hits', lambda *a, **k: (self.hits, dict(info))):
            self.a.chat([{'role': 'user', 'content': question}], None, events.append, lambda: False)
        return {e['type']: e for e in events}, events

    def test_sure_answers_as_before(self):
        ev, _ = self.run_chat('how do i purify water', 'sure')
        self.assertNotIn('suggest', ev)
        self.assertEqual(len(self.rounds), 1)
        self.assertEqual(ev['done']['answer'], 'Boil it [S1].')

    def test_unsure_offers_buttons_and_answers(self):
        ev, _ = self.run_chat('he is bleeding from the arm', 'buttons', danger=True)      # may be urgent: as before
        self.assertEqual(ev['suggest']['prompt'], self.a.SUGGEST_PROMPT['buttons'])
        self.assertIn('Not breathing', [c['label'] for c in ev['suggest']['choices']])
        self.assertEqual(ev['suggest']['confidence']['level'], 'buttons')
        self.assertNotIn('style', ev['suggest'])                             # the emergency buttons' own look
        self.assertEqual(len(self.rounds), 1)

    def test_urgent_cuts_are_unchanged(self):
        for p, buttons in ((0.59, True), (0.3, True), (0.61, False)):
            self.rounds.clear()
            level = 'buttons' if p < 0.6 else 'sure'
            ev, _ = self.run_chat('he is bleeding from the arm', level, danger=True, p=p)
            self.assertEqual('suggest' in ev, buttons, p)
            self.assertEqual(len(self.rounds), 1)

    def test_everyday_unsure_answers_without_buttons(self):
        ev, _ = self.run_chat('how do i build a goat fence', 'buttons', p=0.5)
        self.assertNotIn('suggest', ev)                                     # 0.5 is under 0.60 but over the everyday cut
        self.assertEqual(len(self.rounds), 1)
        self.assertEqual(ev['done']['answer'], 'Boil it [S1].')

    def test_everyday_very_unsure_gets_the_same_buttons_smaller(self):
        ev, _ = self.run_chat('how do i build a goat fence', 'buttons', p=0.27)
        self.assertEqual(ev['suggest']['style'], 'compact')
        self.assertEqual(ev['suggest']['choices'], self.a.suggest_choices({}))   # the same choices as an urgent question's
        self.assertEqual(ev['suggest']['prompt'], self.a.SUGGEST_PROMPT['buttons'])
        self.assertEqual(ev['suggest']['confidence']['level'], 'buttons')
        self.assertTrue(ev['suggest']['confidence']['everyday'])
        self.assertEqual(len(self.rounds), 1)                               # 0.25-0.30: buttons and the answer

    def test_everyday_cut_from_the_environment(self):
        self.addCleanup(os.environ.pop, 'LASTBOOK_CONF_BUTTONS_EVERYDAY', None)
        os.environ['LASTBOOK_CONF_BUTTONS_EVERYDAY'] = '0.55'
        ev, _ = self.run_chat('how do i build a goat fence', 'buttons', p=0.5)
        self.assertEqual(ev['suggest']['style'], 'compact')
        os.environ['LASTBOOK_CONF_BUTTONS_EVERYDAY'] = '0.2'
        self.rounds.clear()
        ev, _ = self.run_chat('how do i build a goat fence', 'unsure', p=0.22)
        self.assertNotIn('suggest', ev)                                     # no request to say more above the buttons cut
        self.assertNotIn('unsure', ev['done'])
        self.assertEqual(len(self.rounds), 1)

    def test_very_unsure_asks_without_the_model(self):
        ev, events = self.run_chat('zebra cellar tomato', 'unsure')
        self.assertEqual(self.rounds, [])                                   # the model is never asked
        self.assertIn('suggest', ev)
        self.assertEqual(ev['done']['answer'], self.a.UNSURE_TEXT)
        self.assertEqual(ev['suggest']['style'], 'compact')                 # everyday: below both cuts, smaller buttons
        self.assertTrue(ev['done']['unsure'])
        self.assertEqual(ev['done']['sources'], [])                         # no pages offered as the answer's
        self.assertEqual([s['doc_id'] for s in ev['done']['consulted']], ['w1'])
        self.assertLess(events.index(ev['suggest']), events.index(ev['done']))

    def test_very_unsure_but_urgent_gives_the_pages(self):
        ev, _ = self.run_chat('my son neary drownd', 'unsure', danger=True)
        self.assertEqual(self.rounds, [])
        self.assertEqual(ev['done']['answer'], self.a.UNSURE_DANGER)
        self.assertEqual([s['doc_id'] for s in ev['done']['sources']], ['w1'])
        self.assertIn('suggest', ev)
        self.assertNotIn('style', ev['suggest'])

    def test_very_unsure_with_a_body_sign_answers(self):
        """fork: "he has no puls": never only "help me help you" (nor the pages without an answer): the model answers from
        the pages, with the emergency buttons."""
        for danger in (True, False):
            self.rounds.clear()
            ev, events = self.run_chat('he has no puls what do i do', 'unsure', danger=danger, p=0.22, body=['pulse'])
            self.assertEqual(len(self.rounds), 1, danger)
            self.assertEqual(ev['done']['answer'], 'Boil it [S1].')
            self.assertNotIn('unsure', ev['done'])
            self.assertEqual(ev['suggest']['prompt'], self.a.SUGGEST_PROMPT['buttons'])
            self.assertTrue(ev['suggest']['confidence']['body'])
            self.assertLess(events.index(ev['suggest']), events.index(ev['done']))
        ev, _ = self.run_chat('mybbyisntbreathing', 'unsure', danger=True, body=['breathing'])
        self.assertEqual((len(self.rounds), ev['done']['answer']), (2, 'Boil it [S1].'))

    def test_very_unsure_in_a_follow_up_is_only_buttons(self):
        ev, _ = self.run_chat('and at night?', 'unsure', route='follow')
        self.assertEqual(ev['suggest']['prompt'], self.a.SUGGEST_PROMPT['buttons'])
        self.assertEqual(len(self.rounds), 1)

    def test_very_unsure_later_in_a_chat_without_follow_ups_is_only_buttons(self):
        info = {'route': 'first', 'buttons': False, 'still': '', 'danger': False,
                'confidence': {'p': 0.1, 'mode': 'keyword', 'level': 'unsure'}}
        events = []
        msgs = [{'role': 'user', 'content': 'how do i purify water'}, {'role': 'assistant', 'content': 'Boil it.'},
                {'role': 'user', 'content': 'and at night?'}]
        with mock.patch.object(self.a, 'turn_hits', lambda *a, **k: (self.hits, dict(info))):
            self.a.chat(msgs, None, events.append, lambda: False)       # not the person's own Gemma: no follow-up search
        self.assertEqual(len(self.rounds), 1)
        self.assertIn('suggest', [e['type'] for e in events])

    def test_noise_keeps_its_own_buttons(self):
        ev, _ = self.run_chat('jdjdjdk', 'unsure', route='noise', still='how do i purify water')
        self.assertEqual(len(self.rounds), 1)
        self.assertNotIn('unsure', ev['done'])
        self.assertEqual(ev['suggest']['choices'][0]['label'], 'Still about: how do i purify water')

    def test_noise_with_nothing_before_asks(self):
        for level in ('sure', 'unsure'):            # a first message "jdjdk": whatever its own search's confidence
            self.rounds.clear()
            ev, events = self.run_chat('jdjdjdk', level, route='noise')
            self.assertEqual(self.rounds, [])
            self.assertEqual(ev['done']['answer'], self.a.UNSURE_TEXT)
            self.assertTrue(ev['done']['unsure'])
            self.assertEqual(ev['suggest']['prompt'], self.a.SUGGEST_PROMPT['unsure'])
            self.assertLess(events.index(ev['suggest']), events.index(ev['done']))
        ev, _ = self.run_chat('fire jdjdk', 'sure', route='noise', danger=True)
        self.assertEqual(ev['done']['answer'], self.a.UNSURE_DANGER)        # may be urgent: the pages all the same
        self.assertEqual([s['doc_id'] for s in ev['done']['sources']], ['w1'])

    def test_glued_first_message_as_the_chat_sees_it(self):
        ev, _ = self.run_chat('heschuokinghelkp', 'unsure', danger=False)    # split off and not split: unknown words
        self.assertEqual(self.rounds, [])
        self.assertEqual(ev['done']['answer'], self.a.UNSURE_TEXT)
        self.assertIn('suggest', ev)


if __name__ == '__main__':
    unittest.main()
