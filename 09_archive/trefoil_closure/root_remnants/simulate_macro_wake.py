#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fase 5: Tijdsdilatatie uit Macroscopische Absolute Vorticiteit (Kelvin Invariant) met CSV export."""

import os
import time
import csv
import numpy as np
import matplotlib.pyplot as plt

from sst_macro_wake_build import ensure_module, MODULE_NAME

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# Auto-compileer de C++ kernel indien nodig
ensure_module(SCRIPT_DIR)
import sst_macro_wake

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

def main():
    print(f"[*] Initialiseer Fase 5 Macroscopische Wake Solver...")
    print(f"[*] Canonieke rustfrequentie: {OMEGA_C:.6e} rad/s")

    # Exporteer mappen structuur opzetten
    export_dir = os.path.join(SCRIPT_DIR, "exports")
    os.makedirs(export_dir, exist_ok=True)

    # We scannen van rust tot 50% van de lichtsnelheid
    u_fractions = np.linspace(0.0, 0.5, 25)
    u_velocities = u_fractions * C

    omega_results = []

    print("[*] Start Biot-Savart Wake Integratie over u/c...")
    t0 = time.time()

    for u in u_velocities:
        # Geen handmatige contractie of asymmetrische fase. Puur Kelvin behoud langs Z-as.
        omega_u = sst_macro_wake.equilibrate_macro_circulation(
            R_C, OMEGA_C, float(u), C
        )
        omega_results.append(omega_u)

    print(f"[*] Voltooid in {time.time() - t0:.2f} s.")

    # Data Analyse
    omega_results = np.array(omega_results)
    u_c_squared = u_fractions**2
    gamma_squared_inv_sim = (omega_results / OMEGA_C)**2
    gamma_squared_inv_theory = 1.0 - u_c_squared

    # ===========================================================================
    # CSV Data Export
    # ===========================================================================
    csv_path = os.path.join(export_dir, "lorentz_fase5_wake_data.csv")
    with open(csv_path, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        # Header
        writer.writerow([
            "u_c_fraction",
            "u_c_squared",
            "omega_sim_rad_s",
            "gamma_inv_squared_sim",
            "gamma_inv_squared_theory"
        ])

        # Data rijen schrijven
        for i in range(len(u_fractions)):
            writer.writerow([
                f"{u_fractions[i]:.6f}",
                f"{u_c_squared[i]:.6f}",
                f"{omega_results[i]:.8e}",
                f"{gamma_squared_inv_sim[i]:.8f}",
                f"{gamma_squared_inv_theory[i]:.8f}"
            ])

    print(f"[*] Numerieke data succesvol geëxporteerd naar: {csv_path}")

    # ===========================================================================
    # Plot Generatie & Export
    # ===========================================================================
    plt.figure(figsize=(10, 6))
    plt.plot(u_c_squared, gamma_squared_inv_theory, 'k--', label=r"Orthodox SR: $1 - (u/c)^2$")
    plt.plot(u_c_squared, gamma_squared_inv_sim, 'bo-', label="SSTcore Numeriek (Puur Wake-Diefstal)")

    plt.xlabel(r"$(u/c)^2$")
    plt.ylabel(r"$(\omega_u / \omega_0)^2$")
    plt.title("Emergente Tijdsdilatatie uit Absoluut Circulatiebehoud (SST Fase 5)")
    plt.legend()
    plt.grid(True)

    plot_path = os.path.join(export_dir, "lorentz_fase5_wake.png")
    plt.savefig(plot_path)
    print(f"[*] Grafiek succesvol geëxporteerd naar: {plot_path}")

    plt.show()

if __name__ == "__main__":
    main()