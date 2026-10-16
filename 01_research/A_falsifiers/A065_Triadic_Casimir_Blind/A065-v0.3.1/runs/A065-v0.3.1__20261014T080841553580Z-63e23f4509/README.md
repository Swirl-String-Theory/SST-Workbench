# A065 Triadic-Casimir / PKLSA Falsifier v0.3.1

**Qualification tranche, not a physical Casimir demonstration.** New version; do not overwrite A065 v0.3.0 or v0.3.0-r1. Uses **external unchanged** `SST_Falsifier_Framework_v1.0.7` for the official protocol freeze, gate ledger and reveal policy.

## Scientific changes

1. **One provider manifest per run:** read raw Fremlin A006 source once before the blind/official stages, commit its exact absolute path and SHA-256, and reverify the *same immutable manifest* in both portable and framework instances. A missing provider remains `UNRESOLVED_SOURCE_MISSING`, not a synthetic replacement. The raw source is not shipped; this package can run with the missing-provider status recorded.
2. **Fixed-core spatial ladder:** N=75/150/300 from **one** authenticated 300-point KnotPlot trefoil. The same `gamma=1`, `epsilon=0.12`, `T_final=0.04` and fine RK4 step count 8 apply to every grid. The 75→150 gate remains exactly as in v0.3.0: ~8.73% vs a predeclared 5% tolerance. The new 150→300 gate is ~3.27% (PASS); 75→300 is ~12.12% (FAIL). No normalization changes, core retuning or retrospective tolerance changes.
3. **Framework CPU DAG:** in the *new instance, before FREEZE*, G5 requires G1 (independent kernel-only C++ parity may run despite a G2 failure); G8 requires G3 plus G5, not disabled G7. Gate G5's narrowed question and recorded authority explicitly cover only the actual C++17 FP64 **velocity kernel**, not full RK4, Euler or physical CASIMIR certification. The frozen framework source is never modified.
4. **Three unchanged sealed datasets:** D01/D02/D03 raw data and their three original SHA-256 seals are byte-identical with A065 v0.3.0-r1. All new v0.3.1 pre-registered numerics live in `preregistration/QUALIFICATION_V031.json`, outside those legacy sealed data.
5. **Unique create-only exports:** every run has its own `runs/A065-v0.3.1__<UTC>-<nonce>/` and `exports/<same_id>/`, including standalone `.tex`, compiled `.pdf`, three sealed dataset ZIPs, blind results, and SHA-256 export manifest. No silent overwrites of old runs.

## Windows run

Install or retain the untouched canonical SST framework under

```text
C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.7
```

Place this instance in a *new* `...\01_research\A_falsifiers\A065_Triadic_Casimir_Blind\A065-v0.3.1` folder. The Fremlin raw file is normally at `03_data\A_knots\02_fourier\resources_swirl\3_1\knot.3_1u.short` relative to `SST_WORKBENCH_ROOT`, or use an explicit override:

```bat
set SST_WORKBENCH_ROOT=C:\workspace\projects\SST-Workbench
set SST_A065_FREMLIN_PATH=C:\workspace\projects\SST-Workbench\03_data\A_knots\02_fourier\resources_swirl\3_1\knot.3_1u.short
run_all.cmd FRAMEWORK
```

To run portable tests and numerical gates, including LaTeX/PDF:

```bat
run_all.cmd ALL
run_all.cmd SELFTEST
run_all.cmd PROVIDER
run_all.cmd DYNAMICS
run_all.cmd VERIFY
```

`FRAMEWORK` mode requires the genuine installed v1.0.7 distribution. `ALL` still produces a standalone PDF if the framework is missing, while honestly marking framework status `FRAMEWORK_NOT_FOUND`. The strict framework pipeline uses `pdf_required=true`; it may require `pdflatex`/`latexmk` installed on Windows. The portable PDF uses `pdflatex` if available and a built-in PDF fallback otherwise. The `.tex` is standalone, without `\input` or external images/fonts.

## Scientifically required next steps

The 150/300 gate is a useful numerical diagnostic, **not** proof of 3D Euler convergence or a physically qualified PKLSA atom-clock, metal response, or Casimir force. A verified raw Fremlin centerline establishes only a second geometry source. Full dynamical replication, pressure boundary conditions, physical matter/link coupling and independent physical stress tests remain unresolved. No physical target is revealed.

See `docs/QUALIFICATION_V031.md`, `preregistration/QUALIFICATION_V031.json` and the generated PDF.
