gRPC Python CSM Observability
=============================

Package for gRPC Python CSM Observability.


Installation
------------

Currently gRPC Python CSM Observability is **only available for Linux**.

Installing From PyPI
~~~~~~~~~~~~~~~~~~~~

::

  $ pip install grpcio-csm-observability


Installing From Source
~~~~~~~~~~~~~~~~~~~~~~

::

  $ export REPO_ROOT=grpc  # REPO_ROOT can be any directory of your choice
  $ git clone -b RELEASE_TAG_HERE https://github.com/grpc/grpc $REPO_ROOT
  $ cd $REPO_ROOT
  $ git submodule update --init

  $ cd src/python/grpcio_csm_observability

  # For the next command do `sudo pip install` if you get permission-denied errors
  $ pip install .


Dependencies
------------
gRPC Python CSM Observability Depends on the following packages:

::

  grpcio
  grpcio-observability
  opentelemetry-sdk


Free-threaded CPython (PEP 703) Support
---------------------------------------

Starting with CPython 3.13, an experimental "free-threaded" build (also
known as ``--disable-gil`` or ``Py_GIL_DISABLED``, with executables
typically named ``python3.13t`` / ``python3.14t``) is available.
``grpcio-csm-observability`` is a pure-Python package; its free-threading
behavior is inherited from its dependencies. The ``grpcio-observability``
Cython extension this package builds on declares itself free-threading
compatible via the ``# cython: freethreading_compatible=True`` directive,
so importing ``grpc_csm_observability`` on a free-threaded interpreter
does **not** trigger CPython's automatic re-enablement of the GIL.

Support status:

* **Beta.** The plugin is expected to work, but free-threading mode is
  not yet exercised in the default CI matrix. Treat free-threaded
  support as *beta* and please report issues at
  https://github.com/grpc/grpc/issues.
* The companion ``grpcio`` (``grpc._cython.cygrpc``),
  ``grpcio-tools`` (``grpc_tools._protoc_compiler``) and
  ``grpcio-observability`` (``grpc_observability._cyobservability``)
  Cython extensions are similarly declared free-threading compatible.

Known limitations:

* **OpenTelemetry exporter dependencies** (for example
  ``opentelemetry-api``, ``opentelemetry-sdk`` and language-specific
  exporters) must themselves declare free-threading compatibility. If
  any imported extension does not, CPython will automatically re-enable
  the GIL for the entire process, which negates the benefit of running
  on a free-threaded interpreter.
* Tuning guidance for the underlying observability plugin (see the
  ``GRPC_PYTHON_CENSUS_*`` environment variables documented below)
  applies equally on free-threaded interpreters and may need adjustment
  if you observe contention regressions.
* The stable limited ABI (``Py_LIMITED_API``) is mutually exclusive
  with free-threaded builds; ``cp313t`` / ``cp314t`` wheels of
  ``grpcio-observability`` are therefore published as separate
  artifacts (when wheels are produced for those ABIs).


Usage
-----

Example usage is similar to `the example here <https://github.com/grpc/grpc/tree/master/examples/python/observability>`_, instead of importing from ``grpc_observability``, you should import from ``grpc_csm_observability``:

.. code-block:: python

    import grpc_csm_observability
    
    csm_otel_plugin = grpc_csm_observability.CsmOpenTelemetryPlugin(
        meter_provider=provider
    )


We also provide several environment variables to help you optimize gRPC python observability for your particular use.

* Note: The term "Census" here is just for historical backwards compatibility reasons and does not imply any dependencies.

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
