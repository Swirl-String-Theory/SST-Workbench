# A003 Import Adapter v0.2.3 — G5 NumPy 2.x compatibility hotfix

- Diagnose from user-provided v0.2.2 G5 bundle: six Fibonacci-torus seeds failed on `np.float` inside pyknotid 0.5.3 with NumPy 2.4.6; a separate archived run could not import pyknotid at all.
- Wrap only `pyknotid` import / determinant calculation in a reversible, single-threaded NumPy legacy-alias compatibility scope (`float`, `int`, `complex`); never patch installed site-packages.
- Add actual provider environment attestation (Python executable, NumPy, pyknotid versions) to G5 report.
- Add 3 regression tests for alias behavior, isolated legacy-provider reproduction, and cleanup on exception.
- No changes to atlas v0.1.2 source hashes, G0–G4 thresholds, G5 expected determinants, G5 strict fail-closed policy or G6 `NOT_RUN`.
- Provider-runtime certification remains **NOT TESTED HERE**: the container does not have pyknotid. Run on the user's Python venv.
- Add `run_g5_smoke.cmd` / `g5_provider_smoketest.py` as minimal real-provider smoke check before longer numerical campaigns.
