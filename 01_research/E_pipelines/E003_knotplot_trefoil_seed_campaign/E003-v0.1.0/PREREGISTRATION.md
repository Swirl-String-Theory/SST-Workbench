# Preregistration — Trefoil Seed Campaign v0.1.1

## Purpose

Generate a prospective set of geometrically independent \(3_1\) trefoil initial
conditions for the SST Phase-Feedback Delay Knot Stability Blind Falsifier v0.2.

The previous preparation campaign produced 41 labelled files but only 10 unique
`i10000` geometries; all 10 had already been used in the v0.1.7 analysis. This
campaign therefore changes the **initial-condition manifold**, not the phase-delay
analysis gates.

## Frozen seed set

Exactly 38 seeds are specified in `seed_manifest.json` before any new `i10000`
phase-delay result is evaluated:

1. 24 closed-Bishop-frame helical perturbations:
   - modes \(m=2,\ldots,7\)
   - RMS amplitudes \(A/d_0 \in \{0.035,0.075\}\)
   - both chiralities \(\chi=\pm1\)
2. 8 mixed normal/binormal low-mode perturbations with fixed mode pairs, phases,
   weights and \(A/d_0=0.065\).
3. 6 positive, invertible PCA-axis affine embeddings.

Here \(d_0\) is the base seed's numerical nonlocal clearance measured on a
fixed 400-point uniform-arclength sampling, excluding the five nearest samples
on either side. This is a numerical embedding-safety screen, not a formal
knot-theoretic proof.

No seed amplitude is automatically tuned in response to safety or outcome data.

## Numerical isotopy safety gate

For every generated seed \(X_1\), the straight-line homotopy

\[
X(u)=(1-u)X_0+uX_1,\qquad u\in[0,1]
\]

is sampled at 21 fixed values. At every slice the same fixed 400-sample
nonlocal-clearance screen is evaluated. Generation aborts if

\[
\min_u d_{\rm clear}(X(u)) < 0.30\,d_0
\]

or if

\[
d_{\rm clear}(X_1)<0.50\,d_0.
\]

KnotPlot additionally runs `safe`, `dowker`, and `lnknum` at `i00000` and
`i10000`; their logs are retained. `alex -1` is intentionally excluded because
the target KnotPlot installation does not provide the external `KP-alex.exe`
helper. This diagnostic change does not alter the relaxation dynamics.

## Frozen relaxation protocol

All 38 seeds use exactly the same relaxation settings:

- 300 beads
- `fitto mindist 1.05`
- `collision fast`
- `close = 1`
- `max-dr = 0.01`
- mechanical + electrical + bend forces ON
- `charge 15`
- `hooke 1`
- `power 6`
- `timeincr 15`
- `bencon = 1`
- `stusplit = 0`
- `dstep = 1`
- `bradius = 0.1`
- `cradius = 0.05`
- energy model MD

Checkpoints are fixed at 0, 1000, 4000 and 10000 iterations.

## Success criterion for dataset generation

This is not a physics PASS/FAIL test. The dataset is eligible for the separate
phase-delay v0.2 confirmatory falsifier only if the final set contains at least

\[
N_{\rm novel,unique}\ge 8
\]

identity-hash geometries not present in the frozen v0.1.7 64-point historical
registry. The preferred target is at least 12.

If the 38 starts converge to fewer than 8 novel unique endpoints, the result is
`CONFIRMATORY INPUT INSUFFICIENT`; the campaign is not adaptively retuned.
