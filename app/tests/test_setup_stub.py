"""The setup stub (app/tests/setup_stub.py) drives the setup screens for previews. Its scenarios must run to their end
without the stub itself failing. No server is started: the Stub class is driven directly on a moved clock. Never packaged."""
import sys, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import setup_stub  # noqa: E402


class BusyScenario(unittest.TestCase):
    def test_busy_waits_with_a_countdown_then_finishes(self):
        """busy: past 40% the item shows retry_in_s with no rate for 2 minutes, then the download goes on and finishes."""
        now = [1000.0]
        with mock.patch.object(setup_stub.time, 'time', lambda: now[0]):
            stub = setup_stub.Stub('busy')
            stub.start({'pack': 'small', 'ai': False})
            seen = []
            for _ in range(400):
                now[0] += 1
                stub.tick()                       # the crossing of 40% used to raise KeyError('busy') here
                it = stub.public()['items'][0]
                if 'retry_in_s' in it:
                    seen.append((it['retry_in_s'], it['rate_bps'], it['eta_s']))
                if stub.public()['state'] == 'done':
                    break
        self.assertTrue(seen, 'no countdown shown')
        self.assertTrue(all(rate == 0 and eta is None for _, rate, eta in seen), seen[:3])
        self.assertLessEqual(seen[0][0], 120)
        self.assertEqual(stub.public()['state'], 'done')
        self.assertIsNone(stub.public()['error'])

    def test_server_scenario_still_fails_once(self):
        """server: the generic failure path is unchanged for the other downloading faults."""
        now = [1000.0]
        with mock.patch.object(setup_stub.time, 'time', lambda: now[0]):
            stub = setup_stub.Stub('server')
            stub.start({'pack': 'small', 'ai': False})
            for _ in range(20):
                now[0] += 1
                stub.tick()
        self.assertEqual(stub.public()['state'], 'failed')
        self.assertEqual(stub.public()['error']['code'], 'server')


if __name__ == '__main__':
    unittest.main()
