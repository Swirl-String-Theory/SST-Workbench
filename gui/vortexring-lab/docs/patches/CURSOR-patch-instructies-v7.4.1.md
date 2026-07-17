# Cursor-instructies — vortexring-lab v7.4 → v7.4.1

## Toepassen

Gebruik vanuit de projectroot:

```bash
git apply --check docs/patches/vortexring-lab-v7.4-to-v7.4.1.diff
git apply docs/patches/vortexring-lab-v7.4-to-v7.4.1.diff
```

De patch laat de bestaande v7.4-bestanden intact en voegt de volgende v7.4.1-bestanden toe (nu onder `archive/v7/` en `archive/v7-tools/`):

- `archive/v7/vortexring-lab-v7.4.1.html`;
- `archive/v7-tools/validate-v7.4.1.py`;
- `docs/releases/release-notes-v7.4.1.md` (indien aanwezig);
- `docs/planning/stappenplan-vortexring-lab-v7x-v5.md`;
- dit instructiebestand.

## Verplichte controles

```bash
python archive/v7-tools/validate-v7.4.1.py archive/v7/vortexring-lab-v7.4.1.html
```

Verwacht:

```text
PASS: statische v7.4.1-integriteitscheck en node --check groen
```

Open daarna:

```text
archive/v7/vortexring-lab-v7.4.1.html?selftest=1
```

Accepteer alleen wanneer:

1. alle T0–T6- en T0e–T0h-tests groen zijn;
2. er gedurende minstens tien renderframes geen console-error of rood runtimeflag verschijnt;
3. `MODEL → KERN` precies één GP-Δ-paneel bevat;
4. de algemene GP-kernreadout meeverandert tussen `0.615000` en `0.619351`;
5. `Ω=0` in de HUD `— · — · <a/R>` toont;
6. de DIAGNOSE-tab `GEOMETRISCHE DIAGNOSTIEK` heet en nergens `ENERGIE E_eff` toont;
7. een te hoge simulatiesnelheid na de opwarmtijd paars wordt, terwijl echte numerieke ongeldigheid rood blijft;
8. de fysieke tijd blijft doorlopen en het traject bij Auto-relax uit niet verandert door uitsluitend de afspeelsnelheid te wijzigen.

## Niet opnieuw introduceren

- `ENERGIE E_eff` of `mathcal{E}_{rm eff}` voor de vrije score;
- claims dat ACN een afstotingskracht of drukbarrière is;
- claims dat `γĤ` zonder extra mechanisme een stabiliteitsenergie is;
- een eindige `χ_Ω` of `Ro_z` bij `Ω=0`;
- `window.ModelLog` als guard voor de top-level `const ModelLog`;
- `perfScore` als onderdeel van de numerieke stabiliteitsscore;
- een rode rand voor uitsluitend een computer-capaciteitslimiet.
