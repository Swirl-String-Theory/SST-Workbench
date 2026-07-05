# Plotly 3D version of NeutronStarTimeDilation.py
# Converted from matplotlib to Plotly for Streamlit integration
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# Constants
C_e = 1.09384563e6        # m/s
rho_ae = 3.8934358266918687e+18  # æther density in kg/m^3
r_c = 1.40897017e-15      # m
c = 2.99792458e8          # m/s
G = 6.67430e-11           # m^3/kg/s^2

# Derived constants
gamma = G * rho_ae**2     # m^5/s^2
kappa = C_e * r_c         # m^2/s
alpha = (r_c**2) / (C_e**2)  # s^2
Omega_k = C_e / r_c       # rad/s

# Physical constants
t_p = 5.391247e-44     # Planck time [s]
M_e = 9.10938356e-31   # Electron mass [kg]
A_0 = 5.29177210903e-11 # Bohr radius [m]
h = 6.62607015e-34     # Planck's constant [J s]
pi = np.pi
mu_0 = 4 * pi * 1e-7   # Vacuum permeability [H/m]

# Redefine key constants
gamma = (C_e * c**3 * t_p**2) / (rho_ae**2 * r_c * M_e)         # m^5/s^2
kappa_1 = C_e * r_c                                             # m^2/s
kappa_2 = h / (4 * pi * M_e * A_0)                              # m^2/s
alpha_1 = C_e**2 * t_p**2 / r_c**2                              # s^2
alpha_2 = (t_p / (r_c / C_e))**2                                # s^2
alpha_3 = (2 * A_0 * r_c) / c**2                                # s^2

# Use updated gamma, kappa, and alpha from previous validation
gamma = 136.21023318101015        # m^5/s^2
kappa = 1.541195863254857e-09     # m^2/s
alpha = 1.7518097295713056e-45    # s^2
Omega_k = C_e / r_c               # rad/s

# Neutron star properties
M_sun = 1.98847e30       # kg
M_ns = 1.4 * M_sun       # kg
R_ns = 1.2e4             # m

# GR time dilation near a mass (Schwarzschild)
def time_dilation_gr(M, r):
    return np.sqrt(1 - (2 * G * M) / (r * c**2))

# Create radius range from core to several multiples of neutron star radius
radii = np.linspace(1.2e4, 1e5, 500)  # from 12 km to 100 km

# GR time dilation curve
t_gr = np.sqrt(1 - (2 * G * M_ns) / (radii * c**2))

# Æther-vortex time dilation using: t/t_inf = sqrt(1 - 2γΩ² / rc²)
# Using Ω = C_e / r
omega = C_e / radii
t_ae = np.sqrt(1 - (2 * gamma * omega**2) / (radii * c**2))
t_ae = np.where(np.isreal(t_ae), t_ae, np.nan)  # avoid NaNs

# Recompute with constant Ω
Omega_const = C_e / r_c  # constant angular velocity from core

# Time dilation from vortex model with 1/R decay
val_ae_const = 1 - (2 * gamma * Omega_const**2) / (radii * c**2)
# Add a small tolerance to avoid sqrt of tiny negative numbers due to floating-point errors
tolerance = 1e-12
t_ae_const = np.where(val_ae_const >= -tolerance, np.sqrt(np.clip(val_ae_const, 0, None)), np.nan)
t_ae_const = np.where(np.isreal(t_ae_const), t_ae_const, np.nan)

def st_app():
    """Streamlit app for Neutron Star Time Dilation visualization."""
    st.title("Time Dilation Near a Neutron Star: GR vs Æther Model")
    
    # 2D Plot
    st.subheader("2D Comparison")
    fig_2d = go.Figure()
    fig_2d.add_trace(go.Scatter(
        x=radii / 1e3,
        y=t_gr,
        mode='lines',
        name="GR Time Dilation",
        line=dict(color='black', width=2)
    ))
    fig_2d.add_trace(go.Scatter(
        x=radii / 1e3,
        y=t_ae_const,
        mode='lines',
        name="Æther Model (Const Ω)",
        line=dict(color='blue', width=2, dash='dash')
    ))
    fig_2d.update_layout(
        xaxis_title="Radius from NS center [km]",
        yaxis_title="Normalized Time Rate",
        title="Time Dilation Near a Neutron Star: GR vs Æther (Ω constant)",
        hovermode='closest',
        width=None,  # Use container width
        height=400,  # Fixed height for 2D plot
        autosize=True
    )
    st.plotly_chart(fig_2d, width='stretch')
    
    # 3D Plot
    st.subheader("3D Visualization")
    fig_3d = go.Figure()
    
    # Add both lines in separate planes to visualize them distinctly
    z_gr = np.zeros_like(radii)
    z_ae = np.ones_like(radii)
    
    fig_3d.add_trace(go.Scatter3d(
        x=radii / 1e3,
        y=t_gr,
        z=z_gr,
        mode='lines',
        name="GR Time Dilation",
        line=dict(color='black', width=4)
    ))
    fig_3d.add_trace(go.Scatter3d(
        x=radii / 1e3,
        y=t_ae_const,
        z=z_ae,
        mode='lines',
        name="Æther Model",
        line=dict(color='blue', width=4, dash='dash')
    ))
    
    fig_3d.update_layout(
        scene=dict(
            xaxis_title="Radius from NS center [km]",
            yaxis_title="Normalized Time Rate",
            zaxis_title="Model Index (0 = GR, 1 = Æther)",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            )
        ),
        title="Time Dilation Around a Neutron Star: GR vs Æther Model (3D)",
        width=None,  # Use container width
        height=800,  # Fixed height to fill viewport
        autosize=True
    )
    st.plotly_chart(fig_3d, width='stretch')
    
    # Display key values
    st.subheader("Key Values")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("GR Time Dilation at NS surface", f"{time_dilation_gr(M_ns, R_ns):.6f}")
    with col2:
        st.metric("Æther Model Time Dilation", f"{t_ae_const[0]:.6f}")

if __name__ == "__main__":
    st_app()