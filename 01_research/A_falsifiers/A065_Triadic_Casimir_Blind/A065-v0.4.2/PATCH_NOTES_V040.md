# A065 v0.4.0 — finite-resolution 3D Euler/volume campaign

* Canonical SST Falsifier Framework v1.0.10 kept byte-for-byte frozen and externally linked.
* Genuine A003 v0.2.3 imports required; original 384-record A003-v0.1.2 atlas stays external.
* The same two source hashes, XYZ points (N1200, stride 6), Gaussian a=0.55,
  circulation=1, box L=12 and time T=0.02 apply on all 48³/64³/96³ grids.
* G37–G42 are additive; older sealed D01–D03, prior failures and G36 are unmodified.
* Independent numerical time evolution is 3D periodic inviscid Euler, rotational RK4 with 2/3 de-aliasing.
  It starts from the same **assumed Gaussian filament field** and is **NOT independent PKLSA physical initialization**.
* G41 MUST remain UNRESOLVED without genuinely independent source-native 3D PKLSA data
  and physically independent pressure measurements/provider.
* GRID verification on the current container with no original A003 384 XYZ assets is NOT a
  genuine A003 volumetric validation. Use `run_all.cmd CAMPAIGN` on user's Windows instance.
* Report status, execution status and scientific authority are distinct under framework v1.0.10.
