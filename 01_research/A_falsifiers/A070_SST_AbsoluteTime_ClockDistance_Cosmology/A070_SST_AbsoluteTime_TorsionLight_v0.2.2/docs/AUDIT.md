# Audit - v0.2.0 vs v0.2.1

- v0.2.0: theta=50 deg chosen without physical motivation; Omega=v_swirl/r_c, k=1/r_c fixed; SI output group speed ~1.676e6 m/s was derived from fixed reference scales; not measured light propagation.
- v0.2.0 masking hid class IDs, but classifications and class count were directly anticipated in the public source, and datasets were synthetic.
- v0.2.1: freeze a uniform angular/k grid BEFORE inspection; the BLIND analysis knows candidate model classes but receives no masked-ID-to-class mapping, generator, SI calibration, c, r_c or v_swirl.
- v0.2.1 uses an analytic invariant check and test thresholds without selecting one favorable angle. Endpoints are degeneracies; guard against declaring zero frequency a propagating wave.
- A real independent scientific blind study requires source-native PKLSA/real observations, a separate dataset custodian and held-out providers. Those gates explicitly remain closed.
- Canonical source of prior package SHA256 in `preregistration/PRIOR_V020_SHA256.txt`.
