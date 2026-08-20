# Preregistration

The scientific preregistration was frozen in v0.1.0 and is unchanged by the v0.1.1 compiler-only hotfix. The primary source claim is directional:

> Matched Fremlin `.fseries` seeds have lower dynamical-departure metrics than matched ideal seeds under the same VortexLab-style inviscid filament model.

Primary metrics and tie margin are stored in each `config/preset_*.json` before the blind run.

Per pair, take the median of anonymous A/B log-ratios across the declared primary metrics. A pair is a tie inside the preregistered multiplicative margin.

After reveal, source-level support requires both:

1. one-sided exact sign-test `p <= 0.05` among non-tied matched pairs;
2. median source effect at least 10% in the declared direction.

The torus subset is reported separately with the same `alpha`; low sample size is not repaired by relaxing the threshold.

Any change to metrics, core ratio/model, tie margin, alpha, minimum effect, topology set or numerical tolerance after inspecting blind outputs constitutes a new campaign/version.
