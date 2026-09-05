# SST Dimensionless Dynamic Predictions v0.2.0 — Infinite Background Vortex

Deze release breidt de v0.1.0-harness uit met een opgelegde achtergrondvortex met
\(R_{\rm bg}\to\infty\). Dit is de overal geldige binnenste Rankine-tak:

\[
\mathbf u_{\rm bg}=\boldsymbol\Omega_{\rm bg}\times(\mathbf x-\mathbf x_0),
\qquad
\boldsymbol\zeta_{\rm bg}=2\boldsymbol\Omega_{\rm bg}.
\]

De door de gebruiker opgegeven combinatie

\[
\alpha c r_c=2v_{\circlearrowleft}r_c
\]

heeft de dimensie van circulatie, niet van vorticiteit. De fysisch consistente
vertaling is

\[
\zeta_{\rm bg}=\frac{\alpha c r_c}{r_c^2}
=\frac{\alpha c}{r_c}
=\frac{2v_{\circlearrowleft}}{r_c},
\qquad
\Omega_{\rm bg}=\frac{v_{\circlearrowleft}}{r_c}.
\]

Wanneer de circulatie-eenheid de canonieke
\(\Gamma_0=2\pi r_cv_{\circlearrowleft}\) is en de lengte-eenheid \(r_c\), is

\[
\zeta_{\rm bg}^*=\frac{\zeta_{\rm bg}r_c^2}{\Gamma_0}=\frac1\pi,
\qquad
\Omega_{\rm bg}^*=\frac1{2\pi}.
\]

**Analytische guard:** een uniforme solid-body-vorticiteit voegt alleen een
rigide rotatie toe. Omdat de relative-equilibrium-gate vrije translatie en
rotatie aftrekt, hoort het vormresidu invariant te blijven. Deze release test
dat expliciet. Een stabiliserend achtergrondveld vereist shear, strain, een
finite-radius overgang of een andere niet-rigide ruimtelijke structuur.

---

# SST Dimensionless Dynamic Predictions — v0.1.0

**Status:** `[RESEARCH TRACK / NUMERICAL HARNESS]`  
**Doel:** de eerste verdedigbare SST-voorspelling zoeken in **dimensieloze dynamische verhoudingen**, zonder \alpha, \(m_e\), \(G\), \(L_p\), \(a_0\) of een andere targetconstante als invoer te gebruiken.

> Dit pakket is geen claim dat een elektron reeds als vortexknoop is afgeleid. Het is een preregistreerbaar falsificatie- en ratioframework waarmee eerst de voorspellende inhoud van de knoopdynamica zelf kan worden getest.

## 1. Kernconclusie uit de voorafgaande audit

De centrale conclusie van het laatste antwoord is:

\[
\boxed{
\text{SST kan echte niet-algebraïsche dynamische berekeningen uitvoeren,}
\quad
\text{maar heeft nog geen gevalideerde onafhankelijke fysieke voorspelling.}
}
\]

Het relevante onderscheid is:

\[
\boxed{
\text{algebraïsche herschrijving}
\neq
\text{niet-triviale modelberekening}
\neq
\text{gevalideerde fysieke voorspelling}.
}
\]

De huidige SST-sterkte ligt vooral in:

- echte dimensieloze modelberekeningen;
- expliciete dependency-audits;
- negatieve resultaten en falsificatiegates;
- het lokaliseren van de nog ontbrekende theorema's.

De huidige beperking is:

\[
\boxed{
\text{geen bestaande berekening levert reeds onafhankelijk }
\alpha,\ m_e,\ G,\ c\text{ of het atomaire spectrum.}
}
\]

## 2. De tien belangrijkste bevindingen

### 2.1 SST berekent wel degelijk nieuwe getallen

Biot--Savart-residuen, geometrische energieratio's, knot-action-ratio's, niet-lineaire fixed points en regulatorgevoeligheden zijn niet eenvoudig in CODATA verborgen. Zij zijn echte modeloutputs. Ze zijn alleen nog geen bevestigde uitspraken over elementaire deeltjes.

### 2.2 Statische ideal knots zijn geen dynamisch gecertificeerde deeltjes

In de eerdere audit slaagde de ronde ring voor de relative-equilibrium-gate, terwijl de statische \(3_1\)- en \(4_1\)-atlasvormen faalden. De belangrijke consequentie is:

\[
\boxed{
\text{ropelength-optimaal}
\not\Rightarrow
\text{dynamisch periodiek of relatief stationair}.
}
\]

Een fysieke knooptoestand moet eerst een oplossing, relative equilibrium, periodieke baan of relative-periodic orbit van één vastgelegde dynamica zijn.

### 2.3 De geometrische \(\alpha\)-formule is de sterkste onafhankelijke constantekandidaat

\[
\alpha^{-1}_{\rm lead}
=
\frac{8\pi}{3}\mathcal L_{3_1}
\approx137.15471
\]

is tijdens evaluatie \(\alpha\)-vrij en ligt circa \(866\) ppm van CODATA. Dat is interessant, maar de prefactor en correctietermen zijn nog niet uniek bepaald. De huidige CANON v0.8.34 classificeert dit terecht als een parameterlichte sub-per-mille coincidentie plus obstructieresultaat, niet als ppm-afleiding.

### 2.4 Het oude proton--neutronmodel bevat een echte ratio en die faalt

In de verhouding \(M_n/M_p\) vallen gemeenschappelijke calibraties weg. De oude topologische-volumeconstructie gaf circa \(3.6647\%\) afwijking. Dit is waardevol omdat het onafhankelijke residu daardoor werkelijk wordt getest en niet met één gemeenschappelijke schaal kan worden gerepareerd.

### 2.5 De lokale \(\beta_Q\)-selector is niet triviaal, maar zeer profielgevoelig

De eerder verkregen closure kan worden gereduceerd tot

\[
\beta_Q(\chi)
=
\frac{\chi^3}{2}
\exp\!\left[\frac{\pi^2\chi^6-1}{4}\right],
\qquad
\chi=\frac{a_{\rm core}}{r_c}.
\]

Rond \(\chi=1\) is de logaritmische gevoeligheid ongeveer \(17.8\). Eén onbepaalde geometrische parameter is dus al voldoende om \(c_T\) sterk te verschuiven of zelfs op \(c\) af te stemmen. Zonder onafhankelijk variatietheorema is monometriciteit geen voorspelling.

### 2.6 De nabijheid van de factor vijftien is geen afleiding

Hoewel \(15c_T/c\) numeriek dicht bij één kan liggen, vermenigvuldigt een verzameling van vijftien identieke gekoppelde elementen normaal zowel inertie als stijfheid. Dan blijft

\[
c=a\sqrt{K/I}
\]

onveranderd. Een factor vijftien vereist een specifiek asymmetrisch of collectief koppelingsmechanisme dat uit de dynamica volgt.

### 2.7 Route I lokaliseert het zwaartekrachtprobleem

De huidige eenvoudige boundary-state-telling mist de benodigde entropy-area-dichtheid met ongeveer \(10^{41}\)--\(10^{42}\). Dit falsificeert de concrete simpele telling, maar maakt precies zichtbaar wat een succesvolle microtheorie nog moet leveren: een onafhankelijk afgeleide en enorm grotere fysieke grensstaatdichtheid of een ander extensief intern alfabet.

### 2.8 De letterlijke Toroflux-atoomkerninterpretatie faalt

Een enkele canonieke core-circulatie draagt slechts een zeer klein deel van een atomaire actie-eenheid. Een Bohr-ladder ontstaat in het simpele potentiaalmodel pas nadat de gewenste circulatiequantisatie wordt opgelegd. Een mogelijke overblijvende route is daarom:

\[
\boxed{
\text{microscopische knoopkern}
+
\text{afzonderlijke atomaire envelope-eigenmodus}.
}
\]

### 2.9 De meeste mooie constanteformules zijn Rosetta-relaties

De relaties voor de swirl speed, hornradius, maximale swirl force, Bohrstraal, Rydbergconstante en meerdere herschrijvingen van \(G\) zijn intern coherente vertalingen van reeds bekende schalen. Dat is bruikbaar als woordenboek en consistency framework, maar geen onafhankelijke voorspelling.

### 2.10 De beste eerste voorspelling is een dimensieloze dynamische ratio

De snelste verdedigbare route is niet direct een nieuwe dimensionale constante, maar bijvoorbeeld:

\[
\boxed{
\mathcal R_E(K)
=
\frac{E_K}{E_{0_1}},
\qquad
\mathcal R_\Omega(K)
=
\frac{\Omega_K}{\Omega_{0_1}},
\qquad
\mathcal R_U(K)
=
\frac{U_K/R_K}{U_{0_1}/R_{0_1}}.
}
\]

Deze ratio's kunnen zo worden opgezet dat

\[
\frac{\partial\mathcal R}{\partial\alpha}
=
\frac{\partial\mathcal R}{\partial m_e}
=
\frac{\partial\mathcal R}{\partial G}
=0.
\]

## 3. De vijf vervolgonderzoeken

Elke track staat in een afzonderlijk document:

1. [`docs/01_dynamically_certified_knot_states.md`](docs/01_dynamically_certified_knot_states.md)  
   Dynamisch gecertificeerde ring-, trefoil-, spiegel-trefoil- en figure-eight-toestanden; frequentie-, energie- en stabiliteitsratio's.

2. [`docs/02_geometric_alpha_candidate.md`](docs/02_geometric_alpha_candidate.md)  
   De geometrische \(\alpha\)-kandidaat, identificeerbaarheid van \(8\pi/3\), ropelength-onzekerheid en preregistratie van correcties.

3. [`docs/03_variational_core_ratio_chi.md`](docs/03_variational_core_ratio_chi.md)  
   Onafhankelijke variationale selectie van \(\chi=a_{\rm core}/r_c\), coreprofiel, neck law en robuustheid van \(\beta_Q\) en \(c_T\).

4. [`docs/04_route_I_boundary_state_counting.md`](docs/04_route_I_boundary_state_counting.md)  
   Route-I boundary-state counting, entropy-area-coëfficiënt, gauge constraints en de huidige \(10^{41}\)-hiërarchie.

5. [`docs/05_atomic_envelope_eigenproblem.md`](docs/05_atomic_envelope_eigenproblem.md)  
   Een apart atomaire-envelope-eigenprobleem dat \(n,\ell,m,j\), acties en selectieregels moet genereren zonder de Bohrregels als invoer.

## 4. Wat het Python-script reeds doet

Het hoofdscript is:

```text
src/sst_dimensionless_ratios.py
```

Het bevat een volledig zelfstandig NumPy-startpunt voor:

- reconstructie van Brian Gilbert `AB` ideal-knot-coëfficiënten;
- ring, \(3_1\), spiegel-\(3_1\) en \(4_1\);
- uniforme booglengte-hersampling;
- sampled reach, kromming, bending integral en ropelengthdiagnostiek;
- geregulariseerde Biot--Savart-snelheid;
- drie corekernels:
  - Rosenhead;
  - Rankine-cutoff;
  - Winckelmans--Leonard;
- best-fit translatie en rotatie modulo tangentiële gauge;
- relative-equilibrium-residu;
- regularized self-induction energy proxy;
- hydrodynamische impuls;
- RK4-filamentevolutie;
- periodieke remeshing;
- recurrence error modulo translatie, rotatie en cyclische parameter-shift;
- dominante vormfrequentie uit een tijdreeks;
- energie-, snelheids-, impuls-, bending- en deformation-rate-ratio's;
- resolutie-, core-radius- en regulatorkerncampagnes;
- JSON-, CSV- en convergence-output;
- expliciete provenance en claim guards.

## 5. Wat het script nadrukkelijk nog niet doet

Het script levert nog geen:

- gecertificeerde finite-core Euler-oplossing;
- exact dcsd/reach-certificaat;
- Ridgerunner-KKT-certificaat;
- periodic-orbit Newton--Krylov solve;
- tangent-linear monodromiematrix;
- Floquetmultipliers en Krein-signaturen;
- KAM-certificaat;
- Gross--Pitaevskii- of Navier--Stokes-benchmark;
- identificatie van een knoop met een elektron;
- fysieke voorspelling voor \(\alpha\), \(m_e\), \(G\) of \(c\).

De huidige status is daarom:

\[
\boxed{
\texttt{RESEARCH-TRACK HARNESS / DIMENSIONLESS PRE-PREDICTION STAGE}
}
\]

## 6. Normalisatieprotocol

De standaardcampagne gebruikt:

- \(\Gamma=1\);
- \(\rho=1\) impliciet in de energieproxy;
- dezelfde totale centerlinelengte \(L=2\pi\) voor iedere topologie;
- dezelfde dimensieloze core-radius \(\epsilon\);
- dezelfde integrator en dezelfde Biot--Savart-kernel per vergelijking.

Dit protocol fixeert bij gelijke \(\epsilon\) ook hetzelfde eenvoudige tube-volumeproxy \(\pi\epsilon^2L\). Het is niet de enige mogelijke vergelijking. Daarom ondersteunt het script ook normalisatie op RMS-radius of sampled reach. Een publiceerbare test moet één protocol **vooraf** kiezen en niet na het zien van de uitkomst wisselen.

## 7. Eerste ratio's in het pakket

Per topologie worden onder andere berekend:

\[
\mathcal R_E
=
\frac{E_K}{E_{0_1}},
\qquad
\mathcal R_{\rm rigid}
=
\frac{\sqrt{(U_K/R_K)^2+|\Omega_K|^2}}
{\sqrt{(U_{0_1}/R_{0_1})^2+|\Omega_{0_1}|^2}},
\]

\[
\mathcal R_{\rm def}
=
\frac{\dot q_{\rm def}(K)}{\dot q_{\rm def}(0_1)},
\qquad
\mathcal R_I
=
\frac{|\mathbf I_K|}{|\mathbf I_{0_1}|},
\qquad
\mathcal R_B
=
\frac{\oint\kappa_K^2ds}{\oint\kappa_{0_1}^2ds}.
\]

De ring dient als interne numerieke benchmark, niet als experimentele calibratie.

## 8. Hard gates

Een kandidaat-ratio mag pas als serieuze SST-voorspelling worden besproken wanneer:

1. dezelfde governing dynamics voor alle topologieën is gebruikt;
2. de initial state dynamisch is gecertificeerd;
3. de ratio convergeert met resolutie en tijdstap;
4. de ratio stabiel blijft onder ten minste twee admissibele corekernels;
5. topology, circulatie en volume tijdens de meetperiode behouden blijven;
6. alle parameters vóór externe vergelijking zijn bevroren;
7. geen targetobservable of equivalent ervan in de dependency chain voorkomt;
8. de uitkomst wordt vergeleken met een onafhankelijke simulatie of experiment.

## 9. Installatie en snelle test

Vereist:

```text
Python 3.11+
NumPy 2.x
```

Optionele editable installatie:

```bash
pip install -e .
```

Daarna is ook `sst-ratios` als consolecommando beschikbaar.

Vanaf de pakketmap:

```bash
python src/sst_dimensionless_ratios.py selftest
```

Snelle campagne:

```bash
python src/sst_dimensionless_ratios.py campaign \
  --config configs/quick_campaign.json \
  --output outputs/quick_start
```

Windows PowerShell:

```powershell
.\examples\run_quick.ps1
```

Linux/macOS:

```bash
./examples/run_quick.sh
```

## 10. Voorbeeld: één statische diagnose

```bash
python src/sst_dimensionless_ratios.py diagnose \
  --knot-id 3:1:1 \
  --label trefoil \
  --ideal-file data/ideal_favorites.txt \
  --resolution 128 \
  --epsilon 0.08 \
  --kernel rosenhead \
  --normalization fixed_length
```

## 11. Voorbeeld: één evolutie

```bash
python src/sst_dimensionless_ratios.py evolve \
  --knot-id 3:1:1 \
  --label trefoil \
  --ideal-file data/ideal_favorites.txt \
  --resolution 128 \
  --epsilon 0.08 \
  --kernel winckelmans \
  --dt 0.00025 \
  --steps 400 \
  --sample-every 10 \
  --output outputs/trefoil_evolution.json
```

## 12. Uitvoer

Een campagne produceert:

```text
campaign_results.json
campaign_summary.csv
convergence_summary.csv
```

Belangrijke velden zijn:

- `relative_motion.projected_residual`;
- `energy_proxy_ratio`;
- `rigid_rate_ratio`;
- `deformation_rate_ratio`;
- `impulse_norm_ratio`;
- `dominant_shape_frequency_ratio`;
- `final_recurrence_error`;
- `relative_energy_drift`;
- `relative_length_drift`.

## 13. Pakketstructuur

```text
SST_dimensionless_dynamic_predictions_v0.1.0/
├── README.md
├── CHANGELOG.md
├── requirements.txt
├── pyproject.toml
├── VALIDATION.md
├── PACKAGE_STATUS.json
├── configs/
│   ├── quick_campaign.json
│   └── research_campaign.json
├── data/
│   └── ideal_favorites.txt
├── docs/
│   ├── 01_dynamically_certified_knot_states.md
│   ├── 02_geometric_alpha_candidate.md
│   ├── 03_variational_core_ratio_chi.md
│   ├── 04_route_I_boundary_state_counting.md
│   ├── 05_atomic_envelope_eigenproblem.md
│   ├── METHODOLOGY.md
│   ├── PREREGISTRATION.md
│   └── SOURCE_MAP.md
├── examples/
├── outputs/quick_start/
├── source_material/
├── src/
│   ├── sst_dimensionless_ratios.py
│   └── sstcore_bridge.py
└── tests/
```

## 14. Bronnen en versiegrondslag

Dit pakket is inhoudelijk gebaseerd op:

- `SST_CANON-v0.8.34.tex` — actuele MAIN CANON;
- `SST_CANON-v0.8.34-research-track.tex` — actuele Research Track;
- `deep-research-Can Swirl-String Theory Compute Anything Not Already Encoded in Its Calibration Constants(1).md` — dependency- en voorspellingsaudit;
- `ideal_favorites.txt` — Fourier/AB-centrumlijnbron;
- de ropelength- en Ridgerunner-literatuur als geometrische achtergrond.

De deep-research audit is oorspronkelijk uitgevoerd tegen een eerdere CANON-snapshot. De relevante epistemische guards, finite-cell-obstructie en dynamische certificatie-eisen zijn in v0.8.34 nog steeds aanwezig of verder aangescherpt. Dit pakket claimt niet dat alle numerieke bevindingen reeds opnieuw op elke v0.8.34-codebranch zijn uitgevoerd.

## 15. Eindstatus

\[
\boxed{
\text{SST is momenteel een falsifieerbaar onderzoeksprogramma met echte}
\atop
\text{niet-algebraïsche berekeningen, maar nog zonder bevestigde onafhankelijke voorspelling.}
}
\]

De eerste serieuze kans is een robuuste, preregistreerde en extern geteste dimensieloze dynamische knoopratio.

## Windows `.bat` workflow

Voor een stapsgewijze Windows-uitvoering zijn genummerde scripts toegevoegd onder `batch/`.
Begin met:

```text
batch\00_check_python.bat
batch\01_setup_venv.bat
batch\02_selftest.bat
batch\03_quick_campaign.bat
```

Zie `WINDOWS_BATCH_GUIDE.md` voor de volledige uitleg en de medium/volledige convergentiecampagnes.
