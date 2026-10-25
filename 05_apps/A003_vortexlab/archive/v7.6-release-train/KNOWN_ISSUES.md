# Known issues

## v7.6.7 — startup regression

Status: **fixed in v7.6.8**.

Symptoom: zwart simulatorcanvas; statische HUD/UI blijft zichtbaar.

Oorzaak: een vroege `syncUi()` riep `syncSpecClockQuickControls()` aan, die `typeof ModelLog` gebruikte terwijl de lexicale `const ModelLog` nog in de temporal dead zone stond. Voor een `let`/`const` in de TDZ is zelfs `typeof` niet veilig.

## v7.6.8 — te sterke spec-clock-classificatie en flikkerende overlay

Status: **fixed in v7.6.9**.

Symptomen: een ongemapte body-faseproxy buiten de formele veldbracket werd ten onrechte als falsificatie van de parametercombinatie omschreven; `SPEC CLOCK QUICK` kon zichtbaar flikkeren en bleef in botsingsmodus ook zonder actieve diagnose staan.

Oorzaken: twee proxies zonder afgeleide overdrachtswet werden als formele closure-test behandeld, terwijl de overlay bij iedere periodieke update het volledige `innerHTML`-subtree opnieuw opbouwde.

## v7.6.9 — quick-controls springen terug en afstand stopt op 1 m

Status: **fixed in v7.6.10**.

Symptomen: \(\Delta z_{AB,0}\) kon niet boven de cilinderhoogte worden ingesteld; quick-velden sprongen tijdens typen terug; de quick-knoppen veranderden de MODEL-toestand niet.

Oorzaken: de afstandssetter gebruikte \(2H_{\rm cyl}\) als harde modelgrens, periodieke diagnostiek schreef de invoerwaarden continu terug, en de visueel gekloonde quick-controls hadden geen eventbindings. Een grotere afstand vereiste bovendien expliciete uitschakeling van periodieke z-wrapping.
