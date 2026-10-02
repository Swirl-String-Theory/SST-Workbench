# Roadmap v0.3.0

1. Run the signed 48-member PKLSA trefoil BASIC screen and freeze the blind ledger.
2. Promote only preregistered suspicious geometries to N=32/48/64 plus explicit dt-halving replays; never promote on revealed source parameters.
3. Add transported deformation-gradient and pressure-Hessian diagnostics, including numerical checks of `F_t = M F` and `F_tt = -H F` along selected trajectories.
4. Add the theorem-inspired transported phase/amplitude packet diagnostic without tuning against SST targets.
5. Add checkpoint/resume and CFL fail-closed guards for the expensive certification branch.
6. Add non-PKLSA external trefoil controls (Gilbert/Fremlin, KnotPlot, Ridgerunner/ideal) through the same canonical centerline adapter, with source-family stratification.
7. Emit an A038-consumable P0 regularity certificate/rejection record.
