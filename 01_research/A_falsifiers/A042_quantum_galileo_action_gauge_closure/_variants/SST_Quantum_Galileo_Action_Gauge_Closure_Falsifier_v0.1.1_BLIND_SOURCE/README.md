# SST Quantum Galileo Action–Gauge Closure Falsifier v0.1.1

## Scientific correction relative to v0.1.0

v0.1.0 was genuinely blind with respect to **knot/source identity**, but its near-Planck
SST action scale was not an independent blind discovery of Planck's constant.

The provenance audit shows that the legacy definitions already contain \(\hbar\) upstream.
Consequently,

\[
4\pi^2\rho_{\text{core}}
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}r_c^4=h
\]

is an algebraic echo in that legacy chain.

v0.1.1 fixes the interpretation and protocol.

## Three meanings of blind

### 1. Label blind

The solver does not know whether a carrier is relaxed, shader-derived, or control.

### 2. Target blind

The blind runtime does not contain or read the SI Planck target.

v0.1.1 enforces this and moves the Planck target to a physically separate reveal archive.

### 3. Provenance independent

None of the inputs used to predict an action quantum may contain \(h\) or \(\hbar\) upstream.

**The current legacy SST action relation fails this criterion.**

It is therefore reported only as:

```text
ALGEBRAIC_ECHO_CONTROL
```

and never as SST evidence.

---

# Blind stage

The blind stage works in action units:

\[
\Delta S_{\rm QGI}
=
-\frac13 m g^2T^3.
\]

It independently integrates the laboratory action and the accelerated-frame gauge
boundary term. These gates require no Planck constant.

The legacy SST action number is also computed and sealed, but explicitly tagged as a
dependent control.

---

# Separate reveal protocol

`run_all.cmd` now performs only the STRICT BLIND chain and seals:

```text
..\SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.1-outputs_BLIND.zip
```

Only after that archive exists should the separate `REVEAL_KEY` archive be extracted into
the project.

Then run:

```bat
run_reveal.cmd
```

---

# Experimental QGI route

A genuinely target-blind empirical inference can use measured QGI phase values:

\[
\hbar_{\rm QGI}(T)
=
-\frac{m g^2T^3}{3\Delta\phi_{\rm measured}(T)}.
\]

This requires actual measured/extracted phase values. v0.1.1 does not fabricate synthetic
phase data. If no real phase dataset is supplied, the empirical gate reports:

```text
NOT_RUN_NO_RAW_PHASE_DATA
```

---

# Knot sources

The shader-derived set remains a first-class dataset alongside the relaxed set.

The built-in shader sweep contains 48 trefoil-track candidates and includes exactly:

```text
baseR   = 4.08248290463863
bulge_R = 2.2
z_weave = 3.0
```

No knot-to-QGI phase correction is invented.

The next new-physics step is to derive a provenance-clean action functional from knot/fluid
dynamics itself.

See `PROVENANCE_AUDIT.md`.
