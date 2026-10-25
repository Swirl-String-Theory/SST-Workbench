# VCCR v0.2.0 veilige herinstallatie

De eerste v0.2.0-release en de gecorrigeerde release hebben verschillende README.md-bestanden en Windows-startscripts. Daarom weigert de *create-only* installer terecht gewijzigde bestanden te vervangen.

Dit script bewaart bij een conflict de volledige bestaande `tools\VCCR_v0.2.0`-directory (inclusief lokale output en aanpassingen) en, als aanwezig, `run_vccr_v020.cmd`, elk met een unieke back-upnaam. Vervolgens installeert het de bijgewerkte versie vanaf dit pakket. Er worden geen bestanden verwijderd en `run_all.cmd` en `knotplotrc.kps` blijven onaangeroerd.

Open een CMD in deze uitgepakte map en voer uit:

```bat
py -3 repair_vccr_v020.py --base "C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0" --check
py -3 repair_vccr_v020.py --base "C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0" --apply
```

Vervolgens in de A006-v0.5.0 directory:

```bat
run_vccr_v020.cmd TEST
run_vccr_v020.cmd EULER --case both
```

Bij problemen: STOP, bewaar de output en ga niet handmatig overschrijven. De oude installatie blijft in `tools/VCCR_v0.2.0_backup_...`, en het oude startscript in `run_vccr_v020_backup_....cmd`. Verwijder deze back-ups pas nadat je zeker weet dat de nieuwe omgeving werkt en je de eerdere resultaten niet meer nodig hebt.
