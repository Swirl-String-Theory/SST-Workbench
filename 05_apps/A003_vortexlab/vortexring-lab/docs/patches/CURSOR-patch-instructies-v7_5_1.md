# Cursor-instructies — vortexring-lab v7.5 → v7.5.1

## Bestanden in de patch

De patch hernoemt en actualiseert:

- `vortexring-lab-v7_5.html` → `vortexring-lab-v7_5_1.html`
- `validate-v7_5.py` → `validate-v7_5_1.py`
- `release-notes-v7_5.md` → `release-notes-v7_5_1.md`
- `browser-smoke-v7_5.mjs` → `browser-smoke-v7_5_1.mjs`

Daarnaast wordt dit instructiebestand toegevoegd.

## Toepassen

Maak eerst een commit of reservekopie. Voer daarna vanuit de projectroot uit:

```bash
git apply --check vortexring-lab-v7_5-to-v7_5_1.diff
git apply vortexring-lab-v7_5-to-v7_5_1.diff
```

Bij gebruik van GNU `patch`:

```bash
patch --dry-run -p1 < vortexring-lab-v7_5-to-v7_5_1.diff
patch -p1 < vortexring-lab-v7_5-to-v7_5_1.diff
```

## Statische acceptatie

```bash
python validate-v7_5_1.py vortexring-lab-v7_5_1.html
```

Verwacht:

```text
VALIDATOR: PASS (275 unieke IDs)
```

De validator moet tevens melden dat `node --check` groen is.

## Browseracceptatie

```bash
npm i puppeteer
node browser-smoke-v7_5_1.mjs vortexring-lab-v7_5_1.html
```

Controleer daarnaast handmatig:

1. Open `vortexring-lab-v7_5_1.html?selftest=1` en bevestig dat T0–T9i groen zijn.
2. Onder **MODEL → KERN** staan drie afzonderlijke schalen:
   - `a_sim`: numerieke filament-/contactstraal;
   - `R_horn`: read-only canonieke waarde `1.409 fm`;
   - `r_kern`: lege Research-Track invoer.
3. Voer bij `r_kern` bijvoorbeeld `0.001 fm` in. De waarde moet worden geaccepteerd en kleiner blijven dan `R_horn`.
4. Voer een waarde ≥ `R_horn` in. De simulator moet de invoer afwijzen en `r_kern` weer onbepaald maken.
5. Activeer de SST-vortexbundel en de veldkoppeling. Tracers en stroomlijnen moeten dezelfde draairichting en eindige-bundelovergang volgen als de filamenten.
6. Kies een bundelstraal duidelijk kleiner dan de cilinder. Binnen de bundel is de beweging solid-body; buiten de bundel neemt de azimutale snelheid af als `1/r`.
7. De zichtbare representatieve lijnen moeten de volledige bundelschijf vullen en niet uitsluitend op de buitenrand liggen.
8. Controleer de HUD-regels:
   - `R_horn · r_kern · R_horn/r_kern`;
   - `ω_c(horn) · Ω_kern · ζ_kern`.
9. Zonder `r_kern` moeten de kernwaarden `—` tonen; er mag geen fictieve vaste-kernfrequentie uit `R_horn` worden afgeleid.
10. Controleer de console gedurende minstens tien animatieframes op errors en unhandled rejections.

## Niet accepteren

Accepteer de patch niet wanneer één van de volgende situaties optreedt:

- `RCORE_SST`, `OMEGA_CORE_SST`, `aPhys`, `sAPhys` of `vAPhys` komt nog voor;
- de UI noemt GP/NLSE “het kernmodel per Canon”;
- `a_sim`, `r_kern` en `R_horn` worden gelijkgesteld;
- het bundelveld gebruikt buiten `R_bundle` nog `u_θ=Ωr`;
- tracers of stroomlijnen missen de bundelbijdrage;
- de representatieve lijnen vormen nog een cilindrische schil;
- de simulator beweert dat expliciete verre knooplagen zijn opgelost;
- een zelftest, validatorcheck of browser-smoke faalt.
