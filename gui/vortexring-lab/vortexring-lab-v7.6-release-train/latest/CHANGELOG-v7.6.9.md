# v7.6.9 — Spec-clock proxysemantiek en stabiele overlay

Parent: `v7.6.8`

## Fixed

- Een faseproxy buiten de formele veldbracket wordt niet langer als falsificatie van de parametercombinatie of SST-klokwet gepresenteerd.
- Ruwe overlap en afwijking zijn expliciet ongemapte Research-Track-diagnoses; beide vereisen nog een afgeleide interne fase-observable en overdrachtswet.
- De `SPEC CLOCK`-overlay is alleen zichtbaar wanneer de speculative clock actief is.
- De overlay bouwt zijn DOM één keer op en wijzigt daarna alleen veranderde tekstvelden; de voortdurende volledige `innerHTML`-reconstructie en zichtbare flikkering zijn verwijderd.
- Ook uitgeschakelde, geblokkeerde en wachtende toestanden synchroniseren nu de overlay zichtbaar/verborgen-status.

## Regression coverage

- `T0r`: een ongemapte proxy-afwijking heeft altijd `falsified=false`.
- `T0s`: de overlay behoudt dezelfde DOM-nodes over opeenvolgende updates en verdwijnt zodra de diagnose uit staat.
