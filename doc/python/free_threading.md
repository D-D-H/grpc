# Free-threaded (PEP 703) CPython support in gRPC Python

> **Status:** Experimental. Do not rely on it for production workloads. See
> [Rollout](#rollout) below for what is and is not supported in each phase.

## Background

[PEP 703](https://peps.python.org/pep-0703/) introduces a build of CPython
that runs without the Global Interpreter Lock (GIL). This "free-threaded"
build lets pure-Python code execute concurrently on multiple OS threads
within a single interpreter. Starting with CPython 3.13 the free-threaded
interpreter ships alongside the standard one and is recognizable by the
`t` ABI suffix — e.g. `python3.14` (GIL enabled) vs `python3.14t`
(GIL disabled). CPython 3.14 is the first release where the free-threaded
build is non-experimental upstream.

A free-threaded interpreter only truly runs without the GIL when every
C extension module imported into the process has explicitly declared
itself compatible. If any extension has not, CPython 3.14t re-enables the
GIL at import time and prints a `RuntimeWarning`. The extension-module
opt-in is done via the `Py_mod_gil = Py_MOD_GIL_NOT_USED` multi-phase
init slot (see `PEP 703 §"C API"`). This document describes how gRPC
Python opts in, and what thread-safety guarantees the Python API makes
on a free-threaded interpreter.

## Support status matrix

| Package                  | Interpreter    | Status       | Notes                                        |
| ------------------------ | -------------- | ------------ | -------------------------------------------- |
| `grpcio`                 | `python3.14t`  | Experimental | Phase 1 opt-in shipping; see [Rollout](#rollout). |
| `grpcio-tools`           | `python3.14t`  | Experimental | Phase 1 opt-in shipping.                     |
| `grpcio-status`          | `python3.14t`  | Experimental | Pure-Python; inherits `grpcio` support.      |
| `grpcio-reflection`      | `python3.14t`  | Experimental | Pure-Python; inherits `grpcio` support.      |
| `grpcio-health-checking` | `python3.14t`  | Experimental | Pure-Python; inherits `grpcio` support.      |
| `grpcio-testing`         | `python3.14t`  | Experimental | Pure-Python; inherits `grpcio` support.      |
| `grpcio-channelz`        | `python3.14t`  | Experimental | Pure-Python; inherits `grpcio` support.      |
| `grpcio-admin`           | `python3.14t`  | Experimental | Pure-Python; inherits `grpcio` support.      |
| `grpcio-csds`            | `python3.14t`  | Experimental | Pure-Python; inherits `grpcio` support.      |
| `grpcio-csm-observability` | `python3.14t` | Experimental | Pure-Python; inherits `grpcio` support.     |
| `grpcio-observability`   | `python3.14t`  | Experimental | Pure-Python; inherits `grpcio` support.      |
| All packages             | `python3.14`   | Supported    | Standard GIL-enabled build; unchanged.       |

Only `grpcio` and `grpcio-tools` contain C/Cython extension modules, so
they are the only packages whose build configuration needs adjustments;
every other package is pure Python and works as-is once `grpcio` itself
works.

Phase 1 does not yet publish pre-built `cp314t` wheels to PyPI.
Free-threaded users currently have to build from source (see below).

## Installing a free-threaded CPython 3.14

### From Debian / Ubuntu (recommended for development)

```sh
# On Debian 12 (bookworm) or later:
sudo apt-get install python3.14 python3.14-venv python3.14-dev python3.14-nogil
# The interpreter binary is ``python3.14t`` and its venv lives side-by-side
# with the regular ``python3.14`` venv.
python3.14t -c "import sys; print(sys._is_gil_enabled())"  # -> False
```

On distributions that do not ship a free-threaded package, use
[deadsnakes](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa) or build
from source:

```sh
wget https://www.python.org/ftp/python/3.14.0/Python-3.14.0.tgz
tar -xzf Python-3.14.0.tgz && cd Python-3.14.0
./configure --disable-gil --enable-optimizations
make -j"$(nproc)"
sudo make altinstall   # installs /usr/local/bin/python3.14t
```

The same `compile_python_314_freethreaded.include` file under
`templates/tools/dockerfile/` scripts exactly this recipe for our CI
images.

### On macOS

```sh
# With Homebrew (3.14t formula once available):
brew install python-freethreading@3.14
```

Otherwise build from source with `--disable-gil` as above.

### On Windows

The official python.org installer for CPython 3.14 offers an opt-in
"Free-threaded" component in its advanced installer UI that installs
`python3.14t.exe`.

## Building gRPC from source against a free-threaded interpreter

The grpcio and grpcio-tools source distributions detect a free-threaded
interpreter automatically and:

1. Emit a log line `Building grpcio for a free-threaded (PEP 703) CPython
   interpreter; the extension module will opt in to Py_MOD_GIL_NOT_USED.`.
2. Add `-DPy_GIL_DISABLED=1` to the extension's `define_macros` so that
   vendored C/C++ sources which do not transitively include `<Python.h>`
   still compile with a consistent configuration.
3. Pass `freethreading_compatible=True` to Cython's `cythonize(...)`
   compiler directives, which causes Cython (≥ 3.1) to emit
   `Py_mod_gil = Py_MOD_GIL_NOT_USED` in the generated C module.

No opt-in flag is required. The detection is based on
`sysconfig.get_config_var("Py_GIL_DISABLED")`, which CPython sets to 1
on every `t`-ABI interpreter.

To build from source:

```sh
# From a free-threaded interpreter's venv:
python3.14t -m venv ~/venv-grpc-ft
source ~/venv-grpc-ft/bin/activate

pip install -r requirements.txt
GRPC_PYTHON_BUILD_WITH_CYTHON=1 pip install .
# The resulting wheel carries the ``cp314t-cp314t`` ABI/tag. Setuptools
# >= 70 picks this up automatically from ``sysconfig``.
```

If you need to pass additional compiler flags, use `GRPC_PYTHON_CFLAGS`
and `GRPC_PYTHON_LDFLAGS` as with any other gRPC build.

## Thread-safety guarantees of the Python API under no-GIL

Under PEP 703 single-operation access to a built-in container (`dict`,
`list`, `set`, `bytes`, `str`) remains atomic, but **compound**
read-modify-write sequences such as

```python
if key not in my_dict:
    my_dict[key] = expensive()
```

can now race on multiple threads. On a GIL-enabled interpreter the
interpreter lock hid this race; on `python3.14t` you must add explicit
synchronization.

The concrete guarantees gRPC Python commits to on a free-threaded
interpreter are:

* **Safe to share across threads:** `grpc.Channel`, `grpc.Server`,
  stub objects generated by `grpcio-tools`, `grpc.aio.Channel` and
  `grpc.aio.Server` are reference-counted and internally synchronized.
  You may invoke RPCs on the same channel and register handlers on the
  same server from any number of threads concurrently.
* **Safe to call concurrently:** every method that was documented as
  thread-safe on a GIL-enabled interpreter remains thread-safe on the
  free-threaded one. The core gRPC C++ library, which underlies the
  Python bindings, has always used its own mutexes and does not depend
  on the GIL.
* **Application-side invariants are your responsibility:** if your
  server handlers mutate a Python object (e.g. a cache dict) from
  multiple request threads, wrap the mutation in a `threading.Lock` or
  use a free-threading-safe data structure. On a GIL-enabled
  interpreter many such patterns were accidentally race-free; under
  PEP 703 they are not.
* **Import order:** `import grpc` does not re-enable the GIL. The
  smoke test `tests.unit._free_threading_test.FreeThreadingSmokeTest`
  asserts this invariant on every CI run.

## Known limitations and open work (Phase 2 / Phase 3)

The Phase 1 support shipped today covers the build-system opt-in and
the extension-module GIL slot. The following items are tracked as
follow-ups.

### Phase 2 speculative locking (UNVERIFIED)

As of this PR a first, **speculative and stress-test-unverified** pass
of locking has been applied to the Phase 2 audit list. These changes
have **not** been exercised under a free-threaded interpreter or a
concurrent load generator in-tree; they are a best-effort attempt at
closing obvious race windows identified by static review. Consider
them provisional until the Phase 2 stress tests land.

| File | Status | Notes |
| --- | --- | --- |
| `_cygrpc/fork.pyx.pxi` | Locked (speculative) | New `_fork_state.channels_lock` guards `add` / `discard` / iteration of `_fork_state.channels`. Never held across gRPC Core calls. |
| `_cygrpc/completion_queue.pyx.pxi` | Locked (speculative) | New `CompletionQueue._shutdown_lock` serializes transitions of `is_shutting_down` / `is_shutdown`. Hot `poll` path is deliberately unlocked. |
| `_cygrpc/server.pyx.pxi` | Locked (speculative) | New `Server._state_lock` serializes `register_completion_queue`, `register_method`, `start`, `shutdown`, `notify_shutdown_complete`, and `cancel_all_calls` flag transitions. Not held across `grpc_server_*` C calls. `_c_request_(un)registered_call` hot path intentionally unlocked (post-`start()` the registries are effectively read-only). |
| `_cygrpc/channel.pyx.pxi` | Locked (speculative) | The `on_failure` callback path in `_next_call_event` now holds `channel_state.condition`, matching the already-locked `on_success` path, so `segregated_call_states.remove` cannot race with concurrent RPC starts. |
| `_cygrpc/aio/grpc_aio.pyx.pxi` | No change | Already locked by `_global_aio_state.lock`. |
| `_cygrpc/aio/common.pyx.pxi` | No change | No shared mutable state; helpers only. asyncio single-threaded precondition still applies under no-GIL. |
| `grpc/_channel.py`, `grpc/_server.py`, `grpc/_common.py` | No change | Existing `threading.Condition` / `threading.RLock` coverage on `_RPCState`, `_ChannelCallState`, and `_ServerState` is sufficient on the state surfaces we inspected; `_common.py` has no mutable module-level state. |

**Caveats and explicit non-claims:**

* Every lock added above is a plain `threading.Lock` (except where the
  existing code used `threading.Condition`). They are never acquired
  from within a gRPC Core callback running on a Core-owned thread; they
  are only acquired from Python-level entry points.
* We did **not** add locks to hot per-RPC paths
  (`_c_request_unregistered_call`, `_c_request_registered_call`,
  `poll`) because the registries they read are only written before
  `start()` / after `stop()`, and any performance regression from
  coarser locking cannot be measured in this environment.
* We did **not** re-audit the `.pxd.pxi` side or touch any `nogil`
  section; the locking is entirely Python-side.
* No stress test in this repository exercises concurrent RPC data
  paths on a free-threaded interpreter. Until that lands, treat the
  Phase 2 locking as a source-review checkpoint, not a proof of
  race-freedom.

### Still open

* A comprehensive thread-safety audit of the Cython / C layer beyond
  the Phase 2 file list, including the `call.pyx.pxi`,
  `credentials.pyx.pxi`, `grpc_gevent.pyx.pxi` and the full
  `_cygrpc/aio/` subtree.
* A real stress-test suite (concurrent unary, streaming, aio,
  channel-state-watch, server-side handler) hooked into the CI job
  described below. The current smoke test only asserts that the GIL
  stays disabled after import and that a small number of concurrent
  channels can be created and closed without an exception.
* Free-threaded fork support. `grpc._cython.cygrpc` installs
  `os.register_at_fork` handlers; the speculative `channels_lock`
  added above closes one race but these handlers need broader review
  against `pthread_atfork` lock-holding hazards.
* Publishing `cp314t-cp314t` wheels to PyPI.

If you hit a crash, deadlock or data race on `python3.14t`, please
file an issue with `[free-threading]` in the title and include the
output of `python3.14t -X showrefcount -c "import grpc; ..."`.

## Running the free-threaded test suite locally

```sh
# Build and install grpcio + grpcio-tests into a python3.14t venv (see
# "Building gRPC from source" above), then:
python3.14t -m unittest \
    src.python.grpcio_tests.tests.unit._free_threading_test
```

The tests in `_free_threading_test.py` use `sys._is_gil_enabled()` to
skip automatically on any GIL-enabled interpreter, so they are also
safe to run as part of the regular test suite on `python3.14`.

## Running the free-threaded test suite in CI

A non-blocking advisory CI job is wired up under the compiler name
`python3.14_freethreaded`:

```sh
tools/run_tests/run_tests.py -l python -c opt --compiler python3.14_freethreaded
```

This uses the
[`tools/dockerfile/test/python_free_threaded_debian12_x64/Dockerfile`](../../tools/dockerfile/test/python_free_threaded_debian12_x64/Dockerfile)
image, which builds CPython 3.14 with `--disable-gil` and publishes the
binary as `python3.14t`. The job is advisory (non-blocking) during
Phase 1; it will be promoted to required once the Phase 2 audit is
complete.

## Rollout

* **Phase 1 (this release, experimental)**

  * Build system detects free-threaded interpreters.
  * `grpc._cython.cygrpc` and `grpc_tools._protoc_compiler` declare
    themselves compatible with no-GIL via the Cython
    `freethreading_compatible` directive.
  * Smoke test asserts that `import grpc` keeps the GIL disabled.
  * Advisory (non-blocking) CI job builds `python3.14t` from source.
  * Documentation (this file) marked Experimental.

* **Phase 2 (next release)**

  * Full thread-safety audit of the Cython / C and Python-side shared
    state.
  * Real concurrent stress tests (unary / streaming / channel-state-
    watch / aio / fork).
  * CI job promoted to required.
  * This document promoted to "Supported".

* **Phase 3**

  * `cp314t-cp314t` wheels published to PyPI alongside the regular
    `cp314-cp314` wheels.
  * `SUPPORTED_PYTHON_VERSIONS` in `python_version.py` template
    extended with an explicit `3.14t` entry if the Python packaging
    ecosystem asks for it.
