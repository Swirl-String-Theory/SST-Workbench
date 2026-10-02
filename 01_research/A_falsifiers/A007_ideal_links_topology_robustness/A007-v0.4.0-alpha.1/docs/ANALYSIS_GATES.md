
# Analysis gates — v0.2.1

## G0–G3: source, Fourier geometry and topology

As in v0.2.0, with analytic Fourier derivatives, Gauss-linking integer lock and native/Python parity.

## G4: refined curvature

Sampled local maxima seed bounded optimization of the exact truncated Fourier curvature. Both
sampled and refined maxima are retained so under-resolution is visible.

## G5: contact network

- symmetric mutual-nearest contact sampling;
- nonlocal self-contact edges;
- iterative union-find (no recursion-depth failure for continuous contacts);
- clustered contact patches;
- augmented endpoint graph containing contact jumps and centerline arcs.

## G6: directed contact-map cycles

A state jumps across a contact patch and then advances, with fixed orientation, to the next contact
endpoint on the reached component. Functional-graph cycles are reported for both orientations.
This is a discrete contact-map orbit diagnostic, not yet a specular billiard proof.

## G7: circulation sectors and fixed-core comparison

All `2^m` circulation assignments are retained. Cross-link ranking is performed at the preregistered
`comparison_epsilon_D`, default `0.1`. The minimum over epsilon is demoted to a smoothing diagnostic.
A linear fit in epsilon-squared provides an exploratory epsilon-to-zero intercept when at least three
core values are available.

## G8: Ridgerunner bridge

OOGL VECT export supplies an independent re-optimization/strut audit without changing the baseline
Fourier object. Ridgerunner remains optional and external.
