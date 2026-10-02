import numpy as np

import matplotlib
matplotlib.use('TkAgg')  # Ensure it uses Tkinter backend

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
# Corrected and clear visualization with sequences explicitly plotted and labeled with different colors and tints

rotation_steps=0
rotation_angle = (2 * np.pi / 27) / 3
# Define provided base sequence
base_sequence = [1, 5, 9, 4, 8, 3, 7, 2, 6, 1]

# 3-phase offsets on the 27-gon: 120° = 9 steps, 240° = 18 steps
phase_offset_A = 0
phase_offset_B = 9   # +120°
phase_offset_C = 18  # +240°

# Opposite side: ~180° = 13 steps on 27-gon (D/E/F mirror A/B/C)
phase_offset_180 = 13
phase_offset_D = (phase_offset_A + phase_offset_180) % 27
phase_offset_E = (phase_offset_B + phase_offset_180) % 27
phase_offset_F = (phase_offset_C + phase_offset_180) % 27

base_sequence_reverse = list(reversed(base_sequence))

def make_phase_sequences(phase_offset, base):
    seq = [((num * 3 - phase_offset - 1) % 27) + 1 for num in base]
    return seq, seq, seq

sequence_A_forward, sequence_A_neutral, sequence_A_backward = make_phase_sequences(phase_offset_A, base_sequence)
sequence_B_forward, sequence_B_neutral, sequence_B_backward = make_phase_sequences(phase_offset_B, base_sequence)
sequence_C_forward, sequence_C_neutral, sequence_C_backward = make_phase_sequences(phase_offset_C, base_sequence)
sequence_D_forward, sequence_D_neutral, sequence_D_backward = make_phase_sequences(phase_offset_D, base_sequence_reverse)
sequence_E_forward, sequence_E_neutral, sequence_E_backward = make_phase_sequences(phase_offset_E, base_sequence_reverse)
sequence_F_forward, sequence_F_neutral, sequence_F_backward = make_phase_sequences(phase_offset_F, base_sequence_reverse)

# Points setup
angles = np.linspace(0, 2 * np.pi, 28)[:-1]
positions = {i+1: (np.cos(angle), np.sin(angle)) for i, angle in enumerate(angles)}
segment_shift = ((2 * np.pi / 27) / 3)


# Recalculate positions with adjusted angles for rotation and reversed numbering
angles_rotated = np.linspace(0, 2 * np.pi, 28)[:-1] - np.pi*1.5 +(2*np.pi*(1/27)) # Rotate 90° counterclockwise
angles_rotated = angles_rotated[::-1]  # Reverse numbering for clockwise count
positions_rotated = {i+1: (np.cos(angle), np.sin(angle)) for i, angle in enumerate(angles_rotated)}


angles_rotated += rotation_angle

# Plot setup
plt.figure(figsize=(14, 14))
plt.axis('equal')

def plot_rotated_wire(sequence, segment, base_color, style, label, alpha=1.0):
    for i in range(len(sequence)-1):
        num = sequence[i]
        next_num = sequence[i+1]

        # Apply rotation offset here:
        angle_start = angles_rotated[(num - 1 + rotation_steps) % 27] + segment_shift * (segment - 1)
        angle_end = angles_rotated[(next_num - 1 + rotation_steps) % 27] + segment_shift * (segment - 1)

        x_start, y_start = np.cos(angle_start), np.sin(angle_start)
        x_end, y_end = np.cos(angle_end), np.sin(angle_end)

        plt.plot([x_start, x_end], [y_start, y_end],
                 color=base_color, linestyle=style, linewidth=2, alpha=alpha, label=label if i == 0 else "")


# Phase A (Blue)
plot_rotated_wire(sequence_A_forward, 1, 'blue', '-', 'Phase A Forward', alpha=0.9)
plot_rotated_wire(sequence_A_neutral, 2, 'blue', '--', 'Phase A Neutral', alpha=0.1)
plot_rotated_wire(sequence_A_backward, 3, 'blue', '-', 'Phase A Backward', alpha=0.7)

# Phase B (Red)
plot_rotated_wire(sequence_B_forward, 1, 'red', '-', 'Phase B Forward', alpha=0.9)
plot_rotated_wire(sequence_B_neutral, 2, 'red', '--', 'Phase B Neutral', alpha=0.1)
plot_rotated_wire(sequence_B_backward, 3, 'red', '-', 'Phase B Backward', alpha=0.7)

# Phase C (Green)
plot_rotated_wire(sequence_C_forward, 1, 'green', '-', 'Phase C Forward', alpha=0.9)
plot_rotated_wire(sequence_C_neutral, 2, 'green', '--', 'Phase C Neutral', alpha=0.1)
plot_rotated_wire(sequence_C_backward, 3, 'green', '-', 'Phase C Backward', alpha=0.7)

# Phase D/E/F — 180° opposite, reversed direction (segments 1↔3 swapped)
plot_rotated_wire(sequence_D_forward, 3, 'navy', '-', 'Phase D Forward', alpha=0.9)
plot_rotated_wire(sequence_D_neutral, 2, 'navy', '--', 'Phase D Neutral', alpha=0.1)
plot_rotated_wire(sequence_D_backward, 1, 'steelblue', '-', 'Phase D Backward', alpha=0.7)

plot_rotated_wire(sequence_E_forward, 3, 'maroon', '-', 'Phase E Forward', alpha=0.9)
plot_rotated_wire(sequence_E_neutral, 2, 'maroon', '--', 'Phase E Neutral', alpha=0.1)
plot_rotated_wire(sequence_E_backward, 1, 'salmon', '-', 'Phase E Backward', alpha=0.7)

plot_rotated_wire(sequence_F_forward, 3, 'darkgreen', '-', 'Phase F Forward', alpha=0.9)
plot_rotated_wire(sequence_F_neutral, 2, 'darkgreen', '--', 'Phase F Neutral', alpha=0.1)
plot_rotated_wire(sequence_F_backward, 1, 'yellowgreen', '-', 'Phase F Backward', alpha=0.7)

# Draw clearly numbered main points with rotated positions
for num, (x, y) in positions_rotated.items():
    plt.plot(x, y, 'ko', markersize=6)
    plt.text(x * 1.05, y * 1.05, str(num), fontsize=10, ha='center', va='center')

# Adjustments and display
plt.legend()
plt.title("6-Phase Rodin Coil (ABC + DEF)", fontsize=16)
plt.grid(True)


# ✅ Get the script filename dynamically
import os
from datetime import datetime
script_name = os.path.splitext(os.path.basename(__file__))[0]
timestamp = datetime.now().strftime("%H%M%S")
filename = f"{script_name}_{timestamp}.png"
plt.savefig(filename, dpi=150)  # Save image with high resolution
plt.tight_layout()
plt.show()
