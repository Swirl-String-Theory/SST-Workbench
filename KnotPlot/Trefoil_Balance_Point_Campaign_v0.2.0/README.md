# Trefoil_Balance_Point_Campaign_v0.2.0

Targeted **K31-only zero-bracket search**.

```text
20 new q/h/p configurations
1 trefoil: load 3.1
2 independent scan lanes
10 checkpoints per run
```

No T(2,3) control is run yet.

## The two lanes

**12 joint q/h/p points** continue the old balance ray beyond R100.

**8 hooke-dominant points** determine whether a true CONTRACT region is
reachable even if the joint ray is nonlinear or incorrectly oriented.

See `balance_design.json` for the exact frozen values.

## Recommended workflow

First:

```bat
run_00_install.cmd
run_02_verify_preregistration.cmd
run_05_generate.cmd
run_10_validate_syntax.cmd
run_20_smoke.cmd
```

The smoke uses the first and last frozen settings.

If both pass:

```bat
run_30_campaign.cmd
run_40_analyze.cmd
run_90_pack_outputs.cmd
```

or:

```bat
run_all.cmd
```

## Desired result

The main result we want is not the smallest positive expansion. It is an
actual measured sign transition:

\[
E'>0\quad\rightarrow\quad E'\approx0\quad\rightarrow\quad E'<0.
\]

The analyzer reports the first valid adjacent sign bracket and interpolates
the corresponding q/h/p point.

If only the hooke lane crosses zero, that still establishes that a contractive
regime exists; it means the old combined q/h/p ray needs to be reoriented.

Only after this K31 search has produced a zero should the same local bracket be
repeated on explicit `torus 2 3` as an independent embedding control.
