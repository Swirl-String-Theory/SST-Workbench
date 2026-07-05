# Numerical validation for SST swirl helicity mapping
# Using provided constants:
# C_e (tangential swirl velocity), r_c (core radius)
# Sensitivity sweep and multi-core helicity estimates for SST
import numpy as np
import matplotlib.pyplot as plt
import math
import pandas as pd
from ace_tools_open import display_dataframe_to_user

# Given constants
C_e = 1_093_845.63       # m/s, "Vortex-Tangential-Velocity"
r_c = 1.40897017e-15     # m, "Vortex-Core radius"

# Circulation for a single core loop (rigid swirl approximation)
# Γ = ∮ v · dl ≈ 2π r_c * C_e  (units: m^2/s)
Gamma0 = 2 * math.pi * r_c * C_e  # m^2/s
H0 = Gamma0**2                    # base helicity scale for L_per = 1
# Choose a representative periodic swirl-linking density L_per = 1 (dimensionless)
L_per = 1.0

# Swirl helicity H_swirl = Γ^2 * L_per  (units: m^4/s^2)
H_swirl = Gamma0**2 * L_per

df = pd.DataFrame({
    "Parameter": ["C_e", "r_c", "Γ (circulation)", "L_per", "H_swirl"],
    "Value": [C_e, r_c, Gamma0, L_per, H_swirl],
    "Units": ["m s^-1", "m", "m^2 s^-1", "—", "m^4 s^-2"]
})

display_dataframe_to_user("SST Swirl Helicity Numerical Check", df)

print(Gamma0, H_swirl)

# --- 1) Sensitivity sweep over scalings of r_c and C_e ---
lambdas = np.array([0.1, 0.5, 1, 2, 5, 10], dtype=float)  # scale for r_c
mus     = np.array([0.1, 0.5, 1, 2, 5, 10], dtype=float)  # scale for C_e


rows = []
for la in lambdas:
    for mu in mus:
        Gamma = Gamma0 * (la * mu)
        H = (Gamma**2)  # L_per = 1
        rows.append({
            "lambda_r_c": la,
            "mu_C_e": mu,
            "Gamma[m^2/s]": Gamma,
            "H_swirl[m^4/s^2]": H
        })

sweep_df = pd.DataFrame(rows)
sweep_df = sweep_df.sort_values(by=["lambda_r_c", "mu_C_e"]).reset_index(drop=True)

# Display the sweep table to the user
display_dataframe_to_user("SST Sensitivity Sweep (lambda, mu) → Γ and H_swirl", sweep_df)

# Plot 1: H vs lambda (mu fixed at 1)
plt.figure()
H_vs_lambda = H0 * (lambdas**2)  # mu=1
plt.plot(lambdas, H_vs_lambda, marker='o')
plt.title("Helicity scaling vs λ (mu=1)")
plt.xlabel("λ = scale on r_c")
plt.ylabel("H_swirl [m^4/s^2]")
plt.grid(True)
plt.savefig("H_vs_lambda.png", bbox_inches="tight")
plt.close()

# Plot 2: H vs mu (lambda fixed at 1)
plt.figure()
H_vs_mu = H0 * (mus**2)  # lambda=1
plt.plot(mus, H_vs_mu, marker='o')
plt.title("Helicity scaling vs μ (lambda=1)")
plt.xlabel("μ = scale on C_e")
plt.ylabel("H_swirl [m^4/s^2]")
plt.grid(True)
plt.savefig("H_vs_mu.png", bbox_inches="tight")
plt.close()

# --- 2) Multi-core estimate with uniform pairwise periodic winding L_ij = 1 ---
# H_total = Γ^2 * sum_{i<j} L_ij = Γ^2 * N(N-1)/2
N_vals = np.arange(1, 31)  # up to 30 cores
H_total = H0 * (N_vals * (N_vals - 1) / 2.0)

multi_df = pd.DataFrame({
    "N_cores": N_vals,
    "pairs": N_vals * (N_vals - 1) / 2.0,
    "H_total[m^4/s^2]": H_total
})

display_dataframe_to_user("SST Multi-core Helicity (uniform L_ij=1)", multi_df)

# Plot 3: H_total vs N
plt.figure()
plt.plot(N_vals, H_total, marker='o')
plt.title("Total swirl helicity vs number of cores (uniform L_ij=1)")
plt.xlabel("N (number of cores)")
plt.ylabel("H_total [m^4/s^2]")
plt.grid(True)
plt.savefig("H_total_vs_N.png", bbox_inches="tight")
plt.close()

# Save CSVs
sweep_csv_path = "sst_sensitivity_sweep.csv"
multi_csv_path = "sst_multicore_helicity.csv"
sweep_df.to_csv(sweep_csv_path, index=False)
multi_df.to_csv(multi_csv_path, index=False)

# Return key values and file paths for reference
print(Gamma0, H0, sweep_csv_path, multi_csv_path, "H_vs_lambda.png", "H_vs_mu.png", "H_total_vs_N.png")