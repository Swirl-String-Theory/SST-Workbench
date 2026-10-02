# Plotly 3D version of GUI - 3 Fat-knots.py (trefoil knot visualization)
# Converted from matplotlib/PyQt5 to Plotly for Streamlit integration
import numpy as np
import plotly.graph_objects as go
import streamlit as st

def generate_trefoil_knot(n_points=300):
    """Generate trefoil knot parametric centerline."""
    theta = np.linspace(0, 2 * np.pi, n_points)
    x = (2 + np.cos(3 * theta)) * np.cos(2 * theta)
    y = (2 + np.cos(3 * theta)) * np.sin(2 * theta)
    z = np.sin(3 * theta)
    return x, y, z

def generate_tube_surface(x, y, z, tube_radius=0.3, n_circle=12):
    """Generate tube surface around the knot centerline."""
    tube_x, tube_y, tube_z = [], [], []
    
    for i in range(len(x)):
        # approximate local tangent
        if i < len(x) - 1:
            dx, dy, dz = x[i+1] - x[i], y[i+1] - y[i], z[i+1] - z[i]
        else:
            dx, dy, dz = x[i] - x[i-1], y[i] - y[i-1], z[i] - z[i-1]
        tangent = np.array([dx, dy, dz])
        tangent /= np.linalg.norm(tangent)
        
        # generate two orthogonal vectors
        normal = np.cross(tangent, [0, 0, 1])
        if np.linalg.norm(normal) == 0:
            normal = np.cross(tangent, [0, 1, 0])
        normal /= np.linalg.norm(normal)
        binormal = np.cross(tangent, normal)
        binormal /= np.linalg.norm(binormal)
        
        # build the ring
        phi = np.linspace(0, 2 * np.pi, n_circle)
        circle_x = tube_radius * np.cos(phi)
        circle_y = tube_radius * np.sin(phi)
        
        ring_x = x[i] + circle_x * normal[0] + circle_y * binormal[0]
        ring_y = y[i] + circle_x * normal[1] + circle_y * binormal[1]
        ring_z = z[i] + circle_x * normal[2] + circle_y * binormal[2]
        
        tube_x.append(ring_x)
        tube_y.append(ring_y)
        tube_z.append(ring_z)
    
    return tube_x, tube_y, tube_z

def build_knot_figure(x, y, z, tube_x, tube_y, tube_z, show_tube=True, show_centerline=True, 
                     quiver_point=None, quiver_tangent=None):
    """Build Plotly figure with knot visualization."""
    fig = go.Figure()
    
    # Add tube surface
    if show_tube and tube_x:
        # Create mesh for tube surface
        n_points = len(x)
        n_circle = len(tube_x[0])
        
        # Flatten tube coordinates for mesh
        X = np.array(tube_x).flatten()
        Y = np.array(tube_y).flatten()
        Z = np.array(tube_z).flatten()
        
        # Create indices for mesh
        i_indices = []
        j_indices = []
        k_indices = []
        
        for i in range(n_points - 1):
            for j in range(n_circle - 1):
                base_idx = i * n_circle + j
                i_indices.extend([base_idx, base_idx + 1, base_idx + n_circle])
                j_indices.extend([base_idx + 1, base_idx + n_circle, base_idx + n_circle + 1])
                k_indices.extend([base_idx + n_circle, base_idx + n_circle + 1, base_idx])
        
        # Add mesh surface
        fig.add_trace(go.Mesh3d(
            x=X, y=Y, z=Z,
            i=i_indices, j=j_indices, k=k_indices,
            color='lightblue',
            opacity=0.6,
            name='Vortex Core Tube'
        ))
    
    # Add centerline
    if show_centerline:
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines',
            name='Knot Centerline',
            line=dict(color='darkblue', width=3)
        ))
    
    # Add quiver (tangential velocity vector)
    if quiver_point and quiver_tangent is not None:
        scale = 1.0
        fig.add_trace(go.Cone(
            x=[quiver_point[0]],
            y=[quiver_point[1]],
            z=[quiver_point[2]],
            u=[quiver_tangent[0] * scale],
            v=[quiver_tangent[1] * scale],
            w=[quiver_tangent[2] * scale],
            sizemode="absolute",
            sizeref=0.5,
            anchor="tail",
            colorscale=[[0, 'crimson'], [1, 'crimson']],
            showscale=False,
            name='Tangential Velocity C_e'
        ))
    
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-4, 4], title="x"),
            yaxis=dict(range=[-4, 4], title="y"),
            zaxis=dict(range=[-2.5, 2.5], title="z"),
            aspectmode='cube',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            )
        ),
        title="Trefoil Knot with Physical Vortex Core (radius r_c)",
        width=None,  # Use container width
        height=800,  # Fixed height to fill viewport
        autosize=True
    )
    return fig

def st_app():
    """Streamlit app for Trefoil Knot visualization."""
    st.title("Trefoil Knot with Vortex Core")
    st.caption("3D visualization of a trefoil knot with tangential velocity vector")
    
    # Sidebar controls
    with st.sidebar:
        st.header("Controls")
        
        n_points = st.slider("Number of points", 100, 500, 300, 50)
        tube_radius = st.slider("Tube radius", 0.1, 0.8, 0.3, 0.05)
        n_circle = st.slider("Circle resolution", 8, 24, 12, 2)
        
        show_tube = st.checkbox("Show tube surface", value=True)
        show_centerline = st.checkbox("Show centerline", value=True)
        show_quiver = st.checkbox("Show tangential velocity", value=True)
    
    # Generate knot
    x, y, z = generate_trefoil_knot(n_points)
    
    # Generate tube surface
    tube_x, tube_y, tube_z = generate_tube_surface(x, y, z, tube_radius, n_circle)
    
    # Calculate quiver point and tangent
    quiver_point = None
    quiver_tangent = None
    if show_quiver:
        quiver_pos = len(x) // 2  # mid point
        if quiver_pos < len(x) - 1:
            dx, dy, dz = x[quiver_pos+1] - x[quiver_pos], y[quiver_pos+1] - y[quiver_pos], z[quiver_pos+1] - z[quiver_pos]
        else:
            dx, dy, dz = x[quiver_pos] - x[quiver_pos-1], y[quiver_pos] - y[quiver_pos-1], z[quiver_pos] - z[quiver_pos-1]
        tangent = np.array([dx, dy, dz])
        tangent /= np.linalg.norm(tangent)
        quiver_point = (x[quiver_pos], y[quiver_pos], z[quiver_pos])
        quiver_tangent = tangent
    
    # Build and display figure
    fig = build_knot_figure(x, y, z, tube_x, tube_y, tube_z, 
                           show_tube=show_tube, show_centerline=show_centerline,
                           quiver_point=quiver_point, quiver_tangent=quiver_tangent)
    st.plotly_chart(fig, width='stretch')
    
    # Display info
    st.info("💡 The trefoil knot represents a vortex core in Swirl-String Theory. The tangential velocity vector C_e indicates the swirl direction.")

if __name__ == "__main__":
    try:
        st.set_page_config(page_title="Fat Knots 3D", layout="wide")
    except:
        pass
    st_app()