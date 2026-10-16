# CHANGELOG

## v0.1.4
- Recovery-analysis release for completed v0.1.3 acquisition; no KnotPlot rerun.
- Corrected Framework-v1.0.6 gate semantics: G4 confirmation, G5 CPU certification, G6 GPU, G7 cross-source replication.
- Moved A058 plateau/resolution/generator convergence decision to G8.
- Added read-only v0.1.3 campaign importer with file hashing and completeness checks.
- Treats zero-byte KnotPlot metrics CSVs as missing and derives geometry metrics from the complete ASCII coordinate checkpoints.
- Fixed source-contract Workbench-relative paths.
- Added coordinate-only null/liveness, plateau, resolution and generator diagnostics.
- New private key/nonce and new protocol version; v0.1.3 remains immutable provenance.

## v0.1.3
- Prior acquisition release.
