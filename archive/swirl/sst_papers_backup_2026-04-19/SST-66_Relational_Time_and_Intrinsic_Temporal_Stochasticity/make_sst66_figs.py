#!/usr/bin/env python3
"""
make_sst66_figs.py
Generate a "Neukart-style" figure set, but mapped to SST-66 (relational time via delay-selected modes
and an emergent relational clock field).

Dependencies:
  pip install numpy matplotlib networkx

Outputs:
  ./sst66_figs/fig_sst66_*.png
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
import networkx as nx

OUTDIR = Path("sst66_figs")
OUTDIR.mkdir(parents=True, exist_ok=True)

def savefig(path, dpi=220):
    plt.tight_layout()
    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close()

# ----------------------------
# Fig 01: Conceptual overview
# ----------------------------
plt.figure(figsize=(12,4))
ax = plt.gca()
ax.axis("off")

boxes = [
    (0.03, 0.25, 0.27, 0.5, "Standard QM\\nExternal parameter $t$"),
    (0.36, 0.25, 0.28, 0.5,
     "Closed-loop delay dynamics\\n$\\\\dot\\\\phi(t)=\\\\omega_0+\\\\kappa\\\\sin[\\\\phi(t-\\\\tau)-\\\\phi(t)]$"),
    (0.69, 0.25, 0.28, 0.5,
     "Relational clock field\\n$\\\\theta(x)$ and direction $T^a=\\\\partial^a\\\\theta$"),
]
for (x,y,w,h,txt) in boxes:
    rect = patches.FancyBboxPatch((x,y), w,h, boxstyle="round,pad=0.02,rounding_size=0.02",
                                  linewidth=2, edgecolor="black", facecolor="white")
    ax.add_patch(rect)
    ax.text(x+w/2, y+h/2, txt, ha="center", va="center", fontsize=14)

def arrow(x1,y1,x2,y2):
    arr = FancyArrowPatch((x1,y1),(x2,y2), arrowstyle="-|>", mutation_scale=20, linewidth=2, color="black")
    ax.add_patch(arr)

arrow(0.30,0.50,0.36,0.50)
arrow(0.64,0.50,0.69,0.50)
ax.set_title("Conceptual overview: external time → delay-selected modes → relational clock field", fontsize=18, pad=10)
savefig(OUTDIR/"fig_sst66_01_conceptual_overview.png")

# ------------------------------------------------
# Fig 02: Navigational vs chronological depiction
# ------------------------------------------------
plt.figure(figsize=(12,6))
ax = plt.gca()
ax.axis("off")

ax.text(0.5, 0.95, "Synthesis: chronological order vs navigational time", ha="center", va="top", fontsize=22)
ax.text(0.5, 0.80, "Observer trajectory (navigational time)", ha="center", va="center", fontsize=16)

xs = np.linspace(0.08, 0.92, 7)
ys = 0.65 + 0.05*np.sin(np.linspace(0, 2*np.pi, 7))
ax.plot(xs, ys, color="black", linewidth=3)
ax.scatter(xs, ys, s=220, color="#1f77b4", zorder=3)

for i in range(len(xs)-1):
    ax.annotate("", xy=(xs[i+1], ys[i+1]), xytext=(xs[i], ys[i]),
                arrowprops=dict(arrowstyle="-|>", lw=2, color="black", shrinkA=16, shrinkB=18))

rect = patches.FancyBboxPatch((0.08,0.12),0.84,0.22, boxstyle="round,pad=0.02,rounding_size=0.01",
                              linewidth=3, edgecolor="black", facecolor="white")
ax.add_patch(rect)
ax.text(0.5, 0.23,
        "Relational ordering manifold (chronological constraints)\\n"
        "(e.g., delay-consistency / phase-lock inequalities)",
        ha="center", va="center", fontsize=15)

savefig(OUTDIR/"fig_sst66_02_navigational_vs_chronological.png")

# --------------------------------------------
# Fig 03: Relational lattice with local T field
# --------------------------------------------
plt.figure(figsize=(9,9))
ax = plt.gca()
ax.set_aspect("equal")
ax.set_title("Relational lattice: nodes, adjacency, and local clock direction $T$", fontsize=18)

n = 6
xs, ys = np.meshgrid(np.arange(n), np.arange(n))
x = xs.flatten(); y = ys.flatten()

X = xs/(n-1)*2 - 1
Y = ys/(n-1)*2 - 1
theta = X + 0.3*Y + 0.8*np.exp(-(X**2+Y**2)/0.25)

dtheta_dx = np.zeros_like(theta)
dtheta_dy = np.zeros_like(theta)
dtheta_dx[:,1:-1] = (theta[:,2:]-theta[:,:-2])/2
dtheta_dx[:,0]    = theta[:,1]-theta[:,0]
dtheta_dx[:,-1]   = theta[:,-1]-theta[:,-2]
dtheta_dy[1:-1,:] = (theta[2:,:]-theta[:-2,:])/2
dtheta_dy[0,:]    = theta[1,:]-theta[0,:]
dtheta_dy[-1,:]   = theta[-1,:]-theta[-2,:]

U = dtheta_dx.flatten()
V = dtheta_dy.flatten()
norm = np.sqrt(U**2+V**2) + 1e-9
U /= norm; V /= norm

ax.scatter(x, y, s=150, color="#1f77b4", zorder=3)
ax.quiver(x, y, U, V, angles="xy", scale_units="xy", scale=2.5, width=0.006, color="black", zorder=4)

for i in range(n):
    for j in range(n):
        if j < n-1:
            ax.plot([j, j+1], [i, i], color="0.85", lw=2, zorder=1)
        if i < n-1:
            ax.plot([j, j], [i, i+1], color="0.85", lw=2, zorder=1)

loops = [
    [(1,1),(3,1),(3,3),(1,3),(1,1)],
    [(4,0),(5,0),(5,2),(4,2),(4,0)],
]
colors = ["#d62728", "#2ca02c"]
for loop, c in zip(loops, colors):
    xs_l = [p[0] for p in loop]
    ys_l = [p[1] for p in loop]
    ax.plot(xs_l, ys_l, lw=4, color=c, zorder=2)

ax.set_xlim(-0.5, n-0.5)
ax.set_ylim(-0.5, n-0.5)
ax.set_xticks([]); ax.set_yticks([])
savefig(OUTDIR/"fig_sst66_03_relational_lattice.png")

# ------------------------------------------
# Fig 04: Causal–relational coupling network
# ------------------------------------------
rng = np.random.default_rng(4)
G = nx.Graph()
A = [f"A{i}" for i in range(10)]
B = [f"B{i}" for i in range(10)]
G.add_nodes_from(A, group="A")
G.add_nodes_from(B, group="B")

for nodes in [A,B]:
    for i in range(len(nodes)):
        for j in range(i+1,len(nodes)):
            if rng.random() < 0.25:
                G.add_edge(nodes[i], nodes[j], weight=rng.uniform(0.3,1.0), kind="intra")
    for i in range(len(nodes)-1):
        G.add_edge(nodes[i], nodes[i+1], weight=1.5, kind="backbone")

for i in range(10):
    if rng.random() < 0.5:
        j = int(rng.integers(0,10))
        G.add_edge(A[i], B[j], weight=rng.uniform(0.1,0.6), kind="inter")

pos = {}
for nm in A:
    pos[nm] = np.array([-1.0,0.0]) + 0.35*rng.normal(size=2)
for nm in B:
    pos[nm] = np.array([+1.0,0.0]) + 0.35*rng.normal(size=2)

plt.figure(figsize=(9,7))
ax = plt.gca()
ax.set_title("Causal–relational coupling graph (two loop subsystems)", fontsize=18)
ax.axis("off")

for (u,v,dat) in G.edges(data=True):
    w = dat["weight"]
    col = "0.75"
    if dat.get("kind")=="backbone":
        col="0.35"
    elif dat.get("kind")=="inter":
        col="0.80"
    ax.plot([pos[u][0],pos[v][0]],[pos[u][1],pos[v][1]], color=col, lw=1.5*w, alpha=0.9, zorder=1)

for nm in A:
    ax.scatter(pos[nm][0],pos[nm][1], s=220, color="#1f77b4", edgecolor="black", zorder=2)
    ax.text(pos[nm][0],pos[nm][1]+0.06,nm, ha="center", va="bottom", fontsize=10)
for nm in B:
    ax.scatter(pos[nm][0],pos[nm][1], s=220, color="#ff7f0e", edgecolor="black", zorder=2)
    ax.text(pos[nm][0],pos[nm][1]+0.06,nm, ha="center", va="bottom", fontsize=10)

savefig(OUTDIR/"fig_sst66_04_causal_relational_graph.png")

# ----------------------------------------------
# Fig 05: Vector field topology with div & curl
# ----------------------------------------------
plt.figure(figsize=(7,7))
ax = plt.gca()
ax.set_title(r"Topology of $T$ with divergence and curl", fontsize=18)

x = np.linspace(-2.6,2.6,200)
y = np.linspace(-2.6,2.6,200)
X,Y = np.meshgrid(x,y)
U = 0.9*X - 0.6*Y
V = 0.6*X + 0.9*Y

ax.streamplot(X,Y,U,V, density=1.2, linewidth=2)
ax.set_xlim(-2.6,2.6); ax.set_ylim(-2.6,2.6)
ax.set_xticks([]); ax.set_yticks([])
savefig(OUTDIR/"fig_sst66_05_T_div_curl_stream.png")

# ---------------------------------------------------
# Fig 06: Clock potential theta with T and Laplacian
# ---------------------------------------------------
plt.figure(figsize=(9,7))
ax = plt.gca()
ax.set_title(r"Clock potential $\theta$ with $T=\nabla\theta$ and $\nabla^2\theta$", fontsize=18)

x = np.linspace(-3,3,121)
y = np.linspace(-3,3,121)
X,Y = np.meshgrid(x,y)
theta = (0.35*X + 0.10*Y
         + 2.5*np.exp(-(X**2+Y**2)/1.4)
         - 1.5*np.exp(-((X-1.5)**2+(Y+0.8)**2)/0.7))

dx = x[1]-x[0]; dy = y[1]-y[0]
dth_dx = np.gradient(theta, dx, axis=1)
dth_dy = np.gradient(theta, dy, axis=0)
lap = np.gradient(dth_dx, dx, axis=1) + np.gradient(dth_dy, dy, axis=0)

im = ax.imshow(theta, extent=[x.min(),x.max(),y.min(),y.max()], origin="lower", aspect="equal")
step = 6
ax.quiver(X[::step,::step],Y[::step,::step],dth_dx[::step,::step],dth_dy[::step,::step], color="black", scale=35)
cs = ax.contour(X,Y,lap, levels=np.linspace(lap.min()*0.7, lap.max()*0.7, 7), linewidths=2)
ax.clabel(cs, inline=True, fontsize=10)
plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label=r"$\theta$")
ax.set_xticks([]); ax.set_yticks([])
savefig(OUTDIR/"fig_sst66_06_theta_T_laplacian.png")

# -----------------------------------------
# Fig 07: Three-panel clock potential cases
# -----------------------------------------
rng = np.random.default_rng(1)
fig, axes = plt.subplots(1,3, figsize=(16,5))
titles = ["Uniform $\\theta$ (no preferred clock direction)",
          "Linear $\\theta$ gradient (aligned clock direction)",
          "Localized imprint (clock distortion)"]

n = 60
theta1 = rng.normal(size=(n,n))
x = np.linspace(0,1,n); y = np.linspace(0,1,n)
d1y, d1x = np.gradient(theta1, y[1]-y[0], x[1]-x[0])
norm = np.sqrt(d1x**2+d1y**2)+1e-9
u1 = d1x/norm; v1 = d1y/norm

axes[0].imshow(theta1, origin="lower", aspect="auto")
step = 4
axes[0].quiver(np.arange(0,n,step), np.arange(0,n,step), u1[::step,::step], v1[::step,::step], color="black", scale=25)
axes[0].set_title(titles[0], fontsize=14)
axes[0].set_xticks([]); axes[0].set_yticks([])

X,Y = np.meshgrid(x,y)
theta2 = X + 0.3*Y
d2y, d2x = np.gradient(theta2, y[1]-y[0], x[1]-x[0])
norm = np.sqrt(d2x**2+d2y**2)+1e-9
u2 = d2x/norm; v2 = d2y/norm
axes[1].imshow(theta2, origin="lower", aspect="auto")
axes[1].quiver(np.arange(0,n,step), np.arange(0,n,step), u2[::step,::step], v2[::step,::step], color="black", scale=25)
axes[1].set_title(titles[1], fontsize=14)
axes[1].set_xticks([]); axes[1].set_yticks([])

xx = np.linspace(-3,3,n); yy = np.linspace(-3,3,n)
XX,YY = np.meshgrid(xx,yy)
theta3 = 2.5*np.exp(-(XX**2+YY**2)/1.4)
d3y, d3x = np.gradient(theta3, yy[1]-yy[0], xx[1]-xx[0])
norm = np.sqrt(d3x**2+d3y**2)+1e-9
u3 = d3x/norm; v3 = d3y/norm
axes[2].imshow(theta3, extent=[-3,3,-3,3], origin="lower", aspect="auto")
axes[2].quiver(XX[::step,::step], YY[::step,::step], u3[::step,::step], v3[::step,::step], color="black", scale=20)
axes[2].set_title(titles[2], fontsize=14)
axes[2].set_xticks([]); axes[2].set_yticks([])

plt.suptitle("Clock potential examples and induced local direction field $T=\\nabla\\theta$", fontsize=18)
savefig(OUTDIR/"fig_sst66_07_three_panel_examples.png")

# -------------------------------------------------
# Fig 08: Mode ladder from the delay locking equation
# -------------------------------------------------
def roots_scan(K, z0, zmin=0.0, zmax=70.0, ngrid=6000):
    z = np.linspace(zmin, zmax, ngrid)
    f = z + K*np.sin(z) - z0
    s = np.sign(f)
    idx = np.where(s[:-1]*s[1:] < 0)[0]
    roots = []
    for i in idx:
        a,b = z[i], z[i+1]
        fa = f[i]
        lo,hi = a,b
        for _ in range(60):
            mid = (lo+hi)/2
            fm = mid + K*np.sin(mid) - z0
            if fa*fm <= 0:
                hi = mid
            else:
                lo = mid
                fa = fm
        roots.append((lo+hi)/2)
    return roots

z0 = 30.0
Ks = np.linspace(0,20,301)
roots_by_K = [roots_scan(K,z0) for K in Ks]

branches = []
for ki,K in enumerate(Ks):
    zs = roots_by_K[ki]
    st = [(1 + K*np.cos(z) > 0) for z in zs]  # proxy stability
    if ki == 0:
        for z,stable in zip(zs,st):
            branches.append([(K,z,stable)])
        continue
    assigned = [False]*len(zs)
    for b in branches:
        _, zprev, _ = b[-1]
        dmin = 1e9; jmin = None
        for j,z in enumerate(zs):
            if assigned[j]:
                continue
            d = abs(z - zprev)
            if d < dmin:
                dmin = d; jmin = j
        if jmin is not None and dmin < 0.6:
            b.append((K,zs[jmin],st[jmin]))
            assigned[jmin] = True
    for j,z in enumerate(zs):
        if not assigned[j]:
            branches.append([(K,z,st[j])])

plt.figure(figsize=(10,6))
ax = plt.gca()
ax.set_title(r"Delay-selected mode ladder: roots of $z + K\sin z = z_0$ ($z_0=\omega_0\tau$)", fontsize=14)

for b in branches:
    if len(b) < 40:
        continue
    Kb = np.array([p[0] for p in b])
    zb = np.array([p[1] for p in b])
    sb = np.array([p[2] for p in b])
    start = 0
    for i in range(1,len(b)):
        if sb[i] != sb[i-1]:
            ax.plot(Kb[start:i+1], zb[start:i+1], lw=2, linestyle="-" if sb[i-1] else "--")
            start = i
    ax.plot(Kb[start:], zb[start:], lw=2, linestyle="-" if sb[-1] else "--")

ax.set_xlabel(r"$K=\kappa\tau$")
ax.set_ylabel(r"$z=\Omega\tau$")
ax.set_xlim(Ks.min(), Ks.max())
ax.set_ylim(0, 70)
ax.grid(True, alpha=0.3)
savefig(OUTDIR/"fig_sst66_08_mode_ladder.png")

# --------------------------------------------
# Fig 09: Example temporal jitter (simulation)
# --------------------------------------------
dt = 0.01
tau = 4.0
delay_steps = int(tau/dt)
T_total = 300.0
N = int(T_total/dt)
t = np.arange(N)*dt

omega0 = 1.2
kappa = 0.9
sigma = 0.35  # rad/sqrt(s)
phi = np.zeros(N)
phi[:delay_steps+1] = omega0 * t[:delay_steps+1]

rng = np.random.default_rng(3)
for i in range(delay_steps+1, N):
    dphi = omega0 + kappa*np.sin(phi[i-delay_steps] - phi[i-1])
    phi[i] = phi[i-1] + dphi*dt + sigma*np.sqrt(dt)*rng.normal()

two_pi = 2*np.pi
cross_times = []
target = two_pi
for i in range(1,N):
    while target <= phi[i] and target > phi[i-1]:
        frac = (target - phi[i-1])/(phi[i]-phi[i-1] + 1e-12)
        cross_times.append(t[i-1] + frac*dt)
        target += two_pi

cross_times = np.array(cross_times)
intervals = np.diff(cross_times)
intervals_ss = intervals[int(len(intervals)*0.3):]  # discard transient

plt.figure(figsize=(10,6))
ax = plt.gca()
ax.set_title("Intrinsic temporal stochasticity (example): distribution of cycle intervals", fontsize=14)
ax.hist(intervals_ss, bins=50, density=True, alpha=0.7)
mu = intervals_ss.mean()
std = intervals_ss.std()
xgrid = np.linspace(mu-4*std, mu+4*std, 400)
pdf = 1/(std*np.sqrt(2*np.pi))*np.exp(-(xgrid-mu)**2/(2*std**2))
ax.plot(xgrid, pdf, lw=2)
ax.set_xlabel("Inter-event interval Δt (s)")
ax.set_ylabel("Probability density")
ax.text(0.02, 0.95,
        f"mean={mu:.3f} s\\nstd={std:.3f} s\\nτ={tau:.1f} s, κ={kappa:.2f}, σ={sigma:.2f}",
        transform=ax.transAxes, ha="left", va="top", fontsize=11,
        bbox=dict(facecolor="white", alpha=0.9, edgecolor="black"))
ax.grid(True, alpha=0.3)
savefig(OUTDIR/"fig_sst66_09_temporal_jitter.png")

print(f"Wrote figures to: {OUTDIR.resolve()}")
