# A003 Twist Flow P7 v0.7.1 — Ideal Ropelength Tube Visualization

## Scope
This is a **CMD install overlay** for an existing **P7 v0.7.0** installed A003_vortexlab checkout, based on `A003_vortexlab(2).zip` and the exact previous P7 installer. It does NOT run on the pre-P7 base without installing P7 first.

### Core correction
The old `displayTubeRadii()` used `a_sim` (e.g. 0.00012415 m) for Three.js TubeGeometry even when a Gilbert-ideal reference predicted a relatively thick physical tube. A thin amber line therefore became even less visible when tube display was enabled.

Only on `/twist-flow/`, the new display path constructs a **solid, opaque lit tube**. For **eligible Gilbert ideal single-component knots**:

- reference visual diameter (in VortexLab scene coordinates): `D_scene(0) = L_scene(0) / (L_metadata / D_metadata)`.
- With this reference, P7's hypothesis `a(0) = r_c` yields `physicalPerSimMeter = (2*r_c*(L_metadata/D_metadata))/L_scene(0)`; this is NOT equal to the scene's `a_sim`.
- At later times, each material segment's equivalent area-conserving radius changes as `a_j/a_0 = sqrt(dl_j(0)/dl_j(t))`.
- Tube rings are sampled at equal arclength, interpolating the adjacent material radii. True elliptical cross-section, self-contact/reach and continuous Euler vorticity are **not solved**.
- In physical interpretation, `D_physical(0)=2*r_c`; do not confuse scene meter and physical meter. Model A still reports physical fm scalings.

For **A006 twist and KnotPlot relaxed candidates**, the renderer does NOT fabricate ideal ropelength. It displays an adjustable **schematic-only** tube, with radius 2%–30% of the live knot xy radius, default 12%; the UI labels it accordingly.

Never changes numerical Biot–Savart softening `P.a`, circulation, contact/guard, native N, physics time or topology. Original VortexLab `/` and benchmarks retain their old renderer.

## CMD install

1. First install existing P7 v0.7.0 CMD overlay, if not already installed.
2. Close `npm start` and open CMD in the unzipped patch folder.
3. `Apply-P7.1.cmd --dry-run` then `Apply-P7.1.cmd`.
4. Start with `cd /d C:\workspace\projects\SST-Workbench\05_apps\A003_vortexlab` and `npm start`.
5. Open `http://127.0.0.1:4173/twist-flow/`; select `Gilbert ideal 3:1:1`, enable `Vortexbuis zichtbaar`, and verify thickness. Disable checkbox: only centerline should remain. For KnotPlot/A006 adjust schematic thickness slider.

Default target: `C:\workspace\projects\SST-Workbench\05_apps\A003_vortexlab`; override with `--target "C:\...\A003_vortexlab"`.

Installer: Python standard library only (via `py -3` or `python`), strict P7 SHA256 preflight, automatic backups, node regressions and transactional rollback. `--dry-run` never writes. Does not require PowerShell. Installer does not silently reinstall/upgrade SSTcore.

## Tests and status

- Node syntax and new P7.1 diameter/stretched-radius tests, P7 material tests, existing `test:twist-flow`, `test:native`, `test:fluid`, and source-hash verification.
- This is **render/diagnostics research-track only**, not dynamic finite-core coupling or a stability proof.
- Application-wide `npm run check` may still require native `sst-core` Node addon, not just `pip install SSTcore` Python package.
- Full interactive browser/graphics behavior requires a local visual smoke test.
