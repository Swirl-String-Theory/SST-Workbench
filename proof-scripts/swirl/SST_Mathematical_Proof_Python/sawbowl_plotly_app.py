# Plotly 3D version of GUI-SawBowl.py
# Converted from matplotlib to Plotly for Streamlit integration
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ---------- Fixed SawShape parameters ----------
S = 40
step_fwd = 11
step_bwd = -9
samples_per_seg = 24
power = 2.2  # exponent for exponential profiles

phase_colors = ['purple', 'blue', 'green']
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

def build_figure(Rb, Rt, n_pairs, Hc, curved, profile, show_phases):
    """Build Plotly figure with current parameters."""
    seq = alternating_skip_indices(S, step_fwd, step_bwd, n_pairs, start=1)
    
    fig = go.Figure()
    
    for i, (label, color, ang_off) in enumerate(zip(phase_labels, phase_colors, phase_offsets)):
        if not show_phases[i]:
            continue
        if curved:
            x, y, z = build_curved_phase(seq, Rb, Rt, n_pairs, angle_offset=ang_off, profile=profile)
        else:
            x, y, z = build_straight_phase(seq, Rb, Rt, n_pairs, angle_offset=ang_off, profile=profile)
        
        fig.add_trace(go.Scatter3d(
            x=x,
            y=y,
            z=z*Hc,
            mode='lines',
            name=label,
            line=dict(color=color, width=4)
        ))
    
    Rmax = max(Rb, Rt)*1.1
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-Rmax, Rmax], title="x"),
            yaxis=dict(range=[-Rmax, Rmax], title="y"),
            zaxis=dict(range=[0, 1.0], title="z (normalized)"),
            aspectmode='cube',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2),
                center=dict(x=0, y=0, z=0)
            )
        ),
        title="SawShape — 3‑Phase, interactive<br>S=40, steps (+11,−9); selectable bowl profile",
        width=None,  # Use container width
        height=800,  # Fixed height to fill viewport
        autosize=True,
        legend=dict(x=0, y=1)
    )
    return fig

def st_app():
    """Streamlit app for SawBowl visualization."""
    st.title("SawShape 3D Coil - Bowl Profile")
    st.caption("Interactive 3-phase SawShape coil with bowl-guided r(z) and z progression")
    
    # Sidebar controls
    with st.sidebar:
        st.header("Controls")
        
        # Mode selection
        mode = st.radio(
            "Mode",
            ["Straight SawShape", "Curved SawShape"],
            index=1
        )
        curved = (mode == "Curved SawShape")
        
        # Profile selection
        profile = st.radio(
            "Bowl Profile",
            ["Exponential", "Linear", "Inverse Exp"],
            index=0
        )
        
        # Phase toggles
        st.subheader("Phases")
        show_phases = [
            st.checkbox(phase_labels[0], value=True, key="phase_a"),
            st.checkbox(phase_labels[1], value=True, key="phase_b"),
            st.checkbox(phase_labels[2], value=True, key="phase_c")
        ]
        
        # Sliders
        st.subheader("Parameters")
        Rb = st.slider("R bottom", 0.01, 2.0, 0.5, 0.01)
        Rt = st.slider("R top", 0.01, 2.0, 1.5, 0.01)
        n_pairs = st.slider("Layers (pairs: 1 = +11/−9 once)", 1, 160, 20, 1)
        Hc = st.slider("Spacing", 0.1, 1.0, 0.1, 0.01)
    
    # Build and display figure
    fig = build_figure(Rb, Rt, n_pairs, Hc, curved, profile, show_phases)
    st.plotly_chart(fig, width='stretch')

if __name__ == "__main__":
    try:
        st.set_page_config(page_title="SawBowl 3D", layout="wide")
    except:
        pass
    st_app()