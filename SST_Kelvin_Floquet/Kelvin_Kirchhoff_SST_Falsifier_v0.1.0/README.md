# Kelvin–Kirchhoff SST Blind Falsifier v0.1.0

A ready-to-run Windows/Python/C++ workbench for the relaxed KnotPlot/Ridgerunner `*_final.txt` centerlines.

The package implements the **centerline-testable** part of the Kelvin/Kirchhoff research route without filling missing physics with fitted proxies.

## One-command run

Expected placement:

```text
C:\workspace\projects\SST-Workbench\SST_Kelvin\Kelvin_Kirchhoff_SST_Falsifier_v0.1.0
```

Default relaxed-knot directory:

```text
C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
```

From `cmd.exe`:

```bat
run_all.cmd 16
```

This performs, in order:

1. Python environment detection/creation;
2. dependency install;
3. C++17/pybind11 native build;
4. native-vs-Python self-test;
5. basic **blind** campaign on 8 fixed representative datasets;
6. extended **blind** campaign on every `*_final.txt` dataset;
7. frozen-preregistration scoring;
8. unblinding and final CSV/JSON/Markdown report generation.

Custom knot directory:

```bat
run_all.cmd 16 D:\other\KnotPlot\knots\final
```

## Ready-made commands

```bat
run_00_install.cmd
run_01_selftest.cmd 16
run_10_basic.cmd 16
run_20_extended.cmd 16
run_30_custom.cmd basic 16 D:\other\knots\final
run_30_custom.cmd extended 16 D:\other\knots\final
```

There are **no empty example manifests or placeholder datasets**. `basic.json`, `extended.json`, and `preregistered_gates.json` are complete campaign definitions.

## What is actually falsified

### K0 — geometry/provenance gate

Checks Ridgerunner residual, **post-resampling** edge-length CV, and whether the regularization radius came from the supplied `.metrics.json` thickness. Original edge-length CV is preserved as a diagnostic but is not a rejection criterion because the solver explicitly resamples uniformly in arclength.

### K1 — Kelvin relative-equilibrium gate

For a relaxed centerline `X`, the C++ kernel computes the regularized Biot–Savart self-induced velocity `V(X)`. The best rigid motion

```text
V_rigid = U + Omega x (X - Xbar)
```

is found by least squares. The preregistered observable is

```text
epsilon_RE = RMS(V - V_rigid) / RMS(V).
```

This is a direct numerical version of Kelvin's steady-vortex idea: a steady configuration may translate and/or rotate without changing shape.

### K2 — blind Kelvin `2 Omega` spectral-gap gate

The numerical stage never inserts a `2*Omega` gap into its operator.

A rigid-projected normal/binormal deformation basis is built on the resampled closed components. The shape velocity is finite-difference linearized:

```text
d(delta X)/dt = A delta X.
```

The eigenvalues of `A` give growth rates and oscillation frequencies. Each eigenmode receives an independently measured effective wavenumber from its arclength derivative. A training subset fits

```text
sigma^2 = sigma0^2 + c_eff^2 k^2
```

and a held-out subset tests predictive error. **Only after raw extraction is frozen** is the Kelvin hypothesis evaluated:

```text
sigma0 / (2 |Omega_eff|) = 1.
```

The gap model must also beat the forced-zero-gap model by the preregistered AIC margin.

### K3 — evanescent-confinement gate

For the lowest sufficiently stable extracted mode, fixed off-filament probe points are placed at several multiples of the supplied resolved tube thickness. The perturbation-induced velocity response is measured with the C++ field kernel.

The radial amplitude is fitted independently to:

```text
A(d) ~ exp(-d/L)
```

and to a power law. Only afterward is the Kelvin prediction

```text
L_K = c_eff / (2 |Omega_eff|)
```

compared with the measured exponential decay length. A nominal length agreement is **not** enough: the exponential must also fit well and beat the power law.

### K4 — Kirchhoff detailed balance

This is intentionally reported as:

```text
NOT_TESTABLE_FROM_CENTERLINES
```

Kirchhoff's law requires mode-resolved equilibrium emission and absorption information. Static relaxed centerlines do not contain incident flux, absorbed flux, emitted flux, temperature/effective equilibrium state, or linewidth/coupling data. The package therefore refuses to manufacture an emissivity/absorptivity proxy.

That status is a scientific guard, not an unfinished code path.

## Important SST Canon guard

The current SST research-track Canon distinguishes the resolved tube radius

```text
a_core(K) = reach/thickness of the resolved centerline
```

from the canonical horn/circulation radius `r_c` and explicitly keeps

```text
a_core != r_c
```

unless a separate profile calculation proves otherwise.

Accordingly, this workbench **does not scale Ridgerunner thickness to `r_c`**. The blind tests are performed in the dataset's own length/time units with circulation fixed to `Gamma = 1`; the decisive Kelvin ratios are dimensionless, so no forbidden `a_core = r_c` identification is needed.

## Blind architecture

Each campaign creates:

```text
outputs_<mode>_YYYYMMDD_HHMMSS/
├── datasets.private.json
├── private_blind_key.json          # identities; outside blind campaign
├── campaign_config.json
├── blind_campaign/
│   ├── blind_manifest.json         # CASE_* only
│   ├── data/
│   │   └── CASE_*.txt
│   └── results/
│       ├── frozen_preregistration.json
│       ├── frozen_preregistration.sha256.json
│       ├── blind_run_summary.json
│       ├── blind_scores.json
│       └── CASE_*/
│           ├── raw.json
│           ├── score.json
│           ├── spectrum.csv
│           ├── radial_response.csv
│           └── operator_A.npy
├── unblinded_summary.json
├── unblinded_summary.csv
└── REPORT.md
```

The private filename mapping is never copied into `blind_campaign`. Thresholds are copied and SHA-256 frozen before any case result is produced.

## C++ acceleration

The supplied SST pybind template was used as the build pattern. The native kernel implements regularized segment Biot–Savart evaluation for:

- self-induced velocity at all centerline vertices;
- velocity at arbitrary off-filament probes.

The builder tries OpenMP first and automatically retries without OpenMP if the compiler does not support it. Extended scripts require the native backend rather than silently running an impractically slow Python campaign.

## Interpretation limits

A `FAIL` does **not** falsify all SST. It falsifies the declared Kelvin-inspired centerline closure under this fixed regularized Biot–Savart model on that geometry.

In particular:

- a Ridgerunner length-critical geometry need not be a dynamical vortex relative equilibrium;
- a centerline model cannot resolve finite-core internal eigenfields;
- a regularized filament kernel is a model choice, not a derivation of the SST core constitutive law;
- Kirchhoff detailed balance needs additional dynamical/radiative data;
- no canonical SST value such as `r_c` or `v_swirl` enters the blind optimization or stopping rules.

## References

```latex
\bibitem{Thomson1879RotatingWater}
W.~Thomson (Lord Kelvin),
``On Gravitational Oscillations of Rotating Water,''
\emph{Proceedings of the Royal Society of Edinburgh}
\textbf{10}, 92--100 (1879/1880),
\href{https://doi.org/10.1017/S0370164600043467}
{doi:10.1017/S0370164600043467}.

\bibitem{Thomson1876VortexStatics}
W.~Thomson (Lord Kelvin),
``Vortex Statics,''
\emph{Proceedings of the Royal Society of Edinburgh}
\textbf{9}, 59--73 (1876).

\bibitem{Kirchhoff1860Radiation}
G.~Kirchhoff,
``On the Relation between the Radiating and Absorbing Powers of Different Bodies for Light and Heat,''
\emph{The London, Edinburgh, and Dublin Philosophical Magazine and Journal of Science},
Series~4, \textbf{20}, 1--21 (1860),
\href{https://doi.org/10.1080/14786446008642901}
{doi:10.1080/14786446008642901}.

\bibitem{Eisenga1997VortexRing}
A.~H.~M. Eisenga,
\emph{Dynamics of a Vortex Ring in a Rotating Fluid},
Ph.D. thesis, Eindhoven University of Technology (1997),
\href{https://doi.org/10.6100/IR492965}{doi:10.6100/IR492965}.
```
