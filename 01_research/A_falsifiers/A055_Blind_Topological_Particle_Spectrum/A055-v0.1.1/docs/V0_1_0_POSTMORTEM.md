# v0.1.0 postmortem and v0.1.1 correction basis

The first executed campaign was generated before the falsifier number was corrected and therefore carries A054 filenames.  It is retained as historical evidence; v0.1.1 is canonically A055.

Input output archives reviewed for this patch:

- BLIND ZIP SHA-256: `3f4dc64471a1cea0e11b9e660322d8c6e522e77b4bb29d05d6a83fa490d7a59a`
- REVEALED ZIP SHA-256: `5e85e844f1e53695f7d9c75973e8a11bcb9e0410ca8da2abca8f78a1c94a4b7e`

The executed v0.1.0 basic configuration used:

- 40 points/component;
- 2 embedding replicates;
- 5 null targets;
- one mixed feature space containing `bend_energy`, `abs_neumann_energy`, `contact_ratio`, `abs_writhe`, and `linking_strength`.

Observed historical result under that old metric:

\[
\operatorname{rank}(5_2,6_1)=551/595,
\qquad
D=3.2892952078460436.
\]

The v0.1.0 reveal also reported:

- a very close `W/Z/H` fit using `contact_ratio`, but a null fraction of 0.667 with only five null trials;
- an `up_quarks` best mixed-atlas fit using `linking_strength`, even though knots have no pairwise linking observable.

These outputs motivated the v0.1.1 corrections:

1. `contact_ratio` is removed from primary ranking and ratio search;
2. `min_distance` is used as the resolution-compatible contact observable;
3. `linking_strength` becomes links-only;
4. mixed `abs_writhe` use is forbidden;
5. resolution and embedding-CV qualification are mandatory;
6. null trials increase to 10,000;
7. raw and qualified pair tables are separated.

The v0.1.0 result is **not** overwritten or retroactively reinterpreted.  v0.1.1 creates a new campaign with a new opaque mapping and new blind seal.
