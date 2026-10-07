# A056 v0.2.1 preregistration

Frozen before real PKLSA/Euler/finite-core provider data are scored.

## Primary nulls

1. A periodic restoring law is not required: Sine--Gordon does not outperform Wave/Klein--Gordon/Duffing competitors on discovery and held-out confirmation.
2. Fractional memory is not required: Mittag--Leffler does not outperform exponential, stretched-exponential, and bi-exponential competitors.
3. Any apparent preference does not replicate across **physically independent** evidence after numerical certification.

## Discovery / confirmation split

Phase coefficients and BIC are fit on the first 65% of temporal samples; the final 35% is a frozen holdout used only for confirmation NRMSE. Ringdown uses a 70/30 temporal split. No threshold is tuned after reveal.

## Primary thresholds

For Sine--Gordon support: \(a>0\), \(b>0\), design condition number \(\le10^8\), discovery \(\Delta\mathrm{BIC}\ge10\), and held-out NRMSE ratio \(\le0.95\) (`basic`) or \(\le0.93\) (`full`).

For Mittag--Leffler support: discovery \(\Delta\mathrm{BIC}\ge10\), held-out NRMSE ratio \(\le0.95\) (`basic`) or \(\le0.93\) (`full`), and \(0.48<\alpha<0.97\).

## Numerical certification

A confirmed case must remain stable under deterministic 2x time/space coarsening. The relative \(\ell_2\) change of the Sine--Gordon coefficient pair must be below the frozen profile threshold. Production profiles additionally require CPU/native FP64 parity. The framework smoke profile permits native absence but records it.

## Evidence classes and replication

Each provider case must declare

`evidence_class in {synthetic_control, simulation, independent_source, experimental}`.

The replication unit is not merely a file or label:

- synthetic controls are grouped by generator identity;
- simulation cases are grouped by solver-independence identity;
- physical cross-source replication may use only `independent_source` or `experimental` groups.

`G5_CONTROL_REPLICATION` is an implementation-validation gate. `G5_CROSS_SOURCE_REPLICATION` is the scientific replication gate. Synthetic or same-solver replication cannot satisfy the latter.

At least two physical independent groups are required for `G5_CROSS_SOURCE_REPLICATION = PASS`.

## GPU policy

SYCL/Arc is screening-only.  DD32/FP32x2 is explicitly not IEEE FP64.  Backend smoke may validate DD32 numerics, but final scientific promotion still requires CPU/Python or C++ FP64 certification.
