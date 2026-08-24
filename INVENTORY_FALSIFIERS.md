# Falsifier inventory

Generated from `falsifier_registry.yaml` (schema v1) on 2026-08-24 16:41 UTC.
Regenerate: `python scripts/render_falsifier_inventory.py --write`.

## Status legend

| Symbol | Meaning |
|---|---|
| 🔴 | Physics FAIL or strong falsification signal |
| 🟢 | Physics PASS (blind gate cleared) |
| 🟠 | Physics INDETERMINATE — numerics may pass |
| 🟡 | Physics weak / partial signal |
| ⚪ | Physics UNTESTED |
| 🔧 | REFERENCE_ONLY — metrology / QA, not a physics claim |

**Physics vs numerics:** `physics_status` (PASS | FAIL | INDETERMINATE | UNTESTED | REFERENCE_ONLY) is independent of `numerics_status` (PASS | FAIL | NOT_RUN | N/A). A green pytest run never implies a physics PASS.

## Hypothesis roadmap

Core hypothesis rows (28) plus 17 registry-only hypotheses.

| # | ID | Status | ★ | Central question | Pack (latest) | Physics | Numerics |
|---:|---|:---:|:---:|---|---|:---:|:---:|
| 1 | SST-FALS-I-01 | 🔴🟠 | ★★★★★ | Does (ωτ) causally control knot stability? | Phase-Feedback-Delay / Swirl-Clock Knot Stability (v0.2.0) | INDETERMINATE | PASS |
| 2 | SST-FALS-I-02 | 🔴🟠 | ★★★★★ | Does frozen internal thread stabilise the knot? | Axial-Vortex-Bundle (B0–B8) Stability (v0.3.0) | INDETERMINATE | PASS |
| 3 | SST-FALS-I-03 | 🟠 | ★★★★☆ | Does finite-core mode coupling stabilise the knot? | Finite-Core m=2 Swirl-Clock Stability (v0.1.2) | INDETERMINATE | PASS |
| 4 | SST-FALS-I-04 | 🟡 | ★★★★☆ | Is Fourier-series dynamics better than ideal geometry? | Fourier vs Ideal Knot Dynamics (v0.1.1) | INDETERMINATE | PASS |
| 5 | SST-FALS-I-05 | 🔴🟠 | ★★★★★ | Is there an intrinsic trefoil lobe restoring point? | Self-Confinement / Trefoil Lobe Stability (v0.3.0) | INDETERMINATE | PASS |
| 6 | SST-FALS-I-06 | 🔴🟠 | ★★★★★ | Do RPOs with stable Floquet multipliers exist across topologies? | MultiTopology RPO / Floquet Stability (v0.4.8) | INDETERMINATE | PASS |
| 7 | SST-FALS-I-07 | 🟠 | ★★★★☆ | Is a threaded hole dynamically different from a geometric hole? | Threaded Hole / Separatrix Dynamics (v0.3.0) | INDETERMINATE | PASS |
| 8 | SST-FALS-II-01 | 🟠 | ★★★★☆ | Does chiral Kelvin core localise swirl energy? | Chiral Kelvin Core Localization (v0.1.3.1) | INDETERMINATE | PASS |
| 9 | SST-FALS-II-03 | 🟠 | ★★★★☆ | Is swirl-clock visible in spectral data? | v↺ Spectral Swirl-Clock Signature (v0.2.1) | INDETERMINATE | PASS |
| 10 | SST-FALS-II-04 | 🟠 | ★★★★☆ | Does local thread texture add physical structure? | Local Thread Texture + Boost (v0.3.0) | INDETERMINATE | PASS |
| 11 | SST-FALS-II-05 | 🟡 | ★★★☆☆ | Do Helmholtz vortex gates preserve transport invariants? | Helmholtz Vortex Gates / Transport Invariants (v0.1.1) | INDETERMINATE | PASS |
| 12 | SST-FALS-III-01 | 🟠 | ★★★★☆ | Does pressure-Poisson closure hold? | 7-Article Closure / Pressure-Poisson (v0.1.2) | INDETERMINATE | PASS |
| 13 | SST-FALS-III-02 | 🔴🟠 | ★★★★★ | Does emergent metric yield Poisson with 1/r monopole gates? | Einstein Emergent Metric + Poisson (v0.1.1) | INDETERMINATE | NOT_RUN |
| 14 | SST-FALS-III-04 | 🟡 | ★★★☆☆ | Does Maxwell 3 physical-lines closure hold? | Maxwell 3 Physical Lines Closure (v0.2.0) | INDETERMINATE | PASS |
| 15 | SST-FALS-III-05 | 🟡 | ★★★☆☆ | Does Maxwell 4 falsifier reject null field models? | Maxwell 4 Falsifier (v0.2.0) | INDETERMINATE | PASS |
| 16 | SST-FALS-III-06 | 🟡 | ★★★☆☆ | Does reciprocal-figures closure hold for Maxwell 5? | Maxwell 5 Reciprocal Figures (v0.2.0) | INDETERMINATE | PASS |
| 17 | SST-FALS-IV-01 | 🟡 | ★★★☆☆ | Does Maxwell 1 kinetic-energy closure hold? | Maxwell 1 Kinetic Energy Closure (v0.3.1) | INDETERMINATE | PASS |
| 18 | SST-FALS-IV-02 | 🟡 | ★★★☆☆ | Does Maxwell 2 dynamical-field energy closure hold? | Maxwell 2 Dynamical Field Energy (v0.2.0) | INDETERMINATE | PASS |
| 19 | SST-FALS-IV-03 | 🟡 | ★★★☆☆ | Does Kelvin–Joule transient energy accounting close? | Kelvin–Joule Transient Energy (v0.1.1) | INDETERMINATE | PASS |
| 20 | SST-FALS-IV-04 | ⚪ | ★★★☆☆ | Does the six-source blind falsifier reject spurious routes? | Six-Source Blind Energy Falsifier (v0.1.0) | UNTESTED | PASS |
| 21 | SST-FALS-V-01 | 🟠 | ★★★★☆ | Does boost invariance control catch preferred-frame artefacts? | Preferred-Frame / Boost Invariance Control (v0.1.1) | INDETERMINATE | PASS |
| 22 | SST-FALS-V-02 | 🟡 | ★★★☆☆ | Are results robust across ideal link topologies? | Ideal Links Comprehensive Topology Robustness (v0.4.0) | INDETERMINATE | PASS |
| 23 | SST-FALS-V-03 | 🔧 | ★★★☆☆ | Does SST21D qualify knot-order ranking? | SST21D Knot-Order Pipeline Qualification (v0.2.0) | REFERENCE_ONLY | PASS |
| 24 | SST-FALS-V-04 | 🔧 | ★★☆☆☆ | Does KnotPlot multi-dynamics matrix generate qualified candidates? | KnotPlot Multi-Dynamics Matrix Generator (v0.1.6) | REFERENCE_ONLY | PASS |
| 25 | SST-FALS-V-05 | 🔧 | ★★☆☆☆ | Does the parameter atlas catch campaign failures? | KnotPlot Parameter Atlas QA (v0.3.0) | REFERENCE_ONLY | PASS |
| 26 | SST-FALS-V-06 | 🔧 | ★★☆☆☆ | Are trefoil seeds qualified for falsifier runs? | KnotPlot Trefoil Seed Campaign (v0.1.3) | REFERENCE_ONLY | PASS |
| 27 | SST-FALS-V-07 | 🔧 | ★★☆☆☆ | Does certification catch missing KnotPlot parameters? | KnotPlot MissingParameter Certification (v0.2.0) | REFERENCE_ONLY | PASS |
| 28 | SST-FALS-V-08 | 🟡 | ★★★☆☆ | Does the ropelength gate qualify geometry? | Counterpulley α / Ropelength Geometry Gate (v0.5.0) | INDETERMINATE | PASS |

### Additional hypotheses (not in original 28-row table)

| ID | Family | Status | Central question | Physics | Numerics |
|---|:---:|:---:|:---|:---:|:---:|
| SST-FALS-I-06b | I | ⚪ | Does the adaptive RPO ladder converge to a stable orbit? | UNTESTED | PASS |
| SST-FALS-I-08 | I | ⚪ | Does the finite-core c2 falsifier decide secondary stability? | UNTESTED | NOT_RUN |
| SST-FALS-II-02 | II | 🟡 | Do evanescent core modes gate Kelvin transport? | INDETERMINATE | PASS |
| SST-FALS-II-06 | II | ⚪ | Does material-phase EFT close holonomy observables? | UNTESTED | PASS |
| SST-FALS-III-03 | III | ⚪ | Does the blind Einstein falsifier reject null models? | UNTESTED | NOT_RUN |
| SST-FALS-IV-05 | IV | ⚪ | Does contact billiard close the hydrodynamic energy adjunct? | UNTESTED | PASS |
| SST-FALS-V-09 | V | 🔧 | Does the minimal harness establish a reproducible baseline? | REFERENCE_ONLY | PASS |
| SST-FALS-V-10 | V | 🔧 | Does the Sutcliffe HSS gate reject infeasible candidates? | REFERENCE_ONLY | PASS |
| SST-FALS-V-11 | V | ⚪ | Does the nonfit harness control spurious prediction routes? | UNTESTED | NOT_RUN |
| SST-FALS-V-12 | V | 🟡 | Does Route-B v3 reject synthetic BEM nulls? | INDETERMINATE | PASS |
| SST-FALS-V-13 | V | 🟡 | Does Route-B v3.1 reject synthetic BEM nulls? | INDETERMINATE | PASS |
| SST-FALS-V-14 | V | 🟡 | Does Route-B v3.2 reject synthetic BEM nulls? | INDETERMINATE | PASS |
| SST-FALS-V-15 | V | 🟡 | Does Route-B v3.3 reject synthetic BEM nulls? | INDETERMINATE | PASS |
| SST-FALS-V-16 | V | 🟡 | Does Route-B v4 reject synthetic BEM nulls? | INDETERMINATE | PASS |
| SST-FALS-V-17 | V | 🟡 | Does Route-B v5 reject synthetic BEM nulls? | INDETERMINATE | PASS |
| SST-FALS-V-18 | V | 🟡 | Does Stecklov BEM control reject synthetic nulls? | INDETERMINATE | PASS |
| SST-FALS-V-19 | V | ⚪ | Does the dark-knot Rayleigh gate qualify candidates? | UNTESTED | NOT_RUN |

## Master registry

**45** entries — single source of truth in [`falsifier_registry.yaml`](falsifier_registry.yaml).

| ID | Name | Version | Family | Blind | Physics | Numerics | Next test |
|---|---|:---:|:---:|:---:|:---:|:---:|---|
| SST-FALS-I-01 | Phase-Feedback-Delay / Swirl-Clock Knot Stability | v0.2.0 | I | yes | INDETERMINATE | PASS | independent replication on held-out atlas shard |
| SST-FALS-I-02 | Axial-Vortex-Bundle (B0–B8) Stability | v0.3.0 | I | yes | INDETERMINATE | PASS | held-out bundle shard + native parity audit |
| SST-FALS-I-03 | Finite-Core m=2 Swirl-Clock Stability | v0.1.2 | I | yes | INDETERMINATE | PASS | independent m=2 replication |
| SST-FALS-I-04 | Fourier vs Ideal Knot Dynamics | v0.1.1 | I | no | INDETERMINATE | PASS | blind replication on new trefoil seeds |
| SST-FALS-I-05 | Self-Confinement / Trefoil Lobe Stability | v0.3.0 | I | yes | INDETERMINATE | PASS | held-out lobe perturbation shard |
| SST-FALS-I-06 | MultiTopology RPO / Floquet Stability | v0.4.8 | I | yes | INDETERMINATE | PASS | expand topology panel + blind seal |
| SST-FALS-I-06b | Adaptive Period-Aware RPO Ladder | v0.1.0 | I | yes | UNTESTED | PASS | blind ladder campaign on held-out topology |
| SST-FALS-I-07 | Threaded Hole / Separatrix Dynamics | v0.3.0 | I | yes | INDETERMINATE | PASS | blind separatrix replication |
| SST-FALS-I-08 | Finite-Core c2 Falsifier (Archive) | v0.1.0 | I | yes | UNTESTED | NOT_RUN | unpack archive + run c2 campaign |
| SST-FALS-II-01 | Chiral Kelvin Core Localization | v0.1.3.1 | II | yes | INDETERMINATE | PASS | held-out chiral core shard |
| SST-FALS-II-02 | Kelvin–Kirchhoff Evanescent Core Modes | v0.1.1 | II | yes | INDETERMINATE | PASS | independent evanescent gate replication |
| SST-FALS-II-03 | v↺ Spectral Swirl-Clock Signature | v0.2.1 | II | yes | INDETERMINATE | PASS | blind spectral replication |
| SST-FALS-II-04 | Local Thread Texture + Boost | v0.3.0 | II | yes | INDETERMINATE | PASS | held-out texture shard |
| SST-FALS-II-05 | Helmholtz Vortex Gates / Transport Invariants | v0.1.1 | II | yes | INDETERMINATE | PASS | blind Helmholtz replication |
| SST-FALS-II-06 | Material Phase EFT / Holonomy Closure | v0.1.1 | II | yes | UNTESTED | PASS | blind EFT campaign |
| SST-FALS-III-01 | 7-Article Closure / Pressure-Poisson | v0.1.2 | III | yes | INDETERMINATE | PASS | blind Poisson replication |
| SST-FALS-III-02 | Einstein Emergent Metric + Poisson | v0.1.1 | III | yes | INDETERMINATE | NOT_RUN | unpack archive + run blind monopole gate |
| SST-FALS-III-03 | Einstein Blind Falsifier | v0.1.0 | III | yes | UNTESTED | NOT_RUN | run blind Einstein pack from archive |
| SST-FALS-III-04 | Maxwell 3 Physical Lines Closure | v0.2.0 | III | yes | INDETERMINATE | PASS | blind Maxwell 3 replication |
| SST-FALS-III-05 | Maxwell 4 Falsifier | v0.2.0 | III | yes | INDETERMINATE | PASS | held-out Maxwell 4 shard |
| SST-FALS-III-06 | Maxwell 5 Reciprocal Figures | v0.2.0 | III | yes | INDETERMINATE | PASS | blind Maxwell 5 replication |
| SST-FALS-IV-01 | Maxwell 1 Kinetic Energy Closure | v0.3.1 | IV | yes | INDETERMINATE | PASS | blind Maxwell 1 replication |
| SST-FALS-IV-02 | Maxwell 2 Dynamical Field Energy | v0.2.0 | IV | yes | INDETERMINATE | PASS | blind Maxwell 2 replication |
| SST-FALS-IV-03 | Kelvin–Joule Transient Energy | v0.1.1 | IV | yes | INDETERMINATE | PASS | held-out Kelvin–Joule shard |
| SST-FALS-IV-04 | Six-Source Blind Energy Falsifier | v0.1.0 | IV | yes | UNTESTED | PASS | run six-source blind campaign |
| SST-FALS-IV-05 | Contact Billiard Hydrodynamic Closure | v0.2.0 | IV | no | UNTESTED | PASS | blind billiard campaign |
| SST-FALS-V-01 | Preferred-Frame / Boost Invariance Control | v0.1.1 | V | yes | INDETERMINATE | PASS | held-out boost shard |
| SST-FALS-V-02 | Ideal Links Comprehensive Topology Robustness | v0.4.0 | V | no | INDETERMINATE | PASS | expand ideal-link panel |
| SST-FALS-V-03 | SST21D Knot-Order Pipeline Qualification | v0.2.0 | V | no | REFERENCE_ONLY | PASS | blind order-qualification on held-out knots |
| SST-FALS-V-04 | KnotPlot Multi-Dynamics Matrix Generator | v0.1.6 | V | no | REFERENCE_ONLY | PASS | expand dynamics matrix panel |
| SST-FALS-V-05 | KnotPlot Parameter Atlas QA | v0.3.0 | V | no | REFERENCE_ONLY | PASS | atlas shard on new topology |
| SST-FALS-V-06 | KnotPlot Trefoil Seed Campaign | v0.1.3 | V | no | REFERENCE_ONLY | PASS | held-out trefoil seed shard |
| SST-FALS-V-07 | KnotPlot MissingParameter Certification | v0.2.0 | V | no | REFERENCE_ONLY | PASS | expand command certification panel |
| SST-FALS-V-08 | Counterpulley α / Ropelength Geometry Gate | v0.5.0 | V | no | INDETERMINATE | PASS | held-out ropelength shard |
| SST-FALS-V-09 | Minimal Falsification Harness Baseline | v0.3.0 | V | no | REFERENCE_ONLY | PASS | extend harness coverage |
| SST-FALS-V-10 | Sutcliffe HSS Feasibility Gate | v0.1.0 | V | no | REFERENCE_ONLY | PASS | expand HSS panel |
| SST-FALS-V-11 | Nonfit Prediction Harness (Routes Control) | v0.8.19 | V | yes | UNTESTED | NOT_RUN | unpack archive + run nonfit harness |
| SST-FALS-V-12 | Route-B BEM Falsifier v3 | v3 | V | yes | INDETERMINATE | PASS | held-out BEM v3 shard |
| SST-FALS-V-13 | Route-B BEM Falsifier v3.1 | v3.1 | V | yes | INDETERMINATE | PASS | held-out BEM v3.1 shard |
| SST-FALS-V-14 | Route-B BEM Falsifier v3.2 | v3.2 | V | yes | INDETERMINATE | PASS | held-out BEM v3.2 shard |
| SST-FALS-V-15 | Route-B BEM Falsifier v3.3 | v3.3 | V | yes | INDETERMINATE | PASS | held-out BEM v3.3 shard |
| SST-FALS-V-16 | Route-B BEM Falsifier v4 | v4 | V | yes | INDETERMINATE | PASS | held-out BEM v4 shard |
| SST-FALS-V-17 | Route-B BEM Falsifier v5 | v5 | V | yes | INDETERMINATE | PASS | held-out BEM v5 shard |
| SST-FALS-V-18 | Route-B Stecklov BEM Control | v5.1 | V | yes | INDETERMINATE | PASS | held-out Stecklov shard |
| SST-FALS-V-19 | Dark-Knot Rayleigh Feasibility (Archive) | v1.2 | V | no | UNTESTED | NOT_RUN | unpack archive + run Rayleigh gate |

## Per-family overview

### Family I — Dynamic particle stability

9 entries.

| ID | Version | Blind | Physics | Numerics |
|---|:---:|:---:|:---:|:---:|
| SST-FALS-I-01 | v0.2.0 | yes | INDETERMINATE | PASS |
| SST-FALS-I-02 | v0.3.0 | yes | INDETERMINATE | PASS |
| SST-FALS-I-03 | v0.1.2 | yes | INDETERMINATE | PASS |
| SST-FALS-I-04 | v0.1.1 | no | INDETERMINATE | PASS |
| SST-FALS-I-05 | v0.3.0 | yes | INDETERMINATE | PASS |
| SST-FALS-I-06 | v0.4.8 | yes | INDETERMINATE | PASS |
| SST-FALS-I-06b | v0.1.0 | yes | UNTESTED | PASS |
| SST-FALS-I-07 | v0.3.0 | yes | INDETERMINATE | PASS |
| SST-FALS-I-08 | v0.1.0 | yes | UNTESTED | NOT_RUN |

### Family II — Local mode / field structure

6 entries.

| ID | Version | Blind | Physics | Numerics |
|---|:---:|:---:|:---:|:---:|
| SST-FALS-II-01 | v0.1.3.1 | yes | INDETERMINATE | PASS |
| SST-FALS-II-02 | v0.1.1 | yes | INDETERMINATE | PASS |
| SST-FALS-II-03 | v0.2.1 | yes | INDETERMINATE | PASS |
| SST-FALS-II-04 | v0.3.0 | yes | INDETERMINATE | PASS |
| SST-FALS-II-05 | v0.1.1 | yes | INDETERMINATE | PASS |
| SST-FALS-II-06 | v0.1.1 | yes | UNTESTED | PASS |

### Family III — Gravity / pressure / emergent fields

6 entries.

| ID | Version | Blind | Physics | Numerics |
|---|:---:|:---:|:---:|:---:|
| SST-FALS-III-01 | v0.1.2 | yes | INDETERMINATE | PASS |
| SST-FALS-III-02 | v0.1.1 | yes | INDETERMINATE | NOT_RUN |
| SST-FALS-III-03 | v0.1.0 | yes | UNTESTED | NOT_RUN |
| SST-FALS-III-04 | v0.2.0 | yes | INDETERMINATE | PASS |
| SST-FALS-III-05 | v0.2.0 | yes | INDETERMINATE | PASS |
| SST-FALS-III-06 | v0.2.0 | yes | INDETERMINATE | PASS |

### Family IV — Energy / thermodynamics / Maxwell–Kelvin

5 entries.

| ID | Version | Blind | Physics | Numerics |
|---|:---:|:---:|:---:|:---:|
| SST-FALS-IV-01 | v0.3.1 | yes | INDETERMINATE | PASS |
| SST-FALS-IV-02 | v0.2.0 | yes | INDETERMINATE | PASS |
| SST-FALS-IV-03 | v0.1.1 | yes | INDETERMINATE | PASS |
| SST-FALS-IV-04 | v0.1.0 | yes | UNTESTED | PASS |
| SST-FALS-IV-05 | v0.2.0 | no | UNTESTED | PASS |

### Family V — Anti-self-deception / metrology

19 entries.

| ID | Version | Blind | Physics | Numerics |
|---|:---:|:---:|:---:|:---:|
| SST-FALS-V-01 | v0.1.1 | yes | INDETERMINATE | PASS |
| SST-FALS-V-02 | v0.4.0 | no | INDETERMINATE | PASS |
| SST-FALS-V-03 | v0.2.0 | no | REFERENCE_ONLY | PASS |
| SST-FALS-V-04 | v0.1.6 | no | REFERENCE_ONLY | PASS |
| SST-FALS-V-05 | v0.3.0 | no | REFERENCE_ONLY | PASS |
| SST-FALS-V-06 | v0.1.3 | no | REFERENCE_ONLY | PASS |
| SST-FALS-V-07 | v0.2.0 | no | REFERENCE_ONLY | PASS |
| SST-FALS-V-08 | v0.5.0 | no | INDETERMINATE | PASS |
| SST-FALS-V-09 | v0.3.0 | no | REFERENCE_ONLY | PASS |
| SST-FALS-V-10 | v0.1.0 | no | REFERENCE_ONLY | PASS |
| SST-FALS-V-11 | v0.8.19 | yes | UNTESTED | NOT_RUN |
| SST-FALS-V-12 | v3 | yes | INDETERMINATE | PASS |
| SST-FALS-V-13 | v3.1 | yes | INDETERMINATE | PASS |
| SST-FALS-V-14 | v3.2 | yes | INDETERMINATE | PASS |
| SST-FALS-V-15 | v3.3 | yes | INDETERMINATE | PASS |
| SST-FALS-V-16 | v4 | yes | INDETERMINATE | PASS |
| SST-FALS-V-17 | v5 | yes | INDETERMINATE | PASS |
| SST-FALS-V-18 | v5.1 | yes | INDETERMINATE | PASS |
| SST-FALS-V-19 | v1.2 | no | UNTESTED | NOT_RUN |

## Latest pack paths

<details>
<summary>Resolved working trees and archive zips</summary>

| ID | Working tree | Archive zip |
|---|---|---|
| SST-FALS-I-01 | SST_Phase_Feedback_Delay_Knot_Stability/SST_Phase_Feedback_Delay_Knot_Stability_Blind_Falsifier_v0.2.0 | Restore_Archives/Falsifiers/SST_Phase_Feedback_Delay_Knot_Stability_Blind_Falsifier_v0.2.0.zip |
| SST-FALS-I-02 | SST_dimensionless_dynamic_predictions/SST_dimensionless_dynamic_predictions_v0.3.0_axial_vortex_bundle | Restore_Archives/Dimensionless/SST_dimensionless_dynamic_predictions_v0.3.0_axial_vortex_bundle.zip |
| SST-FALS-I-03 | SST_Finite_Core_Axial_Toroidal_Phase_Delay/SST_Finite_Core_Axial_Toroidal_Phase_Delay_Blind_Falsifier_v0.1.2 | Restore_Archives/Falsifiers/SST_Finite_Core_Axial_Toroidal_Phase_Delay_Blind_Falsifier_v0.1.2.zip |
| SST-FALS-I-04 | SST_Fourier_vs_Ideal_Blind_Falsifier/SST_Fourier_vs_Ideal_Blind_Falsifier_v0.1.1 | Restore_Archives/Falsifiers/SST_Fourier_vs_Ideal_Blind_Falsifier_v0.1.1.zip |
| SST-FALS-I-05 | SST_Trefoil_Lobe_Orientation_Blind_Falsifier/SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.3.0 | Restore_Archives/Falsifiers/SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.3.0.zip |
| SST-FALS-I-06 | SST_Trefoil_Lobe_Orientation_Blind_Falsifier/SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact | Restore_Archives/Falsifiers/SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact.zip |
| SST-FALS-I-06b | SST_Trefoil_Lobe_Orientation_Blind_Falsifier/SST_Adaptive_Period_Aware_RPO_Multiple_Shooting_Floquet_Blind_Falsifier_v0.1.0 | Restore_Archives/Falsifiers/SST_Adaptive_Period_Aware_RPO_Multiple_Shooting_Floquet_Blind_Falsifier_v0.1.0.zip |
| SST-FALS-I-07 | SST_Threaded_Hole_Substrate_Blind_Falsifier_v0.1.0/SST_Threaded_Hole_Substrate_Blind_Falsifier_v0.3.0 | Restore_Archives/Falsifiers/SST_Threaded_Hole_Substrate_Blind_Falsifier_v0.3.0.zip |
| SST-FALS-I-08 | — | Restore_Archives/DeriveConstants/SST_finite_core_c2_falsifier_v0.1.0.zip |
| SST-FALS-II-01 | SST_Chiral-Kelvin-Mode/SST_chiral_kelvin_falsification_v0.1.3.1 | — |
| SST-FALS-II-02 | SST_Kelvin_Floquet/Kelvin_Kirchhoff_SST_Falsifier_v0.1.1 | Restore_Archives/KelvinFloquet/Kelvin_Kirchhoff_SST_Falsifier_v0.1.1.zip |
| SST-FALS-II-03 | SST_vArrow_Spectral_Blind_Falsifier/SST_vArrow_Spectral_Blind_Falsifier_v0.2.1 | Restore_Archives/Falsifiers/SST_vArrow_Spectral_Blind_Falsifier_v0.2.1.zip |
| SST-FALS-II-04 | SST_Threaded_Hole_Substrate_Blind_Falsifier_v0.1.0/SST_Local_Thread_Texture_Boost_Invariance_Blind_Falsifier_v0.3.0 | Restore_Archives/Falsifiers/SST_Local_Thread_Texture_Boost_Invariance_Blind_Falsifier_v0.3.0.zip |
| SST-FALS-II-05 | SST_Helmholtz/Helmholtz_SST_Vortex_Gates_Falsifier_v0.1.1 | Restore_Archives/Falsifiers/Helmholtz_SST_Vortex_Gates_Falsifier_v0.1.1.zip |
| SST-FALS-II-06 | SST_Material_Phase_EFT/SST_Material_Phase_EFT_Falsifier_v0.1.1 | Restore_Archives/Falsifiers/SST_Material_Phase_EFT_Falsifier_v0.1.1.zip |
| SST-FALS-III-01 | SST_7Article_Closure_Holonomy/SST_7Article_Closure_Holonomy_Blind_Falsifier_v0.1.2 | Restore_Archives/Falsifiers/SST_7Article_Closure_Holonomy_Blind_Falsifier_v0.1.2.zip |
| SST-FALS-III-02 | SST_Einstein/Einstein_SST_Emergent_Metric_Poisson_Closure_Gates_v0.1.1 | Restore_Archives/Falsifiers/Einstein_SST_Emergent_Metric_Poisson_Closure_Gates_v0.1.1.zip |
| SST-FALS-III-03 | SST_Einstein/Einstein_SST_Blind_Falsifier_v0.1.0 | Restore_Archives/Falsifiers/Einstein_SST_Blind_Falsifier_v0.1.0.zip |
| SST-FALS-III-04 | SST_Maxwell/3_Maxwell_SST_Physical_Lines_Falsifier_v0.2.0 | Restore_Archives/Maxwell/3_Maxwell_SST_Physical_Lines_Falsifier_v0.2.0.zip |
| SST-FALS-III-05 | SST_Maxwell/4_SST_Maxwell_Falsifier_v0.2.0 | Restore_Archives/Maxwell/4_SST_Maxwell_Falsifier_v0.2.0.zip |
| SST-FALS-III-06 | SST_Maxwell/5_Maxwell_SST_Reciprocal_Falsifier_v0.2.0 | Restore_Archives/Maxwell/5_Maxwell_SST_Reciprocal_Falsifier_v0.2.0.zip |
| SST-FALS-IV-01 | SST_Maxwell/1_Maxwell_SST_Kinetic_Falsifier_v0.3.1 | Restore_Archives/Maxwell/1_Maxwell_SST_Kinetic_Falsifier_v0.3.1.zip |
| SST-FALS-IV-02 | SST_Maxwell/2_Maxwell_SST_Dynamical_Field_Closure_Falsifier_v0.2.0 | Restore_Archives/Maxwell/2_Maxwell_SST_Dynamical_Field_Closure_Falsifier_v0.2.0.zip |
| SST-FALS-IV-03 | — | Restore_Archives/KelvinFloquet/Kelvin_Joule_SST_Transient_Energy_Falsifier_v0.1.1.zip |
| SST-FALS-IV-04 | SST_6Source_Blind_Falsifier_v0.1.0/SST_6Source_Blind_Falsifier_v0.1.0 | Restore_Archives/Falsifiers/SST_6Source_Blind_Falsifier_v0.1.0.zip |
| SST-FALS-IV-05 | SST_contact_billiard_hydrodynamic_falsifier/SST_contact_billiard_hydrodynamic_falsifier_v0.2.0 | Restore_Archives/ContactBilliard/SST_contact_billiard_hydrodynamic_falsifier_v0.2.0.zip |
| SST-FALS-V-01 | SST_preferred_frame_binary_falsifier/SST_preferred_frame_binary_falsifier_v0.1.1 | Restore_Archives/Falsifiers/SST_preferred_frame_binary_falsifier_v0.1.1(1).zip |
| SST-FALS-V-02 | SST_ideal_links/SST_ideal_links_comprehensive_test_suite_v0.4.0-alpha.1 | Restore_Archives/IdealLinks/SST_ideal_links_comprehensive_test_suite_v0.4.0-alpha.1.zip |
| SST-FALS-V-03 | SST21D_knot_order_pipeline/SST21D_knot_order_pipeline_v0.2.0 | Restore_Archives/SST21D/SST21D_knot_order_pipeline_v0.2.0.zip |
| SST-FALS-V-04 | KnotPlot/KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.6 | Restore_Archives/KnotPlot/KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.6_CLEAN_FULL.zip |
| SST-FALS-V-05 | KnotPlot/KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v0.3.0 | Restore_Archives/KnotPlot/KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v0.3.0.zip |
| SST-FALS-V-06 | KnotPlot/KnotPlot_3p1_Trefoil_Seed_Campaign_v0.1.3 | Restore_Archives/Trefoil/KnotPlot_3p1_Trefoil_Seed_Campaign_v0.1.3.zip |
| SST-FALS-V-07 | KnotPlot/KnotPlot_3p1_MissingParameter_Command_Certification_v0.2.0 | Restore_Archives/KnotPlot/KnotPlot_3p1_MissingParameter_Command_Certification_v0.2.0.zip |
| SST-FALS-V-08 | SST_counterpulley_alpha_falsifier/SST_counterpulley_alpha_falsifier_v0.5.0 | Restore_Archives/Falsifiers/SST_counterpulley_alpha_falsifier_v0.5.0.zip |
| SST-FALS-V-09 | SST_minimal_falsification_harness/SST_minimal_falsification_harness_v0.3.0 | Restore_Archives/Falsifiers/SST_minimal_falsification_harness_v0.3.0_calibration.zip |
| SST-FALS-V-10 | SST_Sutcliffe_HSS_feasibility_gate/Sutcliffe_HSS_feasibility_gate_v0.1.0 | Restore_Archives/Falsifiers/Sutcliffe_HSS_feasibility_gate_v0.1.0.zip |
| SST-FALS-V-11 | SST_v0_8_19_routes_research/sst_nonfit_prediction_harness_v0_8_19 | Restore_Archives/Routes_v0819/sst_nonfit_prediction_harness_v0.8.19_draft1.zip |
| SST-FALS-V-12 | SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v3 | — |
| SST-FALS-V-13 | SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v3_1 | — |
| SST-FALS-V-14 | SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v3_2 | — |
| SST-FALS-V-15 | SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v3_3 | — |
| SST-FALS-V-16 | SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v4 | — |
| SST-FALS-V-17 | SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v5 | — |
| SST-FALS-V-18 | SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_stecklov | — |
| SST-FALS-V-19 | — | Restore_Archives/Falsifiers/SST_dark_knot_rayleigh_harness_v1_2_taxonomy (1).zip |

</details>

## Unregistered packs (CI warning)

20 working-tree pack(s) match falsifier heuristics but no registry glob:

- `SST_Kelvin_Floquet/SST_Kelvin_Floquet_Workbench_cpp_pybind_v0.1.0`
- `SST_Kelvin_Floquet/SST_Kelvin_Floquet_Workbench_cpp_pybind_v0.1.1`
- `SST_Maxwell/3_SST_Maxwell_Blind_Falsifier_v0.1.0`
- `SST_dimensionless_dynamic_predictions/SST_dimensionless_dynamic_predictions_v0.1.0`
- `SST_dimensionless_dynamic_predictions/SST_dimensionless_dynamic_predictions_v0.2.0_infinite_background_vortex`
- `SST_dimensionless_dynamic_predictions/SST_dimensionless_dynamic_predictions_v0.4.0_iso_gamma_area_dynamic_clock`
- `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v10`
- `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v11`
- `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v12`
- `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v13`
- `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v14`
- `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v15`
- `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v16`
- `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v17`
- `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v18`
- `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v19`
- `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v6`
- `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v7`
- `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v8`
- `SST_routeB_RT_bem_research/SST_routeB_RT_bem_research_v9`
