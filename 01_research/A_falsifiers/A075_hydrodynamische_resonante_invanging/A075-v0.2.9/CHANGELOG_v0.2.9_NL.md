# A075-v0.2.9 — Ruban Depositie & Geometrietracking

- Correctie per-geometrie B0 in `resolution_gate`, inclusief afzonderlijke Ruban- en B0=0.32-rapportage.
- `RUBAN_PREVIEW` registreert werkelijke `config.geometry` in plaats van de misleidende `0_1`-default.
- Nieuw `RUBAN_DEPOSITION`: spectrale depositie, initiele energie/enstrofie, vorticiteitsdoorsneden, veldrug, kern- en roosterdiagnostiek.
- Optionele korte meegevoerde markers met afzonderlijke lokale vorticiteitsrug uit de werkelijke Euler-veldoplossing.
- Gedocumenteerde sigma-/rooster-/box-scan; status altijd DEVELOPMENT_ONLY / UNRESOLVED.
- Zelfstandige outputmap + archive + SHA-256; geen private reveal-data.
- Embedded Framework v1.1.0 blijft byte-identiek; A075-v0.2.8 blijft ongewijzigd.
- Automatisch per-run PDF-falsifierrapport en versionele kopie naast de A075-versiemap.
