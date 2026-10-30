"""Free 2N-DOF normal-graph, gauge-fixed Jacobian-free Newton--Krylov.

NOT an exact-continuum-equilibrium proof. All values in Ruban's R0=1,
Gamma=2*pi model units. Uses the independent v0.2.11 high_order.field.

Tangential reparameterization is removed by a fixed normal-graph slice plus
projection on the *current* tangent. Axial translation/rotation are phase-pinned
by two independent gauge constraints. U and Omega are solved simultaneously.
The physical field is NOT modified by the trust region or preconditioner.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np
from scipy.sparse.linalg import LinearOperator, gmres
from .core import GAMMA, DELTA, derivative, torus
from .high_order import field as ruban_field, validate
from .full_spectrum import normal_frame


class InvalidCurve(ValueError):
    pass


def axial_spin(x):
    return np.column_stack((-x[:, 1], x[:, 0], np.zeros(len(x))))


@dataclass
class GaugeSlice:
    reference: np.ndarray
    normal1: np.ndarray
    normal2: np.ndarray
    phase_orthobasis: np.ndarray

    @classmethod
    def from_reference(cls, reference):
        x, _ = validate(reference)
        a, b = normal_frame(x)
        ez = np.tile([0., 0., 1.], (len(x), 1))
        symmetry = [ez, axial_spin(x)]
        cols = []
        for s in symmetry:
            w = np.column_stack((np.sum(a*s, axis=1), np.sum(b*s, axis=1))).reshape(-1)
            cols.append(w)
        q, r = np.linalg.qr(np.column_stack(cols), mode='reduced')
        if np.min(np.abs(np.diag(r))) < 1e-5:
            raise ValueError('Phase gauge rank deficient for reference geometry')
        return cls(np.array(x,copy=True), a,b,q)

    @property
    def n(self): return len(self.reference)

    def coordinates(self, y):
        y = np.asarray(y, dtype=float)
        if y.shape != (2*self.n+2,) or not np.isfinite(y).all():
            raise InvalidCurve('Invalid free normal coordinate vector')
        z = y[:-2].reshape(self.n, 2)
        return self.reference + z[:,0,None]*self.normal1 + z[:,1,None]*self.normal2

    def phase(self,y):
        return self.phase_orthobasis.T @ y[:-2] / np.sqrt(self.n)

    def y0(self, initial_U=0., initial_Omega=0.):
        v=np.zeros(2*self.n+2)
        v[-2:] = [initial_U/GAMMA,initial_Omega/GAMMA]
        return v


def geometric_quality(x, *, delta=DELTA, sample_stride=1):
    d=derivative(x)
    speed=np.linalg.norm(d,axis=1)
    edges=np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)
    return {'min_speed':float(np.min(speed)),
            'max_segment_over_delta':float(np.max(edges)/delta),
            'min_segment_over_delta':float(np.min(edges)/delta),
            'segment_ratio':float(np.max(edges)/np.min(edges)),
            'max_radius':float(np.max(np.linalg.norm(x,axis=1))),
            'min_cylindrical_radius':float(np.min(np.linalg.norm(x[:,:2],axis=1))),
            'length':float(np.sum(speed)*2*np.pi/len(x))}


def eval_system(gauge:GaugeSlice,y,*,scheme='trapezoid',delta=DELTA,velocity_function=None,
                min_speed=1e-5, max_displacement=.55):
    x=gauge.coordinates(y)
    if float(np.max(np.linalg.norm(x-gauge.reference,axis=1)))>max_displacement:
        raise InvalidCurve('Exceeded trust chart: normal displacement too large')
    d=derivative(x);spd=np.linalg.norm(d,axis=1)
    if np.min(spd)<min_speed:raise InvalidCurve('Degenerate parameterization')
    t=d/spd[:,None]
    v = ruban_field(x,scheme=scheme,delta=delta) if velocity_function is None else velocity_function(x)
    if not np.isfinite(v).all():raise InvalidCurve('Invalid field')
    ez=np.array([0.,0.,1.]); U,Om=y[-2:]*GAMMA
    g=v-U*ez-Om*axial_spin(x)
    # subtract tangential material reparameterization, leaving normal physics
    g=g-np.sum(g*t,axis=1)[:,None]*t
    # reference-frame normal components of a CURRENT normal physical residual
    s=np.sqrt(spd/np.mean(spd))
    c=np.column_stack((np.sum(g*gauge.normal1,axis=1),
                       np.sum(g*gauge.normal2,axis=1)))
    F=np.r_[(c*s[:,None]/GAMMA).reshape(-1),gauge.phase(y)]
    # Independent gauge-invariant physical norm, not just optimization merit.
    eps=float(np.sqrt(np.sum(spd*np.sum(g*g,axis=1))/np.sum(spd))/GAMMA)
    return F,{'epsilon':eps,'U':float(U),'Omega':float(Om),
              'gauge_norm':float(np.linalg.norm(gauge.phase(y))),
              'shape_residual_rms_components':float(np.linalg.norm(F[:-2])/np.sqrt(gauge.n)),
              'geometry':geometric_quality(x,delta=delta)}


def fit_speeds(gauge, x, *,scheme='trapezoid',delta=DELTA):
    from .high_order import residual
    r=residual(x,scheme=scheme,delta=delta)
    return r['U'],r['Omega']


def jvp(gauge,y,vec, *,f0=None, fd_step=1e-6, scheme='trapezoid',delta=DELTA,velocity_function=None):
    norm=float(np.linalg.norm(vec))
    if norm<=1e-15:return np.zeros_like(y)
    # Differentiate all 2N shape coordinates and both symmetry velocities.
    # Perturbations scale by vector norm, avoiding coordinate-count scaling.
    h=fd_step*(1.0+float(np.linalg.norm(y))/np.sqrt(len(y)))/norm
    if f0 is None:f0=eval_system(gauge,y,scheme=scheme,delta=delta,velocity_function=velocity_function)[0]
    return (eval_system(gauge,y+h*vec,scheme=scheme,delta=delta,velocity_function=velocity_function)[0]-f0)/h


def solve(reference, *,max_newton=6, gmres_restart=28, gmres_cycles=2,
          krylov_rtol=.035, fd_step=2e-6, initial=None, scheme='trapezoid',
          delta=DELTA, objective_tolerance=1e-6, max_displacement=.55,
          preconditioner_strength=.008,velocity_function=None,verbose=False):
    """Square 2N+2 system: 2N normal equations + 2 axial phase gauges.

    `gmres_cycles` sets SciPy restart cycles (not Krylov dimension).
    No false equilibrium certificate is issued even at finite-N tolerance.
    """
    gauge=GaugeSlice.from_reference(reference)
    n=gauge.n
    if not(0<delta and 0<fd_step<1e-2 and 0<krylov_rtol<1):raise ValueError('Bad solver parameters')
    if max_newton<1:raise ValueError('Need Newton iterations')
    if initial is None:
        y=gauge.y0(*fit_speeds(gauge,gauge.reference,scheme=scheme,delta=delta))
    else:
        y=np.asarray(initial,dtype=float).copy()
        gauge.coordinates(y)
    history=[];status='MAX_NEWTON'; prev_merit=None
    # Right preconditioner: smoothed node displacement, free physical equations unchanged.
    w=np.fft.fftfreq(n,d=1/n)
    smooth=1/(1+preconditioner_strength*w*w)
    def precondition(vec):
        a=vec[:-2].reshape(n,2)
        a=np.fft.ifft(np.fft.fft(a,axis=0)*smooth[:,None],axis=0).real
        return np.r_[a.ravel(),vec[-2:]]
    for it in range(max_newton+1):
        try:
            f,meta=eval_system(gauge,y,scheme=scheme,delta=delta,max_displacement=max_displacement,velocity_function=velocity_function)
        except (InvalidCurve,ValueError,RuntimeError,FloatingPointError) as exc:
            status='INVALID_GEOMETRY';history.append({'iteration':it,'error':str(exc)});break
        merit=float(np.linalg.norm(f)/np.sqrt(n))
        history.append({'iteration':it,'merit':merit,'epsilon':meta['epsilon'],
                        'gauge_norm':meta['gauge_norm'],'U':meta['U'],'Omega':meta['Omega'],
                        'max_displacement':float(np.max(np.linalg.norm(gauge.coordinates(y)-reference,axis=1)))})
        if verbose:print(f'  Newton {it}: merit={merit:.7g}, eps={meta["epsilon"]:.7g}',flush=True)
        if meta['epsilon']<objective_tolerance and meta['gauge_norm']<objective_tolerance:
            status='FINITE_N_CANDIDATE';break
        if it==max_newton:break
        def mv(v):
            z=precondition(v)
            return jvp(gauge,y,z,f0=f,fd_step=fd_step,scheme=scheme,delta=delta,velocity_function=velocity_function)
        op=LinearOperator((len(y),len(y)),matvec=mv,dtype=float)
        gmres_residual=[]
        try:
            rhs=-f
            z,info=gmres(op,rhs,rtol=krylov_rtol,atol=0.,restart=gmres_restart,
                         maxiter=gmres_cycles,callback=lambda val:gmres_residual.append(float(val)),callback_type='pr_norm')
        except (InvalidCurve,ValueError,FloatingPointError) as exc:
            status='KRYLOV_INVALID_JVP';history[-1]['error']=str(exc);break
        direction=precondition(z)
        history[-1]['gmres_info']=int(info)
        history[-1]['gmres_iterations']=len(gmres_residual)
        history[-1]['gmres_residual_final']=gmres_residual[-1] if gmres_residual else None
        if not np.isfinite(direction).all() or np.linalg.norm(direction)>1e5:
            status='NONFINITE_OR_UNBOUNDED_STEP';break
        accepted=False
        for ls in range(14):
            a=2.0**(-ls)
            trial=y+a*direction
            try:
                ft,mt=eval_system(gauge,trial,scheme=scheme,delta=delta,
                                  max_displacement=max_displacement,velocity_function=velocity_function)
                val=float(np.linalg.norm(ft)/np.sqrt(n))
            except (InvalidCurve,ValueError,RuntimeError,FloatingPointError):continue
            if val<merit*(1-1e-4*a):
                y=trial;history[-1]['line_step']=a;history[-1]['accepted_merit']=val
                accepted=True;break
        if not accepted:
            status='LINESEARCH_STALLED';break
        if prev_merit is not None and abs(prev_merit-merit)<1e-11*max(merit,1):
            status='STAGNATED';break
        prev_merit=merit
    try:
        final,summary=eval_system(gauge,y,scheme=scheme,delta=delta,max_displacement=max_displacement,velocity_function=velocity_function)
        x=gauge.coordinates(y)
    except Exception:
        final=np.full_like(y,np.nan);summary={'epsilon':math.inf,'U':math.nan,'Omega':math.nan,'gauge_norm':math.inf};x=gauge.reference
    return {'status':status, 'x':x,'y':y,'history':history,'gauge':gauge,
            'summary':summary,'final_merit':float(np.linalg.norm(final)/np.sqrt(n)),
            'method':'normal_graph_2N_+_two_axial_phases_Newton_Krylov',
            'physical_stability':'UNRESOLVED','exact_equilibrium_proven':False}


def prolongate(gauge_old, y_old, reference_new):
    """Spectrally prolongate normal-graph coordinates, not raw XYZ or unrelated phases."""
    from scipy.signal import resample
    gg=GaugeSlice.from_reference(reference_new)
    old=y_old[:-2].reshape(gauge_old.n,2)
    uv=resample(old,gg.n,axis=0)
    y=np.r_[uv.reshape(-1),y_old[-2:]]
    # After resampling, enforce exact phase gauges by removing only group coordinates.
    y[:-2]-=gg.phase_orthobasis @ (gg.phase_orthobasis.T @ y[:-2])
    return gg,y
