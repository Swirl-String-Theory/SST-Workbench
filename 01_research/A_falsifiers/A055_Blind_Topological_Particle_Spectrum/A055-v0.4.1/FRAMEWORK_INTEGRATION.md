# Framework integration — v0.4.1

The instance is pinned to `SST_Falsifier_Framework_v1.0.6` using the generated `framework_bootstrap.py` + `.sst_framework_root` contract.

Pin precedence is fail-closed: explicit `SST_FALSIFIER_FRAMEWORK_ROOT`, then the instance locator, then legacy discovery only when no locator exists. An invalid explicit pin does not silently fall back.

Framework package manifest SHA-256: `233730abad5ef26f851db0ae75c691fd17daa75e99beb8419d6934ccf85c15be`.
Canonical freeze JSON SHA-256: `03813843a3c00907ed12def0decf3572a57b7f40e5671276bd14b9189ac31759`.

The v1.0.6 backend arithmetic is unchanged from v1.0.4; this migration does not alter the A055 numerical thresholds.
