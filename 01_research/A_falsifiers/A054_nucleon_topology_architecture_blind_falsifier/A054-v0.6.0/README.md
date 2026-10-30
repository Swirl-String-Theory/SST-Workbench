# A054-v0.6.0 — E013 Provider-Convergent State-Selection Falsifier

A054-v0.6.0 is the numerical-consistency successor to the frozen v0.5.0 run. It tests the same scientific hypothesis and keeps the provider/topology thresholds unchanged: distinct current E011 provider anchors may be different representatives of the same topology, and one target-free state-selection operation may map them toward a common stationary/stable state.

## v0.6.0 numerical patch

v0.5.0 differentiated the raw reduced Hamiltonian but accepted trial states only after deterministic resampling and reach normalization. v0.6.0 removes that mismatch by defining one canonical constrained objective for the entire variational lane:

\[
U_c(q;X)=\widehat H_a\!\left(\mathcal N[\mathcal R(X+\delta X(q))]\right).
\]

The finite-difference gradient, Armijo line search, stationarity score, endpoint Hessian and nonlinear reduced ringdown all use exactly this `U_c`.

The selector now uses a global Armijo/trust-region backtracking policy. If the registered numerical ladder cannot demonstrate constrained-objective descent, the carrier is tagged `UNRESOLVED_NUMERICAL`; that condition is not counted as scientific evidence against state selection.

Endpoint Hessian authority is also stricter. The Hessian is recomputed at `eps`, `eps/2` and `eps/4`; its sign is promoted only when the sign class is consistent and the two finest Hessians satisfy the frozen relative-L2 convergence threshold.

## Scientific separation

1. **State selection** — Bishop-Fourier descent on the single constrained objective `U_c`; this is a variational selector, not claimed physical dissipation.
2. **Provider convergence** — independent E011 providers must converge in endpoint energy and geometry descriptors.
3. **Stability** — stationarity is not enough; the constrained Hessian must be numerically converged and nonnegative within tolerance, followed by bounded ringdown on the same objective.
4. **Handoff** — only provider-converged + stationary + Hessian-converged + stable endpoints enter `STATE_SELECTED_CARRIERS.jsonl`.

## E013 contract

A054 consumes only `%SST_CROSS_CARRIER_MANIFEST%` with schema `E013-COMMON-CARRIER-MANIFEST-1`. Legacy A054/A057 output directories are never searched as scientific input. E010 is used only as the source-native parser.

## Install / first run

```bat
run_00_install.cmd
```

Then run from E013:

```bat
run_all_cross_falsifier.cmd PLAN C:\workspace\projects\SST-Workbench
run_all_cross_falsifier.cmd BASIC C:\workspace\projects\SST-Workbench
run_all_cross_falsifier.cmd FULL C:\workspace\projects\SST-Workbench
```

The first scientific invocation automatically executes framework `FREEZE` if `preregistration/FROZEN_PROTOCOL.json` does not yet exist. Freeze is create-once for this v0.6.0 instance.

## Expected E013 order

A054 remains cross-falsifier stage **30**. A057-v0.2.0 remains stage **60** and continues to evaluate the original E013 source states; a later A057 successor can explicitly consume the v0.6.0 state-selection handoff. No existing A057 preregistration is silently changed.

## Important with E013-v0.1.1

E013-v0.1.1 does not deduplicate multiple enabled versions of the same catalog ID. If v0.5.0 is still present, read `E013_UPGRADE_NOTE.md` before running the campaign so the frozen v0.5.0 contract is not discovered alongside v0.6.0.
