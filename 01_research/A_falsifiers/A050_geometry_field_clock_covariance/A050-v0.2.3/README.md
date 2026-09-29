# A050 — Geometry Field Clock Covariance — v0.2.3

**Local Basin / Perturbation-Sensitivity Map around G0002**

v0.2.3 is a frozen **post-confirmatory diagnostic** derived from the revealed v0.2.2 outcome. It does not rerun the full v0.2.2 falsifier and cannot alter its primary verdict (`MODAL_PERSISTENCE_NOT_REPRODUCED`).

The purpose is narrower: map whether the revealed G0002 m=3 transverse branch has a finite local perturbation basin.

## Primary run

Windows:

```bat
run_all.cmd
```

The run is resumable. Per-trajectory JSON files are stored in the output `trajectory_cache/` directory. Re-running `run_all.cmd` resumes missing trajectories without changing the frozen inputs.

By default the scientific run uses one Python worker for maximum reproducibility and to avoid nested numerical-library oversubscription. The runner is resumable; users may explicitly request more workers after validating their local environment. Override manually with, for example:

```bat
python -m sst_gfcc_blind.cli --config config/default.json --out SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.2.3-outputs --workers 4
```

## Scientific boundary

A `FINITE_RADIUS_M3_BASIN_SUPPORTED` result would show robustness of this generated dimensionless G0002 branch within the preregistered local perturbation map. It would **not** validate SST, physical Kelvin-wave speed, real-knot dynamics, or reverse the v0.2.2 confirmatory failure. The next independent geometry step remains a separately frozen PKLSA/ideal-knot campaign.
