# A065 v0.3.3 — Numerically Qualified G3 Execution Routing

**Scope:** Complete locally executable source instance, derived from archived A065 v0.3.2. The 11 protected input/seal files and v0.3.2 numerical protocol are byte-identical. Framework v1.0.7 is external, frozen and untouched.

## Run on Windows (Python 3.10+, g++ / MinGW-w64 for native C++)

Unpack alongside previous A065 releases, NOT on top of v0.3.2. From this folder:

```cmd
run_all.cmd VERIFY
run_all.cmd SELFTEST
run_all.cmd QUALIFY
run_all.cmd PARITY
run_all.cmd FRAMEWORK
run_all.cmd ALL
```

`QUALIFY` is a numerics-only, blind, always-PDF path and does not require the external framework. `FRAMEWORK` and `ALL` require the real frozen framework v1.0.7 and pdflatex; they exit code 3 if that framework is missing or failed. Each run creates distinct `runs/<RUN_ID>` and `exports/<RUN_ID>`, without overwriting past runs. `G2=FAIL` is expected, `G10=PASS` is expected, `G3=UNRESOLVED` after numerical readiness is expected. `G11` remains FAIL when authentic Fremlin N59-vs-N118 spatial refinement fails, or unresolved when the source or compiler is unavailable.

Set `SST_FALSIFIER_FRAMEWORK_ROOT` to absolute framework folder if not installed at canonical Workbench path:

```cmd
set "SST_FALSIFIER_FRAMEWORK_ROOT=C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.7"
set "CXX=g++"
run_all.cmd FRAMEWORK
```

For genuine Fremlin geometry, supply unchanged source at default `03_data/A_knots/02_fourier/resources_swirl/3_1/knot.3_1u.short`, or use `set "SST_A065_FREMLIN_PATH=C:\path\to\knot.3_1u.short"`. Exact expected raw SHA-256 is `73cd5304e79a9cf52b71c88d1d7ebc21948a6d87526b0e95ba5aa6f257150e80`. Never silently substitute generated coordinates.

Optional GPU: G6/G7 remain disabled in the v0.3.3 canonical CPU profile. No GPU code or GPU certification is claimed. GPU screening could be added in a later, separately preregistered exploratory module, without affecting G2, G3 or G10.

## Evidence

- `preregistration/ROUTING_V033.json`: versioned fail-closed eligibility rules; original V032 precommit preserved.
- `outputs/ROUTING_V033_RESULT.json` per run: whether refined numerical diagnostics permit G3 **evaluation**, NEVER physical PASS.
- `outputs/QUALIFICATION_V032.json`: original numerical conditions and preserved historical G2 FAIL.
- `docs/RELEASE_V033_AUDIT.json`: release provenance and protected 11 SHA-256 values.
- `tests/test_v033_routing.py`: fail-closed test cases, tamper checks and gate DAG assertions.

Scientific boundary: authentic geometry and numerical regularized filament RK4 do **not** certify full 3D Euler, physical surface materials, Casimir force or gravity. Private reveal comparator stays blocked.
