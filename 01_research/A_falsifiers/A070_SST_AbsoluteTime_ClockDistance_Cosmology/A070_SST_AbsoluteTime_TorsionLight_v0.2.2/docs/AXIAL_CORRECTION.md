# Axial physical geometry - correction to v0.2.1

The SST light **hypothesis** requires torsional pulses to travel parallel to the straight cylindrical vortex-filament axis. Define theta = angle(k, vortex_axis), so physically theta = 0 deg (or 180 deg for the opposite direction), NOT 90 deg. The wavevector is normal to a planar endcap (90 deg to its plane) and tangent to the curved lateral surface. Azimuthal twist is transverse *motion*, not transverse *propagation*.

## Critical analytic negative control
For unbounded uniformly rotating incompressible Euler background,
    omega_I = +/-2 Omega kz / sqrt(kx^2+ky^2+kz^2),
    v_g = +/-2 Omega (ez/|k|-kz kvec/|k|^3).
At kx=ky=0 and kz != 0, omega_I = +/-2 Omega but v_g = 0: a phase oscillation alone is not a transport of a packet. The v0.2.0 theta=50 group speed is no longer treated as geometrically relevant. In contrast, at theta=90 deg, omega=0 but v_g along the rotation axis is finite in the ideal plane-wave limit; this degenerate endpoint must not be misconstrued as photon light propagation.

For a pure azimuthal disturbance in an otherwise QUIESCENT Euler fluid d_t delta_u_phi=0. A constant axial background U_z gives (d_t+U_z d_z) delta_u_phi=0, which is only passive advection. For finite swirling-core background these equations are not the complete linearized system: pressure and other velocity components couple and require source-native 3D Euler solution.

## Selection and scientific blindness
- v0.2.1 frozen 7-angle, five-k masked synthetic outputs and their exact old science contract stay immutable and are retained ONLY as diagnostic reference; they are not physical torsional-photon candidates.
- v0.2.2 introduces a separate **axial-only** masked synthetic control archive and independent hash lock. Wave numbers are [1,2,3,4] dimensionless. No scale set by c or any canonical SST speed is used.
- The synthetic axial cases test: static, passive axial advection, externally prescribed traveling phase, and mixed anomaly. A synthetic propagating phase is **not** a solved Euler eigenmode.
- Physical acceptance is **not run** until a qualified finite-core PKLSA source provides a perturbation with longitudinal wavepacket energy transport relative to flow and a convergent finite-core eigenfrequency branch. Test both +/-z and separate Kelvin bending, bulk inertial modes, and advected markers. If vg,z - U_z -> 0 on refinement, reject intrinsic axial propagation.
- Absolute SST time t is the background evolution; local tau_i and operational ruler ell_i are independently measured and not fitted to c during blindness.

## Version/data custody
Never modify v0.2.1 archives, existing frozen SHA, masked inputs, or REVEAL truth. Additional v0.2.2 axial truth remains only in the separately sealed new REVEAL ZIP. This is NOT an instance generated or certified via v1.0.7 framework.
