# Preregistration — SST Threaded-Hole Substrate v0.2.1

The following claims are independent.

- **H-SC:** active threading improves carrier self-confinement.
- **H-F:** active circulation focuses the threaded substrate relative to passive zero-circulation tracers.
- **H-P:** active threading makes center-minus-shell pressure more negative.
- **H-B:** the symmetric pressure law has negative leading even quadratic coefficient.
- **H-Q:** the induced pressure source has a positive, non-negligible monopole with convergent magnitude.
- **H-G:** the blind free exponent is Newton-like and convergent in free space.
- **H-GEAR:** active triple-gear threading improves a marker-invariant geometric phase-lock proxy; no gear ratio is supplied.

## Geometry gates

- acceptable source provenance;
- Gauss-link estimate >= 0.75;
- hole clearance > `2.4 a`;
- complete finite-segment initial gap > `2.5 a`.

## Contact semantics

Zero-circulation ghost components are excluded from contact and CFL physics. Contact-stopped trajectories never enter ordinary AUC/RPO/Floquet scoring.

## Independent experimental unit

Repeated beta/thread/pitch settings of one carrier are clustered to one carrier-level vote before exact sign testing.

## Free-space gravity closure

A combined gravity-survival verdict requires simultaneously:

1. carrier-clustered negative induced center-minus-shell pressure;
2. positive induced source monopole `Q_delta` above `gravity_min_monopole_fraction_abs`;
3. induced monopole relative span <= `pressure_ladder_monopole_rel_span_tolerance`;
4. blind free exponent with adequate profile R2 and post-reveal `|nu-1|` tolerance;
5. exponent span <= `pressure_ladder_nu_span_tolerance`.

Failure of any item prevents a gravity-closure pass.

## Fixed confirmatory stability pairs

The fresh confirmatory campaign contains exactly:

- `T(2,3)`: `beta=-1.5`, with `beta=+1.5` sign control, `N_B=1`, one helix turn;
- `5_2`: `beta=-1.0`, with `beta=+1.0` sign control, `N_B=1`, zero helix turns.

These settings are fixed before new dynamics are evaluated.

## Discovery scan

The long discovery scan uses

```text
beta = -3,-2.5,-2,-1.5,-1,-0.5,-0.25,+0.25,+0.5,+1,+1.5,+2,+2.5,+3
N_threads = 1,3
helix_turns = 0,1,3
```

Selected minima remain discovery-only.
