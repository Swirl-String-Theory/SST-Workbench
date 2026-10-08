# Preregistration — A055 v0.4.0

Machine-authoritative protocol: `preregistration/FROZEN_PROTOCOL.json` after framework freeze.

Frozen thresholds:

- positive-frequency floor: `1e-7` relative to spectral radius;
- Kelvin-family fraction: `>=0.50`;
- dominant-harmonic participation: `>=0.50`;
- circulation-relative purity: `|xi|>=0.60`;
- oscillatory quality: `|Re(lambda)|/|Im(lambda)|<=1.0`;
- minimum eligible modes per sector: `3`;
- sector vote bias: `|B_s|>=0.50`;
- anonymous recurrence: same bias sign in at least `2` sectors;
- representation metamorphic absolute error: `<=1e-8`;
- sealed-spectrum assignment error: `<=1e-8`;
- C++/Python signed-power parity: relative L2 `<=1e-10`.

The resolution ladder and Jacobian finite-difference epsilon values are inherited without modification from the sealed A054 FULL config. No v0.3.1 effect size is used as a decision threshold.

The v0.3.1 result is explicitly discovery evidence. v0.4.0 does not claim independent confirmation because it reuses the same underlying A054 simulation family.
