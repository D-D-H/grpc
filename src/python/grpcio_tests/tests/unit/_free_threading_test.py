# Copyright 2026 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Smoke tests for running grpcio on free-threaded (PEP 703) CPython.

See ``doc/python/free_threading.md`` for the overall design. These tests are
Phase-1 smoke tests only; a full thread-safety audit and stress test suite
lives in follow-up work (Phase 2).

The tests are skipped automatically on any interpreter that still runs with the
GIL, which includes every regular CPython build and PyPy. They only execute on
the free-threaded CPython 3.14+ build (``python3.14t``).
"""

import concurrent.futures
import logging
import sys
import threading
import unittest

import grpc


def _is_free_threaded_python():
    """Return True iff we are running under a free-threaded (no-GIL) CPython.

    CPython 3.13 introduced ``sys._is_gil_enabled()``; on any older or non-
    CPython interpreter we conservatively report False.
    """
    is_gil_enabled = getattr(sys, "_is_gil_enabled", None)
    if is_gil_enabled is None:
        return False
    return not is_gil_enabled()


_SKIP_REASON = (
    "This test only runs on a free-threaded (PEP 703) CPython build "
    "(e.g. python3.14t). Install such an interpreter and re-run to exercise "
    "it."
)


@unittest.skipUnless(_is_free_threaded_python(), _SKIP_REASON)
class FreeThreadingSmokeTest(unittest.TestCase):
    """Verifies that importing grpc on 3.14t does not re-enable the GIL."""

    def test_gil_remains_disabled_after_import_grpc(self):
        # ``import grpc`` has already happened at module load time; importing
        # it a second time is cheap and makes the intent explicit.
        import grpc  # noqa: F401

        self.assertFalse(
            sys._is_gil_enabled(),
            msg=(
                "Importing grpc caused CPython to re-enable the GIL. This "
                "most likely means a C extension module in the grpc import "
                "graph is missing the Py_mod_gil = Py_MOD_GIL_NOT_USED slot."
            ),
        )

    def test_cygrpc_import_does_not_reenable_gil(self):
        from grpc._cython import cygrpc  # noqa: F401

        self.assertFalse(sys._is_gil_enabled())


def _invoke_channel_ready(address):
    channel = grpc.insecure_channel(address)
    try:
        # We don't actually need the server to answer; we only want to exercise
        # channel creation, state-watch, and teardown from many threads at the
        # same time to shake out obvious registry-level races.
        try:
            grpc.channel_ready_future(channel).result(timeout=0.1)
        except grpc.FutureTimeoutError:
            pass
    finally:
        channel.close()


@unittest.skipUnless(_is_free_threaded_python(), _SKIP_REASON)
class FreeThreadingChannelStressTest(unittest.TestCase):
    """Minimal concurrent channel-create/destroy smoke test.

    This is intentionally lightweight (Phase 1). A full stress suite that
    spins up a real server and performs concurrent unary/streaming/aio RPCs
    is tracked by Phase 2 in ``doc/python/free_threading.md``.
    """

    _NUM_THREADS = 8
    _ITERATIONS_PER_THREAD = 4

    def test_concurrent_channel_lifecycle(self):
        # Use a clearly-unreachable address so the call never actually
        # connects. We only care that the library survives concurrent
        # create/destroy without crashing or corrupting internal state.
        address = "localhost:1"

        errors = []
        errors_lock = threading.Lock()

        def worker():
            try:
                for _ in range(self._ITERATIONS_PER_THREAD):
                    _invoke_channel_ready(address)
            except Exception as exc:  # pylint: disable=broad-except
                with errors_lock:
                    errors.append(exc)

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self._NUM_THREADS
        ) as executor:
            futures = [
                executor.submit(worker) for _ in range(self._NUM_THREADS)
            ]
            for future in concurrent.futures.as_completed(futures):
                future.result()

        self.assertEqual(
            errors,
            [],
            msg="Concurrent channel lifecycle on free-threaded CPython "
            "raised unexpected exceptions: {!r}".format(errors),
        )
        self.assertFalse(sys._is_gil_enabled())


if __name__ == "__main__":
    logging.basicConfig()
    unittest.main(verbosity=2)
