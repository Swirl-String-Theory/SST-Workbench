# Validation — v0.1.4

Added regression gate: one valid candidate must produce a strict-JSON `INCONCLUSIVE` result with `null` for statistically undefined fields. Scientific kernels and thresholds are unchanged.

# Validation — v0.1.3

The v0.1.3 change is orchestration-only. It removes PowerShell from input discovery
to support systems enforcing signed PowerShell scripts. Scientific code and frozen
gates are unchanged.

Static validation:
- `_RESOLVE_INPUT.cmd` contains no `powershell` invocation.
- `resolve_input.py --help` parses successfully.
- Existing Python scientific regression suite remains unchanged.
- Native parity logic remains unchanged.

# Validation — v0.1.2

Scientific kernels and preregistered thresholds are unchanged from v0.1.1.

Hotfix scope:
- input-directory resolution only;
- explicit verification that `*_i10000.txt` exists before blind preparation;
- checkpoint diagnostics when final files are absent;
- support for the two workspace path spellings observed in the campaign.

Regression status in artifact environment:
- Python unit tests: PASS (4/4)
- C++ core compilation: unchanged from v0.1.1 PASS
- resolver script static inspection: PASS
- blind scientific formulas/configuration: unchanged

The PowerShell resolver must ultimately be exercised on the Windows target because
the exact drive/layout is target-specific.
