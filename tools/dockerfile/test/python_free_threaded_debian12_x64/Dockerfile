# Copyright 2026 The gRPC Authors
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
#
# Dockerfile used by the advisory ``python3.14_freethreaded`` CI job.
# This image builds a free-threaded (PEP 703, no-GIL) CPython 3.14 from
# source and exposes it as ``python3.14t``. See
# ``doc/python/free_threading.md`` for the overall design.

FROM debian:12

#=================
# Basic C core dependencies

RUN apt-get update && apt-get install -y \
  build-essential \
  autoconf \
  libtool \
  pkg-config \
  gcc \
  g++ \
  libc6 \
  libc6-dbg \
  libc6-dev \
  && apt-get clean

# Tools
RUN apt-get update && apt-get install -y \
  bzip2 \
  curl \
  dnsutils \
  git \
  lcov \
  make \
  strace \
  time \
  unzip \
  wget \
  zip \
  && apt-get clean

#=================
# Setup git to access working directory across docker boundary.
RUN git config --global --add safe.directory '*'
RUN git config --global protocol.file.allow always

RUN mkdir /var/local/jenkins

#=================
# Base CPython 3.11 (Debian 12 default) for the test driver itself.
# The free-threaded interpreter below is only used to exercise grpcio; the
# run_tests.py harness itself still runs on a regular GIL interpreter.
RUN apt-get update && apt-get install -y python3 python3-dev python3-pip python3-venv && apt-get clean
RUN python3 -m pip install --break-system-packages coverage six
RUN python3 -m pip install --break-system-packages --upgrade \
    google-auth==1.23.0 google-api-python-client==1.12.8 oauth2client==4.1.0

#=================
# Compile free-threaded (PEP 703 / no-GIL) CPython 3.14 from source.
#
# Kept in sync with
# ``templates/tools/dockerfile/compile_python_314_freethreaded.include``.

RUN apt-get update && apt-get install -y zlib1g-dev libssl-dev libsqlite3-dev && apt-get clean
RUN apt-get update && apt-get install -y jq build-essential libffi-dev && apt-get clean

RUN cd /tmp && \
    wget -q https://www.python.org/ftp/python/3.14.0/Python-3.14.0.tgz && \
    tar xzvf Python-3.14.0.tgz && \
    mv Python-3.14.0 Python-3.14.0-freethreaded && \
    cd Python-3.14.0-freethreaded && \
    ./configure --disable-gil && \
    make -j4 && \
    make altinstall

RUN python3.14t -m ensurepip && \
    python3.14t -m pip install coverage

#=================
# Install cmake
RUN apt-get update && apt-get install -y cmake && apt-get clean

#=================
# Install ccache
RUN curl -sSL --fail --retry 5 -o ccache.tar.gz https://github.com/ccache/ccache/releases/download/v4.11.3/ccache-4.11.3.tar.gz \
    && tar -zxf ccache.tar.gz \
    && cd ccache-4.11.3 \
    && mkdir build && cd build \
    && cmake -DCMAKE_BUILD_TYPE=Release -DZSTD_FROM_INTERNET=ON -DHIREDIS_FROM_INTERNET=ON .. \
    && make -j4 && make install \
    && cd ../.. \
    && rm -rf ccache-4.11.3 ccache.tar.gz
