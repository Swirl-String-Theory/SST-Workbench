# SST Preferred-Frame & Binary-Radiation Falsifier v0.1.1

C++/Python `pybind11` audit pack built in the standard **SST cpp_pybind audit template** layout. It operationalizes the falsification routes motivated by Vaglio et al. (2026), *Constraints on Einstein-aether gravity from the precision timing of PSR J1738+0333*.

## Scientific scope

This pack does **not** assume that Einstein-aether parameters are SST parameters. In particular, it does not identify `c_omega` with SST vorticity, circulation, or energy density. Instead it tests generic observables that any preferred-medium gravity model must eventually confront:

1. **Uniform-drift sensitivity of a finite-core vortex knot**
2. **Isotropic vs anisotropic preferred-frame response**
3. **Universality of radiative/gravitational charge-to-mass ratio** and the associated dipole mismatch
4. **Existence/non-existence of a free linear bulk-wave sector** in homogeneous incompressible Euler flow
5. **Far-field flux vs orbital radiation-reaction energy balance**
6. **PSR J1738+0333 orbital-decay gate** once SST supplies a predicted corrected `Pdot_b`
7. **Effective PPN preferred-frame gate** once SST supplies an independently derived mapping to `alpha1_eff`, `alpha2_eff`

The package distinguishes:

- `BASELINE`: consequences of ordinary incompressible Euler / Galilean invariance;
- `DIAGNOSTIC_ONLY`: scale comparisons that are not SST derivations;
- `INPUT_REQUIRED`: a real SST closure/prediction must be supplied before the gate can falsify it;
- `CONTROL`: manufactured positive/negative test used only to validate the audit machinery.

## Layout

```text
SST_preferred_frame_binary_falsifier_v0.1.1/
├── README.md
├── CHANGELOG.md
├── CITATIONS.md
├── requirements.txt
├── pyproject.toml
├── run_example.py
├── run_sweep.py
├── run_all_checks.py
├── run_drift_scan.py
├── run_pf_gate.py
├── run_j1738_gate.py
├── run_dipole_gate.py
├── run_linear_euler_gate.py
├── run_energy_balance.py
├── run_fit_drift_data.py
├── run_ideal_database.py
├── run_ideal_quick.cmd
├── run_ideal_full_catalog.cmd
├── cpp/
│   └── native.cpp
├── sst_pf_binary_falsifier/
│   ├── __init__.py
│   ├── _config.py
│   ├── build_ext_if_needed.py
│   ├── constants.py
│   ├── core.py
│   ├── fallback.py
│   └── ideal_db.py
├── data/
│   ├── Ideal.txt.gz
│   ├── IdealLinks.txt.gz
│   ├── ideal_knots_index.csv
│   ├── ideal_links_index.csv
│   ├── ideal_source_length_validation.csv
│   └── j1738_reference.json
├── examples/
│   ├── minimal_commands.txt
│   ├── full_commands.txt
│   ├── objects_universal.json
│   ├── objects_nonuniversal.json
│   ├── energy_balance_example.csv
│   └── drift_external_example.csv
└── tests/
    └── test_core.py
```



## v0.1.1 — direct `Ideal.txt` / `IdealLinks.txt` support

The supplied Brian Gilbert databases are bundled unchanged as:

```text
data/Ideal.txt.gz
data/IdealLinks.txt.gz
```

The parser evaluates the database Fourier representation

\[
\mathbf X(t)=\frac{\mathbf A_0}{2}+\sum_{i\ge1}
[\mathbf A_i\cos(it)+\mathbf B_i\sin(it)].
\]

Zero coefficients may be omitted in the files. `Ideal.txt` knot lengths are audited at the source 512-point polygon convention. Link strings use 256 points for 2/3-component links and 128 points for 4/5-component links unless `--samples` overrides this.

The database uses tube diameter `D=1`. For SST dynamical runs the default is

\[
D_{\rm database}=1 \longmapsto D_{\rm SST}=2r_c,
\]

so the coordinate scale factor is `2*r_c/D`. This is an explicit geometry mapping, not a derivation that the Gilbert SONO tube is an SST core profile.

### Parse and validate the databases

```bat
python run_ideal_database.py --knot-ids 3:1:1 --link-ids L2a1,L4a1,L6n1
python run_ideal_database.py --all-knots --all-links --no-linking --out-dir audit_out/ideal_full
```

### Use the exact ideal trefoil in the preferred-frame baseline

```bat
python run_drift_scan.py --ideal-knot-id 3:1:1 --ideal-samples 96 --steps 2 --out-dir audit_out/drift_3_1_1
```

### Use all strings of an ideal link without connecting them

```bat
python run_drift_scan.py --ideal-link-id L2a1 --ideal-samples 64 --steps 1 --out-dir audit_out/drift_L2a1
```

The multi-component C++/Python kernel includes self- and inter-component Biot–Savart interactions while preserving each `STRING` as its own closed filament. `run_ideal_database.py` also evaluates pairwise Gauss linking numbers as a topology sanity check.

Windows one-click entry points:

```text
run_ideal_quick.cmd
run_ideal_full_catalog.cmd
```

## Canonical SST constants used

```text
v_swirl = 1.09384563e6 m s^-1
r_c = 1.40897017e-15 m
rho_core = 3.8934358266918687e18 kg m^-3
rho_f = 7.0e-7 kg m^-3
F_swirl_max = 29.053507 N
F_gr_max = 3.02563e43 N
Gamma = 2*pi*r_c*v_swirl
```

The package computes

```text
Gamma = 9.683619203488876e-09 m^2 s^-1
(v_swirl/c)^2 = 1.331283856...e-05
```

## 1. Drift-sensitivity gate

The phenomenological observable discussed in the SST analysis is

\[
\frac{\Delta E_K}{E_K}
=
\chi_{0,K}\frac{W^2}{c^2}
+
\chi_{2,K}
\frac{(\mathbf W\cdot\hat{\mathbf a})^2-W^2/3}{c^2}
+\cdots.
\]

`run_drift_scan.py` does **not** insert this response by default. Instead it evolves a regularized torus-knot filament with

\[
\dot{\mathbf X}=\mathbf u_{\rm BS}(\mathbf X)+\mathbf W
\]

and checks whether translation-reduced intrinsic energy/shape changes with a uniform background velocity `W`.

For plain incompressible Euler, a uniform `W` is a Galilean boost. Therefore the expected baseline is

\[
\chi_0=\chi_2=0
\]

up to numerical error. If this baseline fails, the numerical method is suspect. If SST predicts a nonzero drift sensitivity, that term must arise from additional SST structure beyond an unmodified homogeneous Euler filament.

The finite-core energy proxy is

\[
E_{\rm fil}
\approx
\frac{\rho_f\Gamma^2}{8\pi}
\oint\!\oint
\frac{d\mathbf X\cdot d\mathbf X'}
{\sqrt{|\mathbf X-\mathbf X'|^2+r_c^2}}.
\]

This is an audit regularization, not a claim that this expression is the final SST particle mass functional.

### Run

```bash
python run_drift_scan.py --n 96 --steps 3 --out-dir audit_out/drift_hi
# Or use a real Workbench/ideal-knot centerline:
python run_drift_scan.py --points ideal_trefoil_xyz.csv --steps 3 --out-dir audit_out/ideal_trefoil
```

Synthetic `--inject-chi0` and `--inject-chi2` options are **fit-recovery controls only**.


### Fit real SST drift output

If a separate SST solver computes energies for multiple drift magnitudes/orientations, export

```text
beta,mu,energy_J
```

with `beta=W/c` and `mu=cos(angle(W, object_axis))`, then run

```bash
python run_fit_drift_data.py --csv your_sst_drift_scan.csv
```

This is the route from the baseline harness to a real SST `chi0/chi2` measurement. Optional `--chi0-max` and `--chi2-max` thresholds are deliberately user-supplied until a first-principles SST-to-observation mapping exists.

## 2. Preferred-frame observational gate

Vaglio et al. report the one-sided PSR J1738+0333 constraints

\[
\alpha_1>-4.4\times10^{-5}\quad(68\%),
\qquad
\alpha_1>-7.2\times10^{-5}\quad(90\%).
\]

The same paper quotes the usual Solar-System scales

\[
|\alpha_1|\lesssim10^{-4},
\qquad
|\alpha_2|\lesssim10^{-7}.
\]

`run_pf_gate.py` never maps SST to these parameters on its own. Supply effective values only after a separate derivation:

```bash
python run_pf_gate.py --alpha1-eff -5e-5 --alpha2-eff 5e-8
```

The pack also reports the purely diagnostic scaling coefficients for

\[
\alpha_{i,\rm eff}=C_i\left(\frac{\mathbf v_{\!\boldsymbol{\circlearrowleft}}}{c}\right)^2.
\]

These are scale diagnostics, not identities.

## 3. q/m universality and dipole gate

For a generic radiative/gravitational charge `q_A`, the binary dipole is proportional to

\[
\Delta_{12}=\frac{q_1}{m_1}-\frac{q_2}{m_2},
\]

so the universal mismatch factor entering dipole power is

\[
\Delta_{12}^2.
\]

If SST derives

\[
q_A/m_A=\lambda\quad\forall A,
\]

the dipole mismatch vanishes identically. The package checks this property on arbitrary model outputs:

```bash
python run_dipole_gate.py --objects examples/objects_universal.json
python run_dipole_gate.py --objects examples/objects_nonuniversal.json --tolerance 1e-8
```

No physical radiation normalization is invented by the package.

## 4. Linearized homogeneous incompressible Euler gate

Linearizing

\[
\partial_t\mathbf u +(\mathbf u\cdot\nabla)\mathbf u
=-\frac{1}{\rho_f}\nabla p,
\qquad \nabla\cdot\mathbf u=0,
\]

about homogeneous rest gives, after transverse projection in Fourier space,

\[
\partial_t\hat{\mathbf u}_\perp=0.
\]

Therefore this baseline has no ordinary propagating free bulk mode. Run:

```bash
python run_linear_euler_gate.py
```

This does **not** exclude Kelvin waves on vortices or modes supported by a structured SST background.

## 5. Energy-balance closure

A viable binary-radiation model should independently satisfy

\[
\frac{dE_{\rm orbit}}{dt}=-\mathcal F_\infty=P_{\rm RR}.
\]

Provide CSV columns

```text
t_s,E_orbit_J,flux_inf_W,p_rr_W
```

and run

```bash
python run_energy_balance.py --csv your_binary_output.csv --rel-tolerance 0.05
```

This is designed to catch a mismatch between a far-field flux derivation and an orbital radiation-reaction derivation.

## 6. PSR J1738+0333 gate

From the values reported by Vaglio et al.,

\[
\dot P_b^{\rm corr}
=
\dot P_b-\dot P_b^{\rm Shk}-\dot P_b^{\rm Gal}.
\]

The package reconstructs

\[
\dot P_b^{\rm corr}\simeq -2.72\times10^{-14}\;\mathrm{s\,s^{-1}}
\]

with a simple independent-Gaussian uncertainty propagation. This is a convenience check only; publication-level inference should use the full timing posterior.

Once SST yields its own corrected prediction:

```bash
python run_j1738_gate.py --model-pdot-corr -2.70e-14
```

A `>2 sigma` failure in this proxy falsifies the **supplied SST binary closure**, not every possible SST reformulation.

## Build and quick test

```bash
pip install -r requirements.txt
python -m sst_pf_binary_falsifier.build_ext_if_needed --force --strict
python run_all_checks.py --out-dir audit_out
python -m pytest -q
```

The loader follows the standard SST template behavior:

1. hash `cpp/native.cpp`;
2. rebuild the extension only when needed;
3. try the native C++17/pybind11 backend;
4. fall back to the NumPy/Python implementation when compilation is unavailable.

## What v0.1.1 can and cannot falsify

| Gate | Can falsify now? | Meaning |
|---|---:|---|
| C++/Python parity | yes | implementation correctness |
| Uniform-drift Euler baseline | yes | numerical violation of Galilean baseline |
| Injected chi recovery | yes | fitting machinery |
| q/m universality | yes, if real SST q,m supplied | dipole channel opens when non-universal |
| Homogeneous Euler bulk mode | structural | no free bulk waves in this baseline |
| Energy balance | yes, if real SST flux/RR supplied | closure consistency |
| J1738 Pdot | yes, if SST Pdot supplied | observational binary test |
| alpha1/alpha2 | yes, if SST->PPN mapping supplied | preferred-frame test |

The key intentionally unresolved inputs are therefore **scientific**, not software omissions: the full SST theory must supply its drift coupling, radiative degree of freedom, `q/m` definition, and binary decay prediction.
