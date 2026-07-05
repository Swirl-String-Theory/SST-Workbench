import numpy as np
from pyknotid.spacecurves import Knot

def generate_knot_dhf(alexander_notation, output_filename, harmonics=10):
    """
    Retrieves relaxed dimensionless coordinates for a given prime knot,
    computes the DHF coefficients, and formats them for Fortran ingestion.
    """
    # 1. Retrieve topological manifold (N x 3 array)
    try:
        k = Knot(alexander_notation)
        # Ensure we have a concrete NumPy array of shape (N, 3)
        coords = np.asarray(k.points, dtype=float)
    except Exception as e:
        print(f"Topology retrieval failed: {e}")
        return

    # Validate coordinate array shape
    if coords.ndim != 2 or coords.shape[1] != 3:
        print(f"Topology retrieval failed: unexpected coordinates shape {coords.shape}")
        return

    N = coords.shape[0]

    # 2. Centralize topological center of mass to origin
    coords -= np.mean(coords, axis=0)

    x, y, z = coords[:, 0], coords[:, 1], coords[:, 2]
    k_array = np.arange(N)

    # 3. Spectral extraction and formatted output
    with open(output_filename, 'w') as f:
        f.write(f"% Knot {alexander_notation} DHF \n")
        f.write("% lines: a_x(j)  b_x(j)  a_y(j)  b_y(j)  a_z(j)  b_z(j)\n")

        for j in range(1, harmonics + 1):
            theta_jk = (2 * np.pi * j * k_array) / N
            cos_theta = np.cos(theta_jk)
            sin_theta = np.sin(theta_jk)

            # Dimensionless L^2 projections
            a_x = (2.0 / N) * np.sum(x * cos_theta)
            b_x = (2.0 / N) * np.sum(x * sin_theta)

            a_y = (2.0 / N) * np.sum(y * cos_theta)
            b_y = (2.0 / N) * np.sum(y * sin_theta)

            a_z = (2.0 / N) * np.sum(z * cos_theta)
            b_z = (2.0 / N) * np.sum(z * sin_theta)

            # Formatted exactly to Fortran 12.3f standard spacing
            line = f"{a_x:12.3f}{b_x:12.3f}{a_y:12.3f}{b_y:12.3f}{a_z:12.3f}{b_z:12.3f}\n"
            f.write(line)

    print(f"Extraction complete: {output_filename}")

# Execute for required knots
generate_knot_dhf('9_2', 'knot92_dhf.d4.1', harmonics=10)
generate_knot_dhf('10_1', 'knot101_dhf.d4.1', harmonics=10)