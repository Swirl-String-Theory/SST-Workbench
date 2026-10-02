import numpy as np


def energy_ratio_general(nvec, omega_dir, deformation):
    """
    Frozen-in Euler/Cauchy affine energy ratio for equal-energy vortical modes.

    For incompressible affine F (det F = 1):
      omega' = F omega,
      k'     = F^{-T} k.
    A transverse Fourier mode has kinetic energy proportional to |omega|^2/|k|^2.
    """
    nvec = np.asarray(nvec, dtype=float)
    omega_dir = np.asarray(omega_dir, dtype=float)
    f = np.asarray(deformation, dtype=float)
    if nvec.ndim != 2 or nvec.shape[1] != 3 or omega_dir.shape != nvec.shape:
        raise ValueError("nvec and omega_dir must have shape (N,3)")
    if f.shape != (3, 3):
        raise ValueError("deformation must have shape (3,3)")
    det = float(np.linalg.det(f))
    if abs(det - 1.0) > 1e-10:
        raise ValueError(f"deformation must be volume preserving; det={det}")
    finvt = np.linalg.inv(f).T
    wp = omega_dir @ f.T
    kp = nvec @ finvt.T
    numerator = np.einsum("ij,ij->i", wp, wp)
    denominator = np.einsum("ij,ij->i", kp, kp)
    return float(np.mean(numerator / denominator))


def energy_ratio_helicity_pair(nvec, e1, e2, deformation):
    """
    Return the + and - circular/helicity branch energy ratios.
    For real F, |F(e1 +/- i e2)/sqrt(2)|^2 are exactly degenerate.
    """
    nvec = np.asarray(nvec, dtype=float)
    e1 = np.asarray(e1, dtype=float)
    e2 = np.asarray(e2, dtype=float)
    f = np.asarray(deformation, dtype=float)
    finvt = np.linalg.inv(f).T
    k = nvec @ finvt.T
    denom = np.einsum("ij,ij->i", k, k)
    a = e1 @ f.T
    b = e2 @ f.T
    num = 0.5 * (
        np.einsum("ij,ij->i", a, a) + np.einsum("ij,ij->i", b, b)
    )
    ratio = float(np.mean(num / denom))
    return ratio, ratio


def isotropy_tensor(nvec):
    nvec = np.asarray(nvec, dtype=float)
    return np.einsum("ni,nj->ij", nvec, nvec) / len(nvec)


def transverse_residual(nvec, omega_dir):
    vals = np.einsum("ij,ij->i", np.asarray(nvec), np.asarray(omega_dir))
    return float(np.max(np.abs(vals)))


def fit_even_energy_coefficient(gammas, rplus, rminus):
    """
    Fit 0.5*(R(+g)+R(-g))-1 = A*g^2 + B*g^4.
    A is the dimensionless quadratic energy coefficient.
    """
    g = np.asarray(gammas, dtype=float)
    rp = np.asarray(rplus, dtype=float)
    rm = np.asarray(rminus, dtype=float)
    y = 0.5 * (rp + rm) - 1.0
    x = np.column_stack((g * g, g ** 4))
    a, b = np.linalg.lstsq(x, y, rcond=None)[0]
    pred = x @ np.array([a, b])
    rms = float(np.sqrt(np.mean((y - pred) ** 2)))
    return {"A2": float(a), "A4": float(b), "fit_rms": rms}


def born_modulus_from_A2(A2, rho=1.0, u_rms=1.0):
    """
    If e0 = rho*u_rms^2/2 and e/e0 = 1 + A2*gamma^2 + ...,
    then mu = d^2 e/d gamma^2 = A2*rho*u_rms^2.
    """
    return float(A2) * float(rho) * float(u_rms) ** 2


def transverse_wave_ratio_from_A2(A2):
    """Candidate c_T/u_rms if the Born modulus persists dynamically."""
    return float(np.sqrt(max(0.0, float(A2))))


def linearized_rest_euler_frequency(kvec, uvec):
    """
    Projected linearized incompressible Euler about homogeneous rest.
    The transverse acceleration operator vanishes, hence omega=0.
    Returns a numerical residual of that zero operator.
    """
    k = np.asarray(kvec, dtype=float)
    u = np.asarray(uvec, dtype=float)
    khat = k / np.linalg.norm(k)
    p = np.eye(3) - np.outer(khat, khat)
    # No background velocity gradient and no restoring term at rest.
    accel = p @ np.zeros(3)
    return float(np.linalg.norm(accel)), float(abs(khat @ u))
