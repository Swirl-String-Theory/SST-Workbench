# A075 Heartbeat / voortgang — v0.2.9

## Lopende v0.2.5-run
Deze versie is niet geïnstrumenteerd. Voeg **geen** code toe in een lopende of reeds bevroren v0.2.5; de draaiende interpreter laadt nieuwe code bovendien niet betrouwbaar. Controleer activiteit in een tweede console met Windows Taakbeheer of de PowerShell-procescommando's hieronder.

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python|sst_sycl_worker' } | Select ProcessId,Name,CommandLine
```

## Volgende run in v0.2.9

```bat
run_all.cmd FREEZE
run_all.cmd BASIC --grid 80 --threads 12 --heartbeat-seconds 10
```

De console toont elke tien seconden een regel met `phase`, `backend`, `knot`, `grid`, `progress`, `t/T`, `steps`, `elapsed` en een **indicatieve ETA van alleen de huidige fase**. De ETA gebruikt verstreken rekentijd en fysieke tijdfractie, niet het theoretisch aantal vaste stappen. Adaptieve integratie maakt haar onzeker.

Live status uit een tweede console (zelfde versie):

```bat
run_all.cmd STATUS
```

Het bestand `run_status/heartbeat.json` wordt atomair bijgewerkt buiten de officiële gehashte uitvoermap. `RUNNING` betekent dat de bewakingsthread het laatst leefde; `STALE_TELEMETRY` duidt op afwezigheid van updates, niet op een bewezen crash. Een trage `RK4`-stap kan meerdere heartbeats zonder nieuwe geaccepteerde stap veroorzaken. Kijk dan naar de proces- en GPU-belasting.

**Niet inbegrepen:** procent voltooide totale studies, gegarandeerde eindtijd, fysieke PASS, daadwerkelijke apparaatmonitoring of certificering. Backendmatrix kan de gehele duur verveelvoudigen.
