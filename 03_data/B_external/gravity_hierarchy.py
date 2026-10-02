import matplotlib.pyplot as plt
import numpy as np
import matplotlib
matplotlib.use('TkAgg') # Interactive backend

# Canonical Constants
rho_f = 7.0e-7
rc = 1.40897e-15
v_swirl = 1.09384563e6
Gamma0 = 2 * np.pi * rc * v_swirl
G_phys = 6.67430e-11

# Calculation of Natural Gravity (G_nat)
# G_nat = Gamma0^2 / (rho_f * rc^4)
numerator = Gamma0**2
denominator = rho_f * (rc**4)
G_nat = numerator / denominator

# The Lambda Factor
lambda_G = G_phys / G_nat

# Visualization Data
values = [np.log10(G_nat), np.log10(G_phys)]
labels = ['Natural Vortex Gravity\n(Strong Force Scale)', 'Observed Gravity\n(Residual Scale)']
colors = ['firebrick', 'navy']

# Plotting
fig, ax = plt.subplots(figsize=(8, 6))
bars = ax.bar(labels, values, color=colors, alpha=0.8)

# Baseline at 0
ax.axhline(0, color='black', linewidth=1)

# Annotations
ax.set_ylabel('Log Magnitude ($Log_{10}$)', fontsize=12)
ax.set_title(f'The SST Gravitational Hierarchy\n$\lambda_G \\approx 10^{{{int(np.log10(lambda_G))}}}$', fontsize=14)
ax.grid(axis='y', linestyle='--', alpha=0.3)

# Add text labels on bars
for bar, val in zip(bars, values):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + (5 if height > 0 else -10),
            f'$10^{{{int(val)}}}$',
            ha='center', va='bottom' if height > 0 else 'top', fontsize=12, fontweight='bold')

# Arrow annotation for the gap
ax.annotate('', xy=(0.5, np.log10(G_phys)), xytext=(0.5, np.log10(G_nat)),
            arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
ax.text(0.5, (np.log10(G_nat) + np.log10(G_phys))/2, f'Geometric Suppression\nFactor $\\approx 10^{{-60}}$',
        ha='left', va='center', fontsize=11, backgroundcolor='white', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

plt.tight_layout()
plt.savefig('sst_gravity_hierarchy.png')
plt.show()