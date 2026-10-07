# A056 v0.2.0 preregistration

Frozen before real PKLSA/Euler/finite-core provider data are scored.

## Primary nulls

1. A periodic restoring law is not required: Sine--Gordon does not outperform Wave/Klein--Gordon/Duffing competitors on discovery and held-out confirmation.
2. Fractional memory is not required: Mittag--Leffler does not outperform exponential, stretched-exponential, and bi-exponential competitors.
3. Any apparent preference does not replicate across independent source groups after numerical certification.

## Discovery / confirmation split

Phase coefficients and BIC are fit on the first 65% of the temporal samples; the final 35% is a frozen holdout used only for confirmation NRMSE. Ringdown uses a 70/30 temporal split. No threshold is tuned after reveal.

## Primary thresholds

For Sine--Gordon support: \(a>0\), \(b>0\), design condition number \(\le10^8\), discovery \(\Delta\mathrm{BIC}\ge10\), and held-out NRMSE ratio \(\le0.95\) (`basic`) or \(\le0.93\) (`full`).

For Mittag--Leffler support: discovery \(\Delta\mathrm{BIC}\ge10\), held-out NRMSE ratio \(\le0.95\) (`basic`) or \(\le0.93\) (`full`), and \(0.48<\alpha<0.97\).

## Numerical certification

A confirmed case must remain stable under deterministic 2x time/space coarsening. The relative \(\ell_2\) change of the Sine--Gordon coefficient pair must be below the frozen profile threshold. Production profiles additionally require CPU/native parity; the framework smoke profile permits native absence but records it.

## Independence

The primary independent unit is the provider-declared `source_group`, not mesh resolution, seed, GPU replica, or multiple files derived from one carrier. Replication requires at least two independent groups.

## GPU policy

SYCL/Arc is screening-only. The framework's planned worker architecture is represented by an out-of-process probe; A056 v0.2.0 does not allow an accelerator result to promote a scientific claim without CPU certification.
