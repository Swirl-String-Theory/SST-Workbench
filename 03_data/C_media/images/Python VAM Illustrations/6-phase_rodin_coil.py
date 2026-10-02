import matplotlib
matplotlib.use('TkAgg')  # Ensure it uses Tkinter backend
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

D_target = 9.0                # target OUTER diameter in your plot units

# Function to generate 3-phase shifted windings
def generate_rodin_3phase(R, r, num_turns=5, num_points=1000):
    """
    Generate 3-phase interwoven Rodin coil windings.

    Returns:
    Three sets of x, y, z coordinates corresponding to phase shifts of 120° each.
    """

    # Apply 120-degree phase shifts
    theta_shift = 2 * np.pi / 3
    theta = np.linspace(0, num_turns * 2 * np.pi, num_points)
    phi = (2 + 2 / 5) * theta  # Adjusted winding ratio for Rodin pattern

    x1 = (R + r * np.cos(phi)) * np.cos(theta)
    y1 = (R + r * np.cos(phi)) * np.sin(theta)
    z1 = r * np.sin(phi)

    x2 = (R + r * np.cos(phi + theta_shift)) * np.cos(theta + theta_shift)
    y2 = (R + r * np.cos(phi + theta_shift)) * np.sin(theta + theta_shift)
    z2 = r * np.sin(phi + theta_shift)

    x3 = (R + r * np.cos(phi - theta_shift)) * np.cos(theta - theta_shift)
    y3 = (R + r * np.cos(phi - theta_shift)) * np.sin(theta - theta_shift)
    z3 = r * np.sin(phi - theta_shift)

    return (x1, y1, z1), (x2, y2, z2), (x3, y3, z3)



# Function to plot the Rodin coil and its variations
def plot_rodin_coil():
    # Setup 3D plot
    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_subplot(111, projection='3d')

    phi_g = (1 + np.sqrt(5)) / 2  # golden ratio

    R = D_target / (2 * phi_g)    # ensures 2*(R + R/phi_g) = D_target
    r = R / phi_g

    colors1 = ['crimson', 'darkred', 'gold']
    colors2 = ['dodgerblue', 'navy', 'darkorange']

    # Plot 3-phase Rodin coil windings
    (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = generate_rodin_3phase(R, r)
    ax.plot(x1, y1, z1, color=colors1[0], linewidth=2, label="Phase 1")
    ax.plot(x2, y2, z2, color=colors1[1], linewidth=2, label="Phase 2")
    ax.plot(x3, y3, z3, color=colors1[2], linewidth=2, label="Phase 3")

    # Plot 3-phase Rodin coil windings
    (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = generate_rodin_3phase(-R, r)
    ax.plot(x1, y1, z1, color=colors2[0], linewidth=2, label="Phase 1")
    ax.plot(x2, y2, z2, color=colors2[1], linewidth=2, label="Phase 2")
    ax.plot(x3, y3, z3, color=colors2[2], linewidth=2, label="Phase 3")

    # Plot the ring torus in blue with 85% transparency
    # ax.plot_surface(X_ring, Y_ring, Z_ring, rstride=5, cstride=5, color='blue', alpha=0.15, edgecolor='k')

    # Plot the horn torus in red with 90% transparency
    # ax.plot_surface(X_horn, Y_horn, Z_horn, rstride=5, cstride=5, color='red', alpha=0.10, edgecolor='k')

    # Plot toroidal frame
    theta = 5* np.linspace(0, 2 * np.pi, 100)
    phi = 12* np.linspace(0, 2 * np.pi, 100)
    theta, phi = np.meshgrid(theta, phi)

    X = (R + r * np.cos(phi)) * np.cos(theta)
    Y = (R + r * np.cos(phi)) * np.sin(theta)
    Z = r * np.sin(phi)

    ax.plot_wireframe(X, Y, Z, color='gray', alpha=0.2, linewidth=0.5)


    # Set plot labels
    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')
    ax.set_zlabel('Z-axis')
    ax.set_title("Optimized 3-Phase Rodin Coil")

    # Set equal aspect ratio
    lim = D_target / 2
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(-lim, lim)
    ax.set_box_aspect([1, 1, 1])

    ax.legend()
    # ✅ Get the script filename dynamically
    import os
    from datetime import datetime
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"{script_name}_{timestamp}.png"
    plt.savefig(filename, dpi=150)  # Save image with high resolution
    plt.show()

# Generate and plot the optimized Rodin coil
plot_rodin_coil()