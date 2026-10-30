# A026 HSM v0.1.0 - Hidden-State Memory & Reversible Backreaction

**Development-only independent sidecar**; *not* a replacement for A026-v0.2.1 and not an installed or certified SST Falsifier Framework v1.1.0 RC2 instance. **No physical 3D Euler or Swirl Clock finding** is produced by this release.

This package answers only the **pilot falsification** question: Does a precisely known conservative system show better future-state prediction when *past observations* are included beyond the currently observed variables, and does that extra effect disappear in an exact decoupled null?

## Why not create a fresh A catalog ID?

The inspected 2026-10-26 inventory already contains A026 (phase feedback and knot stability), A049 (Euler transverse rigidity), A068 (phase clock), A069 (3D clock candidate), and A075 (Ruban trefoil). A026-v0.2.1 already tests a measured delay of Kelvin transport. The missing operation is **conditioning on the current observed state and comparing independent prior histories**, with native backreacting Euler geometry. This package is a separate candidate sidecar; it does not claim that the user's canonical registry has approved a new version or ID.

## Windows

```cmd
py -3 -m pip install -r requirements.txt
run_all.cmd TEST
run_all.cmd BASIC
```

On other OS:

```bash
python -m pip install -r requirements.txt
python run_falsifier.py TEST
python run_falsifier.py BASIC
```

For externally supplied independent full-field Euler trajectories:

```cmd
run_all.cmd EULER "C:\path\to\independent_trajectories.npz"
```

`EULER` intentionally returns exit 3 (`science not certified`) even if the data pass a format check and an observational signal is detected. `FULL` without verified native data refuses to run, also exit 3. The current sidecar does not create a false second backend or pass physical certification on synthetic data.

## Science & scope

The analytic benchmark is the Hamiltonian two-mode system

\[
\ddot x+\omega_K^2x+gy=0,\qquad \ddot y+\omega_B^2y+gx=0.
\]

A full-state observer needs only `(x,xdot,y,ydot)`. A limited observer sees `(x,xdot)`; delayed observations can reveal the hidden mode. This **does not** establish viscoelasticity or spontaneous clock slowing in an ideal fluid. A genuine 3D Euler test is still required for knotted filament backgrounds.

## Generated outputs

- `../A026_HiddenStateMemory_v0.1.0-outputs/<run_id>/GATE_LEDGER.json`
- `../A026_HiddenStateMemory_v0.1.0-outputs/<run_id>/MEASUREMENTS.json`
- `../A026_HiddenStateMemory_v0.1.0-outputs/<run_id>/A026_HiddenStateMemory_v0.1.0_FALSIFIER_REPORT.{md,pdf}`
- `../A026_HiddenStateMemory_v0.1.0_outputs.zip` plus matching `.sha256` (unique name if prior archive exists)
- `../A026_HiddenStateMemory_v0.1.0_FALSIFIER_REPORT_<timestamp>.pdf`

The scientific report explains the hypotheses, physics, 16-section methodology, numerical controls, gates and unresolved status. PDF rendering uses ReportLab as a **development fallback**; it does not satisfy official RC2 native-LaTeX publication gates.

## Provenance / installation safety

- Nothing is written to the existing A026, A049, A068, A069, E010 or A075 directories.
- No existing frozen results are overwritten.
- Only the exact scientific artifacts from your own external solver should enter the Euler adapter.
- Recommended eventual integration is a new, properly registered A026 version **only after** the canonical project registry and RC2 framework instance have been supplied and validated locally.

See [SCIENTIFIC_PROTOCOL.md](docs/SCIENTIFIC_PROTOCOL.md), [EULER_PROVIDER_CONTRACT.md](docs/EULER_PROVIDER_CONTRACT.md) and [RC2_INTEGRATION.md](docs/RC2_INTEGRATION.md).
