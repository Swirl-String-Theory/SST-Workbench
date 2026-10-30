# A075-v0.2.10 — A007 Ruban Relative Equilibrium & Exploratory Spectral Diagnostics

**Software:** uitvoerbare, zelfstandige en **additieve A075-uitbreiding**. **NIET** een volledige vervanging van de oorspronkelijke `A075-v0.2.9`-falsifier. De Framework v1.1.0-runtime is **niet gekopieerd of gewijzigd**. Bron A007 is exact vastgepind; de oorspronkelijke A075-v0.2.9-filamentsolver wordt byte-identiek bewaard als een wetenschappelijke referentie. De nieuwe berekeningsmodule heeft zijn eigen onafhankelijke operator en is nog niet gecertificeerd gelijkwaardig aan de originele auteurssolver.

**Wetenschappelijke status:** `DEVELOPMENT_ONLY / EQUILIBRIUM_UNRESOLVED / SPECTRAL_UNRESOLVED / PHYSICAL_STABILITY_UNRESOLVED`.

## Waar installeren?

Pak uit naast bestaande `A075-v0.2.9`:

```text
C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\
  A075_hydrodynamische_resonante_invanging\
    A075-v0.2.9\                      (bestaand; ongewijzigd)
    A075-v0.2.10_Ruban_Equilibrium_Addon\  (deze nieuwe zelfstandige module)
```

Dit pakket vereist **niet** dat de oude bestanden worden aangepast. Er zijn geen `FREEZE`, `BASIC`, `FULL` of `CERTIFY`-commando's in deze addon: de bestaande Framework-gates worden niet geraakt. De formele certificatie van een eventuele volledige A075-v0.2.10-release vereist later afzonderlijk de oorspronkelijke Framework-runtime.

## Installeren en testen

Python 3.11+ en de pakketten in `requirements.txt`.

```bat
cd C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A075_hydrodynamische_resonante_invanging\A075-v0.2.10_Ruban_Equilibrium_Addon
python -m pip install -r requirements.txt
run_all.cmd SELFTEST
run_all.cmd VERIFY
run_all.cmd PILOT --n 128 --harmonics 1 --modes 4 --run-id T23_PILOT_LOCAL_001
```

Een lokale, uitsluitend voorspellende scan:

```bat
run_all.cmd SCAN --n 256 --harmonics 2 --modes 6 --run-id T23_SCAN_LOCAL_001
```

De standaard `PILOT` test B0=0.152,0.154,0.156. De standaard `SCAN` heeft 25 waarden van 0.148 t/m 0.160 met stap 0.0005. Met `--b-values 0.152,0.154,0.156` kan een expliciete lijst worden gekozen.

**Kostenwaarschuwing:** de niet-lokale interacties schalen als O(N²), en de Fourier-variaties veroorzaken herhaalde veldberekeningen. Standaard blokkeert de runner N>512 zonder `--allow-expensive`. De exploratieve spectrale Ritzmatrix groeit met `--modes`, niet met de volledige discretisatie.

## Authentieke broninput

- `inputs/a007/RUBAN_T23_B0_0p154_N2048_EQUAL_ARCLENGTH.xyz`, exacte A007 SHA-256 `127de915c8eaae59325b8bd2697a0ab50c71eb1c5cf0a91fc55ed44de70fcc89`.
- `inputs/a007/SEED_MANIFEST.json`, `RUBAN_FILAMENT_CONFIG.json`, oorspronkelijke A007-generator en A075-seedloader.
- `source_evidence/A075_v029_ruban_filament.py`, exact dezelfde bronhash als `experiment/ruban_filament.py` uit A075-v0.2.9: `27cad14f87262d496b1f3b3cb0d13b63fff0163e8face210d3463f053f860411`.
- `source_evidence/SOURCE_MANIFEST_v0.2.9.json` voor gecontroleerde bronherkomst.

Het bijzondere B0=0.154-geval wordt NIET simpelweg herberekend met de torusformule: de **werkelijke A007-XYZ-punten** worden geladen, geverifieerd en met periodieke kubische interpolatie op een uniforme torusparameter gebracht, zodat de onafhankelijke spectrale afgeleiden toepasbaar zijn. Andere B0-waarden worden als analytische T(2,3)-varianten gegenereerd. Dit onderscheid staat per geval in de CSV-kolom `geometry_source`.

## Wiskundig model

Voor de stationariteitsdiagnostiek minimaliseren we, over U en Omega, het normale residu van Rubans geregulariseerde filamentoperator:

\[
\varepsilon=\frac{R_0}{|\Gamma|}\min_{U,\Omega}\sqrt{\frac{1}{L}\int \|P_{\perp}[\mathcal F(\mathbf X)-U\mathbf e_z-\Omega\mathbf e_z\times\mathbf X]\|^2\,ds}.
\]

De mode `--harmonics 0` controleert de ongewijzigde torus. Vanaf `--harmonics 1` worden begrensde aanvullende radiale en verticale Fourierharmonischen gebruikt. **Deze beperkte familie kan een echte vervormde relatief-stationaire oplossing missen.** Relaxatie gebruikt begrensde niet-lineaire kleinste kwadraten; een `success=true` betekent optimizerconvergentie, niet bewezen evenwicht.

De beperkte spectrale matrix (`--modes`) is een **niet-gecertificeerde Fourier-Ritzprojectie**. Zij is niet volledig gauge-correct en mag **niet** als complete lineaire stabiliteit, Floquet-exponent of fysische groeisnelheid worden geïnterpreteerd. Gebruik `--modes 0` om haar over te slaan.

## Stop- en statusvoorwaarden

1. Als A007 of A075 source SHA256 niet klopt: **STOP, geen berekening**.
2. Als n, B0 of geometrie ongeldig is: **STOP**.
3. Als output `run-id` al bestaat: **STOP, niet overschrijven**.
4. Geen claim `EQUILIBRIUM_PASS` zonder onafhankelijk geverifieerd klein residu met meerdere convergentieniveaus én onbeperkte/adequate vormbasis.
5. Geen claim `SPECTRAL_STABLE` zonder volledige linearisatie en gaugecorrectheid, modes- én ruimtelijke convergentie en eventuele periodieke baan via Floquet.
6. Geen claim `EULER_STABLE` zonder eigen A075-driedimensionale finite-core-, box-, tijd- en topologiegates.

## Output

```text
A075_Hydrodynamische_Resonante_Invanging_v0.2.10-outputs/<run-id>/
  RUN_CONFIG.json
  RUBAN_EQUILIBRIUM_RESULTS.csv
  T23_B*_N*_RELAXED.npz
  T23_B*_RITZ.json
  SCIENTIFIC_ASSESSMENT.json
  FALSIFIER_REPORT.md
  A075-v0.2.10_FALSIFIER_REPORT.pdf
  MANIFEST_SHA256.json
```

Daarnaast komt het outputarchief in de **bovenliggende map**:

`../A075_Hydrodynamische_Resonante_Invanging_v0.2.10_<run-id>_outputs.zip` en `.sha256`.

## Wat nog moet gebeuren?

Dit is de **eerste mathematische module**, geen complete falsifiercertificatie. Volgende tranche: independent quadrature parity met originele Ruban-filamentvergelijking, geaugmenteerde relatieve-evenwichtsoplosser, eindige-differentie-vs-analytische Jacobiaancontroles, correcte quotient/gauge-linearisatie, volledige eigenmodes, stapgrootte- en roosterconvergentie, direct tijdsevolutietests, én onafhankelijke Euler-finite-corevalidatie. Pas daarna B007 en E010 synchroniseren.

## Literatuur

V. P. Ruban (2018), "Long-lived quantum vortex knots", *JETP Letters* 107, 307–311, DOI: 10.1134/S0021364018050120.

V. P. Ruban (2018), "Quasi-stable configurations of torus vortex knots and links", *Journal of Experimental and Theoretical Physics* 127, 581–586, DOI: 10.1134/S106377611809008X.
