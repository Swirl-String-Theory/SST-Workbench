# VortexLab v7.6.24e1

## Status

Minimal startup/bootstrap hotfix on top of v7.6.24e. No solver, benchmark, scenario, tolerance, or research logic was changed.

## Fixed

`initGlobalRunStrip(shell)` created the global run-status strip inside a UI shell that had not yet been appended to `document.body`. The implementation then tried to bind the close button through `document.getElementById('vlGlobalRunClose')`. Because the shell was still detached, that lookup returned `null`, causing startup to abort with:

```text
Cannot read properties of null (reading 'addEventListener')
```

The run strip now:

- queries its own children with `strip.querySelector(...)` while detached;
- stores local references to the close button, text node, and progress node;
- validates that all three internal nodes exist before binding;
- uses those local references for later status updates;
- guards against duplicate initialization in both the document and the detached shell.

## Regression test

Self-test `T0e24b` activates the run strip, clicks the close button, and verifies that both the strip and body active-state classes are cleared. This would fail if the close handler were not bound.

## Unchanged

- Biot–Savart and LIA calculations
- RK4 integration and timestep logic
- topology guard and reach diagnostics
- SPEC CLOCK and decomposition scenario definitions
- D0–D14 and Research gate definitions
- tracer suppression and restoration policy
- result accordions, runner focus, lower HUD, and D14 evidence introduced in v7.6.24e
