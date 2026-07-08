#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
routeA_line_density_trial.py
Trial audit for SST Route A: horizon-piercing line density -> Planck time.

This script separates:
  A0: orthodox reference target sigma*Lambda = 1/(2 Lp^2), circular if used as input.
  A1: non-G trial ansatz using only SST canonical core/fluid quantities:
      sigma*Lambda ≈ r_c^-2 * (rho_core/rho_f) * (16/pi^2) * (c/vchar)^6.

Status: RESEARCH-TRACK / TRIAL, not canon-derived.
"""
import math

# Orthodoxy for comparison only
HBAR = 1.054571817e-34
G    = 6.67430e-11
C    = 299792458.0

# SST canonical constants
VCHAR = 1.09384563e6
R_C = 1.40897017e-15
RHO_CORE = 3.8934358266918687e18
RHO_F = 7.0e-7

def routeA_target():
    Lp = math.sqrt(HBAR*G/C**3)
    tp = Lp/C
    sigmaLambda = 1.0/(2.0*Lp**2)
    return Lp, tp, sigmaLambda

def routeA_trial_sigmaLambda():
    return (1.0/R_C**2) * (RHO_CORE/RHO_F) * (16.0/math.pi**2) * (C/VCHAR)**6

def main():
    Lp, tp_ref, target = routeA_target()
    trial = routeA_trial_sigmaLambda()
    tp_trial = 1.0/(C*math.sqrt(2.0*trial))
    sigma_fit = target/trial

    print("SST Route A line-density trial")
    print("="*72)
    print(f"Reference Lp       = {Lp:.15e} m")
    print(f"Reference tp       = {tp_ref:.15e} s")
    print(f"Target sigmaLambda = {target:.15e} m^-2")
    print()
    print("Trial ansatz:")
    print("  sigmaLambda_A1 = r_c^-2 * (rho_core/rho_f) * (16/pi^2) * (c/vchar)^6")
    print(f"  sigmaLambda_A1 = {trial:.15e} m^-2")
    print(f"  ratio A1/target = {trial/target:.15f}")
    print(f"  tp_A1           = {tp_trial:.15e} s")
    print(f"  tp_A1/tp_ref    = {tp_trial/tp_ref:.15f}")
    print()
    print("Fitted per-piercing entropy weight needed for exact match:")
    print(f"  sigma_pierce_fit = target/A1 = {sigma_fit:.15f} nats")
    print(f"  exp(sigma_fit)   = {math.exp(sigma_fit):.15f} states per piercing")
    print()
    print("STATUS: RESEARCH-TRACK/TRIAL. sigma_pierce must be derived, not fitted.")

if __name__ == "__main__":
    main()
