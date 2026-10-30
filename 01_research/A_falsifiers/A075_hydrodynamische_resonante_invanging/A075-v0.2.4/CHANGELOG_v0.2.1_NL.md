# A075-v0.2.1 — verfijnde rooster- en tijdstapladder

De A075-v0.2.0-campagne, eventuele bevriezing en outputs blijven intact.

- PREVIEW: N=48 -> 64; dt=0,020 -> 0,010; T=0,6. Nog ONDEROPGELOST: alleen software-smoke.
- BASIC: N=80 -> 112; dt=0,015 -> 0,0075; T=1,2. Begin-screening, 4,0 -> 5,6 cellen per Gaussische sigma.
- FULL: N=96 -> 128; dt=0,010 -> 0,005; T=9,0. Zware screening, 4,8 -> 6,4 cellen per sigma.
- Fysieke kernbreedte a=0,50 en box L=10 blijven binnen de verfijningsladder onveranderd.
- Courant-screen <= 0,20. Fluxresidu en Courant worden nu over basis, halve tijdstap én fijner rooster getoetst.
- Nieuw `python run_preview.py --profile FULL --plan` controleert vooraf zonder Euler-run.
- Framework-v1.0.10-prefreeze-fix uit v0.2.0-p1 geïntegreerd.
- 14 korte tests; geen fysische PASS, geen nieuwe FULL-run en geen knoopbestanden meegeleverd.

Vereist voor fysische conclusies: minimaal derde ruimtelijke resolutie, afgenomen kernprofielen, verificatie van dynamisch veranderende kernbreedte, doosgrootte, drukflux, onafhankelijke bronvertrek- en ontvanger-klokdiagnostiek.

Deze nieuwe bron is **niet** een overlay voor een reeds bevroren v0.2.0-protocol. Plaats als `A075-v0.2.1` naast de oudere versie. Genereer nieuwe private commitments bij deze nieuwe versie.
