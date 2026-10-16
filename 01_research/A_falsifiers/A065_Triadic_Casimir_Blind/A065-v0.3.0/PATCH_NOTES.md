# A065 v0.3.0-r1 — unieke exports + zelfstandige LaTeX

**Maintenance patch only.** Original v0.3.0 scientific equations, source datasets, three individual seals and global commitment are unchanged. Keep your original `A065-v0.3.0` folder intact; extract this full distribution into a **new** folder `A065-v0.3.0-r1`.

## What is fixed

- Every writing run (`ALL`, `FRAMEWORK`, `BLIND`, `FULL`, `BASIC`, `REPORT`, `PARITY`, `DYNAMICS`) uses a fresh `runs/A065-v0.3.0__YYYYMMDDTHHMMSSffffffZ-<random>/` folder. The timestamp is UTC with microsecond resolution; a secure random suffix and atomic directory allocation prevent collisions.
- Every PDF, TeX, blind-results ZIP, separately sealed D01/D02/D03 ZIP, framework PDF and manifest is published under `exports/<RUN_ID>/` with `<RUN_ID>_...` filenames; exclusive create-only file modes refuse collisions.
- No writing run modifies earlier runs, earlier PDF files, existing output archives, source datasets, or source seals. These are separate per-run scientific instances; the canonical framework itself stays frozen.
- The official framework `FRAMEWORK` mode generates its own v1.0.7 `cpu` instance **inside** that run folder. `FREEZE`, `FULL` and `REVEAL_IF_ALLOWED` and its native PDF are retained and exported separately.
- The project report is generated as a **single, self-contained LaTeX `.tex`** with all formulas, gate tables, metrics and seal digests written inline: no `\input`, `\include`, bibliography files, external images or custom font files. Requires a local TeX installation to compile. When `pdflatex` is available, this `.tex` is compiled to PDF twice. When not, the original Python-stdlib PDF fallback still makes a PDF; the `.tex` is always exported.
- `REVEAL` stays blocked while the spatial G2 gate fails / physical G3 is unresolved, even if private escrow is present. No blind target is included in this public patch.

## Windows commands

```bat
run_all.cmd
run_all.cmd FRAMEWORK
run_all.cmd REPORT
run_all.cmd SELFTEST
run_all.cmd VERIFY
run_all.cmd DYNAMICS
run_all.cmd PARITY
```

Find all exported artifacts by unique name in `exports\<RUN_ID>\`; complete per-run workspaces are in `runs\<RUN_ID>\`. No generated data are written to the release root. `REPORT` performs a fresh blind computation in a separate run rather than reusing or overwriting a previous PDF.

The official v1.0.7 framework is looked up from the Workbench under `06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.7`, or by setting `SST_FALSIFIER_FRAMEWORK_ROOT`. It is never packaged or modified.

## Scientific qualification

The dynamic filament spatial convergence gate remains `FAIL` (roughly 8.73% versus pre-registered 5%). The time-step gate and analytical controls are reproducible, but geometry does not certify Euler dynamics or a metallic Casimir response. Fremlin A006 source bytes still require authentic upstream import. D01/D02/D03 are independently **sealed**, not three independent physical-source families.

## Security

SHA-256 manifests detect unexpected byte changes but do not authenticate third-party data origin. A user with access to the public source can recompute outputs; the physical target remains outside the public release and reveals are blocked.

