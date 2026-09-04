# import numpy as np
#
# # Suppose you loaded your N‐point curve as arrays X, Y, Z in order
# # Example: load from file or embed manually
# points = np.loadtxt("knot8_5.xyz")  # Nx3 array
# X, Y, Z = points[:,0], points[:,1], points[:,2]
# N = len(points)
# s = np.linspace(0, 2*np.pi, N, endpoint=False)
#
# def fourier_coeffs(coord, s, maxJ=None):
#     N = len(coord)
#     if maxJ is None:
#         maxJ = N//2 - 1
#     a = np.zeros(maxJ)
#     b = np.zeros(maxJ)
#     for j in range(1, maxJ+1):
#         a[j-1] = (2/N) * np.sum(coord * np.cos(j*s))
#         b[j-1] = (2/N) * np.sum(coord * np.sin(j*s))
#     return a, b
#
# maxJ = 50  # adjust based on desired resolution
# ax, bx = fourier_coeffs(X, s, maxJ)
# ay, by = fourier_coeffs(Y, s, maxJ)
# az, bz = fourier_coeffs(Z, s, maxJ)
#
# # Print results in your fseries format:
# for j in range(maxJ):
#     print(f"{ax[j]: .6f} {bx[j]: .6f} {ay[j]: .6f} {by[j]: .6f} {az[j]: .6f} {bz[j]: .6f}")
#

import numpy as np

# Data
points = np.array([
    (  -0.646253,   -1.938277,   -0.769706),
    (  -0.825099,   -1.898104,   -0.865705)
])
N = len(points)
s = np.linspace(0, 2*np.pi, N, endpoint=False)
X, Y, Z = points[:,0], points[:,1], points[:,2]

def fourier_coeffs(coord, s, maxJ):
    a = np.zeros(maxJ)
    b = np.zeros(maxJ)
    for j in range(1, maxJ + 1):
        a[j-1] = (2 / N) * np.sum(coord * np.cos(j * s))
        b[j-1] = (2 / N) * np.sum(coord * np.sin(j * s))
    return a, b

maxJ = 50
ax, bx = fourier_coeffs(X, s, maxJ)
ay, by = fourier_coeffs(Y, s, maxJ)
az, bz = fourier_coeffs(Z, s, maxJ)

# Output in .fseries format
print("% Knot 8_17 (Fourier projection)")
print("% lines  a_x(j) b_x(j)  a_y(j) b_y(j)  a_z(j) b_z(j)")
for j in range(maxJ):
    print(f"{ax[j]: .6f} {bx[j]: .6f} {ay[j]: .6f} {by[j]: .6f} {az[j]: .6f} {bz[j]: .6f}")