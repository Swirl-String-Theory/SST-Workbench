# CHANGELOG v0.2.2

## Fixed false RUN_FAILED classification
- Ignores `nothing to save` / `nothing to output` in the pre-load startup preamble.
- Hard save/output errors after the first `knot loaded` marker still fail the run.
- Parameter rejection parsing is unchanged.

## Observed target-run interpretation
The v0.2.1 output bundle contains complete `i00000` and `i00100` outputs for
charge, hooke and power, with process exit 0 and no parameter rejection.
Those families were falsely failed only by the preamble parser.

`timeincr = value` is genuinely rejected as `Unknown parameter: timeincr`.

## Scientific sweep values
Unchanged.
