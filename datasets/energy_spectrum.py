import matplotlib.pyplot as plt
import numpy as np
import matplotlib
matplotlib.use('TkAgg') # Interactive backend


# Set up the figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
plt.subplots_adjust(wspace=0.3)

# ==========================================
# Panel 1: The SST Velocity Ladder (Energy)
# ==========================================

# Quantum numbers
n_levels = np.array([1, 2, 3, 4])
energies = -13.6 / n_levels**2  # eV
velocities = 1 / n_levels       # relative to alpha*c

# Plot energy levels
for n, E, v in zip(n_levels, energies, velocities):
    color = 'green' if n == 1 else 'blue'
    alpha_val = 1.0 if n == 1 else 0.7

    # Draw the line
    ax1.hlines(E, 0, 1, colors=color, linestyles='solid', linewidth=1, alpha=alpha_val)

    # Annotate State and Velocity
    label_text = f"n={n}: {E:.2f} eV"
    vel_text = f"$v_{n} = \\alpha c / {n}$"

    ax1.text(0.02, E - 0.5, label_text, fontsize=9, color=color, fontweight='bold')
    ax1.text(0.98, E - 0.5, vel_text, fontsize=11, color='black', ha='right')

# Labels and Styling
ax1.set_title("SST Hydrodynamic Energy Spectrum", fontsize=14)
ax1.set_ylabel("Vacuum Pressure Potential (eV)", fontsize=12)
ax1.set_xlabel("State Density", fontsize=12)
ax1.set_ylim(-15, 1)
ax1.set_xticks([])
ax1.grid(True, axis='y', linestyle='--', alpha=0.3)
ax1.text(0.5, -14.5, "Vacuum Ground State Limit", ha='center', color='green', fontsize=9)

# ==========================================
# Panel 2: The Vacuum Mach Limit (Geometry)
# ==========================================

# Circle data
theta = np.linspace(0, 2*np.pi, 200)

# The Nucleus (Point)
ax2.plot(0, 0, 'o', color='black', markersize=10, label='Nucleus (Vortex Core)')

# The Forbidden Zone (Turbulence/Collapse)
r_forbidden = 0.7  # Scale relative to n=1
ax2.fill_between(theta, 0, r_forbidden, color='red', alpha=0.15, label='Forbidden Zone ($v > \\alpha c$)')
ax2.plot(r_forbidden*np.cos(theta), r_forbidden*np.sin(theta), '--', color='red', linewidth=1)

# The n=1 Ground State (Stable Laminar Flow)
r_ground = 1.0
ax2.plot(r_ground*np.cos(theta), r_ground*np.sin(theta), '-', color='green', linewidth=3, label='Ground State n=1 ($v = \\alpha c$)')

# The n=2 Excited State
r_excited = 1.8 # Scaled down for visual fit (physically 4x)
ax2.plot(r_excited*np.cos(theta), r_excited*np.sin(theta), ':', color='blue', linewidth=2, label='Excited State n=2 ($v = \\alpha c / 2$)')

# Annotations
ax2.text(0, 0.3, "Unstable\nTurbulence", ha='center', va='center', color='darkred', fontsize=9)
ax2.text(0, -1.2, "Maximum Laminar Flow Speed", ha='center', color='green', fontsize=10, fontweight='bold')

# Velocity Arrows on n=1
arrow_angles = [0, np.pi/2, np.pi, 3*np.pi/2]
for ang in arrow_angles:
    ax2.arrow(np.cos(ang), np.sin(ang), -0.1*np.sin(ang), 0.1*np.cos(ang),
              head_width=0.05, head_length=0.1, fc='green', ec='green')

# Styling
ax2.set_title("The Vacuum Stability Limit ($\\alpha \\approx 1/137$)", fontsize=14)
ax2.set_aspect('equal')
ax2.set_xlim(-2, 2)
ax2.set_ylim(-2, 2)
ax2.axis('off')
ax2.legend(loc='upper right', fontsize=9)

plt.tight_layout()
plt.savefig('sst_energy_spectrum.png')
plt.show()