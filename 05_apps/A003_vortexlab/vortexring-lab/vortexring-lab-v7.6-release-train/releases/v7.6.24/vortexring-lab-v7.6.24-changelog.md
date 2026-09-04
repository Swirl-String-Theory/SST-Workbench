# VortexLab v7.6.24 — changelog en technische audit

**Parent:** v7.6.23  
**Base lineage:** v7.5.3  
**Proxy schema:** `vortexlab-spec-clock-proxy-decomposition/1.8`  
**Status:** Research Track; geen solverfeedback en geen canonieke klokwet

## Samenvatting

V7.6.24 corrigeert de resterende aggregatiefouten in R24–R26, vervangt de cross-knotvergelijking op de vaste lab-z-as door een intrinsieke rigid-rotationprojectie, canonicaliseert de holdout-embeddings en breidt de holdoutmatrix uit naar vijf Fourier/idealparen.

De CLOCK-sidebar is daarnaast horizontaal resizebaar en bewaart zijn breedte. In het CLOCK-paneel staat een ingebouwde roadmap voor de volgende onderzoeksversies.

## 1. Gecorrigeerde gates

R24, R25 en R26 filteren voortaan vóór aggregatie op:

```js
candidate.applicable === true && Number.isFinite(metric)
```

Replay op de echte v7.6.23-output geeft:

- R24: `PASS`, maximale tijdstrajectspreiding `0.0434457`;
- R25: `PASS`, maximale pariteitsmismatch `9.8448e-5`, maximale null/signal `3.8076e-5`;
- R26: `PASS`, maximale verandering N=512→768 `0.0419358`;
- R27 blijft `FAIL`;
- R22 blijft `FAIL` wegens niet-geconvergeerde reach/DCSD-route.

Niet-toepasselijke ideal-metadatafactoren op Fouriercurves kunnen daardoor geen `NaN` meer in het algemene verdict injecteren.

## 2. Volledige rigid-rotationvector

Iedere snapshot exporteert voor A en B, en voor `iso`, `mutual` en `full`:

\[
\boldsymbol\Omega=(\Omega_x,\Omega_y,\Omega_z),
\]

plus:

\[
\Omega_\parallel=\boldsymbol\Omega\cdot\hat{\mathbf e}_{\rm carrier},
\qquad
|\boldsymbol\Omega|,
\qquad
|\boldsymbol\Omega_\perp|.
\]

De intrinsieke carrier-as is de kleinste-variantie-as van een arclengthgewogen covariance-frame. Het frame wordt rechtsdraaiend opgebouwd en heeft een deterministische tekenconventie.

De oude `bodyOmegaFlat`/lab-z-projectie blijft behouden voor backwards-compatible trefoil- en Shapleydiagnostiek, maar is niet meer de confirmatoire cross-knotobservable.

## 3. Canonicalized holdout-embeddings

Iedere holdout wordt vóór de passieve run gecanonicaliseerd:

1. centroid blijft op de bestaande A/B-positie;
2. de kleinste principal axis wordt naar lab-z gebracht;
3. een rechtsdraaiend principal frame wordt gebruikt, zonder reflectie;
4. de transversale RMS-radius wordt vastgezet op `0.05 m`;
5. point order, circulatierichting en chiraliteit worden niet herschreven.

Hiermee worden bronoriëntatie, arbitraire rotatie en bron-schaal niet langer stilzwijgend met topology vermengd.

## 4. Tien cross-knot-holdouts

Vijf embeddingparen worden bij N=256, t=0 en t=3 s gemeten:

| Topologie | Fourierbron | Ideal/Gilbert-bron |
|---|---|---|
| trefoil | `3_1` | `3:1:1` |
| figure-eight | `4_1` | `4:1:1` |
| cinquefoil | `5_1` | `5:1:1` |
| twist knot | `5_2` | `5:1:2` |
| stevedore | `6_1` | `6:1:1` |

Per holdout worden gerapporteerd:

- bron en topologyKey;
- canonicalisatieframe en schaal;
- volledige \(\boldsymbol\Omega\)-vectoren;
- legacy \(\delta Q_L\);
- intrinsieke \(\delta Q_\parallel\);
- formele veld-delta;
- vereiste intrinsieke \(\kappa\);
- residu van iedere toepasselijke preregistreerde kandidaat.

De analyse groepeert Fourier en ideal per topologyKey. Het verschil binnen een paar wordt als **embedding/representatiegevoeligheid** gerapporteerd, niet direct als topology-effect.

## 5. Reach-factoren blijven geblokkeerd

De volgende factoren blijven niet-confirmatoir zolang de continue DCSD/reach-solver ontbreekt:

\[
\frac{a_{\rm core}}{L_K},
\qquad
\frac{2a_{\rm core}}{L_K},
\qquad
\frac{1}{\pi\operatorname{Rop}_{\rm diam}},
\qquad
\frac{1}{n_{\rm cross}\operatorname{Rop}_{\rm diam}},
\qquad
\frac{1}{2\pi\operatorname{Rop}_{\rm diam}}.
\]

Ze worden nog wel diagnostisch geëvalueerd, maar `byCandidate.pass` kan voor deze factoren in v7.6.24 niet waar worden.

## 6. Resizebare CLOCK-sidebar

De CLOCK-sidebar heeft een sleepbare linker rand.

- standaard: `560 px`;
- minimum: `360 px`;
- maximum: `min(1100 px, beschikbare viewport)`;
- dubbelklik: herstel standaardbreedte;
- toetsenbord: pijlen ±20 px, Home minimum, End maximum;
- opslag: `localStorage['vortexlab.clock.width']`;
- overlay-offsets en andere geopende rechterpanelen worden live herberekend.

## 7. Ingebouwde roadmap

Onder CLOCK staat een inklapbaar blok **ONTWIKKELROADMAP · v7.6.25 → v7.7.0**. De roadmap staat ook in een afzonderlijk Markdown-bestand in het releasepakket.

## 8. Runneromvang

De decompositionrunner bevat nu:

- 20 scenario’s;
- 49 snapshots;
- zes resoluties voor de basistrefoil;
- twee `a_sim`-negatieve controles;
- tien canonicalized cross-knot-holdouts.

## 9. Exports

JSON en TXT bevatten de volledige intrinsieke datastructuur. CSV bevat aanvullende `INTRINSIC_OMEGA`-records voor:

- carrier A/B;
- current/calibration;
- iso/mutual/full;
- vectorcomponenten;
- \(\Omega_\parallel\), \(|\Omega|\) en \(|\Omega_\perp|\);
- intrinsieke as en topology/embeddingmetadata.

Timestamped auto-export blijft actief.

## 10. Validatie

Uitgevoerd:

- inline JavaScript syntax: PASS;
- 432 statische DOM-id’s, alle uniek;
- 20 scenario’s en 10 holdouts gedetecteerd;
- verwachte snapshotcount: 49;
- alle tien bronkeys aanwezig in `fourier_knots_data.js` en `ideal_knots_data.js`;
- synthetic rigid-rotationtest: \(|\Omega|\), \(|\Omega_\parallel|\) en \(|\Omega_\perp|\) rotatie-invariant;
- canonicalisatie brengt de kleinste principal axis naar lab-z;
- frame-determinant: +1;
- v7.6.23-replay: R24/R25/R26 PASS, R27/R22 FAIL;
- unified diff past schoon op v7.6.23.

Een volledige interactieve WebGL-run van alle 49 snapshots kon niet in de container worden uitgevoerd. De browserrun blijft daarom de definitieve runtimecontrole.
