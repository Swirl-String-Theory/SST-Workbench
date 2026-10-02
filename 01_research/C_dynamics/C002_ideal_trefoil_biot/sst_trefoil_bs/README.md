# sst_trefoil_bs

**SST trefoil Biot-Savart & energetic-minimum closure**

Self-contained Python/C++ package for computing the Biot-Savart self-energy of
the ideal trefoil knot and finding the energetic minimum closure radius in the
Swirl-String Theory (SST) framework.

## Contents

| File | Purpose |
|------|---------|
| `ideal_source.py` | Resolver + parser for `ideal.txt` (5-level fallback chain) |
| `sst_bs_kernel.cpp` | C++17/pybind11 kernel: Biot-Savart integral + writhe |
| `build.py` | Auto-compile kernel (OpenMP optional) |
| `trefoil_energy.py` | Main pipeline: geometry → energy sweep → minimum → SST values |
| `README.md` | This file |

## Quick start

```bash
# 1. Install dependencies (once)
pip install pybind11 numpy scipy matplotlib --break-system-packages

# 2. Compile C++ kernel
python3 build.py

# 3. Run
python3 trefoil_energy.py
```

All output (report + PNG plot) goes to the package directory.

## ideal.txt resolution order

1. **SSTcore bundled** → `ssc.get_ideal_txt_path()`
2. **Env override** → `$SST_IDEAL_TXT`
3. **Local candidates** → `./ideal.txt`, `./resources/ideal.txt`, …
4. **GitHub raw** → `SSTcore/master/resources/ideal.txt` (cached to `~/.cache/sst`)
5. **katlas.org** → `katlas.org/images/d/d2/Ideal.txt.gz` (cached)

Set `$SST_CACHE_DIR` to override the cache location.

## Format

```xml
<AB Id="3:1:1" Conway="3" L="16.371637" D=" 1.000000">
  <Coeff I="1" A=" ax, ay, az" B=" bx, by, bz" />
  …
</AB>
```

Curve: `r(t) = Σ_k [ A_k cos(kt) + B_k sin(kt) ]`,  t ∈ [0, 2π]

## Physics

**Biot-Savart self-integral (Rosenhead regularisation):**

```
I(K, a) = Σ_{i≠j}  (dl_i · dl_j) / sqrt(|r_i − r_j|² + a²)
```

**Asymptotic fit (slender filament):**

```
I(K, a) ≈ A_K · L · ln(L/a) + B_K · L
A_K → 1/(4π)   (slender-body theorem — ORTHODOX)
```

**Variational minimum (pressure/surface term E_surf ~ πa²/L):**

```
a* = L √(A_K / 2π)
```

**SST Compton closure:**

```
r_c = α ħ / (2 m_e c)  ≈ 1.409e-15 m
L_phys = ropelength × r_c  ≈ 4.62e-14 m
```

## CLI options

```
python3 trefoil_energy.py [OPTIONS]

  --n       INT    Polygon sample points     [default: 600]
  --a-min   FLOAT  Min tube radius (norm)    [default: 5e-3]
  --a-max   FLOAT  Max tube radius (norm)    [default: 1.2]
  --n-pts   INT    Number of a values        [default: 40]
  --no-plot        Skip matplotlib output
  --plot-out PATH  PNG output path
```

## Epistemic labels

| Result | Label |
|--------|-------|
| A_K → 1/(4π) | `[ORTHODOX]` — slender-body theorem |
| Writhe Wr ≈ 3 | `[DERIVED]` — Gauss integral on ideal geometry |
| L_phys = ropelength × r_c | `[DERIVED]` — from Compton closure |
| ρ_f matched to m_e c² | `[CALIBRATED]` — not independently fixed |
| Variational a* as equilibrium radius | `[SPECULATIVE]` |

## Authors

Omar Iskandarani (ORCID: 0009-0006-1686-3961) / Claude (Anthropic), July 2026.
