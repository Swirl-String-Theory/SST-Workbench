# Source traceability — v0.3.1

| Implemented concept | Source basis | Workbench status |
|---|---|---|
| complexion vs state distribution vs macrostate | Boltzmann 1877 translation/commentary | implemented as separate state-count and occupation tables |
| maximum multiplicity / permutability measure | Boltzmann 1877 | combinatorial `log P` audit |
| exponential energy distribution | Boltzmann 1877 | occupation fit and temperature recovery |
| spatial + energy dependence of entropy description | Boltzmann 1877 commentary | state counts depend on both `x` and `E`; no automatic additive decomposition asserted |
| `F = T dS/dx` | Verlinde Sec. 2–3 | optional bridge gate |
| `dS/dx = 2 pi k_B m c/hbar` | Verlinde Eq. 3.6 | optional postulate audit |
| `N propto A` and `N = Ac^3/(G hbar)` | Verlinde Eq. 3.10 | optional screen audit |
| equipartition `E = 1/2 Nk_BT` | Verlinde Eq. 3.11 | optional screen audit |
| inverse-square law | Verlinde Eq. 3.13 | independent radial slope audit |
| entropy per bit vs Newton potential | Verlinde Eq. 3.16 | optional potential/entropy audit |
| `F_hyd=-(m/rho_f) grad p` | SST Euler-pressure bridge, not derived from the two papers | independent comparison target |
| integrability `grad(1/T) x grad p=0` | new v0.3 derived consistency condition | conditional bridge falsifier |
| `r_c^2/l_P^2` hierarchy | new dimensional/numerical guard | always reported, never a pass/fail by itself |

The workbench intentionally does **not** implement Verlinde's relativistic Einstein-equation reconstruction as an SST result.  That route assumes additional relativistic/holographic structure that the present centerline workbench does not derive.
