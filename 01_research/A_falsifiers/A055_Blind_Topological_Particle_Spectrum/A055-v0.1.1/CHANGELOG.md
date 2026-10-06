# Changelog

## v0.1.1 — 2026-10-06

Administrative correction:

- canonical falsifier identifier changed from the accidentally reused `A054` to **A055**;
- Python package renamed `a055_spectrum`;
- native module renamed `a055_native`;
- output/archive names now use `A055`.

Scientific/statistical corrections following the first run:

- adds `N = 40, 80, 160` resolution ladder;
- raises embedding ensemble to 8 (`basic`) or 16 (`full`) replicates per resolution;
- adds per-feature resolution-convergence gate;
- adds per-feature high-resolution embedding-CV gate;
- replaces primary `contact_ratio` with resolution-stable normalized `min_distance`;
- retains `contact_ratio` as diagnostic only;
- introduces explicit feature-domain registry;
- makes `linking_strength` link-only and removes the former `+1e-6` knot/mixed ratio floor;
- forbids mixed knot/link `abs_writhe` ratio fits;
- excludes non-positive logarithmic ratio inputs rather than shifting them;
- splits blind pair distances into `common_all`, `knots`, and `links` spaces;
- writes both RAW and QUALIFIED pair tables;
- historical `5_2/6_1` rank is scientific only when both cases survive the knot-space gates;
- increases null search to 10,000 trials for both normal presets;
- adds exact lower-envelope acceleration for repeated null triplet searches;
- writes complete compressed null distributions;
- fixes MSVC portability by using an explicit `constexpr` \(\pi\) in the C++ kernel.

The corrected historical reveal-only hypothesis remains

\[
u\leftrightarrow5_2,\qquad d\leftrightarrow6_1.
\]

## v0.1.0 — superseded screening baseline

- first 82-object self-contained PD screening campaign;
- exposed the resolution dependence of `contact_ratio`;
- exposed the invalid mixed use of `linking_strength`;
- used only five null targets in the first executed basic campaign;
- historical `5_2/6_1` raw rank in that run was 551/595 under the old feature space.
