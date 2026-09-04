# Starship coil = SawShape on S=9 (+4/+4), mapped to 27-gon, 6 phases

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

STARSHIP_S = 9
STARSHIP_STEP_FWD = 4
STARSHIP_STEP_BWD = 4
n_pairs = 4  # incremental pairs like SawShape (1→[1,5,9], 4→[1,5,9,4,8,3,7,2,6])

rotation_angle = (2 * np.pi / 27) / 3
COIL_ANGLES = (
    np.linspace(0, 2 * np.pi, 28)[:-1] - np.pi * 1.5 + (2 * np.pi / 27)
)[::-1] + rotation_angle
SEGMENT_SHIFT = (2 * np.pi / 27) / 3
layer_spacing = 0.4


def alternating_skip_indices(S, step_fwd, step_bwd, n_pairs, start=1):
    idx = start
    seq = [idx]
    for k in range(2 * n_pairs):
        if k % 2 == 0:
            idx = (idx + step_fwd - 1) % S + 1
        else:
            idx = (idx + step_bwd - 1) % S + 1
        seq.append(idx)
    return np.array(seq, dtype=int)


def saw_to_27(saw_seq, phase_offset_27):
    return np.array([
        ((int(s) * 3 - phase_offset_27 - 1) % 27) + 1 for s in saw_seq
    ], dtype=int)


saw_seq = alternating_skip_indices(STARSHIP_S, STARSHIP_STEP_FWD, STARSHIP_STEP_BWD, n_pairs)
NUM_STEPS = len(saw_seq) - 1
z_per_step = layer_spacing / max(NUM_STEPS, 1)

PHASES = [
    (0,  0.0,    False, ('blue', '-', 0.9), ('blue', '--', 0.3), ('cyan', '-', 0.9)),
    (9,  0.0,    False, ('red', '-', 0.9), ('red', '--', 0.3), ('orange', '-', 0.9)),
    (18, 0.0,    False, ('green', '-', 0.9), ('green', '--', 0.3), ('purple', '-', 0.9)),
    (0,  np.pi,  True,  ('navy', '-', 0.9), ('navy', '--', 0.3), ('steelblue', '-', 0.9)),
    (9,  np.pi,  True,  ('maroon', '-', 0.9), ('maroon', '--', 0.3), ('salmon', '-', 0.9)),
    (18, np.pi,  True,  ('darkgreen', '-', 0.9), ('darkgreen', '--', 0.3), ('yellowgreen', '-', 0.9)),
]


def draw_wire_step(seq_27, segment, phase_angle, step_i, z_start, z_end, color, style, alpha):
    num = int(seq_27[step_i])
    next_num = int(seq_27[step_i + 1])
    seg = SEGMENT_SHIFT * (segment - 1)
    angle_start = COIL_ANGLES[num - 1] + seg + phase_angle
    angle_end = COIL_ANGLES[next_num - 1] + seg + phase_angle
    ax.plot(
        [np.cos(angle_start), np.cos(angle_end)],
        [np.sin(angle_start), np.sin(angle_end)],
        [z_start, z_end],
        color=color, linestyle=style, linewidth=2, alpha=alpha,
    )


fig = plt.figure(figsize=(12, 12))
ax = fig.add_subplot(111, projection='3d')

for off27, phase_angle, reverse, fwd_s, neu_s, bwd_s in PHASES:
    path = saw_seq[::-1] if reverse else saw_seq
    seq_27 = saw_to_27(path, off27)
    for step_i in range(NUM_STEPS):
        z0 = step_i * z_per_step
        z1 = (step_i + 1) * z_per_step
        draw_wire_step(seq_27, 1, phase_angle, step_i, z0, z1, *fwd_s)
        draw_wire_step(seq_27, 2, phase_angle, step_i, z0, z1, *neu_s)
        draw_wire_step(seq_27, 3, phase_angle, step_i, z0, z1, *bwd_s)

ax.set_title(
    f"Starship = Saw S={STARSHIP_S} (+{STARSHIP_STEP_FWD}/+{STARSHIP_STEP_BWD}), "
    f"pairs={n_pairs}, seq={list(saw_seq)}"
)
ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2); ax.set_zlim(0, layer_spacing)
ax.set_box_aspect([1, 1, 1])

import os
script_name = os.path.splitext(os.path.basename(__file__))[0]
plt.savefig(f"{script_name}.png", dpi=150)
plt.tight_layout()
plt.show()
