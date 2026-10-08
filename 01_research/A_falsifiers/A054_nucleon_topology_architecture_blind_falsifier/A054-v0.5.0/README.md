# A054-v0.5.0 — E013 Provider-Convergent State-Selection Falsifier

Purpose: test the hypothesis exposed by A057-v0.2.0 without importing any old falsifier result as evidence: distinct current E011 provider anchors may be different representatives of the same topology, and a target-free state-selection operation may map them toward a common stationary/stable state.

## Scientific separation

1. **State selection**: reduced Bishop-Fourier steepest descent of the same reach-normalized finite-core Hamiltonian used for comparison. This is a variational selector, not claimed physical dissipation.
2. **Provider convergence**: independent E011 providers must converge in endpoint energy and geometry descriptors.
3. **Stability**: stationarity is not enough; the endpoint Hessian must be nonnegative within tolerance and nonlinear reduced ringdown must remain bounded.
4. **Handoff**: only provider-converged + stationary + stable endpoints enter `STATE_SELECTED_CARRIERS.jsonl`.

## E013 contract

A054 consumes only `%SST_CROSS_CARRIER_MANIFEST%` with schema `E013-COMMON-CARRIER-MANIFEST-1`. Legacy A054 output directories are never searched. E010 is used only as the source-native parser.

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

The first scientific invocation automatically executes framework `FREEZE` if `preregistration/FROZEN_PROTOCOL.json` does not yet exist. Freeze is create-once.

## Expected E013 order

A054 has cross-falsifier stage **30**. A057-v0.2.0 is stage **60**, so E013 runs A054 first. A057-v0.2.0 still evaluates the original E013 carriers; a later A057 successor can explicitly consume `A054_STATE_SELECTION_HANDOFF.json`. This avoids silently changing A057-v0.2.0 after preregistration.
