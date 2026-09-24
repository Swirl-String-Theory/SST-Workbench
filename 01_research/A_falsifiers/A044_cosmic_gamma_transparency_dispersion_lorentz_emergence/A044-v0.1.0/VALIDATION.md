# Validation record

Validation performed in the build environment on 2026-09-08.

- Python source compilation: PASS.
- C++17 pybind11 binding syntax: PASS.
- Native extension manual build against available pybind11 headers: PASS.
- pytest: 5/5 PASS.
- Blind campaign execution: PASS.
- Blind reveal-leakage scan: PASS.
- Reveal commitment verification: PASS.
- Reveal campaign execution: PASS.
- Output packaging: PASS.

The supplied Windows `run_all.cmd` was not executed on Windows in this environment; its native extension code and Python pipeline were exercised equivalently on Linux.
