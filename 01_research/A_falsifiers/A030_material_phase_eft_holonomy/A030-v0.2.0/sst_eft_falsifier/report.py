from pathlib import Path


def write_report(outdir,s):
    lines=[
        '# SST Material-Coordinate / Phase-Shift EFT Falsifier','',
        f"**Version:** {s['version']}  ", f"**Overall:** **{s['overall_status']}**  ",
        f"**Samples analyzed:** {s['n_samples']}  ",'',
        '## Gate counts','', '| Gate | PASS | FAIL | SKIP |','|---|---:|---:|---:|'
    ]
    for g,c in s['gate_counts'].items():
        lines.append(f"| {g} | {c.get('PASS',0)} | {c.get('FAIL',0)} | {c.get('SKIP',0)} |")
    lines += [
        '', '## Verdict semantics','',
        '- **G1** is a centerline-accessible numerical surrogate of material relabeling, not the full 3D material-coordinate symmetry.',
        '- **G2** is a geometric candidate-phase/gauge diagnostic. With no measured phase field and no preregistered phase-lock target, a G2 FAIL is not an SST phase-clock falsification.',
        '- **G3** verifies total-derivative / integration-by-parts reduction and implementation consistency; it is not an independent physical prediction.',
        '- **G4** is the physical closure gate in this package: regularized finite-core Biot-Savart local linear response fitted to `omega^2 = a2 q^2 + a4 q^4` after finite-difference linearization convergence filtering.',
        '- **T/S** are numerical certification gates. A certification failure makes the physical verdict numerically inconclusive.',
        '',
        'Projected eigenvalues are explicitly treated as **instantaneous local-response eigenvalues**, not Floquet/stability exponents unless the base curve is independently shown to be a relative equilibrium of the same dynamics.',
        '',
        'A survived closure is not confirmation of SST. `CLOSURE_FAIL` falsifies the tested closure at the configured thresholds; `INCONCLUSIVE` or `NUMERICALLY_INCONCLUSIVE` requires a better-resolved run before a physical conclusion.'
    ]
    Path(outdir,'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
