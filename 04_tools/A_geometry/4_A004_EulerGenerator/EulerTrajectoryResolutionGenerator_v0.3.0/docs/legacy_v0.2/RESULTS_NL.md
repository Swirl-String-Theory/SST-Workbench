# Resultaten en kwalificatielimieten — v0.2.0

## Werkelijk uitgevoerd in deze bouwomgeving

| Provider | Studie | Uitgevoerde N | Voltooide runs | Scope |
|---|---|---|---:|---|
| A075-v0.2.10 | spatial | 16, 24, 32 | 3 | korte echte Euler/tracer-smoketest |
| A077-v0.1.2 | spatial | 16, 24, 32 | 3 | korte echte Euler/tracer-smoketest |
| A077-v0.1.2 | temporal | 32; dt, dt/2, dt/4 | 3 | machineprecisie in deze zeer korte tijd |
| A077-v0.1.2 | core | 32; 0.8, 1.0, 1.2× | 3 | gewijzigde inputprofielen, geen kernlimiet |
| A077-v0.1.2 | box | 24, 32, 40; 0.75,1,1.25× | 3 | domeingevoeligheid |
| A077-v0.1.2 | perturb | 32; 0, 0.005, 0.02; 3 seeds per amplitude | 7 | afzonderlijke initiële veldperturbaties |
| **Totaal** | | | **22** | software- en uitvoercontroles, niet fysisch gecertificeerd |

Alle trajecten en diagnostiek zijn uit echte **gepinde providerkernels** berekend (niet uit gesimuleerde of vooraf opgeslagen uitslagwaarden). Elke run heeft opnieuw geëvalueerde bestandsmanifests en bronherkomst. Per geval was de genormaliseerde integratietijd `T=0.002` met aanvankelijke stap `dt=0.001`. Dat tijdvenster is veel te kort voor een dynamische stabiliteitsconclusie.

**Noot:** een eerder gestarte volledige A075-smokecampagne is afgebroken voordat alle vijf assen klaar waren en wordt **niet** als geslaagd of opgenomen in de resultaten beschouwd.

### Overeenkomende-trajectverschillen

- A075 spatial n16→n24 tegenover n24→n32: verhouding van eindpositieverschillen ≈ **0.513**; geometrische Ruban-kern bij n32 blijft <1 roosterafstand breed. Geen fysische bewijswaarde.
- A077 spatial n16→n24 tegenover n24→n32: verhouding ≈ **1.039**; de afwijking daalt niet op deze ongekwalificeerde roosters.
- A077 temporal: de eindpositieverschillen bedragen respectievelijk circa **4.0×10⁻¹⁶** en **6.7×10⁻¹⁶** maal de kleinste kernradius. Dit is de precisiebodem; er kan **geen** orde uit worden gemeten. De software rapporteert `PRECISION_FLOOR_ORDER_UNMEASURABLE`.
- De drie gevoeligheidsassen `core`, `box` en `perturb` leveren elk numerieke padverschillen, zonder daaruit automatisch self-confinement af te leiden.

### Planningsdrempels, niet uitgevoerd

| Provider | Vier nominale punten / radius | Geschatte RAM, indicatief | Vier heuristisch bandbegrensde punten / radius | Geschatte RAM, indicatief |
|---|---:|---:|---:|---:|
| A075 | N=260 | 31.25 GiB | N=390 | 104.62 GiB |
| A077 | N=170 | 8.99 GiB | N=254 | 29.16 GiB |

Dit zijn **basis-N**. Een boxgrootte van 1.25× met ongeveer constant Δx leidt tot hogere N en hogere geheugenbehoeften. De werkelijke geheugenschaal kan afwijken; het programma gebruikt alleen een empirische preflightschatting.

Zelfs een positief tijd/spatial/core/box/perturb-resultaat is niet hetzelfde als een topologisch stabiele, materiële vortexbuis. Daarvoor zijn expliciete material-surface RK4-advectoren, heliciteits- en circulatieflux, kernradiusontwikkeling, perturbatierespons en externe referentie nodig. Spin-½ is een aparte, onopgeloste hypothese.
