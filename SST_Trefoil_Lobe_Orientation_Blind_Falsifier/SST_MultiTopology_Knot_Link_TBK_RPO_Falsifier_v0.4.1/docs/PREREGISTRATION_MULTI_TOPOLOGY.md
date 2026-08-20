# v0.4.0 Multi-Topology Preregistration

The canonical BASIC and EXTENDED JSON files are the authoritative numerical preregistration.

## Scope

The panel asks whether the local/self-nonlocal/mutual finite-core Biot--Savart dynamics and the generic breathing/torsion/Kelvin perturbation subspace discriminate among unknots, nontrivial knots, unlinks and nontrivial links without introducing a reconnection or hard-core repulsion operator.

## Blinding

Input paths, topology names and source type are hashed and replaced by deterministic blind IDs before scientific scoring. Per-input analysis and gate scores are written under `pre_unblind/` before `unblind_manifest.json` is emitted.

## Core closure

For RidgeRunner data the sidecar `thickness` is the preferred tube-radius estimate. For Fremlin data a curvature/doubly-critical-distance estimator is used. The numerical finite-core radius is

\[
a=0.90\,\Delta_{\rm tube}.
\]

The core event criterion is based on the evolving tube-thickness/core-radius ratio, not on an arbitrary centerline chord distance.

## Generic basis

For each component, the operational basis contains a normal breathing displacement, first-harmonic binormal torsion-sensitive modes, and the Kelvin-like normal/binormal harmonics listed in the config. Rigid translation, rigid rotation and tangential reparameterization are projected out before modal scoring.

This basis is intentionally topology-agnostic. It does not replace the symmetry-adapted trefoil-lobe basis of v0.3.0.

## Links

Multi-component induced velocity includes all self and mutual contributions. Pairwise Gauss linking is evaluated at high resolution before downsampling and is followed throughout short ringdown. No cut/splice/reconnection operation exists in the panel dynamics.

## RPO/Floquet guardrail

Floquet multipliers are computed only if the RPO scan first reaches the minimum excursion and then returns below both the absolute recurrence and return-ratio thresholds. No RPO means `P8 = N/A`, not an instability verdict.
