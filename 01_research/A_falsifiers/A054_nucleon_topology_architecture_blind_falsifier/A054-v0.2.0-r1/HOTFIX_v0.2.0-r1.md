# A054 v0.2.0-r1 execution hotfix

Scientific protocol unchanged from v0.2.0. No geometry, threshold, gate, or reveal rule changed.

Fixes:
1. Every command uses `.venv\\Scripts\\python.exe` explicitly; venv activation no longer leaks across `setlocal` boundaries.
2. Stale ABI-specific `_native*.pyd`/`.so` files are deleted before native rebuild.
3. Extended/FULL require OpenMP before candidate preparation starts.
4. The isolated blind runner only copies a native extension compatible with the current interpreter ABI.
5. The copied extension is immediately imported in isolation with the same interpreter; failure removes it and is recorded in `RUNNER_MANIFEST.json`.
6. Runner manifest records interpreter path/version and native-import verification.

The v0.2.0 failure log showed a CPython 3.14 editable wheel during installation while the archived blind runner carried `_native.cp313-win_amd64.pyd`. FULL then correctly aborted because `require_openmp` resolved to `numpy_reference`.
