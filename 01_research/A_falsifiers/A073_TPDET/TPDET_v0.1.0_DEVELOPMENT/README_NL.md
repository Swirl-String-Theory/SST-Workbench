# TPDET v0.1.0 — Topology-Preserving Directed Energy Transfer

**Status: DEVELOPMENT / NOT CERTIFIED — 24 oktober 2026.**

Een reproduceerbare, geblindeerde *ontwikkelproef* voor de vraag of gekoppelde gesloten vortexfilamenten snelle, gerichte energieoverdracht kunnen vertonen zonder reconnection of dissipatie voor te schrijven. De huidige code **bewijst dit nog niet**. De bestaande bronnen zijn geïnspecteerd en hun rekenkern is gebruikt in afzonderlijke controles.

## Bronnen en integraal hergebruik

- **Finite-core filamenten**: `Borromean_Blind_Clock_Falsifier_v0.1.0.zip`, oorspronkelijke `src/dynamics.py`, `src/geometry.py`, C++ `native/biot_savart.cpp` en Linux `.so`. Middenpunts-Biot–Savart met Rosenhead-core-softening, RK4 (Runge–Kutta van orde vier), multicomponent, zonder reconnection-code. Eigenlijk een geregulariseerde filament-surrogaat, **geen volledige Euler-velddynamica**.
- **Euler (volledig andere controle)**: `A006_VCCR_v0.2.0_Independent_Euler_Qualification_FULL.zip` met onveranderde `references/euler_qualification.py`. Deze bevat een exacte analytische affiene incompressibele Euler-stroming met onafhankelijke deeltjesintegratie, niet een geknoopte Euler-oplossing. Het nieuwe `euler_energy_flux.py` toetst de lokale energiebalans van deze exacte stroming numeriek.
- **Seed-geometrie**: trefoil `3_1` uit A006 `.xyz`, torusknoop `T(2,5)` uit bestaande A003 VortexLab-record `torus_2.5`, Borromeaanse `L6a4`-kandidaat uit A003 `ideal_knots_data.js`. De twee laatstgenoemde zijn gedecodeerde Fourier-representaties en geen byte-identieke upstream XYZ-bronnen. Zie `references/provenance.json` voor afkomst, SHA-256 (Secure Hash Algorithm, 256-bit), kwalificaties en tekortkomingen.
- **Bestaande PKLSA (Parametric Knot-Link Seed Atlas)** E010-v0.3.1 en **SKLSA (Selected Knot-Link Seed Atlas)** E011-v0.3.0 zijn als kwalificatiebronnen in Google Drive geïdentificeerd, maar hun volledige lokale Workbench-paden/hashes zijn in deze standalone run **niet** opnieuw gevalideerd. Daarom geen claim dat de geselecteerde A003-seeds PKLSA/SKLSA-gekwalificeerd zijn.
- Framework v1.0.7 `CANONICAL_FROZEN` is bekeken. Dit is een **standalone development harness**, geen via framework gegenereerde/gefreeze-de instantie. Het krijgt pas een Falsifier A-nummer na een registry-controle.

## Geteste armen en blindering

Vier vaste armen (alle circulaties +1 dimensieloos, kernregularisatie `a=0.12`, `N=128` punten per component, `dt=0.015`, `T=8`; alle segmenten worden op gelijke numerieke resolutie per component genomen):

1. Twee coaxiale ringen voor het *leapfrogging*-controlefenomeen (6 positiewisselingen in het gebruikte venster).
2. Trefoil `3_1` plus dezelfde type ontvangerring.
3. Torusknoop `T(2,5)` plus ontvangerring.
4. Borromeaanse `L6a4`-link plus ontvangerring.

De labels worden **vóór** de vier berekeningen met een willekeurig geheim gemapt op `BX_*` identifiers en met een commitment vastgelegd in `LOCK.json`. De resultaten in `BLIND` bevatten geen labels, aantal componenten, componentgewijze geschiedenis, linkingmatrix of geopenbaarde ring-swapstatistiek. `SEALED/mapping.json` wordt apart geleverd. *Pas onthullen na vooraf schriftelijk vastgelegde analysebeslissingen.*

**Belangrijke confounder:** deze armen hebben verschillende componentaantallen, vorticiteitsverdelingen, begingeometrie en bron-ontvanger nabijheid. Een verschil is *niet* een zuiver effect van topologie. Een matched-geometry/energy/circulation vervolgexperiment is vereist.

## Wiskundig gedefinieerde indicatoren

Voor de filament-surrogaat wordt berekend

\[
H_a=\frac{\rho_f}{8\pi}\sum_{i,j}\Gamma_i\Gamma_j
\oint_{C_i}\oint_{C_j}\frac{d\boldsymbol\ell_i\cdot d\boldsymbol\ell_j}{\sqrt{|\mathbf x_i-\mathbf x_j|^2+a^2}}.
\]

Hier geldt expliciet **\(\rho_f=1\) in dimensieloze simulatie-eenheden**. Dit is niet automatisch de ruimtelijke energiedichtheid van een volledig Euler-veld en niet het aangetoonde transport door een fysisch controleoppervlak. De max. verandering van een componentgewijze zelfenergie, gedeeld door `H_a(t=0)`, heet daarom **`self_energy_exchange_proxy`**, niet bewezen energieoverdracht. De term `H_a` in de software is een discreet benaderde Hamiltoniaan en geen gecertificeerd exact behouden numeriek invariant.

Voor de bestaande affiene Euler-controle geldt de afzonderlijk getoetste identiteit

\[
\frac{d}{dt}\int_V \frac{\rho_f |\mathbf u|^2}{2}dV
+\oint_{\partial V}\left(\frac{\rho_f|\mathbf u|^2}{2}+p\right)\mathbf u\cdot\mathbf n\,dA=0.
\]

De numerieke quadratuur over een vast kubisch volume levert maximale relatieve restfout **2.032×10⁻¹¹** bij drie gekozen tijdstippen. Dat bevestigt uitsluitend deze exacte Euler-controle, **niet** de knoop/filamentveld-energiebalans.

## Precommitted stopcriteria, vóór reveal

- `G0`: geometrie aanwezig plus hashes verifieerbaar.
- `G1`: originele native kernel draait of transparante Python-fallback.
- `G2`: volledige looptijd zonder vroegtijdige stop.
- `G3`: minimale **intercomponent polygonsegmentafstand** op gesamplede momenten > `2a`; geen tijdcontinue of intra-component-topologiecertificering.
- `G4`: Gauss-pairwise-linkingafwijking <0.08 en initiële integerconsistentie <0.08; **geen** toets van Milnor triple linking.
- `G5`: \(\max_t|H_a(t)-H_a(0)|/|H_a(0)|\le 0.02\). De drempel is een dev-prekwalificatie, **niet** nauwkeurig genoeg voor fysische conclusies.
- `G6`: minstens twee relatieve positie-omwisselingen in de ringcontrole; geen gesloten baan/Floquetbewijs.
- `G7`: daadwerkelijke **gerichte Euler-energietransportflux** bij knoopconfiguratie — `NOT_RUN`.
- `G8`: onafhankelijke **volledige 3D Euler-validatie** van de geknoopte kern — `NOT_RUN`.
- `G9`: topologische certificering van elke gesloten kromme, inclusief eventuele Milnor-invariant van Borromeaanse links — `NOT_RUN`.
- `G10`: tijd/ruimte/core-onafhankelijkheid voor alle vier armen — `NOT_RUN` (aparte leapfrogging-resolutieladder aanwezig).
- `G11`: astrophysische, thermische en stralingsvoorspellingen — `NOT_CLAIMED`.

Tijdafhankelijke minimumafstand wordt op `record_every` uitvoerpunten gecontroleerd, niet op alle Runge–Kutta-substappen. Dus er kan **niet** worden beweerd dat ongeobserveerde snijmomenten onmogelijk zijn.

## Ontwikkelresultaten (BLIND)

Met de vaste instellingen halen **2/4** armen de volledige horizon. De andere **2/4** stoppen bij `t≈2.1013` vanwege \(H_a\)-drift \(>2\%\), niet vanwege een gedetecteerde intercomponent-kernoverlap. De volledige rijwaarden, inclusief component-neutrale geschiedenis, zitten in `output/TPDET_v0.1.0_R2/BLIND/summary.json` en `BLIND/summary.csv`.

De leapfrogging-controle toont zes omwisselingen bij `N=64,128,192`; op de samengestelde resolutieladder neemt de maximale relatieve energieproxy-drift af van \(4.9025\times10^{-5}\) (`N=64,dt=0.03`) tot \(5.2959\times10^{-6}\) (`N=192,dt=0.015`). De leapfrogging-swapvolgorde is een *numerieke demonstratie*, niet een bewezen analytisch exacte baan.

## Uitvoeren op Windows

In PowerShell of `cmd`, vanuit deze map:

```bat
py -3 -m pip install -r requirements.txt
build_native.cmd
py -3 -m pytest -q tests
py -3 euler_energy_flux.py --out output\euler_flux_NEW.json
py -3 references\euler_qualification.py --out output\affine_NEW --case both --steps-per-unit 200
py -3 tpdet.py --n 128 --dt 0.015 --t-end 8 --core 0.12 --record-every 10 --out output\TPDET_NEW_BLIND
```

`run_all.cmd` voert tests, fluxcontrole en een **nieuwe** geblindeerde run uit. De bestaande `LOCK.json`/`SEALED` outputroot kan niet stil worden overschreven. Gebruik voor iedere volledige nieuwe run een nieuwe `--out`.

Het bijgevoegde `libbs_native.so` is Linux-only. Op Windows `build_native.cmd` gebruiken: C++17-compiler MinGW `g++` of Microsoft `cl`. Bij afwezigheid valt de code expliciet terug op Python, met veel lagere snelheid. C++-native uitvoering is geen Intel SYCL (Single-source C++ for Heterogeneous Computing) GPU/XPU-pariteitsbewijs.

## Minimale volgende kwalificatiestap

1. Bevries de `BLIND` resultaten; analyseer convergentie en stopoorzaken voordat `SEALED` wordt geopend.
2. Repareer of kwalificeer de twee voortijdig afgebroken gevallen *zonder* hun identiteit op grond van uitkomst te tunen.
3. Kwalificeer alle bronseeds via PKLSA/E011 inclusief knooptype, segmentafstand, Borromean Milnor \(\bar\mu_{123}\) en onafhankelijke herkomst.
4. Koppel het filamentmodel aan een druk-Poisson en volume-geïntegreerde Euler-energy-flux-solver voor werkelijk gerichte overdracht. Gebruik een vaste controlevolumeconfiguratie en integrale energiebalans.
5. Bouw als volgende stap pas een framework-gefreeze-de, registreerde productie-instantie; behoud de development-outputs als negatieve/provisorische bewijsstukken.

## Bronnen

```latex
\bibitem{Vardi2026}
G. Vardi et al.,
``Observation of a Solar-like Magnetic Reconnection Event in an AGN Corona with XRISM,''
The Astrophysical Journal Letters \textbf{1007}, L23 (2026).
doi:10.3847/2041-8213/ae8f44.

\bibitem{Davila2024}
J. D\'avila, M. del Pino, M. Musso, and J. Wei,
``Leapfrogging vortex rings for the three-dimensional incompressible Euler equations,''
Communications on Pure and Applied Mathematics \textbf{77}, 3843--3957 (2024).
doi:10.1002/cpa.22199.

\bibitem{Saffman1992}
P. G. Saffman, \textit{Vortex Dynamics}, Cambridge University Press (1992).
doi:10.1017/CBO9780511624063.
```
