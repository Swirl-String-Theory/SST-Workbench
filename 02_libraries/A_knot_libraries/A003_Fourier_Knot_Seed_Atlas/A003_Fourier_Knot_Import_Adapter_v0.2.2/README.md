# A003 Fourier Knot Import Adapter v0.2.2

## Frozen version contract

- **Atlas:** `../A003-v0.1.2` only; pinned complete `manifest.json` SHA-256: `01d57ec3f259fee4a09caa6aac8d3410ad6e1d8a8f159c6a9fb7ba71d0a6169d`.
- **Historical parent adapter:** `v0.2.1` remains unchanged.
- **240 original XYZ sources byte-preserved; 144 new:** expected 48 seeds × 2 samplings × 4 resolutions = **384**.
- `legacy_v0.1.1_sha256.json` pins every original XYZ record without requiring the old directory at runtime.
- The adapter requires NumPy; optional pyknotid for G5 numerical invariant screening; optional pinned `sst-knot-library/0.2.5` for `prepare`.

## Windows Workbench placement

```text
C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\
    A003-v0.1.1\                           (unchanged)
    A003-v0.1.2\                           (new)
    A003_Fourier_Knot_Import_Adapter_v0.2.1\ (unchanged)
    A003_Fourier_Knot_Import_Adapter_v0.2.2\ (new)
```

In the v0.2.2 folder:

```bat
run_all.cmd
```

Expected local audit: `GEOMETRIC_IMPORT_QUALIFIED`, 384 source records, 48 seeds, G0/G1/G2/G3 PASS, G4 `PASS_DIMENSIONAL_HYPOTHESIS_ONLY` (default `a_star=0.05`), G5 `NOT_RUN`, G6 `NOT_RUN`. Both sampling profiles are tested. Failure must stop with nonzero exit code.

To check all assets without implicit physical scale:

```bat
python fourier_atlas_adapter.py audit
```

To run **optional determinant screening** with installed `pyknotid`:

```bat
python -m pip install pyknotid
run_g5.cmd
```

Note: full G5 includes five Kauffman `F(n)` rows with unknown reference determinants; those remain `NO_REFERENCE_INVARIANT`, so a strict full-atlas G5 run is expected to be `PARTIAL_UNRESOLVED` even if the provider succeeds. Use a limited screen *as a diagnostic only*:

```bat
python fourier_atlas_adapter.py --reference-core-radius-units 0.05 --g5 --g5-family fibonacci_torus --g5-resolutions BASIC catalog
```

A match of the Alexander determinant **does not certify** a knot type or chirality. No Fibonacci-specific physical effect is certified. `prepare` still uses the installed Knot Library and is not implicitly qualified by the mock regression test.

## Gates and scientific scope

- G0 manifest schema/expected catalogue (48)
- G1 XYZ source hashes, finite values, polygon geometry, strict root path policy
- G2 signed mirror projection **diagnostic** (not chirality certification)
- G3 BASIC↔FULL convergence with **legacy thresholds preserved**
- G4 optional dimensional mapping using \(s=r_c/a_\star\), not a derived core model
- G5 optional independent invariant screen; unknown `F(n)` stays without a knot table reference
- G6 PKLSA Euler **NOT_RUN**

The 20 legacy chord-disparity warnings remain; they are not suppressed.

## References

- L. H. Kauffman (1997), *Fourier Knots*, arXiv:q-alg/9711013, Sections 6–7, https://arxiv.org/abs/q-alg/9711013.
- J. Hoste (2009), *Torus knots are Fourier-(1,1,2) knots*, *Journal of Knot Theory and Its Ramifications* **18**, 265–270, DOI:10.1142/S0218216509006926.
