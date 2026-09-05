# v0.4.2 clock-domain hotfix

## Failure in v0.4.1

The bifurcation campaign entered a region with

\[
S^2=1-\lVert\boldsymbol\beta\rVert^2<0.
\]

The expression

```python
max((1.0 - beta2) ** 1.5, 1e-300)
```

created a complex number before `max` was evaluated.

## Correct rule

```python
s2 = 1.0 - beta2
if s2 <= 0.0:
    classification = "CLOCK_INVALID"
else:
    d_R_F = G / s2**1.5
```

The implementation goes further: discovery and refinement use the real numerator

\[
G=S^2+\rho\,\boldsymbol\beta\cdot(J_\beta\mathbf e_\rho),
\]

and never send a valid/invalid transition through the ordinary stationary-root refiner.

## New diagnostics

- `clock_boundary_bracket_count`
- `clock_boundary_brackets`
- `clock_domain_split_count`
- `clock_domain_splits`

A clock boundary is not a stationary root and does not contribute to candidate counts.
