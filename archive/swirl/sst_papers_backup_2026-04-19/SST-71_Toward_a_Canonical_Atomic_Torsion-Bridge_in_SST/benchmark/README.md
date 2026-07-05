# SST-71 Helicity Asymmetry Benchmark

A small standalone Python benchmark package that numerically verifies the **helicity asymmetry** for hydrogenic 1s photoionization in the **reduced SST atomic bridge model** (Swirl-String Theory). This is a benchmark of the model, not a full first-principles derivation of atomic structure.

## Scientific purpose

The benchmark observable is the total rate asymmetry

$$A_{\mathrm{tot}}(\omega) = \frac{\Gamma_{h=+1}(\omega) - \Gamma_{h=-1}(\omega)}{\Gamma_{h=+1}(\omega) + \Gamma_{h=-1}(\omega)}$$

with

- **Initial state**: hydrogenic 1s  
- **Final states**: attractive Coulomb continuum partial waves  
- **Probe**: pure-helicity circulation packet  
  $\gamma_h(r,t) = A_\gamma\, f(\rho,z)\, \exp(i(h\phi + q z - \omega t))$, $h = \pm 1$  
- **Axisymmetric envelope**:  
  $f(\rho,z) = \exp(-\rho^2/(2w_r^2))\,\exp(-z^2/(2w_z^2))$

The reduced interaction is  
$\delta H_{\mathrm{int}}^{(\sigma)}\psi_{1s} = E_R\,\eta_0\,\sigma\,C_h\,\gamma_h\,\psi_{1s}$  
with $C_h = -2 + h/2$, so $C_{+1} = -3/2$, $C_{-1} = -5/2$.

For an axisymmetric envelope and central Coulomb problem, the azimuthal selection rule gives $m = h$, and the magnitudes of the Coulomb–continuum overlap integrals match between $h=+1$ and $h=-1$. Therefore

$$A_{\mathrm{tot}} = \frac{|C_+|^2 - |C_-|^2}{|C_+|^2 + |C_-|^2} = -\frac{8}{17}.$$

The code verifies this by **computing the rates** (not by hardcoding the ratio).

The package’s primary target is the **asymmetry ratio** $A_{\mathrm{tot}}$, not absolute cross sections. Because the main observable is a ratio, common continuum-normalization factors cancel between helicity channels. The current package is therefore intended to validate the asymmetry benchmark first, not absolute ionization rates.

## Implementation notes

- **Main benchmark (axisymmetric helical)**: The $\phi$ integral is performed **analytically**, yielding the selection rule $m = h$ and a factor $2\pi$. The integration is reduced to a **2D (r, $\theta$) quadrature** using Gauss–Legendre rules. When the optional **pybind11** extension `sst_benchmark_core` is built, this quadrature is executed in C++; otherwise the same 2D quadrature runs in pure Python (reference/fallback). **N_r** and **N_theta** are active convergence parameters.
- **Python** remains the reference and orchestration layer: Coulomb radial functions, hydrogen 1s, probe envelope, benchmark scans, CSV output, and plotting are all in Python. The compiled extension is used only to accelerate the axisymmetric 2D quadrature kernel.
- **Non-helical control**: Both helicity channels are **computed from the physics** (probe $h=0$, same scalar coupling $C = -2$ for both), so the asymmetry is ~0 without imposing it by hand. They use the same axisymmetric kernel (C++ or Python) as the main benchmark.
- **Broken-axisymmetry control (secondary)**: The older control used envelope $\propto (1 + \epsilon\cos(2\phi))$ and a **3D (r, $\theta$, $\phi$) quadrature**. This perturbation is **mirror-symmetric** and preserves enough **residual $m \leftrightarrow -m$ pairing** in the Coulomb problem, so in practice $A_{\mathrm{tot}}$ can remain close to $-8/17$; it does not genuinely stress-test the pinning. It is kept as an optional secondary diagnostic only.
- **Stronger control – helical_mode_plus1**: A **one-sided Fourier perturbation** breaks the residual $m \leftrightarrow -m$ pairing. The probe is  
  $\gamma_h^{\mathrm{strong}} = A_\gamma\, f(\rho,z)\, e^{i q z}\, e^{i h\phi}\, (1 + \varepsilon\, e^{i\phi})$,  
  i.e. a finite harmonic sum: $e^{i h\phi} + \varepsilon\, e^{i(h+1)\phi}$. So  
  **$h=+1$** couples to azimuthal channels **$m=+1$ and $m=+2$**; **$h=-1$** couples to **$m=-1$ and $m=0$**. The exact pinning to $-8/17$ is then **no longer symmetry-protected**, so finite $\varepsilon$ is expected to move $A_{\mathrm{tot}}$ away from $-8/17$. This control is still **computationally efficient**: it is a finite harmonic sum and uses the **same fast 2D axisymmetric-harmonic kernel** (one call per channel $m$, then incoherent sum of rates). No return to a slow generic 3D control for the main non-axisymmetric stress test.
- The package’s **primary target is the asymmetry ratio** $A_{\mathrm{tot}}$, not absolute cross sections. The compiled extension accelerates that ratio benchmark.

### Why the previous cos(2φ) control did not move the ratio

The cos(2φ)-style perturbation preserves mirror symmetry in $\phi$ and leaves a **residual $m \leftrightarrow -m$ pairing** in the Coulomb matrix elements. Under that pairing, the contributions that fix $A_{\mathrm{tot}} = -8/17$ for the axisymmetric case can remain dominant, so the ratio need not move off $-8/17$ in the tested regime. It is therefore a **weak** non-axisymmetric control.

### Why the new control is stronger

The **one-sided** Fourier term $e^{i\phi}$ introduces **different** additional channels for $h=+1$ vs $h=-1$:  
$h=+1 \to m=+1,+2$ and $h=-1 \to m=-1,0$. There is no symmetric $(-m)$ counterpart for the extra channel in each helicity, so the exact pinning to $-8/17$ is no longer symmetry-protected. For $\varepsilon = 0$ the new control reduces exactly to the main (axisymmetric) benchmark; for $\varepsilon > 0$, $A_{\mathrm{tot}}$ is expected to deviate from $-8/17$.

## Expected results

- **Main benchmark** (helical, axisymmetric, with anticommutator):  
  $A_{\mathrm{tot}}(\omega) \approx -8/17 \approx -0.4706$.
- **Null control – no anticommutator**: $C_h = -2$ for both $h$ → $A_{\mathrm{tot}} \approx 0$.
- **Null control – non-helical probe**: probe with $h=0$ and $C = -2$ for both channels → $A_{\mathrm{tot}} \approx 0$ from the computed rates.
- **Stronger control (helical_mode_plus1)**: at $\varepsilon = 0$, recovers the main benchmark ($A_{\mathrm{tot}} \approx -8/17$); at $\varepsilon > 0$, $A_{\mathrm{tot}}$ generally **deviates** from $-8/17$. This is the **primary non-axisymmetric stress test** of the robustness of the pinning, **not** a replacement for the main benchmark. The main benchmark remains the axisymmetric helical probe with exact result $-8/17$; the null controls (no anticommutator, non-helical) remain the checks that yield $A_{\mathrm{tot}} \approx 0$.
- **Broken axisymmetry (secondary)**: older cos(2φ)-style perturbation; may not move $A_{\mathrm{tot}}$ off $-8/17$ due to residual $m \leftrightarrow -m$ pairing; kept as optional diagnostic.

### Stronger-control convergence study

Because the stronger control **intentionally** moves the asymmetry away from $-8/17$, one must show that the shifted value is **numerically converged** and not a discretization artifact. A dedicated convergence study is provided:

- **Fixed**: photon energy = 30 eV, $\varepsilon = 0.25$, probe_type = helical_mode_plus1, use_anticommutator = True.
- **Reference resolution** (used for non-varied parameters in each sweep): $R_{\max} = 100\,a_0^{\mathrm{SST}}$, $N_r = 320$, $N_\theta = 256$, $l_{\max} = 8$.
- **Varied** (in separate sweeps): $R_{\max}$ (multipliers 20, 40, 80, 120, 160), $N_r$ (80, 160, 240, 320, 480), $N_\theta$ (64, 128, 192, 256, 384), $l_{\max}$ (2, 4, 6, 8, 10, 12).

**What to expect**: The main benchmark remains pinned at $-8/17$; the stronger control deviates from $-8/17$. The convergence study shows that this **deviation stabilizes** under resolution increase (asymmetry and $\delta = A_{\mathrm{tot}} - (-8/17)$ settle to a stable value). Output: `convergence_study_helical_mode_plus1.csv` and the plots `convergence_helical_mode_plus1.png`/`.pdf` and `convergence_helical_mode_plus1_delta.png`/`.pdf`. In **quick** mode this study is **skipped** to keep the run short.

## Package structure

| File | Role |
|------|------|
| `constants.py` | SI and SST canonical constants; derived scales; `print_constants_summary()` |
| `hydrogen.py` | Hydrogenic 1s wavefunction and ionization energy I1 |
| `coulomb_continuum.py` | Attractive Coulomb continuum radial functions (mpmath) and spherical harmonics |
| `helical_probe.py` | Pure-helicity probe $\gamma_h$, controls (non-helical, broken axisymmetry), and helical_mode_plus1 harmonic components |
| `matrix_elements.py` | Overlap integrals, total rate, asymmetry, selection-rule check; dispatches to C++ or Python |
| `benchmark_scan.py` | Energy scan and control runs; writes CSVs |
| `plot_results.py` | Plots A_tot vs energy, control comparison, stronger-control A_tot and epsilon scan, main and stronger-control convergence |
| `sst_benchmark_core.cpp` | C++ axisymmetric 2D quadrature kernel (pybind11) |
| `pyproject.toml` | Build and project metadata; build requires setuptools, pybind11 |
| `setup.py` | Builds the `sst_benchmark_core` extension |
| `README.md` | This file |
| `requirements.txt` | Dependencies |

## Install

From the `benchmark` directory:

```bash
pip install -r requirements.txt
```

### Optional: build the C++ extension

To use the accelerated axisymmetric kernel, build the pybind11 extension from the `benchmark` directory:

```bash
python -m pip install -e .
```

You need a C++14-capable compiler (e.g. MSVC on Windows, g++ or clang on Linux/macOS) and pybind11. If the extension is not built, the package still runs using the **pure-Python** axisymmetric 2D quadrature (same result, slower for large N_r, N_theta).

## Run

From the **benchmark** directory:

```bash
python benchmark_scan.py
```

This prints the constants summary, runs the main benchmark, the null controls (no anticommutator, non-helical), the **stronger control** (helical_mode_plus1, $\varepsilon=0.25$) and an **epsilon scan** at 30 eV, the optional broken-axisymmetry control, the **main convergence study** at 30 eV, and the **stronger-control convergence study** (30 eV, $\varepsilon=0.25$). CSVs are saved in the same directory (e.g. `benchmark_main.csv`, `control_helical_mode_plus1.csv`, `control_helical_mode_plus1_eps_scan.csv`, `convergence_study.csv`, `convergence_study_helical_mode_plus1.csv`).

For a **quick** run (fewer energies, smaller `l_max` and `R_max`) so the script finishes in minutes:

```bash
set SST71_QUICK=1
python benchmark_scan.py
```

or

```bash
python benchmark_scan.py --quick
```

In **quick** mode the **stronger-control convergence study** is **skipped** (the main convergence study still runs with reduced resolution). Full mode regenerates all outputs including `convergence_study_helical_mode_plus1.csv` and the corresponding plots.

The main axisymmetric benchmark uses 2D quadrature (N_r, N_theta) and is much faster than the broken-axisymmetry path, which uses 3D quadrature. Increase `l_max` and the number of energy points for publication-grade results.

Then:

```bash
python plot_results.py
```

This reads the CSVs and saves figures (PNG and PDF): A_tot vs photon energy, control comparison, stronger-control A_tot(ω) and epsilon-scan plots, **main convergence** (`convergence.png`/`.pdf`), and **stronger-control convergence** (`convergence_helical_mode_plus1.png`/`.pdf`, `convergence_helical_mode_plus1_delta.png`/`.pdf`) when the corresponding CSVs exist.

### Progress bar

By default, `benchmark_scan.py` shows a progress bar for each energy scan and for the convergence study (requires the optional **tqdm** package). Use **`--no-progress`** to disable (e.g. in CI or when redirecting output). The bar is automatically disabled when using **`--verbose`** or **`--debug`** so it does not clash with log output.

### Verbosity

- **`--verbose`**, **`-v`**: Log most steps (per-energy results, file saves, convergence points). Use with `benchmark_scan.py` or `plot_results.py`.
- **`--debug`**: Log additional detail from the integration layer (grid sizes, C++ vs Python path, per-call rates). Use with `benchmark_scan.py` for full trace.

### Parallel runs (multiple CPU cores)

- **`--jobs`**, **`-j`** *N*: Run energy scans and the convergence study in parallel using *N* worker processes. Each energy point (or each convergence configuration) is computed in a separate process. Default is 1 (sequential). Example:

```bash
python benchmark_scan.py --quick -j 4
python benchmark_scan.py -j 8 --verbose
```

Example (verbose + parallel):

```bash
python benchmark_scan.py --quick --verbose -j 4
python plot_results.py --verbose
```

## Dependencies

- numpy  
- scipy  
- mpmath  
- matplotlib  
- tqdm (optional; for progress bar; script runs without it)  

All units are SI internally; energies are converted to eV only for reporting and plotting.
