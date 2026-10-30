# A075 v0.2.3: adaptieve Euler-tijdstap en backendmatrix

- Adaptive RK4: tijdstap begrensd door celverplaatsing, fysieke Gauss-kernbreedte en maximale vorticiteitsrotatieproxy; exacte fysieke eindtijd.
- Onafhankelijke temporele en ruimtelijke verfijningen op hetzelfde eindtijdstip.
- `*_energy_matrix.csv` met numerieke energieverliezen en -winsten per stap, plus lokale druk-/fluxdiagnostiek op bemonsterde tijden.
- `BASIC`, `EXTENDED`, `FULL`, `PREVIEW`; `--backends py,cpp,gpu` met harde preflight `--require-all-backends`.
- CPU Python FFT, hybride C++/OpenMP niet-lineariteitskern, en echte optionele PyTorch-XPU full spectral solver; geen SYCL Biot-Savart-mislabeling.
- Geen physische gatepromotie bij enkele softwarepariteit of ontbrekende fysieke exit/clock/core/box-convergentie.
