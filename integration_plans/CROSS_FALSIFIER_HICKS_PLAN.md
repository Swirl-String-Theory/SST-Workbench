# Hicks/Hill analytical foundation and historical falsifier upgrades

Audit date: 2026-10-09. Scientific basis: Hill (1894), Hicks (1899), Moffatt (1969), and the user-provided `Hicks_on_Vortex_Motion.pdf`. Previous Workbench versions checked via the connected Drive source: A046 0.2.0, A054 0.5.1, A055 0.4.1, A057 0.2.0, A050 0.4.0, A060 0.1.0, A061 0.2.0, A023 0.5.0.

## Non-migration policy (requested)

1. Current v1.0.7 is CANONICAL_FROZEN for **new** scientific instances; do not patch that framework in place.
2. Historical falsifiers **remain pinned to their existing framework**. A new scientific hypothesis produces a *new instance version* on the same legacy framework if it still executes reliably; an exception requires an explicit infrastructure justification.
3. A PDF can be produced with `04_tools/D_proof/SST_Falsifier_Report_Generator/report_generator.py`, without modifying the old run, protocol or source output tree. PDF is labelled external.
4. The standalone A063 candidate is a **prototype**: scientific H0-H6/H9-H10 analytical controls can PASS, whereas topology-tube stability, independent native certification and a real v1.0.7 FREEZE are **UNRESOLVED**. Do not cite this as v1.0.7 certification.
5. `A063` must be checked against the authoritative catalog/registry before making that ID permanent. Drive filename search alone cannot reserve the number.

## Tranche 1 - analytical controls (delivered as working prototype)

Source: `01_research/A_falsifiers/A063_Hicks_Hill_Euler_Separatrix_Falsifier/A063-v0.1.1` (new release; v0.1.0 remains unchanged).

- Exact `J(lambda r/a)` Hicks spherical streamfunction and matched exterior dipole.
- Euler, incompressibility, Beltrami, pressure, material separatrix and zero-translating family.
- A046 pressure-Poisson and strain bridge `hicks_hill/bridges.py`.
- A057 finite laboratory-frame volume-energy integration, including analytic exterior dipole energy.
- Numerical, **noncertified** winding return values on a small set of invariant tori.
- Gate-record JSON and post-hoc external PDF report; no v1.0.7 manifest signatures are forged.

## Tranche 2 - promote analytic reference to official framework, but only for the new instance

1. Check catalog occupancy; register A063 if free. Do not modify the existing A062 family.
2. Generate *a new official v1.0.7 instance* in the Workbench with `tools/new_falsifier.py` (do not call this prototype a frozen instance).
3. Port current science kernel unchanged and add protocol bundle, independent C++ FP64 verifier, framework backend and reveal controls; certify source commitment and backend provenance.
4. Extend the spatial/temporal error ladders and interval-certify the winding range, including 2/3 and 3/2 trefoil winding candidates.
5. Separate vortex-line topology from a **finite-core, material** vortex tube; any finite-core stability claim must be independently certified.

## Tranche 3 - surgical historical upgrades

- **A046 v0.3.0**: accept exact Hill/Hicks 3D Euler/pressure controls, correct rotating-frame objectivity and non-Beltrami null.
- **A054 v0.6.0**: demonstrate its constrained state-selection strategy on exact known stationary flows before promoting selected PKLSA geometries; do not confuse pressure/Euler stationarity with Hessian positivity.
- **A057 v0.3.0**: compare globally finite kinetic energy with regularized filament Hamiltonian at matched volume/circulation/helicity and regularization, using only frozen E013 carriers.
- **A055 v0.5.0**: certify attainable winding intervals and finite-core topology distinction; preserve v0.4.1 G8 FAIL and do not repackage as a success.
- **A050/A060/A061**: lower-priority phase/coherence/clock analytical nulls; SST-28 remains falsified historical comparator only.

## E013 provenance firewall

Current source authority: E010 geometry parser -> E011 STATIC_READY provider anchors -> optional E012 mode extractor -> E013 shared frozen `CROSS_CARRIER_MANIFEST.json` -> member falsifiers. Only independently sourced E011 anchors can close E013 cross-provider gates. Hicks is `synthetic_control`; never replace unavailable `L4a1` or `L6a4` source anchors with Hicks geometry. Historical A054 and A057 outputs cannot be used as fresh E013 evidence. A062 is already occupied; use A063 for this Hicks/Hill candidate, subject to authoritative registry confirmation.

## Scientific questions requiring real 3D numerical solvers

- An arbitrary PKLSA knotted core embedded within a deformable Hicks-like separatrix is not constructed in this v0.1.1 analytical reference.
- The external kinetic-energy integral is computed in the inertial laboratory frame because the co-translating exterior far field is uniform; directly integrating un-subtracted co-moving velocity globally diverges.
- Exact stationary Euler solutions do not imply perturbative or nonlinear stability.
- A closed vortex line is not equivalent to an independently isolated, finite-thickness knotted vortex tube.
- The winding ratio depends on which cycle is called poloidal/azimuthal. Both 2/3 and 3/2 trefoil conventions must be handled and invariance under orientation changes verified.

## Acceptance and output rules

Every future version should retain original gate identifiers/thresholds only as historical provenance, register new hypotheses before running, preserve failure-continuation diagnostics, and leave infrastructure/provenance gates fail-closed. Output each new member's external PDF and optional LaTeX report *outside* the original sealed output tree. For the new official A063 instance, generate PDF with its own 1.0.7 report pipeline instead of mistaking the stand-alone report for framework evidence.
