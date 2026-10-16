# A058 changelog

## v0.2.10 — numeric getter precision and provenance-qualified reuse

- Corrects the state acceptance bug: compares at six-decimal getter **display** precision, with half-decimal-unit tolerance. The failed v0.2.9 measurements are not rewritten; the confidence label is `ROUNDED_GETTER`, not internal FP64 identity.
- Uses a compulsory numeric getter alias for S3 and genuine getter switch aliases for R2/R3; checks both initial and final states. No setter-only exception remains for S3.
- New `run_all.cmd IMPORT_BASIC "<old v0.2.9 root>"` re-audits complete prior BASIC evidence and copies it into a new instance while retaining the original statuses and independent immutable BLIND/FREEZE archives. Writes a source-bound overlay; heavy selection validates this overlay **and final coordinate hashes**.
- On the supplied historical private source: 237/271 getter/safety/iteration-qualified, including **143 of the originally rejected conditions**; R4 34 remain unsupported.
- Keeps BASIC=512, 2048=full 271, 32768=up to 31 preselected, registered design and Framework-v1.0.8 unchanged.
- New private material and fresh preregistration are generated separately from the preceding version.

## v0.2.8

Previous version preserved separately. Historical source/provenance available in v0.2.8 ZIP.
