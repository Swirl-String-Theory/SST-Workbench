# SST Framework v1.0.9 release validation — 2026-10-17

- Parent v1.0.8 source: **99/99** SHA-256 checks matched the parent `PACKAGE_MANIFEST.json` as distributed with A062-v0.7.0.
- Linux Python 3.13 environment: **72/72** pytest regressions passed.
- v1.0.8 two-run archival/PDF smoke rerun on v1.0.9: **PASS**; two distinct BLIND PDF/ZIP publications, previous working output preserved.
- v1.0.9 report-only integration: **PASS**; one blind run + 2 separate `REPORT_ONLY` PDF rerenders; original PDF/ZIP unchanged; science evidence manifest and final output manifest unchanged and verified.
- Visual: generated A4 PDF rendered and inspected; gate table no longer overlaps/truncates status/question columns in the smoke example.
- Portable protocol hash: CRLF-versus-LF normalizes to same additional diagnostic SHA, whereas byte-exact `bundle_sha256` intentionally differs; changed content changes portable SHA.
- Circular PDF hash: report displays immutable science evidence SHA and defers to separate final output manifest; same identifier survives report publication/rerender.
- Ten backend/science contract source files (listed in `SOURCE_PROVENANCE.json`) **byte-identical** to v1.0.8.
- Release-clean source check and ZIP checksum recorded at packaging.

**Certification boundary:** No Windows MSVC/oneAPI/Arc A770 execution was possible in this Linux environment. Carried-forward earlier hardware JSON is historical validation of unchanged kernels only. Run `run_all.cmd ALL` on the Windows target and retain a new `BACKEND_SELFTEST.json` before calling its native backends qualified on that installation.
