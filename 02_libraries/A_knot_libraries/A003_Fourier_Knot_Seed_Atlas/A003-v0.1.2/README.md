# A003 Fourier Knot Seed Atlas v0.1.2 — Fibonacci extension

**Scientific status:** `GEOMETRIC_SEEDS_ONLY`. This version does not establish independent topology classification, chirality, core viability, dynamic frequency resonance, PKLSA/Euler closure or physical golden-ratio preference.

## Release and immutability

- Parent `A003-v0.1.1` is NOT edited.
- **Exactly 240/240 legacy source XYZ records are byte-for-byte unchanged**, including filename and SHA-256.
- Adds **18 new analytic curve seeds**, **144 new XYZ files** (BASIC: 1200/2400; FULL: 4800/9600; both `uniform_t` and `uniform_s_polyline`).
- Totals: **48 seed identities and 384 XYZ files**.
- The new complete manifest is pinned by SHA-256 `01d57ec3f259fee4a09caa6aac8d3410ad6e1d8a8f159c6a9fb7ba71d0a6169d`.

## New analytic families, with 3D dimensionless coordinates

For \(t\in[0,2\pi)\), Fibonacci \((a,b,c)=(2,3,5),(3,5,8),(5,8,13),(8,13,21),(13,21,34),(21,34,55)\):

**Kauffman's true Fibonacci Fourier family** (`fibonacci_F3` ... `fibonacci_F8`; Section 6):

\[
\mathbf X_{F(n)}(t) =
\bigl(\cos(at),\ \cos(bt+0.5),\
\tfrac12\cos(ct+0.5)+\tfrac12\sin(bt+0.5)\bigr),
\qquad c=a+b.
\]

`F(3)` is the trefoil from Section 4. For `F(4)`–`F(8)`, **no Rolfsen identifier is asserted**; `F(n)_UNCLASSIFIED` is a source-construction label, not a classification result.

**Fibonacci torus family** (`fibonacci_torus_F3` ... `F8`; Section 7, using `T=p*t`):

\[
\mathbf X_{T(p,q)}(t)=
\bigl((1+0.5\cos(qt))\cos(pt),\
(1+0.5\cos(qt))\sin(pt),\ 0.5\sin(qt)\bigr).
\]

Here \((p,q)=(a,b)\) with consecutive Fibonacci values; each pair is coprime. **Do not confuse this family with the independent Kauffman `F(n)` family.**

**Nearby, nonconsecutive-frequency torus controls** (`nonfibonacci_torus_control_F3` ... `F8`) use the same toroidal analytic formula but pairs
`(2,5), (3,4), (5,9), (8,15), (13,22), (21,32)` respectively. These are *not topology-matched controls*: changed `p,q` generally change the torus knot type. They test geometric frequency sensitivity but cannot by themselves isolate a pure Fibonacci or golden-ratio effect.

All coordinates are **dimensionless**. A torus curve obtained by irrational `q/p = phi` is *not a closed knot*; all saved torus pairs remain integer, coprime and periodic. Fourier integers here are spatial parameter harmonics, not temporal Kelvin/Floquet eigenfrequencies.

## Sampling

The original 240 exports use exactly the v0.1.1 algorithm. New high-harmonic seeds use **16x analytic oversampling** to produce the `uniform_s_polyline` arclength map; this does not change the analytic centerline or perform relaxation. `uniform_t` is sampled directly from formulas. There is no repeated endpoint. All 4 resolutions are represented.

## Reproduce, validate, upgrade

To regenerate all 384 source XYZ files and manifests within a new directory:

```bat
python generate.py --profiles BASIC FULL
```

To apply the *incremental upgrade* without modifying v0.1.1, extract the `A003_Fibonacci_Atlas_Patch_v0.1.2.zip` next to the parent atlas and run its `apply_patch.py`. The installer validates old byte hashes, new payload hashes and complete manifest before atomically publishing `A003-v0.1.2`.

The matching adapter is `A003_Fourier_Knot_Import_Adapter_v0.2.2`. Run `run_all.cmd` there for G0-G4 audits. G4 is **conditional scale bookkeeping** anchored to an assumed radius (default `a_star=0.05` dimensionless units, mapping it to canonical `r_c`). G5 is optional numerical invariant screening and **not independent topology certification**; G6 is not run.

## References

- L. H. Kauffman, *Fourier Knots* (1997), arXiv:q-alg/9711013, Section 6 (Fibonacci family, Figure 5) and Section 7 (torus parametrization): https://arxiv.org/abs/q-alg/9711013
- J. Hoste, *Torus knots are Fourier-(1,1,2) knots* (2009), *J. Knot Theory Ramif.* **18**, 265–270. DOI:10.1142/S0218216509006926.
- A. Boocher, J. Daigle, J. Hoste, W. Zheng, *Sampling Lissajous and Fourier Knots* (2009), *Experimental Mathematics* **18**, 481–497. DOI:10.1080/10586458.2009.10129057.
