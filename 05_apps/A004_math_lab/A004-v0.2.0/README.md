# SST Math Lab v0.2.0

Local browser-based knot-physics workbench. No Math Suite extension is required.

## Start

### Normal start
Double-click:

`run.cmd`

If the six pinned JavaScript libraries are not present in `lib/`, the launcher runs `install_libs.cmd` once. Later runs use the local copies.

### Local HTTP mode
If your browser blocks a `file://` operation, use:

`run_server.cmd`

This starts a Python HTTP server on `http://127.0.0.1:8787/`.

## What changed from v0.1.0

v0.2.0 keeps the geometry and math-console layer and adds a physical finite-core branch:

1. finite-core regularized Biot–Savart evaluation in SI units;
2. tangent/normal/binormal velocity decomposition;
3. shape velocity with the tangential reparameterization component removed;
4. dynamic-pressure magnitude diagnostics;
5. incompressible Euler pressure-Poisson source probe;
6. numerical divergence sanity check;
7. periodic rotation-minimizing / parallel-transport perturbation frame;
8. raw frame-holonomy measurement around the closed curve;
9. reduced normal/binormal Fourier stability Jacobian;
10. complex eigenspectrum with growth rate `Re(lambda)` in `s^-1`;
11. centered perturbation differences and optional `epsilon/2, epsilon, 2 epsilon` convergence ladder;
12. multi-file and folder batch import for KnotPlot / Ridgerunner centerlines;
13. batch CSV export.

## Canonical SST constants

The app uses exactly:

- `v_swirl = 1.09384563e6 m s^-1`
- `r_c = 1.40897017e-15 m`
- `rho_core = 3.8934358266918687e18 kg m^-3`
- `rho_f = 7.0e-7 kg m^-3`
- `F_swirl_max = 29.053507 N`
- `F_gr_max = 3.02563e43 N`

and

`Gamma_SST = 2 pi r_c v_swirl`.

## Geometry pipeline

For generated and imported closed centerlines:

1. parse/generate centerline;
2. remove a duplicate closing vertex if present;
3. uniformly resample closed polygonal arclength;
4. evaluate periodic centered finite differences;
5. compute curvature and torsion;
6. map coordinate units to metres with `physical scale`;
7. resample independently to the lower-resolution physics grid.

Uniform arclength resampling is intentional for KnotPlot/Ridgerunner exports with nonuniform point spacing.

## Finite-core Biot–Savart model

The browser kernel evaluates the regularized segment quadrature

`v(x_i) = Gamma/(4 pi) sum_j [ dl_j x (x_i - m_j) / (|x_i-m_j|^2 + a_core^2)^(3/2) ]`.

Here `m_j` is the segment midpoint and `dl_j` is its directed segment vector.

Dimensions:

`[Gamma] [dl] [r] / [r^3] = (m^2/s) m m / m^3 = m/s`.

The default is:

`a_core = 1.0 r_c`

but this is exposed as a sensitivity parameter. The discrete regularization is a numerical finite-core model; it must not be interpreted as a uniquely derived SST core kernel.

## Velocity decomposition

At each physics station:

`v_T = v . T`

`v_N = v . N`

`v_B = v . B`

and the geometry-changing velocity is

`v_shape = v - (v . T) T`.

Tangential filament velocity largely changes parameterization rather than instantaneous centerline shape. The reduced stability gate therefore perturbs and observes only normal/binormal degrees of freedom.

## Periodic transport frame and holonomy

A discrete rotation-minimizing frame is parallel-transported around the centerline. Its raw closure mismatch is reported as a holonomy angle.

A distributed counter-rotation is then applied around the loop to create a periodic perturbation frame. This avoids the strongest Frenet-frame flip pathology at low curvature and provides a stable Fourier basis for closed knots.

The reported holonomy is a geometric frame diagnostic. It is not automatically identical to any SST physical phase/clock holonomy.

## Pressure diagnostics

### Dynamic-pressure magnitude

`Delta p_dyn = 1/2 rho_f |v|^2`.

This is a Bernoulli-like magnitude diagnostic, not a solved global pressure field.

### Pressure-Poisson source

For incompressible Euler flow:

`nabla^2 p = -rho_f sum_ij (partial_i v_j)(partial_j v_i)`.

The app samples the Biot–Savart velocity at positive/negative Cartesian offsets around every physics station, constructs the local velocity-gradient tensor, and evaluates the right-hand side.

The same tensor gives:

`div v = partial_x v_x + partial_y v_y + partial_z v_z`.

Because femtometre spatial scales produce enormous dimensional gradients, the UI reports both dimensional divergence and the more useful ratio

`R_div = RMS(div v) / RMS(||grad v||_F)`.

A small `R_div` is the numerical incompressibility sanity target.

## SST local time diagnostic

The UI can use one of four velocity sources:

- finite-core Biot–Savart shape speed;
- finite-core Biot–Savart total speed;
- exploratory curvature-weighted speed;
- canonical constant swirl speed.

The displayed diagnostic is

`d tau/dt = sqrt(1 - v^2/c^2)`

and the plot shows

`10^6 (1 - d tau/dt)` in ppm.

If `|v| >= c`, the point is explicitly marked invalid rather than clipped.

## Reduced physical stability gate

The perturbation space contains, for every mode `m = 1 ... M`,

- normal cosine;
- binormal cosine;
- normal sine;
- binormal sine.

Therefore the reduced Jacobian dimension is

`4 M`.

For basis field `e_a(s)` and coefficient `q_a` with dimensions of length, the code computes a centered finite difference of the induced velocity:

`d v / d q_a ~= [v(r + epsilon e_a) - v(r - epsilon e_a)] / (2 epsilon)`.

It projects this response onto the periodic normal/binormal basis to form

`A_ba = <e_b, d v/dq_a> / <e_b,e_b>`.

Since velocity divided by displacement has dimensions

`(m/s)/m = s^-1`,

the eigenvalues of `A` are reported in `s^-1`.

Interpretation:

- `Re(lambda) > 0`: instantaneous growing component in the reduced frozen-geometry linearization;
- `Re(lambda) < 0`: instantaneous decaying component;
- `Im(lambda) != 0`: oscillatory component;
- near-zero values may include symmetries, gauge effects, truncation effects or marginal modes.

### Critical limitation

This is **not** a Floquet/RPO stability proof. A relaxed knot may translate, rotate, precess or execute a relative periodic orbit. Definitive stability requires linearizing the correct co-moving periodic dynamics and evaluating monodromy/Floquet multipliers.

The current gate is therefore best used as a fast falsifier and mode-discovery tool.

## Epsilon convergence ladder

With the checkbox enabled, the reduced Jacobian is evaluated at

`epsilon/2`, `epsilon`, and `2 epsilon`.

The reported spread of the maximum growth rate is

`(max(g)-min(g)) / mean(|g|)`.

Large spread means the selected perturbation amplitude is not in a trustworthy linear regime or the discretization is too coarse.

## Kelvin / LIA diagnostic

The older v0.1 leading-log gate remains available:

`omega_n ~= Gamma k_n^2/(4 pi) ln[1/(k_n a)]`,

`k_n = 2 pi n/L`.

It remains a thin-filament diagnostic, not a replacement for the finite-core Biot–Savart stability operator.

## Batch KnotPlot / Ridgerunner workflow

Use either:

- `Select files` for multiple `.txt/.xyz/.csv/.dat` centerlines;
- `Select folder` for a complete dataset directory.

Then press `Run batch`.

The batch table records:

- filename/path;
- raw point count;
- `L/r_c`;
- maximum `kappa r_c`;
- mean and maximum Biot–Savart speed;
- maximum reduced growth rate if batch stability is enabled.

`Export batch CSV` writes the summary table.

### Recommended first pass

For a large relaxed-knot collection:

- geometry points: `1200`;
- physics points: `128` or `192`;
- batch stability: OFF.

Use the summary to identify outliers, then rerun a shortlist with:

- physics points: `192 -> 256 -> 384`;
- stability modes: `3 -> 4 -> 6`;
- epsilon convergence: ON;
- several `a_core/r_c` values.

This separates physical trends from resolution/core-model sensitivity.

## Self-test

`Run self-test` uses a circular filament to check:

- circumference;
- curvature;
- zero torsion;
- expected purely binormal Biot–Savart direction by symmetry;
- periodic finite-difference spectral accuracy.

A self-test PASS confirms basic numerical plumbing. It does not validate an SST physical hypothesis.

## Export

### Current CSV
Contains both:

1. geometry-grid curvature/torsion and exploratory diagnostics;
2. finite-core physics-grid `v_T`, `v_N`, `v_B`, speed, shape speed, pressure and pressure gradient.

### Current JSON
Contains settings, summary metrics, Kelvin modes and—after running stability—the reduced matrix and complex eigenvalues.

## Falsifier interpretation

A useful SST claim should survive at least:

1. geometry-point convergence;
2. physics-point convergence;
3. finite-core radius sensitivity;
4. pressure-probe-step sensitivity;
5. perturbation-epsilon convergence;
6. reduced-mode ceiling convergence;
7. change of centerline sampling before/after uniform resampling;
8. eventual comparison with a co-moving RPO/Floquet calculation.

Do not treat one positive or negative eigenvalue at one discretization as a final claim about knot stability.

## Files

- `index.html` — UI
- `js/geometry.js` — resampling, curvature, torsion
- `js/physics.js` — finite-core Biot–Savart, pressure-Poisson probe, transport frame, reduced stability
- `js/diagnostics.js` — time/Kelvin/FD sanity gates
- `js/batch.js` — multi-file processing
- `js/plots.js` — Plotly views
- `js/app.js` — UI orchestration
- `REFERENCES.tex` — copy-ready bibliography entries
- `FALSIFIER_GATES.md` — concise gate definitions

