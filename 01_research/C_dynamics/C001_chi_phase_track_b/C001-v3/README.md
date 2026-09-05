# SST chi-phase package v3

**Purpose:** v3 replaces the archived v1/v2 shared-moment identity checks with a
non-tautological torsional-stiffness extractor.

v1/v2 used the constitutive assignment

\[
\mathcal I_\chi=\rho_f J,
\qquad
\mathcal K_\chi=\rho_f v_{\rm swirl}^2 J,
\]

so

\[
c_\chi=\sqrt{\mathcal K_\chi/\mathcal I_\chi}=v_{\rm swirl}
\]

was algebraically guaranteed.  v3 does **not** do that.

Instead, v3 computes

\[
\mathcal I_\chi=\rho_f\int_A r_\perp^2\,dA,
\qquad
\mathcal K_\chi=\rho_f\int_A v_\theta(r)^2 r_\perp^2\,dA,
\]

and therefore

\[
c_\chi^2=
\frac{\int_A v_\theta(r)^2 r_\perp^2\,dA}
     {\int_A r_\perp^2\,dA}.
\]

This can differ from \(v_{\rm swirl}^2\).  Thus v3 can fail and is a genuine
Research Track extractor.

## Profiles included

The default run evaluates:

- `uniform` boundary-normalized: should give \(c_\chi/v=1\).
- `solid_body` boundary-normalized: should give \(c_\chi/v=\sqrt{2/3}\).
- `quadratic_core` boundary-normalized.
- `irrotational_reg` boundary-normalized with inner regularization `eps=0.05`.
- `rankine` max-normalized.
- `lamb_oseen` max-normalized.
- `gaussian_core` max-normalized.
- `gaussian_shell` max-normalized.
- `solid_body` with `rms_r2` normalization, explicitly labelled as calibration mode because it forces \(c_\chi/v=1\).

## Run

```powershell
cd path\to\sst_chi_phase_package_v3
python simulate_chi_phase_v3.py
```

Force pure Python fallback:

```powershell
python simulate_chi_phase_v3.py --python
```

Force rebuild of the C++ backend:

```powershell
python sst_chi_phase_v3_build.py --force
```

## Outputs

The run writes to `exports/`:

- `chi_v3_profile_stiffness.csv`
- `chi_v3_profile_speed_ratio.png`
- `chi_v3_profile_spectrum.csv`
- `chi_v3_profile_spectrum.png`
- `chi_v3_spectrum_convergence.csv`
- `chi_v3_spectrum_convergence.png`
- `chi_v3_run_results_summary.txt`

## Interpretation

A PASS means:

1. The code can distinguish the archived identity checks from a profile-derived
   stiffness extraction.
2. Boundary-normalized solid-body swirl gives the expected nontrivial value
   \(c_\chi/v=\sqrt{2/3}\).
3. The horn-loop spectrum now inherits the extracted \(c_\chi/v\), so
   \(\omega_n/(n\omega_c)\) is not forced to one.

A PASS does **not** prove \(Q_\chi\to Q_{\rm em}\), SU(2), SU(3), or a full
SST gauge derivation.  It only addresses the local torsional-stiffness problem.

## Canon status

Recommended label:

\[
\boxed{\text{Research Track: profile-derived torsional stiffness extractor.}}
\]

The canon-worthy target is not the old identity
\(c_\chi=v_{\rm swirl}\), but the conditional statement:

\[
c_\chi^2=\left\langle v_\theta^2\right\rangle_{r^2}
:=
\frac{\int_A v_\theta(r)^2 r_\perp^2\,dA}
     {\int_A r_\perp^2\,dA}.
\]

Then \(c_\chi=v_{\rm swirl}\) only follows if \(v_{\rm swirl}\) is independently
defined as the \(r^2\)-weighted RMS swirl speed of the resolved core.
