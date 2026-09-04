# Fysieke vortexbuizen versus numerieke discretisatie

## Fysieke buizen

Iedere buis draagt een vaste circulatie:

\[
\Gamma_j=\Gamma_{\rm tube}.
\]

Daarom:

\[
\Gamma_{\rm hole}=N\Gamma_{\rm tube},
\qquad
\overline\omega_z=
\frac{N\Gamma_{\rm tube}}
{\pi R_{\rm bundle}^2}.
\]

Meer buizen betekent een andere fysieke toestand, een andere klokfrequentie en doorgaans een sterker achtergrondveld.

## Numerieke discretisatie

De totale bundelflux is vooraf vastgelegd:

\[
\Gamma_{\rm hole}=\Gamma_{\rm target}.
\]

Iedere discretisatiebuis draagt:

\[
\Gamma_j=\frac{\Gamma_{\rm target}}{N}.
\]

Daarom zijn

\[
\Gamma_{\rm hole},\quad
\overline\omega_z,\quad
\Omega_\Gamma
\]

onafhankelijk van \(N\). Alleen de ruimtelijke benadering van het continuüm verandert.

## Verboden samenvoeging

De twee \(N\)-ladders mogen niet in één fit of convergentiegrafiek worden samengevoegd:

\[
\boxed{
N_{\rm physical}\neq N_{\rm discretization}.
}
\]

Een fysieke-buizenreeks is een parameterstudie van de totale flux. Een discretisatiereeks is een numerieke foutstudie.

## Huidige modelgrens

De buizen zijn in v0.3.0:

- recht;
- parallel aan de gekozen as;
- oneindig in beide richtingen;
- bevroren in positie;
- finite-core geregulariseerd.

Niet inbegrepen:

- buiging van de achtergrondbuizen;
- reconnection;
- Kelvin-golven op de buizen;
- terugreactie van de trefoil op de buisposities;
- dynamische vortexdichtheidscompressie.
