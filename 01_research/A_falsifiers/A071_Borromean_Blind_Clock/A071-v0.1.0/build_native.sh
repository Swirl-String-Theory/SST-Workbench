#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p native/bin
g++ -std=c++17 -O3 -fopenmp -fPIC -shared native/biot_savart.cpp -o native/bin/libbs_native.so
