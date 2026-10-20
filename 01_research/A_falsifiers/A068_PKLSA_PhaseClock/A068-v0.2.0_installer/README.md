# A068 PKLSA Intrinsic Phase Clock v0.2.0 / Framework v1.0.8

**Status: local science overlay built and method-tested; NOT frozen or physically certified.**

This archive contains a *versioned scientific instance overlay* designed to be installed by the **actual** `SST_Falsifier_Framework_v1.0.8/tools/new_falsifier.py`. It is **not** a changed v1.0.8 framework distribution, and does not modify that framework or the prior `A068-v0.1.0` instance.

## Windows install

1. Unpack the archive to a temporary working folder.
2. From its root run:

```bat
py -3 install_A068_v0.2.0.py --workbench-root C:\workspace\projects\SST-Workbench
```

The installer refuses to overwrite an existing v0.2.0 directory and refuses to run if the official v1.0.8 generator is missing. It uses the generated relative `.sst_framework_root` pin and **retains the private randomly generated keys outside this public ZIP**.

3. Then:

```bat
cd C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A068_PKLSA_PhaseClock\A068-v0.2.0
py -3 -m pip install -r requirements.txt
py -3 -m pytest -q tests
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd REVEAL_IF_ALLOWED
```

Do not FREEZE until final source and private-reveal contracts have been checked. `REVEAL_IF_ALLOWED` is expected to **withhold** reveal because G3 is UNRESOLVED.

## Included experimental inputs

* `PREFLIGHT_RESULTS.json`: synthetic method development; positive clock and negative controls.
* `PREFLIGHT_WITH_A064.json`: identical synthetic method plus upstream audit.
* `A064-v0.3.0_results.json`: numerical operator and wavepacket audit; **not** a physical PKLSA clock.

The SHA-256 values of all three datasets are verified by the A068 scientific pipeline. Synthetic controls are not independent physical providers.

## Gate semantics

* G0 = frozen pinned runtime integrity (only official runner can set PASS)
* G1 = three immutable audit inputs pass SHA-256 validation; may PASS
* G2 = synthetic positive, rigid-rotation null, beating null, and upstream audit consistency; may PASS
* G3 = physical PKLSA clock qualification; **UNRESOLVED**, even if an optional NPZ produces a coherent numerical screen
* G4 = independent held-out Euler/Floquet frequency; pending G3
* G5 = strict C++ FP64; pending G4
* G6 = Arc/SYCL FP32/DD32 screening; pending G5 (DD32 not IEEE FP64)
* G7 = true cross-provider independent replication; pending G6
* G8 = material topology/core/time/space mechanism; pending G7
* G9 = reveal; only official runner can authorize, blocked by unresolved science

The simulator / field processing in `experiment/phaseclock.py` is the **unchanged A068 v0.1.0 method source**; no frequencies or SST time-dilation laws are imposed. The new `experiment/pipeline.py` holds the v1.0.8 gate bridge and exact source checks. An optional `data/PKLSA_DYNAMICS.npz` can be analyzed as **development diagnostic only**; registering a new physical source with blinded discovery, provider group and fixed core/mesh/time thresholds requires a new source-qualified frozen campaign.

## v1.0.8 export retention

A new BASIC/FULL/CERTIFY run archives the existing `*-outputs` tree under its previous run ID instead of replacing it. Both blind zip and blind report PDF carry the new run ID. Do **not** manually rename v0.1.0 outputs or reuse their blinded commitment values.

## Source status

v1.0.8 was located on connected Google Drive as a **local validated candidate**, not necessarily production-qualified on Windows/Arc. This package is not proof that framework CPU/SYCL target-machine verification has run. Framework v1.0.7 remains the independently frozen ancestor.

## Supplementary report

`overlay/report/FALSIFIER_REPORT.tex` is the exact scientific pre-freeze report; `FALSIFIER_REPORT.pdf` in the ZIP is an independently compiled **preview only**, not the framework-produced run-identified report.
