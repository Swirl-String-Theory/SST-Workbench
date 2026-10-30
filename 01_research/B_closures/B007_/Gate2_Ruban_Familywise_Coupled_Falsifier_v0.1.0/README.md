# Gate2 Ruban Familywise Coupled Falsifier v0.1.0

**One four-stage falsifier, run in strict order. DEVELOPMENT; no Euler relative equilibrium yet.**

## Scientific question
Can a finite-core trefoil and initially parallel, fully coupled background vortex tubes form a common relative equilibrium in 3D incompressible Euler flow? The four stages are a *single pipeline*; reduced filament seed screening is a candidate-generation tool, NOT a physical proof.

## Source provenance
- Bundled, unchanged `data/E010_Ruban_Torus_Dynamics_Family_v0.3.5-outputs.zip`. `FAMILY_INDEX.json` gives 12 parametrized torus-knot embeddings, seven B0 values each (84 seeds), including a perturbed counterpart for each. Per-seed SHA-256 checks are mandatory.
- E010's historical 672 scenarios were declared but not executed. This program computes a **new** independent screening ledger; it does not retrofit the old E010 results.
- Vendored `src/reference_euler.py` is inherited from Gate2 Coupled Trefoil Grid v0.1.0, for provenance, not a claim of independent implementation parity.

## Four gates in one command
G1: Validate all 84 source seed geometries and hashes; approximate curvature and nonlocal distances. The distance proxy is not a proven reach or isotopy certificate.

G2: Evaluate all 84 nominal + 84 deterministic perturbed seeds with a regularized midpoint-segment filament model at `Lambda=4`, with a very short two-evaluation Heun step. This is an inexpensive ranking proxy; **not 3D Euler dynamics**. `--extended` sweeps all four Lambdas, 672 nominal+perturbed cases.

G3: Select one provisional winner *within each of the twelve embedding families* based on G2 proxy. Re-evaluate those twelve winners at 128, 256, and 512 filament vertices (G2 used 192). Keep `T_2_3` and `T_3_2` distinct though both are topological trefoils; avoid claiming independent physical source providers.

G4: Select the best B0 from **each trefoil embedding**. Construct Gaussian-mollified periodic closed polygon vorticity and truly coupled Fourier Euler dynamics with one or three living vertical-centre-section racetrack return loops. Also compute independent free-knot/background controls, a one-step full-vector-vorticity RK4 update, and a fixed translation speed `U` 20^3 -> 24^3 spatial holdout. **Default stage 4 runs four cases**. Extended adds exploratory 3x3 and 5x5 networks, but the present simple racetrack return topology may cross or closely approach other returns; this is recorded as INVALID_GEOMETRY_OVERLAP_RISK and blocks physical interpretation. Continuous rotation about z is NOT a symmetry of the finite cubic torus; Omega is forbidden in this gate.

Every gate emits its own `G*_GATE.json`; `G0_G4_ASSESSMENT.json` never reports `G2_PASS` without continuum zero-residual certification.

## Windows install / run
```
py -m pip install -r requirements.txt
run_all.cmd
```
Extended 4-Lambda and background grid campaign:
```
run_all_extended.cmd
```
On Linux/macOS: `./run_all.sh` or `./run_all.sh --extended`.

Outputs are written to `./Gate2_Ruban_Familywise_Coupled_Falsifier_v0.1.0-outputs/` and packed as `../Gate2_Ruban_Familywise_Coupled_Falsifier_v0.1.0_outputs.zip` plus `.sha256`. A scientific PDF report is generated after the gates.

## Absolute limits
1. G2 is a filament induction *proxy*, not validated fully coupled finite-core Euler dynamics.
2. G4 is a periodically Gaussian-mollified vortex field; not compactly supported; spectral cutoff alters the field.
3. G4 is a forward time pilot and a relative-residual diagnostic, **not a full-field optimizer**.
4. Fixed U holdout samples two modest resolutions; this **cannot** certify a continuum zero residual. Independent operator/backend parity not established.
5. Exact reach, embedded material topology and helicity/circulation preservation under spectral stepping are not established; periodic returns and boundary images influence the field.
6. The user should not interpret `0.2` B2000 as increased grid resolution: B is the geometric minor/major torus radius ratio.
7. Config records are dimensionless R0=1, GammaK=1. Core width is `exp(-Lambda)` in G2, but `sigma=0.12` in G4; different physical models; no unjustified equality.

## SST-Workbench catalog
A new official `A###` identifier cannot be chosen without examining the **current** `catalog_index.json` and `family_hierarchy.json`. The bundle intentionally uses an unassigned catalog ID, and includes `FAMILY.yaml`/`project.json` stubs for controlled registration. It does not overwrite E010 or any existing falsifier.

**Output preservation:** extended runs write to the `...-outputs/extended/` subdirectory rather than overwriting the default-stage data. Filter correction above 10% blocks numerical prequalification.

**Extended-network geometry warning:** the returned 3x3 and 5x5 loops are currently NOT qualified as disjoint Euler vortex tubes. They are executable numerical stress tests. The G4 preflight records sampled inter-component distances and denies physical promotion for a spacing below 2*sigma. A future nonintersecting closure construction is required.
