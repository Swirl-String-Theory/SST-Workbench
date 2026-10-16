# A062-v0.3.0 — Swirl-Clock monopole / Euler pressure source falsifier

**Framework included:** `SST_Falsifier_Framework_v1.0.8` in `SST-Workbench/06_templates/SST_Falsifier_Framework/`. It is the unmodified **LOCAL_VALIDATED_CANDIDATE** (not a certified canonical frozen release). Its run-ID archive retention and unique ZIP/PDF filenames are active. Framework historical instances are not modified. Framework release metadata and tests included.

## Installation (Windows)

Extract the distribution ZIP to any temporary directory. Merge the **contents of `SST-Workbench_DISTRIBUTION`** into your existing `C:\workspace\projects\SST-Workbench` root, preserving the `06_templates` and `01_research` layout; do not place an extra distribution-folder level in the Workbench. New folders are versioned. Use a venv with Python 3.11+ and `pip install -r requirements.txt` in the A062 instance; `g++` or `clang++` for strict C++17 parity; LaTeX for the framework PDF (MiKTeX or TeX Live). No SYCL required.

```
cd C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A062_SST_Microgravity_Force_Gradient\A062-v0.3.0
python -m pytest -q tests
run_all.cmd FREEZE
run_all.cmd CERTIFY
```

`run_all.cmd FREEZE` calls `init_private.py` once: creates `private/REVEAL_NONCE.bin` and `private/OPAQUE_ID_KEY.bin` with 32 cryptographically random bytes only if missing and only before any existing commitments or frozen protocol. Never regenerate them for a frozen instance. They are intentionally **NOT SHIPPED** in the distributable source ZIP. These files and other `private/` contents must remain private; do not commit them to a public repository.

### Scientific protocol

* **H0** Euler-only: `laplacian(p)=-rho_f partial_i partial_j(v_i v_j)` has zero integrated source for localized solenoidal velocity fields with vanishing boundary terms. Thus the directly identified clock monopole is zero under this restricted hypothesis.
* **H1** Conditional massless scalar field: postulates `kappa laplacian(tau)=-lambda rho_Q`, normalized charges `Q_A=Q_B=1` and unit `kappa=lambda=1`; computes scalar Green pair force + independent stress surface integral. H1 inverse-square is *assumed at the field-law level* and is not a microphysical SST derivation. Outputs are normalized (not SI newtons).
* **H2** Genuine bridge: seeks a nonzero source charge, physical mass, constitutive action and dimensionful `lambda^2/kappa` from PKLSA; **UNRESOLVED** for general SST modes. The specific direct pressure-source identification fails.

Two raw original E011/SKLSA v0.3.0 trefoil anchors are included (`Gilbert Ideal.txt.gz` and KnotPlot final VECT). Input hashes checked; E011 `STATIC_READY != DYNAMICS_READY`. v0.2 user run results stored as an immutable *historical comparison input*, not rerun or elevated to evidence.

The peer-reviewed 2026 microgravity paper is already public; no empirical blind result or gravitational constant is inferred. Framework source honesty: v1.0.8 release metadata names it `LOCAL_VALIDATED_CANDIDATE`, not `CANONICAL_FROZEN`. PDF report uses its actual version and label.

Outputs: `sst_microgravity_force_gradient_v0.3.0-outputs/` current working tree; previous trees archived to unique `-outputs__RUN-ID` directories; sibling `...outputs__RUN-ID_BLIND.zip`; parent run-unique PDF. The archive excludes generated private files and output folders; each Windows execution generates different run-ID exports while keeping existing results.
