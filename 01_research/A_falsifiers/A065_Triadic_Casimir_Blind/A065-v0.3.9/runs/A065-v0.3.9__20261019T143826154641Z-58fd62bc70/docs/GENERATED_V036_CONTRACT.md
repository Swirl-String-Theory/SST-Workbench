# A065 v0.3.6 numerical generator / smoothing contract

Preregistration SHA256: `7ca11af33d2e48fdc3293b6153e76ce97be403b250cf54afe382fe89518a15bd`

The two historical parametrizations from the user's 2015 notebooks are evaluated on
equal arclength meshes N600,1200,2400,4800 by the stdlib generator. The original
SciPy regenerate.py and all eight pinned v0.3.5 XYZ inputs remain unmodified.
Newly generated coordinates must agree with original files <1e-7 (Euclidean norm).

Numerical kernel: u(x) = Gamma/(4*pi) sum_j Delta X_j cross (x-mid_j)
/ (|x-mid_j|^2 + epsilon^2)^(3/2). eps = 0.06 dimensionless, NOT SST r_c.
RK4 steps 8, Gamma 1, T 0.04. Report mean segment / epsilon for each grid.
G19 generated geometry, G20 ratio diagnostic only, G21 fine-pair convergence
at 1% with coarse 600/1200 explicitly retained. G2, G11, G13 FAIL remain.
No force target fitting, no physical source, no reveal, no physical closure.
