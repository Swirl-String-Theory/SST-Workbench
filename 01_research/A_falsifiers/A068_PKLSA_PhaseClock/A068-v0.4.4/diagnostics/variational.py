"""Independent A068 development instrumentation (NOT official frozen science).

Compares the exact derivative of A068's trilinear particle interpolator
with divergence-free Fourier interpolation of the *same* Euler field.
Integrates F'=grad(u)(X,t) F in synchrony with the true Euler RK4 stages.
"""
from __future__ import annotations
import numpy as np

TWO_PI = 2 * np.pi


def trilinear_value_jacobian(grid, U, X):
    """Value, spatial Jacobian of actual A068 periodic trilinear interpolant.

    U[a,i,j,k], grad[a,b,p] = derivative of vector component a wrt x_b.
    For this interpolant trace(grad) need not vanish between grid nodes.
    """
    pts = np.asarray(X, dtype=np.float64).reshape(-1, 3)
    n = grid.n
    cell = (pts % TWO_PI) / grid.dx - 0.5
    base_float = np.floor(cell)
    frac = cell - base_float
    base = base_float.astype(np.int64)
    val = np.zeros((len(pts), 3), dtype=np.float64)
    J = np.zeros((len(pts), 3, 3), dtype=np.float64)
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                bits = (a, b, c)
                i = (base[:, 0] + a) % n
                j = (base[:, 1] + b) % n
                k = (base[:, 2] + c) % n
                v = U[:, i, j, k].T
                w = [frac[:, ax] if bit else 1 - frac[:, ax] for ax, bit in enumerate(bits)]
                prod = w[0] * w[1] * w[2]
                val += v * prod[:, None]
                for ax in range(3):
                    deriv = (1.0 if bits[ax] else -1.0) / grid.dx
                    others = np.ones(len(pts))
                    for other in range(3):
                        if other != ax: others *= w[other]
                    J[:, :, ax] += v * (deriv * others)[:, None]
    return val.reshape(np.shape(X)), J.reshape(np.shape(X)[:-1] + (3, 3))


def spectral_value_jacobian(grid, U, X, chunk=32):
    """Exact Fourier evaluation of the finite Galerkin state at particle locations.

    Cell centers at (j+1/2)*dx; unlike trilinear interpolation, the
    reconstructed velocity is divergence free up to roundoff everywhere.
    """
    pts = np.asarray(X, dtype=np.float64).reshape(-1, 3)
    f = np.fft.fftn(np.asarray(U), axes=(-3, -2, -1)).reshape(3, -1) / grid.n**3
    kk = grid.k.reshape(3, -1)
    f = f * grid.mask.reshape(1, -1)
    out = np.empty((len(pts), 3)); grad = np.empty((len(pts), 3, 3))
    # FFT of cell-centered samples: phase exp(i k (x - dx/2)).
    for start in range(0, len(pts), chunk):
        x = pts[start:start+chunk] - grid.dx / 2
        exponential = np.exp(1j * (x @ kk))
        out[start:start+chunk] = np.real(exponential @ f.T)
        for a in range(3):
            for b in range(3):
                grad[start:start+chunk, a, b] = np.real(exponential @ (1j * kk[b] * f[a]))
    return out.reshape(np.shape(X)), grad.reshape(np.shape(X)[:-1] + (3, 3))


def step_euler_points_F(grid, U, X, F, dt, sampler=spectral_value_jacobian):
    """One simultaneous RK4 step for Euler U, particle X, variational F.

    IMPORTANT: choose matching interpolator/Jacobian for X and F.
    """
    empty = np.empty((0, 3, grid.n, grid.n, grid.n), dtype=float)
    def stage(u, x, f):
        du, _ = grid.rhs(u, empty)
        v, jac = sampler(grid, u, x)
        return du, v, jac @ f
    k1, h1, j1 = stage(U, X, F)
    k2, h2, j2 = stage(U + .5*dt*k1, X + .5*dt*h1, F + .5*dt*j1)
    k3, h3, j3 = stage(U + .5*dt*k2, X + .5*dt*h2, F + .5*dt*j2)
    k4, h4, j4 = stage(U + dt*k3, X + dt*h3, F + dt*j3)
    return (grid.project(U+dt*(k1+2*k2+2*k3+k4)/6),
            X+dt*(h1+2*h2+2*h3+h4)/6,
            F+dt*(j1+2*j2+2*j3+j4)/6)


def compare_interpolators(grid, U, X):
    u_tri, G_tri = trilinear_value_jacobian(grid, U, X)
    u_fft, G_fft = spectral_value_jacobian(grid, U, X)
    return {
        'max_trilinear_divergence': float(np.max(np.abs(np.trace(G_tri, axis1=-2, axis2=-1)))),
        'max_spectral_divergence': float(np.max(np.abs(np.trace(G_fft, axis1=-2, axis2=-1)))),
        'relative_velocity_discrepancy': float(np.linalg.norm(u_tri-u_fft)/max(np.linalg.norm(u_fft),1e-30)),
        'interpretation': 'A nonzero trilinear trace measures the particle-advection velocity, not Euler grid divergence.'}


def compare_deformation_methods(grid,U,X,dt,steps,epsilon=1e-3,method='spectral'):
    """Evolve variational F AND symmetric finite-difference satellites.
    Satellite errors can be tested with epsilon halving, not assumed physical.
    """
    sampler={'spectral':spectral_value_jacobian,'trilinear':trilinear_value_jacobian}[method]
    points=np.asarray(X,dtype=float).reshape(-1,3)
    n=len(points)
    probes=np.stack([points,*[points+epsilon*np.eye(3)[j] for j in range(3)],
                           *[points-epsilon*np.eye(3)[j] for j in range(3)]],axis=1)
    F=np.broadcast_to(np.eye(3),(n,3,3)).copy()
    Ustate=np.asarray(U).copy(); Xstate=points.copy()
    history=[]
    for step in range(steps+1):
        F_sat=np.stack([(probes[:,1+j]-probes[:,4+j])/(2*epsilon) for j in range(3)],axis=-1)
        determinant=np.linalg.det(F); determinant_sat=np.linalg.det(F_sat)
        history.append({'t':float(step*dt),
            'detF_var_error_max':float(np.max(abs(determinant-1))),
            'detF_sat_error_max':float(np.max(abs(determinant_sat-1))),
            'F_sat_vs_var_rel':float(np.linalg.norm(F_sat-F)/max(np.linalg.norm(F),1e-30))})
        if step==steps:break
        # Integrate independent probe positions in same RK4 stages, including U.
        Unew,Xnew,Fnew=step_euler_points_F(grid,Ustate,Xstate,F,dt,sampler)
        # For satellites use actual RK4 Euler states from ORIGINAL Ustate.
        empty=np.empty((0,3,grid.n,grid.n,grid.n),dtype=float)
        k1,_=grid.rhs(Ustate,empty)
        k2,_=grid.rhs(Ustate+dt*k1/2,empty)
        k3,_=grid.rhs(Ustate+dt*k2/2,empty)
        def get_v(u,p):return sampler(grid,u,p)[0]
        h1=get_v(Ustate,probes)
        h2=get_v(Ustate+dt*k1/2,probes+dt*h1/2)
        h3=get_v(Ustate+dt*k2/2,probes+dt*h2/2)
        h4=get_v(Ustate+dt*k3,probes+dt*h3)
        probes=probes+dt*(h1+2*h2+2*h3+h4)/6
        Ustate,Xstate,F=Unew,Xnew,Fnew
    return {'schema':'A068-DEVELOPMENT-VARIATIONAL-v0.4.5','method':method,
        'epsilon':epsilon,'steps':steps,'dt':dt,'history':history,
        'authority':'NUMERICAL_DIAGNOSTIC_ONLY'}
