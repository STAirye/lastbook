"""Small loopback regression fixtures for #122-derived disk-write safeguards."""
import builtins
import errno
import os
import threading
from pathlib import Path
from unittest import mock

from app.tests import test_setup as fixture
from engine.setup import download


class DiskFaults(fixture.Base):
    def setUp(self):
        super().setUp()
        self.big = os.urandom(3 * fixture.MiB + 4321)
        self.files.data['big.bin'] = self.big

    def dl(self, connections):
        return download.Download(f'{self.base}/big.bin', self.tmp / 'dl' / 'big.bin', len(self.big),
                                 fixture.sha(self.big), download.Control(), allowed=fixture.ALLOWED,
                                 context=self.ctx, connections=connections)

    def fault(self, transfer, kind):
        real_open = builtins.open
        lock = threading.Lock()
        state = {'done': False}

        class Wrapped:
            def __init__(self, stream, buffering):
                self.stream = stream
                self.buffering = buffering

            def __getattr__(self, name):
                return getattr(self.stream, name)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return self.stream.__exit__(*args)

            def write(self, data):
                if self.buffering != 0:
                    raise AssertionError("download payload writer must be unbuffered")
                with lock:
                    if not state['done']:
                        state['done'] = True
                        count = max(1, len(data) // 2)
                        self.stream.write(data[:count])
                        self.stream.flush()
                        if kind == 'half_error':
                            raise OSError(errno.EINVAL, 'injected partial write')
                        if kind == 'full':
                            raise OSError(errno.ENOSPC, 'injected disk full')
                        return count
                return self.stream.write(data)

        def opened(path, mode='r', *args, **kwargs):
            stream = real_open(path, mode, *args, **kwargs)
            if str(path) == str(transfer.part) and '+' in mode:
                return Wrapped(stream, kwargs.get('buffering'))
            return stream

        return mock.patch.object(download, 'open', opened, create=True)

    def run_fault(self, kind, parallel):
        transfer = self.dl(connections=4 if parallel else 1)
        with fixture.pieces(), fixture.fast_backoff(), self.fault(transfer, kind):
            result = transfer.run()
        self.assertEqual(Path(result).read_bytes(), self.big)

    def test_serial_short_write(self):
        self.run_fault('short', False)

    def test_parallel_short_write(self):
        self.run_fault('short', True)

    def test_serial_partial_error(self):
        self.run_fault('half_error', False)

    def test_parallel_partial_error(self):
        self.run_fault('half_error', True)

    def test_disk_full_resume(self):
        transfer = self.dl(connections=1)
        with fixture.pieces(), fixture.fast_backoff(), self.fault(transfer, 'full'):
            with self.assertRaises(download.Failed) as caught:
                transfer.run()
        self.assertEqual(caught.exception.code, 'no_space')
        self.assertTrue(Path(transfer.part).exists())
        with fixture.pieces(), fixture.fast_backoff():
            result = self.dl(connections=1).run()
        self.assertEqual(Path(result).read_bytes(), self.big)

    def test_zero_write_fails(self):
        stream = mock.Mock()
        stream.write.return_value = 0
        with self.assertRaises(OSError) as caught:
            download._write_all(stream, b'abc')
        self.assertEqual(caught.exception.errno, errno.EIO)
        self.assertEqual(stream.write.call_count, 1)
