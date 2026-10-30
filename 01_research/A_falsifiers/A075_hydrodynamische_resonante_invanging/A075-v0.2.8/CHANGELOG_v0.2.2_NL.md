# A075-v0.2.2 — Framework CPU-FFT-parallelisatie en runtime gridopties

- Vervolg van v0.2.1, afzonderlijke versie zonder oude FREEZE en outputroots te wijzigen.
- `run_all.cmd BASIC/FULL --grid=N --grid-up=M --threads=12 --dt=...` via authentiek Framework v1.0.10.
- SciPy FFT op CPU met expliciet aantal workers, en originele NumPy-referentie als pariteitscontrole.
- Runmanifest met exacte gekozen geometrieën, rooster, tijdstap, CPU-backend en threads.
- `GPU_PROBE` via het bestaande Framework SYCL-workerpad, maar geen onterechte 3D-Euler-claim.
- `--backend arc` geblokkeerd totdat echte FFT/Leray/druk/RK4-kernels en device-pariteit bestaan.
- Configuratie, geheugenschatter en rekenbudgetafwijzing bij grote runs; `--allow-expensive` vereist waar nodig.
- Alle fysische gates voor bronvertrek, klokcycli, kern-/boxconvergentie en langdurige retentie blijven UNRESOLVED.
