# Validation — E012 v0.2.0

v0.2.0 separates five validation layers:

1. **E011 provenance:** at least two independent `STATIC_READY` provider anchors are required.
2. **C006 execution:** every preregistered `(provider,N,m)` level must execute against C006-v0.3.0; native/Python backend identity is recorded per level.
3. **Background conditioning:** each provider is tested with C006's same-generator RPO search using the exact spectral-generator parameters and no parameter scan.
4. **Mode identity and convergence:** the finest-N positive-frequency C006 root is tracked backward using eigenvalue distance plus complex eigenvector overlap. Only individually qualified modes can enter a provider branch.
5. **Cross-provider agreement and physical handoff:** at least three modes must be independently qualified by every provider and agree inside the frozen dynamic-provider bands. SI/energy mapping remains a separate approved contract.

The v0.1.x full-spectrum root-persistence result is retained as a diagnostic. It is not silently deleted; v0.2 replaces its use as **specific branch identity** with a stricter branch-specific eigenvector-overlap test.

An RPO acceptance does not establish true Floquet monodromy. v0.2.0 makes no true-Floquet claim.
