# Three-domain blind protocol (A065 v0.3.0)

## Separation and commitments

1. `D01_EULER`: independent `SHA256(dataset content)` and a self-hashed manifest in `seals/D01_EULER.seal.json`.
2. `D02_CLOCK_LINK`: analogous independent D02 seal.
3. `D03_TWO_SURFACE`: analogous independent D03 seal; precommits pairings, distances and temperatures **without force data**.

`seals/GLOBAL_COMMITMENT.json` binds all three independent seals plus the SHA-256 commitment to `private_reveal/targets.json`. The target file does **not** exist in the public archive. It is supplied only by a separate private escrow archive and is not read during BLIND. A physical reveal remains blocked by G2 FAIL and G3 NOT_RUN. REVEAL checks dataset seals, global commitment, the private target hash, blind result hashes and physical gate eligibility. There is no allowed reveal path in this v0.3.0 campaign.

Changing any dataset or comparator after the commitments have been frozen causes VERIFY and/or REVEAL to fail. Deliberately rewriting all four commitment files can still circumvent local SHA-256: use an independent externally published root ZIP SHA for author authentication. SHA-256 does not encrypt information and source inspection can reveal comparator design. The protocol is computational target-blind, not perfect informational blinding.

## Gate status semantics

`PASS` is permitted only for preregistered **synthetic implementation controls**, never `PHYSICAL_SST_CERTIFIED`. A failed individual gate does not block the remaining gates, but any unverified or modified seal aborts the run before results. Invalid provenance aborts certification (not mathematical exploration).

## Dataset/gate contract

- D01 G01: max |div u| <1e-12
- D01 G02: max |Poisson RHS - Laplacian p| <1e-12
- D01 G03: omega=0 potential flow while strain >0
- D01 G04: nonuniform clock diagnostic for irrotational control
- D02 G01: gauge invariant phase (<1e-12)
- D02 G02: direct derivative vs covariant phase rate (<1e-12)
- D02 G03: two-path holonomy (<1e-12)
- D02 G04: nonnegative imaginary-branch susceptibility
- D02 G05: positive effective toy sheet stiffness
- D02 G06: exactly decoupled reference sheet
- D03 G01: |P_stress-P_derivative|/|P_stress| <= 0.015
- D03 G02: zero free energy/force when one sheet is removed
- D03 G03: toy interacting sheets have finite signed pressure (diagnostic, not a match to actual Casimir data)

## Non-negotiable physical gates absent from this pilot

- D01 G07: RK4 time-step halving PASS. D01 G08: 75/150 spatial resolution fails its frozen 5% tolerance. Fremlin A006 raw source missing; provider registration is not validation.

- Real 3D resolved time-dependent Euler/PKLSA data with independently computed velocity/pressure and physically meaningful boundaries.
- Independent provider replication (two upstream independence groups with validated hashes).
- First-principles matter-link clock coupling and measured-material reflection tensor.
- Dynamic fluctuation distribution/quantum occupation derived without target force.
- Physical force-stress agreement from independent measurement or solver channels.
- Environmental/electrostatic/magnetic/thermal/confound controls.

`run_all.cmd CERTIFY` intentionally fails closed because spatial refinement fails and physical gates remain open. The **17** analytic/simulation gates yield **16 PASS, 1 FAIL**. The physical Casimir claim remains unqualified.
