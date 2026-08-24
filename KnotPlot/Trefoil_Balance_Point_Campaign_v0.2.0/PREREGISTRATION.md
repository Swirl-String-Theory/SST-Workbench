# Preregistration — Trefoil Balance Point Campaign v0.2.0

## Single scientific question

For **KnotPlot `load 3.1` only**, can the signed early geometric response be
driven from EXPAND through zero into CONTRACT by a preregistered q/h/p scan?

The independent `torus 2 3` representation is deliberately deferred until
after the K31 zero has been found. It will be a later control, not an input to
the present search.

## Prior result

v0.1.0 ran 20/20 successfully. Its best common setting was R100:

```text
q = 37.27046411874018
h = 1.3563655804274017
p = 6.0
```

but K31 still had a positive early response:

\[
E'_{100}=+6.849953049959006\times10^{-4}.
\]

Therefore v0.2.0 searches beyond that point.

## Frozen 20 new configurations

### Lane A — extended joint q/h/p ray, 12 settings

\[
q(t)=15+22.27046411874018\,t,
\]
\[
h(t)=1+0.3563655804274017\,t,
\]
\[
p(t)=5+t.
\]

Frozen:

```text
t = 1.05, 1.10, 1.15, 1.20, 1.25, 1.35,
    1.50, 1.70, 1.95, 2.25, 2.60, 3.00
```

All are new relative to v0.1.0.

### Lane B — hooke-dominant contract bracket, 8 settings

Fixed:

```text
q = 26.13523205937009
p = 5.5
```

Frozen:

```text
h = 1.35, 1.40, 1.45, 1.50, 1.60, 1.75, 2.00, 2.40
```

These are also new relative to v0.1.0.

This lane determines whether a CONTRACT regime is reachable even if the joint
ray itself misses the zero.

## Geometry and non-q/h/p controls

Every run:

```text
reset all
load 3.1
refine nbeads 300
mode cb
centre
fitto mindist 1.05
collision fast
energy model MD
```

All non-q/h/p assignments are copied exactly from v0.1.0.

## Checkpoints

\[
i=\{0,10,25,50,100,250,500,1000,4000,10000\}.
\]

Primary observable:

\[
E(i)=\frac12\left[
\frac{L(i)-L(0)}{L(0)}
+
\frac{R_g(i)-R_g(0)}{R_g(0)}
\right].
\]

Primary early slope is an OLS fit through:

```text
0, 10, 25, 50, 100
```

with two consistency windows:

```text
0,25,50
25,50,100
```

A response is:

- `EXPAND` if the primary slope is above `+0.0002` per 100 and the windows do
  not show an opposite non-near-zero sign;
- `CONTRACT` if below `-0.0002`;
- `NEAR_ZERO` if absolute slope is at most `0.0002`;
- `INCONSISTENT_TRANSIENT` if the two early windows have opposite resolved signs.

## Frozen zero rule

Within each lane, sort by the preregistered scan coordinate.

A zero bracket exists only for **adjacent** settings with stable opposite
`EXPAND` / `CONTRACT` classifications. The zero coordinate is linearly
interpolated between those two measured responses.

No q/h/p value is moved after seeing the results.

## Interpretation

`ZERO_BRACKET_FOUND` identifies an operational expansion/contraction balance
candidate. It does not yet prove a mechanical restoring equilibrium.

After K31 has a reproducible zero, the same frozen local bracket should be run
on `torus 2 3` as the independent representation control.
