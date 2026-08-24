# Maxwell-SST v0.3 workflow results

Preset: `basic`  
Backend: `cpp`  
Curves: 2  
Interaction probes: 2

## Interpretation guard

v0.3 generates geometry candidates and regularized Biot-Savart coupling PROXIES. It does not derive physical mode energies, true gaps, thermodynamic contributions, or spectroscopic shifts. Those remain inputs to the physical falsifier skeleton from a declared physical solver/experiment.

- `geometry_metrics.csv`: resolved centerline geometry and writhe convergence diagnostic.
- `mode_candidates.csv`: rigid-projected normal Fourier deformation basis; **not yet physical eigenmodes**.
- `interaction_coupling_proxy.csv`: instantaneous regularized Biot-Savart response of a displaced second curve.
- `physical_campaign_skeleton/`: preregistered physical-energy/gap/state-count/entropy-force tables for the strict falsifier layer.
