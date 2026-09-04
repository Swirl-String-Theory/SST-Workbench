import numpy as np

def extract_dhf_coefficients(input_file, output_file, harmonics=10, scale_factor=1.0):
    """
    Ingests N x 3 Cartesian coordinates and exports formatted DHF coefficients.
    scale_factor allows mapping to canonical physical dimensions (e.g., r_c) if required by downstream logic.
    """
    # Load discrete topological vertices
    coords = np.loadtxt(input_file)
    N = len(coords)

    # Enforce origin centralization (remove j=0 translation bias)
    coords -= np.mean(coords, axis=0)
    coords *= scale_factor

    x, y, z = coords[:, 0], coords[:, 1], coords[:, 2]
    k_array = np.arange(N)

    with open(output_file, 'w') as f:
        f.write(f"% Computed DHF Coefficients for {input_file}\n")
        f.write("% lines: a_x(j)  b_x(j)  a_y(j)  b_y(j)  a_z(j)  b_z(j)\n")

        for j in range(1, harmonics + 1):
            # Phase angle calculation for harmonic j
            theta_jk = (2 * np.pi * j * k_array) / N
            cos_theta = np.cos(theta_jk)
            sin_theta = np.sin(theta_jk)

            # Discrete sums for orthogonal components
            a_x = (2.0 / N) * np.sum(x * cos_theta)
            b_x = (2.0 / N) * np.sum(x * sin_theta)

            a_y = (2.0 / N) * np.sum(y * cos_theta)
            b_y = (2.0 / N) * np.sum(y * sin_theta)

            a_z = (2.0 / N) * np.sum(z * cos_theta)
            b_z = (2.0 / N) * np.sum(z * sin_theta)

            # Formatted exactly to Fortran/C expectations (12.3f standard spacing)
            line = f"{a_x:12.3f}{b_x:12.3f}{a_y:12.3f}{b_y:12.3f}{a_z:12.3f}{b_z:12.3f}\n"
            f.write(line)

# Execution example:
# extract_dhf_coefficients('knot92_raw.txt', 'knot92_dhf.d4.1', harmonics=10)