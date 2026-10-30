# Testaudit 2026-10-30 — development-only

Bronnen (gelezen uit Google Drive A075-v0.2.9) zijn lokaal geëvalueerd; de bronbestanden **zijn niet in de patch opgenomen**.

## Gecontroleerd

- De exacte A075-v0.2.9 `euler3d.py` en `ruban.py` bronhashes worden bij uitvoering gecontroleerd.
- De echte Ruban `B0=77/500`, `N=2048`, gelijk-booglengte-seed is met de originele `SEED_MANIFEST.json` gelezen en gecontroleerd. Seed SHA-256: `127de915c8eaae59325b8bd2697a0ab50c71eb1c5cf0a91fc55ed44de70fcc89`.
- Een korte 4×12- en een aparte 3×12-smoke met de echte A075-Eulerkern zijn uitgevoerd.
- Een volledige **80×12 softwarecontractcampagne** op `n=16`, `box=10`, `sigma=0.5`, `dt<=0.01`, `t_end=0.04` met 80 onafhankelijke `SeedSequence`-perturbaties is uitgevoerd.
- `times_s`, `q_m`, `qdot_m_s`, `trial_ids`, `metadata_json` zijn door de format-validator én door de echte `A026_HiddenStateMemory_SIDECAR_v0.1.0/src/intake.py` geaccepteerd.
- A026 `run_falsifier.py EULER --input ...` schreef een geldig diagnostisch rapport met `G0 PASS`, `G1 PASS` (diagnostic), `G2/G3 NOT_EXECUTED`, `G4/G5/G6 UNRESOLVED`, `G7/G8 NOT_EXECUTED`, exitcode **3 zoals bedoeld**.
- De grootste relatieve energieafwijking in deze korte n=16 campagne was `5.647e-14` (beperkte n=16 smoke, geen oplossingsconvergentie).

## Noodzakelijke correctie t.o.v. eerste kandidaat

A026-v0.1.0 heeft een ongedimensioneerde numerieke afkapwaarde `std(feature)<1e-14`. Daardoor worden de variabelen bij Canon-kernschaal `r_c=1.40897017e-15 m` afgewezen, zelfs bij niet-gedegenereerde veldtrajecten. De exporter gebruikt daarom **standaard het expliciete Euler-similariteitspaar L*=1 m, U*=1 m/s**, wat SI-consistent maar **niet canoniek fysisch gekalibreerd** is. Canon-scaled analyse vereist een expliciet gereviseerde A026 feature-normalisatie, niet een fictieve conclusie.

## Niet gekwalificeerd

- Geometry/core/spatial/time/domain convergence, centerline topology, phase clocks, exact pressure field diagnostics, matched-state counterfactuals en parallel-kernenachtergrond zijn nog niet gevalideerd.
- Slechts 1 echte Euler provider (SciPy FFT) getest; nog geen onafhankelijke C++/GPU backendequivalentie.
- Testresultaten zijn **NIET** overgedragen als wetenschappelijke certificering of als resultaat van een blinde falsifier.

## Reproduceerbare local Windows acceptance

Run eerst `py -3 -m pytest -q tests`, dan `run_a026_export.cmd ... --trials 4 ...`, daarna `--trials 80 ...`, vervolgens `validate_a026_npz.py`, en pas daarna A026 `run_all.cmd EULER`. Laat onveranderde A026-exitcode 3 staan.
