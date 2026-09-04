# SSTcore chiE Step-2 Next Tests

Status: **RESEARCH-TRACK / falsification-first / not canonized**.

This package has now separated the closed-loop energy problem into measurable pieces:

\[
\chi_E=\chi_K+\chi_{\rm cav}+\chi_{\rm grad}+\chi_{\sigma}+\chi_{\rm ren}.
\]

The current hollow-core positive-cavity horn test gives

\[
\chi_K(\lambda=1,\epsilon=1)\approx 7.760966,
\qquad
\chi_{\rm cav}(1)=\pi^2\approx 9.869604,
\]

so

\[
\chi_E^{\rm hollow}(1)\approx 17.630571 \neq 2\pi.
\]

This is a useful negative result: the simple hollow-core horn-torus model must not be promoted to a derivation of \(\chi_E=2\pi\).

## Added diagnostic runs

### Run 1 — epsilon sweep

Script:

```bash
python simulate_epsilon_sweep.py --python --lambda 1.0 --eps-min 0.2 --eps-max 2.0 --eps-count 37 --n 8192
```

Exports:

- `exports/epsilon_sweep.csv`
- `exports/epsilon_sweep_summary.json`
- `exports/epsilon_sweep.png`
- `exports/epsilon_sweep_run_results_summary.txt`

Purpose: test whether \(\chi_K\) or \(\chi_E^{\rm hollow}\) approaches \(2\pi\) without tuning the softening radius \(\epsilon=a_{\rm soft}/a_0\). A match produced only by a special \(\epsilon\) is calibrated, not derived.

### Run 2 — mass-mode comparison

Script:

```bash
python simulate_mass_mode_comparison.py --python --lambda-min 1 --lambda-max 8 --lambda-count 33 --epsilon 1 --n 8192
```

Exports:

- `exports/mass_mode_comparison.csv`
- `exports/mass_mode_comparison_summary.json`
- `exports/mass_mode_comparison.png`
- `exports/mass_mode_comparison_run_results_summary.txt`

Modes:

- `kinetic_only`: counts only exterior kinetic Dirichlet energy.
- `kinetic_plus_cavity`: strict hollow-core total, including positive \(P_{\rm vac}V_{\rm cav}\).
- `vacuum_subtracted`: records a \(-P_{\rm vac}V_{\rm cav}\) subtraction; numerically equals kinetic-only.
- `target_renormalized`: reports the calibrated subtraction needed to force \(\chi_E=2\pi\). This is diagnostic, not derivation.

### Run 3 — trefoil thickness audit

Script:

```bash
python simulate_trefoil_thickness_audit.py --n 384
```

Exports:

- `exports/trefoil_thickness_audit_summary.json`
- `exports/trefoil_minrad_values.csv`
- `exports/trefoil_thickness_audit.png`
- `exports/trefoil_thickness_audit_run_results_summary.txt`
- `exports/3_1_1_thickness_audit_points.xyz`

Purpose: audit the imported `ideal.txt` trefoil geometry using segment-segment clearance, MinRad, and radius/diameter-normalized ropelength proxies. This is not a substitute for a full octrope/ridgerunner constraint-thickness certificate.

## Proposed next physical models

### 1. Hollow core + positive cavity work — already falsified for the horn limit

Assumptions:

\[
E=E_K+P_{\rm vac}V_{\rm cav}.
\]

Horn-limit issue:

\[
\chi_{\rm cav}(1)=\pi^2>2\pi.
\]

Therefore the target \(\chi_E=2\pi\) is impossible if positive cavity work counts fully as rest energy.

### 2. Kinetic-only / vacuum-subtracted hollow core

Assumptions:

\[
E_{\rm mass}=E_K
\]

or equivalently

\[
E_{\rm mass}=E_K+P_{\rm vac}V_{\rm cav}-P_{\rm vac}V_{\rm cav}.
\]

Next test: replace the regularized filament kernel by a true exterior Neumann/Dirichlet boundary solve for a toroidal obstacle and evaluate

\[
\chi_K^{\rm horn}=\lim_{\lambda\to1^+}\frac12\int_{\Omega_\lambda}|\nabla\phi|^2\,dV.
\]

### 3. Solid/vast core with constant density

Assumptions:

\[
0\leq s\leq a_0,
\qquad
\rho(s)=\rho_{\rm sat},
\]

with a Rankine-like core velocity profile

\[
v_\theta(s)=\frac{\Gamma_0}{2\pi a_0^2}s
\quad (s<a_0),
\qquad
v_\theta(s)=\frac{\Gamma_0}{2\pi s}
\quad (s\ge a_0).
\]

Next test: integrate internal + external energy in toroidal coordinates. This removes cavitation work but introduces internal kinetic core energy.

### 4. Constant volume versus constant pressure asymptotic ring models

The user's Page-51 table gives thin-ring constants:

| model | energy constant \(\alpha\) | speed constant \(\beta\) |
|---|---:|---:|
| solid core + constant volume | \(7/4\) | \(1/4\) |
| hollow core + constant volume | \(2\) | \(1/2\) |
| hollow core + constant pressure | \(3/2\) | \(1/2\) |
| hollow core + surface tension | \(1\) | \(0\) |
| nonlinear Schrödinger | \(1.61\) | \(0.61\) |

Asymptotic formulas:

\[
E\simeq \frac12\rho\Gamma^2R\left[\log\left(\frac{8R}{a}\right)-\alpha\right],
\]

\[
V\simeq \frac{\Gamma}{4\pi R}\left[\log\left(\frac{8R}{a}\right)-\beta\right].
\]

These are useful for \(R/a\gg1\), but not decisive in the horn limit \(R/a=O(1)\). They should be implemented as asymptotic checks only.

### 5. Smooth constant-pressure / compressible core

Assumptions:

\[
E=\int\left(\frac12\rho |v|^2+U(\rho)+\frac\kappa2|\nabla\rho|^2\right)dV.
\]

Next test: solve a 1D resolved core profile \(\rho(s)\), then bend it into a toroidal tube and integrate the full energy. This is the real reviewer-grade replacement for the hollow-core idealization.

### 6. Surface tension model

Add torus surface energy

\[
E_\sigma=\sigma A_{\rm torus},
\qquad
A_{\rm torus}=4\pi^2Ra_0=4\pi^2\lambda a_0^2.
\]

In \(\chi_E\)-normalization:

\[
\chi_\sigma=\frac{E_\sigma}{\rho_{\rm sat}v_0^2a_0^3}
=4\pi^2\lambda\frac{\sigma}{\rho_{\rm sat}v_0^2a_0}
=2\pi^2\lambda\frac{\sigma}{P_{\rm vac}a_0}.
\]

Surface tension is therefore another dimensionless control parameter, not a free proof. If tuned to rescue \(2\pi\), it must be labelled calibrated.

## Recommended next implementation order

1. Epsilon robustness and mass-mode comparison: already added.
2. Full trefoil thickness certificate: replace the proxy audit with octrope/ridgerunner-style constraint thickness.
3. Solid constant-density Rankine core in toroidal coordinates.
4. Smooth resolved-core profile \(\rho(s)\) with gradient term.
5. Surface tension and constant-pressure/constant-volume asymptotic checks.
6. Boundary-element Dirichlet solve for the exterior potential around a toroidal obstacle.

