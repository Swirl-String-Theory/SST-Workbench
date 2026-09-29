import numpy as np
from .filament import filament_field

def grid_points(n, half_extent):
    h = float(half_extent)
    axis = np.linspace(-h, h, int(n), endpoint=False)
    X,Y,Z = np.meshgrid(axis,axis,axis,indexing="ij")
    pts = np.column_stack([X.ravel(),Y.ravel(),Z.ravel()])
    dx = 2.0*h/int(n)
    return axis, pts, dx

def _wavevectors(n, dx):
    k = 2.0*np.pi*np.fft.fftfreq(int(n), d=float(dx))
    # For an even real grid, the Nyquist derivative mode is self-conjugate.
    # Zeroing it keeps the spectral derivative/projection operator real-valued.
    if int(n) % 2 == 0:
        k[int(n)//2] = 0.0
    return np.meshgrid(k,k,k,indexing="ij")

def project_div_free(u, dx):
    u = np.asarray(u, float)
    n = u.shape[0]
    kx,ky,kz = _wavevectors(n, dx)
    uh = [np.fft.fftn(u[...,j]) for j in range(3)]
    k2 = kx*kx + ky*ky + kz*kz
    dot = kx*uh[0] + ky*uh[1] + kz*uh[2]
    mask = k2 > 0
    for j,kk in enumerate((kx,ky,kz)):
        corr = np.zeros_like(dot)
        corr[mask] = kk[mask]*dot[mask]/k2[mask]
        uh[j] = uh[j] - corr
    out = np.stack([np.fft.ifftn(a).real for a in uh], axis=-1)
    return out

def divergence_rms(u, dx):
    n=u.shape[0]
    kx,ky,kz=_wavevectors(n,dx)
    uh=[np.fft.fftn(u[...,j]) for j in range(3)]
    dh=1j*(kx*uh[0]+ky*uh[1]+kz*uh[2])
    div=np.fft.ifftn(dh).real
    return float(np.sqrt(np.mean(div*div)))

def gradient_rms(u, dx):
    n=u.shape[0]
    kx,ky,kz=_wavevectors(n,dx)
    acc=0.0
    for j in range(3):
        uh=np.fft.fftn(u[...,j])
        for kk in (kx,ky,kz):
            g=np.fft.ifftn(1j*kk*uh).real
            acc += float(np.mean(g*g))
    return float(np.sqrt(acc))

def normalized_velocity_on_grid(curve, n, half_extent, core, chunk):
    _, pts, dx = grid_points(n, half_extent)
    raw = filament_field(pts, curve, core, chunk=chunk)
    u = raw.reshape((n,n,n,3))
    u = project_div_free(u, dx)
    scale = np.sqrt(np.mean(np.sum(u*u, axis=-1)))
    if not np.isfinite(scale) or scale <= 0:
        raise RuntimeError("invalid field normalization")
    u = u/scale
    return u, dx

def pressure_like(u, dx):
    n=u.shape[0]
    kx,ky,kz=_wavevectors(n,dx)
    ks=(kx,ky,kz)
    grad=np.empty((3,3,n,n,n),float)
    for j in range(3):
        uh=np.fft.fftn(u[...,j])
        for i in range(3):
            grad[i,j]=np.fft.ifftn(1j*ks[i]*uh).real
    source=np.zeros((n,n,n),float)
    for i in range(3):
        for j in range(3):
            source -= grad[i,j]*grad[j,i]
    sh=np.fft.fftn(source)
    k2=kx*kx+ky*ky+kz*kz
    ph=np.zeros_like(sh)
    mask=k2>0
    ph[mask]=-sh[mask]/k2[mask]
    p=np.fft.ifftn(ph).real
    p-=p.mean()
    return p, source
