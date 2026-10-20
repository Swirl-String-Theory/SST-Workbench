# SST Historical Trefoil XYZ v0.2.2 — completeness/provenance fix

This release is a **geometry seed atlas**, not Euler equilibrium, a PKLSA material vortex, or a measured Swirl Clock.

Fixes compared with v0.2.1:

1. Default N={600,1200,2400,4800,9600}, resulting in 2 parameterizations × 2 chiralities × 2 traversal directions × 5 resolutions = **40 XYZ files**.
2. Output uses a **new directory**, refusing to overwrite or mix with any previous XYZ/manifest. No unregistered stale files.
3. Both a manifest and `SHA256SUMS.txt` are checked, including exact resolution/variant coverage, periodic closure and chirality/traversal controls.
4. `regenerate.py` also creates a separate `.zip` and its `.zip.sha256`.
5. `regenerate_v0_2_1.py` is an *unchanged* embedded calculation core. No modifications to its numerical sampling or `cw` start-point convention.

## Regeneration

Install: `py -m pip install numpy scipy` (or `python -m pip install numpy scipy`).

From extracted directory:

```powershell
py regenerate.py
```

Output (fresh; refuses existing output):

- `generated/SST_Historical_Trefoil_XYZ_v0.2.2/` (40 XYZ files, `manifest.json`, checksums)
- `generated/SST_Historical_Trefoil_XYZ_v0.2.2.zip`
- `generated/SST_Historical_Trefoil_XYZ_v0.2.2.zip.sha256`

Alternate output / resolutions:

```powershell
py regenerate.py --n 600 1200 --out .\new_seed_run
py verify_release.py --dir .\generated\SST_Historical_Trefoil_XYZ_v0.2.2
```

To rerun, specify a **different empty/non-existing output path**; never use existing frozen input folders. The ZIP that contains this README already includes the 40 verified XYZ files under `data/`.

## Compatibility / science

Model A: `X=(cos t+1.5 cos 2t, sin t-1.5 sin 2t, 0.35 sin 3t)`.

Model B: `X=((2+cos 3t)cos 2t,(2+cos 3t)sin 2t,sin 3t)`.

- `orig_ccw` means increasing t; `orig_cw` means reversed list retaining the same first point.
- `mirrorX` reflects x and reverses handedness. Reversing list order does **not** change knot chirality.
- Point ordering **alone** does not impose circulation sign in Euler or SST; it must be set independently and recorded in the scientific contract.
- N=600..9600 is **centerline discretization**, not the 3D Euler mesh size or finite-core convergence.
- Different XYZ variants derived from the same analytic family are not independent physical PKLSA providers.
- The new manifest/hash values are not interchangeable with v0.2.0 / v0.2.1 or the frozen A068 v0.4.1 protocol. To test these in A068, create a **new versioned A068 instance**, preserving all historical hashes.
