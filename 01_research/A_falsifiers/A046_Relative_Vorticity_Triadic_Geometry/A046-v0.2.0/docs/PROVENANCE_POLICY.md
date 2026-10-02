# v0.2.0 provenance policy

The release identity is frozen as:

- catalog: `A046`
- version: `v0.2.0`
- package: `sst-triadic-a046==0.2.0`
- source directory: `A046-v0.2.0`
- output directory: `A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs`

`run_all.cmd` stores and seals:

- Python campaign log;
- Python pytest log;
- Python runtime metadata;
- native build log;
- native campaign log;
- native pytest log;
- native module path, size, and SHA-256;
- Python/native parity summary;
- both backend blind summaries and case metrics;
- prepare/config/source-manifest hashes.

The reveal stage refuses to proceed if any sealed file has changed.
