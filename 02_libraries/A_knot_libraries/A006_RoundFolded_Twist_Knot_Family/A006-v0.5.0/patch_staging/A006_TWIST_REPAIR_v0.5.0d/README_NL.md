# A006 v0.5.0d — Twistsladder geometrische herstelkandidaten

**Status:** 36/48 statische geometriekandidaten; 12 quarantaine; **GEEN Euler-/PKLSA-/finite-core-certificering**.

## Diagnose

De `4_1`, `7_2`, `8_1`, `9_2`, `10_1`, `11a247` 4-plat-bronseeds hebben een sector zonder projectiepunten van ongeveer 24,3–24,7°. De vroegere XYZ-bestanden zijn doorgaans *periodiek gesloten* (laatste vertex wordt cyclisch aan de eerste verbonden); de C-vorm is het gevolg van de constructie, niet van een afwezige sluitvertex. De oorspronkelijke 3_1, 5_2 en 6_1 blijven ongemoeid; ook alle torusknopen blijven buiten scope. `11a247` wordt als legacy-label bewaard, niet als onafhankelijk bevestigd KnotInfo-nummer.

## Reparatie

Deze exploratieve patch gebruikt een oriëntatiebehoudende hoekvervorming op een lege projectiesector, met 0,5° als streefsector. De radiale positie en z-coördinaat blijven behouden. Voor de bezette sector is

\[
\theta' = b+\delta +\frac{2\pi-\delta}{2\pi-g}\operatorname{mod}(\theta-b,2\pi),\qquad\delta=0.5^\circ,
\]

met \(g\) de lege sector en \(b\) de eerste bezette hoek erna. De lege sector kan via een monotone interpolatie worden uitgebreid tot een omgevings-isotopie van een *continue* broncurve in het annulaire gebied. Na re-discretisatie en rechte verbindingssegmenten is **geen formeel bewijs geleverd** dat alle polygonen via een isotopie uit de bronpolygoon ontstaan.

## Inhoud

- `source_snapshots/`: 6 origineel gedownloade N2048 XYZ-invoerbestanden, ongewijzigd.
- `REPLACEMENTS/`: 36 gegenereerde `KNOT_..._N0512/N1024/N2048_{ORIG,MIRROR}` XYZ- en KPT-bestanden. Alle halen de opgegeven projectie-invarianten, segmentafstand, segmentlengte-CV, visuele sectorsluiting en binaire KPT-roundtrip. **Statische kandidaat**, geen fysische validatie.
- `QUARANTINE/`: 12 N0256 XYZ- en KPT-bestanden. Topologische projectietest en/of lengtespreiding faalt; **niet gebruiken voor fysica of als standaardselectie in het lab**.
- `MANIFEST.json`: per bestand hashes, oorspronkelijke bron-hash, knoopprojectie, meetwaarden en alle gates.
- `BEFORE_AFTER.png`: vergelijkende XY-projectie.
- `install_candidates.py`: dry-run standaard; maakt backups bij expliciet `--apply`.
- `repair_twist_seeds.py`, `validate_generated.py`, `segregate.py`, `validation_lib/`: volledig herbouwbaar met NumPy, SciPy en Shapely.

## Niet-destructief toepassen op lokale A006

```
py -3 install_candidates.py --target "C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0"
```

Dit toont wat overeenkomt met bestaande bestandsnamen. Alleen nadat deze overeenkomsten zijn bekeken:

```
py -3 install_candidates.py --target "C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0" --apply
```

Bij meerdere overeenkomende bestanden weigert de installer standaard; gebruik alleen na inspectie `--allow-multiple`. De `original_frozen`-gegevens worden nooit aangepast. Bij geen match wordt niets geschreven. De patch **herstelt geen interne galerijcache**: de loader moet naar de nieuwe XYZ/KPT wijzen, periodiek laatste→eerste verbinden, N0256 verbergen en bestaande thumbnails opnieuw genereren.

## Reproduceerbaarheid

Vanaf een schone uitgepakte kopie:

```
py -3 -m pip install numpy scipy shapely
py -3 repair_twist_seeds.py
py -3 validate_generated.py
py -3 segregate.py
```

**Beperkingen:** alleen Alexander-polynoom, determinant en aantal projectiekruisingen zijn getest, geen volledig onafhankelijke knoopisomorfie-certificering. Een niet-nul middellijnsegmentafstand is geen fysische core-clearance voor een gekozen straal; de clearance (~0,4–0,6 coördinaateenheden) kan kleiner zijn dan `2a` voor A006's nominale kernel. Geen Biot–Savart, druk-Poisson-oplossing, Euler-evolutie, PKLSA, rek-/ropelengthrelaxatie, of stabiliteitsmeting.

## Literatuur

```latex
\bibitem{Alexander1928} J.~W. Alexander, ``Topological Invariants of Knots and Links,'' Transactions of the American Mathematical Society, 30, 275--306 (1928), \url{https://doi.org/10.1090/S0002-9947-1928-1501429-1}.
```
