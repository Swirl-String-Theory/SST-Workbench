# Outputschema

## `summary.json`

Hoofdvelden:

- `source`: inputpad, SHA-256 en recordmetadata;
- `constants`: canonieke SST-constanten en afgeleide \(\Gamma\), \(t_c\);
- `settings`: resoluties, core sweep, fysieke thickness en interacties;
- `geometry`: lengte, edge-uniformiteit, bron-\(L,D\)-residuen, kromming, torsie en thickness-proxy;
- `contact`: completeness, winding, inverse residual en orthogonaliteit;
- `billiard`: seed, orbit, closure en lower-period guard;
- `geometric_force`: lokale en niet-lokale compatibility;
- `hydrodynamics`: één rij per `(interaction, core_ratio)`;
- `gates`: H0–H8 evidence;
- `scientific_verdict` en `non_claims`.

## `hydrodynamics/core_sweep.csv`

Belangrijke kolommen:

- `interaction`: `full`, `local` of `nonlocal`;
- `core_ratio`: \(a/\Delta\);
- `relative_equilibrium_residual`;
- `fitted_shape_residual`;
- `normal_alignment_cosine`;
- `fitted_scale_N`;
- `tension_mean_N`, `tension_cv`;
- `binormal_leakage`, `tangential_leakage`;
- `force_density_rms_N_m`;
- rigide `translation_*` en `rotation_*`.

## `contact/contact_map.csv`

Per sourceparameter \(s\): beide branches, lifts, `pt`-waarden en dubbel-kritische
orthogonaliteitsresiduen.

## `force/geometric_force_balance.csv`

Per \(s\): \(F^{\mathrm I}\), \(F^{\mathrm O}\), lokale balans, beide
compatibility residuals, determinant en kaartafgeleiden.
