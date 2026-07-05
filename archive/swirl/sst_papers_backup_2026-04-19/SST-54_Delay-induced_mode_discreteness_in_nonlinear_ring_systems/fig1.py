import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')  # Ensure it uses Tkinter backend
# =============================================================
# Delay–Induced Mode Discreteness Simulation (Hybrid Figure)
# =============================================================
# This code numerically integrates the cubic delayed-feedback
# equation described in the manuscript:
#
#   ε * x'(t) = -x(t) + μ * x(t - τ) - [x(t - τ)]^3
#
# Equation (1) in your paper.
# -------------------------------------------------------------
# Physical Interpretation:
# - ε: fast relaxation timescale (small parameter)
# - μ: feedback gain (controls Hopf bifurcation threshold)
# - τ: delay (circulation time in ring systems)
# - x(t): scalar field amplitude representing the circulating field
#
# In the long-delay regime (τ >> ε), the delay interval acts as
# a pseudo-space σ ∈ [0, τ], and successive intervals of length τ
# represent evolution in "slow time" n. This yields a space–time
# pattern equivalent to domain formation in a 1D extended medium.
# -------------------------------------------------------------

# ------------------ PARAMETERS -------------------------------
epsilon = 0.01  # fast relaxation
mu = 1.5        # feedback gain (supercritical regime)
tau = 60.0      # delay (loop propagation time)
dt = 0.01       # integration step
t_max = 2000.0  # total integration time (allows plateau stabilization)

# Derived quantities
steps = int(t_max / dt)             # number of integration steps
delay_steps = int(tau / dt)         # delay in time steps

# ------------------ INITIAL CONDITION -------------------------
# History function: random noise around zero to break symmetry
history = np.random.normal(0, 0.01, delay_steps)
x = np.zeros(steps)
x[:delay_steps] = history

# ------------------ NUMERICAL INTEGRATION ---------------------
# Integration by "method of steps":
# Each new x(t) depends on its delayed value x(t - τ)
for i in range(delay_steps, steps - 1):
    x_delayed = x[i - delay_steps]
    dxdt = (-x[i] + mu * x_delayed - x_delayed ** 3) / epsilon
    x[i + 1] = x[i] + dt * dxdt

# ------------------ RESHAPING FOR SPACE–TIME PLOT -------------
# The data is reshaped so each delay interval τ corresponds to a
# pseudo-space slice σ ∈ [0, τ]; rows correspond to slow time n.
points_per_tau = delay_steps
num_intervals = steps // points_per_tau
space_time = x[:num_intervals * points_per_tau].reshape((num_intervals, points_per_tau))

# ------------------ HYBRID FIGURE -----------------------------
# Figure combines:
# (a) Schematic conceptual view (pseudo-space vs slow time, labeled)
# (b) Numerical simulation result (space–time pattern from integration)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# --- (a) Conceptual schematic ---
ax = axes[0]
ax.set_title("(a) Conceptual schematic")
ax.set_xlabel("Pseudo-space σ ∈ [0, τ]")
ax.set_ylabel("Slow time (n τ)")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

# Draw conceptual plateaus (x1 and x2) and a sharp front
ax.fill_betweenx([0, 0.4], 0.0, 0.45, color="gold", alpha=0.7, label="Plateau x₁")
ax.fill_betweenx([0, 0.4], 0.55, 1.0, color="purple", alpha=0.7, label="Plateau x₂")
ax.text(0.18, 0.15, "Plateau $x_1$", fontsize=10, color="black")
ax.text(0.7, 0.15, "Plateau $x_2$", fontsize=10, color="white")
ax.arrow(0.5, 0.1, 0.0, 0.25, head_width=0.03, head_length=0.03, color="black")
ax.text(0.52, 0.25, "Front drift", fontsize=9, rotation=90, va="bottom")
ax.legend(frameon=False, fontsize=8, loc="upper right")

# --- (b) Numerical simulation ---
ax2 = axes[1]
im = ax2.imshow(space_time, aspect='auto', cmap='inferno', origin='lower',
                extent=[0, tau, 0, num_intervals], vmin=-1, vmax=1)
ax2.set_title("(b) Numerical integration of Eq. (1)")
ax2.set_xlabel("Pseudo-space σ ∈ [0, τ]")
ax2.set_ylabel("Slow time (n τ)")

cbar = fig.colorbar(im, ax=ax2, shrink=0.8)
cbar.set_label("x(σ, n)")

plt.suptitle("Delay–Induced Mode Discreteness: Schematic vs Numerical Dynamics", fontsize=13)
plt.tight_layout(rect=[0, 0, 1, 0.95])
import os
from datetime import datetime
script_name = os.path.splitext(os.path.basename(__file__))[0]
timestamp = datetime.now().strftime("%H%M%S")
filename = f"{script_name}.png"
plt.savefig(filename, dpi=600)  # Save image with high resolution
plt.show()