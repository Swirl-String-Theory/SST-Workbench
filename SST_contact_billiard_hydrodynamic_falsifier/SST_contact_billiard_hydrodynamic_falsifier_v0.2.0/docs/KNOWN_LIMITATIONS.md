# Bekende beperkingen en noodzakelijke upgrades

1. **Geen exact thicknesscertificaat.** De implementatie gebruikt continue splines en
een sampled DCSD/reach-proxy. Voor theorem-grade resultaten is een biarc- of gecertificeerde
polygonal-thicknesslaag vereist.

2. **Contacttakken kunnen verkeerd wisselen.** Continuationtracking minimaliseert lokale
sprongen, maar globale branch swaps blijven mogelijk. Inspecteer altijd `contact_map.png`
en de winding/inverse residuals.

3. **De 9-billiard kan een interpolatieartefact zijn.** Vereist stabiliteit onder
resolutie, inputfamilie, optimizer tolerance, splineorde en contacttolerance.

4. **Twee-contactaanname.** Geïsoleerde derde contacten of kink-active constraints
worden niet als aparte complementarity multipliers opgelost.

5. **Finite core is een regularisatie.** De Rosenhead-type kernel lost geen
vorticiteitsprofiel, drukveld of kernvervorming op. Een vervolgversie moet ten minste
twee onafhankelijke coreprofielen en uiteindelijk een resolved-core Euler/BEM/PDE-laag
bevatten.

6. **Hamiltoniaanse gradiënt is geen dissipatieve krachtwet.** H6 test de
variatiederivaat van de regularized kinetic-energy proxy; H5 test afzonderlijk de
vortexkinematica.

7. **Local/nonlocal split is gridafhankelijk.** `local_band=3` heeft geen invariant
continuumbetekenis. Alleen convergente trends mogen fysisch worden geïnterpreteerd.

8. **Absolute SST-schaal is conditioneel.** De standaardkeuze
\(\Delta_{\rm phys}=r_c\), \(\Gamma=2\pi r_c\mathbf v_{\!\boldsymbol{\circlearrowleft}}\)
en \(\rho_{\!f}=7.0\times10^{-7}\,\mathrm{kg\,m^{-3}}\) is canonieke
normalisatie, geen afleiding uit de contactgeometrie.

9. **Topologie wordt niet opnieuw bewezen.** Een Gilbert-ID of bestandsnaam is
provenance (\cite{Gilbert2016}). Gebruik een onafhankelijke knot
invariant/topology guard wanneer de input niet uit een gecontroleerde
Ridgerunner-pipeline komt.

9a. **Niet elk Gilbert-AB-record is een ideale knoop.** Ongeveer 144 van ~250
Fourier-records hebben na reconstructie geen zelfcontact en
\(\hat\kappa_{\max}=2\) exact (krommingsartefact). Pas `C_cont > 0.05` toe
vóór gebruik als ideale seed; zie SST-Workbench `sst_gilbert_usability.py`.

10. **Geen fit op een bekende natuurconstante.** Het pakket gebruikt geen
\(\alpha\), massa, \(G\) of Plancklengte als target.

11. **Referentie-implementatie, geen performance solver.** De energiegradiënt gebruikt
centrale finite differences en een directe dubbele segmentsom. De kosten schalen
ongeveer als \(O(N^3)\). Hogere hydrodynamische resoluties vereisen analytische
gradiënten, blockwise kernels, native code of een tree/FMM-accelerator.

12. **Eén component.** De huidige VECT- en hydrodynamische route accepteert één gesloten
component. Links vereisen expliciete intra- en intercomponent-contacttakken.


## RUN_ALL-computationele grens

De `max`- en `extreme`-presets vergroten de evidence matrix, maar veranderen de fundamentele modelklasse niet: alle hydrodynamische runs gebruiken dezelfde Rosenhead-type filamentregularisatie. Resolutie- en parameterrobustheid binnen één kernel is geen onafhankelijk bewijs van een resolved finite-core Euler-oplossing. De finite-difference Hamiltoniaangradiënt schaalt bovendien ongeveer als $O(N^3)$; de hoogste presets zijn bedoeld voor langdurige lokale campagnes en niet voor interactieve uitvoering.
