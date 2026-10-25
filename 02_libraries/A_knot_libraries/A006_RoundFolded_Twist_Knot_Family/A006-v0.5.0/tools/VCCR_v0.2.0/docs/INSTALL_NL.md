# VCCR v0.2.0 installeren (Windows)

Dit is de **v0.2.0**-installatiehandleiding. De eerdere tekst in `docs/INSTALL_NL.md` betrof v0.1.0.

## Aanbevolen: als veilige uitbreiding van A006-v0.5.0

1. Pak de ZIP uit en open een terminal in `A006_Volume_Circulation_CoreRadius_Closure_v0.2.0`.
2. Controleer de Python-versie: `py -3 --version` (Python 3.10 of hoger).
3. Installeer NumPy: `py -3 -m pip install -r requirements.txt`.
4. Controleer zonder bestanden te schrijven:

```bat
py -3 install_sidecar.py --base "C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0" --check
```

5. Alleen na `CHECK PASS`, pas toe:

```bat
py -3 install_sidecar.py --base "C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0" --apply
```

6. Ga naar `A006-v0.5.0` en start:

```bat
run_vccr_v020.cmd TEST
run_vccr_v020.cmd EULER --case both
run_vccr_v020.cmd DEMO
```

De installer schrijft uitsluitend onder `tools\VCCR_v0.2.0` en maakt `run_vccr_v020.cmd` aan in A006. `run_all.cmd`, KnotPlot- en ForceGrid-bestanden blijven behouden. Bij afwijkende bestaande doelbestanden weigert hij te overschrijven.

## Zonder integratie

In de uitgepakte VCCR v0.2.0-map:

```bat
py -3 -m pip install -r requirements.txt
run_vccr.cmd TEST
run_vccr.cmd EULER --case both
```

**Interpretatie:** `EULER` is een exacte affine Euler-benchmark, geen bewijs van een finite-core of geknoopte vortexevolutie.
