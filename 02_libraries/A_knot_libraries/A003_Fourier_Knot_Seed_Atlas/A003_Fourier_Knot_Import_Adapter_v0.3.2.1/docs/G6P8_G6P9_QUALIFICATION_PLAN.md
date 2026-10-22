# G6P8 / G6P9 closure plan

## G6P8: versioned E010 registry change, NOT a patched frozen E010 v0.3.1

Source-dependent `G6P8_E010_PROPOSED_SOURCE_CONTRACT.json` and
`G6P8_E010_CARRIER_INDEX_PROPOSAL.json` are created from the live E010
production contract and the exact frozen 8 A003 source XYZ byte hashes.
This artifact is **not an E010 code update**. Review and incorporate the
source index only in a new E010 registry release, with a new manifest,
versioned registration API or catalog index, source role and independence group,
`doctor`/resolve readback and an independent validation/freeze record.
Do not overwrite `E010-v0.3.1/configs` in-place. An edited v0.3.1 config
invalidates the original E010 package manifest and its freeze claims.

## G6P9: scientifically meaningful Euler/finite-core closure

The C005 source's Rosenhead-midpoint kernel defines a regularized circulation
field and filament velocity, but it does not supply full volumetric vorticity,
pressure Poisson solve, or Euler PDE momentum residual. An adequate future
source-native solver contract must define a domain/boundary conditions, a
physically meaningful finite-core vorticity profile, its circulation and units,
a divergence-free 3-D velocity, projection/pressure boundary treatment, coupled
time integration with convergence to fixed physical time, a PDE residual
measured independently, a known analytic verification case, and adversarial
3-D topology/reconnection cases.

Do not infer full inviscid Euler from RK4 convergence of the centerline ODE.
The P9 gate cannot PASS while these materials are unavailable.
