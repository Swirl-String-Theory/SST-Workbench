# A054 v0.4.0-r3 maintenance hotfix

No scientific equations, mechanism arms, gain grid, source cohorts, or hard gates are changed.

Execution/reporting fixes:
1. Fix LaTeX bibliography escaping in `report/FALSIFIER_REPORT.tex`.
2. Move the Python virtual environment outside the blinded instance root so the framework blind scanner cannot inspect third-party `site-packages`.
3. Remove a legacy in-instance `.venv` during setup migration.
4. Preserve fail-closed command propagation.

The r2 BASIC scientific result is not changed or reinterpreted by this hotfix.
