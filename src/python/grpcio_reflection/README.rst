gRPC Python Reflection package
==============================

Reference package for reflection in GRPC Python.


Dependencies
------------

Depends on the `grpcio` package, available from PyPI via `pip install grpcio`.


Free-threaded CPython (PEP 703) Support
---------------------------------------

Starting with CPython 3.13, an experimental "free-threaded" build (also
known as ``--disable-gil`` or ``Py_GIL_DISABLED``, with executables
typically named ``python3.13t`` / ``python3.14t``) is available.
``grpcio-reflection`` is a pure-Python package; its free-threading
behavior is inherited from its dependencies. The ``grpcio`` Cython
extension this package builds on declares itself free-threading
compatible via the ``# cython: freethreading_compatible=True``
directive in ``src/python/grpcio/grpc/_cython/cygrpc.pyx``, so
importing ``grpc_reflection`` on a free-threaded interpreter does
**not** trigger CPython's automatic re-enablement of the GIL.

Support status:

* **Beta.** The reflection servicer is expected to work, but
  free-threading mode is not yet exercised in the default CI matrix.
  Treat free-threaded support as *beta* and please report issues at
  https://github.com/grpc/grpc/issues.
* The companion ``grpcio`` (``grpc._cython.cygrpc``),
  ``grpcio-tools`` (``grpc_tools._protoc_compiler``) and
  ``grpcio-observability`` (``grpc_observability._cyobservability``)
  Cython extensions are similarly declared free-threading compatible.

