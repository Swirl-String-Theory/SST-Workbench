import numpy as np
import matplotlib.pyplot as plt

# Define the domain for Magnetic Field Strength B (in Tesla)
# Range from 0 to extreme fields (hypothetical 100T for theoretical limit visualization)
B = np.linspace(0, 100, 500)

# Constants for the simulation
L = 1.0          # Path length (arbitrary units)
V_standard = 2.5 # Standard Verdet constant
c = 3e8          # Speed of light

# 1. Standard Linear Model (Classical)
# theta = V * L * B
theta_linear = V_standard * L * B

# 2. SST Model with Tangential Velocity Saturation
# The coupling efficiency drops as local vortex alignment saturates.
# We model the effective tangential velocity interaction as a Langevin-type saturation function
# or a hyperbolic tangent saturation common in alignment mechanics.
# SST factor: tanh(B / B_saturation)
B_sat = 40.0 # Field strength where vortex alignment saturates
theta_sst = V_standard * L * B_sat * np.tanh(B / B_sat)

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(B, theta_linear, 'k--', label='Standard Linear Prediction (Classic)', linewidth=1.5)
plt.plot(B, theta_sst, 'r-', label='SST Prediction (Velocity Saturation)', linewidth=2.5)

# Annotations
plt.title(r'Photon Polarization Rotation ($\theta$) vs. Magnetic Field Strength ($B$)', fontsize=14)
plt.xlabel('Magnetic Field Strength $B$ [Tesla]', fontsize=12)
plt.ylabel(r'Rotation Angle $\theta$ [Degrees]', fontsize=12)
plt.legend(fontsize=11)
plt.grid(True, which='both', linestyle='--', alpha=0.6)

# Highlight the divergence
plt.fill_between(B, theta_linear, theta_sst, where=(B > 10), color='gray', alpha=0.1, label='Divergence Zone')

# Mark the saturation region
plt.annotate('Vortex Alignment Saturation\n($v_t$ limit reached)',
             xy=(70, 100), xytext=(50, 150),
             arrowprops=dict(facecolor='black', shrink=0.05))

plt.tight_layout()
plt.savefig('sst_faraday_saturation.png')

import numpy as np
import matplotlib.pyplot as plt

# SST Canonical Constants (from user text)
v_swirl = 1.09384563e6      # m/s
r_c = 1.40897017e-15        # m
omega_max = v_swirl / r_c   # ~7.76e20 rad/s (The UV/Gamma Cutoff)
c = 3e8                     # Speed of light

# Simulation Parameters
# We simulate a frequency range from Visible (10^15) up to the Cutoff (10^20)
frequencies = np.logspace(15, 20.9, 500)
B_field = 1.0               # 1 Tesla
L_path = 0.01               # 1 cm path length
n0 = 1.5                    # Base refractive index (glass-like)

# Larmor Frequency (approximate for electron mass)
e_charge = 1.602e-19
m_electron = 9.109e-31
omega_L = (e_charge * B_field) / (2 * m_electron)

# SST Dispersion-based Rotation Calculation
# Rotation theta ~ proportional to derivative of refractive index
# Scaling factor A combines material density constants
A = (n0**2 - 1) / 2.0

# Calculate Rotation Angle (theta)
# We use the derived proportionality: theta propto omega / (omega_max^2 - omega^2)
# We normalize to show the RELATIVE magnitude divergence
denominator = omega_max**2 - frequencies**2
# Avoid division by zero near resonance
denominator[np.abs(denominator) < 1e38] = 1e38

theta_response = (frequencies * omega_L) / denominator

# Normalize for plotting (Arbitrary Units to show behavior topology)
theta_norm = theta_response / np.max(np.abs(theta_response))

# Plotting
plt.figure(figsize=(10, 6))

# Plot the rotation curve
plt.plot(frequencies, theta_norm, 'b-', linewidth=2, label='SST Faraday Rotation')

# Add the Cutoff Line (omega_max)
plt.axvline(x=omega_max, color='r', linestyle='--', linewidth=2, label=r'$\omega_{max}$ (SST Cutoff)')

# Formatting
plt.xscale('log')
plt.yscale('symlog', linthresh=1e-4) # Symlog to handle the divergence
plt.title(r'SST Resonant Faraday Effect: From Visible to $\omega_{max}$', fontsize=14)
plt.xlabel(r'Photon Frequency $\omega$ [rad/s]', fontsize=12)
plt.ylabel('Normalized Rotation Angle (Log Scale)', fontsize=12)
plt.grid(True, which="both", alpha=0.5)

# Annotations
plt.text(1e16, 1e-2, 'Visible/UV Regime\n(Linear Behavior)', fontsize=10, color='green')
plt.text(1e19, 0.5, 'Resonant Divergence\n(Gamma Ray Limit)', fontsize=10, color='red')

plt.legend()
plt.tight_layout()

plt.savefig('sst_resonant_faraday.png')