# Maxwell-SST v0.2 workflow results

Preset: `basic`  
Backend: `python`  
Curves: 2  
Interaction probes: 2

## Interpretation guard

v0.2 generates geometry candidates and regularized Biot-Savart coupling PROXIES. It does not derive physical mode energies, true gaps, thermodynamic contributions, or spectroscopic shifts. Those remain inputs to the v0.1-compatible falsifier skeleton from a declared physical solver/experiment.

- `geometry_metrics.csv`: resolved centerline geometry and writhe convergence diagnostic.
- `mode_candidates.csv`: rigid-projected normal Fourier deformation basis; **not yet physical eigenmodes**.
- `interaction_coupling_proxy.csv`: instantaneous regularized Biot-Savart response of a displaced second curve.
- `v01_physical_campaign_skeleton/`: blank physical-energy/gap tables for the strict falsifier layer.
