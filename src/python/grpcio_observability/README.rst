gRPC Python Observability
=========================

Package for gRPC Python Observability.

More details can be found in `OpenTelemetry Metrics gRFC <https://github.com/grpc/proposal/blob/master/A66-otel-stats.md#opentelemetry-metrics>`_.

How gRPC Python Observability Works
-----------------------------------

gRPC Python is a wrapper layer built upon the gRPC Core (written in C/C++). Most of telemetry data
is collected at core layer and then exported to Python layer. To optimize performance and reduce
the overhead of acquiring the GIL too frequently, telemetry data is initially cached at the Core layer
and then exported to the Python layer in batches.

Note that while this approach enhances efficiency, it will introduce a slight delay between the
time the data is collected and the time it becomes available through Python exporters.



Installation
------------

Currently gRPC Python Observability is **only available for Linux**.

Installing From PyPI
~~~~~~~~~~~~~~~~~~~~

::

  $ pip install grpcio-observability


Installing From Source
~~~~~~~~~~~~~~~~~~~~~~

Building from source requires that you have the Python headers (usually a
package named :code:`python-dev`) and Cython installed. It further requires a
GCC-like compiler to go smoothly; you can probably get it to work without
GCC-like stuff, but you may end up having a bad time.

::

  $ export REPO_ROOT=grpc  # REPO_ROOT can be any directory of your choice
  $ git clone -b RELEASE_TAG_HERE https://github.com/grpc/grpc $REPO_ROOT
  $ cd $REPO_ROOT
  $ git submodule update --init

  $ cd src/python/grpcio_observability
  $ python -m make_grpcio_observability

  # For the next command do `sudo pip install` if you get permission-denied errors
  $ GRPC_PYTHON_BUILD_WITH_CYTHON=1 pip install .


Free-threaded CPython (PEP 703) Support
---------------------------------------

Starting with CPython 3.13, an experimental "free-threaded" build (also
known as ``--disable-gil`` or ``Py_GIL_DISABLED``, with executables
typically named ``python3.13t`` / ``python3.14t``) is available. The
``grpcio-observability`` Cython extension declares itself free-threading
compatible via the ``# cython: freethreading_compatible=True`` directive
in ``grpc_observability/_cyobservability.pyx``. As a result, importing
``grpc_observability`` on a free-threaded interpreter does **not**
trigger CPython's automatic re-enablement of the GIL.

Support status:

* **Beta.** The native extension loads cleanly and the observability
  plugin is expected to work, but free-threading mode is not yet
  exercised in the default CI matrix. Treat free-threaded support as
  *beta* and please report issues at
  https://github.com/grpc/grpc/issues.
* The companion ``grpcio`` (``grpc._cython.cygrpc``) and
  ``grpcio-tools`` (``grpc_tools._protoc_compiler``) Cython extensions
  are similarly declared free-threading compatible.

Known limitations:

* **OpenTelemetry exporter dependencies** (for example
  ``opentelemetry-api``, ``opentelemetry-sdk`` and language-specific
  exporters) must themselves declare free-threading compatibility. If
  any imported extension does not, CPython will automatically re-enable
  the GIL for the entire process, which negates the benefit of running
  on a free-threaded interpreter.
* Because telemetry data collected at the gRPC Core layer is exported
  to Python in batches via a dedicated thread, free-threaded
  interpreters may exhibit different contention characteristics than a
  GIL-enabled build. Tune
  ``GRPC_PYTHON_CENSUS_EXPORT_BATCH_INTERVAL`` and
  ``GRPC_PYTHON_CENSUS_MAX_EXPORT_BUFFER_SIZE`` (see below) if you
  observe regressions.
* The stable limited ABI (``Py_LIMITED_API``) is mutually exclusive
  with free-threaded builds; ``cp313t`` / ``cp314t`` wheels are
  therefore published as separate artifacts (when wheels are produced
  for those ABIs).


Dependencies
------------
gRPC Python Observability Depends on the following packages:

::

  grpcio
  opentelemetry-api


Usage
-----

You can find example usage in `Python example folder <https://github.com/grpc/grpc/tree/master/examples/python/observability>`_.

We also provide several environment variables to help you optimize gRPC python observability for your particular use.

1. GRPC_PYTHON_CENSUS_EXPORT_BATCH_INTERVAL
    * This controls how frequently telemetry data collected within gRPC Core is sent to Python layer.
    * Default value is 0.5 (Seconds).

2. GRPC_PYTHON_CENSUS_MAX_EXPORT_BUFFER_SIZE
    * This controls the maximum number of telemetry data items that can be held in the buffer within gRPC Core before they are sent to Python.
    * Default value is 10,000.

3. GRPC_PYTHON_CENSUS_EXPORT_THRESHOLD
    * This setting acts as a trigger: When the buffer in gRPC Core reaches a certain percentage of its capacity, the telemetry data is sent to Python.
    * Default value is 0.7 (Which means buffer will start export when it's 70% full).

4. GRPC_PYTHON_CENSUS_EXPORT_THREAD_TIMEOUT
    * This controls the maximum time allowed for the exporting thread (responsible for sending data to Python) to complete.
    * Main thread will terminate the exporting thread after this timeout.
    * Default value is 10 (Seconds).
