# 3_Maxwell_SST_Physical_Lines_Falsifier_v0.3.0

**Prefix:** `3_`  
**Mode:** blind, fail-closed, PKLSA-source-native  
**Upstream family:** E010 SST Parametric Knot-Link Seed Atlas (PKLSA) `v0.3.x`  
**Validated design target:** E010 `v0.3.1` as present in the SST-Workbench Google Drive snapshot.

This release replaces the v0.2.0 direct `KnotPlot\knots\final` reader with the full repository-native PKLSA evidence graph. The Maxwell-3 falsifier does **not** choose raw KnotPlot files itself. It asks E010 which carriers exist, uses E010 carrier envelopes / qualification / independence metadata, reloads the original source bytes from the current Workbench, and re-verifies both the raw SHA-256 and PKLSA geometry SHA-256 before computation.

## Scientific boundary

Maxwell's Plate VIII, Fig. 1 is treated as the historical motivation for a closed current loop accompanied by a closed force-line loop that embraces it. In modern language this motivates a linking-number test; it is **not** evidence that Maxwell proposed topological solitons.

For a closed vortex filament `K` and a disjoint closed probe `C`, the v0.3.0 primary gate is

\[
\oint_C \mathbf u\cdot d\boldsymbol{\ell}
=\Gamma\,\operatorname{Lk}(C,K).
\]

The blind numerical kernel uses `Gamma_num = 1`, so the primary test is target-free:

\[
Q_C \equiv \oint_C \mathbf u\cdot d\boldsymbol{\ell}
\stackrel{?}{=}\operatorname{Lk}(C,K).
\]

For multicomponent links the mutual-helicity gate is

\[
H_{\rm mutual}
=2\sum_{i<j}\Gamma_i\Gamma_j\operatorname{Lk}(K_i,K_j).
\]

No self-helicity claim is made for a single centerline because a finite-core self-helicity decomposition also requires framing/twist information.

## What v0.3.0 tests

- **M1--M3 — PKLSA finite-core stress anchors.** The v0.2 coarse-grained anisotropic stress surrogate is retained, but its geometry/core scale now comes from E010 carriers and E010 `reach`; only preregistered reach-quality states are admitted.
- **M4 — reduced momentum bridge.** Optional external-data gate retained from v0.2.0.
- **M5 — structural displacement/storage current.** Optional external-data gate retained from v0.2.0.
- **M6 — Maxwell--Hopf Topological Circulation Gate.** E010's exact polygonal linking number is the independent topological target. Maxwell-3 computes the Biot--Savart circulation with its **own** C++/OpenMP kernel. Controls are `Lk=+1`, orientation reversal `-1`, a twice-traversed winding control `+2`, and a translated null loop `0`.
- **M7 — Mutual Helicity/Linking Gate.** For multicomponent carriers, Maxwell-3 independently evaluates the cross-component Biot--Savart line integrals and compares them with E010 exact pairwise linking numbers.

The key anti-circularity feature is that **PKLSA provides the geometry and exact topological invariant, while this package provides the independent dynamical line-integral kernel**.

## PKLSA admission policy

The current E010 v0.3.1 Drive release reports source-native/source-contract/identity/topology admission gates as green, but its **global all-topology campaign is not globally publication-ready** (`full_campaign_gate_pass=false`, `publication_ready_geometry_layer=false` in the inspected release snapshot). Therefore this falsifier does not use the global campaign flag as blanket evidence.

Instead every carrier is admitted fail-closed:

1. topology qualification files, geometry metrics, source-independence ledger and carrier envelope must exist;
2. individual E010 literature hard gates must pass;
3. byte-identical mirrors and declared raw/geometry duplicates are excluded;
4. the original source path is remapped to the current `SST-Workbench` root;
5. raw SHA-256 is recomputed and must match the carrier envelope;
6. geometry is decoded with **E010's own `pklsa_builder.io_geometry.load_geometry`**;
7. E010 `geometry_sha256` is recomputed and must match;
8. the E010 declared common translation + total-length normalization is applied, preserving relative placement of link components.

An aggregate topology failure may coexist with an individually clean carrier. Such a carrier can support only a **carrier-specific** numerical result; v0.3.0 never promotes it to a topology-class claim.

## C++ acceleration

The package follows the existing SST C++/pybind11 pattern:

- C++17;
- pybind11;
- OpenMP when available;
- explicit setuptools package discovery (no flat-layout auto-discovery);
- pure NumPy reference backend for audit/self-test;
- native/Python equality checks.

E010's own `_native` extension is used only for the exact polygonal topological target when available. The circulation/helicity calculation is deliberately implemented in the separate Maxwell-3 native extension.

## Workbench discovery

Default canonical root:

```text
C:\workspace\projects\SST-Workbench
```

Override it with:

```bat
set SST_WORKBENCH_ROOT=D:\path\to\SST-Workbench
```

The resolver selects the newest local E010 `E010-v0.3.*` release with a production `RELEASE.json`. You can pin one explicitly through the CLI with `--pklsa-release`.

## Ready-to-run commands

Fast representative blind run:

```bat
run_all_basic.cmd
```

Full admitted PKLSA topology scan, one deterministic provenance-clean carrier per topology:

```bat
run_all_extended.cmd
```

Very expensive all-admissible-carrier campaign:

```bat
run_all_certification.cmd
```

Individual stages:

```text
run_00_install.cmd              install + build C++ + native self-test
run_01_preflight.cmd [profile]  inspect E010 release/admission before a run
run_02_basic.cmd                representative blind run
run_03_extended.cmd             full topology scan
run_03_certification.cmd        all admitted carriers
run_04_native_benchmark.cmd     C++ vs Python circulation benchmark
run_05_python_reference.cmd     pure-Python unit/reference tests
run_06_native_selftest.cmd      native numerical self-test
run_07_with_external_closures.cmd  optional M4/M5 data
run_90_verify_frozen.cmd        verify frozen hashes
run_90_pack_blind.cmd           package one frozen run as *_BLIND.zip
run_99_unblind.cmd              reveal committed comparison targets
```

The extended/certification profiles require the native backend. Basic can fall back to Python but will be much slower.

## Output convention

Runs are written beneath

```text
./3_Maxwell_SST_Physical_Lines_Falsifier_v0.3.0-outputs/<profile>_YYYYMMDD_HHMMSS/
```

Every run writes `FROZEN_SHA256.json`. Blind result ledgers do not contain raw source paths or human-readable carrier/provider identities; those identifiers are one-way hashed. The `basic` preregistration intentionally retains its requested topology IDs so that topology selection is auditable before the run.

## Blind/unblind discipline

The main package contains commitments only. The separate unblind archive contains:

- Maxwell's historical uniform-vortex coefficient comparison;
- the Bernoulli/dynamic-pressure comparison;
- the existing `m_e/e` bridge target for optional M4;

The M6/M7 pass/fail logic does not use an SST circulation constant at all; SI-scale restoration, if desired after the blind run, is a separate Canon-level interpretation step.

## Important interpretation

A PASS means that the admitted source-native PKLSA geometry obeys the preregistered numerical circulation/linking or stress closure within the stated discretization. It does **not** imply that electromagnetism is literally a fluid vortex model, that Maxwell's mechanical ether is correct, that PKLSA's global atlas is certified, or that SST has been established.


## Build hotfix 2026-09-29

On deeply nested Windows Workbench paths, the original v0.3.0 generated setuptools build used an absolute `cpp/native.cpp` path. MSVC/setuptools mirrored that absolute path beneath `build\\temp...`, which could make the linker `.exp` path exceed the legacy Windows `MAX_PATH` limit and fail with `LNK1104`. The hotfix uses the repository-relative `cpp/native.cpp` path plus short `build\\t` and `build\\l` directories. The `run_all_*.cmd` wrappers were also corrected to propagate a failed install/preflight exit code instead of accidentally returning 0. No scientific gate, threshold, blind commitment, or numerical kernel was changed.
