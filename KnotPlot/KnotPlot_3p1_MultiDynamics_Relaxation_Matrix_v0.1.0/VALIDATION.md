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
