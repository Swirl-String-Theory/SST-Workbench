# Triple gear / three-unknot-link note — v0.2.1

`TRIPLE_GEAR_T3_3` is an analytic `T(3,3)` proxy with three individually unknotted components. It is used only as a vortex-coupling geometry; no literal mechanical teeth are assumed.

v0.2.1 removes the old cyclic-marker phase estimator because uniform arclength redistribution destroys material-marker phase. The new diagnostic is geometric:

- each carrier ring gets a toroidal/poloidal embedded phase from `(rho-<rho>) + i z` relative to toroidal azimuth;
- each central thread gets a helix phase from azimuth versus axial position on its low-radius central pass;
- global carrier rigid translation/rotation is removed first;
- small rational `p:q` relations are searched only after phase rates are measured; no expected gear ratio enters blind scoring.

A discovered rational relation is exploratory unless it is fixed and reproduced in a new sealed campaign.
