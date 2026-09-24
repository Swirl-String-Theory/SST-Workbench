# A046 v0.2.0 blind protocol

The blind stage contains only dimensionless synthetic controls and frozen tolerances.

`prepare_blind.py` deletes stale v0.2.0 output, creates the evidence tree, and records config and source
manifest hashes.

Python reference mode writes `BLIND/python_backend/` and its console/test evidence into `BLIND/logs/`.
The full run then builds the C++17/pybind11/OpenMP extension, repeats the blind campaign under
`SST_BACKEND=native`, records native pytest and build logs, hashes the loaded native module, and writes a
Python/native parity summary.

Only then does `seal_blind.py` recursively SHA-256 every evidence file under `BLIND/`.

`reveal.py` verifies every seal entry before importing canonical SST constants or the orthodox Earth-rotation
benchmark. A full native run is labeled `FULL_PYTHON_NATIVE_QUALIFIED` only when both blind campaigns are
qualified and backend parity passes.
