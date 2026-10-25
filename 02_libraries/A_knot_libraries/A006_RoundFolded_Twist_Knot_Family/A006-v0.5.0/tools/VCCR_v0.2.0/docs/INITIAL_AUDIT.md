# VCCR v0.1.0 — initiële numerieke audit

## Canonieke, conditionele calibratie

- `r_c = 1.40897017e-15 m`
- karakteristieke swirl snelheid `|v| = 1.09384563e6 m/s` aangenomen als **kernrandsnelheid** voor deze *hypothetische* uniforme-core referentie
- ideale trefoil `R_d = 16.3714672385` (ratio booglengte / diameter; numerieke benadering; geen exacte mathematische minimumwaarde)
- `L0 = 4.6133817956357553e-14 m`
- `V0 = 2.877218654223102e-43 m^3`
- `Gamma0 = 9.683619203488876e-09 m²/s`
- `mean_omega0 = 1.5526881310766143e21 s^-1`

De omvang van `V0` en `Gamma0` volgt volledig uit de gekozen beginwaarden; ze zijn niet onafhankelijk gemeten.

## Variabele materiaalbooglengte bij constant V en Gamma

| L/L0 | L (m) | a (m) | omega (s^-1) | R_d=L/(2a) |
|---:|---:|---:|---:|---:|
| 1 | 4.6133817956e-14 | 1.4089701700e-15 | 1.5526881311e21 | 16.3714672385 |
| 2 | 9.2267635913e-14 | 9.9629236170e-16 | 3.1053762622e21 | 46.3055020093 |
| 4 | 1.8453527183e-13 | 7.0448508500e-16 | 6.2107525243e21 | 130.971737908 |

## A006 v0.5.0a XYZ bronaudit (geometrische eenheden, GEEN SI)

| Bron | Componenten | Aantal beads | Totale geometrische lengte |
|---|---:|---:|---:|
| `KNOT_3_1_N0512_ORIG.xyz` | 1 | 512 | 980.4795485 |
| `KNOT_5_2_N0512_ORIG.xyz` | 1 | 512 | 850.0538164 |
| `KNOT_6_1_N0512_ORIG.xyz` | 1 | 512 | 967.1521431 |
| `LINK_5_5_6_BALANCED_N0512_ORIG_CPFIXED61.xyz` | 3 | 1608 | 6328.0117984 |

Verschillende losse brongeometrieën hebben niet noodzakelijk dezelfde schaalcalibratie, hoeveelheid vortexvloeistof of circulatie. Geen metertabel wordt uit bovenstaande lengtes geconstrueerd.

## Voorbeeld AMECH 5_2 (NIET fysisch gecertificeerd)

De originele N512-geom. lengte 850.0538164 en de gebruikers-AMECH N512-export van ongeveer 588.84 geven een ratio ~0.693. Onder de **extra en onbewezen aannames** dat dit dezelfde materiële vortexbuis is en beide XYZ de identieke coördinaatschaal behouden, zou `a_final/a_initial ~1.2015` volgen. Dit is enkel een rekenvoorbeeld, **geen meting** van de kernradius of van Kelvin-behoud. Voor de echte vergelijking zijn materiële vorticiteitsflux- en doorsnedemetingen vereist.

## Tests

7 unit tests PASS, installatiecontrole op een dummy A006-project PASS, herhaalde installatie idempotent, tamper refusal PASS. Geen solver, Ridgerunner of KnotPlot-dynamica in deze versie uitgevoerd.
