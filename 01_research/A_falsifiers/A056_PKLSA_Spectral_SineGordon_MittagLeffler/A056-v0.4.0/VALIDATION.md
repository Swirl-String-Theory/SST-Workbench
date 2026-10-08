# A056-v0.4.0 validation

**Release:** A056-v0.4.0  
**Framework:** SST Falsifier Framework **v1.0.6 CANONICAL_FROZEN**  
**Validation date:** 2026-10-07  
**Status:** **IMPLEMENTATION / PREREGISTRATION VALIDATED; REAL v0.4.0 PHYSICS UNRUN**

## Scientific version boundary

v0.4.0 is a new scientific version because the blocking G2 spectral test changes. The historical A056-v0.3.0 `m=3` filament result remains a valid G2 FAIL under its frozen raw-phase split-POD rule. Its observed diagnostics are retained only as development provenance and cannot satisfy any v0.4.0 gate.

Official v0.4.0 real-provider campaigns use the preregistered fresh Kelvin perturbation `m=4`, `epsilon=0.03`. No such E010 campaign was executed during release assembly in this container, so no new SST/SG/ML physics conclusion is claimed here.

## Canonical framework pin

- framework version: `1.0.6`
- status: `CANONICAL_FROZEN`
- canonical Workbench path: `06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.6`
- canonical framework ZIP SHA-256: `24629848e3befcde67c02a935fc78347560ac42107043fbc14aaabdf146ee60d`
- framework package-manifest SHA-256: `233730abad5ef26f851db0ae75c691fd17daa75e99beb8419d6934ccf85c15be`
- framework regression selftest executed from this release environment: **54 passed**

The framework numerical backend implementation is unchanged from the v1.0.4 validated backend baseline; v1.0.6 adds bootstrap, output-integrity and reveal-orchestration hardening.

## Frozen A056 protocol

Frozen protocol bundle SHA-256:

```text
4080f933a8277b548f4251f0d19b668ef3cb62c85a3480e11a627abde8b022dd
```

Post-freeze verification: **PASS**. Public forbidden-term scan: **PASS, 0 hits**.

The science contract SHA-binds all three real-provider configs and all four score configs. Changing `m`, `epsilon`, a blocking G2 threshold, or a scoring/provider config requires a new A056 version.

## v0.4.0 G2 implementation

Blocking metrics:

```text
circular top-3 POD energy fraction        >= 0.95
circular POD orthogonality residual       <= 1e-10
early/late non-zero Fourier-power overlap >= 0.90
Mittag-Leffler alpha=1 identity error      <= 1e-12
```

The raw-phase split-POD overlap is diagnostic only. The circular early/late POD subspace overlap is also diagnostic only. The legacy derived-ringdown fallback still uses the historical raw-POD coordinates, so changing G2 did not silently change the downstream ringdown observable.

Metamorphic tests cover integer `2*pi` wrapping, time-dependent global phase shifts, and fixed cyclic spatial relabelling. A separate sector-change test verifies that true early/late Fourier-sector redistribution is rejected.

## Public instance regression suite

```text
28 passed
```

This includes contract/hash checks, v1.0.6 pin/bootstrap checks, provider tests, Windows runtime-reset regression, circular/Fourier metamorphic tests, synthetic-control G2 tests, read-only diagnostic tests, and G2 fail-path artifact checks.

## Dynamic-provider selftest

An analytic trefoil finite-core filament selftest with the v0.4.0 `m=4`, `epsilon=0.03` perturbation returned:

```text
status               PASS
nt                   61
ns                   96
provider_valid       true
phase_valid_fraction 1.0
ringdown_min         1.0
ringdown_max         1.0268562667975254
```

This validates implementation plumbing only; it is not E010 evidence.

## Synthetic FULL acceptance smoke

The five bundled synthetic controls all passed the new invariant G2:

```text
G0 PASS
G1 PASS
G2 PASS
G3 PASS
G4 PASS
G5 UNRESOLVED
G6 NOT_RUN_PREREQUISITE
G7 NOT_RUN_PREREQUISITE
G8 NOT_RUN_PREREQUISITE
G9 DEFERRED
```

Observed G2 extrema were:

```text
min circular top-3 energy = 0.9999705068006987
max circular orth residual = 1.8503289070904708e-15
min Fourier-power overlap  = 0.9996380365061194
max ML alpha=1 identity err= 1.1102230246251565e-16
```

G5 is `UNRESOLVED` only because this container does not have the `pybind11` package/headers needed to build the instance-local C++ extension. The build provenance correctly records the failed local attempt; the target Windows `run_install.cmd` installs pybind11 before G5. No C++ certification claim is made from this container.

Framework v1.0.6 `REVEAL_IF_ALLOWED` was exercised against this smoke. It verified the blind ledger/output-manifest integrity and correctly withheld reveal because G5 remained `UNRESOLVED`.

## Historical development snapshot

The exact user-supplied v0.3.0 G2 read-only diagnostic is retained at:

```text
data/development/A056_v0.3.0_G2_DIAGNOSTICS_READONLY.json
```

SHA-256:

```text
17c3e192ccb48ea70fb0afecf5a79505cd53d0cf27051e369d2bb0cef4e46bd2
```

It is not referenced by any runtime config or by `experiment/pipeline.py`.

## PDF validation

The generated falsifier report is 11 A4 pages. It was rendered to PNG and visually inspected after the final blind smoke: no clipped tables, overlaps, black boxes, or broken layout were observed.

## Target-machine next step

The first official v0.4.0 scientific run is:

```bat
run_e010_filament.cmd C:\workspace\projects\SST-Workbench
```

That run must use the frozen fresh `m=4`, `epsilon=0.03` provider config. If G2 passes, the unchanged G3/G4/G5 chain becomes scientifically interpretable; if G2 fails, the failure should be retained rather than retuned in-place.
