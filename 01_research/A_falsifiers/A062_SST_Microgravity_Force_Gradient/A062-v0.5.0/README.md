# A062-v0.5.0 — Dynamic Vortex-Tube & Gravitational Source Closure

**Status:** Exploratory genuine **3D short-time periodic incompressible Euler/Navier–Stokes** computation; finite Gaussian E011 tube initialization; no long-time particle-stability or gravity claim. Framework v1.0.8 `LOCAL_VALIDATED_CANDIDATE` is shipped unmodified.

## Scientific separation

The preserved v0.4.0 static baseline tests original E011 Gilbert/KnotPlot (raw SHA-256), free-space finite Gaussian self-energy, finite `E/c²`, and the zero-monopole SST-73 double-divergence in the isolated-decay case. That static result is not a proof of active/passive gravitational mass.

The **new v0.5.0 dynamic module** initializes a *heavily smoothed* Gaussian tube (`a=0.11` normalized, significantly larger than upstream reach 0.025–0.028), projects to a solenoidal bandlimited velocity field in a 3D periodic box `L=1.2`, and solves the *full nonlinear incompressible velocity equation* using a Fourier 2/3-dealiased pseudo-spectral RK4 method. It runs Euler (`nu=0`) and viscous unforced NS (`nu=0.005`) for a **short dimensionless** interval `T=0.03` on N=24,32,48 (FULL/CERTIFY). BASIC uses N=24,32 and T=.012. ν>0 is a numerical/constitutive sensitivity, not a foundational SST viscosity.

The exact Beltrami ABC flow provides the analytic unforced NS decay check, `u(t)=u(0) exp(-nu t)`, in the 2π-periodic box. Additional screens: spectral divergence, Euler energy drift, NS enstrophy dissipation, dt vs dt/2, spatial refinement, and initial vorticity-projector error. **G10 PASS indicates only a successful short-time solver screen, not dynamically stable `3_1`.** Genuine knot topology under advection, relative equilibria, Floquet/Kelvin stability and isolated asymptotics remain open.

The periodic transport-stress double divergence has zero `k=0` Fourier mode, while a periodic Poisson problem with nonzero average energy source is incompatible unless a compensating background is introduced. Therefore a periodic energy charge is not an isolated Newtonian 1/R monopole. Physical Swirl-Clock coupling, Newton-G and equivalence are **G8 UNRESOLVED**. No `G` or electron mass is fitted.

G6 remains NOT_APPLICABLE (SYCL disabled in framework CPU profile); G11 remains UNRESOLVED until long-term stability and topology persist under proper core refinement.

## Windows installation

Merge `SST-Workbench_DISTRIBUTION` from the complete source ZIP into your existing `C:\workspace\projects\SST-Workbench`; it **adds v0.5.0** without modifying v0.4.0.

```bat
cd C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A062_SST_Microgravity_Force_Gradient\A062-v0.5.0
python -m pip install -r requirements.txt
python -m pytest -q tests
run_all.cmd FREEZE
run_all.cmd CERTIFY
```

The `FREEZE` launcher initializes unique 32-byte secrets only if absent **and only if not frozen or committed**; never re-key a frozen instance. Unique run-ID output handling is provided by framework v1.0.8.

## Linux/macOS (where platform tools permit)

```sh
python -m pip install -r requirements.txt
python -m pytest -q tests
./run_all.sh FREEZE
./run_all.sh CERTIFY
```

## Data and epistemic scope

Full numerical records: `V050_DYNAMIC_RESULTS.json` and `V050_SCIENCE_RESULTS.json` in the framework run output; diagnostic plot `V050_DYNAMIC_ENERGY.png`. `inputs/SST_KNOWLEDGE_CENSUS.json` contains 91 article references with explicitly differentiated reading status; indexing is not a claim that all have been substantively tested. SST-28 stays excluded. Public source documents are not held-out experimental evidence.

**Known PDF framework issue:** v1.0.8 `AUTO_RESULTS.tex` may print a provisional output-manifest hash differing from the final archived `OUTPUT_MANIFEST.json`; file hashes inside the final manifest remain independently checked. This distribution leaves the original framework unchanged.
