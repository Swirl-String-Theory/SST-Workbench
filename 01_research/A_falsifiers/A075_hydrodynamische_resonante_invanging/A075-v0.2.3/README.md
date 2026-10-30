# A075-v0.2.3 — 3D Euler finite-core localization and knot-screening

**Status: DEVELOPMENT_ONLY; physical question UNRESOLVED.** No claim of lasting capture or photon identification. Source extends A075-v0.1.0 without changing its frozen protocol. The entire v0.2.3 protocol is new and has **not been frozen using the authentic Framework v1.0.10 in this environment**. The framework itself is NOT bundled.

## Central falsifier question
Can a freely evolving, fully coupled vortical receiver retain positive additional local energy **after** the incoming excitation has independently departed, for many independent receiver cycles, while local energy flux, core deformation and convergence all close?

## Science engine
- Fully 3D *periodic Fourier-Galerkin* incompressible Euler reference solver; `dt` fourth-order Runge–Kutta, 2/3 de-aliasing, Fourier-Leray projection, pressure-Poisson (via Lamb-vector projection), and zero viscosity.
- Three smooth finite-width vorticity objects: two receivers and a separate incoming `0_1`; never prescribes a circular configuration during evolution. Finite-core *initial condition* uses Gaussian Fourier smoothing of a solenoidal deposited filament current. It is not an independently established superfluid/physical core constitutive model.
- Analytic `0_1` unknot and `3_1` T(2,3) trefoil; original `5_2`/`6_1` files are **required** for their cases (see `inputs/README.md`). No artificial substitution.
- Matches no-donor and donor run in the **same translating fixed-shape smooth control window** (the center is determined from the no-donor run). Smooth window flux balance must converge with resolution/width. This is not a deforming material volume, though the moving-frame formula is exact for an arbitrarily prescribed boundary velocity in the continuum.
- Measures total kinetic-energy drift, `div(u)`, maximum Courant number, approximate moving-window pressure-energy flux and separately compares spatial and temporal refinements at the identical final absolute time.
- Does not infer source exit from apparent z-centerline displacement; must verify material-core departure with separate tracers/vorticity diagnosis before G3 can pass.
- Receiver oscillation probe is not qualified as clock unless multiple resolved peaks exist with stable period under mesh/time/geometry changes; no cycles are invented.
- `PREVIEW` is deliberately underresolved for software smoke. `BASIC` samples 4.0 and 5.6 grid cells per Gaussian sigma, while `FULL` samples 4.8 and 6.4; neither result proves physical convergence, donor departure or retained energy.

## Execution — Framework v1.0.10 with selectable CPU grid and thread count

The shared Framework is **required** for `FREEZE`, `BASIC`, and `FULL`.

```bat
python -m pip install -r requirements.txt
python -m pytest -q tests
python tools\preflight_contract.py
python tools\prepare_private.py
run_all.cmd FREEZE
run_all.cmd BASIC --grid 80 --threads 12 --plan
run_all.cmd BASIC --grid 80 --threads 12
run_all.cmd FULL --grid 128 --threads 12 --plan
run_all.cmd FULL --grid 128 --threads 12 --allow-expensive
```

`--grid 80` and `--grid=80` both work; with no mode, `BASIC` is assumed. The specified grid is the **coarse** N^3 grid; the spatial refinement grid is chosen independently by `--grid-up` or defaults to approximately 1.4N (rounded to multiple of 8). Both a base and half absolute time-step are run. Examples:

```bat
run_all.cmd BASIC --grid=80 --grid-up=112 --dt=0.015 --threads=12
run_all.cmd FULL --grid 128 --grid-up 160 --dt 0.010 --threads 12 --allow-expensive
run_all.cmd BASIC --grid 64 --knots 0_1,3_1 --threads 12 --plan
run_all.cmd GPU_PROBE
```

`GPU_PROBE` uses the actual shared Framework v1.0.10 SYCL device worker to probe the Arc A770, writing `diagnostics/arc_device_probe.json`. **This is not an Euler GPU backend or GPU parity.** `--backend arc` is deliberately rejected: the shared worker implements a Biot–Savart operation, but A075 needs Fourier transforms, the Leray projector, pressure and RK4 on the device. No automatic fallback, no false GPU qualification.

`cpu-scipy-fft` delegates FFTs to SciPy's native, multithreaded pocketfft library (`workers=12`); no compiler/pybind11 needed. The reference `--backend cpu-numpy-reference` is included for parity. `threads` applies to FFT workers, not twelve concurrent independent simulations; speedup depends on the grid and RAM bandwidth.

Each run writes `EXECUTION_OPTIONS.json`, provenance, output manifests and the Framework gate ledger. The `science_contract.json` contains frozen allowed grid/backend ranges. The intended run matrix must be recorded *before inspecting scientific results*; the runtime selection is a declared exploratory parameter unless separately preregistered. Selecting a new combination after inspecting results remains exploratory: scientific claims still require an independently frozen specific test matrix and holdout. Do not edit a prior version's `FROZEN_PROTOCOL.json`. `FULL` usually requires `--allow-expensive`; inspect `--plan` first. Limits are guards, not accurate time/memory predictions.

No source geometry is invented: `5_2`, `6_1` require original `inputs/KNOT_5_2_N2048_ORIG.xyz` and `inputs/KNOT_6_1_N2048_ORIG.xyz`. If absent, these cases are `BLOCKED` rather than fake substitutes. Test the Euler response before claiming knot topology retention.

## Frozen prerequisites and acceptance gates
- G0: authentic framework v1.0.10 FREEZE, with **new private key/commitments**; prior v0.1 private metadata is not reusable.
- G1: byte-verified A021/A032 methodology sources; geometry hashes and independent topological identity checks for 5_2/6_1.
- G2: solver no-loss plus distinct fixed-physical-time spatial and temporal diagnostics with resolved core width (>= 4 grid cells per Gaussian sigma in BASIC/FULL, *necessary not sufficient*).
- G3: predeclared source exit, no-return, minimum late excess significantly greater than all error budgets, >=100 independently resolved local receiver cycles, closed pressure and advective flux.
- G4: preregistered held-out configurations before inspecting positive capture data.
- G5/G6: native C++ and device parity remain not run.
- G7: independent geometry source and knot family sensitivity.
- G8: full periodic-box/core-profile/control-volume convergence and verified vorticity/topology fidelity. A Fourier-Galerkin field *implementation* does not mean fully physically resolved Euler.
- G9: private reveal prohibited until qualifying G8 and locked framework permissions.

## Scientific non-promotion
An initial donor field overlaps the receiver, and the initial total energy is not the isolated donor self-energy (kinetic cross term). A positive short-time window-energy difference is **not** absorbed donor energy. The smooth window tracks a passive marker, not an automatically material surface. Periodic replicas can create delayed interactions, hence box-size independence is an additional gate. A Gaussian starting vorticity width is not synonymous with a dynamically proven finite-core equilibrium. The user-provided analytic trefoil is an initializer, not an asserted stable eigenmode. Do not promote intrinsic clock, Floquet, photon absorption or atomic ontology.


## v0.2.3 numerical resolution and CPU-parallel execution campaign

The physical Gaussian kernel width remains a=0.50 and periodic box side remains L=10 across the resolution ladder. PREVIEW (48^3 -> 64^3, dt 0.020 -> 0.010, T=0.6) is **underresolved**. BASIC (80^3 -> 112^3, dt 0.015 -> 0.0075, T=1.2) is an initial spatial/temporal screening. FULL (96^3 -> 128^3, dt 0.010 -> 0.005, T=9) is intended to improve spatial and temporal accuracy without changing physical core sigma. All comparisons inside each profile use *the same final absolute time*. Increased resolution does **not** prove 3D Euler capture. Dynamic core sharpening, box-size interactions, donor departure, cycle count and window-flux convergence remain independent gates.

Run `python run_preview.py --profile BASIC --plan` to see the actual proposed grid sizes, spacings, RK4 steps and conservative one-field memory proxy **without computing**. The full run will be significantly more expensive. The SciPy FFT provider runs CPU-parallel FFTs, while A075 full Euler GPU/SYCL remains blocked pending a device-specific solver and parity evidence. Source/metadata of the frozen v0.2.0 campaign must NOT be modified in place; place v0.2.3 in its own catalog version folder and create NEW blind commitments.


## v0.2.3 adaptieve tijdstap en backendmatrix

Een nieuw A075-versienummer is vereist: wijzig nooit protocolbestanden van een
bestaande `FROZEN_PROTOCOL.json`.

```bat
python -m pytest -q tests
python tools\build_native.py
run_all.cmd BASIC --grid 80 --grid-up 112 --dt .015 --adaptive --cfl .15 --threads 12 --backends py,cpp,gpu --plan
python tools\prepare_private.py
run_all.cmd FREEZE
run_all.cmd BASIC --grid 80 --grid-up 112 --dt .015 --adaptive --cfl .15 --threads 12 --backends py,cpp,gpu --allow-expensive
```

`--backends py,cpp,gpu --require-all-backends` weigert vroegtijdig als er een
backend ontbreekt. Zonder `--require-all-backends` gaan werkende backends door
terwijl ontbrekende backends `BLOCKED` worden, nooit stilzwijgend CPU.
`--fixed-dt`, `--max-core-shift`, `--max-vorticity-turn`, `--dt-min`,
`--gpu-precision fp32|fp64`, `--diagnostic-stride`, `--t-end` zijn optioneel.
Voor `EXTENDED` is het standaardtijdvenster 3 absolute eenheden; de presets
kiezen een maximale tijdstap, waarna CFL/core/rotatie deze dynamisch verlagen.

De GPU route is PyTorch XPU (Intel Arc), **niet** de Biot-Savart SYCL
worker van Framework v1.0.10. Je hebt een PyTorch wheel met Intel XPU-
ondersteuning nodig; `torch.xpu.is_available()` moet `True` zijn.
GPU `fp32` blijft **SCREENING_ONLY** en wordt nooit als FP64 gecertificeerd.

`*_base_energy_matrix.csv`, `*_dt_half_energy_matrix.csv`, en
`*_space_up_energy_matrix.csv` onderscheiden numerieke energieverlies/-winst
per iteratie van de bewegende controlevolume-flux (in `timeseries`).
Een blijvende positieve lokale extra-energie is geen claim zolang de donor
niet bewezen vertrokken is en de klok-/convergentiegates ontbreken.


PyTorch XPU is listed by current PyTorch documentation as supporting Intel
Arc A-Series on Windows 11. Install from the official XPU selector:
https://pytorch.org/get-started/additional-platforms/
If `torch.xpu.is_available()` is false, `--backends ...gpu` will mark GPU
BLOCKED, and `--require-all-backends` will refuse the campaign. Do not assume
native FP64 availability or numerical parity on an Arc A770.
