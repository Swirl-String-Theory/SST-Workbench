# A075-v0.2.8 — Ruban T(2,3) Seed Fidelity & Stability

- Exacte gereconstrueerde seed uit Ruban (2018) figuur 3; B0 = 77/500, delta = 1/20, Lambda = 7/5 + ln(200)/2. Dit zijn inputparameters, geen teruggewonnen originele simulatiestaat.
- 2048-punts gesloten equal-arclength XYZ plus originele seedmanifest, referentieconfiguratie, en 4096-puntscontrole.
- G11: exacte seedhash, windingen (2,3), torusstraalresiduen en sample-evenredigheid.
- G12: source-free 3D Euler-diagnostiek met globale energie, enstrofie en translatie-invariante vorticiteitsspectrale verandering. Blijft UNRESOLVED voor fysische stabiliteit/topologie.
- Vergelijking met dezelfde R0=1 Euler-analytische T(2,3) op B0=0.32, overige veldparameters gelijk; geen donor.
- `RUBAN_PREVIEW` voor snelle afzonderlijke smoke; `BASIC --ruban-study` voor framework-run en echte py/cpp/gpu Ruban-trajecten. `--ruban-refinement` activeert aparte dt en N tests.
- Geen wijziging aan ingebedde Framework v1.1.0, Fourier-Euler kern of oudere A075-versies.
- Numerieke grenzen en tijd: periodieke beelden blijven; Rubans delta is niet de Euler Gaussian sigma; oorspronkelijke willekeurige verstoring ontbreekt. Geen claim van langdurige stabiliteit.

- Optionele `RUBAN_FILAMENT` diagnostiek voor Ruban Eq.(9), regelbare filamentresolutie/dt/T; géén geclaimde reproductie van zijn pseudospectrale integrator.
- G13 registreert uitsluitend de optionele filament-screendata, nooit fysische stabiliteit.
