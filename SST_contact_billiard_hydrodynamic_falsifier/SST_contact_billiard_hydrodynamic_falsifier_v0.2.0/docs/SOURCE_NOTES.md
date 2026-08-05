# Bronnotities: Carlen EPFL thesis no. 4621

Pakketonderdelen die rechtstreeks door de thesis zijn gemotiveerd:

- definitie van thick curves, thickness en `pt`;
- extractie van contactchords met numerieke tolerantie;
- twee contacttakken voor de ideale trefoil;
- gesloten 9-billiard door iteratie van een contactfunctie;
- reductie tot twee onafhankelijke curvefragmenten via symmetrie;
- evenwicht \(T\kappa\mathbf n+\mathbf F=0\);
- scalaire compatibility
  \(F^{\mathrm O}(s)=-F^{\mathrm I}(\sigma(s))\sigma'(s)\).

Niet door de thesis geleverd en daarom in dit pakket als nieuwe testlaag gemarkeerd:

- de Rosenhead-regularized Biot–Savart sweep;
- de Hamiltoniaanse finite-core energiegradiënt;
- de SST SI-normalisatie;
- H5–H8 thresholds;
- de interpretatie als SST-falsificatieketen.

De thesis zelf waarschuwt dat de hoek-/krachtcompatibiliteit niet a priori uit
ropelength-minimalisatie volgt. Het pakket behandelt H4 daarom als bridge en niet als
bewezen Euler–Lagrange-wet voor de ideale trefoil.


## Gebundelde geometriebron

Vanaf v0.2.0 is de gebruiker-aangeleverde `data/ideal_favorites.txt` byte-identiek gebundeld
(\cite{Gilbert2016}). De letterlijke XML-header is:

```xml
<DATA Title="Database of Ideal Knots 3-10 crossings" Author="Brian Gilbert" Date="6/11/2016 2:12:11 p.m.">
```

De file-SHA-256 is `942cb24b2a461b66cc3d35352f0723de97718a0e579ec524b8bb1c7ac4b9ad27`.
De softwarelicentie wordt niet geïnterpreteerd als databanklicentie.

### Bruikbaarheid van Fourier-records

Van de ~250 AB-records zijn er ongeveer **144** reconstrueerbare
krommingsartefacten zonder zelfcontact (`κ̂_max = 2` exact; dikte volledig
door MinRad bepaald). Ongeveer **106** records hebben echt contact.
Behandel een record pas als ideaal wanneer de thickness-partition score
`C_cont > 0.05` (zie SST-Workbench `sst_gilbert_usability.py`:
`C_cont = clamp((2D - d_min)/D, 0, 1)` met booglengte-uitsluiting ~π·R).
Op de bruikbare set is empirisch
\(I_{\kappa^2}/L_D = 1{,}0587\pm0{,}0699\) (6,6%);
`C_cont·L_D` is praktisch niet te onderscheiden van `L_D` (\(r\approx0{,}997\)).
Validatie-ankers: trefoil-writhe-magnitude ≈ 3,417; cirkel `0:1:1` geeft
`I_κ²/L_D = 4` exact.
