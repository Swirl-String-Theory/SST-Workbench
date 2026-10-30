# Wiskundige constructie en kwalificatiegrenzen

## Doel: gekoppeld Euler-evenwicht, niet alleen knoopvormbehoud

Voor de trefoil K en de (gesloten) achtergrondvorticiteit B geldt onder
3D incompressibele Euler met gedeelde snelheid

\[ \partial_t\omega_\alpha=\nabla\times(u_{\rm tot}\times\omega_\alpha),\quad
u_{\rm tot}=\mathcal K_D[\omega_K+\omega_B],\quad \alpha\in\{K,B\}. \]

Er wordt **geen** one-way coupling toegepast, behalve in de expliciet gemarkeerde
`frozen_background_diagnostic`-controlerun.

## Exact solenoïdale seed bij een gesloten polygonale lijn

Voor iedere georiënteerde, gesloten polygonale lijn `X` is de *geperiodiseerde*
Gaussian-gespreide vorticiteit

\[ \omega_\sigma(x)=\Gamma\sum_j\int_0^1
 (X_{j+1}-X_j)G_\sigma^{\mathrm{per}}(x-X_j-t(X_{j+1}-X_j))\,dt. \]

De divergentie is continu exact nul: uit
`d/dt G(x-X_j-t ΔX_j)=-ΔX_j·∇G`
volgt `∇·ω = -Γ Σ[G(x-X_{j+1})-G(x-X_j)] = 0`.

De Fouriercoëfficiënten van het polygonale lijnintegraal worden **analytisch**
uit de eindpunten berekend:

\[
 \hat\omega(k)=\frac{\Gamma}{h^3}e^{-\sigma^2|k|^2/2}
 \sum_j\Delta X_j\,e^{-ik\cdot (m_j+L_{\rm box}/2)}
 \operatorname{sinc}\left(\frac{k\cdot\Delta X_j}{2}\right).
\]

Daarbij `sinc(z)=sin(z)/z`. De implementatie verwijdert hoge Fouriermodi
via de 2/3-dealiaseringsregel en voert een spectrale Helmholtz-projectie uit.
De correctiegrootte wordt gelogd: dit is NIET hetzelfde als een bewijs van
continuumconvergentie.

Gaussianmollificatie is glad, maar heeft GEEN compacte drager.
`σ=0.12` is de vervagingsbreedte en **niet** een bewezen scherpe buisgrens of
electron/kernstraal in fysieke meter. Er wordt geen SST-constante gebruikt.

## Periodieke ruimte en terugtak

De kubus `[-3,3)^3` heeft periodieke randvoorwaarden. Eén achtergrondlus is
een racetrack met hoofdtak `(x,y)=(0,0)` voor `z∈[-1.3,1.3]`, retourtak
bij `x=2` en gladde halfronde eindkappen op `|z|>1.3`. Daarom is de
netto axiale vorticiteitsflux nul. De retourtak behoort onlosmakelijk tot de
gehele Euler-vorticiteit en reageert zelf ook dynamisch. Een oneindige
parallelle vortex en een oneindig rooster zijn NIET gesimuleerd.

De kubische 3-torus is continu invariant onder `z`-translatie maar niet
onder willekeurige rotatie rond `z`. Daarom kwalificeert deze versie alleen
het residu in een gemeenschappelijk `U_z`-meebewegend frame:

\[
 R_\alpha=\nabla\times(u_{\rm tot}\times\omega_\alpha)
       +U_z\partial_z\omega_\alpha.
\]

`U_z` wordt over **alle** afzonderlijke vorticiteitscomponenten gezamenlijk
met kwadratische foutminimalisatie gefit.

**Cruciaal interpretatiepunt:** het achtergrondresidu in de alleen-run
wordt met een ándere optimale `U_z` gemeten dan het achtergrondresidu in
de gezamenlijke run. Het verschil van die twee residunormen meet dus
NIET zuiver de terugkoppeling. De fysieke kruistermen worden ook
rechtstreeks, zonder referentiekaderfit, gemeten als
`curl(u_B × ω_K)` en `curl(u_K × ω_B)` en tegen de directe Euler-RHS
verschillen gevalideerd. Rotatie-`Ω` is bewust niet gefit.
De grootte `R*_α=L0^4/Γ_K^2 rms(R_α)` wordt voor iedere component
apart gerapporteerd, evenals `max_α R*_α`.

## Onafhankelijke formuleringscontrole

Daarnaast wordt de druk-geëlimineerde impulsbalans berekend:

\[ \mathcal M=P_{\rm div=0}\{[(u-U_z e_z)\cdot\nabla]u\},\quad
 M^*=L_0^3/\Gamma_K^2\operatorname{RMS}(\mathcal M). \]

Beide controles gebruiken hetzelfde spectrale snelheidsveld maar
**verschillende Euler-formuleringen en afgeleideoperatoren**. Dit is
een cross-check, niet een volledig onafhankelijke eindige-elementenoplosser.
Het stationaire ABC (Arnold–Beltrami–Childress)-controleveld heeft nulresidu;
een voortplantende vortexringtest controleert `U_z` (geen Fourier/reële-ruimte
vermenigvuldiging toegestaan).

## Kwalificatie en beperkingen

- `G2_COUPLED_UNRESOLVED`: geen geoptimaliseerd gezamenlijk Euler-evenwicht;
  het residu is groot en niet ruimtelijk naar nul geconvergeerd.
- Analytisch divergentievrij: waar voor het Gaussian-gespreide gesloten
  lijnveld; digitaal bandbegrensd divergentievrij tot afronding.
- Numerieke topologie: nog niet rigoureus gevolgd of gecertificeerd;
  afzonderlijke evoluerende spectrale vorticiteitsvelden bewaren wel hun
  divergentieregel maar niet automatisch materiële linkinggetallen.
- Tijdsolver: pseudo-spectrale Euler-evolutie met RK4 (vierde-orde
  Runge–Kutta), 2/3-dealiasering en CFL (Courant–Friedrichs–Lewy)-controle.
- Geen universele rotorfrequentie, viskeuze demping, kunstmatige druk of
  externe stabiliserende kracht toegevoegd.
- Bronembeddings `T_2_3` en `T_3_2` blijven onafhankelijke geometrische
  seeds. Géén a-priori dynamische equivalentie.
- Alle waarden zijn dimensieloos, `R0=1`, `Γ_K=1`, `σ=0.12`,
  `Γ_B=0.05` (met negatieve en sterkere controles op lage resolutie).

## Hard stop voor wetenschappelijke evenwichtsclaims

Gate 2 kan pas PASS krijgen als een niet-triviaal gemeenschappelijk stationair
veld is gevonden, met klein `R*_K` én `R*_B`, onafhankelijke druk/
impulscheck, ruimtelijke en temporele convergentie, en behoud van
niet-onthullende topologische invarianten. Niets hiervan wordt door een
korte-tijdsrun afgedwongen of reeds beweerd.
