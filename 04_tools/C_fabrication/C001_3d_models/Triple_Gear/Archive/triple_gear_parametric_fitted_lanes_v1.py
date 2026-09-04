
import numpy as np, math, trimesh, json

# Recovered from the uploaded STL + paper parameters
scale = 20.474859961280593
Rmajor = scale
rho0 = scale * 0.3228837
theta = -0.8560281

# Similarity fit to the paper's canonical Hopf-link placement
Rot = np.array([
    [-0.4989723792009656, -0.8666178885728867,  7.146846953755606e-10],
    [ 0.8666178885728866, -0.49897237920096543, -1.0162474985210268e-09],
    [ 1.2373061447477534e-09,  1.122791182599479e-10,  1.0]
])
trans = np.array([6.959134320636191e-09, 2.18244843894799e-08, -0.033492749680358834])

U0 = np.array([1.,0.,0.])
V0 = np.array([0., math.sin(theta), math.cos(theta)])
V0 = V0 / np.linalg.norm(V0)
N0 = np.cross(U0, V0); N0 = N0 / np.linalg.norm(N0)

# Fitted tooth-lane parameters
N_teeth = 16
lane_betas = [1.2298655, -1.2298655, math.pi]
lane_phase = [0.08079530458299489, -0.1884386224703129, 0.14288275133699713]
lane_amp   = [2.6, 2.6, 2.2]    # mm
lane_sa    = [0.09, 0.09, 0.095]
lane_sb    = [0.22, 0.22, 0.20]
lane_skew  = [0.18, -0.18, 0.0]

def wrap(a):
    return (a + np.pi) % (2*np.pi) - np.pi

def tooth_bump(alpha, beta):
    d = np.zeros_like(alpha, dtype=float)
    for beta0, phase0, A, sa, sb, skew in zip(lane_betas, lane_phase, lane_amp, lane_sa, lane_sb, lane_skew):
        local = wrap(alpha - phase0)
        tooth_phase = wrap(N_teeth * local) / np.pi
        beta_c = beta0 + skew * tooth_phase
        db = wrap(beta - beta_c)
        da = wrap(N_teeth * local) / N_teeth
        bump = np.exp(-0.5 * (db / sb)**2) * np.exp(-0.5 * (da / sa)**2)
        bump = bump**1.4
        d += A * bump
    d -= 0.25*np.exp(-0.5*(wrap(beta)/0.9)**2)
    return d

def torus_component_mesh(k, n_alpha=480, n_beta=180):
    ang = k*2*np.pi/3
    Rz = np.array([[np.cos(ang), -np.sin(ang), 0],
                   [np.sin(ang),  np.cos(ang), 0],
                   [0,0,1]])
    U = Rot @ (Rz @ U0)
    V = Rot @ (Rz @ V0)
    N = Rot @ (Rz @ N0)
    C = scale * (Rot @ (Rz @ np.array([0.4950197,0,0]))) + trans

    alphas = np.linspace(-np.pi, np.pi, n_alpha, endpoint=False)
    betas = np.linspace(-np.pi, np.pi, n_beta, endpoint=False)
    A, B = np.meshgrid(alphas, betas, indexing='ij')
    rho = rho0 + tooth_bump(A, B)

    P = (C[None,None,:]
         + (Rmajor + rho*np.cos(B))[...,None] * (np.cos(A)[...,None]*U + np.sin(A)[...,None]*V)
         + (rho*np.sin(B))[...,None] * N)

    verts = P.reshape(-1,3)
    faces = []
    nb = n_beta
    for i in range(n_alpha):
        i2 = (i+1) % n_alpha
        for j in range(n_beta):
            j2 = (j+1) % n_beta
            a = i*nb + j
            b = i2*nb + j
            c = i2*nb + j2
            d = i*nb + j2
            faces.extend([[a,b,c], [a,c,d]])

    m = trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=False)
    m.update_faces(m.unique_faces())
    m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices()
    m.fix_normals()
    return m

if __name__ == "__main__":
    meshes = [torus_component_mesh(k) for k in range(3)]
    combined = trimesh.util.concatenate(meshes)
    combined.update_faces(combined.unique_faces())
    combined.update_faces(combined.nondegenerate_faces())
    combined.remove_unreferenced_vertices()
    combined.fix_normals()
    combined.export("triple_gear_parametric_fitted_lanes_v1.stl")
    combined.export("triple_gear_parametric_fitted_lanes_v1.obj")
    combined.export("triple_gear_parametric_fitted_lanes_v1.glb")
    print("Exported triple_gear_parametric_fitted_lanes_v1.[stl|obj|glb]")
