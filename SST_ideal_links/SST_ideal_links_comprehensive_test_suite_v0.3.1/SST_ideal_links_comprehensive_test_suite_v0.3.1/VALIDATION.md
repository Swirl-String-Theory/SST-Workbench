# Validation — v0.3.0

## Executed release checks

### Python/unit suite

```text
17 passed in 13.12 s
```

The 17 tests cover the inherited parser/Fourier/contact/native contracts plus the new:

- topological circulation-sector quotient;
- reduced normal-basis orthonormality;
- candidate two-form antisymmetry/even rank;
- finite-difference Hessian shape and symmetry;
- end-to-end Hopf-link QM-readiness smoke path.

### Native C++/NumPy parity

A strict native parity audit was executed for `L2a1` and `L6a4` at `N=64` and
`epsilon/D=0.10`. The audit passed.

Representative maximum absolute errors:

- Biot–Savart velocity: `1.67e-16`;
- Gauss-linking matrix: `4.44e-16` for `L2a1`;
- Neumann coupling matrix: `1.67e-16`.

The complete ledger is `validation/v0.3.0/native_parity.json`.

### Eighteen-link quick QM screen

All requested links through seven crossings completed with the strict native backend:

```text
18 requested
18 completed
0 failures
elapsed: 16.03 s
```

The `qm_quick` preset uses a diagonal central-difference Hessian. It is a Q1–Q2 screening campaign
and is deliberately barred from passing Q3–Q5. Its full outputs are included under
`validation/v0.3.0/qm_18_quick/`.

### Full-Hessian Hopf regression

`L2a1` completed with the `qm_full` preset:

```text
hessian_scheme: full-central
completed: 1/1
failures: 0
elapsed: 4.86 s
```

The run reached readiness level 2, not a positive quantization result. Its reduced Hessian had
negative directions and the candidate two-form retained a null space. This is scientifically useful:
the software does not promote a familiar topology to “QM-ready” merely because the pipeline works.

## Interpretation

These checks validate software implementation and numerical plumbing. They do not validate the
selected effective energy closure as SST CANON, nor do they derive Hilbert space, Born probabilities,
operator commutators, an absolute action scale or measured particle spectra.


## v0.3.1 hotfix validation scope

The numerical C++ source is unchanged. Added runner-contract tests verify the new native-build flags
and the executable preflight interface. Windows compiler execution must still be confirmed locally,
because the `.pyd` is ABI- and platform-specific.
