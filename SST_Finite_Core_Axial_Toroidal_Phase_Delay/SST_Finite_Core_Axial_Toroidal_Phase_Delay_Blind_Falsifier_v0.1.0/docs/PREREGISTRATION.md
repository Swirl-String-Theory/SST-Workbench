# Blind preregistration

The scientific hypothesis is **not** “phase must equal pi”. No preferred loop phase is preregistered.

For every nuisance-parameter tuple, prepare constructs two anonymous candidates:

- one satisfies the measured closed-loop/Bishop holonomy quantization;
- one uses the same carrier, finite-core profile, axial flow, core radius and \((m,n)\), but a non-integer closure offset whose sign is randomized.

The blind runner has no carrier/family/condition labels and scores only numerical finite-core quantities. A SHA-256 seal is written before reveal.

### Primary thresholds

- finite-core mode valid fraction: preset-specific, normally >= 0.60;
- median group-delay vs wave-packet-return relative error <= 0.30;
- carrier-cluster exact sign test for closed-loop lower growth: one-sided p <= 0.05;
- carrier-cluster median closed/control growth ratio <= 0.90;
- leave-one-carrier-out circular phase-growth CV R^2 >= 0.15;
- grouped phase permutation p <= 0.05.

No individual favorable point can override a failed aggregate gate.
