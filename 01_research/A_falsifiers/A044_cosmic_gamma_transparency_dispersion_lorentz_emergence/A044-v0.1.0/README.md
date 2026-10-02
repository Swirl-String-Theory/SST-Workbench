\
# SST_Cosmic_Gamma_Transparency_Dispersion_Lorentz_Emergence_Falsifier v0.1.0

Blind **cosmic gamma transparency / photon-dispersion / emergent-Lorentz** qualification gate inspired by Galanti & Roncadelli, arXiv:2504.01830v3.

## One-click Windows run

```bat
run_all.cmd
```

The command:

1. creates/updates `.venv`;
2. installs Python dependencies;
3. builds the C++17/pybind11 native backend;
4. runs pytest;
5. executes the blind campaign;
6. audits blind output for reveal leakage;
7. reveals SST only if the private payload is present;
8. writes outputs to `./SST_Cosmic_Gamma_Transparency_Dispersion_Lorentz_Emergence_Falsifier_v0.1.0-outputs/`;
9. creates shareable `../SST_Cosmic_Gamma_Transparency_Dispersion_Lorentz_Emergence_Falsifier_v0.1.0-outputs_BLIND.zip` and, when revealed, `../SST_Cosmic_Gamma_Transparency_Dispersion_Lorentz_Emergence_Falsifier_v0.1.0-outputs_REVEALED.zip`.

## Blind/reveal separation

The blind engine reads only:

- `configs/blind_config.json`
- `data/public/constraints.json`
- `data/public/reveal_commitment_sha256.txt`

It does **not** read `private/`, SST constants, or the candidate identity. A SHA-256 commitment freezes the reveal payload before the blind verdict.

## Frozen v0.1.0 gates

- conventional-propagation Poisson observability at the Carpet event;
- non-birefringent linear \(n=1\) interval consistency;
- birefringent linear \(n=1\) interval consistency;
- quadratic \(n=2\) interval consistency;
- robustness to the quoted Carpet upper-bound uncertainty;
- reveal commitment integrity;
- naive \(O(1)\,k r_c\) and \(O(1)(k r_c)^2\) UV mappings;
- direct \(\hbar\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}/r_c=E_{\rm LIV}\) mapping;
- independent SST photon-dispersion closure (OPEN until supplied independently).

See `docs/SCIENTIFIC_SCOPE.md` for the exact scope and non-claims.
