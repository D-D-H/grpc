gRPC Python
===========

Package for gRPC Python.


Installation
------------

gRPC Python is available for Linux, macOS, and Windows.

Installing From PyPI
~~~~~~~~~~~~~~~~~~~~

If you are installing locally...

::

  $ pip install grpcio

Else system wide (on Ubuntu)...

::

  $ sudo pip install grpcio

If you're on Windows make sure that you installed the :code:`pip.exe` component
when you installed Python (if not go back and install it!) then invoke:

::

  $ pip.exe install grpcio

Windows users may need to invoke :code:`pip.exe` from a command line ran as
administrator.

n.b. On Windows and on Mac OS X one *must* have a recent release of :code:`pip`
to retrieve the proper wheel from PyPI. Be sure to upgrade to the latest
version!

Installing From Source
~~~~~~~~~~~~~~~~~~~~~~

Building from source requires that you have the Python headers (usually a
package named :code:`python-dev`).

::

  $ export REPO_ROOT=grpc  # REPO_ROOT can be any directory of your choice
  $ git clone -b RELEASE_TAG_HERE https://github.com/grpc/grpc $REPO_ROOT
  $ cd $REPO_ROOT
  $ git submodule update --init

  # To include systemd socket-activation feature in the build,
  # first install the `libsystemd-dev` package, then :
  $ export GRPC_PYTHON_BUILD_WITH_SYSTEMD=1

  # For the next two commands do `sudo pip install` if you get permission-denied errors
  $ pip install -r requirements.txt
  $ GRPC_PYTHON_BUILD_WITH_CYTHON=1 pip install .

You cannot currently install Python from source on Windows. Things might work
out for you in MSYS2 (follow the Linux instructions), but it isn't officially
supported at the moment.

Troubleshooting
~~~~~~~~~~~~~~~

Help, I ...

* **... see the following error on some platforms**

  ::

    /tmp/pip-build-U8pSsr/cython/Cython/Plex/Scanners.c:4:20: fatal error: Python.h: No such file or directory
    #include "Python.h"
                    ^
    compilation terminated.

  You can fix it by installing `python-dev` package. i.e

  ::

    sudo apt-get install python-dev


Versioning
~~~~~~~~~~

gRPC Python is developed in a monorepo shared with implementations of gRPC in
other programming languages. While the minor versions are released in
lock-step with other languages in the repo (e.g. 1.63.0 is guaranteed to exist
for all languages), patch versions may be specific to only a single
language. For example, if 1.63.1 is a C++-specific patch, 1.63.1 may not be
uploaded to PyPi. As a result, it is __not__ a good assumption that the latest
patch for a given minor version on Github is also the latest patch for that
same minor version on PyPi.


Free-threaded CPython (PEP 703) Support
---------------------------------------

Starting with CPython 3.13, an experimental "free-threaded" build (also known
as ``--disable-gil`` or ``Py_GIL_DISABLED``, with executables typically named
``python3.13t`` / ``python3.14t``) is available. The ``grpcio`` Cython
extension declares itself free-threading compatible via the
``# cython: freethreading_compatible=True`` directive in
``src/python/grpcio/grpc/_cython/cygrpc.pyx``. As a result, importing
``grpc`` on a free-threaded interpreter does **not** trigger CPython's
automatic re-enablement of the GIL.

Support status:

* **Beta.** The native extension loads cleanly and the synchronous and
  ``grpc.aio`` APIs are expected to work, but free-threading mode is not
  yet exercised in the default CI matrix. Treat free-threaded support as
  *beta* and please report issues at
  https://github.com/grpc/grpc/issues.
* The companion Cython extensions in
  ``grpcio-tools`` (``grpc_tools._protoc_compiler``) and
  ``grpcio-observability`` (``grpc_observability._cyobservability``) are
  similarly declared free-threading compatible.

Known limitations:

* **gevent integration** (``grpc.experimental.gevent``) is not supported on
  free-threaded interpreters, because gevent itself does not currently
  declare free-threading compatibility.
* **Third-party C/C++ extensions** that gRPC commonly interacts with —
  notably ``protobuf`` (when the C++ implementation is selected) and the
  OpenTelemetry exporter packages used by ``grpcio-observability`` — must
  themselves declare free-threading compatibility. If any imported
  extension does not, CPython will automatically re-enable the GIL for
  the entire process.
* ``os.fork()``-based fork support
  (``GRPC_ENABLE_FORK_SUPPORT=1``) is more fragile under free-threading.
  Prefer ``multiprocessing`` with ``set_start_method("spawn")`` when
  possible.
* The stable limited ABI (``Py_LIMITED_API``) is mutually exclusive with
  free-threaded builds; ``cp313t`` / ``cp314t`` wheels are therefore
  published as separate artifacts (when wheels are produced for those
  ABIs).

