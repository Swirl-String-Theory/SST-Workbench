# Helmholtz_SST_Vortex_Gates_Falsifier_v0.1.1

Windows-first, target-blind Python/C++ workbench for relaxed KnotPlot/RidgeRunner centerlines.

Default input directory:

```text
C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
```

The native layer follows the established `SST_cpp_pybind_audit_template` architecture: C++17 hot kernels, pybind11, automatic build-if-needed, NumPy/Python fallback, and native-vs-Python parity tests.

## What is tested

- **H0-GEOMETRY** — closed-centerline/data-integrity precondition.
- **H1-CONVERGENCE** — finite-core self-energy and relative-equilibrium resolution convergence.
- **H2-HOLONOMY** — unit-circulation meridian-loop integral versus integer topology.
- **H3-RELATIVE-EQUILIBRIUM** — the main Helmholtz-inspired falsifier: after removing best rigid translation, rigid rotation, and tangential reparameterization, the remaining normal self-induced velocity must be small.
- **H4-SYMMETRY** — orientation/circulation reversal and mirror covariance.
- finite-core energy and core-radius sensitivity diagnostics.

Static centerlines **do not** test Helmholtz material-line persistence in time, time-dependent vortex-flux conservation, or the SST `rho_f` torsion impedance lemma. Those are explicitly reported as untested rather than inferred from static geometry.

## One-click commands

From a fresh extraction:

```bat
run_all_basic.cmd
```

creates the virtual environment, installs dependencies, compiles C++, runs synthetic controls, and audits up to three relaxed knots.

For the recommended normal campaign:

```bat
run_all_normal.cmd
```

This goes from installation through controls/tests to a blind campaign over every `*_final.txt` file in the default knot directory.

For the heavier resolution campaign:

```bat
run_all_extended.cmd
```

`run_all.cmd` is an alias for `run_all_normal.cmd`.

## Individual stages

```bat
run_00_install.cmd
run_01_basic.cmd
run_02_normal.cmd
run_03_extended.cmd
run_05_native_parity.cmd
run_06_synthetic_controls.cmd
run_90_tests.cmd
```

Override the knot directory without editing files:

```bat
set SST_KNOTS_DIR=D:\my\relaxed\knots
run_all_normal.cmd
```

Override native threads:

```bat
set SST_NATIVE_THREADS=16
run_all_normal.cmd
```

## Blindness and reveal

During the campaign the console prints only blind IDs. Filenames are stored under:

```text
outputs_*\private\reveal_map.json
```

Do **not** inspect that file until `frozen_result.json` and `frozen_result.json.sha256` exist.

Then reveal with:

```bat
run_04_reveal.cmd C:\path\to\outputs_normal_YYYYMMDD_HHMMSS\frozen_result.json
```

Reveal adds identity and secondary SST interpretations. It does not retroactively change blind scientific status.

## Important density/torsion separation

The blind finite-core calculation returns a geometry coefficient `energy_length_reference` such that

\[
E=\rho\Gamma^2\ell_E.
\]

Blind scoring does not substitute either SST density. Post-freeze reveal reports both:

- bulk Helmholtz interpretation using `rho_f = 7.0e-7 kg m^-3`;
- a conditional `rho_core` interpretation, clearly labeled conditional.

The transverse torsion research-track relation is kept separate:

\[
c_T^2=K/\rho_{\!f},\qquad Z_{\rm torsion}=\rho_{\!f}c_T.
\]

No torsion closure is claimed from static relaxed knots.

## Exit behavior

The `run_all*.cmd` scripts return nonzero only for installation/build/input/pipeline failures. A **scientific falsification is a successful run** and is recorded in the frozen output. To turn scientific failures into exit code 2, call `run_campaign.py` manually with `--strict-exit`.

## Outputs

Each campaign creates:

- `summary.json`
- `frozen_result.json`
- `frozen_result.json.sha256`
- `<blind_id>.json` per completed sample
- `private/reveal_map.json`
- after reveal: `revealed_result.json` and `revealed_summary.csv`

Read `SCIENTIFIC_BASIS.md`, `BLIND_PROTOCOL.md`, and the files under `schemas/` before interpreting a pass.
