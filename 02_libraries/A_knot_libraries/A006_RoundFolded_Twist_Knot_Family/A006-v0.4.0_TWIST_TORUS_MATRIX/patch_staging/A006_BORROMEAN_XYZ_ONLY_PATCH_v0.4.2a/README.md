# A006 v0.4.2a — STRICT XYZ ONLY (correctie op v0.4.2)

De gebruiker heeft expliciet één XYZ met drie numerieke componenten, gescheiden door precies één lege regel, vereist. De vorige release leverde daarnaast ongewenste LOAD KPC bestanden; die worden niet langer gegenereerd. Bestaande KPC bestanden worden alleen na byte-inhoudcontrole in een backup gearchiveerd.

**Doel**: de bestaande `A006-v0.4.0_TWIST_TORUS_MATRIX` inclusief de geïnstalleerde v0.4.1 + v0.4.2 patches.

## Installeren vanuit de bestaande A006 map

`py -3 patch_staging\A006_BORROMEAN_XYZ_ONLY_PATCH_v0.4.2a\install_patch.py --base . --check`

`py -3 patch_staging\A006_BORROMEAN_XYZ_ONLY_PATCH_v0.4.2a\install_patch.py --base . --apply`

`run_all.cmd BORROMEAN WHOLE TEST`

`run_all.cmd BORROMEAN WHOLE BUILD`

`run_all.cmd BORROMEAN WHOLE BUILD FULL`

### Bestanden

`output/borromean/Borromean_5_5_6_BALANCED_N1024.xyz` etc.

**GEEN** *_LOAD.kpc; **GEEN** automatische KPC generator; **GEEN** Component-headers; precies 1024/2048 numerieke XYZ-regels per blok.

`coords`-snapshots van KnotPlot kunnen componentheaders bevatten. Om deze als apart, kaal XYZ te exporteren:

`py -3 extensions\borromean\whole\strict_xyz.py --normalize-raw raw_coords.txt --output normalized.xyz --n 1024`

Het originele bestand blijft ongemoeid. `--validate` controleert een bestaand XYZ.

### Wetenschappelijke status

Topologie van individuele componenten na transport en Borromeaanse triple linking blijft UNRESOLVED. Geen Eulerclaim.
