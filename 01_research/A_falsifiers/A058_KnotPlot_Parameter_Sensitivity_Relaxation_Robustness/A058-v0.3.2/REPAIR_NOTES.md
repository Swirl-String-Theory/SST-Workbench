# v0.3.8 repair notes

**Confirmed empirical failure:** In the user's KnotPlot 2026 v0.3.7 native experiment, both `data open`-after-`length/rog` controls returned CSV length=0 and Rg=0 while both `data open`-before-computation controls produced matching nonzero CSV and coordinate scalars. The internally responsible subcommand has not been isolated.

**Repair:** Acquire after each matched `go N` and after initializing the complete `data` stream, compute `length`, `rog`, and then write exactly one `data` row. Reject invalid/zero scalars, parameter readback discrepancies, missing safety markers, wrong iteration, or incorrect geometry even for process returncode 0.

**Important:** These are new, additive non-blind diagnostic probes. This version does not patch the native KnotPlot binary, does not rewrite the original A058 frozen acquisition scripts, and does not certify the 271-condition dataset.

**Historical replay:** `AUDIT_SCALAR_CLOSURE` validates all four originally acquired branches and original case receipt hashes and declares methodological closure `PASS` only when the two valid controls pass and the two deliberately invalid controls reproduce the invalid scalars; it NEVER promotes the two negatives to numerically qualified runs.

**Native requirement:** The new six cases have been tested only with mocked process output on Linux. Real Windows KnotPlot native proof must still be collected and interpreted from the new output directory.
