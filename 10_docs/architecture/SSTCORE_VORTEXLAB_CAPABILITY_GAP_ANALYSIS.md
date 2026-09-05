# SSTcore 0.8.18 ↔ VortexLab v7.6.25b capability-gap analysis

## Doel

Dit document inventariseert welke numerieke functies momenteel in de VortexLab HTML-monolith staan, welke SSTcore C++-klassen al bruikbaar zijn, welke bestaande klassen moeten worden uitgebreid en welke canonieke kernels nog volledig ontbreken.

Auditbasis:

- `vortexring-lab-v7.6.25b.html`
- aangeleverde SSTcore 0.8.18-broncode
- aangeleverde Node/buildbestanden
- huidige SSTcore-repositorystructuur waar buildcontext nodig was

De migratieregel is:

\[
\boxed{\text{één C++-bron van waarheid; Node en Python zijn dunne bindings}}
\]

Niet iedere JavaScriptfunctie hoort naar C++. UI, rendering, workflowstatus, exports en benchmarkrapportage blijven in TypeScript. Alleen pure, numerieke en wetenschappelijk gezaghebbende kernels gaan naar SSTcore.

---

## 1. Hoofdconclusie

SSTcore bevat al sterke bouwblokken, maar is nog geen drop-in backend voor VortexLab.

### Direct bruikbare of bijna bruikbare C++-bouwblokken

1. `sst::FourierKnot`
   - Fseries parsing.
   - Ideal/Gilbert parsing.
   - Fourier-evaluatie.
   - Exacte eerste en tweede afgeleiden.
   - Exacte kromming, lengte en bending energy.

2. `sst::ResolvedTubeGeometry`
   - Polygonale lengte.
   - Polygonale MinRad.
   - Exacte segment-segmentafstand.
   - Discrete DCSD-kandidaten.
   - Discrete thickness/reach en ropelength.

3. `sst::BiotSavart`
   - Punt- en grid-Biot–Savart.
   - Expliciete circulatie.
   - Veld/vorticiteit/invariant-primitieven.

4. `sst::KnotDynamics`
   - Writhe/linking/twist APIs.
   - Fourier series evaluation.
   - PD/crossing utilities.
   - Deze invarianten gebruiken echter niet dezelfde exacte polygonale solid-anglemethode als VortexLab.

5. `sst::FrenetHelicity`
   - Frenetframes.
   - Kromming/torsie.
   - Helicity utilities.
   - Een RK4-helper, maar niet de volledige VortexLab multi-filamentsolver.

6. `sst::FilamentEvolution`
   - Basiscurve-initialisatie.
   - Basis-Biot–Savart-evolutie.
   - Momenteel single-filament en Euler; niet geschikt als VortexLab-pariteitsengine.

7. `sst::clock` en canonical constants
   - Canonieke constanten.
   - Swirl-clockfactor uit snelheid.
   - Goede basis voor scalar utilities.

### Vier grootste ontbrekende canonieke kernels

\[
\boxed{\text{1. VortexLab multi-filament velocity + RK4}}
\]

\[
\boxed{\text{2. continue }C^2\text{ reach/DCSD}}
\]

\[
\boxed{\text{3. exacte polygonale Gauss/Wr/Lk/ACN}}
\]

\[
\boxed{\text{4. intrinsic frame + rigid-motion decomposition}}
\]

Zonder deze vier blokken kan de browsermonolith nog niet worden vervangen door SSTcore zonder numerieke of semantische regressies.

---

## 2. Wat niet naar C++ hoeft

Deze onderdelen blijven frontend of Node-service:

- Three.js rendering.
- DOM-controls en sidebars.
- HUD/SPARK/LIVE-layout.
- downloadknoppen en bestandsnamen.
- workflow unlock/lock.
- benchmarkscenarioselectie.
- Shapley-combinatoriek en rapportopmaak.
- JSON/CSV/TXT exports.
- progress events.
- UI-presets.
- visual suppression/restoration.
- `fitContinuumSeries` mag voorlopig TypeScript blijven; het is niet de zware kernel.
- ENGINE/RESEARCH-presentatie blijft TypeScript, maar de onderliggende numerieke observabelen komen uit C++.

---

## 3. C++-klassen die al grotendeels klaar zijn

### 3.1 `sst::FourierKnot` — grotendeels klaar

VortexLab-functies:

- `sampleFourierParametric`
- `sampleFourierKnot`
- `sampleIdealComponent`
- `vlBuildFourierCurve`

Bestaand in C++:

- `FourierKnot::evaluate`
- `FourierKnot::evaluate_with_derivatives`
- `FourierKnot::curvature_exact`
- `FourierKnot::length_exact`
- `FourierKnot::parse_fseries_*`
- `FourierKnot::parse_ideal_*`
- `FourierKnot::evaluate_ideal_ab_components`

Nog nodig:

- uniforme gesloten-booglengteresampling;
- één brononafhankelijk `sample_curve`-contract;
- Node-wrapper voor Ideal/Gilbert;
- Node-wrapper voor exacte afgeleiden;
- expliciete componentmetadata.

Advies: **niet alles verder in `FourierKnot` stoppen**. Voeg `sst::curve::CurveSampling` en `sst::catalog::KnotCatalog` toe.

### 3.2 `sst::ResolvedTubeGeometry` — sterke polygonale basis

VortexLab-functies:

- `arcLength`
- `segSegDist2`
- `pairGapExact2`
- `dminSelf`
- `topologyClearance`
- `minCurvatureRadius`

Bestaand in C++:

- `length`
- `global_minrad`
- `segment_segment_distance`
- `dcsd_candidates`
- `analyze`
- witnessparameters `s`, `t` in `SegmentPair`

Nog nodig:

- meerdere componenten in één analyse;
- expliciete inter-componentminimumafstand;
- component-ID’s in witnesses;
- aparte `clearance` API zonder ropelengthsemantiek;
- Node-binding;
- onderscheid tussen polygonale thickness en continue \(C^2\)-reach.

Advies: breid `ResolvedTubeGeometry` alleen uit voor **polygonale** geometrie. Maak continue reach als aparte klasse.

### 3.3 `sst::BiotSavart` — primitief klaar, VortexLab-semantiek ontbreekt

VortexLab gebruikt een specifieke midpoint-segmentkernel met:

- per-filament \(\Gamma\);
- LIA-lokale term;
- nonlocal self-term;
- mutual term;
- `a_sim²` alleen op cross/mutual routes volgens de huidige implementatie;
- uitsluiting van aangrenzende eigen segmenten;
- ghostfilamenten als niet-bron;
- optionele externe velocity;
- optionele Schwarz mutual friction.

De huidige `BiotSavart` is bruikbaar als primitive, maar niet als volledige `velocityCore`-vervanging.

Advies: voeg geen tientallen booleans aan `BiotSavart` toe. Maak:

```cpp
sst::filament::FilamentVelocitySolver
```

die intern `BiotSavart`-primitieven gebruikt.

### 3.4 `sst::KnotDynamics` — API aanwezig, algoritme niet parity-safe

VortexLab gebruikt `segPairOmega` + `gauss2`:

- exacte polygonale solid angle per segmentpaar;
- signed integral;
- absolute integral;
- Wr en ACN in één passage;
- Lk en cross-ACN in één passage;
- geen interne integer rounding.

SSTcore gebruikt momenteel een sampled Gauss-som en `compute_linking_number` rondt naar `int`.

Advies: voeg een nieuwe klasse toe:

```cpp
sst::knot::PolygonalGaussInvariants
```

en laat legacy `KnotDynamics::compute_linking_number` voorlopig bestaan voor backward compatibility.

### 3.5 `sst::FrenetHelicity` — bruikbaar met conventieaudit

De Frenet- en curvaturefuncties zijn bruikbaar. Controleer wel:

- periodieke eindpunten;
- normalisatie van tangenten;
- parameter versus booglengte;
- gedrag bij bijna nul kromming;
- resultaatconventies tegen VortexLab-golden fixtures.

De bestaande `rk4_integrate` is niet automatisch dezelfde integrator als `rk4Step`.

### 3.6 `sst::FilamentEvolution` — class aanwezig, fundamentele uitbreiding nodig

De huidige implementatie:

- ondersteunt één positiearray;
- berekent velocity per punt;
- gebruikt Euler;
- kent geen meerdere componenten/carriers;
- kent geen per-component circulatie;
- kent geen regularisatieconfiguratie;
- kent geen topology guard;
- kent geen external/background field;
- kent geen CFL.

Deze class kan als compatibiliteitswrapper blijven bestaan, maar de nieuwe backend hoort op een nieuwe pure systeem-API te bouwen.

---

## 4. Nieuwe C++-klassen die moeten worden toegevoegd

### 4.1 `sst::curve::CurveSampling`

```cpp
struct CurveComponent {
    std::string id;
    std::vector<Vec3> points;
    double circulation = 1.0;
};

class CurveSampling {
public:
    static std::vector<Vec3> sample_fourier(
        const FourierBlock&, std::size_t n, bool arclength_uniform);

    static std::vector<Vec3> resample_closed_arclength(
        const std::vector<Vec3>&, std::size_t n);

    static std::vector<Vec3> reverse_traversal(
        const std::vector<Vec3>&);
};
```

Vervangt:

- `sampleFourierParametric`
- `sampleFourierKnot`
- `resampleClosedCurve`
- `reverseTraversal`

### 4.2 `sst::catalog::KnotCatalog`

Ondersteun:

- Fseries.
- Ideal/Gilbert.
- KnotPlot uniform-N300.
- meerdere componenten.
- `L`, `D`, status, family, topology ID.
- `torus_6.9`-metadata.
- pairwise linkingmetadata.
- source SHA-256 en source role.

Geen browser-specifieke globale JS-objecten in de engine.

### 4.3 `sst::geometry::PeriodicCubicSpline3D`

Vervangt:

- `vlTridiagonalSolve`
- `vlCyclicSolve`
- `vlBuildPeriodicSpline`
- spline `eval` met \(p,p',p''\)

Eisen:

- periodiek \(C^2\);
- chord-lengthparameter;
- deterministisch;
- evaluatie modulo totale lengte;
- unit tests op cirkel en rigid transform.

### 4.4 `sst::geometry::ContinuousReachSolver`

Vervangt:

- `vlCurvature`
- `vlGoldenMax`
- `vlContinuousCurvatureLimit`
- `vlPairMetrics`
- `vlRefinePair`
- `vlContinuousPairDistance`
- `vlBuildKnotPlotReachCurve`

Resultaat:

```cpp
enum class ReachLimiter {
    Curvature,
    SelfDcsd,
    InterComponent,
    Tie
};

struct PairWitness {
    std::size_t component_a;
    std::size_t component_b;
    double s;
    double t;
    Vec3 p;
    Vec3 q;
    double distance;
    double orthogonality_residual;
    bool local_minimum;
    double hss, htt, hst, hessian_det;
    bool used_damped_least_squares;
};

struct ContinuousReachResult {
    double curvature_radius;
    double self_dcsd;
    double self_radius;
    double inter_component_distance;
    double inter_component_radius;
    double reach;
    ReachLimiter limiter;
    PairWitness self_witness;
    PairWitness inter_witness;
};
```

Belangrijk: de solver moet de gedempte least-squaresfallback uit v7.6.25a behouden voor rank-deficiënte cirkelfamilies.

### 4.5 `sst::filament::FilamentVelocitySolver`

Vervangt:

- `velocitySingle`
- `velocityCore`
- `velAll`
- `directMutualGlobal`
- `carrierMutualTangentialRms`
- `carrierMeanSelfVz`

Voorstel:

```cpp
struct FilamentComponent {
    std::string id;
    std::string carrier;
    std::vector<Vec3> points;
    double circulation;
    bool dynamic = true;
    bool source = true;
};

struct VelocityOptions {
    bool lia_only = false;
    bool include_external = true;
    bool include_mutual_friction = false;
    double a_sim = 0.0;
    double core_delta = 0.0;
    double lia_constant = 0.0;
};

struct VelocityFieldResult {
    std::vector<std::vector<Vec3>> velocity;
    double maximum_speed;
};

class FilamentVelocitySolver {
public:
    static VelocityFieldResult evaluate(
        const std::vector<FilamentComponent>&,
        const VelocityOptions&,
        const ExternalVelocityField* external = nullptr);
};
```

De eerste parity-versie implementeert alleen:

1. LIA.
2. Nonlocal self.
3. Mutual Biot–Savart.
4. Per-component \(\Gamma\).
5. `a_sim`-semantiek exact zoals de monolith.

Background flow en mutual friction pas na deze basis.

### 4.6 `sst::filament::FilamentIntegrator`

Vervangt:

- `rk4Step`
- `dtCFL`
- `lminAll`

```cpp
struct Rk4StepResult {
    FilamentSystemState state;
    double maximum_stage_speed;
};

class FilamentIntegrator {
public:
    static Rk4StepResult rk4_step(...);
    static double estimate_cfl_dt(...);
};
```

De class mag geen DOM, globale state of logging bevatten.

### 4.7 `sst::topology::TopologyGuard`

Vervangt:

- `topologyClearance`
- `topologyStepMayTunnel`
- `transientContactWithinStep`
- `contactEvent`
- `bisectFirstHit`

Eisen:

- exact segmentniveau;
- self- en inter-componentclearance;
- sweep binnen trialstap;
- first-hit bisection;
- retourneert veilige state en witness;
- nooit reconnectie uitvoeren;
- trialstappen hebben geen diagnostische side effects.

### 4.8 `sst::analysis::IntrinsicFrame`

Vervangt:

- `weightedCentroid`
- `symmetricEigen3`
- `intrinsicFrame`
- `deterministicAxisSign`
- `projectOmegaVector`

Eisen:

- gewogen covariance;
- eigenwaarden oplopend;
- kleinste variantie-as als \(e_z\);
- deterministische tekenkeuze;
- rechtshandig orthonormaal frame.

### 4.9 `sst::analysis::RigidMotionDecomposition`

Vervangt:

- `rigidFit`
- `bodyOmegaFlat`
- `carrierBodyOmegaFromVelocity`
- delen van `canonicalizeCarrierGeometry`
- `quaternionRotation`
- `bestCyclicPose`

Resultaat:

```cpp
struct RigidMotionResult {
    Vec3 centroid;
    Vec3 translation;
    Vec3 omega;
    std::vector<Vec3> translation_field;
    std::vector<Vec3> rotation_field;
    std::vector<Vec3> deformation_field;
    double reconstruction_relative_error;
    double deformation_relative_norm;
};
```

---

## 5. Bestaande C++-klassen die moeten worden uitgebreid

| Klasse | Huidige waarde | Vereiste uitbreiding |
|---|---|---|
| `FourierKnot` | parsing/evaluation/derivatives | uniforme arclengthroute of delegate naar `CurveSampling`; Node Ideal wrappers |
| `ResolvedTubeGeometry` | sterke polygonale geometry | multi-component analyze, inter-component witnesses, clearance API, Node wrapper |
| `BiotSavart` | primitive velocity/grid | regularized segment primitive met expliciete options; geen volledige orchestration in deze class |
| `KnotDynamics` | legacy Wr/Lk | nieuwe exact-polygonal API; behoud legacy voor compatibility |
| `FilamentEvolution` | single curve + Euler | compatibility wrapper rond nieuw `FilamentIntegrator`, of deprecate |
| `FrenetHelicity` | frames/curvature/torsion | periodieke/conventietests en typed output |
| `clock` | scalar factor | optioneel stable log-delta/envelope |
| Node addon | veel bestaande wrappers | nieuwe wrappers voor tube, continuous reach, curve catalog, filament solver en analysis |

---

## 6. Functies die in C++ volledig ontbreken

### P0 — nodig voordat SSTcore de VortexLab-engine kan zijn

- `resample_closed_arclength`
- KnotPlot N300 catalog/parser
- multi-component carrier representation
- VortexLab-compatible regularized segment Biot–Savart
- VortexLab LIA-term
- volledige multi-filament velocity RHS
- pure RK4 multi-filamentstep
- VortexLab CFL-estimator
- exact polygonal solid-angle Gauss pair
- signed + absolute Gauss integral
- floating linking diagnostic zonder rounding
- multi-component topology clearance
- swept-step topology guard
- first-hit bisection
- periodieke \(C^2\)-spline
- continue curvature maximum
- continuous self-DCSD
- continuous inter-component minimumdistance
- reach limiter/witness/orthogonalitydiagnostics

### P1 — nodig voor decomposition/holdout authority

- weighted intrinsic frame
- deterministic symmetric eigensolver contract
- transverse-RMS canonicalization
- rigid translation/rotation/deformation fit
- body \(\Omega\)-vector
- \(\Omega_\parallel\)-projectie
- cyclic pose alignment
- exact VortexLab carrier normalization metrics

### P2 — later voor volledige backenddekking

- Schwarz mutual-friction transform
- background wall rotation policy
- bundle velocity profiles
- stretch-profile velocity/vorticity
- bundle BEM Neumann solver
- tracer/streamline fields hoeven niet naar SSTcore tenzij ze wetenschappelijke outputs worden

---

## 7. Node-bindingstatus

### Reeds Node-exposed

- Biot–Savart primitives.
- Fourier/Fseries parsing en evaluation.
- Legacy writhe/linking.
- Frenetframes en curvature/torsion.
- Fluid utilities.
- Vorticity utilities.
- Basic time evolution.
- Canonieke SST utilities verspreid over modules.

### C++ aanwezig maar Node ontbreekt

- `ResolvedTubeGeometry`.
- Ideal/Gilbert parsing en component evaluation.
- uitgebreide Fourier exact-derivative APIs.
- veel moderne `sst::tube` types.
- mogelijk nieuwe split `sst::filament` APIs.

### Volledig nieuw voor C++ én Node

- ContinuousReachSolver.
- PeriodicCubicSpline3D.
- FilamentVelocitySolver.
- FilamentIntegrator parity API.
- TopologyGuard.
- IntrinsicFrame.
- RigidMotionDecomposition.
- PolygonalGaussInvariants.
- KnotPlotCatalog.

---

## 8. Aanbevolen implementatievolgorde

### Kernel milestone K0 — datacontracten

1. `CurveComponent`
2. `FilamentComponent`
3. `FilamentSystemState`
4. typed options/results
5. Node conversion utilities
6. engine version/capabilities

### K1 — geometry parity

1. closed arclength resampler
2. polygonal multi-component clearance
3. exact polygonal Gauss
4. Node wrappers
5. golden tests

### K2 — continuous reach

1. periodic spline
2. continuous curvature
3. self-DCSD
4. inter-component distance
5. witness diagnostics
6. exact circle/two-circle/trefoil/torus fixtures

### K3 — velocity parity

1. regularized segment primitive
2. LIA
3. self/mutual assembly
4. per-component gamma
5. `directMutualGlobal`
6. tangential RMS

### K4 — integration/topology

1. RK4
2. CFL
3. topology clearance
4. step tunneling detector
5. first-hit bisection

### K5 — decomposition

1. intrinsic frame
2. canonicalization
3. rigid fit
4. body omega
5. cyclic alignment

### K6 — optional physical policies

1. mutual friction
2. background rotation
3. bundle/stretch profiles
4. BEM

---

## 9. Golden acceptance tests uit v7.6.25b

### Continuous reach

- Exact circle:
  \[
  a_{\rm reach}=1
  \]
- Twee cirkels op \(z=\pm0.4\):
  \[
  a_{\rm inter}=0.4
  \]
- DCSD orthogonality:
  \[
  \epsilon_\perp < 10^{-8}
  \]
- `torus_6.9`:
  limiter `INTER_COMPONENT`, reach ongeveer \(0.499878\) bij de standaard audit.
- Ideal `3:1:1`:
  self-radius ongeveer \(0.499995\), curvature-limiter ongeveer \(0.461508\).

### Gauss/linking

Voor `torus_6.9` moeten de paarsgewijze linkingwaarden numeriek dicht bij \(-6\) liggen. De API retourneert floating diagnostics plus afzonderlijke integer audit.

### Velocity/decomposition

Gebruik opgeslagen v7.6.25b snapshots:

\[
|x_{\rm C++}-x_{\rm JS}|
\le
a_{\rm tol}
+
r_{\rm tol}\max(|x_{\rm C++}|,|x_{\rm JS}|)
\]

Begin met per-kernel toleranties; gebruik geen algemene ruime tolerantie.

### Dirty-state test

De C++ request bevat alle kritieke parameters expliciet. Geen enkele run mag `a_sim`, BEM, resolution, drift of frame uit een vorige run erven.

---

## 10. Beslissing per monolithfunctie

### Naar SSTcore C++

- curve sampling en resampling
- polygonale en continue geometry
- Biot–Savart/LIA velocity
- RK4/CFL
- topology guard
- exact Gauss/Wr/Lk/ACN
- intrinsic frame
- rigid decomposition
- canonical numerical observables

### Naar Node TypeScript service

- benchmarkscenario’s
- workflow
- Shapley orchestration
- continuumfit orchestration
- gates en reports
- caching/jobs/progress
- provenance en hashes

### In browser houden

- rendering
- UI-controls
- view state
- downloadinteraction
- visual overlays

---

## 11. Minimale eerste VortexLab Node capability release

De eerste bruikbare `@sst/sstcore-native` release hoeft nog niet de volledige simulatie te draaien. Zij moet minimaal bieden:

```ts
engineInfo()
getCapabilities()

sampleCurve(request)
resampleClosedCurve(request)

analyzeResolvedTube(request)
computeContinuousReach(request)

computePolygonalGauss(request)

computeRegularizedMutualVelocity(request)
computeFilamentVelocity(request)

rk4Step(request)
estimateCflDt(request)

computeTopologyClearance(request)
guardTopologyStep(request)

computeIntrinsicFrame(request)
computeRigidMotion(request)
```

Daarmee kan de monolith stap voor stap worden uitgefaseerd zonder een big-bang rewrite.

## 12. Volledige capabilitymatrix

| Domein | VortexLab-functies | Bestaand C++ | Node-status | Status | Vereiste actie | Prioriteit |
|---|---|---|---|---|---|---|
| Curve sampling | `sampleFourierParametric`, `sampleFourierKnot`, `vlBuildFourierCurve` | `sst::FourierKnot::evaluate`, `evaluate_with_derivatives`, `curvature_exact`, `length_exact` | `parseFseriesMulti`, `evaluateFourierBlock` | **PARTIAL_READY** | Add one versioned curve-sampling API; expose exact derivatives and arclength-uniform sampling to Node. | **P0** |
| Ideal-knot loading | `sampleIdealComponent`, `sampleCatalogComponent` | `FourierKnot::parse_ideal_gilbert_from_string`, `parse_ideal_ab_by_id_from_embedded`, `evaluate_ideal_ab_components` | `getEmbeddedIdealFiles only` | **CPP_READY_NODE_MISSING** | Add Node wrappers for ideal metadata, components and sampling. | **P0** |
| KnotPlot uniform-N300 | `sampleKnotPlotComponent`, `vlBuildKnotPlotReachCurve` | `—` | `—` | **MISSING** | Add KnotPlot catalog model with multi-components, native point count, L, D, status, torus/link metadata and SHA provenance. | **P0** |
| Closed-curve arclength resampling | `resampleClosedCurve` | `—` | `—` | **MISSING** | Add deterministic closed-polyline arclength resampler. | **P0** |
| Polygonal tube geometry | `arcLength`, `segSegDist2`, `pairGapExact2`, `dminSelf`, `topologyClearance`, `minCurvatureRadius` | `sst::ResolvedTubeGeometry::length`, `segment_segment_distance`, `global_minrad`, `dcsd_candidates`, `analyze` | `—` | **CPP_STRONG_NODE_MISSING** | Expose ResolvedTubeGeometry to Node; extend it for multi-component clearance and explicit witness records. | **P0** |
| Continuous reach / DCSD | `vlBuildPeriodicSpline`, `vlContinuousCurvatureLimit`, `vlRefinePair`, `vlContinuousPairDistance`, `vlBuildFourierCurve`, `vlBuildKnotPlotReachCurve` | `FourierKnot exact derivatives`, `ResolvedTubeGeometry polygonal reach only` | `reachProxyFromFseries is polygonal proxy only` | **MISSING_CANONICAL_KERNEL** | Create PeriodicCubicSpline3D and ContinuousReachSolver with curvature, self-DCSD, inter-component distance, witnesses, Hessian and orthogonality diagnostics. | **P0** |
| Biot-Savart primitive | `directMutualGlobal`, `carrierMutualTangentialRms` | `sst::BiotSavart::computeVelocity`, `BiotSavart::velocity` | `computeVelocity`, `biotSavartVelocity`, `biotSavartVelocityGrid` | **PRIMITIVE_READY_NOT_PARITY** | Add regularized midpoint segment kernel and explicit target/source multi-component API matching VortexLab a_sim semantics. | **P0** |
| Full filament velocity RHS | `velocitySingle`, `velocityCore`, `velAll`, `carrierMeanSelfVz` | `BiotSavart primitives`, `FilamentEvolution basic single-filament evolution` | `BiotSavart wrappers`, `TimeEvolution` | **MISSING** | Create FilamentVelocitySolver supporting LIA, nonlocal self/mutual Biot-Savart, per-component gamma, regularization, external velocity callback/data and optional mutual friction. | **P0** |
| Time integration and CFL | `rk4Step`, `dtCFL`, `lminAll`, `prescribedKinematicSpeedBound` | `FilamentEvolution::evolve uses Euler`, `FrenetHelicity::rk4_integrate is not the VortexLab system integrator` | `rk4Integrate`, `TimeEvolution` | **NOT_DROP_IN** | Add pure multi-filament RK4 step and deterministic CFL estimator; do not reuse the current Euler evolution as a parity implementation. | **P0** |
| Topology guard | `topologyStepMayTunnel`, `transientContactWithinStep`, `contactEvent`, `bisectFirstHit`, `topologyClearance` | `ResolvedTubeGeometry distance primitives`, `KnotDynamics::detect_reconnection_candidates is point-based` | `detectReconnectionCandidates` | **MISSING** | Create TopologyGuard using segment clearance, swept-step sampling and first-hit bisection. It must stop before contact and never reconnect. | **P0** |
| Gauss invariants | `segPairOmega`, `gauss2`, `gauss` | `KnotDynamics::compute_writhe`, `compute_linking_number` | `computeWrithe`, `computeLinkingNumber` | **ALGORITHM_MISMATCH** | Add exact polygonal solid-angle pair integration returning signed and absolute values. Do not round linking internally; expose integer audit separately. | **P0** |
| Intrinsic frame and canonicalization | `segmentInfo`, `weightedCentroid`, `symmetricEigen3`, `intrinsicFrame`, `canonicalizeCarrierGeometry`, `canonicalizeHoldoutGeometry` | `basic Vec3 operations only` | `—` | **MISSING** | Create GeometryCanonicalizer / IntrinsicFrame with weighted covariance, deterministic axis signs, right-handed frame and transverse-RMS scaling. | **P1** |
| Rigid motion decomposition | `rigidFit`, `bodyOmegaFlat`, `carrierBodyOmegaFromVelocity`, `quaternionRotation`, `bestCyclicPose`, `projectOmegaVector` | `—` | `—` | **MISSING** | Create RigidMotionDecomposition returning centroid, translation U, Omega, rotational field, deformation field and reconstruction residual. | **P1** |
| Frenet / curvature / torsion | `pointTangent`, `stretchSegmentStats` | `sst::FrenetHelicity::compute_frenet_frames`, `compute_curvature_torsion` | `computeFrenetFrames`, `computeCurvatureTorsion` | **READY_WITH_VALIDATION** | Retain, but validate conventions and endpoint/periodicity behavior against VortexLab fixtures. | **P1** |
| Swirl-clock scalar utilities | `specClockEta`, `specClockEnvelope`, `specClockEtaDiffFromDeltaLogs` | `sst::clock::factor_from_speed`, `map_from_velocity_field`, `FluidDynamics::swirl_clock_rate` | `swirlClockRate` | **PARTIAL** | Add numerically stable log-eta delta/envelope utilities only if gate authority moves into C++; otherwise keep orchestration in Node TypeScript. | **P1** |
| Background flow / mutual friction | `backgroundVelocityForFilamentPoint`, `bundleVelocityAt`, `stretchProfileVelocityAt`, `mfTransform` | `FluidDynamics utilities`, `VorticityDynamics utilities` | `fluid and vorticity wrappers` | **MISSING_VORTEXLAB_MODEL** | Add explicit background-field and Schwarz mutual-friction policies after the core unforced solver reaches parity. | **P2** |
| Bundle BEM | `solveDensePivot`, `bemKernelGradient`, `solveBundleNeumann`, `evalBundleBEMGradient` | `FieldKernels contains wire/dipole grid kernels only` | `field kernel wrappers` | **MISSING_OPTIONAL** | Create a separate BundleBoundarySolver only after P0/P1. Do not mix it into BiotSavart. | **P2** |
| Continuum fitting and Shapley orchestration | `fitContinuumSeries`, `counterfactual`, `shapley`, `evaluate`, `buildContinuumAudit` | `—` | `—` | **KEEP_IN_NODE_SERVICE** | Keep orchestration and report construction in TypeScript; call C++ only for canonical numerical kernels. | **TS** |
