import numpy as np
import matplotlib.pyplot as plt

G  = 6.67430e-11
m1 = 1.67262192369e-27   # proton mass (demo)
m2 = 9.1093837015e-31    # electron mass (demo)

L = 1e-9
N = 600
x = np.linspace(-L, L, N); y = np.linspace(-L, L, N)
X, Y = np.meshgrid(x, y)

sep = 2e-10
x1,y1 = -sep/2,0.0
x2,y2 = +sep/2,0.0
eps = 2e-12

R1 = np.sqrt((X-x1)**2 + (Y-y1)**2 + eps**2)
R2 = np.sqrt((X-x2)**2 + (Y-y2)**2 + eps**2)
chi = -G*m1/R1 - G*m2/R2

dchi_dx, dchi_dy = np.gradient(chi, x, y, edge_order=2)
gx, gy = -dchi_dx, -dchi_dy

plt.figure(figsize=(7.5,6.5))
chi_log = np.log10(np.abs(chi) + 1e-40)
plt.contourf(X*1e10, Y*1e10, chi_log, levels=40)
plt.colorbar(label=r'$\log_{10}|\chi|$ (SI)')
step=30
plt.quiver(X[::step,::step]*1e10, Y[::step,::step]*1e10,
           gx[::step,::step], gy[::step,::step], scale=1e14)
plt.scatter([x1*1e10,x2*1e10],[0,0])
plt.xlabel('x (Å)'); plt.ylabel('y (Å)')
plt.gca().set_aspect('equal','box')
plt.tight_layout()
plt.savefig("chi_slice_demo.png", dpi=200)