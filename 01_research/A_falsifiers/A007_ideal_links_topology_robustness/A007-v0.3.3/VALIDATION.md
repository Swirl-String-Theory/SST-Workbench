# Validation — v0.3.3

## Completed checks

- pytest: **28 passed**;
- C++17/pybind11 build: **PASS** on the validation environment;
- native C++/NumPy parity: **PASS** for `L2a1` and `L6a4`;
- fixed-arc velocity parity: machine-precision agreement;
- fixed-arc Neumann parity: machine-precision agreement;
- strict-native quick QM campaign: **18/18 completed, 0 failures**;
- strict-native full-Hessian Hopf smoke: **1/1 completed, 0 failures**;
- fixed-arc continuum campaign on `L2a1 L4a1 L6a4 L6n1 L7n2`: **5/5 completed**.

## Continuum-audit result at N = 96, 192, 384

The configured full-preset tolerance is 5% on the largest last-pair relative change among the audited
baseline diagnostics.

| link | max last-pair relative change | 5% pass |
|---|---:|:---:|
| L2a1 | 0.03770 | yes |
| L4a1 | 0.08346 | no |
| L6a4 | 0.05402 | no |
| L6n1 | 0.06312 | no |
| L7n2 | 0.07955 | no |

This is a useful negative result: v0.3.3 does **not** hide remaining spatial-discretization sensitivity.
Candidates that fail should be refined further (for example 192/384/768) before a v0.4 closure claim.

## Full-Hessian Hopf smoke

The v0.3.3 Hopf run retains the two-dimensional kernel of the candidate two-form.  The new algebraic
image-space quotient has dimension 16, but `physical_quotient_established=false` by construction.
The local Newton probe reduced the best-sector primary gradient from about `8.00` to about `6.02`,
but did not reach the configured stationarity threshold.  No stationary-background claim is made.

## Claims boundary

The release validates implementation and numerical gates, not the physical correctness of the chosen
energy closure.  No 18-link full-Hessian campaign, no 130-link QM campaign, and no numerical Milnor
`mu-bar_123` derivation are claimed here.
