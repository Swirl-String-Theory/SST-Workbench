# Ruban v0.1.1 validation summary (development only)

- 12 tests pass locally (seven inherited from v0.1.0, five patch regressions).
- v0.1.0 numerical failure: N=256, requested dt=0.002, t=1 had catastrophic energy growth. Suspected local induction explicit-step instability.
- v0.1.1 local smoke verification: N=256, requested dt=0.002, t=1 reaches TIME_LIMIT with relative energy drift near 1.86e-5, because the new cap restricts the accepted step to about 0.0004 initially.
- v0.1.1 BASIC test: B0=0.170 stops at t=0.175 on energy drift; FAIL gate and exit code 2 correctly propagated. Other B0 cases hit short time limit but do not qualify stability.
- Fixed-time comparison under CONVERGE is a short development screening, not a certified spatial/temporal-convergence gate; compare model sensitivity at fixed delta separately from delta sensitivity.
- Template alignment: based on actual SST Falsifier Framework v1.1.0 RC2 LaTeX report, 16 section markers, dynamic AUTO_RESULTS and 2x2 seed plot; no framework runtime certification and no protocol freeze.
- FULL to t=320, independent numerical convergence, internal twist, finite-core Euler and parallel lattice: not executed / unresolved.

Do not interpret `TIME_LIMIT` as physical stability, or short-term gate G2 PASS as framework certification.
