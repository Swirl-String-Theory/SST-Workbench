# Einstein–SST Emergent Metric and Poisson Closure Gates v0.1.1

Blind Python/C++ workbench for relaxed-knot centerlines. The load-bearing tests are:

- **1/r monopole:** does the reconstructed closed-knot field satisfy \(v^2\propto1/r\), required by \(\Phi_{\rm SST}=-v^2/2=-GM/r\)?
- **pressure-Poisson integral:** does \(\int Q\,dV\), with \(Q=\tfrac12\omega^2-S:S\), approach a nonzero monopole and agree with the \(v^2\)-derived strength?
- **pressure--Phi closure:** does the pressure-Poisson surface integral agree with the surface integral of \(\nabla(-v^2/2)\)?

The package reconstructs a regularized incompressible filament field from each relaxed centerline. This reconstruction is explicit and preregistered; a relaxed curve by itself does not uniquely determine a 3-D velocity field.

## Easiest Windows run

From the unpacked workbench folder:

```bat
run_all.cmd "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
```

`run_all.cmd` is the **normal** preset and performs install -> C++ build -> selftest -> blind normal campaign -> reveal/report.

Ready-made full-chain scripts:

```bat
run_all_basic.cmd "..\..\KnotPlot\knots\final"
run_all_normal.cmd "..\..\KnotPlot\knots\final"
run_all_extended.cmd "..\..\KnotPlot\knots\final"
```

Optional second argument is the output directory.

## Outputs

Each run writes:

- `preregistered_config.json`
- `measurements_blind.csv`
- `shells/K_<blind>_shells.csv`
- `reveal_gates.csv`
- `revealed_results.csv`
- `campaign_summary.json`
- `REPORT.md`
- plots
- `runtime.json`

`outputs\LATEST.txt` points to the latest run.

## Interpretation

A FAIL of the headline gates means the **direct** chain

\[
\mathbf v\to g^{\rm eff}_{\mu\nu}\to\Phi=-v^2/2\to p/\rho_{\!f}\to Q
\]

is not supported for the preregistered regularized closed-filament reconstruction. It does **not** automatically exclude a separate/nonlocal SST long-range gravitational closure.


## v0.1.1 build compatibility

This release fixes the MSVC/pybind11 `C2665` error produced by mixed integer types in NumPy shape initializer lists. All native array dimensions are explicitly `py::ssize_t`. The numerical model, preregistered thresholds, blind protocol, and gate definitions are unchanged from v0.1.0.

For a compiler-only diagnostic without OpenMP, run `run_build_cpp_noomp.cmd`.
