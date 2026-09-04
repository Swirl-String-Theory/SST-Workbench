# Final retry to generate and store the foliation diagram image
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Foliation planes
z_vals = np.linspace(0, 10, 6)
x = np.linspace(-5, 5, 10)
y = np.linspace(-5, 5, 10)
X, Y = np.meshgrid(x, y)
for z in z_vals:
    Z = np.full_like(X, z)
    ax.plot_surface(X, Y, Z, color='lightgray', alpha=0.3)

# Timelike flow u^μ
grid_density = 5
x = np.linspace(-4, 4, grid_density)
y = np.linspace(-4, 4, grid_density)
X, Y = np.meshgrid(x, y)
Z = np.zeros_like(X)
U = np.zeros_like(X)
V = np.zeros_like(Y)
W = np.ones_like(Z)
ax.quiver(X, Y, Z, U, V, W, length=1.2, normalize=True, color='blue', alpha=0.6)

# Projection vector
ax.quiver(0, 0, 0, 0, 0, 1.2, color='blue', linewidth=2)
ax.quiver(0, 0, 1.2, 1, 0, 0, color='green', linewidth=2)
ax.text(0.2, 0, 2.0, r"$h^\mu_{\ \nu}$", fontsize=12, color='green')

# Axis config
ax.set_title("Preferred Foliation in SST: Time Vector and Spatial Leaves", fontsize=13)
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_zlabel("t (Absolute Time)")
ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
ax.set_zlim(0, 10)
ax.view_init(elev=30, azim=30)

# Export
file_path = "figs/sst_foliation_diagram.png"
plt.tight_layout()
plt.savefig(file_path)
plt.close()


