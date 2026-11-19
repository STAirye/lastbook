"""Body-read cancellation on held TLS responses and healthy slow responses."""
import os
from pathlib import Path
import ssl
import threading
from unittest import mock

from app.tests import test_setup as fixture
from engine.setup import download


class CancellableBodyTests(fixture.Base):
    def setUp(self):
        super().setUp()
        self.big = os.urandom(3 * fixture.MiB + 4321)
        self.files.data['big.bin'] = self.big

    dl = fixture.ParallelDownloads.dl
    ranges = fixture.ParallelDownloads.ranges
    outcome = staticmethod(fixture.ParallelDownloads.outcome)
    download_threads = staticmethod(fixture.ParallelDownloads.download_threads)
    snapshot = staticmethod(fixture.ParallelDownloads.snapshot)

    def test_connection_close_body_pause(self):
        states = []
        original = download._cancellable_body

        def observe(conn, response, stopping, timeout):
            states.append((conn.sock is None, response.will_close))
            return original(conn, response, stopping, timeout)

        with mock.patch.object(fixture.Handler, 'protocol_version', 'HTTP/1.0'):
            with mock.patch.object(download, '_cancellable_body', observe):
                fixture.ParallelDownloads.test_pause_and_resume(self)
        self.assertIn((True, True), states, 'exercise the response-owned socket, not only keep-alive')

    def test_slow_response_does_not_restart_or_spend_retry_budget(self):
        self.files.pace = .06
        with fixture.pieces():
            result = self.dl().run()
        self.assertEqual(Path(result).read_bytes(), self.big)
        self.assertEqual(len(self.ranges()), 13, 'healthy delayed TLS data must not cause request retries')
        self.assertEqual(self.download_threads(), [])

    def test_want_read_keeps_original_deadline(self):
        class Socket:
            def setblocking(self, value):
                self.blocking = value

            def recv_into(self, *args):
                raise ssl.SSLWantReadError()

        sock = Socket()
        conn = mock.Mock(sock=sock)
        response = mock.Mock()
        stopping = threading.Event()
        download._cancellable_body(conn, response, stopping, 30)
        with mock.patch.object(download.time, 'monotonic', side_effect=[100, 100, 129.95, 130]):
            with mock.patch.object(download.select, 'select', return_value=([], [], [])) as wait:
                with self.assertRaises(TimeoutError):
                    sock.recv_into(bytearray(1))
        self.assertEqual(wait.call_count, 2)
        self.assertAlmostEqual(wait.call_args.args[-1], .05)

    def test_stop_is_checked_before_reading(self):
        class Socket:
            def setblocking(self, value):
                pass

            def recv_into(self, *args):
                raise AssertionError('stop must be checked first')

        sock = Socket()
        conn = mock.Mock(sock=sock)
        stopping = threading.Event()
        download._cancellable_body(conn, mock.Mock(), stopping, 30)
        stopping.set()
        with self.assertRaises(download.Stopped):
            sock.recv_into(bytearray(1))
