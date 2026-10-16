# A063 candidate: Hicks/Hill Euler Separatrix, analytical prototype v0.1.0

**Status:** Work started; this is an independent **analytical prototype**, **NOT YET** a v1.0.7 `CANONICAL_FROZEN` scientific instance, and **NOT** a certified SST/deuteron/electron/mass claim. A063 replaces the occupied A062 ID at the user's request; authoritative registry admission is still to be verified. No SST constants or target particle labels are used in the blind controls.

The reproducible model is Hill's no-swirl vortex and the axisymmetric Hicks family in co-translating cylindrical coordinates, with meridional Stokes streamfunction and azimuthal swirl. Pressure is derived from Bernoulli/Euler, rather than independently imposed. Outside the sphere we match a translating dipole field with uniform far-field motion. The exterior far-field kinetic energy requires background subtraction when a volume energy is implemented in the future.

Within `hicks_hill/analytic.py`:

- `J(y) = sin(y)/y - cos(y)`
- `psi_inside(s,z)=A[J(lambda*r/a) - (r²/a²)J(lambda)]s²/r²`
- `u_s=-psi_z/s, u_z=psi_s/s, u_phi=(lambda/a)*psi/s`
- first `lambda1` roots: `J(lambda)=0` (Beltrami `curl u = lambda/a u`)
- first `lambda2` roots: `3J(lambda)-lambda sin lambda = 0` (zero aggregate translation)
- zero-swirl Hill limit implemented separately to avoid `lambda->0` cancellation.

Run:

```cmd
python -m pip install numpy scipy pytest reportlab
run_all.cmd SELFTEST
run_all.cmd BASIC
```

On Linux/macOS: `python -m pytest tests -q && python run_hicks.py`, then run the external PDF generator separately.

### Readiness and evidence classes

- H0-H6: synthetic/analytical Python-FP64 controls only (not full field, timestep, or backend certification)
- H7: sampled winding return mapping; finite-core knot classification and stability UNRESOLVED
- H8: official framework v1.0.7 and native C++ FP64 certification UNRESOLVED

Next: (1) instantiate a proper new v1.0.7 instance using `tools/new_falsifier.py` and port this science package as a source library; (2) preregister FULL/CERTIFY gates independently; (3) verify E013 carrier contracts and add A046/A054 reference adapters. Historical instances must remain unchanged.

### Falsifier-family upgrade guidance

See `../../../../integration_plans/` in the release bundle for individually scoped change protocols for A046/A054/A055/A057/A050/A060/A061. The implementation of these historical suites has deliberately not been altered by this prototype.
