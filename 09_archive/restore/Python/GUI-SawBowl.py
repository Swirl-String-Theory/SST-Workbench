# Smooth "SawShape" 3D coil with bowl-guided r(z) and z progression
# ------------------------------------------------------------------
# This revises your earlier script so that:
#  1) z does NOT jump linearly per step; instead it follows a smooth
#     "exponential bowl" profile z(s) and r(s) with s∈[0,1].
#  2) r at each sample also follows the bowl law r(z) (coupled path).
#  3) Between successive SawShape step indices, we interpolate several
#     samples so the path is smooth in 3D (no z-steps).
#
# You can set:
#   - corners (S), skip_forward, skip_backward
#   - turns: number of global revolutions worth of (forward,back) pairs
#   - height, r_start, r_end, power: bowl parameters
#   - samples_per_seg: smoothness along each step segment
#
# We draw 3 phases with 120° offsets. Set draw_phases=False for 1-phase.
#
import matplotlib

matplotlib.use('TkAgg')
# Extended GUI: add a "Bowl profile" radio group (1 of 3):
#   - "Exponential (r_start→r_end)"     r(s) = r_start + (r_end-r_start)*s^power
#   - "Inverse Exp (r_end→r_start)"     r(s) = r_end   - (r_end-r_start)*s^power
#   - "Linear"                           r(s) = r_start + (r_end-r_start)*s
#
# This integrates with the existing Straight/Curved SawShape, 3-phase toggles,
# and sliders for R_bottom (r_start), R_top (r_end), and Layers (pairs).
#
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons, RadioButtons, Slider
import os

# ---------- Fixed SawShape parameters ----------
S = 40
step_fwd = 11
step_bwd = -9
samples_per_seg = 24
power = 2.2  # exponent for exponential profiles
rVal = [0.01, 2.0, 0.5]  # initial Rb, Rt, n_pairs
RVal = [0.01, 2.0, 1.5]

phase_colors = ['tab:purple', 'tab:blue', 'tab:green']
phase_labels = ['Phase A', 'Phase B', 'Phase C']
phase_offsets = [0.0, 2*np.pi/3, 4*np.pi/3]

# ---------- Helpers ----------
def alternating_skip_indices(S, step_fwd, step_bwd, n_pairs, start=1):
    idx = start
    seq = [idx]
    for k in range(2*n_pairs):
        if k % 2 == 0:
            idx = (idx + step_fwd - 1) % S + 1
        else:
            idx = (idx + step_bwd - 1) % S + 1
        seq.append(idx)
    return np.array(seq, dtype=int)

slot_angles_base = np.linspace(0, 2*np.pi, S, endpoint=False) - np.pi/2.0

def r_profile(s, Rb, Rt, profile, power):
    if profile == 'Exponential':
        return Rb + (Rt - Rb) * (s**power)              # r_start -> r_end (exp)
    elif profile == 'Inverse Exp':
        return Rt - (Rt - Rb) * (s**power)              # r_end   -> r_start (exp decay)
    else:  # Linear
        return Rb + (Rt - Rb) * s

def build_straight_phase(seq, Rb, Rt, n_pairs, angle_offset=0.0, profile='Exponential'):
    N = len(seq) - 1
    s_nodes = np.linspace(0, 1, N+1)
    r_nodes = r_profile(s_nodes, Rb, Rt, profile, power)
    z_nodes = s_nodes  # normalized 0..1
    x = np.zeros(N+1); y = np.zeros(N+1); z = z_nodes.copy()
    for k in range(N+1):
        a = slot_angles_base[seq[k]-1] + angle_offset
        x[k] = r_nodes[k] * np.cos(a)
        y[k] = r_nodes[k] * np.sin(a)
    return x, y, z

def build_curved_phase(seq, Rb, Rt, n_pairs, angle_offset=0.0, profile='Exponential'):
    N = len(seq) - 1
    s_nodes = np.linspace(0, 1, N+1)
    r_nodes = r_profile(s_nodes, Rb, Rt, profile, power)
    z_nodes = s_nodes
    xs, ys, zs = [], [], []
    for k in range(N):
        i0, i1 = seq[k]-1, seq[k+1]-1
        a0 = slot_angles_base[i0] + angle_offset
        a1 = slot_angles_base[i1] + angle_offset
        da = (a1 - a0 + np.pi) % (2*np.pi) - np.pi
        a_line = a0 + np.linspace(0, 1, samples_per_seg, endpoint=False) * da
        r_line = np.linspace(r_nodes[k], r_nodes[k+1], samples_per_seg, endpoint=False)
        z_line = np.linspace(z_nodes[k], z_nodes[k+1], samples_per_seg, endpoint=False)
        xs.append(r_line * np.cos(a_line))
        ys.append(r_line * np.sin(a_line))
        zs.append(z_line)
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(zs)

# ---------- Starship 6-phase — same SawShape engine, S=9, steps +4/+4 ----------
STARSHIP_S = 9
STARSHIP_STEP_FWD = 4
STARSHIP_STEP_BWD = 4
STARSHIP_ROT_ANGLE = (2 * np.pi / 27) / 3
STARSHIP_COIL_ANGLES = (
    np.linspace(0, 2 * np.pi, 28)[:-1] - np.pi * 1.5 + (2 * np.pi / 27)
)[::-1] + STARSHIP_ROT_ANGLE
STARSHIP_SEGMENT_SHIFT = (2 * np.pi / 27) / 3

_STARSHIP_ABC_COLORS = [
    ('tab:blue', '-', 0.9), ('tab:blue', '--', 0.35), ('tab:cyan', '-', 0.85),
    ('tab:red', '-', 0.9), ('tab:red', '--', 0.35), ('tab:orange', '-', 0.85),
    ('tab:green', '-', 0.9), ('tab:green', '--', 0.35), ('tab:purple', '-', 0.85),
]
# phase_offset_27, xy_rotation, reverse saw path, segment triple, colors, tag
STARSHIP_PHASE_SPEC = [
    (0,  0.0,    False, (1, 2, 3), _STARSHIP_ABC_COLORS[0:3], 'A'),
    (9,  0.0,    False, (1, 2, 3), _STARSHIP_ABC_COLORS[3:6], 'B'),
    (18, 0.0,    False, (1, 2, 3), _STARSHIP_ABC_COLORS[6:9], 'C'),
    (0,  np.pi,  True,  (1, 2, 3), [
        ('navy', '-', 0.9), ('navy', '--', 0.35), ('steelblue', '-', 0.85)], 'a'),
    (9,  np.pi,  True,  (1, 2, 3), [
        ('maroon', '-', 0.9), ('maroon', '--', 0.35), ('salmon', '-', 0.85)], 'b'),
    (18, np.pi,  True,  (1, 2, 3), [
        ('darkgreen', '-', 0.9), ('darkgreen', '--', 0.35), ('yellowgreen', '-', 0.85)], 'c'),
]
STARSHIP_CHECK_MAP = [(0, 3), (1, 4), (2, 5)]


def starship_saw_to_27(saw_seq, phase_offset_27):
    """Map 9-gon saw indices (1..9) to 27-gon wire points."""
    return np.array([
        ((int(s) * 3 - phase_offset_27 - 1) % 27) + 1 for s in saw_seq
    ], dtype=int)


def build_starship_straight(seq_27, phase_angle, segment, Rb, Rt, profile):
    N = len(seq_27) - 1
    s_nodes = np.linspace(0, 1, N + 1)
    r_nodes = r_profile(s_nodes, Rb, Rt, profile, power)
    z_nodes = s_nodes
    x = np.zeros(N + 1)
    y = np.zeros(N + 1)
    z = z_nodes.copy()
    seg = STARSHIP_SEGMENT_SHIFT * (segment - 1)
    for k in range(N + 1):
        a = STARSHIP_COIL_ANGLES[int(seq_27[k]) - 1] + seg + phase_angle
        x[k] = r_nodes[k] * np.cos(a)
        y[k] = r_nodes[k] * np.sin(a)
    return x, y, z


def build_starship_curved(seq_27, phase_angle, segment, Rb, Rt, profile):
    N = len(seq_27) - 1
    s_nodes = np.linspace(0, 1, N + 1)
    r_nodes = r_profile(s_nodes, Rb, Rt, profile, power)
    z_nodes = s_nodes
    seg = STARSHIP_SEGMENT_SHIFT * (segment - 1)
    xs, ys, zs = [], [], []
    for k in range(N):
        i0, i1 = int(seq_27[k]) - 1, int(seq_27[k + 1]) - 1
        a0 = STARSHIP_COIL_ANGLES[i0] + seg + phase_angle
        a1 = STARSHIP_COIL_ANGLES[i1] + seg + phase_angle
        da = (a1 - a0 + np.pi) % (2 * np.pi) - np.pi
        a_line = a0 + np.linspace(0, 1, samples_per_seg, endpoint=False) * da
        r_line = np.linspace(r_nodes[k], r_nodes[k + 1], samples_per_seg, endpoint=False)
        z_line = np.linspace(z_nodes[k], z_nodes[k + 1], samples_per_seg, endpoint=False)
        xs.append(r_line * np.cos(a_line))
        ys.append(r_line * np.sin(a_line))
        zs.append(z_line)
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(zs)


def redraw_starship(ax, elev, azim, curved=True):
    n_pairs = int(L_slider.val)
    Hc = H_slider.val
    Rb = Rb_slider.val
    Rt = Rt_slider.val
    profile = profile_radio.value_selected
    phase_active = phase_checks.get_status()

    saw_seq = alternating_skip_indices(
        STARSHIP_S, STARSHIP_STEP_FWD, STARSHIP_STEP_BWD, n_pairs, start=1
    )
    build_fn = build_starship_curved if curved else build_starship_straight
    path_kind = 'Curved' if curved else 'Straight'

    ax.cla()
    ax.set_title(
        f"Starship 6‑Phase ({path_kind}) — Saw S={STARSHIP_S}, "
        f"steps (+{STARSHIP_STEP_FWD},+{STARSHIP_STEP_BWD})\n"
        f"pairs={n_pairs}, spacing={Hc:.2f}; ABC + anti @ 180°"
    )
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z (normalized × spacing)")

    for ci, (abc_i, def_i) in enumerate(STARSHIP_CHECK_MAP):
        if not phase_active[ci]:
            continue
        for idx in (abc_i, def_i):
            off27, phase_angle, reverse, segs, styles, tag = STARSHIP_PHASE_SPEC[idx]
            path = saw_seq[::-1] if reverse else saw_seq
            seq_27 = starship_saw_to_27(path, off27)
            s_fwd, s_neu, s_bwd = segs
            for segment, style_tuple, strand in (
                (s_fwd, styles[0], 'fwd'),
                (s_neu, styles[1], 'neu'),
                (s_bwd, styles[2], 'bwd'),
            ):
                x, y, z = build_fn(seq_27, phase_angle, segment, Rb, Rt, profile)
                color, ls, alpha = style_tuple
                ax.plot(x, y, z * Hc, lw=1.8, color=color, linestyle=ls, alpha=alpha,
                        label=f'{tag} {strand}')

    Rmax = max(Rb, Rt) * 1.1
    ax.set_xlim(-Rmax, Rmax); ax.set_ylim(-Rmax, Rmax); ax.set_zlim(0, 1.0)
    ax.view_init(elev=24, azim=45)
    ax.legend(loc='upper left', fontsize=7, ncol=2)
    ax.view_init(elev=elev, azim=azim)

# ---------- Figure & controls ----------
fig = plt.figure(figsize=(11.5, 8.2))
ax = fig.add_subplot(111, projection='3d')
plt.subplots_adjust(left=0.05, right=0.80, bottom=0.20)
#               axes([left, bottom, width, height])
rax_mode  = plt.axes([0.81, 0.68, 0.18, 0.26])  # Straight/Curved × SawShape/Starship
rax_chk   = plt.axes([0.81, 0.50, 0.18, 0.20])  # Phase toggles
rax_prof  = plt.axes([0.81, 0.28, 0.18, 0.20])  # Bowl profile (1 of 3)
rax_Rb    = plt.axes([0.12, 0.07, 0.30, 0.03])  # R bottom
rax_Rt    = plt.axes([0.56, 0.07, 0.30, 0.03])  # R top
rax_L     = plt.axes([0.12, 0.03, 0.74, 0.03])  # Layers
rax_S     = plt.axes([0.12, 0.05, 0.74, 0.03])  # spacing

mode_radio = RadioButtons(
    rax_mode,
    labels=[
        'Straight SawShape',
        'Curved SawShape',
        'Straight Starship',
        'Curved Starship',
    ],
    active=1,
)
phase_checks = CheckButtons(rax_chk, labels=phase_labels, actives=[True, True, True])
profile_radio = RadioButtons(rax_prof, labels=['Exponential', 'Linear', 'Inverse Exp'], active=0)

Rb_slider = Slider(rax_Rb, 'R bottom', rVal[0], rVal[1], valinit=rVal[2], valstep=0.01)
Rt_slider = Slider(rax_Rt, 'R top',    RVal[0], RVal[1], valinit=RVal[2], valstep=0.01)
L_slider  = Slider(rax_L,  'Layers (pairs: Saw +11/−9, Star +4/+4)', 1, 160, valinit=20, valstep=1)
H_slider  = Slider(rax_S,  'Spacing', 0.1, 1, valinit=0.1, valstep=0.01)

def redraw(event=None):
    # save current camera
    elev, azim = ax.elev, ax.azim
    mode = mode_radio.value_selected

    if 'Starship' in mode:
        redraw_starship(ax, elev, azim, curved=mode.startswith('Curved'))
        fig.canvas.draw_idle()
        return

    ax.cla()
    ax.set_title("SawShape — 3‑Phase, interactive\nS=40, steps (+11,−9); selectable bowl profile")
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z (normalized)")

    Rb = Rb_slider.val
    Rt = Rt_slider.val
    n_pairs = int(L_slider.val)
    Hc = H_slider.val
    curved = mode.startswith('Curved')
    profile = profile_radio.value_selected

    seq = alternating_skip_indices(S, step_fwd, step_bwd, n_pairs, start=1)

    for i, (label, color, ang_off) in enumerate(zip(phase_labels, phase_colors, [0.0, 2*np.pi/3, 4*np.pi/3])):
        if not phase_checks.get_status()[i]:
            continue
        if curved:
            x, y, z = build_curved_phase(seq, Rb, Rt, n_pairs, angle_offset=ang_off, profile=profile)
        else:
            x, y, z = build_straight_phase(seq, Rb, Rt, n_pairs, angle_offset=ang_off, profile=profile)
        ax.plot(x, y, z*Hc, lw=2, color=color, label=label)

    Rmax = max(Rb, Rt)*1.1
    ax.set_xlim(-Rmax, Rmax); ax.set_ylim(-Rmax, Rmax); ax.set_zlim(0, 1.0)
    ax.view_init(elev=24, azim=45)
    ax.legend(loc='upper left', fontsize=9)

    # restore camera
    ax.view_init(elev=elev, azim=azim)
    fig.canvas.draw_idle()

# Hook up callbacks
for w in (mode_radio, profile_radio):
    w.on_clicked(redraw)
for s in (Rb_slider, Rt_slider, L_slider, H_slider):
    s.on_changed(redraw)
phase_checks.on_clicked(lambda evt: redraw())


out_path = "../images/SawShape_GUI.png"
# Ensure output directory exists
os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
plt.savefig(out_path, dpi=160, bbox_inches='tight')

plt.show()