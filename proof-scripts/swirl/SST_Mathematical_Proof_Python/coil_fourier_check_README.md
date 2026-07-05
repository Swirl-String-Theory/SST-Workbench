# coil_fourier_check.py

Standalone spatial Fourier checker for coil geometries.

## Install

```bash
pip install numpy pandas matplotlib
```

## Built-in comparison

```bash
python coil_fourier_check.py --geometry all --out-dir coil_fourier_out --preview
```

Outputs:

- `wire_spectrum.csv` — driven wire geometry spectrum `S_wire`
- `field_spectrum.csv` — Biot–Savart field spectrum on a probe ring
- `summary.csv` — strongest modes per geometry
- `mode_lock_frequencies.csv` — conditional speed-scaling table
- `spatial_fourier_spectrum.png` — spectrum plot
- `field_profiles.png` — field signal around the probe ring
- `metadata.json` — exact run parameters

## Single geometry examples

```bash
python coil_fourier_check.py --geometry rodin --rodin-P 5 --rodin-Q 12 --out-dir rodin_out --preview
python coil_fourier_check.py --geometry sawshape --saw-S 40 --saw-fwd 11 --saw-bwd -9 --out-dir saw_out
python coil_fourier_check.py --geometry starship --starship-S 9 --starship-fwd 4 --starship-bwd 4 --out-dir starship_out
```

## Phase reversal test

```bash
python coil_fourier_check.py --geometry rodin --phase-mode abc --out-dir rodin_abc
python coil_fourier_check.py --geometry rodin --phase-mode acb --out-dir rodin_acb
```

Compare the resulting field profiles and spectra. A chirality-sensitive response should be antisymmetric under ABC ↔ ACB, but heating-like scalar backgrounds usually are not.

## Custom CSV geometry

CSV columns:

```csv
lane,x,y,z,phase_deg,current
A,10,0,0,0,1
A,9.9,1,0,0,1
B,-5,8.66,0,120,1
```

Run:

```bash
python coil_fourier_check.py --custom-csv mycoil.csv --out-dir custom_out --probe-r-mm 25 --probe-z-mm 20
```

By default coordinates are interpreted as mm. Change with `--units-to-m`, for example meters: `--units-to-m 1`.

## Important interpretation

- `S_wire` describes the driven path geometry.
- `S_field_Bz`, `S_field_Br`, or `S_field_Bphi` describes the actual field mode content at the probe ring.
- For experiments, the field spectrum is usually more important than the wire spectrum.
- The mode-lock frequency table is conditional only; always map ordinary LC/RF resonances separately.
