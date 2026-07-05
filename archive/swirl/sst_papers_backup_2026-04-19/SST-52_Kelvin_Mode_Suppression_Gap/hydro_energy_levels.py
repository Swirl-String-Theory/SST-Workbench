import matplotlib.pyplot as plt
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Interactive backend (optional)

# Set up the figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
plt.subplots_adjust(wspace=0.3)

# ==========================================
# Panel 1: Hydrodynamic Energy Levels
# ==========================================
n_levels = np.array([1, 2, 3, 4])
energies = -13.6 / n_levels**2  # eV (hydrogenic scaling)
velocities = 1 / n_levels       # relative to alpha*c

# Plot energy levels
for n, E, v in zip(n_levels, energies, velocities):
    color = 'green' if n == 1 else 'blue'
    alpha_val = 1.0 if n == 1 else 0.7

    # Level line
    ax1.hlines(E, 0, 1, colors=color, linestyles='solid', linewidth=1, alpha=alpha_val)

    # Annotations
    label_text = f"n={n}: {E:.2f} eV"
    vel_text = f"$v_{n} = \\alpha c / {n}$"
    ax1.text(0.02, E - 0.5, label_text, fontsize=9, color=color, fontweight='bold')
    ax1.text(0.98, E - 0.5, vel_text, fontsize=11, color='black', ha='right')

# Labels and styling
ax1.set_title("Hydrodynamic Energy Levels (Vortex–Filament Picture)", fontsize=14)
ax1.set_ylabel("Energy (eV)", fontsize=12)
ax1.set_xlabel("State index (schematic)", fontsize=12)
ax1.set_ylim(-15, 1)
ax1.set_xticks([])
ax1.grid(True, axis='y', linestyle='--', alpha=0.3)

# Ground-state guide
ax1.axhline(-13.6, color='green', linestyle='dashed', linewidth=0.8, alpha=0.6)
ax1.text(0.5, -14.5, "Hydrogen ground state (−13.6 eV)", ha='center', color='green', fontsize=10)

# ==========================================
# Panel 2: Laminar Stability and Geometry
# ==========================================
theta = np.linspace(0, 2*np.pi, 200)

# Nucleus (anchor point)
ax2.plot(0, 0, 'o', color='black', markersize=10, label='Nucleus')

# Forbidden region: super-laminar speeds
r_forbidden = 0.7
ax2.fill_between(theta, 0, r_forbidden, color='red', alpha=0.15, label='Forbidden region ($v > \\alpha c$)')
ax2.plot(r_forbidden*np.cos(theta), r_forbidden*np.sin(theta), '--', color='red', linewidth=1)

# Ground state n=1 (laminar baseline)
r_ground = 1.0
ax2.plot(r_ground*np.cos(theta), r_ground*np.sin(theta), '-', color='green', linewidth=3,
         label='Ground state n=1 ($v = \\alpha c$)')

# Excited state n=2 (schematic radius scaling)
r_excited = 1.8  # (visual scaling; physical ~4x)
ax2.plot(r_excited*np.cos(theta), r_excited*np.sin(theta), ':', color='blue', linewidth=2,
         label='Excited state n=2 ($v = \\alpha c / 2$)')

# Annotations
ax2.text(0, 0.3, "Super-laminar\n(instability)", ha='center', va='center', color='darkred', fontsize=9)
ax2.text(0, -1.2, "Laminar speed limit", ha='center', color='green', fontsize=10, fontweight='bold')
ax2.text(0.8, 0, "Forbidden\nregion", color='darkred', fontsize=9, ha='center', va='center')

# Velocity arrows
arrow_angles = [0, np.pi/2, np.pi, 3*np.pi/2]
for ang in arrow_angles:
    ax2.arrow(np.cos(ang), np.sin(ang), -0.1*np.sin(ang), 0.1*np.cos(ang),
              head_width=0.05, head_length=0.1, fc='green', ec='green')
for ang in arrow_angles:
    ax2.arrow(r_excited*np.cos(ang), r_excited*np.sin(ang),
              -0.1*np.sin(ang), 0.1*np.cos(ang),
              head_width=0.05, head_length=0.1, fc='blue', ec='blue')

# Styling
ax2.set_title("Laminar Stability Limit ($\\alpha \\approx 1/137$)", fontsize=14)
ax2.set_aspect('equal')
ax2.set_xlim(-2, 2)
ax2.set_ylim(-2, 2)
ax2.axis('off')
ax2.legend(loc='upper right', fontsize=9)

plt.tight_layout()
fig.suptitle("Quantized Energy and Stability in a Hydrodynamic Vortex–Filament Model", fontsize=16, y=1.02)

# Neutral filename for the paper
plt.savefig("hydro_energy_levels.png", dpi=300, bbox_inches='tight')
plt.show()