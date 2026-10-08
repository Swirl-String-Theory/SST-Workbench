# A056-v0.3.0 - PKLSA -> finite-core/Euler -> phase/ringdown -> SG/ML falsifier


> **v0.3.0 hotfix 1 (Windows launcher):** the E010 launchers invoke the provider with `python -m a056_provider.campaign`.  Direct execution of `tools\build_e010_provider.py` is also supported through an explicit instance-root bootstrap.  This fixes the Windows `ModuleNotFoundError: a056_provider` seen before the provider campaign started; no scientific contract or frozen threshold changed.

A056-v0.3.0 is the first A056 release that closes the real-provider gap while remaining a thin instance of **SST Falsifier Framework v1.0.4 CANONICAL_FROZEN**.

## Primary chain

\[
\boxed{\text{E010/PKLSA qualified carrier}\rightarrow\text{finite-core / Euler evolution}\rightarrow\{\varphi(s,t),R(t)\}\rightarrow\text{A056 blind SG/ML competition}}
\]

Static XYZ geometry is never scored as dynamics. The package resolves E010-v0.3.1 source-native trefoil carriers, verifies raw and PKLSA geometry hashes, selects strict new-upstream-provider representatives, applies a frozen Kelvin perturbation, evolves paired base/perturbed systems, extracts a pre-registered phase and projected mode envelope, and only then invokes the existing A056 model competition.

### Frozen observables

With a periodic Bishop frame on the initial carrier and a mode-\(m\) perturbation,
\[
\mathbf X_\epsilon(s,0)=\mathbf X_0(s)+\epsilon[\cos(m\theta)\mathbf e_1+\sin(m\theta)\mathbf e_2].
\]
At each sample the unperturbed material carrier is rigidly Kabsch-aligned to its initial geometry; the same rigid transform is applied to the perturbed carrier. No scale or reflection is permitted. Then
\[
q=\delta\mathbf X\cdot\mathbf e_1+i\,\delta\mathbf X\cdot\mathbf e_2,\qquad
\varphi=\arg(qe^{-im\theta}),
\]
and
\[
R(t)=\frac{|c_m(t)|}{|c_m(0)|},\qquad c_m=N_s^{-1}\sum_j q_j e^{-im\theta_j}.
\]
`R(t)` is a projected conservative-mode envelope, not a dissipation claim.

## Dynamic lanes

- `filament_bs`: regularized finite-core Biot-Savart material-filament RK4. Cheap enough for rapid E010 provider screening.
- `euler_ps3d`: paired 3-D incompressible unforced Euler pseudo-spectral evolution, 2/3 dealiased RK4, with a Gaussian finite-core vorticity tube and advected material markers. This is adapted from the A047 E010/Euler route; A056 reuses the method, not A047 verdicts.

Both lanes are **simulation** evidence under framework v1.0.4. Even two independent E010 upstream providers cannot close physical G7. They can establish a replicated simulation conclusion only.

## Run

Synthetic framework acceptance remains:

```cmd
run_all.cmd
```

Real E010 finite-core filament campaign:

```cmd
run_e010_filament.cmd C:\workspace\projects\SST-Workbench
```

Short 3-D Euler integration smoke:

```cmd
run_e010_euler_smoke.cmd C:\workspace\projects\SST-Workbench
```

Multi-resolution 3-D Euler campaign (expensive):

```cmd
run_e010_euler_convergence.cmd C:\workspace\projects\SST-Workbench
```

The provider stage creates opaque NPZ/JSON cases plus a pre-score reveal commitment. Source-family/carrier identities remain in `data/private/<runtime>_reveal/` until `tools\reveal_e010_provider.py` is executed after framework reveal.

## Interpretation

Possible additional v0.3.0 simulation conclusions include `JOINT_DYNAMIC_SIMULATION_SUPPORTED`, `PHASE_DYNAMIC_SIMULATION_SUPPORTED`, `MEMORY_DYNAMIC_SIMULATION_SUPPORTED`, or `DYNAMIC_SIMULATION_NO_REPLICATED_CANDIDATE`. They never substitute for `physical_conclusion`, which requires framework-eligible independent/experimental evidence.

### Windows repeated-run note (hotfix 3)

`data/runtime_e010_*` is now reset by deleting stale children while retaining the directory root. This avoids a Windows `WinError 5` seen when `shutil.rmtree()` successfully removed the contents but an external handle prevented the final root-directory removal. The reset remains fail-closed if any stale child cannot be deleted after bounded retries.

### G2 diagnostics after an early blind stop

If a real-provider run stops at G2, the provider evolution does not need to be regenerated merely to inspect the POD qualification. Run:

```bat
run_diagnose_g2.cmd
```

This reads the existing `data\runtime_e010_filament` directory and writes `A056_G2_DIAGNOSTICS_READONLY.json`. It does not alter the gate ledger or reveal any provider identity. Hotfix 4 also makes future G2-stopped FULL runs preserve `A056_G2_DIAGNOSTICS.json` and `A056_CASE_RESULTS_PARTIAL.csv` automatically.
