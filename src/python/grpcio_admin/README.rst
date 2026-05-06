gRPC Python Admin Interface Package
===================================

Debugging gRPC library can be a complex task. There are many configurations and
internal states, which will affect the behavior of the library. This Python
package will be the collection of admin services that are exposing debug
information. Currently, it includes:

* Channel tracing metrics (grpcio-channelz)
* Client Status Discovery Service (grpcio-csds)

Here is a snippet to create an admin server on "localhost:50051":

    server = grpc.server(ThreadPoolExecutor())
    port = server.add_insecure_port('localhost:50051')
    grpc_admin.add_admin_servicers(self._server)
    server.start()

Welcome to explore the admin services with CLI tool "grpcdebug":
https://github.com/grpc-ecosystem/grpcdebug.

For any issues or suggestions, please send to
https://github.com/grpc/grpc/issues.


Free-threaded CPython (PEP 703) Support
---------------------------------------

Starting with CPython 3.13, an experimental "free-threaded" build (also
known as ``--disable-gil`` or ``Py_GIL_DISABLED``, with executables
typically named ``python3.13t`` / ``python3.14t``) is available.
``grpcio-admin`` is a pure-Python meta-package that re-exports the
admin servicers from ``grpcio-channelz`` and ``grpcio-csds``; its
free-threading behavior is therefore inherited from its dependencies.
The ``grpcio`` Cython extension that those packages build on declares
itself free-threading compatible via the
``# cython: freethreading_compatible=True`` directive in
``src/python/grpcio/grpc/_cython/cygrpc.pyx``, so importing
``grpc_admin`` on a free-threaded interpreter does **not** trigger
CPython's automatic re-enablement of the GIL.

Support status:

* **Beta.** The admin servicers are expected to work, but free-threading
  mode is not yet exercised in the default CI matrix. Treat
  free-threaded support as *beta* and please report issues at
  https://github.com/grpc/grpc/issues.
* The companion ``grpcio`` (``grpc._cython.cygrpc``),
  ``grpcio-tools`` (``grpc_tools._protoc_compiler``) and
  ``grpcio-observability`` (``grpc_observability._cyobservability``)
  Cython extensions are similarly declared free-threading compatible.
