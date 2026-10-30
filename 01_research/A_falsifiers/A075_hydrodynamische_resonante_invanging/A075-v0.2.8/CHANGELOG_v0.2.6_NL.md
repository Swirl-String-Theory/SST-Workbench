# A075-v0.2.6 — Heartbeat voor langdurige Euler-runs

- Gebaseerd op A075-v0.2.5 en de **byte-ongewijzigde** Framework v1.1.0-runtime.
- Nieuw: `run_all.cmd STATUS` leest `run_status/heartbeat.json` zonder een run te starten.
- Nieuwe `--heartbeat-seconds 10` (1..3600) voor BASIC/EXTENDED/FULL; standaard 10.
- Daemon-thread blijft heartbeat tonen ook tijdens langlopende initialisatie of FFT-stap.
- Iedere geaccepteerde RK4-stap registreert tijd, rooster, backend, knotscenario, effectieve delta-t en eventuele rejects.
- Fases: matrix-backend, knoop en ruimtelijke/tijdverfijning; ETA enkel binnen actuele fase.
- Atomair statusbestand buiten framework outputs, om bewijsmanifests en private data niet te wijzigen.
- Geen wijzigingen aan Euleroperator, tijdstapselectie, wetenschappelijke gates of framework-runtime.
- Nieuwe v0.2.6 naast v0.2.5, geen automatische herstart of aanpassing actieve runs.
