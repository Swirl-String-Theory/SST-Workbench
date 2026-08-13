# Canon v0.8.35 patch notes

`SST_CANON-v0.8.35-Maxwell-reciprocal-stress.diff` is a review patch against the supplied v0.8.35 main Canon and research-track companion. It does **not** bump the Canon version by itself.

The patch makes three changes:

1. Adds a short main-Canon research-track interface guard after the existing factor-nine contact-channel guard.
2. Adds `Maxwell--SST reciprocal stress complex and blind equilibrium-rank gate` before the existing colored contact-channel rank test. The new subsection defines local force closure, ordinary rank/nullities, the positive self-stress cone, singular-scale conditioning, the SST force--area normalization guard, strict-reciprocity redundancy handling, and a blind relaxed-knot/contact protocol.
3. Adds the 1864 Maxwell `\bibitem` with DOI `10.1080/14786446408643663`.

The force--area equation deliberately uses the v0.8.35 Canon notation `\rhohorn` because the existing identity in that version is

\[
F_{\rm swirl}^{\max}=\pi r_c^2\rho_{\rm horn}^{\rm eff}(v_{\!\boldsymbol{\circlearrowleft}}^\ast)^2.
\]

No dimensionless Ridgerunner/length-minimization multiplier is promoted to a force in newtons without an explicit physical normalization.

The generated diff was tested with `git apply --check` against byte copies of the supplied two v0.8.35 source files.
