# SST Material-Coordinate / Phase-Shift EFT Falsifier v0.1.0

Blind falsification/certification workbench inspired by Dubovsky, Hui, Nicolis & Son, *Effective field theory for hydrodynamics: thermodynamics, and the derivative expansion* (arXiv:1107.0731; Phys. Rev. D 85, 085029).

## What it tests

The package extracts four structural ideas from the paper without treating the paper as evidence for SST:

1. **G1 — material relabeling surrogate:** centerline observables must survive cyclic relabeling, orientation reversal and nonlinear monotone reparameterization followed by uniform arclength resampling.
2. **G2 — phase-shift / holonomy candidate:** Bishop-frame closed-loop holonomy is checked for periodic gauge-shift invariance and resolution convergence. Static knot files do **not** contain a measured physical SST phase field, so physical phase locking is `UNTESTED` by default.
3. **G3 — operator-redundancy pre-gate:** periodic total derivatives and integration-by-parts equivalent operators must collapse numerically before a coefficient is interpreted as new physics. Full EOM/field-redefinition redundancy is not claimed without an explicit leading SST action.
4. **G4 — derivative-dispersion falsifier:** small helical perturbations are linearized in a four-dimensional Bishop/Fourier Galerkin subspace of a regularized finite-core Biot-Savart filament closure. The projected eigenfrequencies are fit to

   `omega^2 = a2 q^2 + a4 q^4`.

The dynamics closure is a **test model**, not full Euler and not the entire SST canon.

## SST normalization

Canonical values are built in:

- `v_swirl = 1.09384563e6 m s^-1`
- `r_c = 1.40897017e-15 m`
- `rho_core = 3.8934358266918687e18 kg m^-3`
- `rho_f = 7.0e-7 kg m^-3`
- `Gamma = 2*pi*r_c*v_swirl`
- `t_core = r_c/v_swirl`

By default the estimated geometric tube thickness of each curve is mapped to `r_c`. If the coordinate-space core radius is known independently, set `core_radius_coord` in the config; this overrides the estimate. Dynamics is then run in core units, for which `Gamma* = 2*pi` and core radius is 1.

## Blind protocol

Topology/file names are never used by the gates. Paths are replaced by deterministic BLAKE2 blind IDs. The mapping is isolated in `blind_key.csv`; thresholds are read from the preregistered JSON config before analyzing data.

## Numerical certification

The extended campaign has independent numerical gates and uses:

- RK4;
- `Delta t proportional to Delta s^2`;
- exactly constant `T_final`;
- arclength reparameterization during evolution;
- separate temporal convergence (`dt` vs `dt/2`);
- separate spatial convergence at multiple `N`.

## Input

Recursively accepts `.txt`, `.csv`, `.xyz`, `.dat` files with at least 16 XYZ rows. KnotPlot coordinate `.txt` exports work directly.

Default dataset:

```text
..\..\KnotPlot\knots\final
```

## Run

One click, install through extended:

```bat
run_all.cmd
```

Explicit dataset:

```bat
run_all.cmd "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
```

Basic:

```bat
run_basic.cmd
```

Extended + native + certification:

```bat
run_extended.cmd
```

Custom:

```bat
run_campaign.cmd configs\basic.json outputs\my_run "C:\path\to\knots"
```

Synthetic installation smoke test:

```bat
run_smoke.cmd
```

## Outputs

- `manifest.json`: exact config, constants, environment and config hash
- `blind_key.csv`: blind ID ↔ input path
- `gate_results.csv`: detailed gate records
- `mode_results.csv`: projected linear-mode frequency/growth extraction plus RK4 tracking diagnostics
- `sample_summary.csv`
- `summary.json`
- `REPORT.md`

## Interpretation

**PASS** means only that the preregistered hypothesis/closure survived that gate at the configured tolerance. It is not confirmation of SST.

**FAIL** falsifies the tested closure/hypothesis at that tolerance, subject to the separate numerical-certification gates.

## Source-to-SST boundary

The paper supports comoving scalar material coordinates, internal volume-preserving relabelings, the chemical-shift symmetry `psi -> psi + f(phi^I)`, an identically conserved current, derivative expansion, removable/redundant operators, and a sample quartic dispersion correction. The Bishop-holonomy interpretation and finite-core SST vortex-filament dynamics are explicit SST extrapolations in this package.

### References

```latex
\begin{thebibliography}{99}

\bibitem{Dubovsky2012HydroEFT}
S.~Dubovsky, L.~Hui, A.~Nicolis, and D.~T.~Son,
``Effective field theory for hydrodynamics: Thermodynamics, and the derivative expansion,''
Phys.\ Rev.\ D \textbf{85}, 085029 (2012).
doi:10.1103/PhysRevD.85.085029.
\url{https://arxiv.org/abs/1107.0731}

\bibitem{Endlich2011PerfectFluids}
S.~Endlich, A.~Nicolis, R.~Rattazzi, and J.~Wang,
``The quantum mechanics of perfect fluids,''
JHEP \textbf{04}, 102 (2011).
doi:10.1007/JHEP04(2011)102.
\url{https://arxiv.org/abs/1011.6396}

\bibitem{IsraelStewart1979}
W.~Israel and J.~M.~Stewart,
``Transient relativistic thermodynamics and kinetic theory,''
Annals Phys.\ \textbf{118}, 341--372 (1979).
doi:10.1016/0003-4916(79)90130-1.

\bibitem{Saffman1992VortexDynamics}
P.~G.~Saffman,
``Vortex Dynamics,''
Cambridge University Press (1992).
doi:10.1017/CBO9780511624063.

\end{thebibliography}
```
