#!/usr/bin/env python3
"""
Route A preregistered vacuum-tangle target harness.

This is NOT a derivation of Lambda_L. It freezes the target and the admissible
model grammar so future work can test a single independently derived vacuum-line
density without look-elsewhere freedom.
"""
from __future__ import annotations
import json, math
from pathlib import Path

C = {
    'c': 299_792_458.0,
    'hbar': 1.054_571_817e-34,
    'G_N': 6.67430e-11,
}

L_p = math.sqrt(C['hbar'] * C['G_N'] / C['c']**3)
t_p = math.sqrt(C['hbar'] * C['G_N'] / C['c']**5)

# Preregistered target only. No parameter scan is allowed in this file.
sigma_pierce_default = 1.0
sigma_lambda_target = 1.0 / (2.0 * L_p**2)
Lambda_L_target_if_sigma_1 = sigma_lambda_target / sigma_pierce_default
line_spacing_if_sigma_1 = Lambda_L_target_if_sigma_1 ** -0.5

out = {
    'status': '[PREREGISTERED TARGET] [NOT DERIVED]',
    'forbidden_inputs_for_derivation': ['G_N', 'L_p', 't_p'],
    'allowed_role_of_G_N_here': 'target/reporting only, not input to future vacuum-tangle derivation',
    'target': {
        'sigma_pierce_times_Lambda_L_m_minus_2': sigma_lambda_target,
        'Lambda_L_if_sigma_pierce_equals_1_m_minus_2': Lambda_L_target_if_sigma_1,
        'line_spacing_if_sigma_pierce_equals_1_m': line_spacing_if_sigma_1,
        't_p_reference_s': t_p,
        'L_p_reference_m': L_p,
    },
    'acceptance_gate_for_future_model': {
        'must_derive': ['Lambda_L', 'sigma_pierce'],
        'must_not_use': ['G_N', 'L_p', 't_p', 'F_gr_max'],
        'must_predeclare': ['orientation distribution', 'line-density definition', 'microstate count per piercing', 'renormalization/cutoff if any'],
        'pass_condition': 'Report Lambda_L and sigma_pierce first; compare to target only after formula is frozen.',
    },
}

outdir = Path(__file__).resolve().parent.parent / 'routeA_preregistered' / 'results'
outdir.mkdir(parents=True, exist_ok=True)
(outdir/'routeA_preregistered_target.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
(outdir/'routeA_preregistered_target.md').write_text(f"""# Route A Preregistered Vacuum-Tangle Target

Status: {out['status']}.

This file freezes the target for a future independent derivation of the SST vacuum vortex-line density.  It does not derive the density.

```text
sigma_pierce * Lambda_L = {sigma_lambda_target:.15e} m^-2
Lambda_L if sigma_pierce = 1 = {Lambda_L_target_if_sigma_1:.15e} m^-2
line spacing if sigma_pierce = 1 = {line_spacing_if_sigma_1:.15e} m
```

Future Route-A work must derive `Lambda_L` and `sigma_pierce` without using `G_N`, `L_p`, `t_p`, or `F_gr_max` as inputs.  The comparison to the target happens only after the formula is frozen.
""", encoding='utf-8')
print(outdir/'routeA_preregistered_target.json')
print(outdir/'routeA_preregistered_target.md')
