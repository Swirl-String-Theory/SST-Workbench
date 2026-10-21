# A044 Cosmic Gamma Transparency / Dispersion / Lorentz Emergence Falsifier v0.2.0

Upgrade of the existing SST-Workbench A044 falsifier against the **final published** Galanti & Roncadelli PRL analysis of GRB 221009A.

## Scientific purpose

The package deliberately separates two questions:

1. **Blind observational qualification:** what propagation-law classes can simultaneously survive the public GRB 221009A transparency, timing, polarization and lower-bound constraints?
2. **SST reveal:** does an **independently derived** SST photon/eigenmode dispersion law land inside one of those surviving classes without fitting SST constants to the GRB target?

The package does **not** infer an SST dispersion law from the GRB. If no independently derived candidate payload is supplied, the SST closure verdict remains `OPEN_NO_INDEPENDENT_CANDIDATE`.

## Main v0.2.0 additions

- final PRL 2026 source snapshot;
- conventional-propagation and ALP-only Poisson observability gates;
- analytic subluminal pair-production threshold-shift diagnostic;
- cosmological time-of-flight inversion diagnostic using the observed Carpet/LHAASO time window;
- published Ofengeim--Piran nonlinear timing-scale compatibility check;
- arbitrary candidate `\delta(E)=1-v_g(E)/c` interface with log-slope extraction of an effective dispersion order;
- blind/reveal separation with SHA-256 reveal commitment;
- Python reference implementation plus optional C++17/pybind11 kernels.

## One-click Windows run

```bat
run_all.cmd
```

This creates/updates `.venv`, installs dependencies, attempts the native build, runs tests, executes the blind campaign, and packages outputs to:

```text
./SST_Cosmic_Gamma_Transparency_Dispersion_Lorentz_Emergence_Falsifier_v0.2.0-outputs/
../SST_Cosmic_Gamma_Transparency_Dispersion_Lorentz_Emergence_Falsifier_v0.2.0-outputs_BLIND.zip
```

A reveal run is only performed when `private/candidate.json` exists and its SHA-256 matches `data/public/reveal_commitment_sha256.txt`.

## Candidate format

Copy `private/candidate_template.json` to `private/candidate.json` **only after the candidate law has been derived independently**. Supply samples such as

```json
{
  "candidate_id": "SST_PHOTON_EIGENMODE_<frozen-id>",
  "provenance": "independent derivation artifact / commit / hash",
  "birefringent": false,
  "samples": [
    {"energy_TeV": 10.0, "delta_v_over_c": 1.0e-18},
    {"energy_TeV": 100.0, "delta_v_over_c": 1.0e-16},
    {"energy_TeV": 300.0, "delta_v_over_c": 9.0e-16}
  ]
}
```

Do not place SST constants in `configs/` or `data/public/`.

## Primary frozen decision logic

The final SST propagation closure can only pass if an independent candidate:

- is subluminal over the target band;
- has a stable effective order compatible with the tested phenomenological family;
- maps to a scale consistent with the frozen blind transparency window;
- does not invoke the excluded generic birefringent linear class;
- is not in conflict with the conditional timing diagnostic;
- preserves the reveal commitment and blind-output leakage audit.

See `docs/SCIENTIFIC_SCOPE.md` and `docs/EQUATIONS.md`.
