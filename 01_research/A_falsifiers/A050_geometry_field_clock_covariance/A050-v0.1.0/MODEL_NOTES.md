# Model notes

The vector field is generated from a regularized closed-filament kernel with dimensionless unit amplitude. The amplitude is not interpreted physically and is removed by RMS normalization before the closure calculation.

The scalar field is obtained from the incompressible pressure-Poisson structure. The inverse Laplacian is therefore present explicitly, making this falsifier a test of whether the closure produces robust long-range second-order structure after finite-volume averaging.

The periodic box and finite core are numerical regularizations. Any apparent scaling that changes strongly with grid size, window range, box size, or core ratio must be treated as numerical rather than structural.
