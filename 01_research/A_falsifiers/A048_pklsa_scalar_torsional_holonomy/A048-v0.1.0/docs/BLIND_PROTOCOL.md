# A048 v0.1.0 blind protocol

1. `prepare_blind.py` deletes stale output and creates anonymous dimensionless dispersion cases.
2. Generator labels and random parameters are stored in `.a048_private_reveal.json`, outside the evidence tree.
3. BLIND receives only anonymous `(k, omega)` measurements, config/source commitments, and runtime metadata.
4. `run_blind.py` classifies each case using competing quadratic and linear/gapped fits.
5. Optional native mode repeats the same analysis primitives through C++17/pybind11.
6. `seal_blind.py` recursively SHA-256 hashes the complete BLIND tree.
7. `reveal.py` verifies every seal entry before reading the private label map or importing canonical SST constants.
8. `package_outputs.py` creates separate BLIND and REVEALED ZIPs plus the combined output archive.

The synthetic cases are a software/inference qualification set. They are not physical evidence for SST.
