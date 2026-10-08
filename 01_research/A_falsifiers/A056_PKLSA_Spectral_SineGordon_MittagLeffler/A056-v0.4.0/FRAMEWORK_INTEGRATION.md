# Framework integration

A056-v0.4.0 is a thin scientific instance of **SST Falsifier Framework v1.0.6 CANONICAL_FROZEN**.

Canonical Workbench path:

```text
06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.6
```

Expected canonical archive SHA-256:

```text
24629848e3befcde67c02a935fc78347560ac42107043fbc14aaabdf146ee60d
```

Expected framework `PACKAGE_MANIFEST.json` SHA-256:

```text
233730abad5ef26f851db0ae75c691fd17daa75e99beb8419d6934ccf85c15be
```

The instance uses the v1.0.6 shared bootstrap contract, package-safe `run_python` launcher, exact framework pin, output-tree/manifest integrity verification, stale-reveal cleanup and `REVEAL_IF_ALLOWED` orchestration. A056 does not modify the frozen framework. Python/NumPy FP64 is reference arithmetic; C++/OpenMP FP64 is certification; SYCL FP32/DD32 is screening-only.
