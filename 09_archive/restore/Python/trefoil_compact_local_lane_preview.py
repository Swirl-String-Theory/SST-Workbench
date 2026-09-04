import math
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

R = 15.221053514957278
r = 4.843062482031861
a = 3.459330344308472
P = 58.116749784382336
u_min = -0.45600000000000035
u_max = 0.45600000000000035
c = 0.0

def gamma(u, R, r):
    return np.array([
        (R + r*np.cos(3*u))*np.cos(2*u),
        (R + r*np.cos(3*u))*np.sin(2*u),
        r*np.sin(3*u)
    ], dtype=float)

def dgamma(u, R, r):
    return np.array([
        -3*r*np.sin(3*u)*np.cos(2*u) - 2*(R + r*np.cos(3*u))*np.sin(2*u),
        -3*r*np.sin(3*u)*np.sin(2*u) + 2*(R + r*np.cos(3*u))*np.cos(2*u),
        3*r*np.cos(3*u)
    ], dtype=float)

def ddgamma(u, R, r):
    return np.array([
        -9*r*np.cos(3*u)*np.cos(2*u) + 12*r*np.sin(3*u)*np.sin(2*u) - 4*(R + r*np.cos(3*u))*np.cos(2*u),
        -9*r*np.cos(3*u)*np.sin(2*u) - 12*r*np.sin(3*u)*np.cos(2*u) - 4*(R + r*np.cos(3*u))*np.sin(2*u),
        -9*r*np.sin(3*u)
    ], dtype=float)

def frenet_frame(u, R, r):
    g1 = dgamma(u, R, r)
    T = g1 / np.linalg.norm(g1)
    g2 = ddgamma(u, R, r)
    B = np.cross(g1, g2)
    B = B / np.linalg.norm(B)
    N = np.cross(B, T)
    return T, N, B

def X(u, beta, R, r, a):
    T, N, B = frenet_frame(u, R, r)
    return gamma(u, R, r) + a*(np.cos(beta)*N + np.sin(beta)*B)

def wrap_angle(x):
    return (x + np.pi) % (2*np.pi) - np.pi

def residual(beta, u, c, R, r, a, P):
    p = X(u, beta, R, r, a)
    phi = math.atan2(p[1], p[0]) - 2*np.pi*p[2]/P
    return wrap_angle(phi - c)

def solve_beta_local(us, beta_seed=0.0):
    betas = []
    beta = beta_seed
    for u in us:
        for _ in range(30):
            f = residual(beta, u, c, R, r, a, P)
            h = 1e-5
            df = (residual(beta + h, u, c, R, r, a, P) - residual(beta - h, u, c, R, r, a, P)) / (2*h)
            if abs(df) < 1e-10:
                break
            step = -f / df
            beta = wrap_angle(beta + step)
            if abs(step) < 1e-10:
                break
        betas.append(beta)
    return np.array(betas)

nu = 320
nb = 48
us = np.linspace(0, 2*np.pi, nu, endpoint=False)
bs = np.linspace(0, 2*np.pi, nb, endpoint=False)

surface_pts = np.array([X(u, b, R, r, a) for u in us for b in bs])
centerline = np.array([gamma(u, R, r) for u in us])

u_lane = np.linspace(u_min, u_max, 500)
beta_lane = solve_beta_local(u_lane, beta_seed=0.0)
lane_pts = np.array([X(u, b, R, r, a) for u, b in zip(u_lane, beta_lane)])

fig = plt.figure(figsize=(11, 7))
ax = fig.add_subplot(111, projection='3d')
ax.scatter(surface_pts[:, 0], surface_pts[:, 1], surface_pts[:, 2], s=0.15, alpha=0.08)
ax.plot(centerline[:, 0], centerline[:, 1], centerline[:, 2], linewidth=1.2, alpha=0.6)
ax.plot(lane_pts[:, 0], lane_pts[:, 1], lane_pts[:, 2], linewidth=3.0)

ax.set_title("Compact trefoil T(2,3) with local straight-helix-compatible lane")
ax.set_xlabel("x (mm)")
ax.set_ylabel("y (mm)")
ax.set_zlabel("z (mm)")

all_pts = np.vstack([surface_pts[::8], lane_pts])
mins = all_pts.min(axis=0)
maxs = all_pts.max(axis=0)
span = (maxs - mins).max()
mid = 0.5 * (maxs + mins)
ax.set_xlim(mid[0] - 0.55*span, mid[0] + 0.55*span)
ax.set_ylim(mid[1] - 0.55*span, mid[1] + 0.55*span)
ax.set_zlim(mid[2] - 0.55*span, mid[2] + 0.55*span)
ax.view_init(elev=24, azim=38)

plt.tight_layout()
plt.savefig("trefoil_compact_local_lane_preview.png", dpi=220)
plt.show()
