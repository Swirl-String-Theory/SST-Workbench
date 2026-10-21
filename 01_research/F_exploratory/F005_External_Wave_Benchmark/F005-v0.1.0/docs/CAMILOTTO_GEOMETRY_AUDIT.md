# F005 v0.5.0 — Camilotto source-grounded geometry audit

**Status:** `GEOMETRY_DOCUMENTED / EXPERIMENTAL_INPUT_POLARITY_UNVERIFIED / INITIAL_CONDITIONS_UNVERIFIED`.

This update changes only the geometry configuration. **No** measurements, previous development fits, dataset splits, ZIP archives or model source code are changed. The uploaded thesis SHA-256 is `e8db99ce4623942ff621a0c01cbb375afa6b22ef8524083e00dd5ea405d33add`.

## Directly documented source fields

| Config field | Value | Exact thesis evidence | Evidence type |
|---|---:|---|---|
| `tank_length_internal_m` | 0.080 | PDF pp. 20–21, Table 1.1; p. 40 Table 2.1 | Measured with caliper (stated ±0.5 mm) |
| `tank_width_internal_m` | 0.031 | PDF p. 21 Table 1.1; p. 40 Table 2.1 | Measured geometry |
| `fill_depth_m` | 0.043 | PDF p. 21 Table 1.1; p. 40 Table 2.1 | Manually measured liquid level |
| `sensor_x_from_center_m` | +0.040 | PDF pp. 32–33 Eq. 1.11; pp. 44–46 right-wall estimate | *Effective reconstruction point* (+L/2), NOT physical sensor position |
| `liquid_density_kg_m3` | 998 | PDF p. 40 Table 2.1 | **Author's modeling parameter**, NOT experimentally measured soluble-coffee density |
| `gravity_m_s2` | 9.81 | PDF p. 40 Table 2.1 | Author's constant |
| `surface_tension_N_m` | 0.0 | PDF pp. 39–40 assumptions | **Neglected in author's theory**, NOT measured zero surface tension |
| `assumption_2d_longitudinal` | true | PDF pp. 41–42, 46–47 | Adopted mathematical approximation, NOT proof flow is 2D |
| `n_modes` | 4 | PDF p. 48 and Table 2.3 on p. 49 | Author's four-mode truncation |

The fluid is soluble coffee (water-like viscosity and optical contrast), not pure water. Thesis p. 40 also lists kinematic viscosity `1.003e-6 m²/s` and p. 49 an empirically chosen MSD damping ratio `0.0538`. **Neither** belongs in the undamped ideal Euler baseline; do not import the author's calibrated damping into Euler.

## Geometric Euler frequency check (not measured frequencies)

With sigma=0, `k_n=(2n+1)pi/L` and `omega_n=sqrt(g*k_n*tanh(k_n*h))`:

| n | k_n [m^-1] | omega_n [rad/s] | f_n [Hz] |
|---:|---:|---:|---:|
| 0 | 39.26991 | 18.96840 | 3.01892 |
| 1 | 117.80972 | 33.99443 | 5.41038 |
| 2 | 196.34954 | 43.88837 | 6.98505 |
| 3 | 274.88936 | 51.92942 | 8.26482 |

The first four angular frequencies reproduce thesis PDF p. 49, Table 2.3: `18.9684, 33.9944, 43.8884, 51.9294 rad/s` (within rounding). These are NOT fitted to the experimental data.

## Deliberately unresolved gates

1. `acceleration_axis_sign = null`: thesis Eq. 2.23 establishes the *mathematical* +x convention and a negative forcing coefficient, but does not independently certify the stored `INPUT_TRAIN.npy` sign relative to the flask +x axis. Do not choose its sign to minimize validation RMSE.
2. `measurement_height_sign = null`: Eq. 1.11 defines a signed wall elevation from camera slope, but mapping of exported `OUTPUT_TRAIN.npy` to the +x right wall is not proven by thesis text alone. Camera frames are rotated 180° (PDF p. 30), so image pixel direction must not be assumed identical to the model +x axis.
3. `initial_equilibrium_confirmed = false`: thesis PDF p. 35 documents 1000 pre-motion optical baseline samples, and p. 48 assumes zero model initial state, but this does not establish that every synchronized public array has zero physical modal velocity at its first stored sample. The zero-from-rest run remains a conditional model assumption until verified.
4. `provenance_confirmed = false`: means the entire measurement-to-model mapping is NOT attested. This does **not** negate the documented internal geometry. Change only after direct confirmation from acquisition export code / source metadata, with a provenance record.

The existing `f005_euler_v050.py` intentionally fails closed until the two signs and the initial-condition/provenance gates have been confirmed. This is expected; **do not** turn those flags on merely to make the runner execute.

## Subsequent evidence needed

Inspect publisher `load_dataset.py`, generator/export code or accompanying records for (a) acceleration +x definition, (b) positive `OUTPUT_TRAIN` wall convention, (c) equilibrium initial state and synchronization at the start of the exported 1500 samples. Audit only development data until the split rules permit more. Record any mapping discrepancy as a versioned correction; never determine signs from held-out test responses.

## Bibliographic entry

```latex
\bibitem{Camilotto2026}
D. Camilotto, ``A Comprehensive Data-Driven Framework for Robotic Liquid Sloshing Control: From Extensive Experimental Model Validation and Enhancement to Trajectory Optimization,'' Master's thesis, Politecnico di Milano (2026).\\
Permanent record: \url{https://hdl.handle.net/10589/253216}.
```
