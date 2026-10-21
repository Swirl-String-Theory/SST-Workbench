# v0.3.4 launcher validation

- 38/38 automated Python tests PASSED, using `A058_KPDIST_ZIP` pointed at the user-supplied `kpdist-23mar2025.zip`. No skipped tests.
- New regression coverage: relative `.` and `./`, relative EXE-parent and link-parent paths, ambiguous relative path rejection, absent path rejection, absolute CLI override, direct EXE fallback, diagnostic CHECK_SHORTCUT output, immutable probe scripts and absolute export routing.
- `py_compile` for launcher, probe driver and inspector PASSED.
- Test environment was Linux; WScript.Shell resolution was mocked for Windows cases. No real KnotPlot.exe or user's actual `.lnk` was executed.
- The original v0.2.9 science engine, its 271-condition registration, private commitments and gates are unchanged.
- This **does not qualify** native `go 32`, runtime param getters, `safe` outputs or the dstep negative control.

---

# A058 v0.3.2 — validation receipt (2026-10-21)

## Executed on real user-provided source archive

- Input: `/mnt/data/kpdist-23mar2025.zip`, SHA-256 `cb4e49983d18ea373fa2f1f3c63ca0900e0a8093130830c4810cc50e85b50509`.
- 9,268 ZIP entries, explicitly no included KnotPlot solver implementation or executable in this release.
- 15/15 archive-static source/documentation tests: PASS.
- Binary KPF 1.0 native catalog test, big-endian `LOCS`: `basic/0_1` (42), `basic/3.1` (47), `basic/4.1` (69), `basic/8.19` (86): 4/4 supported single-component entries parse correctly.
- `basic/6.3.3` link: **UNSUPPORTED_LINK_OR_ENCODING** (multiple `comp` chunks), deliberately rejected, not a physics FAIL.
- Independent, closed-polyline 3D nonadjacent-segment proximity: four supported snapshots report `SNAPSHOT_CLEAR`. This is an *instantaneous* centerline result, not a topological invariant, swept-cylinder proof or no-reconnection guarantee.
- 22/22 local regression tests: PASS, including all 10 inherited v0.3.1 coordinator tests and 12 v0.3.2 tests.
- Tested independent geometry decode: LOCD, LOCF, LOCS, LOCC (including first bead regression); non-finite, truncated, unknown-section, and multicomponent inputs fail closed.
- Independent safe native control generation: PASS; two equal-budget 32-step Damped candidates (`dstep = 1`, `dstep = 4`), `collision fast`, no velocity/tangent/thermal/gravity terms, exact common seed SHA-256.
- `AUDIT_ALL` fail-closed on nonempty output directory: PASS.
- `SOURCE_EVIDENCE.json`, `GUI_CONTROL_MATRIX.csv`, `PARAMETER_EFFECT_MATRIX_TEMPLATE.csv`, `KPF_AUDIT.csv`, and hashes generated.

## Explicitly untested

- Native Windows KnotPlot-v2026 execution of the generated probe scripts: **NOT RUN**.
- Whether all six parameter command switches used in generated scripts are recognized by the current binary: **NOT VERIFIED**.
- Native `safe` response validation, output `data format` compatibility, 32-step `dstep` null equivalence: **NOT VERIFIED**.
- `No Collide` topology/no-reconnection guarantee between checkpoints: **NOT ESTABLISHED**.
- Original v0.3.0 clone FREEZE / BASIC / 2048 / FULL repaired by v0.3.1 relative-framework patch: **NOT RETESTED**.
- Old A058 gates and old private data: **UNMODIFIED**.
- Physical vortex dynamics / Euler / Biot-Savart / PKLSA self-confinement: **NOT INFERRED**.

## Boundaries

The original distribution is source evidence, not the entire KnotPlot engine. The release does not bundle the copyrighted distribution, the executable, source secrets, old runs or blind map. The user must supply their own ZIP and real installed executable for future native qualification. No new canonical SST physical claims are promoted.

## v0.3.3 shortcut working-directory correction (2026-10-21)

- Original v0.3.2 failure demonstrated by source audit: native probe
  `subprocess.run(... cwd=out/dstep_N)`, ignoring `.lnk` WorkingDirectory;
  feeding `.lnk` to CreateProcess causes WinError 193.
- Added Windows PowerShell/COM shortcut metadata parser; explicit target EXE
  and Start-in directory; fail-closed missing files or invalid Start-in.
- Added generated per-run `probe.native.kpc` that rebinds seed and the two
  output filenames as **absolute** paths to each A058 probe result folder.
  The registered `probe.kpc` is never modified.
- All 29/29 offline unittest tests pass with `A058_KPDIST_ZIP` set to the user-
  supplied historical distribution. Six Windows-shortcut/relative-path tests
  and a mock process test were added. Actual native Windows execution **NOT_RUN**.
- This is not a fix or certification for getter readback, solver iterations,
  topology safety or unreviewed program-level side effects.
