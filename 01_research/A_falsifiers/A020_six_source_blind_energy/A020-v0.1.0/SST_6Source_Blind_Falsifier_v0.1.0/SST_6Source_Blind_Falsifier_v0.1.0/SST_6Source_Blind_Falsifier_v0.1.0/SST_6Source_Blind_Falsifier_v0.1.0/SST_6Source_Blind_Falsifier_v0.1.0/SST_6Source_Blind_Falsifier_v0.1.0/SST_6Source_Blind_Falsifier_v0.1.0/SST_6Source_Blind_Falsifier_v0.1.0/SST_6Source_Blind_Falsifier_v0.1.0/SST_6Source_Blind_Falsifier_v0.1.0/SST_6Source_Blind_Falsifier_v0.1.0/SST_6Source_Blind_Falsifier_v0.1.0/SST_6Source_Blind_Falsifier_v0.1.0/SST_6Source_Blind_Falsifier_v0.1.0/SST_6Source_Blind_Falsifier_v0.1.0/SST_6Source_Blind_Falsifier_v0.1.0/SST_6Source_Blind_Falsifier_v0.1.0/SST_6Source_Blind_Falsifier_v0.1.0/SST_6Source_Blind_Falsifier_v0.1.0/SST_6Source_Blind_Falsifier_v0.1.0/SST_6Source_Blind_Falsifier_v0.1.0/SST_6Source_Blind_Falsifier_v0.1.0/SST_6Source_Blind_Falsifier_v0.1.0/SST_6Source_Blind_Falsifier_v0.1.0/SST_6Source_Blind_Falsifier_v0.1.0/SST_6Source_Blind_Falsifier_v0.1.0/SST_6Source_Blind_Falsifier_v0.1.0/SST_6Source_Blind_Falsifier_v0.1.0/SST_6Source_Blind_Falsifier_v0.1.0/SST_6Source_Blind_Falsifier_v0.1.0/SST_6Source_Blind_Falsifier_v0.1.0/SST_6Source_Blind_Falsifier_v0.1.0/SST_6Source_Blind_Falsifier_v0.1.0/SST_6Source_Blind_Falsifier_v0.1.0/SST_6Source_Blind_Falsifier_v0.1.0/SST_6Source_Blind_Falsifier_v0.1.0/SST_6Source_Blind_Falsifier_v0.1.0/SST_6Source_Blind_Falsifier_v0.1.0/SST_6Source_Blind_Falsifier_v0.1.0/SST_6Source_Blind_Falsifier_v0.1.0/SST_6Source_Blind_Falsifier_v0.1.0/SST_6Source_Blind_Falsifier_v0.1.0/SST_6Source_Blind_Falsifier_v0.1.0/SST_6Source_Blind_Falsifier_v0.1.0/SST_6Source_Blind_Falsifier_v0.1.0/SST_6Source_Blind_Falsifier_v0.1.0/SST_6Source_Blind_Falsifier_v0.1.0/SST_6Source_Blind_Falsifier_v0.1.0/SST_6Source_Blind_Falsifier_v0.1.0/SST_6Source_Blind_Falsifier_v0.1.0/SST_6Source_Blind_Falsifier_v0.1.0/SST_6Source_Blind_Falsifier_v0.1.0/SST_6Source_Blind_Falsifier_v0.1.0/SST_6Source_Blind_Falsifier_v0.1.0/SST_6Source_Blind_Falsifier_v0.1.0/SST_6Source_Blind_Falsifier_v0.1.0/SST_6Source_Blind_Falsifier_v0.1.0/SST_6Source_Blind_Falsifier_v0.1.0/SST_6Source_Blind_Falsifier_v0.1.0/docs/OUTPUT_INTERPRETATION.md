# Output interpretation

Start with `RUN_ALL_SUMMARY.json`, then inspect `extended/SUMMARY.json`.

Recommended order:

1. `backend` must be `cpp` for a production full run.
2. `error_count` must be zero.
3. Both H6 calibration gates must PASS.
4. U1 and H5 ribbon numerical/geometric identities should PASS.
5. Treat U2 only after checking both nested-domain values and the extended resolution.
6. Inspect research/model gates individually; FAILs are retained as results, not erased.
7. Inspect diagnostic/proxy gates last. They are deliberately excluded from the main hypothesis count.

The package does not emit a single `SST true/false` number. Each gate has a narrow hypothesis so a failure has a precise meaning.
