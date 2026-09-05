#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fase 4b: Emergente tijdsdilatatie met gekoppelde ruimtelijke contractie (DDE)."""

import os
import re
import time
import numpy as np
import matplotlib.pyplot as plt

from sst_closure_lab_build import MODULE_NAME, ensure_module

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# Laad de gecompileerde C++ library
ensure_module(SCRIPT_DIR)
import sst_closure_lab as lab

# ===========================================================================
# SST Canonieke Constanten (CODATA-2018)
# ===========================================================================
C = 2.99792458e8
ALPHA = 7.2973525693e-3
M_E = 9.1093837015e-31
HBAR = 1.054571817e-34

VCHAR = ALPHA * C / 2.0
OMEGA_C = (M_E * C**2) / HBAR
R_C = VCHAR / OMEGA_C

def load_ideal_trefoil(filepath="ideal.txt", knot_id="3:1:1", n_points=1024):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"{filepath} not found")

    with open(filepath, "r") as f:
        content = f.read()

    block_match = re.search(rf'<AB Id="{knot_id}".*?>(.*?)</AB>', content, re.DOTALL)
    if not block_match:
        raise ValueError(f"Knoop {knot_id} niet gevonden in bestand.")

    block = block_match.group(1)
    coeffs_A = []
    coeffs_B = []
    for line in block.split("\n"):
        if "<Coeff" in line:
            A_match = re.search(r'A="([^"]+)"', line)
            B_match = re.search(r'B="([^"]+)"', line)
            if A_match and B_match:
                A_vals = [float(x) for x in A_match.group(1).split(",")]
                B_vals = [float(x) for x in B_match.group(1).split(",")]
                coeffs_A.append(A_vals)
                coeffs_B.append(B_vals)

    A = np.array(coeffs_A)
    B = np.array(coeffs_B)

    t = np.linspace(0, 1, n_points, endpoint=False)
    points = np.zeros((n_points, 3))
    for k in range(len(A)):
        points[:, 0] += A[k, 0] * np.cos(2 * np.pi * k * t) + B[k, 0] * np.sin(2 * np.pi * k * t)
        points[:, 1] += A[k, 1] * np.cos(2 * np.pi * k * t) + B[k, 1] * np.sin(2 * np.pi * k * t)
        points[:, 2] += A[k, 2] * np.cos(2 * np.pi * k * t) + B[k, 2] * np.sin(2 * np.pi * k * t)

    return points

def main():
    print(f"[*] Geladen: {MODULE_NAME} (Fase 4b: Met Contractie)")
    print("[*] Genereren van de Ideale Trefoil (Id=3:1:1)...")
    raw_points = load_ideal_trefoil("ideal.txt", n_points=1024)

    scale_factor = 100 * R_C
    points = raw_points * scale_factor

    sim_config = {
        "c_signal": C,
        "kappa": 1e25,
        "max_iter": 2000,
        "tol": 1e-6,
        "lr": 0.05
    }

    u_fractions = np.linspace(0.0, 0.2, 10)
    u_velocities = u_fractions * C
    omega_results = []

    print("[*] Start DDE equilibratie...")
    t0 = time.time()
    for u in u_velocities:
        u_vector = [float(u), 0.0, 0.0]

        # --- LORENTZ CONTRACTIE TOEPASSEN OP HET ROOSTER ---
        gamma_inv = np.sqrt(1.0 - (u / C)**2)
        contracted_points = points.copy()
        contracted_points[:, 0] *= gamma_inv  # Contractie in de u-richting (X-as)

        # Stuur de gecontraheerde geometrie naar de C++ solver
        omega_u = lab.equilibrate_moving_trefoil(
            contracted_points, R_C, VCHAR, OMEGA_C, u_vector, sim_config
        )
        omega_results.append(omega_u)

        print(f"    -> u/c = {u/C:.2f} | (omega_u/omega_0)^2 = {(omega_u/OMEGA_C)**2:.8f} | "
              f"theory = {1.0 - (u/C)**2:.8f}")

    elapsed = time.time() - t0
    print(f"[*] Voltooid in {elapsed:.2f} s.")

    omega_results = np.array(omega_results)
    gamma_squared_inv_sim = (omega_results / OMEGA_C)**2
    gamma_squared_inv_theory = 1.0 - u_fractions**2

    plt.figure(figsize=(10, 6))
    plt.plot(u_fractions**2, gamma_squared_inv_theory, "k--", label=r"SST Swirl-Clock: $1 - (u/c)^2$")
    plt.plot(u_fractions**2, gamma_squared_inv_sim, "ro-", label="SSTcore Numerieke Output (Contracted DDE)")
    plt.xlabel(r"$(u/c)^2$")
    plt.ylabel(r"$(\omega_u / \omega_0)^2$")
    plt.title("Emergente Tijdsdilatatie uit Vertraagde Biot-Savart Dynamica (Gekoppelde Geometrie)")
    plt.legend()
    plt.grid(True)

    plot_path = os.path.join(SCRIPT_DIR, "lorentz_fase4b_contracted.png")
    plt.savefig(plot_path)
    print(f"[*] Plot saved: {plot_path}")
    plt.show()

if __name__ == "__main__":
    main()