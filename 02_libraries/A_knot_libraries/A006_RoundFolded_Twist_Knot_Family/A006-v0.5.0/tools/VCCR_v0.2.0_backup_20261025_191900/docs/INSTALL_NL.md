# Installatie — A006 VCCR v0.1.0

Deze module kan los draaien **of** als veilige toevoeging in je bestaande `A006-v0.5.0`-werkmap. Zij verandert je bestaande KnotPlot-, ForceGrid- en selectieprogramma's niet.

1. Pak de ZIP uit naar een tijdelijke map. Zorg dat Python 3 en NumPy geïnstalleerd zijn (`py -3 -m pip install -r requirements.txt`).
2. Controleer de installatie: `py -3 install_sidecar.py --base "C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0" --check`.
3. Installeer: hetzelfde commando met `--apply`.
4. Ga naar je `A006-v0.5.0`-werkmap. Voer `run_vccr.cmd TEST` uit en daarna `run_vccr.cmd DEMO`.
5. De resultaten komen in `tools\VCCR_v0.1.0\Output\VCCR_v0.1.0\` terecht, niet in de bestaande A006-output.

Het pakket weigert overschrijven. Wil je niets installeren, dan kun je de opdrachten direct in de uitgepakte pakketmap uitvoeren.

## Volgende stap: echte PKLSA

Voor een PKLSA-traject moet je later onafhankelijke tijdreeksen opnemen met (a) centerline-lengtes, (b) materiële dwarsdoorsnede, (c) circulatie/vorticiteitsflux en (d) behoud van topologie. Alleen (a) is via ASCII XYZ beschikbaar. Zonder (b) en (c) blijven de fysische sluitingspoorten open.
