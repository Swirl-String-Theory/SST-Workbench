# A003 Fourier Knot Import Adapter v0.2.4

**Target atlas:** `../A003-v0.1.2` (48 seeds, 384 XYZ files; BASIC = 1200/2400; FULL = 4800/9600). The atlas is an external immutable dependency. Its `manifest.json` SHA-256 must equal the frozen v0.1.2 value. No source XYZ or older adapter release is modified.

## Purpose

v0.2.4 extends the previous G5 **determinant-only** screening with four independent **diagnostic subgates**, while preserving the existing original `G5_INDEPENDENT_TOPOLOGY` result and all G0–G4 contracts.

| Subgate | Implementation | Scientific boundary |
|---|---|---|
| G5a | `pyknotid` symbolic Alexander polynomial from the **actual XYZ polygon**; exact normalized coefficient comparison with pinned torus/twist/known `3_1` references | Alexander polynomial is incomplete and does not detect mirroring |
| G5b | Signed degree-3 Vassiliev invariant from the polygon plus mirror-odd transformation check | Nonzero mirror-odd invariant is a chirality **witness**, not a full class certification |
| G5c | Analytic torus Alexander polynomial, cross-checked by a **separately implemented** positive-braid unreduced Burau determinant modulo two primes | These two algebraic constructions depend on *declared* `p,q`, **not independent XYZ evidence** |
| G5d | G5a/G5b invariants compared over two source resolutions and two deterministic generic projection orientations, including mirrors | Numerical robustness check, **not an isotopy proof** |

A high crossing count can make exact symbolic `pyknotid` calculations prohibitively expensive. The default **predeclared** guard is a theoretical/reference crossing count of 12; all seeds beyond it are reported `COST_GUARD_UNRESOLVED`. Kauffman's `F(4)`–`F(8)` have no declared Rolfsen type or independently established complexity; they remain `TOPOLOGY_UNKNOWN_COMPLEXITY_UNRESOLVED`, not re-labelled as torus knots. The full torus polynomial reference may nevertheless be computed algebraically at high degree, but this is *not* independent topology evidence from the sampled geometry.

These are bounded, explicitly non-certifying checks. Neither PKLSA nor Euler dynamics is evaluated: G6 remains `NOT_RUN`. A G4 physical length scale is also an **assumed mapping** (`a_star=0.05` atlas units identified with `r_c=1.40897017e-15 m`), not a derived core size.

## Where to install

Extract the whole package as a **new sibling release**:

```text
C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\
    A003-v0.1.2\
    A003_Fourier_Knot_Import_Adapter_v0.2.3\  (unchanged)
    A003_Fourier_Knot_Import_Adapter_v0.2.4\  (new)
```

Activate the existing Workbench `.venv` before running the scripts. Ensure `python -c "import pyknotid, sympy, numpy; print(pyknotid.__file__)"` resolves to the intended interpreter. A temporary, reversible legacy NumPy alias shim (from v0.2.3) is still used only during pyknotid calls; it is **single-threaded** and changes no installed package on disk.

## Execution

Basic/geometry and regressions (all 384 XYZ):

```bat
run_all.cmd
```

Run the **fast, real G5c algebraic reference cross-check** on all 30 torus-family seeds (does not require pyknotid):

```bat
run_g5c_braid_reference.cmd
```

Run the **extended numerical G5** for selected Fibonacci torus seeds at BASIC resolution. G5a/G5b only compute on cases within the complexity budget; expensive seeds remain explicitly unresolved:

```bat
run_g5_extended_fibonacci_torus.cmd
```

Run the same bounded G5 screen for all declared twist-family seeds:

```bat
run_g5_extended_twist.cmd
```

Or direct CLI:

```bat
python fourier_atlas_adapter.py --reference-core-radius-units 0.05 --g5 --g5-extended --g5-family fibonacci_torus --g5-resolutions BASIC --g5-extended-max-crossings 12 catalog
```

The higher-cost `FULL` selection can be requested *only deliberately* using `--g5-resolutions FULL`. The `--g5-resolutions ALL` option requires four levels and performs up to 16 polygon/provider evaluations per admitted seed (two projections × each original/mirror); use with care. The provider calculation can be slow because pyknotid 0.5.3 may run its non-Cython Python fallback.

For a strict all-selected-seeds prerequisite use `--require-g5-extended-complete`. Then a provider failure, reference mismatch **or any cost-guarded/unknown case** returns exit code 2. **Do not use this flag for a high-crossing family before increasing compute bounds with a separately qualified resource plan.**

## Gate semantics and provenance

- `G0` manifest schema and identity, `G1` all XYZ hashes, `G2` mirror/diagram geometric witness, and `G3` BASIC/FULL convergence retain their v0.2.3 definitions and thresholds.
- `G4` is conditional dimensional calibration, not an inferred physical scale.
- The previous `G5_INDEPENDENT_TOPOLOGY` determinant-only screen is retained unchanged. New results appear in `extended_g5_screen` (G5a–G5d) with each seed and each numerical observation reported separately. Original `topology_status`/`chirality_status` fields are not promoted.
- The full Alexander-polynomial reference is exact integer algebra; pyknotid's measured coefficients are normalized by their Laurent-unit ambiguity and `Delta(1)=1`.
- G5c's Burau modular checks operate over primes 1000003 and 1000033 at `t=2,3,7`; passing them verifies *algebraic reference consistency*, not the geometry's knot type.
- Source hashes are rechecked immediately before each bounded pyknotid evaluation, and the deterministic geometric rotations/reflections do not write altered XYZ files.
- The existing `--require-g5-evidence` strict behavior is preserved for determinant-only G5. Extended G5 is independent and must be explicitly requested.
- Numerical poly/Vassiliev matching does not imply isotopy certification; the exposed `independent_topology_certified` and `chirality_certified` remain `false`.

## Reporting and tests

The standard run produces `outputs/validation_report.json` and `outputs/fourier_external_registry.json`. Specialized commands write to `outputs_g5c_braid_reference/`, `outputs_g5_extended_fibonacci_torus/`, and `outputs_g5_extended_twist/`. Retain all reports with their executable versions and source hashes for G5 campaigns.

```bat
python -m unittest discover -s tests -v
```

The supplied tests include injected **mock provider** assertions for wrong polynomials, mirror parity, topology-status non-promotion, unknown Fibonacci identity and source-hash failure. These are **unit tests only**; they are not substituted for running actual pyknotid on Windows.

## Citations (LaTeX)

```latex
\bibitem{Alexander1928}
J. W. Alexander (1928),
\textit{Topological Invariants of Knots and Links},
Transactions of the American Mathematical Society 30(2), 275--306.
https://doi.org/10.1090/S0002-9947-1928-1501429-1

\bibitem{BirmanBrendle2005}
J. S. Birman and T. E. Brendle (2005),
\textit{Braids: A Survey}, in Handbook of Knot Theory,
Elsevier, pp. 19--103.
https://arxiv.org/abs/math/0409205

\bibitem{Taylor2017}
A. J. Taylor and others, \textit{pyknotid: knot identification from spatial curves},
Software package and documentation.
https://pyknotid.readthedocs.io/
```
