# vortexring-lab v7.3.1 — release notes

## Classificatie

Hotfix op v7.3. De bestaande v7.1/v7.2-fysica en numerieke betrouwbaarheidspatches blijven intact.

## Blokkerende reparatie

- Repareert de `ACN` temporal-dead-zone in de nieuwe v7.3-diaglogging. In v7.3 kon de eerste diagnosepassage de animation loop beëindigen met `Cannot access 'ACN' before initialization`, ook wanneer ModelLog uit stond.

## Invoer en kernstraal

- Numerieke inputs negeren tijdelijk lege of onvolledige exponentwaarden; `NaN` bereikt de solver niet meer.
- `a_sim` heeft een expliciete vloer van `1e-18 m`.
- SI-parser accepteert `am`, `fm`, `pm`, `nm`, `um`/`µm`, `mm`, `cm` en `m`.
- De UI schrijft altijd de werkelijk toegepaste `P.a` terug na kern-/circulatiekoppeling.
- Wanneer de gevraagde radius onder de minimale gekwantiseerde `n=1` similarity-radius ligt, wordt `coreFlowLock` expliciet ontgrendeld in plaats van de invoer stilzwijgend te vervangen.
- Contactdetectie gebruikt `max(3a, 64·ε_machine·L_ref)`; de HUD-notitie en ModelLog melden wanneer de numerieke vloer actief is.

## ModelLog 0.2

- Globale, vertrouwde UI-registratie werkt ook voor controls die naar het OVERZICHT-dock zijn verplaatst.
- Segmentknoppen, normale controls, steppers, Reset en export worden geregistreerd.
- Diagrecords worden maximaal 5× per seconde opgeslagen.
- Gescheiden limieten voor acties, stappen en events.
- JSON bevat limieten en drop-tellers; de trace is expliciet begrensd en wordt niet als onbeperkte reconstructie gepresenteerd.
- Runtime errors en unhandled promise rejections worden als event vastgelegd en zichtbaar als harde runtimeflag.

## UI en provenance

- Verwijdert de tweede dynamische OVERZICHT-container; alleen `#quickControlsDock` blijft bestaan.
- HTML-meta, runtimeversie, zelftesttitel en exportbestandsnaam gebruiken v7.3.1 consistent.
- De SST-constantencomment verwijst naar Canon v0.8.20; de numerieke waarde is niet gewijzigd.

## Validatie

- Unified diff is droog getest en reproduceert byte-identiek de meegeleverde v7.3.1-build.
- Inline JavaScript slaagt voor `node --check`.
- Een echte browser/WebGL-smoketest blijft verplicht; de huidige container kon geen EGL/WebGL-context initialiseren.
