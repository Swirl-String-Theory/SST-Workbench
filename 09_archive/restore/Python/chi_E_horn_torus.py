#!/usr/bin/env python3
"""
Horn-torus loop-energy test for SST fluid-primitive program (research track).
Computes chi_E(lambda) = E_loop/(rho_sat * Gamma0^2 * a0) from pure hydrodynamics.
Inputs: NONE of {m_e, hbar, alpha, r_c}. Only nondimensional lambda = R/a0.
Step-1 relation used to eliminate P_vac:  P_vac = rho Gamma0^2/(8 pi^2 a0^2).

Layer A: thin-ring asymptotic (hollow core, C=2)  -- diagnostic only
Layer B: finite-core cutoff Biot-Savart double integral -- leading
Kernel:  |x-x'|^2 -> |x-x'|^2 + mu*a0^2   (Rosenhead-Moore; mu=1 baseline)
"""
import numpy as np

TARGET = 1.0/(2.0*np.pi)   # canonical mass normalization in THIS nondimensionalization
                           # m_e c^2 = rho_core Gamma0^2 r_c /(2 pi)  =>  chi_target = 1/(2 pi)

def I_kernel(lam, mu=1.0, N=200001):
    """I(lam) = int_0^{2pi} cos(u) / sqrt(4 sin^2(u/2) + mu/lam^2) du  (trapezoid, periodic)"""
    u = np.linspace(0.0, 2.0*np.pi, N)
    f = np.cos(u)/np.sqrt(4.0*np.sin(u/2.0)**2 + mu/lam**2)
    return np.trapezoid(f, u)

def chi_kin_B(lam, mu=1.0, N=200001):
    return lam*I_kernel(lam, mu, N)/4.0

def chi_cav(lam):
    return lam/4.0            # P_vac * 2 pi^2 R a0^2 in units rho Gamma0^2 a0

def chi_thin(lam):            # Layer A, hollow-core constant C=2
    return 0.5*lam*(np.log(8.0*lam) - 2.0) + chi_cav(lam)

print("=== convergence test, Layer B at lambda=1, mu=1 ===")
for N in (2001, 20001, 200001, 2000001):
    print(f"N={N:8d}  chi_kin(1)={chi_kin_B(1.0,1.0,N):.10f}")

print("\n=== asymptotic matching: extract C_eff = ln(8 lam) - 2 chi_kin/lam ===")
for lam in (10.0, 100.0, 1000.0):
    C = np.log(8*lam) - 2*chi_kin_B(lam)/lam
    print(f"lam={lam:7.1f}  C_eff={C:.6f}   (hollow-core expects 2)")

print("\n=== chi_E(lambda) scan, mu=1 ===")
print(" lam    chi_kin(B)   chi_cav   chi_E(B)   chi_E(thin A)")
for lam in (1.0, 1.25, 1.5, 2.0, 3.0, 5.0, 10.0):
    ck = chi_kin_B(lam); cc = chi_cav(lam)
    print(f"{lam:5.2f}  {ck:10.6f}  {cc:8.4f}  {ck+cc:9.6f}  {chi_thin(lam):9.6f}")

print(f"\nTARGET (canonical normalization) chi_E = 1/(2 pi) = {TARGET:.6f}")
print("NOTE: spec's 'chi_E =? 2 pi' is a normalization error: 2 pi belongs to")
print("      m_e c^2 = chi rho v^2 a^3; with E = chi rho Gamma0^2 a0 the target is 1/(2 pi).")

print("\n=== horn-torus point lam=1: decomposition and comparison ===")
ck1 = chi_kin_B(1.0); cc1 = chi_cav(1.0)
print(f"chi_kin(1) = {ck1:.6f}   ratio to target = {ck1/TARGET:.6f}")
print(f"chi_E(1)   = {ck1+cc1:.6f}   ratio to target = {(ck1+cc1)/TARGET:.6f}")
print(f"thin-ring at lam=1 (invalid regime): {chi_thin(1.0):.6f}  -> Layer A/B kinetic mismatch factor {(0.5*(np.log(8)-2))/ck1:.4f}")

print("\n=== kernel (regularization) sensitivity at lam=1 ===")
for mu in (0.25, 0.5, 1.0, 2.0, 4.0):
    ckm = chi_kin_B(1.0, mu)
    print(f"mu={mu:5.2f}  chi_kin(1)={ckm:.6f}  chi_E(1)={ckm+0.25:.6f}")

print("\n=== variational check: is dE/dlam > 0 at lam=1 (constraint binds)? ===")
h=1e-4
d = (chi_kin_B(1.0+h)+chi_cav(1.0+h) - chi_kin_B(1.0-h)-chi_cav(1.0-h))/(2*h)
print(f"d chi_E/d lam |_(lam=1) = {d:.6f}  (>0 => embedded-torus constraint binds, horn torus selected)")

print("\n=== does chi_E(lam)=target have a solution for lam>=1? ===")
lams = np.linspace(1.0, 20.0, 96)
vals = np.array([chi_kin_B(l, N=20001)+chi_cav(l) for l in lams])
print(f"min chi_E on [1,20] = {vals.min():.6f} at lam={lams[np.argmin(vals)]:.2f}  (target {TARGET:.6f})")
