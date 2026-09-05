# Triple gear / three-unknot-link note — v0.2.0

`TRIPLE_GEAR_T3_3` is an analytic `T(3,3)` three-component link used as a topology-first proxy for the user's three-unknot gear-like configuration. Each carrier component is individually an unknot; the components are mutually linked and share a central passage for the threaded substrate.

v0.2 adds a geometric phase observable. After removing global carrier translation/rotation, cyclic phase shifts of each embedded component are tracked. A corresponding phase is extracted for the closed central thread geometry. The code discovers the best low-order rational relation between mean carrier and thread phase rates.

This must not be overinterpreted:

- there are no material teeth in the filament model;
- arclength remeshing means marker labels are gauge, not material particles;
- the phase observable tracks embedded geometric pattern rotation/winding;
- no previously observed mechanical ratio is provided to the blind solver.

A useful result would be a reproducible active-vs-null reduction of phase-lock residual followed by confirmation of the discovered ratio in a fresh fixed-target campaign.
