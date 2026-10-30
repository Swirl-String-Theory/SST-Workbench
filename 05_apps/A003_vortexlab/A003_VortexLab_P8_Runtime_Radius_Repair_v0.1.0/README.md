# A003 VortexLab P8 — focused playback & radius repair (v0.1.0)

**Input**: the exact `A003_vortexlab_29-10.zip` version. Patch, not full replacement.

## Diagnosed code defects and changes

1. `input type=number step="any"`: the ^/v buttons used a fallback increment of `1` (1 mm for `a_sim`). That immediately hit the geometry maximum. The buttons now use a small bounded nudge; physics clamps remain intact.
2. Heavy per-frame HUD: for large N, `velAll` and Gauss/linking diagnostics ran O(N^2) work at near-frame rate and competed with the integrator. This patch *only* throttles visual readouts for larger N; physics step, timestep/clock, contact and topology gates are unchanged.
3. Twist Flow P7.2 intentionally used Model A/ideal visual radius independently of `a_sim`. A new checkbox **Getekende buisstraal = numerieke a_sim** explicitly allows viewing the numerical radius instead. Switching back restores Model A visuals. The solver remains unchanged by this checkbox.
4. Tube rendering failures were swallowed with `catch(e){}`. Errors now appear in the console and the radius HUD (`RENDER_ERROR`), not silent failures. Clamping emits a clear reason on the existing core note.
5. Existing isolated CFL unit test omitted a new `vlDiscrete.active()` dependency; added only this test stub.

## Installation (Windows)

Extract this patch folder **next to** the existing `run_all.cmd` (or any location). In `cmd.exe` from the A003 root:

```bat
py ".\A003_VortexLab_P8_Runtime_Radius_Repair_v0.1.0\install_patch.py" --target .
py ".\A003_VortexLab_P8_Runtime_Radius_Repair_v0.1.0\install_patch.py" --target . --apply
node --check apps\web\src\legacy\vortexlab-runtime.js
node tools\test-twist-flow-cfl-p5.mjs
node tools\test-tube-ropelength-p71.mjs
npm start
```

Open `http://127.0.0.1:4173` for the main VortexLab. Import `N256/..xyz` first and use **MODEL → KERN → numerieke buisstraal a_sim**; choose tube display and check `tubeThicknessInfo`. The accepted geometry limit still applies and a requested value above it is clamped with an explanatory warning.

For Twist Flow (`/twist-flow/`), new checkbox **Getekende buisstraal = numerieke a_sim** selects numeric tube display instead of the visual Model A thickness.

## What is and is not qualified

Targeted automated JS tests passed in package environment. The broad upstream `npm run check` is **not green in this snapshot**: physics parity requires an external `/mnt/data/SSTcore` module absent here, and an existing P4 test pins an older legacy runtime hash. Do not change pinned scientific reference hashes to force a green result.

**Browser visual playback, video capture, and all catalog families are NOT end-to-end certified here.** A halted simulation (`flagged`) will still stop on genuine contact/out-of-domain/precision violations. For a stubborn case export the console error, core/max reading, chosen geometry/N and `__vlTwistFlowDiagnostics()` readout.

No underlying `B007`, `E010`, SSTcore or scientific status is modified.
