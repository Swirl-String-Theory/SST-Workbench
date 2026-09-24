# KnotInfo / LinkInfo / KAtlas integration

## Legacy `.xls`

The bundled legacy databases are read with `xlrd>=2.0.1`. The builder does not convert them through office software. For every database source it stores the exact archive/file SHA-256, workbook/sheet profile, source row number and raw fields.

The uploaded LinkInfo workbook visibly contains fields such as PD notation, Gauss notation, braid notation, Knot Atlas name, Rolfsen name, Alexander/Jones data and linking matrices. The same schema-driven ingester is used for the KnotInfo database.

## Mapping rule

KnotInfo ↔ Rolfsen ↔ Hoste–Thistlethwaite mapping is evidence-derived:

1. find notation-like labels on one upstream row;
2. preserve all those labels as aliases of that record;
3. expose the crosswalk only through those co-occurrences.

The builder does **not** infer that `K3a1` equals `3_1` from enumeration order alone.

## PD / DT / Gauss / braid comparisons

These representations are generally non-unique. Exact normalized string equality is strong bookkeeping evidence, but different strings are not automatically a topological mismatch. `reference_comparison.json` therefore distinguishes exact string matches, missing values, and “available on both sides but non-unique representation”.

## Geometry certificate boundary

Reference-database agreement is not a complete classifier for a sampled 3-D curve. Optional external curve/diagram providers may be installed independently; final publication campaigns should record those provider versions and failures explicitly.
