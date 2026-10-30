# Leapfrogging Seed v0.1.1 — additieve A003 VortexLab-uitbreiding

**Bronbasis:** actuele aangeleverde `A003_vortexlab(3).zip` (modulaire VortexLab, `7.6.25b-m1-twistflow-p7-v0.7.2`).

## VEILIG INSTALLEREN

Dit archief bevat **uitsluitend nieuwe bestanden** onder:

`extensions/Leapfrogging_Seed_v0.1.1/`

Pak het archief uit in de hoofdmap `05_apps/A003_vortexlab/`, **alleen als deze extensiemap nog niet bestaat**. Als Windows een overschrijfmelding geeft, annuleer dan de installatie en vergelijk de bestanden. **Geen bestaand bestand moet worden overschreven.**

De volgende huidige A003-bestanden blijven **byte-identiek**: `README.md`, `run_all.cmd`, `package.json`, `project.json`, `apps/web/index.html`, `apps/web/src/legacy/vortexlab-runtime.js`, `apps/web/src/legacy/xyz-import.js` en de bestaande tests.

Deze uitbreiding is **geen wijziging van de VortexLab-runtime of menupresets**. Zij gebruikt de al aanwezige native `.xyz`-import van de huidige modulaire applicatie. De verouderde zelfstandige HTML-kopie uit de eerdere v0.1.0-release is bewust **niet** meegeleverd.

## Native simulatie in de bestaande applicatie

1. Start jouw ongewijzigde VortexLab in de A003-projectroot met `npm start` en open `http://127.0.0.1:4173/`.
2. Kies **Solo** (één carrier met twee onafhankelijke geometrische componenten). Gebruik **niet** de botsingsmodus, want die dupliceert beide componenten naar twee carriers.
3. Kies **Biot–Savart**, niet **LIA (Local Induction Approximation; lokale inductiebenadering)**: zonder wederzijdse inductie kan geen leapfrogging ontstaan.
4. Kies medium **Demo**, circulatie **+2.0** in het demo-veld (VortexLab gebruikt dan `Γ=+0.002 m²/s`), straal `R0=0.070 m` en numerieke kernstraal `a_sim=0.0015 m`. Houd achtergrondstroming, drift, wrijving en auto-relax uit; topologiebeveiliging aan. De lokale scherminstellingen moeten handmatig worden gecontroleerd.
5. Kies **Import .xyz…** en selecteer `extensions/Leapfrogging_Seed_v0.1.1/data/N144/leapfrog_two_rings_N144.xyz`.
6. Controleer in de geometrie-uitlezing dat **2 componenten** en **144 + 144 vertices** actief zijn. De ringcentra moeten bij start rond `z=−0.015 m` en `z=+0.015 m` liggen, met gelijke tekenrichting van de circulatie.
7. Start de simulatie. Herhaal de proef met `data/N072/` en `data/N288/` op **vaste fysische eindtijd** en met passende tijdstapconvergentie. Leg zowel ringstralen als posities vast, plus minimale kernafstand, energieafwijking en eventuele stopcodes.

**Let op:** de bestaande A003-import past de hele geometrie aan het ingestelde `P.R0` aan. Daarom is `R0=0.070 m` een vereiste voor behoud van de bij deze seed gebruikte absolute lengtes. Controleer dit in de applicatie voordat fysische resultaten worden geïnterpreteerd. De `.xyz`-bestanden bevatten geen circulatie of kernparameter; die staan in het afzonderlijke `SEED_MANIFEST.json` en moeten handmatig in VortexLab worden ingesteld.

## Geometrische configuratie

- Twee coaxiale, afzonderlijke, gesloten en ongelinkte ringen (elk een `0_1`-unknot).
- Beide tegen de klok in georiënteerd vanaf +z, cirkelstraal `0.070 m`.
- Beginniveaus `z_A=-0.015 m`, `z_B=+0.015 m`, dus `Δz=0.030 m`.
- `Γ_A=Γ_B=+0.002 m²/s`; regularisatie `a_sim=0.0015 m`.
- Ruimtelijke ladder: `N=72`, `N=144`, `N=288` **per ring**.
- Deze basisgeometry is een **startvoorwaarde**, geen analytisch gegarandeerde periodieke leapfrogging-baan.

Elke map `data/N...` bevat twee losse `.xyz`-ringen, één gecombineerd `.xyz`-bestand voor native import, een `.csv`-puntenbestand, manifest en hashes. Een `.xyz`-bestand bevat **geen gedupliceerd eindpunt**; elke component sluit periodiek van de laatste naar de eerste vertex.

## Tests

Vanuit de extensiemap:

```powershell
.\run_leapfrogging_tests.cmd
python .\build_leapfrogging_seed.py --output .\leapfrog_custom_v0.1.1-outputs --n 256
```

Vanuit de bestaande projectroot blijft je oude `run_all.cmd` de normale VortexLab-checks uitvoeren. Deze seedtests zijn **aanvullend**, niet vervangend.

### Wetenschappelijke status

- **GEOMETRY_CONSTRUCTED:** de ringen zijn eindig, coaxiaal en gelijkgericht; afstanden geverifieerd.
- **NATIVE_IMPORT_PARSER_TESTED:** de meegeleverde gecombineerde `.xyz`-vorm is getoetst aan `apps/web/src/legacy/xyz-import.js` uit de aangeleverde A003-snapshot.
- **DYNAMICS_NOT_RUN:** geen traject of herhaalde overtakingscyclus is fysisch/numeriek gecertificeerd.
- **NO_SST_CLOCK_CLAIM:** geen conclusie over intrinsieke Swirl Clock of atomaire tijd.

Axiale volgordewisselingen alleen zijn onvoldoende: valideer de uitwisseling van radii, meerdere herhalingen, energiedrift, ruimtelijke én temporele convergentie en finite-core-gevoeligheid.
