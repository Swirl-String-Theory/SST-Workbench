import os

import numpy as np

from sst_closure_lab_build import MODULE_NAME, ensure_module

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

sst_closure_lab = ensure_module(SCRIPT_DIR)
print(f"{MODULE_NAME} module succesvol geladen.")
# --- SST Canonieke Constanten ---
v_swirl = 1.09384563e6
r_c = 1.40897017e-15
rho_core = 3.8934358266918687e18

Gamma = 2 * np.pi * r_c * v_swirl
alpha = (rho_core * Gamma**2) / (4 * np.pi)

# Torusknoop parameters
R_major = 100 * r_c
r_minor = 30 * r_c
p, q = 2, 3

# Dynamische schaalfactoren voor L(K) en H(K)
# beta heeft dimensie [Kracht], gamma heeft dimensie [Energie]
beta = alpha * np.log(R_major / r_c)
gamma = alpha * r_c

# --- Topologische Generator ---
def generate_torus_knot(p, q, R, r, N_points=2000):
    sigma = np.linspace(0, 2 * np.pi, N_points, endpoint=False)
    points = np.zeros((N_points, 3))
    points[:, 0] = (R + r * np.cos(q * sigma)) * np.cos(p * sigma)
    points[:, 1] = (R + r * np.cos(q * sigma)) * np.sin(p * sigma)
    points[:, 2] = -r * np.sin(q * sigma)
    return points

points_knot = generate_torus_knot(p, q, R_major, r_minor)

# --- Evaluatie van de Functionaal E_eff[K] ---
print(f"\n--- Evaluatie Functionaal E_eff[K] voor ({p},{q})-Torus Knoop ---")

# 1. Biot-Savart (C)
C_K = sst_closure_lab.calculate_neumann_self_energy(points_knot, r_c)
E_C = alpha * C_K

# 2. Lijntensie (L)
L_K = sst_closure_lab.calculate_length(points_knot)
E_L = beta * L_K

# 3. Heliciteit / Writhe (H)
Wr = sst_closure_lab.calculate_writhe(points_knot, r_c)
E_H = gamma * abs(Wr)

# Totale Effectieve Energie
E_total = E_C + E_L + E_H

print(f"Biot-Savart Term (alpha * C) : {E_C:.4e} J")
print(f"Lijntensie Term (beta * L)   : {E_L:.4e} J")
print(f"Heliciteit Term (gamma * |H|): {E_H:.4e} J  [Writhe = {Wr:.4f}]")
print(f"--------------------------------------------------")
print(f"Totale Effectieve Energie    : {E_total:.4e} J")