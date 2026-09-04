# SST–Maxwell Blind Falsifier v0.1.0

Target-blind falsification harness for four Maxwell-inspired SST closure questions:

1. **coarse-grained anisotropic swirl stress** — mandatory;
2. **reduced momentum / effective-potential factorization** — mandatory;
3. **structural displacement-current closure** — optional;
4. **handedness and bulk angular-momentum guard** — part of the stress campaign.

The package is deliberately unable to read the hidden numerical comparison targets during the blind run. It uses only preregistered tensor structure, scaling exponents, held-out residuals, symmetry tests, and numerical tolerances. Hidden numerical values are committed by SHA-256 in `blind/commitments.json`; the separate unblind key is not part of this ZIP.

## Critical interpretation guard

For the inviscid incompressible SST substrate, the primitive Euler Cauchy stress is still isotropic, `-p I`. The anisotropic object tested here is a **coarse-grained kinetic/momentum-flux stress**, not an inserted microscopic shear stress.

## Install / run

Windows PowerShell or cmd:

```text
scripts\\run_synthetic.cmd
```

Linux/macOS:

```text
bash scripts/run_synthetic.sh
```

Real campaign (after optional `py -m pip install -e .`, or via the supplied cmd script):

```text
sst-maxwell-blind run ^
  --config config/preregister.json ^
  --campaign C:\path\campaign.csv ^
  --reduced-momentum C:\path\reduced_momentum.csv ^
  --storage C:\path\storage_current.npz ^
  --outdir results_blind
```

The mandatory tracks are stress + reduced momentum. If either is absent, the overall verdict is `INCONCLUSIVE` unless `--allow-missing-required` is explicitly supplied.

## Field NPZ format

Each velocity file referenced by `campaign.csv` contains:

- `u`: `(nx,ny,nz,3)` velocity array in m/s (or one internally consistent velocity unit for pure similarity scans);
- `spacing`: scalar or length-3 cell spacing in metres (or the matching length unit).

The campaign CSV supplies `rho_kg_m3`, `v_ref_m_s`, `geom_scale`, and optional handedness-pair metadata. `v_ref` must be declared before seeing outputs; do not redefine it to make the coefficient attractive.

## Blindness

The blind report exposes fitted coefficients such as `median_C_blind` and `beta_blind`, because they are data products. It does **not** compare them with Maxwell's historical coefficient or the SST electron normalization. Those comparisons occur only after the result files are frozen and the separate key is opened.

## Synthetic fixture

`examples/generate_synthetic_fixture.py` builds algebraically controlled data only to test the software. A synthetic PASS is not physical evidence.

## Recommended workflow

1. Freeze `config/preregister.json` and SHA-256 it.
2. Export raw solver fields without target-dependent rescaling.
3. Run `sst-maxwell-blind run` once.
4. Archive the raw inputs + `blind_report.json` + hashes.
5. Only then open the separate unblind key and run `sst-maxwell-blind unblind`.
