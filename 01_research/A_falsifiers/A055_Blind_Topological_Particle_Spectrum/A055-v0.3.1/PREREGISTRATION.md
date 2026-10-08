# Preregistration — A055 v0.3.1

The machine-authoritative preregistration is the framework-frozen bundle consisting of `science_contract.json`, `source_contract.json`, `gate_plan.json`, `blind_policy.json`, `falsifier.toml`, the nonced commitments and `report/FALSIFIER_REPORT.tex`.

Frozen numerical thresholds:

- temporal-frequency floor: `1e-7` relative to spectral radius;
- harmonic participation: `>= 0.50`;
- signed traveling purity: `|chi| >= 0.60`;
- oscillatory quality: `|Re(lambda)|/|Im(lambda)| <= 1.0`;
- opposite-direction pair frequency asymmetry: `<= 0.25`;
- anonymous robustness: pair present in at least `2` circulation sectors;
- sealed-spectrum recomputation assignment error: `<= 1e-8`;
- Python/C++ signed-power parity: relative L2 `<= 1e-10`.

The `0.25` frequency-asymmetry threshold and `1.0` oscillatory-quality bound are retained from the prior A055 methodology; the spatial-direction purity/participation thresholds are new and were chosen before v0.3.1 outcome inspection. `|chi|=0.60` means at least 80% of the signed-harmonic pair power lies in one spatial direction; `eta=0.50` requires the tested harmonic pair to contain at least half of the transverse mode power.

Semantic architecture/component labels and historical working hypotheses remain private until framework reveal verification.
