# SST Chiral Kelvin Falsification Program

## Conclusion Ledger

**Release:** v0.1.3.1

This file records changes in scientific interpretation.

It is intentionally separate from `CHANGELOG.md`:

```text
CHANGELOG.md
    -> what changed in the software

CONCLUSIONS.md
    -> what changed in the scientific conclusions
```

Conclusions are append-only.

An earlier conclusion must never be silently rewritten.  If later
results alter an interpretation, the earlier conclusion remains in
the ledger and is marked:

- `[REFINED]`
- `[SUPERSEDED]`
- `[WITHDRAWN]`

---

# Status vocabulary

## [NUMERICALLY VERIFIED]

Directly supported by the current numerical implementation and audit
within the stated model.

## [DERIVED NEGATIVE]

A negative result implied by the implemented model and confirmed
numerically.

## [DIAGNOSTIC]

Observed numerically but not yet promoted to a physical SST result.

## [HEURISTIC]

Engineering/release criterion, not a mathematical theorem.

## [OPEN]

Unresolved.

## [PLANNED TEST]

Explicit future falsification or convergence test.

---

# v0.1.0

## C0.1 — Analytic Jacobian

**Status:** `[NUMERICALLY VERIFIED]`

The analytic Frechet derivative agrees with finite differences at
approximately

\[
10^{-10}
\]

relative error in the validated baseline.

### Conclusion

The linearization of the regularized Biot-Savart kernel is numerically
consistent with the implemented velocity operator.

---

## C0.2 — Python/native parity

**Status:** `[NUMERICALLY VERIFIED]`

The validated Python and C++/pybind implementations agree to
approximately machine precision for the baseline observables.

---

## C0.3 — Circulation reversal

**Status:** `[NUMERICALLY VERIFIED]`

The frozen-geometry operator respects the expected sign structure under

\[
\Gamma\rightarrow-\Gamma.
\]

---

## C0.4 — Four-state scalar-energy degeneracy

**Status:** `[DERIVED NEGATIVE]`

For the isotropic finite-core model,

\[
E(+,+)
=
E(+,-)
=
E(-,+)
=
E(-,-).
\]

Equivalently,

\[
E_h=E_s=E_{hs}=0.
\]

### Conclusion

The present scalar kinetic energy cannot distinguish the four
handedness/circulation states.

Any future nonzero splitting requires either additional physical
structure or a numerical/modeling artefact.

---

# v0.1.1

## C1.1 — Baseline remains valid

**Status:** `[NUMERICALLY VERIFIED]`

The v0.1.0 null and implementation gates remained PASS.

---

## C1.2 — Energy convergence does not imply spectral convergence

**Status:** `[NUMERICALLY VERIFIED]`

For the trefoil \(N=48\rightarrow64\), scalar energy already changed by
only approximately

\[
1.22\times10^{-3},
\]

while the eigenspectrum remained poorly converged.

### Conclusion

\[
\boxed{
\text{energy convergence}
\not\Rightarrow
\text{spectral convergence}
}
\]

---

## C1.3 — Individual frozen-trefoil modes were not converged

**Status:** `[DERIVED NEGATIVE]`

Only a very small fraction of the matched trefoil mode groups passed
the v0.1.1 convergence criterion.

The low-resolution frozen spectrum cannot be interpreted as a physical
SST normal-mode spectrum.

---

## C1.4 — Circularity remains useful

**Status:** `[DIAGNOSTIC]`

Many modes exhibit

\[
|\mathcal C_n|\approx1.
\]

The circularity observable is retained, but convergence of
\(\mathcal C_n\) alone does not establish convergence of \(\omega_n\).

---

## C1.5 — Frozen growth rates are not physical instabilities

**Status:** `[NUMERICALLY VERIFIED]`

The analytic torus trefoil is not a solved relative equilibrium.

Therefore

\[
\sigma_n\ne0
\]

cannot yet be interpreted as a physical instability.

---

# v0.1.2.1

## C2.1 — Matcher self-consistency

**Status:** `[NUMERICALLY VERIFIED]`

The self-match gives approximately

\[
M_{\rm self}=1
\]

and

\[
S_{\rm fp}=1.
\]

### Conclusion

The revised matching machinery is internally self-consistent.

---

## C2.2 — Near-degenerate rotation is not the sole bottleneck

**Status:** `[REFINED]`

### Earlier working hypothesis

Poor \(N\rightarrow N'\) overlap may mainly result from arbitrary
rotation inside nearly degenerate eigenspaces.

### v0.1.2.1 result

Several branches show simultaneously:

- strong field overlap;
- strong Fourier identity;
- stable circularity;
- substantially drifting eigenfrequency.

### Revised conclusion

Near-degenerate rotation explains only part of the discrepancy.

Finite spatial resolution and numerical dispersion are now stronger
candidate bottlenecks.

---

## C2.3 — N <= 96 is not core-resolved

**Status:** `[NUMERICALLY VERIFIED]`

Define

\[
\eta_a
=
\frac{\max_j\Delta s_j}{a}.
\]

Measured values:

| Geometry | N | eta_a(max) | Status |
|---|---:|---:|---|
| ring | 48 | 2.616 | UNDERRESOLVED |
| ring | 64 | 1.963 | DIAGNOSTIC |
| ring | 96 | 1.309 | DIAGNOSTIC |
| trefoil | 48 | 2.211 | UNDERRESOLVED |
| trefoil | 64 | 1.670 | DIAGNOSTIC |
| trefoil | 96 | 1.115 | DIAGNOSTIC |

None satisfy

\[
\eta_a\le0.5.
\]

---

## C2.4 — First core-resolved regime is approximately N=256

**Status:** `[HEURISTIC]`

The observed approximate \(1/N\) scaling places the first useful
core-resolved campaign around

\[
N\sim256.
\]

This is a release-planning estimate, not proof of asymptotic convergence.

---

## C2.5 — Wavelength resolution is an independent gate

**Status:** `[DIAGNOSTIC]`

For a mode with dominant Fourier index \(m_n\), define

\[
\boxed{
\mathrm{PPW}_n
=
\frac{N}{m_n}
}
\]

where PPW is the number of sample points per dominant wavelength.

### Conclusion

Core resolution alone is insufficient.

A mode may retain recognizable shape and circularity while its
eigenfrequency remains affected by numerical dispersion.

---

## C2.6 — Circularity is often more stable than frequency

**Status:** `[DIAGNOSTIC]`

Several branches show approximately

\[
M_{\rm overlap}\gtrsim0.9,
\qquad
S_{\rm fp}\gtrsim0.99,
\]

with small changes in circularity, while frequency drift remains tens
of percent.

### Conclusion

The principal unresolved quantity is spectral/eigenvalue convergence,
not evidence that circularity itself is numerically ill-defined.

---

## C2.7 — Conditioning does not explain the main high-C drift

**Status:** `[DIAGNOSTIC]`

Many high-circularity branches have

\[
\kappa_n\approx1.
\]

Strong non-normal sensitivity therefore does not explain the dominant
frequency drift of those branches.

---

## C2.8 — Fixed m_max=24 is inadequate

**Status:** `[NUMERICALLY VERIFIED]`

At \(N=96\), many distinct high-frequency modes were assigned the same
maximum allowed Fourier index

\[
m=24.
\]

### Conclusion

The fixed fingerprint ceiling limits high-frequency mode identity.

v0.1.3 removes the ceiling and uses

\[
m_{\max}
=
\left\lfloor
\frac{N}{2}
\right\rfloor-1.
\]

---

# v0.1.3

## C3.1 — Two independent spatial-resolution gates

**Status:** `[NUMERICALLY VERIFIED]`

**Previous status:** `[HEURISTIC]`

The \(N=256,320,384\) campaign reaches the adopted core-resolution
criterion for both benchmark geometries.

For the ring,

\[
\eta_a
=
0.490862,\;0.392693,\;0.327246.
\]

For the frozen trefoil,

\[
\eta_a
=
0.419285,\;0.335462,\;0.279551.
\]

A mode is eligible for the strongest numerical convergence class only
when both

\[
\boxed{
\eta_a\le0.5
}
\]

and

\[
\boxed{
\mathrm{PPW}\ge12
}
\]

are satisfied.

Branches with

\[
8\le\mathrm{PPW}<12
\]

remain diagnostic.

These thresholds are engineering convergence criteria rather than
mathematical theorems.

---

## C3.2 — Resolved-grid numerical mode tracking established

**Status:** `[NUMERICALLY VERIFIED]`

**Previous status:** `[PLANNED TEST]`

\[
\frac{316}{358}
=
0.88268
\]

of trefoil matches are numerically trackable for \(256\to320\), and

\[
\frac{328}{344}
=
0.95349
\]

for \(320\to384\).

---

## C3.3 — Three-resolution mode identity established

**Status:** `[NUMERICALLY VERIFIED]`

**Previous status:** `[PLANNED TEST]`

An \(m=4\) branch follows

\[
|\hat\omega|:
0.027223905
\rightarrow
0.027260065
\rightarrow
0.027263785,
\]

with pairwise relative drift decreasing approximately as

\[
0.133\%
\rightarrow
0.0136\%.
\]

An oscillatory \(m=6\) branch follows

\[
|\hat\omega|:
0.16041716
\rightarrow
0.16129630
\rightarrow
0.16172988,
\]

with drift decreasing approximately as

\[
0.545\%
\rightarrow
0.268\%.
\]

---

## C3.4 — Frozen geometry remains non-physical

**Status:** `[NUMERICALLY VERIFIED]`

Even if the analytic torus-trefoil spectrum eventually converges
numerically,

\[
\boxed{
\text{converged frozen mode}
\ne
\text{physical SST normal mode}
}
\]

until a true relative-equilibrium/co-moving operator exists.

---

## C3.5 — Earlier convergence failure was predominantly resolution driven

**Status:** `[NUMERICALLY VERIFIED]`

The increase from the low-resolution regime to

\[
88.27\%
\rightarrow
95.35\%
\]

trackable matched trefoil clusters after entering the resolved regime
strongly supports finite spatial/wavelength resolution as the dominant
earlier convergence bottleneck.

This statement concerns the implemented frozen-geometry numerical
problem only.

---

## C3.6 — PPW predicts spectral convergence quality

**Status:** `[NUMERICALLY VERIFIED]`

The campaign supports

\[
\mathrm{PPW}
=
\frac{N}{m_{\rm dom}}
\]

as an independent spectral-resolution diagnostic.

Branches satisfying the adopted

\[
\mathrm{PPW}\ge12
\]

criterion exhibit substantially improved frequency convergence.

The threshold remains an engineering criterion rather than a theorem.

---

## C3.7 — Circularity is a stable candidate mode observable

**Status:** `[DIAGNOSTIC]`

Across many resolved tracked branches, circularity remains stable while
frequency convergence improves and condition numbers remain modest.

Circularity is therefore retained as a robust numerical diagnostic.
It is not yet established as a physical SST quantum number.

---

## C3.8 — Physical Kelvin spectrum remains open

**Status:** `[OPEN]`

The next physics gate is

\[
\boxed{
\text{ideal trefoil}
\rightarrow
\text{relative equilibrium}
\rightarrow
\text{co-moving linear operator}
}
\]

with rigid-motion and tangential-gauge removal.

---

# v0.1.3.1

## Housekeeping conclusion

v0.1.3.1 introduces no new SST physical claim.

It synchronises the scientific ledger with the v0.1.3 resolved-grid
results and separates:

\[
\text{all matched modes}
\]

from

\[
\text{modes actually eligible for resolved interpretation}.
\]

The v0.1.x endpoint is therefore:

\[
\boxed{
\text{resolved frozen-trefoil branches are numerically trackable}
}
\]

while

\[
\boxed{
\text{physical SST trefoil eigenmodes remain unestablished}.
}
\]

---

# Current global conclusion

## Established

**[NUMERICALLY VERIFIED / DERIVED NEGATIVE]**

1. The finite-core Biot-Savart implementation and analytic Jacobian are
   internally consistent.
2. Python/native agreement is excellent for validated baseline
   observables.
3. The isotropic scalar energy cannot split the four \((h,s)\) states.
4. Scalar energy converges substantially faster than the frozen
   eigenspectrum.
5. \(N\le96\) is not core-resolved under the adopted criterion.
6. The fixed Fourier \(m=24\) ceiling is inadequate.

## Diagnostic

1. Circularity remains numerically coherent.
2. Several modes retain shape/chirality identity while frequencies
   drift.
3. Numerical dispersion / spatial resolution is now a stronger
   explanation than matcher failure alone.

## Open

1. A converged physical Kelvin spectrum of an SST electron trefoil.
2. Physical stability of the trefoil.
3. Physical handedness-dependent mode splitting.
4. A relative-equilibrium ideal SST trefoil.
5. Any experimentally physical interpretation of the frozen spectrum.

---

# v0.2.0 hand-off

v0.2.0 is reserved for physical-geometry/equilibrium work:

1. ideal-trefoil centerline import;
2. arclength-controlled resampling;
3. Bishop / parallel-transport frame;
4. relative-equilibrium solve;
5. co-moving linear operator;
6. rigid translation/rotation removal;
7. tangential gauge removal;
8. four-state \((h,s)\) mode campaign;
9. physical observables

\[
\omega_n,
\qquad
\sigma_n,
\qquad
\mathcal C_n,
\qquad
J_n=\omega_n\mathcal C_n;
\]

10. \(Z_2\times Z_2\) decomposition of physical mode observables.

---

# Maintenance rule

For every future release:

1. append new conclusions;
2. never silently delete an old conclusion;
3. mark revisions as `REFINED`, `SUPERSEDED`, or `WITHDRAWN`;
4. distinguish implementation validity, numerical convergence, model
   implications, and physical interpretation;
5. record negative results with the same prominence as positive ones.
