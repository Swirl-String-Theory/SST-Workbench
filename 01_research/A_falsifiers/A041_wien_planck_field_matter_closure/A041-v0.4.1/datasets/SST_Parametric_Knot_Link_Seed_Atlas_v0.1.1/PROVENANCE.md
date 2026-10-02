# Provenance — PKLSA v0.1.1

Input archive hashes are recorded in `sources/SOURCE_HASHES.json`. The 49-family scope was taken from the SST archive inventory, not inferred from filenames at build time.

The non-torus knot/link base geometries were reconstructed from Brian Gilbert Fourier records in the user's `Ideal_Sources_Official.zip`. The verified Fourier convention is

`gamma(t) = A0/2 + sum_(n>=1) [An cos(nt) + Bn sin(nt)]`.

Using `A0` rather than `A0/2` corrupts relative component placement; PKLSA explicitly implements `A0/2`.

Rolfsen link mappings used by this atlas are written in `manifests/SOURCE_MAP.json`. In particular, `9^2_20 -> L9a28` and `9^2_40 -> L9a32`; `7^2_8 -> L7n2`; `8^2_1 -> L8a14`.

## Redistribution caution

The user's upstream Ideal-Sources provenance file marks the public redistribution/licence status of the original Knot Atlas/Gilbert record files as unresolved. PKLSA therefore does **not** bundle those upstream `.gz` files. It contains derived sampled seed coordinates plus record identifiers/hashes. Before publishing this atlas as third-party supplementary data, resolve the upstream redistribution/licensing question or publish the reconstruction recipe and require users to supply the upstream archive.
