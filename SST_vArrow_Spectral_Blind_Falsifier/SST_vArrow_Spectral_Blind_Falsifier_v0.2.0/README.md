# SST v-arrow Spectral Blind Falsifier v0.2.0

Doel: **blind** bepalen of dynamische knot/link-data een reproduceerbare lage-`k` propagatiesnelheid opleveren, en pas na hash-lock vergelijken met de verzegelde SST-doelsnelheid.

## Nieuw in v0.2.0

- `run_all.cmd` werkt nu **zonder argumenten**.
- standaard wordt `./campaigns/` **recursief** gescand;
- geneste `manifest.csv` bestanden worden automatisch samengevoegd;
- spectrum-CSV, spectrum-NPZ, trajectory-CSV en trajectory-NPZ worden automatisch herkend;
- VortexLab `*.txt`/`*.log` met `tPhys=... type=diag detail={...}` worden automatisch geparseerd;
- scalar VortexLab diagnostics worden bewust als `diagnostic_only` gemarkeerd wanneer ruimtelijke `k`-informatie ontbreekt;
- demo/synthetische datasets worden uit een normale blind run geweerd;
- een echt VortexLab diagnostic excerpt uit een eerder gedeelde dataset is meegeleverd onder `campaigns/imported_library_excerpts/`;
- `run_scan.cmd` laat zien wat de recursive campaign builder heeft gevonden voordat je fit.

## Snelste start

Gewoon:

```cmd
run_all.cmd
```

Dit gebruikt:

```text
campaign root = campaigns
output        = outputs_blind
```

en stopt na de blind/hash-locked fase.

Eerst inspecteren:

```text
outputs_blind\campaign_scan\campaign_scan.csv
outputs_blind\campaign_scan\scan_summary.json
outputs_blind\blind_results.json
outputs_blind\blind_lock.json
```

Pas daarna:

```cmd
run_unblind.cmd outputs_blind
```

## Alleen data inventariseren

```cmd
run_scan.cmd
```

Of voor een andere folder:

```cmd
run_scan.cmd C:\workspace\projects\SST-Workbench\VortexLab\outputs outputs_scan_vortexlab
```

De scanner loopt recursief door alle subfolders.

## `campaigns/` als drop folder

Je hoeft niet meer eerst handmatig een campaign te maken. Kopieer data bijvoorbeeld zo:

```text
campaigns\
  vortexlab_2026_08\
    runA\trajectory.npz
    runB\spectrum.csv
  older_sessions\
    vortexlab-session-7-6-24b-....txt
  my_manual_campaign\
    manifest.csv
    data\...
```

Een expliciete `manifest.csv` blijft de hoogste-prioriteit route wanneer je family IDs, topology blind labels, resoluties of core-radius metadata zelf wilt vastleggen.

## Speed-eligible input A — spectrum CSV

Kolommen:

```text
k_rad_m,omega_rad_s,power
```

`power` is optioneel.

## Speed-eligible input B — spectrum NPZ

Arrays:

```text
k_rad_m
omega_rad_s
power          # optioneel
```

## Speed-eligible input C — trajectory CSV

Kolommen:

```text
time_s,point_id,x_m,y_m,z_m
```

Er zijn minimaal 16 tijdframes nodig.

## Speed-eligible input D — trajectory NPZ

Arrays:

```text
xyz[T,N,3]
time_s[T]
```

De analyzer resamplet elke gesloten centerline uniform op booglengte, verwijdert rigid translation/rotation met Kabsch alignment, projecteert op normal/binormal directions en bouwt vervolgens het 2D-spectrum `S(k,omega)`.

## VortexLab legacy/session logs

v0.2.0 herkent regels van de vorm:

```text
... tPhys=2.280616 type=diag detail={...}
```

Daaruit worden onder andere tijdreeksen van `Wr`, `Lk`, `ACN`, `RA`, `zA`, `topologyGap`, stretch- en spec-clock-diagnostics geëxtraheerd naar:

```text
outputs_blind\campaign_scan\diagnostics\
```

**Cruciaal:** zo'n scalar diagnostic log bevat doorgaans geen volledige `X(s,t)` centerline en ook geen expliciete `(k,omega)` modes. De scanner noemt deze data daarom `diagnostic_only` en zal er niet kunstmatig een snelheid uit fabriceren.

Zodra je de originele VortexLab `.txt` logs of bijbehorende trajectory exports lokaal onder `campaigns\` zet, pakt v0.2.0 ze automatisch op.

## Meegeleverde eerder gedeelde data

`campaigns/imported_library_excerpts/vortexlab_7-6-24b_diag_excerpt.csv` bevat een werkelijk eerder gedeeld VortexLab diagnostic interval. Het is bedoeld om de nieuwe recursive importer/QC direct te testen. Het is **geen** vervanging voor een volledige trajectory.

## Blind gates

1. positieve lage-`k` slope;
2. lineair model moet BIC-competitief zijn;
3. vrije power-law exponent moet nabij 1 liggen;
4. slope moet stabiel zijn tegen de gekozen low-`k` cutoff;
5. intercept moet klein zijn;
6. hoogste twee numerieke resoluties moeten convergeren;
7. kandidaat-snelheid moet over onafhankelijke families reproduceerbaar zijn.

De fit concurreert met quadratic, linear+quadratic, power-law en optioneel `k^2 log(1/(k r_c))`. Een lineaire propagatiesnelheid wordt dus niet afgedwongen.

## Demo

```cmd
run_demo.cmd
```

Dit gebruikt uitsluitend de synthetische decoy-campagne. Demo/synthetische mappen zijn standaard uitgesloten door `run_all.cmd`.

## Blind discipline

Een statische relaxed centerline bevat geen tijdschaal en kan geen onafhankelijke snelheid in m/s bepalen. v0.2.0 blijft dit weigeren. Evenzo wordt een scalar diagnostic tijdserie niet opgewaardeerd tot een `k`-resolved dispersiemeting wanneer die informatie niet in de bron staat.

Survival van alle gates is geen bevestiging van SST; het betekent uitsluitend dat deze vooraf gedefinieerde test de verzegelde target niet heeft gefalsifieerd.