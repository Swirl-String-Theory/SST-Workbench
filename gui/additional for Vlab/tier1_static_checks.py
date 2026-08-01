"""Tier 1 — static validation of the C_eff algebra (straight twisted vortex tube).

Model A (uniform-vorticity Rankine core, uniform vortex-line twist rate q):
    omega_z = Gamma/(pi a^2)           (r <= a)
    omega_phi = q r omega_z            (helical vortex lines, d(phi)/ds = q)
    induced axial flow  w(r) = (q omega_z / 2)(a^2 - r^2)
    targets:  E_w/L = rho Gamma^2 q^2 a^2 / (24 pi)   ->  C_eff = rho Gamma^2 a^2 / (12 pi)
              H/L   = Gamma^2 q / (2 pi)              ->  H = Gamma^2 Tw   (Moffatt-Ricca)

Model B (hollow core / sheet twist):
    all vorticity in a sheet at r = a; twisted sheet induces uniform w0 = q Gamma/(2 pi) inside
    targets:  E_w/L = rho Gamma^2 q^2 a^2 / (8 pi)    ->  C_eff = rho Gamma^2 a^2 / (4 pi)
              H/L   = Gamma^2 q / (2 pi)

All integrals done numerically; every target printed as (numeric, analytic, rel.err).
"""
import numpy as np

rho, Gamma, a, q = 1.0, 1.0, 1.0, 1.0
N = 400_000
r = (np.arange(N) + 0.5) * (a / N)
dr = a / N

def report(name, num, ana):
    print(f"  {name:34s} numeric={num:.10f}  analytic={ana:.10f}  rel.err={abs(num-ana)/abs(ana):.2e}")

print("Model A: Rankine core, uniform twist")
om0 = Gamma / (np.pi * a**2)
w   = 0.5 * q * om0 * (a**2 - r**2)
u_phi = 0.5 * om0 * r                      # inside; outside contributes no energy change or helicity
om_phi = q * r * om0

Ew = 0.5 * rho * np.sum(w**2 * 2*np.pi*r) * dr
report("E_w/L", Ew, rho*Gamma**2*q**2*a**2/(24*np.pi))
Ceff = 2*Ew/q**2
report("C_eff", Ceff, rho*Gamma**2*a**2/(12*np.pi))

H = np.sum((u_phi*om_phi + w*om0) * 2*np.pi*r) * dr
report("H/L", H, Gamma**2*q/(2*np.pi))

print("Model B: hollow core, sheet twist")
w0 = q*Gamma/(2*np.pi)
Ew_B = 0.5*rho*w0**2*np.pi*a**2
report("E_w/L", Ew_B, rho*Gamma**2*q**2*a**2/(8*np.pi))
report("C_eff", 2*Ew_B/q**2, rho*Gamma**2*a**2/(4*np.pi))
# helicity: sheet-averaged velocities at r=a: <u_phi>=Gamma/(4 pi a), <w>=w0/2
H_B = (Gamma/(4*np.pi*a)) * (q*Gamma/(2*np.pi)) * (2*np.pi*a)/(2*np.pi*a) * (2*np.pi*a) \
      + (w0/2) * Gamma
report("H/L", H_B, Gamma**2*q/(2*np.pi))

print("Ring-speed targets (Saffman core constant, -(2 pi / Gamma R) * int w^2 r dr):")
R = 1.0
dU_A = -(2*np.pi/(Gamma*R)) * np.sum(w**2 * r) * dr
report("dU (model A)", dU_A, -Gamma*a**2*q**2/(12*np.pi*R))
dU_B = -(2*np.pi/(Gamma*R)) * w0**2 * a**2/2
report("dU (model B)", dU_B, -Gamma*a**2*q**2/(4*np.pi*R))
