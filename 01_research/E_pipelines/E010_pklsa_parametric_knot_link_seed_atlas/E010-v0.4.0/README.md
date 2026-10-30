# PKLSA / E010 v0.4.0 - Combined Seed Atlas

This portable ingestion release combines 4,497 historical v0.3.1 carriers across
2,227 topology labels with 3,630 nominal and 3,630 perturbed v0.3.6 Ruban geometries.
The 11,757 records are NOT 11,757 topologies or independent providers.

## Scientific boundary

All historical outputs, including failures, remain byte-preserved in `history/v031`.
New Ruban records are `RESEARCH_GEOMETRY_UNADMITTED`, `production_admission=false`,
`dynamic_stability=NOT_TESTED`. All 54,450 proposed scenarios remain PENDING/NOT_RUN.
These samples are one analytic source group, with zero new independent empirical
providers. Native coordinates and dimensionless R0=1 are not automatically SI.
No dynamics, relaxation, normalization, finite-core certification or isotopy proof
is performed. Research inclusion does not change any falsifier admission contract.

## Build or verify on Windows

Use Python 3.14 and the pinned existing dependencies in `requirements.txt`.
From the version directory, `run_all.cmd` runs tests, verifies pinned inputs,
builds the output in a temporary directory, checks a portable ZIP extraction and
publishes a ZIP/SHA-256 plus a technical PDF in the parent family directory.
`run_all.cmd SELFTEST` runs only the targeted regression tests.
`run_all.cmd VERIFY` verifies an already published payload and archive.
An identical repeat is verification-only; all previous logs and artifacts remain.
No command here starts a scientific campaign. Invalid commands fail closed.
Initial build requires the exact inputs described in `configs/SOURCE_INTAKE.json`.
After publication the portable data can be verified without those input locations.

## Using the extracted ZIP

From the extracted output directory run `py -3.14 -B verify_atlas.py`.
Use `--all-geometries` to additionally load/hash every parsed geometry.
The reader needs NumPy 2.4.4; reportlab is needed only to build the technical PDF.

```python
from sst_pklsa import CombinedSeedAtlas
atlas = CombinedSeedAtlas('.')  # extracted output root
historical = atlas.list_ids()  # 4497: does not assert production qualification
all_ids = atlas.list_ids(include_research=True)  # 11757
identity = 'RUBAN_v036_T_3_3_B0200_N1024_nominal'
metadata = atlas.describe(identity)
parts = atlas.load(identity, allow_research=True)  # three ordered arrays
provenance = atlas.provenance(identity)
```

All file lookups used by the reader are relative and constrained to the payload.
Original absolute paths remain only as frozen historical evidence. Original v0.3.1
`Carrier`, XYZ/VECT/Fourier/Gilbert parsers and geometry hash definition are reused
byte-for-byte. Fourier coefficients use the original 4096-point sampling convention;
Ruban XYZ components retain all 1024 points without resampling.

## Payload and integrity

`COMBINED_INDEX.json` joins native geometry, provenance and separate gate axes.
`FILE_MANIFEST.json` hashes every payload file except itself; the archive's external
SHA-256 pins the entire package including that manifest. `DUPLICATES.json` records
shared raw files and exactly equal ordered float64 geometries without removing IDs.
It does not detect equality modulo translation, rotation, resampling or isotopy.
Nominal/perturbed IDs remain distinct even if equal. Unmapped topology labels stay
null; supplied labels and analytic certificates are preserved without promotion.

The original Drive manifest and metadata are retained in `provenance/`.
The source is user-authorized, not independently publisher-authenticated.
The new research binding points to v0.3.6; the old v0.3.5 overlay is not edited.
Family `latest`, the active v0.3.4 view and existing pinned consumers are unchanged.
