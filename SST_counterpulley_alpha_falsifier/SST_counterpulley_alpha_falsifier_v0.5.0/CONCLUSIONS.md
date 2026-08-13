# CONCLUSIONS -- v0.5.0

## Status

**[DERIVED NEGATIVE, bounded solver domain]** v0.5.0 does not find an alpha-blind relative periodic orbit that survives the full Cartesian closure and endpoint-vectorfield gates. Consequently true Floquet monodromy is not scientifically eligible and alpha remains unopened.

## New positive result: the nonlinear solver works

The full native Newton--Krylov multiple-shooting run improves both its reduced and full-state diagnostics:

\[
\|F_{\rm proj}\|: 0.6442244122\rightarrow0.4559781062,
\]

and

\[
\epsilon_{\rm shoot,max}:0.3897500535\rightarrow0.3561396051.
\]

The full relative recurrence improves from the best blind seed

\[
0.4173283240D
\]

to

\[
0.3463310365D.
\]

Therefore v0.5 is not merely repeating the v0.4 scan: its nonlinear correction space moves the state toward better recurrence.

## Why the RPO claim still fails

The preregistered full-state gate requires

\[
\epsilon_{\rm RPO}<0.05D,
\]

but the best corrected candidate remains

\[
\boxed{\epsilon_{\rm RPO}=0.3463310365D}.
\]

Endpoint-vectorfield compatibility is also poor:

\[
\boxed{\epsilon_f=0.7562101428}.
\]

Thus the endpoint is neither geometrically nor dynamically close enough to the initial state modulo the accepted relative symmetry.

## Longitudinal `Delta s_+-` result

A pure longitudinal shift of one complete closed filament along itself is not an additional continuum geometry; it is reparametrisation. The finite-N test supports this:

\[
\epsilon_{\rm relabel}(48)=8.7731\times10^{-2},
\qquad
\epsilon_{\rm relabel}(96)=2.4746\times10^{-2}.
\]

The effect decreases strongly under refinement. Therefore `Delta s_+-` is **not** used as a fitted physical search coordinate in v0.5.

A physical longitudinal phase would require extra material structure, e.g. a non-axisymmetric finite core, a helical internal vortex-line texture, or another field whose phase is attached to material rather than to curve labels. That would be a new model extension and must be tested separately.

## Gate outcome

- H0--H9: PASS.
- H10 full-state RPO closure: FAIL.
- H11 tangent compatibility: FAIL.
- H12--H17: SKIP.
- H18 alpha unblinding: FAIL.

Machine verdict:

```text
NO_ALPHA_BLIND_RPO_FOUND_AFTER_NEWTON_KRYLOV_MULTIPLE_SHOOTING__TRUE_FLOQUET_GATE_CLOSED
```

## Recommended next route

The next meaningful extension is **not** another alpha observable. Two routes are scientifically clean:

1. enlarge the RPO state correction space through continuation in additional genuine shape modes and/or higher Fourier/Kelvin sectors;
2. introduce an explicitly material finite-core degree of freedom only if SST supplies an independent physical reason for it, then test whether its phase survives discretisation and produces a genuine RPO.

A particularly clean v0.6 would use continuation from the v0.5 best candidate while increasing basis dimension and shooting segments, with all acceptance thresholds frozen before the campaign.
