# NOTE: This code requires a desktop Python environment with matplotlib and numpy installed.
# To install dependencies: pip install matplotlib numpy


import matplotlib
matplotlib.use("TkAgg")
# NOTE: This code requires a desktop Python environment with matplotlib and numpy installed.
# To install dependencies: pip install matplotlib numpy
# NOTE: This code requires a desktop Python environment with matplotlib and numpy installed.
# To install dependencies: pip install matplotlib numpy

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.widgets import Slider, CheckButtons
from scipy.constants import mu_0

fig = plt.figure(figsize=(12, 8))
plt.subplots_adjust(left=0.05, bottom=0.25, right=0.95, top=0.95)
ax = fig.add_subplot(111, projection='3d')

# === Dipole Ring Generator ===
# Using correct Halbach orientation from HalBach_magneticCircle.py
# Toroid/Poloid apply additional rotations for visualization
def generate_ring(num_magnets, radius, toroidal_degrees, poloidal_degrees, invert=False):
    positions = []
    orientations = []
    for i in range(num_magnets):
        phi = 2 * np.pi * i / num_magnets
        x, y, z = radius * np.cos(phi), radius * np.sin(phi), 0.0
        positions.append(np.array([x, y, z]))

        # Correct Halbach orientation formula (from magneticCircle.py)
        mx_base = np.cos(2 * phi)
        my_base = np.sin(2 * phi)
        
        # Poloidal tilt: varies linearly from arrow 0 to arrow N/2
        # When poloid=0: flat in xy plane (angle = 0°)
        # When poloid=90: arrow 0 points parallel to +z (90°), arrow N/2 points parallel to -z (-90°)
        if poloidal_degrees == 0:
            # Flat in xy plane
            mx = mx_base
            my = my_base
            mz = 0.0
        else:
            # Linear factor: +1 at i=0, -1 at i=N/2, +1 at i=N
            if i <= num_magnets / 2:
                # Linear from +1 to -1
                poloidal_factor = 1.0 - 2.0 * i / (num_magnets / 2)  # +1 to -1
            else:
                # Linear from -1 back to +1
                poloidal_factor = -1.0 + 2.0 * (i - num_magnets / 2) / (num_magnets / 2)  # -1 to +1
            
            # Convert poloid degrees to tilt angle
            # poloidal_factor * poloidal_degrees gives the angle for this arrow
            tilt_angle_deg = poloidal_factor * poloidal_degrees
            tilt_angle_rad = np.deg2rad(tilt_angle_deg)
            
            # Construct vector with correct tilt angle from xy plane
            # If angle from xy plane is θ, then:
            # - xy magnitude should be cos(θ) of total magnitude
            # - z component should be sin(θ) of total magnitude
            xy_magnitude = np.sqrt(mx_base**2 + my_base**2)
            if xy_magnitude > 1e-10:
                # Scale xy components by cos(θ) and set z = sin(θ)
                scale_xy = np.cos(tilt_angle_rad)
                mx = mx_base * scale_xy
                my = my_base * scale_xy
                mz = np.sin(tilt_angle_rad)
            else:
                # Edge case: if xy components are zero, just set z
                mx = 0.0
                my = 0.0
                mz = np.sin(tilt_angle_rad)
        
        m = np.array([mx, my, (-1 if invert else 1) * mz])
        m /= np.linalg.norm(m) if np.linalg.norm(m) > 1e-10 else np.array([0, 0, 1 if mz > 0 else -1])
        
        # Apply optional toroidal rotation for visualization
        if toroidal_degrees != 0:
            toroidal_angle = np.deg2rad(toroidal_degrees) * i / num_magnets
            # Rotate around z-axis (toroidal) - rotates in xy plane
            cos_t = np.cos(toroidal_angle)
            sin_t = np.sin(toroidal_angle)
            rot_z = np.array([[cos_t, -sin_t, 0], [sin_t, cos_t, 0], [0, 0, 1]])
            m = rot_z @ m
        
        m /= np.linalg.norm(m)  # Renormalize after rotations
        orientations.append(m)
    return positions, orientations

# === Cube Rendering ===
def draw_correctly_aligned_cube(ax, center, direction, size=0.3, north_color='white', south_color='black', side_color='red'):
    direction = direction / np.linalg.norm(direction)
    # z_axis points in the direction of the arrow (front of cube)
    z_axis = direction
    x_axis = np.cross(z_axis, [0, 0, 1]) if np.linalg.norm(np.cross(z_axis, [0, 0, 1])) > 1e-6 else np.cross(z_axis, [0, 1, 0])
    x_axis /= np.linalg.norm(x_axis)
    y_axis = np.cross(z_axis, x_axis)
    
    R = np.stack([x_axis, y_axis, z_axis], axis=1)

    d = size / 2
    cube_verts = np.array([[x, y, z] for x in [-d, d] for y in [-d, d] for z in [-d, d]])
    
    # Rotate cube 90 degrees clockwise around y-axis in local coordinates
    # CW around y: x' = -z, z' = x, y' = y
    angle_90_cw = -np.pi / 2  # Negative for clockwise
    rot_local = np.array([
        [np.cos(angle_90_cw),  0, np.sin(angle_90_cw)],
        [0,                    1, 0],
        [-np.sin(angle_90_cw), 0, np.cos(angle_90_cw)]
    ])
    cube_verts = cube_verts @ rot_local.T  # Rotate in local coordinates
    cube_verts = cube_verts @ R.T + center  # Then apply orientation
    faces = [[0, 1, 3, 2], [4, 5, 7, 6], [0, 1, 5, 4],
             [2, 3, 7, 6], [1, 3, 7, 5], [0, 2, 6, 4]]
    # Local normals in cube's coordinate system
    # [0, 0, 1] points in +z (front), [0, 0, -1] points in -z (back)
    local_normals = np.array([[0, 0, -1], [0, 0, 1], [0, -1, 0],
                              [0, 1, 0], [1, 0, 0], [-1, 0, 0]])
    world_normals = local_normals @ R.T
    # Find face pointing in arrow direction (front = white) and opposite (back = black)
    dots = np.dot(world_normals, direction)
    front_idx = np.argmax(dots)  # Face pointing in arrow direction (white/front)
    back_idx = np.argmin(dots)   # Face pointing opposite to arrow (black/back)
    poly3d = [[cube_verts[idx] for idx in face] for face in faces]
    # White face at front (arrow direction), black face at back
    face_colors_map = [north_color if i == front_idx else south_color if i == back_idx else side_color for i in range(6)]
    ax.add_collection3d(Poly3DCollection(poly3d, facecolors=face_colors_map, edgecolors='k'))

# === Interactive Plot ===
def update_plot(num_magnets, radius, toroidal_deg, poloidal_deg):
    ax.cla()
    ax.set_title(f"Dipole Ring: {num_magnets} magnets")

    positions, orientations = generate_ring(num_magnets, radius, toroidal_deg, poloidal_deg)
    winding_colors = np.linspace(0, 1, num_magnets, endpoint=False)

    for pos, ori, c in zip(positions, orientations, winding_colors):
        if show_cubes[0]:
            # Cube centered at position, aligned with orientation
            draw_correctly_aligned_cube(ax, pos, ori, size=cube_size[0])
        if show_arrows[0]:
            # Arrow offset and length scale with size (matching magneticCircle.py proportions)
            arrow_length = cube_size[0] * 2.0  # Arrow is 2x the cube size
            arrow_offset = arrow_length * 0.5  # Offset is half the arrow length (same as 0.3 in magneticCircle.py for 0.6 arrow)
            start = pos - ori * arrow_offset
            ax.quiver(*start, *ori, length=arrow_length, color=plt.cm.hsv(c), linewidth=2, arrow_length_ratio=0.25, normalize=False)

    ax.set_xlim(-2.5, 2.5)
    ax.set_ylim(-2.5, 2.5)
    ax.set_zlim(-2, 2)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_box_aspect([1, 1, 1])
    fig.canvas.draw_idle()

# Initial parameters
num_magnets_0 = 16
radius_0 = 1.5
toroid_0 = 720  # Additional toroidal rotation (720 = default)
poloid_0 = 0    # Additional poloidal rotation (0 = flat in xy plane)
show_cubes = [True]
show_arrows = [True]
cube_size = [0.3]

update_plot(num_magnets_0, radius_0, toroid_0, poloid_0)

# Slider axes - positioned horizontally at the bottom
axcolor = 'lightgoldenrodyellow'
slider_width = 0.12
slider_height = 0.03
slider_spacing = 0.14
bottom_margin = 0.15
left_start = 0.1

ax_num = plt.axes([left_start + 0*slider_spacing, bottom_margin, slider_width, slider_height], facecolor=axcolor)
ax_rad = plt.axes([left_start + 1*slider_spacing, bottom_margin, slider_width, slider_height], facecolor=axcolor)
ax_toroid = plt.axes([left_start + 2*slider_spacing, bottom_margin, slider_width, slider_height], facecolor=axcolor)
ax_poloid = plt.axes([left_start + 3*slider_spacing, bottom_margin, slider_width, slider_height], facecolor=axcolor)
ax_size = plt.axes([left_start + 4*slider_spacing, bottom_margin, slider_width, slider_height], facecolor=axcolor)
ax_checks = plt.axes([left_start + 5*slider_spacing, bottom_margin, 0.1, 0.08], facecolor='lightgrey')

# Sliders - horizontal orientation (default)
s_num = Slider(ax_num, 'Magnets', 2, 64, valinit=num_magnets_0, valstep=1)
s_rad = Slider(ax_rad, 'Radius', 0.5, 5.0, valinit=radius_0, valstep=0.1)
s_toroid = Slider(ax_toroid, 'Toroid (°)', 0, 1440, valinit=toroid_0, valstep=90)
s_poloid = Slider(ax_poloid, 'Poloid (°)', 0, 720, valinit=poloid_0, valstep=15)
s_size = Slider(ax_size, 'Size', 0.1, 0.8, valinit=cube_size[0], valstep=0.05)

checks = CheckButtons(ax_checks, ['Show Cubes', 'Show Arrows'], [True, True])

# Update callback
def slider_update(val):
    cube_size[0] = s_size.val
    update_plot(int(s_num.val), s_rad.val, s_toroid.val, s_poloid.val)

def check_update(label):
    if label == 'Show Cubes':
        show_cubes[0] = not show_cubes[0]
    elif label == 'Show Arrows':
        show_arrows[0] = not show_arrows[0]
    update_plot(int(s_num.val), s_rad.val, s_toroid.val, s_poloid.val)

s_num.on_changed(slider_update)
s_rad.on_changed(slider_update)
s_toroid.on_changed(slider_update)
s_poloid.on_changed(slider_update)
s_size.on_changed(slider_update)
checks.on_clicked(check_update)

plt.show()
