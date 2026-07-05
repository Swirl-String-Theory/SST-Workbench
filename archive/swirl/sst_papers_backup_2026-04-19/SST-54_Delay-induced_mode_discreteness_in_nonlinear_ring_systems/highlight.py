import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyArrowPatch
from matplotlib import rcParams

# =========================================================
# CONFIGURATION
# =========================================================
W_IN, H_IN = 8.0139, 6.2739
DPI = 300
accent = (0.15, 0.35, 0.55)
bg_red = (0.4, 0.0, 0.1)
bg_blue = (0.1, 0.2, 0.4)

rcParams['pdf.fonttype'] = 42  # For editable text in vector export

# =========================================================
# SIMULATION
# =========================================================
def simulate_delay_dynamics(eps=0.01, mu=1.8, tau=60.0, dt=0.01, N_delays=100):
    steps_per_tau = int(tau / dt)
    total_steps = N_delays * steps_per_tau
    t = np.linspace(-tau, N_delays * tau, total_steps + steps_per_tau)
    x = np.zeros_like(t)
    x[:steps_per_tau] = 0.1 * np.sin(2 * np.pi * t[:steps_per_tau] / tau)

    for i in range(steps_per_tau, len(t)-1):
        xtau = x[i - steps_per_tau]
        dxdt = (-x[i] + mu * xtau - xtau**3) / eps
        dxdt = np.clip(dxdt, -100, 100)
        x[i + 1] = x[i] + dt * dxdt

    return x[steps_per_tau:], steps_per_tau

def reshape_space_time(x, steps_per_tau, select=(30, 80)):
    n_rounds = len(x) // steps_per_tau
    st = x[:n_rounds * steps_per_tau].reshape((n_rounds, steps_per_tau))
    return st[select[0]:select[1]]

# =========================================================
# FINAL FIGURE
# =========================================================
def plot_final_triple_panel(space_time):
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI)

    # PANEL LAYOUT
    axRing = fig.add_axes([0.05, 0.23, 0.20, 0.65])
    axConcept = fig.add_axes([0.38, 0.23, 0.22, 0.65])
    axSim = fig.add_axes([0.71, 0.23, 0.22, 0.65])
    axCaption = fig.add_axes([0.07, 0.07, 0.86, 0.08])

    for ax in [axRing, axConcept, axSim, axCaption]:
        ax.set_axis_off()

    # ------------------------
    # Title & Equation
    # ------------------------
    fig.text(0.5, 0.92, "Delay-induced mode discreteness in nonlinear ring systems",
             ha="center", fontsize=17, weight="bold")
    fig.text(0.5, 0.88, r"$\epsilon \dot{x}(t) = -x(t) + \mu x(t-\tau) - x^3(t-\tau)$",
             ha="center", fontsize=13.5)

    # ------------------------
    # LEFT PANEL — Ring
    # ------------------------
    axRing.set_xlim(0, 1)
    axRing.set_ylim(0, 1)
    cx, cy, R = 0.50, 0.50, 0.30
    axRing.add_patch(Circle((cx, cy), R, fill=False, linewidth=3, alpha=0.8))
    axRing.add_patch(Circle((cx, cy), R, fill=False, linewidth=8, alpha=0.05))

    angles = np.deg2rad([30, 90, 150, 210, 270, 330])
    for a in angles:
        x0, y0 = cx + R*np.cos(a), cy + R*np.sin(a)
        a2 = a + np.deg2rad(22)
        x1, y1 = cx + R*np.cos(a2), cy + R*np.sin(a2)
        axRing.add_patch(FancyArrowPatch((x0, y0), (x1, y1),
                                         arrowstyle='-|>', mutation_scale=14,
                                         linewidth=1.5, color=accent))

    axRing.text(cx + R + 0.09, cy, "delay\n$\\tau$", fontsize=11.5, ha="center", va="center")
    axRing.add_patch(Rectangle((0.22, 0.23), 0.12, 0.08, facecolor="black"))
    axRing.text(0.28, 0.27, r"$f(\cdot)$", fontsize=12, color="white", ha="center", va="center")

    # ------------------------
    # CENTER PANEL — Conceptual
    # ------------------------
    axConcept.set_xlim(0, 1)
    axConcept.set_ylim(0, 1)
    ny = 14
    for i in range(ny):
        y = 0.10 + i*(0.80/ny)
        color = "#e07b91" if (i//2)%2 == 0 else "#6ca0dc"
        axConcept.add_patch(Rectangle((0.15, y), 0.70, 0.80/ny, facecolor=color, alpha=0.4))
    for j in range(4):
        y0 = 0.16 + j*0.18
        axConcept.arrow(0.45, y0, 0.10, 0.06, head_width=0.012, head_length=0.015,
                        fc='k', ec='k', alpha=0.6)
    axConcept.text(0.06, 0.93, r"$n$", fontsize=12)
    axConcept.text(0.92, 0.08, r"$\sigma \in [0,\tau]$", fontsize=12, ha="right")
    axConcept.text(0.5, 0.95, "Conceptual space–time pattern", ha="center", fontsize=11.5)

    # ------------------------
    # RIGHT PANEL — Simulation
    # ------------------------
    axSim.set_xlim(0, space_time.shape[1])
    axSim.set_ylim(0, space_time.shape[0])
    axSim.imshow(space_time, aspect='auto', cmap="RdBu_r", origin='lower', interpolation='none')
    axSim.text(0.5, 1.03, "Numerical integration", ha="center", fontsize=11.5, transform=axSim.transAxes)

    # ------------------------
    # Bottom Caption
    # ------------------------
    axCaption.text(0.0, 0.2,
                   "Delay-induced pattern formation yields bistable plateau states and discrete circulation modes.",
                   fontsize=12.5, style="italic", alpha=0.85, ha="left", va="bottom")

    # ------------------------
    # Save to Multiple Formats
    # ------------------------
    fig.savefig("highlight_triple_FINAL.png", dpi=DPI, bbox_inches='tight')
    fig.savefig("highlight_triple_FINAL.tif", dpi=DPI, bbox_inches='tight', pil_kwargs={"compression": "tiff_lzw"})
    fig.savefig("highlight_triple_FINAL.pdf", bbox_inches='tight')
    plt.close(fig)
    print("✅ Highlight figure saved: PNG, TIFF, PDF")

# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    x, steps_per_tau = simulate_delay_dynamics()
    space_time = reshape_space_time(x, steps_per_tau, select=(30, 80))
    plot_final_triple_panel(space_time)