# E012 PKLSA Dynamic Eigenmode Extractor v0.1.0

Trefoil-first bridge from the **E011 SKLSA STATIC_READY seed contract** to the
existing **C006 Kelvin/Floquet Workbench v0.3.0** dynamics.  E012 does not copy or
redefine the C006 regularized Biot–Savart solver.  It discovers C006 in the
SST-Workbench, imports the published C006 API, runs a frozen local Kelvin-spectrum
campaign on an E011-qualified `3_1` seed, tracks spectral branches across resolution,
and emits a machine-readable dynamical branch.

## Scientific role

The intended chain is

```text
E010 PKLSA geometry/source/topology qualification
        ↓
E011 SKLSA STATIC_READY seed selection
        ↓
E012 dynamic eigenmode extraction
        ↓
A052 link-field / photon dispersion closure
        ↓
A044 GRB 221009A transparency/dispersion falsifier
```

E012-v0.1.0 is deliberately **not** a photon-identification module and it is not a
GRB-fitting module.  It never imports A044 observational targets.

The central output is a dimensionless, provenance-qualified branch

\[
\hat k_m = \frac{2\pi m D}{L}, \qquad
\hat\omega_m = \operatorname{Im}\hat\lambda_m ,
\]

where \(D\) and \(L\) are the E011/Gilbert source scales and
\(\hat\lambda_m\) is extracted by the existing C006 projected temporal
Biot–Savart generator.  The corresponding dimensional mapping, if and only if an
independent scale contract is explicitly supplied, is

\[
\Omega_\Gamma=\frac{|\Gamma|}{4\pi D_{\rm phys}^2},
\qquad
k_m = \frac{\hat k_m}{D_{\rm phys}},
\qquad
\omega_m=\Omega_\Gamma\hat\omega_m .
\]

Then

\[
v_g = \frac{d\omega}{dk}
    = \frac{|\Gamma|}{4\pi D_{\rm phys}}
      \frac{d\hat\omega}{d\hat k}.
\]

No value of \(D_{\rm phys}\), photon energy, or \(E_{\rm LIV}\) is inferred by
E012.  Those mappings must come from an independently justified SST contract.

## v0.1.0 scope

* topology: `3_1` only;
* default provider anchor: E011 `gilbert` / AB record `3:1:1`;
* C006 backend: `C006-v0.3.0`;
* local generator: C006 `projected_kelvin_analysis`;
* spectral tracking: C006 `track_spectrum`;
* quick ladder: `N = 24, 32, 40`, modes `m=1..3`;
* full ladder: `N = 40, 56, 72, 88`, modes `m=1..5`;
* regularized line-filament closure inherited from C006:
  `offset/D = 0.25`, `eps/D = 0.10`, `fd_step/D = 2e-5`,
  counter-rotating `+1/-1` circulation in the dimensionless generator,
  channel phase `pi/2`.

These thresholds are copied from C006's frozen v0.3.0 spectral-certification
policy rather than retuned against E012 output.

## What counts as success

E012 separates three claims:

1. `SEED_PROVENANCE_OK` — E011 provides a `STATIC_READY` upstream seed.
2. `DIMENSIONLESS_DYNAMIC_BRANCH_OK` — the C006 local generator resolves at least
   three ordered mode samples and they satisfy the frozen resolution-persistence
   gate.
3. `A052_PHYSICAL_HANDOFF_READY` — additionally requires a separate, approved
   physical-scale and energy-mapping contract.

A successful v0.1.0 run can therefore legitimately finish with

```text
DIMENSIONLESS_DYNAMIC_BRANCH_OK__A052_PHYSICAL_HANDOFF_BLOCKED
```

This is progress beyond A052's current `NO_DYNAMICAL_EIGENMODE_DATA` result, but
it does not yet claim a photon dispersion law.

## Run

From this version directory:

```bat
run_all.cmd C:\workspace\projects\SST-Workbench
```

Force the Python fallback of C006:

```bat
run_all.cmd C:\workspace\projects\SST-Workbench --force-python
```

Full resolution ladder:

```bat
run_all.cmd C:\workspace\projects\SST-Workbench --preset full
```

The runner installs only E012's Python dependencies.  It discovers:

```text
E011_sklsa_selected_knot_link_seed_atlas\E011-v0.3.0
C006_kelvin_floquet_workbench\C006-v0.3.0
```

under `01_research`, so it does not depend on the exact C-pipeline subfolder name.

## Optional physical-scale contract

`configs/physical_scale.template.json` is intentionally disabled.  To request an
A052-ready SI candidate, copy it to `configs/physical_scale.json` and fill every
required field from an independent SST derivation.  In particular:

* `D_m` must map Gilbert/source `D=1` to a physical length;
* `Gamma_m2_s` must be independently justified;
* every selected `mode_m` must have an independently defined `energy_TeV`;
* `derived_without_GRB_target_fit` must remain `true`.

E012 refuses to emit an A052-ready candidate if any of those conditions is absent.

## Principal outputs

```text
outputs/
  E012_RUN_CONTEXT.json
  E011_SELECTED_SEED.json
  C006_PROVENANCE.json
  DYNAMIC_EIGENMODE_LEVELS.json
  DYNAMIC_EIGENBRANCH.json
  GATES.json
  A052_HANDOFF_STATUS.json
  a052_dynamic_candidate.json        # only when the physical contract passes
  report.md
```

`run_all.cmd` also creates a sibling outputs ZIP.

## Interpretation boundary

C006 v0.3.0 calls this spectrum **frozen-local Kelvin-generator** information.
E012 preserves that language.  No true Floquet claim is made unless a separate
RPO/monodromy gate is passed.  A frozen-local mode is not silently relabelled as
a photon.

## References

See `REFERENCES.tex`.
