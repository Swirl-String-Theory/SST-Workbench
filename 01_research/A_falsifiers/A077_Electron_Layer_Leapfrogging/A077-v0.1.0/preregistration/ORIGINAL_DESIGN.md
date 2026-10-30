# SST Electron-Layer, Jet Analogy & Leapfrogging Unknot Falsifier

**Versie:** concept v0.1.0 — DESIGN_ONLY / NOT_EXECUTED / NOT_FROZEN  
**Catalogus-ID:** ID_PENDING, uitsluitend na controle van actuele `family_hierarchy.json` en `catalog_index.json`.  
**Framework:** SST Falsifier Framework v1.1.0 RC2; onafhankelijke runtime `_sst_runtime/` is **niet** opgenomen in deze ontwerpbijlage. De framework-release is een niet-gecertificeerde release candidate.  
**Scope:** 3D incompressibele inviscide Euler-stroming, constante effectieve vloeistofdichtheid, geen externe kracht, gladde eindige wervelkernen en zonder reconnectie. Absolute tijd t, geen Swirl-Clock-interpretatie vóór afzonderlijke sluiting.

## 1. Onderzoeksvraag

Kunnen dynamisch gekoppelde ongeknoopte wervelringen, inclusief (a) omkering van circulatie, (b) poloïdale/toroïdale stromingscomponenten en (c) leapfrogging/relatieve axialelaag-overgangen, robuuste discrete modale toestanden en een intrinsiek, onafhankelijk afleidbaar spinoriaal 2π/4π-gedrag opleveren?

**Nulhypothesen**  
H0a: circulatiesignatuur levert uitsluitend klassieke oriëntatie/dynamiek, geen spinorrepresentatie.  
H0b: ringvolgorde wisselt continu via leapfrogging maar er ontstaan geen numeriek convergente, symmetrie-onafhankelijke discrete interne niveaus.  
H0c: een 2π-rotatie van het klassieke Euler-veld levert dezelfde configuratie op; eventuele fase -1 vereist een **afzonderlijk gemotiveerde** niet-triviale toestandsbundel/representatie, niet een plot of keuze van signatuur.  
H0d: spritelike/jetlike morfologie is niet meer dan een stromingspatroon en impliceert geen elektron, elektrisch veld of plasmaontlading.

**Alternatieven (research-track):** H1a: gekoppelde poloïdale/toroïdale toestand draagt robuuste nieuw afgeleide modale invariant(en); H1b: dynamische, voor geometrie en numerieke resolutie robuuste voorkeursniveaus bestaan; H1c: configuratieruimte én dynamische/selectieregels dwingen een niet-triviale Z2-holonomie en corresponderende uitwisselingstransformatie af.

## 2. Fysisch model en ondubbelzinnige coördinaten

\[\partial_t\mathbf v+(\mathbf v\cdot\nabla)\mathbf v=-\frac{1}{\rho_{\!f}}\nabla p,\quad \nabla\cdot\mathbf v=0,\quad \boldsymbol\omega=\nabla\times\mathbf v,\quad \partial_t\boldsymbol\omega=\nabla\times(\mathbf v\times\boldsymbol\omega).\]

\[\Gamma(C_t)=\oint_{C_t}\mathbf v\cdot d\boldsymbol\ell,\qquad \frac{d\Gamma(C_t)}{dt}=0\]
voor materiaalcontouren bij gladde barotrope Euler-oplossingen. Materiële vorticiteitstopologie blijft behouden zolang de gladde flowmap een diffeomorfisme blijft; reconnectie is geen toegestane oplossingsstap.

Voor een torusvormige kern definieer op materiële, georiënteerde contouren:
\[\Gamma_{\mathrm{pol}}=\oint_{C_{\mathrm{pol}}}\mathbf v\cdot d\boldsymbol\ell,\quad \Gamma_{\mathrm{tor}}=\oint_{C_{\mathrm{tor}}}\mathbf v\cdot d\boldsymbol\ell,\quad \chi=\Gamma_{\mathrm{tor}}/\Gamma_{\mathrm{pol}}.\]
Bij \(\Gamma_{\mathrm{pol}}=0\) is \(\chi\) ongedefinieerd: afzonderlijk nul-/limietgeval. Exacte contourdefinities, oriëntaties en lab-assen moeten vóór FREEZE worden vastgelegd. CW/CCW is waarnemers-/asafhankelijk: maak die identificatie niet equivalent aan elektronspin, materie of antimaterie.

De doorsnede-lagen zijn twee **andere** grootheden:

1. \(N_i^{\mathrm{ord}}(t)\): axiale rang van ring \(i\) op tijd \(t\). Een sprong \(N\leftrightarrow N\pm1\) bij het passeren is louter geometrische boekhouding en **geen energiekwantisatie**.
2. \(N_i^{\mathrm{phys}}\): kandidaat intern modaal niveau. Definieer uitsluitend na blind ontdekte, resolutie-stabiele scheiding van dynamische invariante toestandsklassen. Geen voorgeschreven z-lagen of energiepotentiaal. Absolute \(z\)-niveaus kunnen niet intrinsiek worden gekozen in translatie-invariante, onbegrensde ongedwongen Euler-stroming.

### Onafhankelijke verticale transportoriëntatie (4-kwadrantcontrole)

Om de hypothese "CW/CCW plus stijgen/dalen tussen lagen" eerlijk te testen, registreer **drie** afzonderlijke grootheden:
\[\sigma_\Gamma=\operatorname{sgn}\Gamma_{\rm pol},\quad \sigma_z=\operatorname{sgn}(\dot z_{\rm cm}),\quad Q_z(A,t)=\int_A v_z\,dA.\]
Hierbij is \(\sigma_z\) een translatieoriëntatie van het ringcentrum, **geen interne circulatie**; \(Q_z\) is een lokaal axiaal volume-debiet met \([Q_z]=\mathrm{m^3/s}\). De vier kwadranten \((\sigma_\Gamma,\sigma_z)\in\{(+,+),(+,-),(-,+),(-,-)\}\) zijn puur klassieke configuraties. Hun aantal vier is niet gelijk aan de twee elektronische spinwaarden. Bereken terugstroom via \(\nabla\cdot\mathbf v=0\) en scheid lokale helical-flow van verplaatsing van het ringcentrum. Als alleen rang \(N^{\rm ord}\) verandert, is dat geen quantisatieresultaat.

### Canonieke schaalcontrole

\[r_c=1.40897017\times10^{-15}\,\mathrm m,\quad \lVert\mathbf v_{\!\boldsymbol{\circlearrowleft}}\rVert=1.09384563\times10^{6}\,\mathrm{m/s},\quad \rho_{\!f}=7.0\times 10^{-7}\,\mathrm{kg/m^3}.\]

\[\Gamma_0=2\pi r_c\lVert\mathbf v_{\!\boldsymbol{\circlearrowleft}}\rVert\approx9.68361920349\times10^{-9}\,\mathrm{m^2/s};\quad t_c=r_c/\lVert\mathbf v_{\!\boldsymbol{\circlearrowleft}}\rVert\approx1.28808867664\times10^{-21}\,\mathrm s.\]
Deze waarden zijn **conditionele SST-schaalankers**, geen onafhankelijke elektronvoorspelling. Gebruik vooral dimensieloze scans \(a/R,\Delta z/R,R_2/R_1,\chi\). De factor \(\rho_{\!f}\) beïnvloedt in de barotrope Euler-basis de druk-/energieschaal, niet de dimensieloze snelheidstrajecten.

## 3. Matrix van concurrerende modellen

| Model | Opstelling | Te meten | Negatieve controle |
|---|---|---|---|
| M0 | Eén eindige 0_1-ring; beide circulatietekens | Translation, kernbehoud, Kelvin, energie, helix | Tekenomkering onder ruimtelijke spiegeling |
| M1 | Twee coaxiale gelijkgerichte 0_1-ringen zonder extra toroïdale stroming | Leapfrogging, relatieve \(\Delta z/R\), radii en periode | Ongelijke sterkte / te grote ringafstand |
| M2 | Twee tegengesteld georiënteerde 0_1-ringen | Translatie, botsingsregime, stabiliteit | Geen leapfrog vooraf aannemen |
| M3 | Ring met niet-nul toroïdale én poloïdale materiaalcirculatie | Helicititeit, \(\chi\), eigenmodi, modensplitsing | \(\chi=0\), omkering van slechts één circulatie |
| M4 | Paar M1 met gecontroleerde interne toroïdale stroming | Koppeling leapfrogging ↔ twistfase ↔ order swap | Geschudde beginfasen; gematchte energie/circulatie |
| M5 | Drie ringen (alleen na M1–M4) | Meerlagige volgordetransities, relatieve modusfamilies | Continue aangepaste controle-oscillatoren |
| M6 | M1/M4 in vrij van binnenkomend momentum 3D-veld | Lokale verticale jet en return-flow; divergentiecontrole | Synthetische plaatjes zonder Euler-oplossing |

Gelijkgerichte ringparen zijn de orthodoxe leapfrogcontrole, niet het bewijs van elektronspin.

## 4. Drie afzonderlijke bewijsladders

**A — Klassieke stroming:** reproduceer vrije ring en ≥3 onderscheiden overnames op een vast fysisch eindtijdstip. Bepaal behoud, goed gedefinieerde kernradius, mate van vervorming en convergentie. Een regulariseerde Biot–Savart-filamentcode is eerst slechts een *modelprovider*; mechanisme-gate vereist later onafhankelijke eindige-kern Euler-veldcontrole.

**B — Lagen/eigenmodi:** volg \(z_i(t),R_i(t),a_i(t),\Gamma_{\mathrm{pol},i}(t),\Gamma_{\mathrm{tor},i}(t),H_i(t),E_i(t)\). Zoek modale clusters en spectral gaps uitsluitend in fysische, translatie-invariante observabelen; vergelijk tegen continue nullen met identieke dof en controleer seed, resolutie, core en scan-window. Ringrang-swaps tellen **niet** als kwantisatie. Vergelijk evt. multipliciteiten 1,3,5,7 pas als een rotatie-invariante achtergrond/operator bestaan; nooit vooraf als scoring labels.

**C — Spinoriaal:** construeer eerst de toegestane configuratieruimte \(\mathcal C\) van fysisch onderscheiden **geframe-de** 0_1-velden inclusief identieke-ringuitwisseling; bewijs/weerleg de noodzakelijke niet-triviale klasse van de 2π-rotatielus. Zoek vervolgens een **niet handmatig opgelegde** representatie \(\rho:\pi_1(\mathcal C)\to\{+1,-1\}\). Toon dat (i) 2π en 4π de vereiste monodromie dragen en (ii) de uitwisselingslus de passende klasse heeft. Een klassieke veldconfiguratie die na 2π hetzelfde is, of een quaternionvisualisatie die na 4π terugkeert, is geen bewijs. Een optioneel kwantisatiemodel mag als afzonderlijke, expliciet toegevoegde hypothese worden getest, nooit als resultaat van Euler alleen.

### Jet/sprite/orkaan vergelijking

Gebruik 'gigantic jet', 'sprite' en 'tyfoon' uitsluitend als **morfologische descriptoren**: as, spiraalvormigheid, verticale transportkolom, vertakkingsscore en return-flow. Atmosferische sprites en jets zijn *elektrische plasmaontladingen*, met ionisatie en elektromagnetische aandrijving; de ongedwongen Euler-provider heeft deze constitutieve natuurkunde niet. Een lokaal omhoog gericht transport moet worden getoetst op compensatiestroming bij \(\nabla\cdot\mathbf v=0\). De gelijkstelling 'elektron = giant jet' mag **niet** als fysische claim worden gepromoveerd.

## 5. Discretisatie, foutbudget en falsificatie

- Start: analytische ringcontrole, twee ringen, poloidal/toroidal, vervolgens pas 3 ringen; \(N\) = 256/512/1024 punten per filament of evenwaardige ruimtelijke rasterresoluties, met **vaste fysieke** eindtijd en tijdstappen omlaag volgens gemeten stabiliteitsrestrictie (bijvoorbeeld CFL). Voor volledig Euler-vloeistofveld extra roosterreeks en buffer tot rand.
- Preregister als **ontwerpgrenzen**: \(|\Delta\Gamma|/|\Gamma_0|\le5\times10^{-3}\), \(|\Delta E|/|E_0|\le10^{-2}\) bij eindige energie, en \(|\Delta H|/|H_0|\le2\times10^{-2}\) alleen voor \(H_0\ne0\). Voor nulheliciteit absolute fouttolerantie uit schaal \(\Gamma^2\) gebruiken. Drift-bewaking afzonderlijk van discretisatiefout; tolerantie aanpassen vereist nieuwe preregistratie.
- Ruimtelijke en temporele convergentie als **aparte** gates. Beoogde relatieve verandering bij laatste twee verfijningen \(\le2\%\) op primaire dynamische observabelen, \(\le1\%\) voor temporele reeks. Gebruik een gedefinieerde absolute fout voor observabelen met nuldoorgangen; meet behoud onafhankelijk.
- Respecteer core radius, minimum niet-lokale afstand, materiaalframes en centerline-stretching. Overlap/intersectie wordt niet stilzwijgend als reconnectie gesimuleerd; meet verlies van modelgeldigheid en markeer ONBEOORDEELBAAR.
- Falsificeer fysieke lagen als gap/multimodaliteit verdwijnt bij resolutie-, seed- of kernradiuscontrole, als alleen \(N^{\mathrm{ord}}\) verandert, of als 'laaggrenzen' meeschuiven met een willekeurige gekozen z-offset.
- Falsificeer H1c in de geteste configuratieruimte wanneer de noodzakelijke niet-triviale rotatie- en uitwisselingseigenschap afwezig is. Als topologische berekening of kwantisatiestructuur niet beschikbaar is: **UNRESOLVED**, geen 2π/4π-PASS.
- Een 2-of-3-backend PASS is een **technische uitvoeringsvoorwaarde**, geen wetenschappelijke kwalificatie. Python NumPy FP64 en echt onafhankelijke C++17/pybind11 implementatie zijn minimumpaar; Intel Arc XPU optioneel derde screeningbackend. Geen GPU-FFTs of lege wrappers meetellen.

## 6. Framework v1.1.0 gate-mapping

| Frameworkgate | Concrete, preregistreerbare vraag | Gating |
|---|---|---|
| G0 | Embedded `_sst_runtime/` + protocol exact gehasht, immutable run ID | FAIL_CLOSED |
| G1 | Exacte analytische geometrie-generator en E010/adapterpin indien gebruikt | BLOCKED als ongeverifieerd |
| G2 | Dimensioneel, Kelvin/ringbenchmark, core/singulariteits- en algebra-controle | Geen geclaimde spin |
| G3 | Blind analyse van leapfrog, modale splitsing en geometrisch versus intrinsiek N | H0/H1 op vooraf gekozen observabelen |
| G4 | Vooraf apart gehouden parameters/provider en onafhankelijk modelcontrol | Geen pseudo-replicatie |
| G5 | Werkelijk uitgevoerde C++ FP64 wetenschappelijke kernel en parity | Geen fallback naar Python |
| G6 | Intel XPU of CUDA als GPU-screening, dtype en device eerlijk geregistreerd | Niet nodig om FP64 te claimen |
| G7 | Werkelijke onafhankelijke bron-/oplossingsfamilie; anders UNRESOLVED | Refinement is geen replicatie |
| G8 | 3D finite-core Euler-provider, afzonderlijke ruimte-/tijdconvergentie en mechanisme | Filament-only bewijs onvoldoende |
| G9 | Reveal strikt na qualified blind gate en commitmentverificatie | Geen promotiestap bij UNRESOLVED |

Eventueel numerieke G10 uit framework-RC1 is specifiek bedoeld voor de A999 E010-control; niet zonder nieuwe implementatie als ingebouwde electron-spin-gate claimen. Gebruik het lokale science contract om subgates P01–P07 expliciet op G2–G8 af te beelden.

### Interne primaire wetenschappelijke subgates

- P01: vrijering en circulation/finite-core baseline sluit.
- P02: gelijkgerichte leapfrogging met ≥3 voltooide overnames en convergentie; of negatief in gescand regime.
- P03: negatieve controle met tegenovergerichte ringen karakteriseert afwijkende baan (geen verwachte overnames ingesmokkeld).
- P04: toroïdale/poloïdale koppeling produceert wel/niet nieuwe, convergente modale eigenwaarden bij gelijkgehouden invarianten.
- P05: fysisch nieuwe N-niveaus blijken robuust of worden gefalsifieerd na subtractie van rank-swaps.
- P06: 2π/4π rotatiepad en identieke-uitwisseling leveren bewezen/topologisch ondersteunde sign-structuur, of UNRESOLVED/FAIL binnen scope.
- P07: jet/sprite morfologie houdt volumebalans en bevat geen ongefundeerde EM-conclusies.

## 7. Uitvoering na implementatie (NIET uitgevoerd in deze ontwerplevering)

Vanuit de exacte releasebron (geen onjuiste CANONICAL_FROZEN-claim):

```cmd
python tools\new_falsifier.py ID_PENDING electron_layer_leapfrogging "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\ID_PENDING_electron_layer_leapfrogging\ID_PENDING-v0.1.0" --profile gpu --version v0.1.0
```

Vervang `ID_PENDING` pas na cataloguscontrole. Vul daarna **vóór FREEZE** alle frameworkbestanden in: `science_contract.json`, `source_contract.json`, `gate_plan.json`, `blind_policy.json`, `falsifier.toml`, `report/FALSIFIER_REPORT.tex` (alle 16 secties), `experiment/backend_matrix.py`, daadwerkelijke Python/C++/GPU-kernels. Bouw Python en C++ onafhankelijk; controleer MSVC `py::ssize_t` i.p.v. globale `ssize_t` en expliciete setuptools package discovery.

```cmd
run_all.cmd BACKEND_PREFLIGHT
run_all.cmd ATLAS_VERIFY
.venv\Scripts\python.exe -m pytest -q tests
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
```

`ATLAS_VERIFY` vereist de pin van E010-v0.4.0 plus `PKLSA_Universal_Atlas_Adapter_v0.1.0` indien atlasgeometrie wordt gebruikt. Voor puur analytische ringen moet atlas-NA expliciet en reproduceerbaar met de framework-policy worden afgehandeld, niet omzeild. Resultaatpad volgens huidige Framework: `<name>_<version>-outputs/` plus parent `_BLIND.zip`, bij toelating `_REVEALED.zip`, onafhankelijke SHA-256-manifests en volledige `FALSIFIER_REPORT.pdf` op het publicatiepad. RC2 progress/heartbeat (15 s) en `RUN_PROGRESS.jsonl` bewaren. PDF fallback is diagnostisch, geen certificering. Eerdere runs niet overschrijven.

**Niet uitgevoerd:** geen kernels, FREEZE, statistische resultaten, lokale catalogusaudit, Windows target-hardware-gates of uitwisselingstopologiebewijs.

## 8. Externe bronnen voor mathematische vergelijking

\begin{thebibliography}{9}
\bibitem{Davila2024} J. Dávila, M. del Pino, M. Musso and J. Wei (2024), *Leapfrogging vortex rings for the three-dimensional incompressible Euler equations*, Communications on Pure and Applied Mathematics 77, 3843--3957, doi:10.1002/cpa.22199.
\bibitem{Butta2025} P. Butta, G. Cavallaro and C. Marchioro (2025), *Leapfrogging Vortex Rings as Scaling Limit of Euler Equations*, SIAM Journal on Mathematical Analysis 57, 789--824, doi:10.1137/24M1642391.
\bibitem{Maggioni2010} F. Maggioni, S. Alamri, C. F. Barenghi and R. L. Ricca (2010), *Velocity, energy, and helicity of vortex knots and unknots*, Physical Review E 82, 026309, doi:10.1103/PhysRevE.82.026309.
\bibitem{Niemi2005} A. J. Niemi (2005), *Exotic Statistics of Leapfrogging Vortex Rings*, Physical Review Letters 94, 124502, doi:10.1103/PhysRevLett.94.124502.
\bibitem{FinkelsteinRubinstein1968} D. Finkelstein and J. Rubinstein (1968), *Connection between Spin, Statistics, and Kinks*, Journal of Mathematical Physics 9, 1762--1779, doi:10.1063/1.1664510.
\bibitem{Neubert2011} T. Neubert and O. Chanrion (2011), *The properties of a gigantic jet reflected in a simultaneous sprite: Observations interpreted by a model*, Journal of Geophysical Research: Space Physics 116, doi:10.1029/2011JA016928.
\end{thebibliography}

Framework-bron: https://drive.google.com/drive/folders/1BAuLj3jgvkCh5yFnNCIYhAgVYnx92i6N (v1.1.0). RC2: https://drive.google.com/drive/folders/1ulcVaU-F-Y4kUbAP4hTwWk1ysG_SNIL_.
