# Geregistreerd testprotocol — Euler Trajectory v0.2.0

## Status

Software: SOURCE-LOCKED DEVELOPMENT; fysieke dynamica: UNRESOLVED. Deze generator is een zijtak en vervangt Framework v1.1.0 G0–G10 van A075/A077 niet. Geen nieuwe versie van die falsifiers wordt aangemaakt. Dit protocol moet **vóór** fysieke kwalificatie worden bevroren en kan voor een afzonderlijke toekomstige blindrun worden gecanoniseerd.

## Schalen en resolutie

Bij kubische periodieke zijde L en N³ roosterpunten geldt Δx = L/N. Voor een relevante radius a is C_nom = aN/L. Voldoende kleine truncatiefout kan niet uit C_nom alleen worden afgeleid. Voor C_nom ≥ 4: N≥ceil_even(4L/a). Een strictere *heuristische* 2/3-spectrale-bandlimiet C_band=(2/3) C_nom≥4 vereist N≥ceil_even(6L/a). De afsnijding verandert het aantal behouden golftallen, niet letterlijk de fysieke roosterafstand.

A075: geometrische Ruban-minorradius 77/500; onafhankelijke solver-Gaussianbreedte 0.42. A077: kleinste initieel ingestelde Euler-ringcore 0.19 (modelparameter). Beide dynamische bronnen leveren periodieke Fourier–Galerkin-Euler-simulaties, geen geïdentificeerde materiële topologische kernen.

## Studieassen en primaire onafhankelijke variabelen

| Studie | Varieert | Vast houden | Meetwaarden | Statusmaximum |
|---|---|---|---|---|
| spatial | N (3 waarden) | L, a, dt, t_final, init en markers | traject RMS, eindtijdverschil, energie/divergentie, C_nom | numeriek verfijningsscreen |
| temporal | dt, dt/2, dt/4 | N, L, a, t_final, init en markers | tijdaligned trajecten, verfijningsratio | numeriek verfijningsscreen |
| core | smoothing/profilebreedte x(0.8,1.0,1.2) | N, L, dt, t_final en fysieke seed | gevoeligheid en heliciteit/energie | modelgevoeligheid, **geen** convergentie |
| box | L x(0.75,1.0,1.25) | bijna gelijke Δx, a, fysieke seed, t_final | maximale padverschuiving, periodieke-imagegevoeligheid | domeingevoeligheid |
| perturb | amplitude 0, 0.005, 0.02; 3 seeds per niet-nul waarde | N, L, a, t_final, dt | volledige veldrespons, padverschil, energie, heliciteit | dynamische respons, geen restoring-force bewijs |

### Stop/kwalificatiecriteria

0. **PROVENANCE**: laat uitsluitend pinned solverhashes en A075-seedmanifest toe; geen generieke importfallback.
1. **MEMORY/CFL**: weigering boven begroting vóór allocatie; per stap niet-eindig/CFL > 0.20 => FAIL_RUN, geen kunstmatige oplossing.
2. **TEMPORAL**: alle drie niveaus bij identiek eindtijdstip; eindpuntverschil <=0.02 kleinste radius en verhouding laatste/vorige verschil <=0.75 is alleen een *verkennende* drempel. Onderzoek asymptotische orde apart bij grotere tijdvensters.
3. **SPATIAL**: de kleinste radius voldoende op ten minste het fijnste rooster, bij voorkeur op alle drie; alleen kleine verschillen na verfijning kwalificeren niet zolang core/box onafhankelijk zijn.
4. **CORE**: rapporteer max|ΔX|/radius tegenover basis; gevoeligheid is uitkomst, geen FAIL van Euler of SST zonder natuurkundig bepaalde core.
5. **BOX**: test beide zijden met expliciete periodieke-afstand; accepteer niet louter minder afwijking door grotere numerieke fout.
6. **PERTURB**: registreer seeds, amplitude, veldnorm; verschillende tracers en tijdstappen zijn géén onafhankelijke realisaties. Een nulverschil na één korte tijd is geen terugdrijvende kracht.
7. **MATERIAL_CORE**: ontbreekt nog: gesloten materiële buis, vorticiteitstangentie, circulatie op materiële lussen, volumetransport, topologie en perturbatiestabiliteit over lange fysieke tijd. Status: UNRESOLVED.
8. **INDEPENDENT_SOURCE**: tweede Euler-provider met dezelfde conditie + periodiek/ongelimiteerd vergelijking. Status: UNRESOLVED.

### Misleidende conclusies uitsluiten

Een klein relatieve energiedrift komt bij een getrunceerd Euler-systeem ook voor bij onfysische initiële wervelprofielen; het is geen bewijs van zelfconfinement. Vergelijking tussen A075 Ruban en A077 ringvelden is geen onafhankelijke reproductie van dezelfde beginsituatie. A077's CW/CCW en toroïdaal/poloïdaal leveren geen spinorrepresentatie zonder onafhankelijke configuratieruimte- en holonomiebewijs.
