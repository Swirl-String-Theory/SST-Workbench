# E010 PKLSA v0.3.0 — production runner patch (2026-09-21)

Extract/copy this patch **over** the canonical directory:

`01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.3.0/`

It adds/replaces the top-level `run_all.cmd`, adds a production orchestration helper, and adds production source maps. It does **not** overwrite the PKLSA Python package itself.

## Run

From an ordinary CMD or x64 Developer Command Prompt:

```bat
run_all.cmd C:\workspace\projects\SST-Workbench
```

The Workbench argument is optional; that canonical path is the default.

## Execution order

1. Create/refresh `.venv` using the existing `run_00_setup.cmd`.
2. Build and import `pklsa_builder._native` (MSVC + pybind11).
3. Run `pytest -q tests`.
4. Validate the current source contract against the live Workbench.
5. Deep-hash and inventory the A001–A008 semantic source families using current post-restructure paths.
6. Filter the old unregistered-source detector against all explicitly registered current source-contract roots; unknown high-confidence source roots still block the run.
7. Ingest bundled KnotInfo and LinkInfo databases.
8. Derive the topology set from the admitted live geometry sources; no historical topology count is hard-coded.
9. Run `3_1` first with `qualification_extended.json` as a proof-of-concept gate.
10. If the POC passes, run every discovered knot/link with `qualification_publication.json`.
11. Require both geometry qualification and an upstream KnotInfo/LinkInfo identity match for every topology.
12. Write `RELEASE.json`; only a complete green run gets `publication_ready_geometry_layer=true`.
13. ZIP the complete output and write a SHA-256 sidecar beside the E010 family.

## Important provenance decision

The missing 98 NPZ files in `E010-v0.1.1` are **not reconstructed or invented**. That historical tree remains provenance/packaging evidence. The production run uses the canonical live Workbench sources plus E009/PTSA and therefore does not require either the missing v0.1.1 NPZ payload or a historical PKLSA v0.2.0 ZIP.

## Output

Inside `E010-v0.3.0`:

`E010_PKLSA_Production_Knot_Link_Basis_v0.3.0-outputs/`

Beside the version directory, under the E010 family:

- `E010_PKLSA_Production_Knot_Link_Basis_v0.3.0-outputs.zip`
- `E010_PKLSA_Production_Knot_Link_Basis_v0.3.0-outputs.zip.sha256`

Interrupted runs can be resumed. Resume is refused if the Workbench path, source maps, qualification configs, package manifest, or runner changed.
