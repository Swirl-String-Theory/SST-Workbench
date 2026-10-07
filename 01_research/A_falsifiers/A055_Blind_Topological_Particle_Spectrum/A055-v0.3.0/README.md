# A055 Blind Topological Particle Spectrum Falsifier v0.3.0

## Why v0.3.0 exists

A055 v0.2.x treated each knot as a single centerline and constructed an artificial
counter-rotating two-channel realization around it. That is useful as an isolated-knot
control, but it is **not** the three-component nucleon architecture.

A054 already owns the correct compound experiment:

- `U`: three unlinked components;
- `G`: `T(3,3)` / Triple-Gear proxy;
- `B`: Borromean skeleton;
- each component locally decorated by a PKLSA `5_2` or `6_1` carrier via certified
  connected sum in a disjoint insertion ball;
- all mixed `5_2/6_1` slot permutations;
- circulation sectors `+++`, `-++`, `+-+`, `++-`;
- finite-core restoring, coupled Kelvin/torsion modes, nonlinear ringdown, RPO and
  conditional projected relative Floquet.

A055 v0.3.0 therefore **does not implement a second compound solver**. It imports sealed
A054-v0.2.x blind certification as the authoritative C-branch and combines it with the
A055 single-knot S-branch only at the level of preregistered categorical gates.

## Main scientific question

Is counter-propagating/oscillatory structure primarily a property of an isolated local
twist knot, or does it emerge from the linked three-component compound?

The comparison is:

```text
S : isolated 5_2 / 6_1 (and atlas controls)
    -> A055 synthetic two-channel C006 control

C0: U(5_2/6_1, 5_2/6_1, 5_2/6_1)
C1: G(5_2/6_1, 5_2/6_1, 5_2/6_1)
C2: B(5_2/6_1, 5_2/6_1, 5_2/6_1)
    -> authoritative A054 three-component dynamics
```

A054-v0.1.1's discovery result—strong linked `2+1` polarity selection and a small
Triple-Gear `6_1`-opposed tendency—is motivation only. It is not converted into a
v0.3.0 threshold.

## New bookkeeping rule

One failed `(provider,N,m)` cell is now stored as e.g.

```text
NO_OSCILLATORY_PAIR
```

without deleting successful cells for other resolutions or modes. A mode is qualified only
when its complete preregistered resolution ladder survives.

## Compound counter-propagating gate

For an A054 projected spectrum let positive and negative oscillatory frequencies be
\(\omega_+>0\) and \(|\omega_-|>0\). Pair existence requires both signs. The preregistered
symmetry diagnostic is

\[
A_\omega =
\frac{|\omega_+-|\omega_-||}
{\tfrac12(\omega_+ + |\omega_-|)}.
\]

A pair is tagged symmetric when

\[
A_\omega \le 0.25.
\]

This is evaluated for both the full A054 projected spectrum and its Kelvin-restricted block.

## What may be compared across S and C?

Raw eigenvalue magnitudes are **not pooled** because the projected bases are different.

Allowed bridge comparisons are categorical only:

- counter-propagating pair available;
- symmetric counter-propagating pair available;
- RPO accepted;
- true/projected Floquet evaluated;
- branch certification state.

## Reveal-only working hypotheses

These are not visible to the blind bridge:

\[
u\leftrightarrow5_2,\qquad d\leftrightarrow6_1.
\]

Working compound hypotheses:

\[
P_{\rm work}=G(5_2,5_2,6_1),\quad 6_1\ {\rm opposed},
\]

\[
N_{\rm work}=B(5_2,6_1,6_1),\quad 6_1\ {\rm opposed}.
\]

They remain hypotheses, not particle identifications.

## Run

```bat
run_all.cmd full
```

The Workbench root defaults to:

```text
C:\workspace\projects\SST-Workbench
```

If no sealed A054 full certification exists, step `[5/9]` invokes the authoritative
A054-v0.2.x `run_all_full.cmd` first. A055 then verifies its blind seal before importing it.

To stop before reveal:

```bat
run_blind_only.cmd full
```

## Critical boundaries

- A054 remains authoritative for multi-component compound physics.
- A055 remains authoritative for the particle-spectrum/selection bridge and single-knot controls.
- No mass, charge, QCD, electroweak or atomic claim follows from a compound oscillatory pair.
- No accepted RPO means no Floquet interpretation.
