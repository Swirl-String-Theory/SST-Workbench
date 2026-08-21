# SST v-arrow Spectral Blind Falsifier v0.1.0

Doel: **blind** bepalen of een dynamische knot/link-campagne een reproduceerbare lage-k propagatiesnelheid oplevert, en pas na hash-lock vergelijken met de canonieke SST-doelsnelheid.

## Wat wordt NIET gedaan

Een statische relaxed centerline bevat geen tijdschaal en kan dus geen snelheid in m/s bepalen. De package weigert daarom statische geometrie als bewijs voor een propagatiesnelheid. Gebruik VortexLab/andere dynamische trajecten, of reeds geëxtraheerde spectra.

## Input A — spectrum CSV

Kolommen:

- `k_rad_m` — golfgetal [rad m^-1]
- `omega_rad_s` — hoekfrequentie [rad s^-1]
- `power` — optionele positieve spectrale weight

## Input B — trajectory CSV

Kolommen:

- `time_s`
- `point_id`
- `x_m`, `y_m`, `z_m`

De analyzer resamplet iedere gesloten centerline op uniforme booglengte, verwijdert rigid translation/rotation met Kabsch alignment, projecteert de verplaatsing op normal/binormal directions, en bouwt vervolgens een 2D `(k,omega)` spectrum.

NPZ is ook ondersteund met arrays `xyz[T,N,3]` en `time_s[T]`.

## manifest.csv

```text
sample_id,family_id,topology,resolution_n,input_type,path,core_radius_m
run_300,knotA,BLINDED_001,300,trajectory_npz,data/run_300.npz,1.40897017e-15
run_600,knotA,BLINDED_001,600,trajectory_npz,data/run_600.npz,1.40897017e-15
run_1200,knotA,BLINDED_001,1200,trajectory_npz,data/run_1200.npz,1.40897017e-15
```

`topology` mag in de echte blind run een gecodeerd label zijn.

## Gates

1. positieve lage-k slope;
2. lineair model moet BIC-competitief zijn;
3. vrij power-law exponent moet nabij 1 liggen;
4. slope moet stabiel zijn tegen low-k cutoff;
5. intercept moet klein zijn ten opzichte van de spectrale schaal;
6. hoogste twee numerieke resoluties moeten convergeren;
7. kandidaat-snelheid moet over onafhankelijke families/topologieën reproduceerbaar zijn.

De fit vergelijkt tevens quadratic, linear+quadratic, power-law en optioneel `k^2 log(1/(k r_c))`. Hierdoor wordt een lineaire propagatiesnelheid niet afgedwongen.

## Blind protocol

```cmd
run_all.cmd C:\path\to\campaign outputs_my_run
```

Dit doet install -> blindness audit -> tests -> blind fit -> plots -> SHA-256 lock en **stopt voor unblinding**.

Controleer daarna `outputs_my_run\blind_results.json` en `blind_lock.json`. Pas daarna:

```cmd
run_unblind.cmd outputs_my_run
```

De unblinder weigert te draaien wanneer het blind-resultaat na het locken gewijzigd is.

## Verdicts

- `BLIND_REJECTS_UNIVERSAL_LINEAR_SPEED`: modelvorm/convergentie faalt vóór targetvergelijking.
- `FALSIFIED_TARGET_SPEED`: blind kandidaat bestaat, maar 95%-CI ligt buiten de vooraf vastgelegde ±1% equivalentieband.
- `CONSISTENT_BUT_NOT_EQUIVALENT`: target valt niet duidelijk buiten de data, maar de CI is te breed.
- `CONSISTENT_WITH_TARGET_BUT_AUXILIARY_GATES_INCOMPLETE`: CI zit binnen ±1%, maar bijvoorbeeld een resolutieladder ontbreekt.
- `SURVIVES_STRONG_EQUIVALENCE_GATE`: alle vereiste blind gates slagen en de volledige 95%-CI ligt binnen ±1%.

Geen enkele survival-status is een bewijs van SST; het betekent alleen dat deze preregistered test de target niet falsificeert.

## Demo

`run_demo.cmd` maakt een volledig synthetische **decoy** campagne met een andere snelheid, zodat de unblinder aantoonbaar een mismatch kan falsifiëren.
