import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.optimize import fsolve
import matplotlib
matplotlib.use('TkAgg') # Interactive backend
# ==========================================
# 1. SST CANONICAL CONSTANTS
# ==========================================
# Characteristic Swirl Velocity [m/s]
SST_V_SWIRL = 1.09384563e6

# ==========================================
# 2. RESONANCE SOLVER
# ==========================================
def torus_knot_length(R, r_ratio, p, q):
    """
    Calculates the physical wire length of a (p,q) torus knot.
    R: Major Radius (m)
    r_ratio: Ratio of minor/major radius (r/R)
    p: Turns around the ring (theta)
    q: Turns through the hole (phi)
    """
    # Integration over one full period (2*pi*p)
    # Using numerical discretization for arc length
    t = np.linspace(0, 2 * np.pi * p, 5000)

    # r is derived from ratio
    r = R * r_ratio

    # Parametric derivatives (dx/dt, dy/dt, dz/dt)
    # x = (R + r*cos(q/p * t)) * cos(t)
    # y = (R + r*cos(q/p * t)) * sin(t)
    # z = r * sin(q/p * t)

    k = q / p  # winding ratio

    dxdt = - (R + r*np.cos(k*t))*np.sin(t) - r*k*np.sin(k*t)*np.cos(t)
    dydt = (R + r*np.cos(k*t))*np.cos(t) - r*k*np.sin(k*t)*np.sin(t)
    dzdt = r * k * np.cos(k*t)

    ds = np.sqrt(dxdt**2 + dydt**2 + dzdt**2)
    L = np.trapz(ds, t) # Integrate
    return L

def find_resonant_radius(target_freq_hz, r_ratio=0.618, p=5, q=12):
    """
    Finds the Major Radius R needed for the wire length L 
    to match the SST fundamental wavelength.
    """
    # Target Wavelength (Fundamental Mode)
    # Lambda = v_swirl / f
    target_L = SST_V_SWIRL / target_freq_hz

    # Define error function for solver: Length(R) - Target_L = 0
    func = lambda R: torus_knot_length(R, r_ratio, p, q) - target_L

    # Initial guess: Target_L / (2*pi*p) roughly
    R_guess = target_L / (2 * np.pi * p * 1.5)

    R_optimal = fsolve(func, R_guess)[0]
    return R_optimal, target_L

# ==========================================
# 3. GENERATION & PLOTTING
# ==========================================
def generate_rodin_phase(R, r, p, q, phase_shift_angle, num_points=2000):
    # theta goes from 0 to 2*pi*p (full closure)
    theta = np.linspace(0, 2 * np.pi * p, num_points)

    # phi is coupled to theta by q/p ratio + phase shift
    phi = (q / p) * theta + phase_shift_angle

    x = (R + r * np.cos(phi)) * np.cos(theta)
    y = (R + r * np.cos(phi)) * np.sin(theta)
    z = r * np.sin(phi)
    return x, y, z

# --- USER PARAMETERS ---
TARGET_FREQ = 14.0e6  # Example: 14 MHz (High Frequency Band)
P_TURNS = 5           # Theta turns (Major axis)
Q_TURNS = 12          # Phi turns (Minor axis) - Matches 12/5 ratio
R_RATIO = 0.618       # Golden Ratio geometry for stability

# --- CALCULATE OPTIMAL GEOMETRY ---
print(f"--- SST RESONANCE CALCULATOR ---")
print(f"Target Frequency: {TARGET_FREQ/1e6} MHz")
print(f"SST Swirl Velocity: {SST_V_SWIRL:.2e} m/s")

R_opt, L_wire = find_resonant_radius(TARGET_FREQ, R_RATIO, P_TURNS, Q_TURNS)
r_opt = R_opt * R_RATIO

print(f"\n[RESULTS]")
print(f"Required Wire Length (L): {L_wire:.4f} m")
print(f"Optimal Major Radius (R): {R_opt*100:.4f} cm")
print(f"Optimal Minor Radius (r): {r_opt*100:.4f} cm")

# --- PLOTTING ---
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection='3d')

# Generate 3 Phases (0, 120, 240 degrees shift in PHI domain)
shifts = [0, 2*np.pi/3, 4*np.pi/3]
colors = ['crimson', 'dodgerblue', 'gold']

for i, shift in enumerate(shifts):
    x, y, z = generate_rodin_phase(R_opt, r_opt, P_TURNS, Q_TURNS, shift)
    ax.plot(x, y, z, c=colors[i], lw=2, label=f'Phase {i+1}')

# Formatting
ax.set_title(f"SST Resonant Coil\nFreq: {TARGET_FREQ/1e6} MHz | R: {R_opt*100:.2f} cm", fontsize=14)
ax.set_xlabel('X (m)')
ax.set_ylabel('Y (m)')
ax.set_zlabel('Z (m)')
ax.set_box_aspect([1,1,0.6]) # Aspect ratio
ax.legend()
plt.tight_layout()
plt.show()