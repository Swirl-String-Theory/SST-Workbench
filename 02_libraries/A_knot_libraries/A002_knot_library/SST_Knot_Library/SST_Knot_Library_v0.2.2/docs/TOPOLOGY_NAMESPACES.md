# Topology namespaces

SST Knot Library separates topology labels that can otherwise collide textually.

## Knot namespace

Alexander-Briggs/Rolfsen-style knot labels retain their familiar form:

```text
3_1
4_1
6_2
7_4
```

These labels always denote one-component knots.

## Link namespace

KnotPlot/SST filenames of the form

```text
link_<crossings>.<components>.<index>_final.txt
```

are represented internally as

```text
L<crossings>_<components>_<index>
```

For example `link_6.3.2_final.txt -> L6_3_2`.

This is intentionally not collapsed to `6_3`, because `6_3` is a knot label in the knot
namespace.

## Torus-family namespace

Files such as `torus_2.3_final.txt` use

```text
T(2,3)
```

rather than `2_3` or `3_1`. The component-count hint is

\[
\gcd(p,q).
\]

Thus `T(2,3)` has one component whereas `T(2,4)` has two.

## Trust rule

All three forms above are metadata hints when inferred from filenames. They do not certify the
imported geometry. Certification requires an independent topology analysis or a constructive
internal generator whose topology follows from the construction.
