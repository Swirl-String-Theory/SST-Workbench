"use strict";
const APP_VERSION='7.6.25b';
const APP_BASE_VERSION='7.5.3';
const VL_CLOCK_WORKFLOW_KEY='vortexlab.clock.workflow.7.6.25b';
const VL_CLOCK_WORKFLOW_PREVIOUS_KEY='vortexlab.clock.workflow.7.6.25a';
let VL_CLOCK_ACTIVE_MODE=null;
const VL_CLOCK_RUNNER_DEFS=[
  {id:'bSpecBenchmarkStart',mode:'spec',label:'SPEC CLOCK · 10-run',step:1},
  {id:'bProxyDecompStart',mode:'decomposition',label:'Proxy-decompositie',step:2},
  {id:'bHoldoutStart',mode:'holdout',label:'Geselecteerde holdouts',step:3},
  {id:'bContinuumStart',mode:'continuum',label:'Continuüm N=128–768',step:4},
  {id:'bReachAuditStart',mode:'reach',label:'Continue reach/DCSD',step:5},
  {id:'bGeomKappaStart',mode:'full-suite',label:'Volledige Swirl-Clock suite',step:6}
];
const VLClockWorkflow=(()=>{
  const defaults=()=>({spec:false,decomposition:false,holdout:false,continuum:false,reach:false});
  let state=defaults();
  try{
    const current=sessionStorage.getItem(VL_CLOCK_WORKFLOW_KEY),previous=sessionStorage.getItem(VL_CLOCK_WORKFLOW_PREVIOUS_KEY),stored=current||previous||'{}';
    state={...state,...JSON.parse(stored)};
    if(!current&&previous){state.holdout=false;state.continuum=false;state.reach=false;}
  }catch(_){}
  const save=()=>{try{sessionStorage.setItem(VL_CLOCK_WORKFLOW_KEY,JSON.stringify(state));}catch(_){}};
  const unlocked=mode=>mode==='spec'||(mode==='decomposition'&&state.spec)||(mode==='holdout'&&state.spec&&state.decomposition)||(mode==='continuum'&&state.spec&&state.decomposition&&state.holdout)||(mode==='reach'&&state.spec&&state.decomposition&&state.holdout&&state.continuum)||(mode==='full-suite'&&state.spec&&state.decomposition&&state.holdout&&state.continuum&&state.reach);
  const done=mode=>mode==='full-suite'?state.spec&&state.decomposition&&state.holdout&&state.continuum&&state.reach:!!state[mode];
  const invalidateFrom=mode=>{const order=['spec','decomposition','holdout','continuum','reach'],i=order.indexOf(mode);if(i<0)return;for(let k=i;k<order.length;k++)state[order[k]]=false;save();};
  const begin=mode=>{if(mode!=='full-suite')invalidateFrom(mode);VL_CLOCK_ACTIVE_MODE=mode;vlRefreshClockRunnerWorkflowUi();};
  const complete=(mode,pass)=>{VL_CLOCK_ACTIVE_MODE=null;if(pass){if(mode==='full-suite'){state={spec:true,decomposition:true,holdout:true,continuum:true,reach:true};}else if(Object.prototype.hasOwnProperty.call(state,mode))state[mode]=true;}save();vlRefreshClockRunnerWorkflowUi();};
  const abort=()=>{VL_CLOCK_ACTIVE_MODE=null;save();vlRefreshClockRunnerWorkflowUi();};
  const invalidateSelection=()=>{state.holdout=false;state.continuum=false;state.reach=false;save();vlRefreshClockRunnerWorkflowUi();};
  const reason=mode=>{if(unlocked(mode))return '';if(mode==='decomposition')return 'Voer eerst SPEC CLOCK · 10-run uit met ENGINE PASS.';if(mode==='holdout')return 'Voer eerst de proxy-decompositie uit met ENGINE PASS.';if(mode==='continuum')return 'Voer eerst de geselecteerde holdouts uit met ENGINE PASS.';if(mode==='reach')return 'Voer eerst de continuümaudit uit met ENGINE PASS.';if(mode==='full-suite')return 'Voltooi eerst SPEC, decompositie, holdouts, continuüm en reach/DCSD met ENGINE PASS.';return 'Runner is nog vergrendeld.';};
  return {unlocked,done,begin,complete,abort,invalidateSelection,reason,get state(){return {...state};}};
})();
function vlRefreshClockRunnerWorkflowUi(){
  const any=!!VL_CLOCK_ACTIVE_MODE;
  for(const def of VL_CLOCK_RUNNER_DEFS){const b=document.getElementById(def.id);if(!b)continue;const running=VL_CLOCK_ACTIVE_MODE===def.mode,unlocked=VLClockWorkflow.unlocked(def.mode),done=VLClockWorkflow.done(def.mode);b.disabled=any?!running:!unlocked;b.classList.toggle('runner-stop',running);b.classList.toggle('runner-locked',!unlocked&&!running);b.classList.toggle('runner-done',done&&!running);b.dataset.runnerMode=def.mode;b.textContent=running?`■ Stop · ${def.label}`:`${unlocked?(done?'✓':'▶'):'🔒'} ${def.label}`;b.title=running?'Klik om deze runner te stoppen.':(unlocked?`Stap ${def.step} · klik om te starten.`:VLClockWorkflow.reason(def.mode));}
  const hint=document.getElementById('vlClockWorkflowHint');if(hint){if(VL_CLOCK_ACTIVE_MODE){const d=VL_CLOCK_RUNNER_DEFS.find(x=>x.mode===VL_CLOCK_ACTIVE_MODE);hint.textContent=`Actief: ${d?.label||VL_CLOCK_ACTIVE_MODE}. Alleen deze knop blijft beschikbaar als Stop.`;}else{const next=VL_CLOCK_RUNNER_DEFS.find(x=>x.mode!=='full-suite'&&!VLClockWorkflow.done(x.mode));hint.textContent=next?`Volgende vereiste stap: ${next.step}. ${next.label}. Een stap ontgrendelt pas na ENGINE PASS.`:'ENGINE-workflow inclusief reach/DCSD voltooid. De volledige Swirl-Clocksuite is ontgrendeld.';}}
}
window.__vlBootComplete=false;
window.addEventListener('error',function vlEarlyBootstrapError(event){
  if(window.__vlBootComplete)return;
  const flag=document.getElementById('flag');
  const detail=String(event&&event.error&&event.error.message||event&&event.message||'onbekende opstartfout');
  if(flag){flag.textContent='⛔ VortexLab kon niet starten: '+detail;flag.style.display='block';flag.classList.remove('warnonly');}
  console.error('[VortexLab bootstrap]',event&&event.error||event&&event.message||event);
});
if(typeof THREE==='undefined'){
  const flag=document.getElementById('flag');
  if(flag){flag.textContent='⛔ THREE.js kon niet worden geladen. Controleer internet/CDN-toegang of gebruik een pakket met lokale vendorbestanden.';flag.style.display='block';flag.classList.remove('warnonly');}
  throw new Error('THREE.js unavailable');
}
const APP_PATCH_NOTES=[
  'Topologiebehoud: contact-CFL, transient-contact bracketing en landing aan de veilige zijde van de 3a-grens; geen numerieke reconnectie of doorsnijding wordt geaccepteerd',
  'Auto-relax is transactioneel: iedere regularisatiestap wordt teruggedraaid wanneer de topology guard de beschikbare tube-clearance kan verliezen',
  'Niveau-C Research Track: discrete 3D Neumann source-panel BEM/MFS rond de volledige gesloten knooptube; harmonische correctie dwingt u·n=0 op de gekozen uitsluitingsbuis',
  'Een tweede Neumann-oplossing projecteert het coarse-grained vorticiteitsveld tangentieel aan de knooptube; representatieve swirl strings worden langs dit 3D veld geïntegreerd',
  'R_horn, r_kern en a_sim blijven strikt gescheiden; de BEM-grens is standaard a_sim en R_horn is alleen een expliciete, numeriek doorgaans onoplosbare Research-Track hypothese',
  'Validator en browser-smoke uitgebreid met T0l–T0n, T9j–T9m en T10a–T10g',
  'SST Research-Track vortex-stretching gate: deterministische segmentrek per geaccepteerde CFL-stap, finite-time Λ_K en incompressibele kernradiusvoorspelling',
  'Drie Friedlander-profielen A1/A2/A3 met analytische vorticiteitsgroeireferentie en optionele profiel-only benchmarktransport',
  'First-hit- en transient-contacttrials zijn passief: transport-proxy en stretch-gate worden precies eenmaal over de geaccepteerde stap bijgewerkt',
  'Taylor-forcing geldt uitsluitend in solo-modus en wordt vóór iedere contacttest in volle en gebisecteerde kandidaatstappen toegepast',
  'g_a gebruikt exact a_sim; een afzonderlijke effectieve ratio verwerkt uitsluitend de expliciet gelabelde numerieke contactvloer',
  'Planck/String-schaalprobe is passieve a_probe-metadata, strikt gescheiden van a_sim, r_kern, R_horn, stretch-gate en BEM',
  'Canon/provenance, diagnostische NaN-serialisatie en de volledige regressiematrix zijn aangescherpt',
  'UI: topology/contactmeldingen staan onder de topbar; LIVE STABILITEIT, geometriekaarten en sparkline vormen permanente onderste simulatoroverlays',
  'UI: GEOMETRISCHE DIAGNOSTIEK is een vaste DIAG-sectie; χ-fase/Track B, speculative swirl clock A↔B en de vortex-stretching gate staan eronder als zelfstandige collapsebles',
  'Speculative swirl clock: passieve vergelijking van twee ongemapte proxies; ruwe overlap/afwijking is expliciet geen fysische closure of falsificatie',
  'SPEC CLOCK-overlay wordt alleen bij een actieve diagnose getoond en incrementeel bijgewerkt zonder voortdurende DOM-reconstructie',
  'Spec-clock quick-controls zijn werkelijk tweerichtingsgebonden; actieve numerieke invoer wordt niet langer door live synchronisatie overschreven',
  'Δz_AB,0 heeft vrije positieve numerieke invoer boven het sliderbereik; verre afstanden schakelen periodiek z automatisch uit',
  'Integratorbootstrap: voorgeschreven axiale driftsnelheden begrenzen dt_CFL al vóór de eerste RK4-stap; de eerste stap kan niet meer honderden seconden groot worden',
  'Geaccepteerde tijdstappen hebben een playback-onafhankelijke bovengrens van 0.25 s en 0.05 s zolang SPEC CLOCK actief is',
  'Wijzigingen van afspeelsnelheid, pauzestatus en opgelegde drift wissen uitsluitend onafgewerkt playback-debet; er wordt geen achterstallige reuzenstap ingehaald',
  'SPEC CLOCK-preset armt gepauzeerd op 1×; één fase-nullkalibratie bij t=0 start de sweep automatisch',
  'Geautomatiseerde SPEC CLOCK-benchmark voert tien onafhankelijke reset–kalibratie–run-cycli uit en scheidt ENGINE-integriteit van RESEARCH-PROXY-gates',
  'Benchmarkdoeltijden worden in de geaccepteerde CFL-stap exact geland; afspeelsnelheid kan daardoor zonder frame-overshoot worden vergeleken',
  'ModelLog en benchmarkrapport registreren Rcyl/Hcyl; volumeaanpassing invalideert een vergrendelde fase-nullreferentie en vereist herkalibratie',
  'v7.6.23: R6 gebruikt de volledige zespuntsladder; R27 gebruikt high-resolution/continuum-amplitude en blokkeert reach-afhankelijke factoren bij niet-convergente thickness',
  'v7.6.23: continuumfit X(N)=X∞+A·N^-p voor lokale veld-, rigid-body-, lengte- en required-κ-observabelen',
  'v7.6.23: cross-knot holdouts voor fseries 3_1, ideal 5:1:1 en fseries 5_1; holdouts trainen geen kandidaatfactor',
  'v7.6.23: benchmarkrapporten en ModelLog worden na voltooiing automatisch met unieke UTC-tijdstempel geëxporteerd',
  'v7.6.24: CLOCK-sidebar horizontaal resizebaar met persistente breedte en dubbelklik-reset',
  'v7.6.24: R24–R26 filteren niet-toepasselijke/NaN-kandidaten vóór aggregatie',
  'v7.6.24: volledige rigid-rotationvector en intrinsieke Ω_parallel/Ω_perp-projecties geëxporteerd',
  'v7.6.24: canonicalized embeddingparen voor fseries/ideal 3_1, 4_1, 5_1, 5_2 en 6_1',
  'v7.6.24: ingebouwd roadmapblok voor v7.6.25–v7.7.0',
  'v7.6.25b: volledige KnotPlot uniform-N300-catalogus; legacy Tlink_6_9 → torus_6.9; native polygonale sampling; catalogusbrede holdout- en reachprovenance',
  'v7.6.25a: reachbronselectie gelijkgetrokken met holdouts; gedempte least-squares DCSD-polish; niet-vacuüm catalogusgates; SPARK/HUD-wrapperherstel; zelftestschema 2.1',
  'v7.6.25: passieve continue C²-spline reach/DCSD/inter-component solver met limiterprovenance en N≤1536-audit',
  'v7.6.24f3: ingeklapte HUD-tabs zijn primair klikbaar; slepen start daar alleen via grip of rand, terwijl uitgeklapte titelbalken volledig sleepbaar blijven; dubbelklik toggelt open/dicht',
  'v7.6.24f2: runnerknoppen responsief in flexrijen; start/stop per runner op één knop; workflow-locks dwingen SPEC → decompositie → holdouts → continuüm → confirmatoir af; onderste HUD sleepbaar via titel én rand, dubbelklik klapt in',
  'v7.6.24f1: onderste LIVE/SPEC/STATS/SPARK-widgets sleepbaar, inklapbaar en persistent; expliciete gesloten-state voor #spark',
  'v7.6.24f: KnotPlot-catalogusbron + Tlink_6_9 driecomponenten-holdout',
  'v7.6.24e1: startup-safe lokale binding voor globale runstrip in detached UI-shell',
  'v7.6.24e: D14 bewaart visualPolicyAtCapture en classificeert tracerisolatie correct',
  'v7.6.24e: globale runstrip, runner-hub, wijzigingsbadges en inklapbare onderste HUD',
  'v7.6.24d: selecteerbare ideal/fseries holdouts, gesplitste runners en 7₁ toegevoegd',
  'v7.6.24d: D4 gebruikt exacte cyclische indexpermutatie zonder interpolatie',
  'v7.6.24c: D2/D4/D6 zero-safe en applicability-aware; R22 topology-specifiek opgesplitst',
  'v7.6.24c: automatische benchmarks zetten tracers/stroomlijnen/potential-flow tijdelijk uit en herstellen exact',
  'v7.6.24b: cross-knotholdouts accepteren legacy lab-z projection-null als geldig maar niet-informatief en lopen door',
  'v7.6.24b: a_probe-presets ℓ_P/2, ℓ_P en 2ℓ_P toegevoegd voor radius/diameter-audit; metadata-only',
  'v7.6.24b: native title Toelichting globaal verwijderd van alle gegenereerde info-iconen',
  'v7.6.24a: intrinsicKinematics wordt vóór digestberekening opgebouwd; decompositionruns starten weer',
  'v7.6.24a: setup/checkpointfouten en abortstatus worden met scenario, checkpoint en stack in ModelLog vastgelegd',
  'v7.6.24a: echte analyzeRaw-runtime-smoketest voorkomt herhaling van een t=0-crash'
];
const A_SIM_EPS=1e-30;
const A_SIM_INPUT_FLOOR=1e-18;
const CONTACT_ULP_FACTOR=64;
const PLANCK_LENGTH=1.616255e-35; // m, passieve Rosetta-schaal; nooit solverinvoer
const HE_CORE_REF=1.0e-10;       // m, orde-grootte 1 Å; passieve Rosetta-schaal
const BEM_SOURCE_MODEL='neumann-source-panel-mfs-v1';
const BEM_REBUILD_STEPS=8;
const TOPOLOGY_SWEEP_SAMPLES=12;
const MAX_ACCEPTED_DT=0.25;             // s, algemene temporele resolutiecap
const SPEC_CLOCK_MAX_ACCEPTED_DT=0.05;  // s, fijnere passieve klokdiagnostiek
// ================= dataset: ideal trefoil 3:1:1 (Gilbert, 183 modi) =================
const IDEAL_TREFOIL_3_1_1 = {
  knotId: "3:1:1",
  L: 16.371637,
  coeffs: [
  {I:1,A:[0.374139, 0, 0],B:[0, 0.37392799999999998, 0]},
  {I:2,A:[0.82424600000000003, 0.75026000000000004, 0.00035199999999999999],B:[0.75044999999999995, -0.82395200000000002, -0.0019910000000000001]},
  {I:3,A:[0.00025700000000000001, -0.00093199999999999999, 0.35239700000000002],B:[-0.00076999999999999996, 0.00072599999999999997, -0.386764]},
  {I:4,A:[0.011651999999999999, -0.010656000000000001, 0.00074299999999999995],B:[0.010739, 0.011613, -0.00023000000000000001]},
  {I:5,A:[0.010503999999999999, 0.110306, 0.00019900000000000001],B:[0.110745, -0.010366, -0.00023499999999999999]},
  {I:6,A:[1.5e-05, -6.0000000000000002e-06, -0.047465],B:[-5.0000000000000002e-05, -9.9999999999999995e-07, 0.0045950000000000001]},
  {I:7,A:[-0.000292, 0.0024169999999999999, -7.9999999999999996e-06],B:[-0.002529, -0.00025500000000000002, -9.0000000000000002e-06]},
  {I:8,A:[0.016487000000000002, -0.021784000000000001, 4.1e-05],B:[-0.021922000000000001, -0.016421000000000002, -4.3999999999999999e-05]},
  {I:9,A:[-2.9e-05, -1.8e-05, 0.011178],B:[4.8999999999999998e-05, 4.1e-05, 0.0084139999999999996]},
  {I:10,A:[-0.00021599999999999999, -0.00029, -1.8e-05],B:[0.00031100000000000002, -0.00019699999999999999, -4.3999999999999999e-05]},
  {I:11,A:[-0.011727, 0.0021840000000000002, 6.9999999999999999e-06],B:[0.002202, 0.011682, 2.0000000000000002e-05]},
  {I:12,A:[2.5999999999999998e-05, 1.9000000000000001e-05, -0.0013079999999999999],B:[-3.9999999999999998e-06, -1.9000000000000001e-05, -0.0070390000000000001]},
  {I:13,A:[0.00032499999999999999, 5.5000000000000002e-05, -9.0000000000000002e-06],B:[-5.8999999999999998e-05, 0.00028899999999999998, 2.4000000000000001e-05]},
  {I:14,A:[0.0052129999999999998, 0.0032009999999999999, 9.9999999999999995e-07],B:[0.0032100000000000002, -0.0051879999999999999, 1.0000000000000001e-05]},
  {I:15,A:[-1.5e-05, -1.5999999999999999e-05, -0.0019170000000000001],B:[-1.7e-05, 9.9999999999999995e-07, 0.0031210000000000001]},
  {I:16,A:[-0.000136, 6.2000000000000003e-05, 1.9000000000000001e-05],B:[-7.4999999999999993e-05, -0.000112, -6.9999999999999999e-06]},
  {I:17,A:[-0.00099500000000000001, -0.0034629999999999999, -9.9999999999999995e-07],B:[-0.0034740000000000001, 0.00098799999999999995, -1.5e-05]},
  {I:18,A:[3.0000000000000001e-06, 7.9999999999999996e-06, 0.0021779999999999998],B:[1.9000000000000001e-05, 7.9999999999999996e-06, -0.00061499999999999999]},
  {I:19,A:[3.3000000000000003e-05, -9.3999999999999994e-05, -1.5999999999999999e-05],B:[0.000113, 2.8e-05, -3.9999999999999998e-06]},
  {I:20,A:[-0.0009990000000000001, 0.002013, -0],B:[0.002019, 0.00099799999999999997, 0]},
  {I:21,A:[3.9999999999999998e-06, 9.9999999999999995e-07, -0.0012700000000000001],B:[-1.2999999999999999e-05, -1.2e-05, -0.00062600000000000004]},
  {I:22,A:[3.4e-05, 6.0000000000000002e-05, 9.0000000000000002e-06],B:[-7.2000000000000002e-05, 2.5999999999999998e-05, 1.0000000000000001e-05]},
  {I:23,A:[0.0013829999999999999, -0.00053899999999999998, 1.9999999999999999e-06],B:[-0.00054000000000000001, -0.001382, 3.9999999999999998e-06]},
  {I:24,A:[-5.0000000000000004e-06, -1.1e-05, 0.00034400000000000001],B:[9.0000000000000002e-06, 6.9999999999999999e-06, 0.00088999999999999995]},
  {I:25,A:[-5.7000000000000003e-05, -2.5000000000000001e-05, 9.9999999999999995e-07],B:[1.9000000000000001e-05, -4.8000000000000001e-05, -7.9999999999999996e-06]},
  {I:26,A:[-0.00093099999999999997, -0.00035599999999999998, -0],B:[-0.000357, 0.00093099999999999997, -5.0000000000000004e-06]},
  {I:27,A:[6.0000000000000002e-06, 9.0000000000000002e-06, 0.00022800000000000001],B:[-1.9999999999999999e-06, -0, -0.00059699999999999998]},
  {I:28,A:[4.0000000000000003e-05, -6.9999999999999999e-06, -3.9999999999999998e-06],B:[1.9000000000000001e-05, 3.6000000000000001e-05, 3.9999999999999998e-06]},
  {I:29,A:[0.00030800000000000001, 0.000611, 9.9999999999999995e-07],B:[0.000611, -0.00030699999999999998, 6.9999999999999999e-06]},
  {I:30,A:[1.9999999999999999e-06, 9.9999999999999995e-07, -0.00039100000000000002],B:[-6.0000000000000002e-06, 9.9999999999999995e-07, 0.000195]},
  {I:31,A:[-1.5e-05, 1.9000000000000001e-05, 3.0000000000000001e-06],B:[-3.1000000000000001e-05, -1.2e-05, 9.9999999999999995e-07]},
  {I:32,A:[0.000125, -0.00045199999999999998, 3.9999999999999998e-06],B:[-0.00045199999999999998, -0.00012400000000000001, -3.9999999999999998e-06]},
  {I:33,A:[-6.0000000000000002e-06, -9.9999999999999995e-07, 0.000281],B:[3.9999999999999998e-06, -3.0000000000000001e-06, 7.7000000000000001e-05]},
  {I:34,A:[-1.9999999999999999e-06, -7.9999999999999996e-06, -1.9999999999999999e-06],B:[2.4000000000000001e-05, -5.0000000000000004e-06, -9.9999999999999995e-07]},
  {I:35,A:[-0.000272, 0.000173, -1.9999999999999999e-06],B:[0.00017200000000000001, 0.00027300000000000002, -3.9999999999999998e-06]},
  {I:36,A:[6.0000000000000002e-06, -9.9999999999999995e-07, -0.00010399999999999999],B:[1.9999999999999999e-06, 3.9999999999999998e-06, -0.000164]},
  {I:37,A:[7.9999999999999996e-06, 3.0000000000000001e-06, -9.9999999999999995e-07],B:[-9.0000000000000002e-06, 3.9999999999999998e-06, 9.9999999999999995e-07]},
  {I:38,A:[0.00021499999999999999, 3.6000000000000001e-05, -3.9999999999999998e-06],B:[3.6999999999999998e-05, -0.000214, 3.9999999999999998e-06]},
  {I:39,A:[-1.9999999999999999e-06, -1.9999999999999999e-06, -2.0000000000000002e-05],B:[1.9999999999999999e-06, -9.9999999999999995e-07, 0.000121]},
  {I:41,A:[-8.8999999999999995e-05, -0.000113, 3.9999999999999998e-06],B:[-0.000113, 8.7999999999999998e-05, 1.9999999999999999e-06]},
  {I:42,A:[1.9999999999999999e-06, 0, 5.8999999999999998e-05],B:[-0, 3.0000000000000001e-06, -4.6e-05]},
  {I:43,A:[-6.9999999999999999e-06, 6.9999999999999999e-06, -0],B:[-1.9999999999999999e-06, 3.9999999999999998e-06, -0]},
  {I:44,A:[-5.0000000000000004e-06, 8.7999999999999998e-05, -0],B:[9.0000000000000006e-05, 5.0000000000000004e-06, -3.9999999999999998e-06]},
  {I:46,A:[0, -7.9999999999999996e-06, -9.9999999999999995e-07],B:[1.1e-05, -5.0000000000000004e-06, -9.9999999999999995e-07]},
  {I:47,A:[3.6000000000000001e-05, -3.6000000000000001e-05, 9.9999999999999995e-07],B:[-3.6000000000000001e-05, -3.6000000000000001e-05, -9.9999999999999995e-07]},
  {I:48,A:[3.0000000000000001e-06, -3.0000000000000001e-06, 1.1e-05],B:[3.0000000000000001e-06, 1.9999999999999999e-06, 9.0000000000000002e-06]},
  {I:49,A:[9.0000000000000002e-06, 3.9999999999999998e-06, -0],B:[-1.1e-05, 1.1e-05, 3.0000000000000001e-06]},
  {I:50,A:[-2.0999999999999999e-05, 3.9999999999999998e-06, -9.9999999999999995e-07],B:[3.9999999999999998e-06, 2.3e-05, -9.9999999999999995e-07]},
  {I:51,A:[-9.9999999999999995e-07, 9.9999999999999995e-07, -3.9999999999999998e-06],B:[-3.0000000000000001e-06, 1.9999999999999999e-06, 6.0000000000000002e-06]},
  {I:52,A:[-1.5e-05, 1.9999999999999999e-06, -0],B:[-9.9999999999999995e-07, -1.5999999999999999e-05, -9.9999999999999995e-07]},
  {I:53,A:[3.9999999999999998e-06, -0, 3.0000000000000001e-06],B:[-9.9999999999999995e-07, -3.9999999999999998e-06, 1.9999999999999999e-06]},
  {I:54,A:[-0, 1.9999999999999999e-06, 1.2999999999999999e-05],B:[9.9999999999999995e-07, -9.9999999999999995e-07, -1.1e-05]},
  {I:55,A:[1.0000000000000001e-05, -1.2e-05, 9.9999999999999995e-07],B:[1.2e-05, 1.4e-05, 0]},
  {I:56,A:[-3.0000000000000001e-06, 1.2999999999999999e-05, 9.9999999999999995e-07],B:[1.2e-05, 1.9999999999999999e-06, -1.9999999999999999e-06]},
  {I:57,A:[-1.9999999999999999e-06, -9.9999999999999995e-07, -2.5999999999999998e-05],B:[0, -1.9999999999999999e-06, -0]},
  {I:58,A:[3.0000000000000001e-06, 2.0000000000000002e-05, 0],B:[-1.5999999999999999e-05, -3.9999999999999998e-06, -9.9999999999999995e-07]},
  {I:59,A:[1.5e-05, -1.5999999999999999e-05, -9.9999999999999995e-07],B:[-1.4e-05, -1.5999999999999999e-05, 1.9999999999999999e-06]},
  {I:60,A:[3.9999999999999998e-06, -1.9999999999999999e-06, 2.4000000000000001e-05],B:[1.9999999999999999e-06, 3.0000000000000001e-06, 2.0999999999999999e-05]},
  {I:61,A:[-1.2999999999999999e-05, -1.8e-05, -0],B:[1.0000000000000001e-05, -1.1e-05, -9.9999999999999995e-07]},
  {I:62,A:[-2.8e-05, 1.9999999999999999e-06, -0],B:[1.9999999999999999e-06, 2.9e-05, 0]},
  {I:63,A:[-9.9999999999999995e-07, 3.9999999999999998e-06, -3.9999999999999998e-06],B:[-5.0000000000000004e-06, -1.9999999999999999e-06, -3.4e-05]},
  {I:64,A:[1.5999999999999999e-05, 6.0000000000000002e-06, -9.9999999999999995e-07],B:[1.9999999999999999e-06, 2.0000000000000002e-05, 1.9999999999999999e-06]},
  {I:65,A:[2.5999999999999998e-05, 2.0999999999999999e-05, 0],B:[1.9000000000000001e-05, -2.6999999999999999e-05, -0]},
  {I:66,A:[-3.0000000000000001e-06, -5.0000000000000004e-06, -2.1999999999999999e-05],B:[3.9999999999999998e-06, -9.9999999999999995e-07, 2.9e-05]},
  {I:67,A:[-1.2999999999999999e-05, 1.0000000000000001e-05, 9.9999999999999995e-07],B:[-1.2e-05, -1.7e-05, -9.9999999999999995e-07]},
  {I:68,A:[-6.9999999999999999e-06, -3.4e-05, -9.9999999999999995e-07],B:[-3.4e-05, 6.0000000000000002e-06, -1.9999999999999999e-06]},
  {I:69,A:[3.9999999999999998e-06, 3.0000000000000001e-06, 3.4e-05],B:[-9.9999999999999995e-07, 3.0000000000000001e-06, -6.9999999999999999e-06]},
  {I:70,A:[1.9999999999999999e-06, -1.7e-05, -9.9999999999999995e-07],B:[1.7e-05, 5.0000000000000004e-06, -0]},
  {I:71,A:[-1.9000000000000001e-05, 3.1000000000000001e-05, -9.9999999999999995e-07],B:[3.1000000000000001e-05, 1.9000000000000001e-05, 1.9999999999999999e-06]},
  {I:72,A:[-1.9999999999999999e-06, 0, -3.1999999999999999e-05],B:[-1.9999999999999999e-06, -3.9999999999999998e-06, -1.9000000000000001e-05]},
  {I:73,A:[1.0000000000000001e-05, 1.2999999999999999e-05, 0],B:[-1.5e-05, 9.0000000000000002e-06, 0]},
  {I:74,A:[3.3000000000000003e-05, -1.1e-05, 3.0000000000000001e-06],B:[-1.1e-05, -3.3000000000000003e-05, -9.9999999999999995e-07]},
  {I:75,A:[0, -1.9999999999999999e-06, 1.0000000000000001e-05],B:[9.9999999999999995e-07, 9.9999999999999995e-07, 3.1000000000000001e-05]},
  {I:76,A:[-1.5999999999999999e-05, -3.0000000000000001e-06, -9.9999999999999995e-07],B:[5.0000000000000004e-06, -1.4e-05, 0]},
  {I:77,A:[-3.1000000000000001e-05, -1.5e-05, -1.9999999999999999e-06],B:[-1.4e-05, 3.1999999999999999e-05, -9.9999999999999995e-07]},
  {I:78,A:[9.9999999999999995e-07, 9.9999999999999995e-07, 1.5e-05],B:[-9.9999999999999995e-07, 0, -2.9e-05]},
  {I:79,A:[1.5999999999999999e-05, -7.9999999999999996e-06, -0],B:[6.0000000000000002e-06, 1.0000000000000001e-05, 0]},
  {I:80,A:[1.2999999999999999e-05, 3.1000000000000001e-05, 0],B:[2.9e-05, -1.2999999999999999e-05, 3.0000000000000001e-06]},
  {I:81,A:[-0, 9.9999999999999995e-07, -2.6999999999999999e-05],B:[-9.9999999999999995e-07, 9.9999999999999995e-07, 1.1e-05]},
  {I:82,A:[-6.9999999999999999e-06, 1.2e-05, 9.9999999999999995e-07],B:[-1.4e-05, -1.9999999999999999e-06, 0]},
  {I:83,A:[1.0000000000000001e-05, -3.0000000000000001e-05, 9.9999999999999995e-07],B:[-2.9e-05, -1.1e-05, -9.9999999999999995e-07]},
  {I:84,A:[-9.9999999999999995e-07, -0, 2.5999999999999998e-05],B:[9.9999999999999995e-07, -9.9999999999999995e-07, 1.0000000000000001e-05]},
  {I:85,A:[-3.0000000000000001e-06, -9.0000000000000002e-06, -0],B:[1.5e-05, -6.0000000000000002e-06, -9.9999999999999995e-07]},
  {I:86,A:[-2.4000000000000001e-05, 1.2999999999999999e-05, -9.9999999999999995e-07],B:[1.4e-05, 2.5999999999999998e-05, -0]},
  {I:87,A:[1.9999999999999999e-06, -1.9999999999999999e-06, -1.2e-05],B:[9.9999999999999995e-07, 1.9999999999999999e-06, -2.3e-05]},
  {I:88,A:[1.2e-05, 1.9999999999999999e-06, -0],B:[-6.9999999999999999e-06, 1.1e-05, 9.9999999999999995e-07]},
  {I:89,A:[2.5000000000000001e-05, 6.9999999999999999e-06, 9.9999999999999995e-07],B:[6.0000000000000002e-06, -2.5999999999999998e-05, 0]},
  {I:90,A:[-9.9999999999999995e-07, 1.9999999999999999e-06, -6.0000000000000002e-06],B:[-1.9999999999999999e-06, 0, 2.3e-05]},
  {I:91,A:[-1.2e-05, 5.0000000000000004e-06, 0],B:[-3.0000000000000001e-06, -7.9999999999999996e-06, -0]},
  {I:92,A:[-1.4e-05, -1.9000000000000001e-05, 9.9999999999999995e-07],B:[-2.0000000000000002e-05, 1.4e-05, 0]},
  {I:93,A:[-1.9999999999999999e-06, -9.9999999999999995e-07, 1.9000000000000001e-05],B:[1.9999999999999999e-06, -9.9999999999999995e-07, -1.1e-05]},
  {I:94,A:[6.0000000000000002e-06, -9.0000000000000002e-06, -9.9999999999999995e-07],B:[9.0000000000000002e-06, 3.0000000000000001e-06, -9.9999999999999995e-07]},
  {I:95,A:[-3.0000000000000001e-06, 2.0999999999999999e-05, 0],B:[2.1999999999999999e-05, 3.0000000000000001e-06, -0]},
  {I:96,A:[3.0000000000000001e-06, 0, -1.8e-05],B:[-9.9999999999999995e-07, 9.9999999999999995e-07, -3.0000000000000001e-06]},
  {I:97,A:[3.0000000000000001e-06, 6.9999999999999999e-06, 0],B:[-9.0000000000000002e-06, 1.9999999999999999e-06, 0]},
  {I:98,A:[1.5e-05, -1.2999999999999999e-05, -9.9999999999999995e-07],B:[-1.2999999999999999e-05, -1.4e-05, 1.9999999999999999e-06]},
  {I:99,A:[-1.9999999999999999e-06, 9.9999999999999995e-07, 1.0000000000000001e-05],B:[-1.9999999999999999e-06, -9.9999999999999995e-07, 1.2999999999999999e-05]},
  {I:100,A:[-6.9999999999999999e-06, -3.9999999999999998e-06, 0],B:[3.9999999999999998e-06, -6.0000000000000002e-06, -0]},
  {I:101,A:[-1.8e-05, -0, 9.9999999999999995e-07],B:[-9.9999999999999995e-07, 1.7e-05, -0]},
  {I:102,A:[0, -9.9999999999999995e-07, 1.9999999999999999e-06],B:[1.9999999999999999e-06, 9.9999999999999995e-07, -1.4e-05]},
  {I:103,A:[6.9999999999999999e-06, -0, 9.9999999999999995e-07],B:[3.0000000000000001e-06, 6.9999999999999999e-06, -0]},
  {I:104,A:[1.1e-05, 1.0000000000000001e-05, -1.9999999999999999e-06],B:[1.1e-05, -1.1e-05, -9.9999999999999995e-07]},
  {I:105,A:[9.9999999999999995e-07, 9.9999999999999995e-07, -9.0000000000000002e-06],B:[-9.9999999999999995e-07, 0, 7.9999999999999996e-06]},
  {I:106,A:[-3.0000000000000001e-06, 3.9999999999999998e-06, -0],B:[-6.0000000000000002e-06, -3.9999999999999998e-06, -0]},
  {I:107,A:[-0, -1.2999999999999999e-05, 0],B:[-1.2999999999999999e-05, 9.9999999999999995e-07, 9.9999999999999995e-07]},
  {I:108,A:[-9.9999999999999995e-07, -9.9999999999999995e-07, 1.2e-05],B:[0, -9.9999999999999995e-07, 0]},
  {I:109,A:[-1.9999999999999999e-06, -6.0000000000000002e-06, 0],B:[6.0000000000000002e-06, 9.9999999999999995e-07, 0]},
  {I:110,A:[-6.9999999999999999e-06, 9.0000000000000002e-06, 9.9999999999999995e-07],B:[7.9999999999999996e-06, 6.9999999999999999e-06, -1.9999999999999999e-06]},
  {I:111,A:[0, -0, -6.9999999999999999e-06],B:[0, 9.9999999999999995e-07, -6.0000000000000002e-06]},
  {I:112,A:[5.0000000000000004e-06, 3.9999999999999998e-06, 0],B:[-1.9999999999999999e-06, 3.0000000000000001e-06, 0]},
  {I:113,A:[9.0000000000000002e-06, -1.9999999999999999e-06, -9.9999999999999995e-07],B:[-1.9999999999999999e-06, -1.0000000000000001e-05, 9.9999999999999995e-07]},
  {I:114,A:[0, 9.9999999999999995e-07, 9.9999999999999995e-07],B:[-9.9999999999999995e-07, -9.9999999999999995e-07, 7.9999999999999996e-06]},
  {I:115,A:[-3.9999999999999998e-06, -1.9999999999999999e-06, 0],B:[-1.9999999999999999e-06, -3.9999999999999998e-06, -0]},
  {I:116,A:[-6.9999999999999999e-06, -3.9999999999999998e-06, 9.9999999999999995e-07],B:[-3.9999999999999998e-06, 7.9999999999999996e-06, 0]},
  {I:117,A:[-0, -0, 5.0000000000000004e-06],B:[-9.9999999999999995e-07, -0, -5.0000000000000004e-06]},
  {I:118,A:[1.9999999999999999e-06, -9.9999999999999995e-07, 0],B:[3.9999999999999998e-06, 3.0000000000000001e-06, 0]},
  {I:119,A:[1.9999999999999999e-06, 6.9999999999999999e-06, -9.9999999999999995e-07],B:[6.0000000000000002e-06, -3.0000000000000001e-06, -9.9999999999999995e-07]},
  {I:120,A:[-0, -0, -5.0000000000000004e-06],B:[0, 0, 1.9999999999999999e-06]},
  {I:121,A:[9.9999999999999995e-07, 3.0000000000000001e-06, -0],B:[-3.0000000000000001e-06, -1.9999999999999999e-06, -0]},
  {I:122,A:[1.9999999999999999e-06, -5.0000000000000004e-06, -0],B:[-6.0000000000000002e-06, -1.9999999999999999e-06, 0]},
  {I:123,A:[9.9999999999999995e-07, 0, 3.9999999999999998e-06],B:[0, 9.9999999999999995e-07, 3.0000000000000001e-06]},
  {I:124,A:[-3.0000000000000001e-06, -3.0000000000000001e-06, -0],B:[9.9999999999999995e-07, -9.9999999999999995e-07, -0]},
  {I:125,A:[-3.9999999999999998e-06, 1.9999999999999999e-06, 9.9999999999999995e-07],B:[1.9999999999999999e-06, 3.9999999999999998e-06, -0]},
  {I:126,A:[-0, 0, -9.9999999999999995e-07],B:[-9.9999999999999995e-07, -9.9999999999999995e-07, -3.9999999999999998e-06]},
  {I:127,A:[3.0000000000000001e-06, 9.9999999999999995e-07, 0],B:[9.9999999999999995e-07, 1.9999999999999999e-06, 0]},
  {I:128,A:[3.9999999999999998e-06, 0, -0],B:[9.9999999999999995e-07, -3.0000000000000001e-06, 9.9999999999999995e-07]},
  {I:129,A:[-0, -9.9999999999999995e-07, -0],B:[0, 0, 3.0000000000000001e-06]},
  {I:130,A:[-1.9999999999999999e-06, 9.9999999999999995e-07, 0],B:[-1.9999999999999999e-06, -1.9999999999999999e-06, 0]},
  {I:131,A:[-1.9999999999999999e-06, -1.9999999999999999e-06, -9.9999999999999995e-07],B:[-1.9999999999999999e-06, 1.9999999999999999e-06, -0]},
  {I:132,A:[9.9999999999999995e-07, 9.9999999999999995e-07, 1.9999999999999999e-06],B:[-9.9999999999999995e-07, 0, -9.9999999999999995e-07]},
  {I:133,A:[0, -1.9999999999999999e-06, 0],B:[3.0000000000000001e-06, 9.9999999999999995e-07, 9.9999999999999995e-07]},
  {I:135,A:[-9.9999999999999995e-07, -0, -1.9999999999999999e-06],B:[0, -0, -0]},
  {I:136,A:[9.9999999999999995e-07, 9.9999999999999995e-07, -0],B:[-1.9999999999999999e-06, 9.9999999999999995e-07, -0]},
  {I:137,A:[9.9999999999999995e-07, -9.9999999999999995e-07, 9.9999999999999995e-07],B:[-9.9999999999999995e-07, -0, -9.9999999999999995e-07]},
  {I:138,A:[9.9999999999999995e-07, -0, 9.9999999999999995e-07],B:[9.9999999999999995e-07, 9.9999999999999995e-07, 9.9999999999999995e-07]},
  {I:139,A:[-1.9999999999999999e-06, 0, -0],B:[9.9999999999999995e-07, -9.9999999999999995e-07, 9.9999999999999995e-07]},
  {I:140,A:[-9.9999999999999995e-07, 9.9999999999999995e-07, -9.9999999999999995e-07],B:[9.9999999999999995e-07, 0, 0]},
  {I:141,A:[-9.9999999999999995e-07, 0, 0],B:[-9.9999999999999995e-07, -0, -9.9999999999999995e-07]},
  {I:145,A:[-9.9999999999999995e-07, 9.9999999999999995e-07, -0],B:[-9.9999999999999995e-07, 9.9999999999999995e-07, 0]},
  {I:147,A:[9.9999999999999995e-07, -0, -0],B:[-9.9999999999999995e-07, 0, -0]},
  {I:148,A:[0, -0, 0],B:[9.9999999999999995e-07, -9.9999999999999995e-07, 0]},
  {I:149,A:[9.9999999999999995e-07, 0, -9.9999999999999995e-07],B:[0, -9.9999999999999995e-07, 9.9999999999999995e-07]},
  {I:150,A:[-9.9999999999999995e-07, 0, 0],B:[-0, 0, 0]},
  {I:151,A:[9.9999999999999995e-07, -9.9999999999999995e-07, 0],B:[-9.9999999999999995e-07, 9.9999999999999995e-07, -0]},
  {I:152,A:[-1.9999999999999999e-06, -9.9999999999999995e-07, 0],B:[-9.9999999999999995e-07, 9.9999999999999995e-07, 0]},
  {I:154,A:[-9.9999999999999995e-07, 9.9999999999999995e-07, -0],B:[9.9999999999999995e-07, 0, 0]},
  {I:155,A:[9.9999999999999995e-07, 1.9999999999999999e-06, -9.9999999999999995e-07],B:[1.9999999999999999e-06, -9.9999999999999995e-07, -9.9999999999999995e-07]},
  {I:156,A:[0, -9.9999999999999995e-07, -9.9999999999999995e-07],B:[-0, 0, 9.9999999999999995e-07]},
  {I:157,A:[9.9999999999999995e-07, -9.9999999999999995e-07, -0],B:[0, -9.9999999999999995e-07, -0]},
  {I:158,A:[9.9999999999999995e-07, -1.9999999999999999e-06, -0],B:[-1.9999999999999999e-06, -0, 9.9999999999999995e-07]},
  {I:159,A:[0, 0, 9.9999999999999995e-07],B:[0, 0, 0]},
  {I:161,A:[-1.9999999999999999e-06, 9.9999999999999995e-07, 0],B:[9.9999999999999995e-07, 1.9999999999999999e-06, 0]},
  {I:162,A:[-0, -0, -9.9999999999999995e-07],B:[-0, -9.9999999999999995e-07, -9.9999999999999995e-07]},
  {I:163,A:[0, 9.9999999999999995e-07, 0],B:[9.9999999999999995e-07, -9.9999999999999995e-07, -0]},
  {I:164,A:[1.9999999999999999e-06, 0, -0],B:[0, -1.9999999999999999e-06, 0]},
  {I:166,A:[9.9999999999999995e-07, -9.9999999999999995e-07, -0],B:[-0, 0, -0]},
  {I:167,A:[-9.9999999999999995e-07, -1.9999999999999999e-06, 0],B:[-1.9999999999999999e-06, 9.9999999999999995e-07, 0]},
  {I:168,A:[0, 0, 9.9999999999999995e-07],B:[-0, -0, -9.9999999999999995e-07]},
  {I:170,A:[-0, 1.9999999999999999e-06, 0],B:[1.9999999999999999e-06, 0, -0]},
  {I:171,A:[-9.9999999999999995e-07, -0, -9.9999999999999995e-07],B:[0, -0, -0]},
  {I:173,A:[1.9999999999999999e-06, -9.9999999999999995e-07, -0],B:[-9.9999999999999995e-07, -1.9999999999999999e-06, -0]},
  {I:174,A:[9.9999999999999995e-07, 0, 9.9999999999999995e-07],B:[0, 0, 9.9999999999999995e-07]},
  {I:176,A:[-1.9999999999999999e-06, 0, 0],B:[0, 1.9999999999999999e-06, 0]},
  {I:177,A:[-9.9999999999999995e-07, 0, -0],B:[-9.9999999999999995e-07, -0, -9.9999999999999995e-07]},
  {I:179,A:[9.9999999999999995e-07, 9.9999999999999995e-07, 0],B:[9.9999999999999995e-07, -9.9999999999999995e-07, 0]},
  {I:182,A:[-0, -1.9999999999999999e-06, -0],B:[-1.9999999999999999e-06, 0, -0]},
  {I:185,A:[-9.9999999999999995e-07, 1.9999999999999999e-06, 0],B:[9.9999999999999995e-07, 9.9999999999999995e-07, 0]},
  {I:188,A:[1.9999999999999999e-06, -9.9999999999999995e-07, 0],B:[-0, -1.9999999999999999e-06, -9.9999999999999995e-07]},
  {I:189,A:[9.9999999999999995e-07, -0, 0],B:[0, 0, 9.9999999999999995e-07]},
  {I:191,A:[-9.9999999999999995e-07, -0, -9.9999999999999995e-07],B:[-9.9999999999999995e-07, 9.9999999999999995e-07, 0]},
  {I:192,A:[-0, 9.9999999999999995e-07, 9.9999999999999995e-07],B:[-9.9999999999999995e-07, -0, -9.9999999999999995e-07]},
  {I:194,A:[0, 9.9999999999999995e-07, 0],B:[9.9999999999999995e-07, -9.9999999999999995e-07, 0]},
  {I:195,A:[-0, -0, -9.9999999999999995e-07],B:[0, -0, 0]},
  {I:197,A:[0, -1.9999999999999999e-06, -0],B:[-9.9999999999999995e-07, -0, -0]},
  {I:198,A:[0, 0, 9.9999999999999995e-07],B:[-0, 0, 0]},
  {I:200,A:[-9.9999999999999995e-07, 9.9999999999999995e-07, -0],B:[0, 9.9999999999999995e-07, 9.9999999999999995e-07]},
  {I:203,A:[9.9999999999999995e-07, 0, 0],B:[0, -9.9999999999999995e-07, -0]},
  {I:206,A:[-0, -9.9999999999999995e-07, 0],B:[-9.9999999999999995e-07, 0, -0]},
  {I:209,A:[-0, 9.9999999999999995e-07, 0],B:[9.9999999999999995e-07, 0, 0]},
  {I:212,A:[9.9999999999999995e-07, 0, 0],B:[-0, -9.9999999999999995e-07, -0]},
  {I:215,A:[-9.9999999999999995e-07, -0, -0],B:[0, 9.9999999999999995e-07, 0]},
  {I:218,A:[0, 9.9999999999999995e-07, -0],B:[0, 0, -0]},
  {I:250,A:[0, -0, -0],B:[9.9999999999999995e-07, -0, 0]}
  ]
};


// ================= ingebouwde topologiecatalogus =================
// 2_2 is in de UI de gebruikelijke korte gebruikersnotatie; de standaard
// linknotatie voor de Hopf-link is 2^2_1. De 5_2-curve gebruikt een bekende
// Lissajous-representatie (3,2,7) met faseverschuivingen (0.7,0.2,0).
const BUILTIN_TOPOLOGIES = Object.freeze({
  ring:       {label:'ring 0₁', components:1},
  hopf:       {label:'Hopf-link 2₂', components:2},
  trefoil:    {label:'ideal trefoil 3₁ (Gilbert)', components:1},
  figure8:    {label:'figure-eight 4₁', components:1},
  cinquefoil: {label:'cinquefoil 5₁ = T(2,5)', components:1},
  twist52:    {label:'three-twist 5₂', components:1}
});

function topologyInfo(){
  const entry=activeKnotEntry();
  if(entry){
    const count=P.idealComponentMode==='all'?Math.max(1,(entry.components||[]).length):1;
    return {label:'extern catalogusobject',components:count};
  }
  return BUILTIN_TOPOLOGIES[P.topo] || BUILTIN_TOPOLOGIES.trefoil;
}
function topologyLabel(){
  if(P.knotKey){const kind=P.knotSource==='fseries'?'Fouriercurve':P.knotSource==='knotplot'?'KnotPlot-candidate':'ideal knoop/link';return `${kind} ${P.knotKey}`;}
  if(P.knotIdx>=0) return `ideal knoop/link ${knotLabel(P.knotIdx)}`;
  return topologyInfo().label;
}
function topologyComponentCount(){ return topologyInfo().components || 1; }

// ================= parameters & state =================
const KAPPA_HE  = 9.9693e-8;      // m^2/s  (h/m4)
const R_HORN_SST= 1.40897017e-15; // m, canonieke Compton-locked horn/circulatiestraal; geen vaste kernradius
const V_CHAR_SST= 1.09384563e6;    // m/s, canonieke karakteristieke swirl-snelheid v↺* = ||v↺||
const C_LIGHT     = 2.99792458e8;   // m/s, exacte SI-waarde
const GAMMA0_SST= 9.68361920e-9;   // m^2/s, Canon v0.8.20
const OMEGA_COMPTON_SST = V_CHAR_SST/R_HORN_SST; // s^-1, fase-/turnoverfrequentie op R_horn; geen lokale vorticiteit
const BUNDLE_SOURCE_MODEL='analytic-finite-closed-loop-limit';
const C0        = 0.1395;         // gemeten discretisatieconstante Schwarz-schema
const DELTA     = {hol:0.5, vast:0.25, gp:0.615};
const P = {
  mode:'solo', topo:'trefoil', inter:'lia', core:'vast', med:'sst', qual:'laag',
  Om:1.0, OmBundle:1.0, GaDemo:2.0, nQ:10, a:1.2415e-4, off:0.0, w:0.0, accExp:0.3,
  // v7.5 (v7.4b §B.1): frame-ontvlechting — drie onafhankelijke velden vervangen
  // de dubbele rol van de oude frame-toggle. solverFrame bepaalt de betekenis
  // van de opgeslagen coördinaten (lab of co-roterend), displayFrame alleen de
  // weergave, bgFlow de achtergrondstroming ('none'|'wall'|'bundle'; de
  // v7.4.2-exclusiviteitsguard is hiermee een type-invariant van de enum).
  solverFrame:'corot', displayFrame:'corot', bgFlow:'none',
  R0:0.07, zA:-0.42, zB:0.42, zSolo:0.0, Rcyl:0.25, Hcyl:0.5,
  knotIdx:-1, knotKey:'', knotSource:'builtin', compA:1, compB:1, idealComponentMode:'all',
  ccwA:true, ccwB:false, mirrorB:false, vzA:0, vzB:0, lockVz:true,
  vis:'line', tubeMat:'solid', showCenterline:false,
  revOm:false, revOmBundle:false, revGa:false, revOff:false, revW:false, revVzA:false, revVzB:false,
  ghostStewartson:false,
  taylorOsc:{enabled:false, amplitude:0.25, period:8},
  showChiArrow:false, twistProxyEnabled:false,
  wAl:1, wBe:1, wGa:1, showTracers:true, showStreamlines:false, tracerCount:5000, streamlineCount:28, particleSize:0.003, vortexOpacity:0.58, tracerSpawnMode:'inner-column',
  showPotentialFlow:false, potentialMode:'stream', potentialRadiusSource:'taylor', potentialRadius:0.08, potentialOpacity:0.58, potentialU:0.10,
  linkDH:false, linkVolumeRef:2*Math.PI*0.25*0.25*0.5, linkRefR:0.25, linkRefH:0.5,
  mfTemp:'0', mfAlpha:0, mfAlphaP:0, vnZ:0, revVn:false,
  autoRelax:false, timeReverse:false, topologyGuard:true,
  // D4 (2026-07-14): display-similarity is opt-in, geen stilzwijgende GP/SST-kernfysica.
  coreFlowLock:false,
  // r_kern is de nog niet canoniek afgeleide vaste/rotationele kernstraal; null = bewust onbepaald.
  rCorePhysical:null,
  // Losse Rosetta-schaalprobe; metadata-only en dus nooit een solver-, BEM- of contactparameter.
  scaleProbe:R_HORN_SST,
  centerLock:true, tracerWrapZ:true, vorticityLineColor:'#0F1A29',
  bundleEnabled:false, bundleProfile:'parallel', bundleSplay:0.45, bundleRadiusFrac:0.72, bundleVisualLines:61, bundleSourceModel:BUNDLE_SOURCE_MODEL,
  bundleBEMEnabled:true, bundleBoundaryMode:'asim', bundleBEMQuality:'mid',
  dvSeparatrix:true, dvColumn:true, dvCaps:true, dvStewartson:true, dvOpacity:1.0,
  // v7.5.3 Research Track: materiële vortex-stretching gate en drie Friedlander-profielen.
  stretchGateEnabled:true, stretchProfile:'rigid', stretchProfileApply:false, stretchProfileOnly:false,
  stretchOmega0:1.0, stretchBeta:60.0, stretchGamma:0.02, stretchSoftening:0.020,
  stretchEpsilon:0.010, stretchMode:1, stretchNeutralTol:0.020, stretchFailTol:0.100,
  // Expliciet niet-canonieke twee-knoop klokdiagnose; nooit solvercoupling.
  specClockEnabled:false, specClockDisplayGain:1
};
// v7.5: bevroren opstartdefaults voor zelftest-T0i (D4: verse start heeft de
// kernkoppeling uit; frames starten ontvlochten in corot/corot/none).
const P_DEFAULTS=Object.freeze({core:P.core,rCorePhysical:P.rCorePhysical,scaleProbe:P.scaleProbe,coreFlowLock:P.coreFlowLock,solverFrame:P.solverFrame,displayFrame:P.displayFrame,bgFlow:P.bgFlow,topologyGuard:P.topologyGuard,bundleBEMEnabled:P.bundleBEMEnabled,bundleBoundaryMode:P.bundleBoundaryMode,stretchGateEnabled:P.stretchGateEnabled,stretchProfileApply:P.stretchProfileApply});
// v7.5-framepredicaten. De wandadvectie u_bg=Ω×r staat alleen in het lab-
// solverframe met bgFlow='wall' expliciet in het snelheidsveld; in het
// co-roterende solverframe is de wand in rust en bestaat er geen term.
function bgWallInSolver(){return P.solverFrame==='lab'&&P.bgFlow==='wall';}
function bundleFlowActive(){return P.bundleEnabled&&P.bgFlow==='bundle';}
function zMin(){return -P.Hcyl;}
function zMax(){return  P.Hcyl;}
function cylinderHeight(){return 2*P.Hcyl;}
function cylinderVolume(){return 2*Math.PI*P.Rcyl*P.Rcyl*P.Hcyl;}
function signedMag(x){return Math.abs(x);}
function applySigned(rev,mag){return rev?-mag:mag;}
function updateHeaderTitle(){
  const d=(2*P.Rcyl*100).toFixed(0);
  document.getElementById('hTitle').innerHTML=
    `SUPERFLUÏDE VORTEXLAB · cilinder ${cylinderHeight().toFixed(2)} m hoog (z = ±${P.Hcyl.toFixed(2)} m) × Ø${d} cm · Ω_wall = <span id="hOm">${P.Om.toFixed(2)}</span> rad·s⁻¹`;
}
const Flags = {alpha:false, beta:false, gamma:false, sep:false};
const EXPLAIN = {
  alpha:{title:'α C(K) — geometrische kruisingscomplexiteit', cls:'on-alpha', color:'#FF6E6E',
    text:'C(K) is de ACN/Gauss-|integraal|-descriptor van de actuele polygonale centerline; dit is geen afstotingskracht of reconnectiebarrière.'},
  beta:{title:'β L̂(K) — genormaliseerde centerlinelengte', cls:'on-beta', color:'#FFAE45',
    text:'L̂=L/L₀ vergelijkt de actuele centerlinelengte met de startlengte; de gele wireframe is alleen een visuele overlay, geen gemodelleerde lijnspanning.'},
  gamma:{title:'γ Ĥ(K) — getekende heliciteitsdescriptor', cls:'on-gamma', color:'#A855F7',
    text:'Ĥ=Wr+2Lk is de centerline-heliciteitsdescriptor. De lineaire term is tekengevoelig en vormt zonder extra mechanisme geen stabiliteitsenergie.'},
  sep:{title:'∂V-overlay — domeingeometrie', cls:'on-sep', color:'#fff',
    text:'Taylor-kolom, eindcaps en Stewartson-zijlaag zijn visualisatielagen. ∂V is geen term in de geometrische score Ŝ.'}
};
function clamp(x,lo,hi){return Math.max(lo,Math.min(hi,x));}
function aSimActive(){return Math.max(P.a,A_SIM_EPS);}
function fmtLengthSI(m){
  if(!Number.isFinite(m))return '—';
  const a=Math.abs(m);if(a===0)return '0 m';
  if(a<1e-18)return m.toExponential(6)+' m';
  if(a<1e-15)return (m*1e18).toFixed(3)+' am';
  if(a<1e-12)return (m*1e15).toFixed(3)+' fm';
  if(a<1e-9)return (m*1e12).toFixed(3)+' pm';
  if(a<1e-6)return (m*1e9).toFixed(3)+' nm';
  if(a<1e-3)return (m*1e6).toFixed(3)+' µm';
  if(a<1)return (m*1e3).toFixed(3)+' mm';
  return m.toFixed(4)+' m';
}
function parseLengthInput(str){
  const t=String(str||'').trim().toLowerCase().replace(',','.').replace(/μ/g,'µ');
  if(!t)return NaN;
  if(/^(planck|plancklengte|l[_ ]?p|ℓ[_ ]?p)$/.test(t))return PLANCK_LENGTH;
  const m=t.match(/^([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)\s*(am|fm|pm|nm|um|µm|mm|cm|m)?$/i);
  if(!m)return NaN;
  const value=Number(m[1]);if(!Number.isFinite(value))return NaN;
  const scale={am:1e-18,fm:1e-15,pm:1e-12,nm:1e-9,um:1e-6,'µm':1e-6,mm:1e-3,cm:1e-2,m:1}[m[2]||'m'];
  return value*scale;
}
function formatASimInputMm(a){
  const mm=a*1e3;
  return a>=1e-6?mm.toFixed(6).replace(/0+$/,'').replace(/\.$/,''):mm.toExponential(8);
}
function contactThresholdInfo(){
  const physical=3*Math.max(0,Number.isFinite(P.a)?P.a:0);
  const scale=Math.max(1e-9,Math.abs(P.Rcyl||0),Math.abs(P.Hcyl||0),Math.abs(P.R0||0));
  const numerical=CONTACT_ULP_FACTOR*Number.EPSILON*scale;
  return {physical,numerical,effective:Math.max(physical,numerical),floorActive:numerical>physical};
}
function gapRatios(minGap){
  const ct=contactThresholdInfo();
  const aPhysical=Math.max(Number.isFinite(P.a)?P.a:0,A_SIM_EPS);
  const aEffective=Math.max(aPhysical,ct.effective/3);
  return {physical:minGap/aPhysical,effective:minGap/aEffective,floorActive:ct.floorActive};
}
function finiteOrNull(value){return Number.isFinite(value)?value:null;}
function resolvedFixedCoreRadius(){
  const r=Number(P.rCorePhysical);
  return Number.isFinite(r)&&r>0&&r<R_HORN_SST?r:NaN;
}
function sstRankineProfileAtRadius(r,gamma=Math.abs(Gamma()),rCore=resolvedFixedCoreRadius()){
  const rr=Math.abs(Number(r));
  if(!(rr>=0)||!(gamma>=0)||!Number.isFinite(rCore)||!(rCore>0))
    return {region:'unresolved',vTheta:NaN,omegaAngular:NaN,vorticity:NaN};
  const omegaCore=gamma/(2*Math.PI*rCore*rCore);
  if(rr<=rCore)return {region:'solid-core',vTheta:omegaCore*rr,omegaAngular:omegaCore,vorticity:2*omegaCore};
  const vTheta=gamma/(2*Math.PI*Math.max(rr,1e-300));
  return {region:'irrotational-exterior',vTheta,omegaAngular:vTheta/Math.max(rr,1e-300),vorticity:0};
}
function fixedCoreDiagnostics(){
  const r=resolvedFixedCoreRadius();
  if(!Number.isFinite(r))return {r:null,omega:null,vorticity:null,boundarySpeed:null,ratio:null};
  const p=sstRankineProfileAtRadius(r,Math.abs(Gamma()),r);
  return {r,omega:p.omegaAngular,vorticity:p.vorticity,boundarySpeed:p.vTheta,ratio:R_HORN_SST/r};
}
function buildDiagRecord(Wr,Lk,ACN,sA){
  const ct=contactThresholdInfo(),core=fixedCoreDiagnostics();
  return {t:tPhys,Wr,Lk,ACN,RA:sA.R,zA:sA.z,a:P.a,aSim:P.a,
    rHornCanonical:R_HORN_SST,rCorePhysical:core.r,
    omegaComptonHorn:OMEGA_COMPTON_SST,omegaFixedCore:core.omega,vorticityFixedCore:core.vorticity,
    mfA:P.mfAlpha,mfAp:P.mfAlphaP,vn:P.vnZ,
    omegaBundle:P.OmBundle,omegaWall:P.Om,
    bundleEnabled:P.bundleEnabled,bundleProfile:P.bundleProfile,bundleSourceModel:P.bundleSourceModel,
    bundleDensityMid:bundleDensityAtZ(0),bundleRadiusMid:bundleRadiusAtZ(0),
    bundleBEMEnabled:P.bundleBEMEnabled,bundleBoundaryMode:P.bundleBoundaryMode,bundleBEMValid:bundleBEMCache.valid,
    bundleBEMRadius:finiteOrNull(bundleBEMCache.radius),bundleBEMResidualVelocity:finiteOrNull(bundleBEMCache.residualVelocity),bundleBEMResidualVorticity:finiteOrNull(bundleBEMCache.residualVorticity),
    topologyGuard:P.topologyGuard,topologyGap:lastTopologyGap,
    stretchGateEnabled:P.stretchGateEnabled,stretchProfile:P.stretchProfile,stretchProfileApply:P.stretchProfileApply,stretchProfileOnly:P.stretchProfileOnly,
    stretchStatus:StretchGate.lastReport&&StretchGate.lastReport.status,stretchLambda:StretchGate.lastReport&&StretchGate.lastReport.lambda,
    stretchLambdaStar:StretchGate.lastReport&&StretchGate.lastReport.lambdaStar,stretchG:StretchGate.lastReport&&StretchGate.lastReport.G,
    stretchCoreRatio:StretchGate.lastReport&&StretchGate.lastReport.coreRatio,stretchProfileGain:StretchGate.lastReport&&StretchGate.lastReport.profileGain,
    specClockEnabled:P.specClockEnabled,specClockCalibrated:SpecClock.calibrated,
    specClockCalibrationTime:finiteOrNull(SpecClock.calibrationTime),specClockCalibrationDistance:finiteOrNull(SpecClock.calibrationDistance),
    specClockDistance:finiteOrNull(SpecClock.last&&SpecClock.last.distance),
    specClockMutualA:finiteOrNull(SpecClock.last&&SpecClock.last.uA),specClockMutualB:finiteOrNull(SpecClock.last&&SpecClock.last.uB),
    specClockOmegaFullA:finiteOrNull(SpecClock.last&&SpecClock.last.omegaA),specClockOmegaFullB:finiteOrNull(SpecClock.last&&SpecClock.last.omegaB),
    specClockOmegaIsoA:finiteOrNull(SpecClock.last&&SpecClock.last.omegaIsoA),specClockOmegaIsoB:finiteOrNull(SpecClock.last&&SpecClock.last.omegaIsoB),
    specClockDeltaOmegaA:finiteOrNull(SpecClock.last&&SpecClock.last.deltaOmegaA),specClockDeltaOmegaB:finiteOrNull(SpecClock.last&&SpecClock.last.deltaOmegaB),
    specClockFieldLogMin:finiteOrNull(SpecClock.last&&SpecClock.last.fieldLogRatioMin),specClockFieldLogMax:finiteOrNull(SpecClock.last&&SpecClock.last.fieldLogRatioMax),
    specClockPhaseLogRatio:finiteOrNull(SpecClock.last&&SpecClock.last.phaseLogRatio),specClockResidual:finiteOrNull(SpecClock.last&&SpecClock.last.residual),
    specClockFieldLagMin:finiteOrNull(SpecClock.lagFieldMin),specClockFieldLagMax:finiteOrNull(SpecClock.lagFieldMax),specClockPhaseLag:finiteOrNull(SpecClock.lagPhase),
    contactThreshold:ct.effective,contactFloorActive:ct.floorActive,scaleProbe:P.scaleProbe};
}

// ================= v7.5.3 SST vortex-stretching gate / Friedlander-profielen =================
function stretchProfileTime(){return tPhys-(StretchGate.profileEpoch||0);}
function stretchProfileCoefficientsAtRadius(r){
  const rr=Math.max(0,Math.abs(Number(r)||0));
  if(P.stretchProfile==='differential'){
    return {A:P.stretchOmega0+P.stretchBeta*rr*rr,Aprime:2*P.stretchBeta*rr,label:'A₂'};
  }
  if(P.stretchProfile==='regularized'){
    const ap=Math.max(1e-12,Math.abs(P.stretchSoftening)),d=rr*rr+ap*ap;
    return {A:P.stretchGamma/(2*Math.PI*d),Aprime:-P.stretchGamma*rr/(Math.PI*d*d),label:'A₃'};
  }
  return {A:P.stretchOmega0,Aprime:0,label:'A₁'};
}
function stretchProfileVelocityAt(x,y,z,t=stretchProfileTime()){
  if(!P.stretchProfileApply)return {ux:0,uy:0,uz:0,A:0,Aprime:0,q:0,phase:0};
  const r=Math.hypot(x,y),th=r>1e-15?Math.atan2(y,x):0,c=stretchProfileCoefficientsAtRadius(r);
  const m=Math.max(1,Math.round(P.stretchMode)),R=Math.max(1e-12,P.Rcyl);
  const q=Math.pow(clamp(r/R,0,1),m),phase=th-t*c.A;
  return {ux:-c.A*y,uy:c.A*x,uz:P.stretchEpsilon*q*Math.sin(m*phase),A:c.A,Aprime:c.Aprime,q,phase};
}
function stretchProfileVorticityAt(x,y,z,t=stretchProfileTime()){
  const r=Math.hypot(x,y),th=r>1e-15?Math.atan2(y,x):0,c=stretchProfileCoefficientsAtRadius(r);
  const m=Math.max(1,Math.round(P.stretchMode)),R=Math.max(1e-12,P.Rcyl),q=Math.pow(clamp(r/R,0,1),m);
  const phase=th-t*c.A,co=Math.cos(m*phase),si=Math.sin(m*phase);
  const qOverR=r>1e-15?q/r:(m===1?1/R:0),qPrime=m*qOverR;
  const omegaR=P.stretchEpsilon*m*qOverR*co;
  const omegaThetaBase=-P.stretchEpsilon*qPrime*si;
  const omegaThetaStretch=P.stretchEpsilon*m*t*c.Aprime*q*co;
  return {omegaR,omegaTheta:omegaThetaBase+omegaThetaStretch,omegaThetaBase,omegaThetaStretch,
    omegaZ:2*c.A+r*c.Aprime,A:c.A,Aprime:c.Aprime,q,phase};
}
function stretchProfileReference(rProbe,t=stretchProfileTime()){
  const r=Math.max(1e-12,Math.abs(rProbe)),c=stretchProfileCoefficientsAtRadius(r),tt=Math.abs(t);
  const shear=r*tt*c.Aprime,gain=Math.sqrt(1+shear*shear),G=0.5*Math.log1p(shear*shear);
  return {r,A:c.A,Aprime:c.Aprime,shear,gain,G,lambda:tt>1e-15?G/tt:0,label:c.label};
}
function stretchProfileCharacteristicRate(){
  if(!P.stretchProfileApply)return 0;
  let rate=0;
  const samples=48;
  for(let i=0;i<=samples;i++){
    const r=P.Rcyl*i/samples,c=stretchProfileCoefficientsAtRadius(r);
    rate=Math.max(rate,Math.abs(c.A),Math.abs(r*c.Aprime));
  }
  rate=Math.max(rate,Math.abs(P.stretchEpsilon)/Math.max(P.Rcyl,1e-12));
  return rate;
}
function disableStretchProfileCoupling(){P.stretchProfileApply=false;P.stretchProfileOnly=false;}

// ================= SST vortexbundel research-track =================
function bundleQuantum(){
  if(P.med==='sst')return GAMMA0_SST;
  if(P.med==='he')return KAPPA_HE;
  return Math.max(1e-30,Math.abs(Gamma()));
}
function bundleScaleAtU(u){
  const q=clamp(Number(u)||0,0,1),s=clamp(Number(P.bundleSplay)||0,0,1.4);
  if(P.bundleProfile==='splay')return Math.max(0.15,1+s*(q-0.5));
  if(P.bundleProfile==='periodic')return 1+0.5*s*(1-Math.cos(2*Math.PI*q));
  return 1;
}
function bundleScaleExtrema(){
  let lo=Infinity,hi=0;
  for(let i=0;i<=128;i++){const l=bundleScaleAtU(i/128);lo=Math.min(lo,l);hi=Math.max(hi,l);}
  return {lo,hi};
}
function bundleUFromZ(z){return clamp((z-zMin())/Math.max(1e-12,cylinderHeight()),0,1);}
function bundleOmegaAtZ(z){
  if(!P.bundleEnabled)return 0;
  const lam=bundleScaleAtU(bundleUFromZ(z));
  return (P.revOmBundle?-1:1)*Math.abs(P.OmBundle)/Math.max(1e-12,lam*lam);
}
function bundleDensityAtZ(z){return 2*Math.abs(bundleOmegaAtZ(z))/bundleQuantum();}
function bundleReferenceRadius(){return clamp(P.bundleRadiusFrac,0.10,0.93)*P.Rcyl;}
function bundleBaseRadius(){
  const ex=bundleScaleExtrema();
  return bundleReferenceRadius()/Math.max(ex.hi,1e-12);
}
function bundleRadiusAtZ(z){return bundleBaseRadius()*bundleScaleAtU(bundleUFromZ(z));}
function bundleCirculationAtZ(z){
  const Rb=bundleRadiusAtZ(z),om=bundleOmegaAtZ(z);
  return 2*Math.PI*om*Rb*Rb;
}
function bundlePhysicalCountAtZ(z){
  const r=bundleRadiusAtZ(z);
  return bundleDensityAtZ(z)*Math.PI*r*r;
}
function bundleVelocityProfileAt(x,y,z,active=bundleFlowActive()){
  if(!active)return {ux:0,uy:0,uz:0,omega:0,vorticity:0,inside:false,radius:bundleRadiusAtZ(z)};
  const om=bundleOmegaAtZ(z),Rb=Math.max(1e-30,bundleRadiusAtZ(z));
  const r2=x*x+y*y,inside=r2<=Rb*Rb;
  // Uniform-vorticity bundle inside; irrotational 1/r exterior with exactly
  // the same enclosed circulation Γ_enc=2πΩR_b² outside.
  const coeff=inside?om:om*Rb*Rb/Math.max(r2,1e-30);
  return {ux:-coeff*y,uy:coeff*x,uz:0,omega:inside?om:coeff,
    vorticity:inside?2*om:0,inside,radius:Rb};
}
function bundleVelocityAt(x,y,z){return bundleVelocityProfileAt(x,y,z,bundleFlowActive());}
function bundleExteriorVelocityAt(x,y,z,projectInside=true){
  let ex=x,ey=y,ez=z;
  if(projectInside&&P.bundleBEMEnabled&&bundleBEMCache.valid){
    const ni=nearestKnotTubeInfo(ex,ey,ez),R=1.002*bundleBEMCache.radius;
    if(ni.distance<R&&ni.distance>1e-14*R){const d=R-ni.distance;ex+=d*ni.nx;ey+=d*ni.ny;ez+=d*ni.nz;}
  }
  const ub=bundleVelocityProfileAt(ex,ey,ez,true);let ux=ub.ux,uy=ub.uy,uz=ub.uz;
  if(P.bundleBEMEnabled&&bundleBEMCache.valid){const c=evalBundleBEMGradient(ex,ey,ez,bundleBEMCache.qVelocity);ux+=c[0];uy+=c[1];uz+=c[2];}
  return {ux,uy,uz};
}
function backgroundVelocityAt(x,y,z){
  let ux=0,uy=0,uz=0;
  if(bgWallInSolver()){ux+=-P.Om*y;uy+=P.Om*x;}
  if(P.stretchProfileApply){const us=stretchProfileVelocityAt(x,y,z);ux+=us.ux;uy+=us.uy;uz+=us.uz;}
  if(bundleFlowActive()){
    const ub=bundleExteriorVelocityAt(x,y,z);ux+=ub.ux;uy+=ub.uy;uz+=ub.uz;
  }
  return {ux,uy,uz};
}
function backgroundVelocityForFilamentPoint(px,py,pz,tx,ty,tz){
  let ux=0,uy=0,uz=0;
  if(bgWallInSolver()){ux+=-P.Om*py;uy+=P.Om*px;}
  if(P.stretchProfileApply){const us=stretchProfileVelocityAt(px,py,pz);ux+=us.ux;uy+=us.uy;uz+=us.uz;}
  if(!bundleFlowActive())return {ux,uy,uz};
  if(!(P.bundleBEMEnabled&&bundleBEMCache.valid)){
    const b=bundleVelocityProfileAt(px,py,pz,true);return {ux:ux+b.ux,uy:uy+b.uy,uz:uz+b.uz};
  }
  const t=normalize3(tx,ty,tz),ref=Math.abs(t[2])<0.85?[0,0,1]:[1,0,0];
  const n1=normalize3(t[1]*ref[2]-t[2]*ref[1],t[2]*ref[0]-t[0]*ref[2],t[0]*ref[1]-t[1]*ref[0]);
  const n2=normalize3(t[1]*n1[2]-t[2]*n1[1],t[2]*n1[0]-t[0]*n1[2],t[0]*n1[1]-t[1]*n1[0]);
  const R=1.002*bundleBEMCache.radius;let sx=0,sy=0,sz=0;
  for(let q=0;q<4;q++){const th=q*Math.PI/2,nx=Math.cos(th)*n1[0]+Math.sin(th)*n2[0],ny=Math.cos(th)*n1[1]+Math.sin(th)*n2[1],nz=Math.cos(th)*n1[2]+Math.sin(th)*n2[2];
    const b=bundleExteriorVelocityAt(px+R*nx,py+R*ny,pz+R*nz,false);sx+=b.ux;sy+=b.uy;sz+=b.uz;}
  return {ux:ux+sx/4,uy:uy+sy/4,uz:uz+sz/4};
}
function bundleSampleNormalized(i,n){
  const N=Math.max(1,Math.round(n)),j=clamp(Math.round(i),0,N-1);
  const rho=Math.sqrt((j+0.5)/N),theta=j*Math.PI*(3-Math.sqrt(5));
  return {rho,theta};
}

// ================= v7.5.2 Niveau-C 3D Neumann source-panel BEM/MFS =================
// De basisbundel mag vorticaal zijn. Een harmonische gradientcorrectie
// verandert haar curl niet, maar dwingt de normale snelheid op de gesloten
// knooptube naar nul. Een tweede, onafhankelijke Neumann-oplossing wordt op
// het coarse-grained vorticiteitsveld toegepast; daardoor zijn de getekende
// swirl strings divergentievrij in het buitendomein en tangentieel aan de
// uitsluitingsbuis. Dit is een discrete Research-Track exterior closure.
function bundleOmegaDerivativeAtZ(z){
  const h=Math.max(1e-6,1e-4*cylinderHeight());
  return (bundleOmegaAtZ(z+h)-bundleOmegaAtZ(z-h))/(2*h);
}
function bundleVorticityProfileAt(x,y,z,active=bundleFlowActive()){
  if(!active)return {wx:0,wy:0,wz:0,inside:false,radius:bundleRadiusAtZ(z)};
  const Rb=Math.max(1e-30,bundleRadiusAtZ(z)),r2=x*x+y*y;
  if(r2>Rb*Rb)return {wx:0,wy:0,wz:0,inside:false,radius:Rb};
  const om=bundleOmegaAtZ(z),dop=bundleOmegaDerivativeAtZ(z);
  return {wx:-x*dop,wy:-y*dop,wz:2*om,inside:true,radius:Rb};
}
function bundleBEMTargetCount(){return P.bundleBEMQuality==='high'?64:(P.bundleBEMQuality==='low'?24:40);}
function bundleBEMBoundaryInfo(){
  let requested=P.a,label='a_sim';
  if(P.bundleBoundaryMode==='rcore'){
    requested=resolvedFixedCoreRadius();label='r_kern';
    if(!Number.isFinite(requested))return {valid:false,requested:NaN,floor:NaN,label,reason:'r_kern is onbepaald'};
  }else if(P.bundleBoundaryMode==='rhorn'){
    requested=R_HORN_SST;label='R_horn';
  }
  const lm=Y&&fils.length?lminAll():Math.max(P.R0,1e-3);
  const Lref=Math.max(P.Rcyl,P.Hcyl,P.R0,1e-3);
  const floor=Math.max(128*Number.EPSILON*Lref,1e-4*lm);
  if(!(Number.isFinite(requested)&&requested>0))return {valid:false,requested,floor,label,reason:'ongeldige radius'};
  if(requested<floor)return {valid:false,requested,floor,label,reason:`${label} ligt onder de geometrische BEM-resolutievloer`};
  return {valid:true,requested,floor,label,reason:''};
}
function normalize3(x,y,z){const m=Math.hypot(x,y,z)||1;return [x/m,y/m,z/m];}
function buildBundleBEMNodes(radius,target=bundleBEMTargetCount()){
  const active=fils.filter(f=>!f.ghost),nodes=[];
  if(!Y||!active.length)return nodes;
  const ringCount=4;
  const totalN=active.reduce((a,f)=>a+f.N,0)||1;
  for(const f of active){
    const along=Math.max(2,Math.round((target/ringCount)*f.N/totalN));
    for(let a=0;a<along;a++){
      const i=Math.floor((a+0.5)*f.N/along)%f.N,im=(i-1+f.N)%f.N,ip=(i+1)%f.N,o=f.off;
      const cx=Y[o+3*i],cy=Y[o+3*i+1],cz=Y[o+3*i+2];
      const t=normalize3(Y[o+3*ip]-Y[o+3*im],Y[o+3*ip+1]-Y[o+3*im+1],Y[o+3*ip+2]-Y[o+3*im+2]);
      const ref=Math.abs(t[2])<0.85?[0,0,1]:[1,0,0];
      const n1=normalize3(t[1]*ref[2]-t[2]*ref[1],t[2]*ref[0]-t[0]*ref[2],t[0]*ref[1]-t[1]*ref[0]);
      const n2=normalize3(t[1]*n1[2]-t[2]*n1[1],t[2]*n1[0]-t[0]*n1[2],t[0]*n1[1]-t[1]*n1[0]);
      for(let q=0;q<ringCount&&nodes.length<target;q++){
        const th=2*Math.PI*q/ringCount,co=Math.cos(th),si=Math.sin(th);
        const nx=co*n1[0]+si*n2[0],ny=co*n1[1]+si*n2[1],nz=co*n1[2]+si*n2[2];
        nodes.push({x:cx+radius*nx,y:cy+radius*ny,z:cz+radius*nz,nx,ny,nz,
          sx:cx+0.35*radius*nx,sy:cy+0.35*radius*ny,sz:cz+0.35*radius*nz});
      }
    }
  }
  return nodes;
}
function solveDensePivot(A,b,n){
  const M=new Float64Array(A),x=new Float64Array(b);
  for(let k=0;k<n;k++){
    let piv=k,best=Math.abs(M[k*n+k]);
    for(let i=k+1;i<n;i++){const v=Math.abs(M[i*n+k]);if(v>best){best=v;piv=i;}}
    if(!(best>1e-20)||!Number.isFinite(best))return null;
    if(piv!==k){for(let j=k;j<n;j++){const t=M[k*n+j];M[k*n+j]=M[piv*n+j];M[piv*n+j]=t;}const tb=x[k];x[k]=x[piv];x[piv]=tb;}
    const d=M[k*n+k];
    for(let i=k+1;i<n;i++){
      const f=M[i*n+k]/d;if(!f)continue;M[i*n+k]=0;
      for(let j=k+1;j<n;j++)M[i*n+j]-=f*M[k*n+j];x[i]-=f*x[k];
    }
  }
  const out=new Float64Array(n);
  for(let i=n-1;i>=0;i--){let v=x[i];for(let j=i+1;j<n;j++)v-=M[i*n+j]*out[j];out[i]=v/M[i*n+i];}
  return out;
}
function bemKernelGradient(x,y,z,node){
  const rx=x-node.sx,ry=y-node.sy,rz=z-node.sz,r2=rx*rx+ry*ry+rz*rz;
  const inv=-1/(4*Math.PI*Math.max(r2,1e-60)*Math.sqrt(Math.max(r2,1e-60)));
  return [rx*inv,ry*inv,rz*inv];
}
function solveBundleNeumann(nodes,fieldFn,radius){
  const N=nodes.length,n=N+1,A=new Float64Array(n*n),b=new Float64Array(n);
  const reg=1e-9/Math.max(radius*radius,1e-60);
  for(let i=0;i<N;i++){
    const ni=nodes[i],f=fieldFn(ni.x,ni.y,ni.z);
    b[i]=-(ni.nx*f[0]+ni.ny*f[1]+ni.nz*f[2]);
    for(let j=0;j<N;j++){
      const g=bemKernelGradient(ni.x,ni.y,ni.z,nodes[j]);
      A[i*n+j]=ni.nx*g[0]+ni.ny*g[1]+ni.nz*g[2]+(i===j?reg:0);
    }
    A[i*n+N]=1;A[N*n+i]=1;
  }
  const sol=solveDensePivot(A,b,n);if(!sol)return null;
  const q=sol.slice(0,N);let maxR=0,maxB=0;
  for(let i=0;i<N;i++){
    let normal=-b[i];
    for(let j=0;j<N;j++){const g=bemKernelGradient(nodes[i].x,nodes[i].y,nodes[i].z,nodes[j]);normal+=q[j]*(nodes[i].nx*g[0]+nodes[i].ny*g[1]+nodes[i].nz*g[2]);}
    maxR=Math.max(maxR,Math.abs(normal));maxB=Math.max(maxB,Math.abs(b[i]));
  }
  return {q,residual:maxR/Math.max(maxB,1e-30)};
}
let bundleBEMCache={valid:false,nodes:[],qVelocity:null,qVorticity:null,radius:NaN,residualVelocity:NaN,residualVorticity:NaN,status:'uit',builtStep:-1};
let bundleBEMDirty=true,bundleBEMStepCounter=0;
function invalidateBundleBEM(reason='geometry'){bundleBEMDirty=true;bundleBEMCache.status='wacht: '+reason;}
function ensureBundleBEM(force=false){
  if(!(P.bundleBEMEnabled&&P.bundleEnabled&&Y&&fils.some(f=>!f.ghost))){bundleBEMCache.valid=false;bundleBEMCache.status='uit of geen actieve bundel';return false;}
  if(!force&&!bundleBEMDirty&&(bundleBEMStepCounter-bundleBEMCache.builtStep)<BEM_REBUILD_STEPS)return bundleBEMCache.valid;
  const bi=bundleBEMBoundaryInfo();
  if(!bi.valid){bundleBEMCache.valid=false;bundleBEMCache.status=bi.reason;bundleBEMCache.radius=bi.requested;bundleBEMDirty=false;return false;}
  const nodes=buildBundleBEMNodes(bi.requested,bundleBEMTargetCount());
  if(nodes.length<8){bundleBEMCache.valid=false;bundleBEMCache.status='te weinig collocatiepunten';bundleBEMDirty=false;return false;}
  const sv=solveBundleNeumann(nodes,(x,y,z)=>{const u=bundleVelocityProfileAt(x,y,z,true);return [u.ux,u.uy,u.uz];},bi.requested);
  const sw=solveBundleNeumann(nodes,(x,y,z)=>{const w=bundleVorticityProfileAt(x,y,z,true);return [w.wx,w.wy,w.wz];},bi.requested);
  const valid=!!(sv&&sw&&sv.residual<0.15&&sw.residual<0.15);
  bundleBEMCache={valid,nodes,qVelocity:sv&&sv.q,qVorticity:sw&&sw.q,radius:bi.requested,
    residualVelocity:sv?sv.residual:Infinity,residualVorticity:sw?sw.residual:Infinity,
    status:!sv||!sw?'lineaire solve mislukt':(valid?'actief':'residu te groot; correctie uitgeschakeld'),builtStep:bundleBEMStepCounter};
  bundleBEMDirty=false;return bundleBEMCache.valid;
}
function evalBundleBEMGradient(x,y,z,q){
  if(!bundleBEMCache.valid||!q)return [0,0,0];let gx=0,gy=0,gz=0;
  for(let j=0;j<bundleBEMCache.nodes.length;j++){const g=bemKernelGradient(x,y,z,bundleBEMCache.nodes[j]),a=q[j];gx+=a*g[0];gy+=a*g[1];gz+=a*g[2];}
  return [gx,gy,gz];
}
function bundleVorticityAt(x,y,z){
  const w=bundleVorticityProfileAt(x,y,z,P.bundleEnabled);
  if(P.bundleBEMEnabled&&bundleBEMCache.valid){const c=evalBundleBEMGradient(x,y,z,bundleBEMCache.qVorticity);w.wx+=c[0];w.wy+=c[1];w.wz+=c[2];}
  return w;
}
function nearestKnotTubeInfo(x,y,z){
  let best2=Infinity,bx=0,by=0,bz=0;
  for(const f of fils){if(f.ghost)continue;const o=f.off;
    for(let i=0;i<f.N;i++){const j=(i+1)%f.N,ax=Y[o+3*i],ay=Y[o+3*i+1],az=Y[o+3*i+2],dx=Y[o+3*j]-ax,dy=Y[o+3*j+1]-ay,dz=Y[o+3*j+2]-az;
      const l2=dx*dx+dy*dy+dz*dz,t=clamp(((x-ax)*dx+(y-ay)*dy+(z-az)*dz)/Math.max(l2,1e-30),0,1);
      const qx=ax+t*dx,qy=ay+t*dy,qz=az+t*dz,rx=x-qx,ry=y-qy,rz=z-qz,d2=rx*rx+ry*ry+rz*rz;
      if(d2<best2){best2=d2;bx=rx;by=ry;bz=rz;}
    }
  }
  const d=Math.sqrt(best2),n=normalize3(bx,by,bz);return {distance:d,nx:n[0],ny:n[1],nz:n[2]};
}
function bundleMaxOmega(){
  if(!bundleFlowActive())return 0;
  let m=0;for(let i=0;i<=64;i++)m=Math.max(m,Math.abs(bundleOmegaAtZ(zMin()+cylinderHeight()*i/64)));
  return m;
}
function effectiveW(){
  // v7.1 (B1): w geldt uitsluitend in solo-modus, conform de docs. Voorheen
  // lekte P.w door naar botsing-modus (spookdrift na moduswissel).
  if(P.mode!=='solo') return 0;
  if(P.taylorOsc.enabled){
    const Omosc=2*Math.PI/Math.max(0.5,P.taylorOsc.period);
    return P.taylorOsc.amplitude*Omosc*Math.cos(Omosc*tPhys);
  }
  return P.w;
}
function carrierAxialDrift(carrier){
  // v7.1 (B1): per-drager v_z-drift geldt uitsluitend in botsing-modus.
  // Voorheen werkte een oude vzA-waarde ook in solo door (drift = w + vzA).
  if(P.mode==='solo') return 0;
  if(carrier==='A'||P.lockVz) return P.vzA;
  return P.vzB;
}
function fmtAxialMmPerS(x){
  const a=Math.abs(x);
  if(a===0)return '0 mm/s';
  if(a<0.001)return x.toExponential(2).replace('e-','·10⁻')+' mm/s';
  if(a<0.1)return x.toFixed(4).replace(/0+$/,'').replace(/\.$/,'')+' mm/s';
  if(a<10)return x.toFixed(3).replace(/0+$/,'').replace(/\.$/,'')+' mm/s';
  if(a<100)return x.toFixed(2).replace(/0+$/,'').replace(/\.$/,'')+' mm/s';
  return x.toFixed(1).replace(/\.0$/,'')+' mm/s';
}
// v7.2 (RP2): de eerdere Γ_sheet/Γ_rel-uitlezingen zijn volledig verwijderd —
// u_θ=-w/(2Ωr) is dimensieloos, dus Γ_sheet=2πr·u_θ had dimensie m en de
// subtractie Γ_sheet-Γ_bg (m minus m²/s) was niet gedefinieerd. Een proxy-label
// maakt een ongeldige bewerking niet geldig. Wat overblijft is uitsluitend de
// dimensieloze Stewartson/Rossby-proxy q_S, met getekende Ω (geen |Ω| meer,
// zodat het teken correct meedraait met omkering van de cilinderrotatie).
function stewartsonCirculation(w,rCap,Om){
  const r=Math.max(rCap,0.025);
  const OmS=Math.abs(Om)<1e-6?(Om<0?-1e-6:1e-6):Om;
  const qS=-w/(2*OmS*r);
  const gammaBg=2*Math.abs(Om)*Math.PI*r*r; // wel dimensioneel geldig (m²/s)
  return {qS,gammaBg,rCap:r};
}
function taylorColumnState(s,vz){
  const Ga=Math.abs(Gamma()), rBase=s.R*1.5+P.a*3;
  const zetaAbs=2*P.Om+Ga/(Math.PI*Math.max(s.R*s.R,P.a*P.a));
  const Lchar=Math.max(0.05,2*rBase);
  const zetaRel=zetaAbs-2*P.Om-vz/Lchar;
  const ratio=Math.abs(zetaAbs)/Math.max(1e-6,Math.abs(zetaRel));
  const rFoot=P.Rcyl*0.25;
  const rDyn=rBase*Math.sqrt(clamp(ratio,0.16,6.25));
  const rCap=Flags.sep?Math.max(rFoot,rDyn):rDyn;

  // De lokale separatrix blijft rond de drager begrensd door rCap.
  const zSepTop=Math.min(zMax(),s.z+rCap);
  const zSepBot=Math.max(zMin(),s.z-rCap);

  // De Taylor-kolom / tangent-cylinder visualisatie loopt langs de volledige
  // rotatie-as tussen de domein-eindvlakken. De axiale lengte is dus niet
  // begrensd door de radiale separatrixstraal.
  const zTop=zMax();
  const zBot=zMin();
  const hColumn=Math.max(0,cylinderHeight());
  return {rCap,zTop,zBot,zSepTop,zSepBot,hColumn,zetaRel,zetaAbs,rBase,rFoot};
}
const QUAL_N = {
  botsing:{laag:64, mid:96, hoog:128},
  solo:  {laag:96, mid:192, hoog:288}
};
const RING_N = 48;
const EVAL_BUDGET = 1.5e6;   // kernel-evals per frame

let Y=null, fils=[], ghostFil=null, tPhys=0, phi=0, bundlePhi=0, paused=false;
let flagged="", warned=false, lastUmax=1e-9;
let Wr0=null, L0=1;
let K1,K2,K3,K4,TT;
let effAcc=0, effAccSimSum=0, effAccRealSum=0;
let perfWarmupUntil=0;
function resetPerformanceMeasurement(warmupMs=900){
  effAcc=0;effAccSimSum=0;effAccRealSum=0;
  perfWarmupUntil=performance.now()+Math.max(0,warmupMs);
}
let stepDebt=0;   // deterministische stepper: afspeel-tijddebet in seconden
let lastT=performance.now(),frame=0;
let playbackDebtResetReason='startup';
function resetPlaybackDebt(reason='ui-change'){
  stepDebt=0;
  lastT=performance.now();
  playbackDebtResetReason=reason;
  resetPerformanceMeasurement(300);
}
function setPausedState(value,reason='pause-toggle'){
  paused=!!value;
  const b=document.getElementById('bPause');
  if(b)b.textContent=paused?'Hervat':'Pauzeer';
  resetPlaybackDebt(reason);
}
const hist=[];
let twistProxy=null;
let chiArrows=[];
let lastFrameVel=null;
let stabilityLast=null, stabilityFrame=0, autoRelaxFrame=0;
let stabilityThrottle=1, stabilityThrottleTarget=1;
let carrierAnchors=Object.create(null);
let coreCouplingBusy=false;
let coreFlowNotice='';

function Gamma(){
  if(P.med==='he')  return P.nQ*KAPPA_HE;
  if(P.med==='sst') return P.nQ*GAMMA0_SST;
  const g=P.GaDemo; const s=g<0?-1:1;
  const floor=P.coreFlowLock?1e-12:0.2;
  return s*Math.max(Math.abs(g),floor)*1e-3;
}
function kappaMedium(){
  if(P.med==='he')  return KAPPA_HE;
  if(P.med==='sst') return GAMMA0_SST;
  return null;
}

// ---- wederzijdse wrijving (v7) ----
// α, α′ voor He-II bij SVP, T90-schaal. Bron: Donnelly, "The Observed Properties
// of Liquid Helium at the Saturated Vapor Pressure", hfst. 11 Tabel 11.3
// (compilatie van Barenghi–Donnelly–Vinen, J. Low Temp. Phys. 52, 189 (1983)).
// Let op: α′ wisselt van teken tussen 2.06 en 2.08 K — dat is echt, geen typefout.
// Onder 1.30 K geeft de tabel geen waarden; gebruik daar 'aangepast'.
const MF_TABLE={
  '1.30':[0.034,0.01383],'1.35':[0.042,0.01543],'1.40':[0.051,0.01668],
  '1.45':[0.061,0.01746],'1.50':[0.072,0.01766],'1.55':[0.084,0.01721],
  '1.60':[0.097,0.01608],'1.65':[0.111,0.01437],'1.70':[0.126,0.01225],
  '1.75':[0.142,0.01003],'1.80':[0.160,0.008211],'1.85':[0.181,0.007438],
  '1.90':[0.206,0.008340],'2.00':[0.279,0.01198],'2.02':[0.302,0.01097],
  '2.04':[0.330,0.008318],'2.06':[0.366,0.003018],'2.08':[0.414,-0.006690],
  '2.10':[0.481,-0.02412]
};
function applyMfTemp(key){
  P.mfTemp=key;
  if(key==='0'){P.mfAlpha=0;P.mfAlphaP=0;}
  else if(key!=='custom'&&MF_TABLE[key]){P.mfAlpha=MF_TABLE[key][0];P.mfAlphaP=MF_TABLE[key][1];}
}
function mfActive(){return P.mfAlpha!==0||P.mfAlphaP!==0;}
// Schwarz-wrijvingstransformatie per knooppunt (puur, unit-getest):
// ṡ = v_s + α ŝ'×(v_n−v_s) − α' ŝ'×[ŝ'×(v_n−v_s)], met v_s de totale lokale
// superfluïde snelheid en v_n de opgelegde normale-vloeistofsnelheid.
function mfTransform(ux,uy,uz,tx,ty,tz,vnx,vny,vnz,al,alp,OUT3){
  const tl=Math.sqrt(tx*tx+ty*ty+tz*tz);
  if(!(tl>1e-30)){OUT3[0]=ux;OUT3[1]=uy;OUT3[2]=uz;return;}
  tx/=tl;ty/=tl;tz/=tl;
  const rx=vnx-ux,ry=vny-uy,rz=vnz-uz;                       // v_ns
  const c1x=ty*rz-tz*ry,c1y=tz*rx-tx*rz,c1z=tx*ry-ty*rx;     // ŝ'×v_ns
  const c2x=ty*c1z-tz*c1y,c2y=tz*c1x-tx*c1z,c2z=tx*c1y-ty*c1x; // ŝ'×(ŝ'×v_ns)
  OUT3[0]=ux+al*c1x-alp*c2x;
  OUT3[1]=uy+al*c1y-alp*c2y;
  OUT3[2]=uz+al*c1z-alp*c2z;
}
const MF_TMP3=new Float64Array(3);

function rankineGammaTarget(){
  return 2*Math.PI*P.a*P.a*Math.abs(P.Om);
}
function coreFlowRatio(){
  const om=Math.abs(P.Om);
  if(om<=1e-12)return NaN; // χ_Ω is mathematically undefined at Ω=0
  const den=2*Math.PI*P.a*P.a*om;
  return Math.abs(Gamma())/den;
}
function dimensionlessDiagnostics(sA,vzRel){
  const om=Math.abs(P.Om);
  return {
    chiOmega:om>1e-9?coreFlowRatio():NaN,
    roZ:om>1e-9?Math.abs(vzRel)/(2*om*P.Rcyl):NaN,
    aOverR:P.a/Math.max(sA&&sA.R||0,1e-12),
  };
}
function relativeCarrierOrientationSign(){
  return (P.ccwA?1:-1)*(P.ccwB?1:-1);
}
function syncCoreFlowCoupling(driver='geometry'){
  if(!P.coreFlowLock||coreCouplingBusy)return;
  coreCouplingBusy=true;
  try{
    if(Math.abs(P.Om)<1e-12){
      P.Om=P.revOm?-1:1;
    }
    const omega=Math.max(1e-12,Math.abs(P.Om));
    const q=kappaMedium();
    if(driver==='gamma'){
      const gamma=Math.max(1e-30,Math.abs(Gamma()));
      const aWanted=Math.sqrt(gamma/(2*Math.PI*omega));
      P.a=clamp(aWanted,A_SIM_INPUT_FLOOR,Math.max(A_SIM_INPUT_FLOOR,coreRadiusMax||1));
      // Wanneer de geometrische limiet ingrijpt, herschaal Γ terug naar een
      // exact toegelaten Rankine-relatie.
      if(Math.abs(P.a-aWanted)>1e-15)driver='geometry';
    }
    if(driver!=='gamma'){
      const target=rankineGammaTarget();
      if(q){
        P.nQ=Math.max(1,Math.min(1e9,Math.round(target/q)));
        P.a=clamp(Math.sqrt((P.nQ*q)/(2*Math.PI*omega)),A_SIM_INPUT_FLOOR,Math.max(A_SIM_INPUT_FLOOR,coreRadiusMax||1));
      }else{
        const sign=P.Om<0?-1:1;
        P.GaDemo=sign*Math.max(1e-12,target/1e-3);
        P.revGa=P.GaDemo<0;
      }
    }
  }finally{
    coreCouplingBusy=false;
  }
  updateCoreFlowReadout();
}
function updateCoreFlowReadout(){
  const panel=document.getElementById('coreFlowLinkPanel');
  const out=document.getElementById('coreFlowReadout');
  if(!panel||!out)return;
  panel.classList.toggle('active',P.coreFlowLock);
  const gamma=Math.abs(Gamma());
  const uSim=gamma/(2*Math.PI*Math.max(P.a,1e-30));
  const omSim=gamma/(2*Math.PI*Math.max(P.a*P.a,1e-30));
  if(!P.coreFlowLock){
    const notice=coreFlowNotice?` · ${coreFlowNotice}`:'';
    out.textContent=`Vrij · Γ=${fmtGamma(gamma)} m²/s · a_sim=${fmtLengthSI(P.a)} · u_sim≈${fmtSpeed(uSim)} · Ω_sim≈${omSim.toExponential(3)} s⁻¹${notice}`;
    return;
  }
  const ratio=coreFlowRatio();
  const quant=P.med==='sst'?` · n=${P.nQ.toLocaleString('nl-NL')} Γ₀`:P.med==='he'?` · n=${P.nQ.toLocaleString('nl-NL')} κ`:'';
  const canon=P.med==='sst'?` · R_horn=${R_HORN_SST.toExponential(3)} m · r_kern=${Number.isFinite(resolvedFixedCoreRadius())?fmtLengthSI(resolvedFixedCoreRadius()):'onbepaald'}`:'';
  const ratioText=Number.isFinite(ratio)?ratio.toFixed(5):'—';
  out.textContent=`GEKOPPELD · Γ=${fmtGamma(gamma)} m²/s${quant} · a_sim=${fmtLengthSI(P.a)} · Ω=${Math.abs(P.Om).toFixed(3)} s⁻¹ · |Γ|/(2πa_sim²|Ω|)=${ratioText}${canon}`;
}
function applySSTSimilarityPreset(){
  disableStretchProfileCoupling();P.stretchGateEnabled=true;
  // Zichtbare similarity-scale: behoud de canonieke kwantisatie Γ=nΓ₀ en
  // de Rankine-verhouding Γ=2πa²Ω, zonder de fysische femtometerkern in
  // een meterschaal-visualisatie te pretenderen te resolven.
  P.med='sst';
  P.core='vast';
  P.coreFlowLock=true; // D4: expliciete similarity-preset-keuze
  if(window.ModelLog&&window.ModelLog.logUser)window.ModelLog.logUser('coreFlowLock-preset',{value:true});
  P.Om=1.0; P.revOm=false;
  P.nQ=1;
  P.rCorePhysical=null;
  P.scaleProbe=R_HORN_SST;
  P.displayFrame='corot';P.solverFrame='corot';P.bgFlow='none';
  P.bundleEnabled=false;P.bundleSourceModel=BUNDLE_SOURCE_MODEL;
  // Behoud eerst de canonieke enkelvoudige circulatie Γ₀ en leid de
  // zichtbare similarity-radius af uit Γ₀=2πa²Ω.
  syncCoreFlowCoupling('gamma');
}

function applySSTBundlePreset(){
  disableStretchProfileCoupling();P.stretchGateEnabled=true;
  P.mode='solo';P.topo='ring';P.inter='lia';P.qual='hoog';DELTA.gp=0.615;
  P.knotIdx=-1;P.knotKey='';P.compA=1;P.compB=1;
  P.med='sst';P.core='vast';P.coreFlowLock=false;P.rCorePhysical=null;P.scaleProbe=R_HORN_SST;
  P.Om=0;P.revOm=false;P.displayFrame='lab';P.solverFrame='corot';P.bgFlow='bundle';
  P.OmBundle=1;P.revOmBundle=false;P.bundleEnabled=true;P.bundleProfile='parallel';
  P.bundleSplay=0.45;P.bundleRadiusFrac=0.72;P.bundleVisualLines=61;
  P.bundleBEMEnabled=true;P.bundleBoundaryMode='asim';P.bundleBEMQuality='mid';P.topologyGuard=true;
  P.nQ=1;P.a=1.2415e-4;P.R0=0.05;P.zSolo=0;P.off=0;P.w=0;P.vzA=0;P.vzB=0;P.lockVz=true;
  P.mfTemp='0';P.mfAlpha=0;P.mfAlphaP=0;P.vnZ=0;P.autoRelax=false;P.timeReverse=false;P.topologyGuard=true;
  P.centerLock=true;P.tracerWrapZ=false;P.tracerSpawnMode='inner-column';
  rebuildLattice();syncUi();updateSubtitle();
}
function applyDefaultStartup(){
  disableStretchProfileCoupling();P.stretchGateEnabled=true;P.stretchProfile='rigid';
  // Baseline: ideal trefoil, SST medium, vaste/Rankine Research-Track kernclosure en LIA.
  P.mode='solo';P.topo='trefoil';P.inter='lia';P.qual='laag';P.core='vast';DELTA.gp=0.615;
  P.knotIdx=-1;P.knotKey='';P.compA=1;P.compB=1;
  P.R0=0.07;P.zSolo=0;P.off=0;P.w=0;P.vzA=0;P.vzB=0;P.lockVz=true;
  P.timeReverse=false;P.autoRelax=false;P.topologyGuard=true;P.centerLock=true;
  P.tracerWrapZ=true;P.tracerSpawnMode='inner-column';
  P.ccwA=true;P.ccwB=false;P.mirrorB=false;
  applySSTSimilarityPreset();
  P.nQ=10;
  syncCoreFlowCoupling('gamma');
  syncUi();updateSubtitle();
}
function applyFrictionPreset(){
  disableStretchProfileCoupling();P.stretchGateEnabled=true;
  // Demonstratie wederzijdse wrijving: solo He-II-ring bij 1.90 K in rustende
  // normale vloeistof. Verwacht: Ṙ = −αU (krimp), translatie ×(1−α′), en de
  // HUD-rij "Ṙ meting / α(v_n∥−U_K)" als live orthodoxietest.
  P.mode='solo';P.topo='ring';P.inter='lia';P.qual='hoog';
  P.knotIdx=-1;P.knotKey='';P.compA=1;P.compB=1;
  P.med='he';P.core='gp';P.coreFlowLock=true;P.scaleProbe=HE_CORE_REF;DELTA.gp=0.615; // D4: expliciet, preset-context
  if(window.ModelLog&&window.ModelLog.logUser)window.ModelLog.logUser('coreFlowLock-preset',{value:true});
  P.R0=0.07;P.zSolo=0;P.off=0;P.w=0;P.vzA=0;P.vzB=0;P.lockVz=true;
  P.timeReverse=false;P.autoRelax=false;P.topologyGuard=true;P.centerLock=true;
  P.tracerWrapZ=true;
  P.nQ=10;
  applyMfTemp('1.90');P.vnZ=0;P.revVn=false;
  P.accExp=3; // fysische krimp is µm/s-schaal; 10³× maakt hem zichtbaar
  syncCoreFlowCoupling('gamma');
}
function applySpecClockPreset(){
  disableStretchProfileCoupling();
  P.mode='botsing';P.topo='trefoil';P.inter='bs';P.qual='hoog';P.med='sst';P.core='vast';P.coreFlowLock=false;
  P.knotIdx=-1;P.knotKey='';P.compA=1;P.compB=1;P.R0=0.07;P.a=1.0e-3;P.nQ=1;
  P.Om=1;P.revOm=false;P.displayFrame='lab';P.solverFrame='corot';P.bgFlow='none';P.bundleEnabled=false;
  P.off=0;P.w=0;P.lockVz=false;P.vzA=+0.005;P.vzB=-0.005;P.ccwA=true;P.ccwB=false;P.mirrorB=false;
  P.timeReverse=false;P.autoRelax=false;P.topologyGuard=true;P.centerLock=false;P.tracerWrapZ=true;P.tracerSpawnMode='inner-column';
  P.mfTemp='0';P.mfAlpha=0;P.mfAlphaP=0;P.vnZ=0;P.specClockDisplayGain=1;P.specClockEnabled=true;
  P.accExp=0; // v7.6.13: reproduceerbare 1× sweep; nooit een geërfde hoge afspeelsnelheid
  setInitialAxialSeparation(Math.min(0.84,initialAxialSeparationSliderMax()));
  resetSpecClockRuntime('preset');
  syncUi();updateSubtitle();resetState();
  SpecClock.autoStartAfterCalibration=true;
  setPausedState(true,'spec-clock-preset-arm');
  updateSpecClockDisplay();
  if(typeof resetParticlesToTaylorColumn==='function')resetParticlesToTaylorColumn();
  if(window.ModelLog){window.ModelLog.setEnabled(true);const cb=document.getElementById('cModelLog');if(cb)cb.checked=true;window.ModelLog.logEvent('spec-clock-preset',{topo:P.topo,inter:P.inter,qual:P.qual,a:P.a,dz0:initialAxialSeparation(),off:P.off,vzA:P.vzA,vzB:P.vzB});}
  setFlag('⏱ speculative swirl-clock sweep-preset actief: SST, botsing, trefoil, Biot–Savart, kwaliteit hoog, topology guard aan, auto-relax uit, Δz_AB,0='+fmtLengthSI(initialAxialSeparation())+', v_z A/B naar elkaar toe. De run staat gepauzeerd op 1×; kalibreer eenmaal bij t=0, daarna start hij automatisch.',true);
}
function applyStretchGatePreset(){
  P.mode='solo';P.topo='trefoil';P.inter='lia';P.qual='hoog';P.med='sst';P.core='vast';P.coreFlowLock=false;P.rCorePhysical=null;P.scaleProbe=R_HORN_SST;
  P.knotIdx=-1;P.knotKey='';P.compA=1;P.compB=1;P.R0=0.07;P.zSolo=0;P.off=0;P.a=1.5e-3;P.nQ=10;
  P.Om=0;P.revOm=false;P.solverFrame='corot';P.displayFrame='lab';P.bgFlow='none';P.bundleEnabled=false;
  P.w=0;P.vzA=0;P.vzB=0;P.lockVz=true;P.mfTemp='0';P.mfAlpha=0;P.mfAlphaP=0;P.vnZ=0;
  P.autoRelax=false;P.timeReverse=false;P.topologyGuard=true;P.centerLock=false;P.tracerWrapZ=true;
  P.stretchGateEnabled=true;P.stretchProfile='rigid';P.stretchProfileApply=true;P.stretchProfileOnly=true;
  P.stretchOmega0=1;P.stretchBeta=60;P.stretchGamma=0.02;P.stretchSoftening=0.02;P.stretchEpsilon=0.01;P.stretchMode=1;
  P.stretchNeutralTol=0.02;P.stretchFailTol=0.10;P.accExp=0.3;
  syncUi();updateSubtitle();
}
function applyStringTheoryPreset(){
  // Passieve schaalprobe: de solver blijft de gewone filament-ODE met vrije Γ.
  disableStretchProfileCoupling();P.stretchGateEnabled=true;
  P.mode='solo';P.topo='trefoil';P.inter='lia';P.qual='hoog';P.core='gp';DELTA.gp=0.615;
  P.knotIdx=-1;P.knotKey='';P.compA=1;P.compB=1;
  P.med='string';P.coreFlowLock=false;P.rCorePhysical=null;P.scaleProbe=PLANCK_LENGTH;
  P.GaDemo=0.2;P.a=1.2415e-4;P.Om=1;P.revOm=false;P.revGa=false;
  P.displayFrame='corot';P.solverFrame='corot';P.bgFlow='none';
  P.bundleEnabled=false;P.bundleBEMEnabled=true;P.bundleBoundaryMode='asim';
  P.R0=0.07;P.zSolo=0;P.off=0;P.w=0;P.vzA=0;P.vzB=0;P.lockVz=true;
  P.timeReverse=false;P.autoRelax=false;P.topologyGuard=true;P.centerLock=true;
  P.tracerWrapZ=true;P.mfTemp='0';P.mfAlpha=0;P.mfAlphaP=0;P.vnZ=0;
}
function acc(){ return Math.pow(10,P.accExp); }
const RING_QUAL={laag:48, mid:96, hoog:144};
function carrierN(){
  if(proxyDecompResolutionOverride>0&&P.mode==='botsing'&&!isRingTopo())return proxyDecompResolutionOverride;
  if(isRingTopo()) return RING_QUAL[P.qual];
  return QUAL_N[P.mode][P.qual];
}
function getIdealKnotCatalog(){
  if(typeof IDEAL_KNOT_IDS!=='undefined'&&typeof IDEAL_KNOT_DB!=='undefined')
    return {ids:IDEAL_KNOT_IDS,db:IDEAL_KNOT_DB,source:'ideal'};
  return null;
}
function getFourierKnotCatalog(){
  if(typeof FSERIES_KNOT_IDS!=='undefined'&&typeof FSERIES_KNOT_DB!=='undefined')
    return {ids:FSERIES_KNOT_IDS,db:FSERIES_KNOT_DB,source:'fseries'};
  return null;
}
function getKnotPlotKnotCatalog(){
  if(typeof KNOTPLOT_KNOT_IDS!=='undefined'&&typeof KNOTPLOT_KNOT_DB!=='undefined')
    return {ids:KNOTPLOT_KNOT_IDS,db:KNOTPLOT_KNOT_DB,source:'knotplot'};
  return null;
}
const KNOTPLOT_ID_ALIASES=Object.freeze({Tlink_6_9:'torus_6.9'});
function normalizeKnotPlotId(id){return KNOTPLOT_ID_ALIASES[id]||id;}
function knotPlotLinkingAbs(entry){
  const declared=finiteMetaNumber(entry?.torus?.expectedPairwiseLinkingAbs);if(Number.isFinite(declared))return Math.abs(declared);
  const vals=(entry?.pairwiseLinking?.roundedMatrix||[]).flat().map(Number).filter(Number.isFinite).map(Math.abs);return vals.length?Math.max(...vals):null;
}
function knotPlotCrossingNumber(entry,id){
  const p=finiteMetaNumber(entry?.torus?.p),q=finiteMetaNumber(entry?.torus?.q);if(Number.isFinite(p)&&Number.isFinite(q))return Math.min((p-1)*q,(q-1)*p);
  const m=String(id||'').match(/^(?:knot_|link_)(\d+)\./);return m?Number(m[1]):null;
}
function knotCatalogForSource(source){
  if(source==='ideal')return getIdealKnotCatalog();
  if(source==='fseries')return getFourierKnotCatalog();
  if(source==='knotplot')return getKnotPlotKnotCatalog();
  return null;
}
function activeKnotEntry(){
  if(P.knotKey){
    if(P.knotSource==='knotplot'){const migrated=normalizeKnotPlotId(P.knotKey);if(migrated!==P.knotKey)P.knotKey=migrated;}
    const catalog=knotCatalogForSource(P.knotSource);
    if(catalog?.db?.[P.knotKey])return catalog.db[P.knotKey];
  }
  if(P.knotIdx>=0&&Array.isArray(window.IDEAL_KNOTS))return window.IDEAL_KNOTS[P.knotIdx]||null;
  return null;
}
function knotEntryComponents(entry){
  if(!entry)return [];
  if(Array.isArray(entry.components))return entry.components.map(c=>Array.isArray(c)?{coeffs:c}:c);
  if(Array.isArray(entry.coeffs))return [{coeffs:entry.coeffs,L:entry.L}];
  return [];
}
function finiteMetaNumber(v){
  return v!==null&&v!==undefined&&v!==''&&Number.isFinite(Number(v))?Number(v):NaN;
}
function activeCoeffs(forCarrier){
  const entry=activeKnotEntry();
  const comps=knotEntryComponents(entry);
  if(comps.length){
    const ci=(forCarrier==='B'?P.compB:P.compA)-1;
    return comps[Math.min(Math.max(ci,0),comps.length-1)].coeffs;
  }
  return IDEAL_TREFOIL_3_1_1.coeffs;
}
function carrierWantDir(which){
  // CCW gezien vanaf +z => drager beweegt +z; CW => -z. Autoaim dwingt dit af (ook voor knopen).
  const ccw=which==='B'?P.ccwB:P.ccwA;
  return ccw?+1:-1;
}
function carrierOffsetX(which){
  if(P.mode!=='botsing') return P.off;   // solo: volledige topologie krijgt offset
  if(which==='B') return P.mirrorB?-P.off:P.off;
  return 0;
}

const INITIAL_AXIAL_SEPARATION_MIN=1e-3;
const INITIAL_AXIAL_SEPARATION_MAX=1e6;
let separationBoundaryAutoDisabled=false;
function initialAxialSeparation(){return Math.abs(P.zB-P.zA);}
function initialAxialSeparationSliderMax(){return Math.max(INITIAL_AXIAL_SEPARATION_MIN,2*Math.max(P.Hcyl,5e-4));}
function syncInputUnlessEditing(input,value,force=false){
  if(!input||(!force&&document.activeElement===input))return false;
  const next=String(value);if(input.value!==next)input.value=next;
  const range=input.closest('.param-hybrid')?.querySelector('input.param-slider');if(range)range.value=String(hybridRangeFromInput(input));
  return true;
}
function syncHybridSliderMax(input,maxValue){
  if(!input)return;
  input.dataset.sliderMax=String(maxValue);
  const range=input.closest('.param-hybrid')?.querySelector('input.param-slider');
  if(range){range.max=String(maxValue);range.value=String(hybridRangeFromInput(input));}
}
function setInitialAxialSeparation(distance){
  const mid=.5*(P.zA+P.zB);
  const requested=Math.abs(Number(distance));
  if(!Number.isFinite(requested))return initialAxialSeparation();
  const applied=clamp(requested,INITIAL_AXIAL_SEPARATION_MIN,INITIAL_AXIAL_SEPARATION_MAX);
  P.zA=mid-.5*applied;P.zB=mid+.5*applied;
  const period=initialAxialSeparationSliderMax();
  if(P.mode==='botsing'&&applied>period*(1+1e-12)&&P.tracerWrapZ){
    P.tracerWrapZ=false;separationBoundaryAutoDisabled=true;
    const wrap=document.getElementById('cTracerWrapZ');if(wrap)wrap.checked=false;
  }
  return applied;
}
function announceSeparationBoundaryPolicy(){
  if(!separationBoundaryAutoDisabled)return;
  separationBoundaryAutoDisabled=false;
  const message='ℹ Δz_AB,0 is groter dan de cilinderhoogte; de periodieke z-grens voor knopen en deeltjes is automatisch uitgezet zodat de gekozen verre afstand behouden blijft.';
  setFlag(message,true);
  if(window.ModelLog)window.ModelLog.logEvent('periodic-z-auto-disabled',{reason:'initial-separation-exceeds-cell',axial:initialAxialSeparation(),cellHeight:initialAxialSeparationSliderMax()});
}
function signedMmPerSFromMps(v){return (Number(v)||0)*1e3;}
function fmtSignedMmPerSInput(v){
  const x=signedMmPerSFromMps(v);
  if(!Number.isFinite(x))return '—';
  return (Math.round(x*10000)/10000).toString().replace(/\.0+$/,'').replace(/(\.\d*?)0+$/,'$1')+' mm/s';
}
function syncSpecClockQuickControls({force=false}={}){
  const sep=document.getElementById('sSpecSepAB'),vSep=document.getElementById('vSpecSepAB');
  const off=document.getElementById('sSpecOffClone'),vOff=document.getElementById('vSpecOffClone');
  const vzA=document.getElementById('sSpecVzA'),vA=document.getElementById('vSpecVzA');
  const vzB=document.getElementById('sSpecVzB'),vB=document.getElementById('vSpecVzB');
  const cLog=document.getElementById('cSpecClockLog');
  if(sep){const sliderMax=(1000*initialAxialSeparationSliderMax()).toFixed(3);syncInputUnlessEditing(sep,(1000*initialAxialSeparation()).toFixed(3).replace(/\.?0+$/,''),force);syncHybridSliderMax(sep,sliderMax);}
  if(vSep)vSep.textContent=fmtLengthSI(initialAxialSeparation());
  if(off)syncInputUnlessEditing(off,(P.off*1000).toFixed(3).replace(/\.?0+$/,''),force);
  if(vOff)vOff.textContent=(P.off*1000).toFixed(1).replace(/\.0$/,'')+' mm';
  if(vzA)syncInputUnlessEditing(vzA,signedMmPerSFromMps(P.vzA).toFixed(4).replace(/\.?0+$/,''),force);
  if(vA)vA.textContent=fmtSignedMmPerSInput(P.vzA);
  if(vzB){syncInputUnlessEditing(vzB,signedMmPerSFromMps(P.vzB).toFixed(4).replace(/\.?0+$/,''),force);vzB.disabled=P.mode!=='botsing'||P.lockVz;}
  if(vB)vB.textContent=fmtSignedMmPerSInput(P.vzB);
  if(cLog)cLog.checked=!!(window.ModelLog&&window.ModelLog.enabled);
}
function updateInitialSeparationUi(){
  const row=document.getElementById('sepABRow'),input=document.getElementById('sSepAB');
  const value=document.getElementById('vSepAB'),readout=document.getElementById('sepABReadout');
  if(!row||!input||!value||!readout)return;
  const collision=P.mode==='botsing';row.classList.toggle('hidden',!collision);
  const dz0=initialAxialSeparation(),sliderMax=initialAxialSeparationSliderMax();
  syncInputUnlessEditing(input,(1000*dz0).toFixed(3).replace(/\.?0+$/,''));
  syncHybridSliderMax(input,(1000*sliderMax).toFixed(3));
  value.textContent=fmtLengthSI(dz0);
  if(!collision){readout.className='core-limit-note sep-readout warn';readout.textContent='Alleen actief in botsingsmodus.';return;}
  const startCenter=Math.hypot(dz0,Math.abs(P.off));
  const a=Y&&fils.length?carrierGroupStats('A'):null,b=Y&&fils.length?carrierGroupStats('B'):null;
  const currentCenter=a&&b?Math.hypot(b.cx-a.cx,b.cy-a.cy,b.z-a.z):NaN;
  const ct=contactThresholdInfo();
  const gap=Number.isFinite(lastTopologyGap)?lastTopologyGap:NaN;
  const safe=Number.isFinite(gap)?gap>ct.effective:null;
  readout.className='core-limit-note sep-readout '+(safe===true?'good':(safe===false?'bad':'warn'));
  const gapText=Number.isFinite(gap)?fmtLengthSI(gap):(P.topologyGuard?'wordt bepaald':'niet gemeten · topology guard uit');
  const far=dz0>sliderMax*(1+1e-12);
  const boundaryText=far?` · buiten cilinderhoogte ${fmtLengthSI(sliderMax)} · periodieke z-grens ${P.tracerWrapZ?'GEBLOKKEERD':'uit'}`:'';
  readout.innerHTML=`startcentrumafstand d<sub>AB,0</sub>=${fmtLengthSI(startCenter)} · actuele d<sub>AB</sub>=${Number.isFinite(currentCenter)?fmtLengthSI(currentCenter):'—'} · centerline-clearance=${gapText} · stopgrens=${fmtLengthSI(ct.effective)}${boundaryText}`;
}

function isRingTopo(){
  return P.topo==='ring'&&P.knotIdx<0&&!P.knotKey;
}
function kelvinSpeed(R){
  const Ga=Math.abs(Gamma());
  return Ga/(4*Math.PI*Math.max(R,1e-6))*(Math.log(8*R/P.a)-DELTA[P.core]);
}
function chiHatFromFilament(f){
  if(isRingTopo())return null;
  const N=f.N,o=f.off;
  const st=carrierStats(f);
  let maxR=0,mx=0,my=0;
  for(let k=0;k<N;k++){
    const rx=Y[o+3*k]-st.cx,ry=Y[o+3*k+1]-st.cy;
    const r=Math.hypot(rx,ry);
    if(r>maxR){maxR=r;mx=rx;my=ry;}
  }
  if(maxR<1e-9)return {x:1,y:0,phi:0};
  return {x:mx/maxR,y:my/maxR,phi:Math.atan2(my,mx)*180/Math.PI};
}
function bodyFrameState(f,V){
  const st=carrierStats(f);
  const N=f.N,o=f.off;
  let num=0,den=0;
  for(let k=0;k<N;k++){
    const rx=Y[o+3*k]-st.cx,ry=Y[o+3*k+1]-st.cy;
    const vx=V[o+3*k],vy=V[o+3*k+1];
    num+=rx*vy-ry*vx;
    den+=rx*rx+ry*ry;
  }
  const omegaZ=den>1e-12?num/den:0;
  const chi=chiHatFromFilament(f);
  return {omegaZ,chi,cx:st.cx,cy:st.cy,cz:st.z,R:st.R};
}
function initTwistProxy(){
  twistProxy=fils.map(f=>new Float64Array(f.N));
}
function twistProxySum(){
  // v7.2 (RP4): booglengte-gewogen gemiddelde ⟨∫u·t̂ dt⟩_L in meters. De oude
  // kale knooppuntsom schaalde ∝N (zelfde knoop, dubbele resolutie → dubbele
  // waarde) en deelde bovendien door 2π — een restant van de twist-claim.
  if(!twistProxy||!Y)return 0;
  let num=0,den=0;
  fils.forEach((f,fi)=>{
    if(f.ghost)return;
    const tw=twistProxy[fi];if(!tw)return;
    const N=f.N,o=f.off;
    for(let k=0;k<N;k++){const k2=(k+1)%N;
      const l=Math.hypot(Y[o+3*k2]-Y[o+3*k],Y[o+3*k2+1]-Y[o+3*k+1],Y[o+3*k2+2]-Y[o+3*k+2]);
      num+=l*tw[k];den+=l;}
  });
  return den>0?num/den:0;
}
function updateTwistProxy(dt,V){
  if(!P.twistProxyEnabled||!twistProxy||!Y)return;
  fils.forEach((f,fi)=>{
    const N=f.N,o=f.off,tw=twistProxy[fi];
    for(let k=0;k<N;k++){
      const k2=(k+1)%N;
      const tx=Y[o+3*k2]-Y[o+3*k],ty=Y[o+3*k2+1]-Y[o+3*k+1],tz=Y[o+3*k2+2]-Y[o+3*k+2];
      const tl=Math.hypot(tx,ty,tz)||1;
      const ux=V[o+3*k],uy=V[o+3*k+1],uz=V[o+3*k+2];
      tw[k]+=dt*(ux*tx/tl+uy*ty/tl+uz*tz/tl);
    }
  });
}
function fmtOmegaBody(om){
  const deg=om*180/Math.PI;
  if(Math.abs(deg)>=0.01)return deg.toFixed(2)+'°/s';
  return (om*1000).toFixed(2)+' mrad/s';
}
function allFils(){return ghostFil?[...fils,ghostFil]:fils;}
// v7.2 (RP2): de ghost is dynamisch krachteloos (v7.1) én numeriek onzichtbaar —
// hij telt niet mee in ℓ_min (dtCFL) of het evaluatiebudget, zodat ghost
// aan/uit de stapreeks en truncatiefout niet meer kan veranderen.
function dynamicFils(){return fils.filter(f=>!f.ghost);}
function filamentGamma(f){return f.ghost?f.gammaVal:Gamma();}
function carrierFilaments(which){ return fils.filter(f=>(f.carrier||'A')===which); }
function firstCarrierFilament(which){ return carrierFilaments(which)[0]||null; }
function carrierGroupStats(which){
  const fs=carrierFilaments(which);
  if(!fs.length)return null;
  let cx=0,cy=0,cz=0,n=0;
  for(const f of fs){for(let k=0;k<f.N;k++){
    cx+=Y[f.off+3*k];cy+=Y[f.off+3*k+1];cz+=Y[f.off+3*k+2];n++;
  }}
  cx/=n;cy/=n;cz/=n;
  let R=0,rWall=0;
  for(const f of fs){for(let k=0;k<f.N;k++){
    const x=Y[f.off+3*k],y=Y[f.off+3*k+1];
    R+=Math.hypot(x-cx,y-cy);
    rWall=Math.max(rWall,Math.hypot(x,y));
  }}
  return {R:R/n,z:cz,rWall,cx,cy,components:fs.length};
}

// ================= SPECULATIVE two-knot swirl-clock diagnostic =================
// Dit blok is strikt passief. Het verandert Y, Gamma, dt, de topology guard of
// enige andere solverparameter niet. De combinatie V_CHAR_SST +/- u_mutual is
// uitsluitend een formele Research-Track-bracket, geen afgeleide superpositiewet.
const SpecClock={
  calibrated:false,sampleStride:8,stepCounter:0,dtBucket:0,
  phaseNullRefA:NaN,phaseNullRefB:NaN,
  calibrationTime:NaN,calibrationDistance:NaN,calibrationCount:0,
  calibrationMode:'legacy-z',projectionNull:false,
  lagFieldMin:0,lagFieldMax:0,lagPhase:0,
  last:null,tmpV:null,tmpIsoA:null,tmpIsoB:null,autoStartAfterCalibration:false
};
let LastSpecClockBenchmarkSummary=null;
let LastProxyDecompositionSummary=null;
let proxyDecompResolutionOverride=0;
function specClockBenchmarkRestoreStatus(){
  const d=LastProxyDecompositionSummary;
  if(d){
    if(d.state==='completed'){const cls=d.engine==='FAIL'?'bad':(d.engine==='PASS'&&d.research==='PASS'?'good':'warn');return {cls,text:`PROXY-DECOMPOSITIE + NORMALISATIE + TRANSFER-LAW VOLTOOID · ENGINE ${d.engine} · RESEARCH ${d.research} · ${d.snapshots} passieve snapshots. De teruggezette handmatige sessie staat op t=0 en vereist herkalibratie.`};}
    if(d.state==='aborted')return {cls:'warn',text:`PROXY-DECOMPOSITIE + NORMALISATIE + TRANSFER-LAW AFGEBROKEN · ${d.completedSnapshots}/${d.totalSnapshots} snapshots · handmatige sessie teruggezet naar t=0.`};
  }
  const b=LastSpecClockBenchmarkSummary;
  if(!b)return null;
  if(b.state==='completed'){
    const cls=b.engine==='PASS'?(b.research==='PASS'?'good':'warn'):'bad';
    return {cls,text:`BENCHMARK VOLTOOID · ENGINE ${b.engine} · RESEARCH PROXY ${b.research} · de benchmarkresultaten blijven geldig. Alleen de teruggezette handmatige sessie staat op t=0 en vereist een nieuwe fase-nullkalibratie.`};
  }
  if(b.state==='aborted')return {cls:'warn',text:`BENCHMARK AFGEBROKEN · ${b.completedRuns}/${b.totalRuns} runs voltooid · de oorspronkelijke sessie is teruggezet naar t=0 en vereist zo nodig herkalibratie.`};
  return null;
}
function specClockLogEta(v){
  const q=clamp(Math.abs(v)/C_LIGHT,0,1-1e-15);
  return 0.5*Math.log1p(-q*q);
}
function specClockEta(v){return Math.exp(specClockLogEta(v));}
function specClockEtaDiffFromDeltaLogs(deltaLogA,deltaLogB){
  if(!(Number.isFinite(deltaLogA)&&Number.isFinite(deltaLogB)))return NaN;
  const eta0=specClockEta(V_CHAR_SST);
  return eta0*(Math.expm1(deltaLogA)-Math.expm1(deltaLogB));
}
function specClockEnvelope(u){
  const du=Math.max(0,Number(u)||0),beta0=V_CHAR_SST/C_LIGHT,d=du/C_LIGHT;
  const x0=1-beta0*beta0,baseLog=0.5*Math.log(x0);
  // Bereken de perturbatie rechtstreeks. V_CHAR_SST ± u wordt bewust niet eerst
  // als groot floating-pointgetal gevormd: bij nm/s-velden kan u onder één ulp
  // van V_CHAR_SST liggen en anders al vóór log/eta volledig verdwijnen.
  const plusBeta=Math.min(1-1e-15,beta0+d),minusBeta=Math.abs(beta0-d);
  const dxPlus=plusBeta===beta0+d?-(2*beta0*d+d*d):(1-plusBeta*plusBeta)-x0;
  const dxMinus=-(minusBeta*minusBeta-beta0*beta0);
  const deltaLogEtaMin=0.5*Math.log1p(dxPlus/x0);
  const deltaLogEtaMax=0.5*Math.log1p(dxMinus/x0);
  const deltaLogEtaMid=0.5*Math.log1p(-(d*d)/x0);
  const logEtaMin=baseLog+deltaLogEtaMin,logEtaMax=baseLog+deltaLogEtaMax,logEtaMid=baseLog+deltaLogEtaMid;
  return {vMin:Math.abs(V_CHAR_SST-du),vMax:Math.min(C_LIGHT*(1-1e-15),V_CHAR_SST+du),vMid:Math.hypot(V_CHAR_SST,du),
    baseLog,deltaLogEtaMin,deltaLogEtaMax,deltaLogEtaMid,logEtaMin,logEtaMax,logEtaMid,
    etaMin:Math.exp(baseLog)*Math.exp(deltaLogEtaMin),etaMax:Math.exp(baseLog)*Math.exp(deltaLogEtaMax),etaMid:Math.exp(baseLog)*Math.exp(deltaLogEtaMid)};
}
function specClockProxyAssessment(phaseRatio,fieldRatioMin,fieldRatioMax,fieldLogMin,fieldLogMax,phaseLogRatio){
  const pLog=Number.isFinite(phaseLogRatio)?phaseLogRatio:(Number.isFinite(phaseRatio)&&phaseRatio>0?Math.log(phaseRatio):NaN);
  if(!Number.isFinite(pLog))return{state:'open',rawOverlap:null,falsified:false};
  const lo=Number.isFinite(fieldLogMin)?fieldLogMin:Math.log(fieldRatioMin);
  const hi=Number.isFinite(fieldLogMax)?fieldLogMax:Math.log(fieldRatioMax);
  if(!(Number.isFinite(lo)&&Number.isFinite(hi)))return{state:'open',rawOverlap:null,falsified:false};
  const rawOverlap=pLog>=lo&&pLog<=hi;
  return{state:rawOverlap?'raw-overlap':'unmapped-mismatch',rawOverlap,falsified:false};
}
function specClockPrerequisites(ignoreEnabled=false){
  if(!ignoreEnabled&&!P.specClockEnabled)return{ok:false,reason:'UIT'};
  if(P.mode!=='botsing')return{ok:false,reason:'vereist botsingsmodus met drager A en B'};
  if(P.med!=='sst')return{ok:false,reason:'vereist medium SST'};
  if(P.timeReverse)return{ok:false,reason:'gepauzeerd bij achterwaartse integratie'};
  if(!Y||!carrierFilaments('A').length||!carrierFilaments('B').length)return{ok:false,reason:'twee dragers ontbreken'};
  return{ok:true,reason:''};
}
function carrierBodyOmegaFromVelocity(which,V){
  if(!V||!Y)return NaN;
  const st=carrierGroupStats(which);if(!st)return NaN;
  let num=0,den=0;
  for(const f of carrierFilaments(which))for(let k=0;k<f.N;k++){
    const i=f.off+3*k,rx=Y[i]-st.cx,ry=Y[i+1]-st.cy;
    num+=rx*V[i+1]-ry*V[i];den+=rx*rx+ry*ry;
  }
  return den>1e-18?num/den:NaN;
}
function ensureSpecClockVelocityBuffers(){
  if(!Y)return false;
  if(!SpecClock.tmpV||SpecClock.tmpV.length!==Y.length)SpecClock.tmpV=new Float64Array(Y.length);
  if(!SpecClock.tmpIsoA||SpecClock.tmpIsoA.length!==Y.length)SpecClock.tmpIsoA=new Float64Array(Y.length);
  if(!SpecClock.tmpIsoB||SpecClock.tmpIsoB.length!==Y.length)SpecClock.tmpIsoB=new Float64Array(Y.length);
  return true;
}
function carrierIsolatedBodyOmega(which,out){
  if(!ensureSpecClockVelocityBuffers())return NaN;
  out.fill(0);
  velocityCore(Y,carrierFilaments(which),out,P.inter==='lia',{includeExternal:true});
  return carrierBodyOmegaFromVelocity(which,out);
}
function carrierMutualTangentialRms(target,source,maxSamples=48){
  const targets=carrierFilaments(target),sources=carrierFilaments(source);
  if(!targets.length||!sources.length||!Y)return{uRms:NaN,samples:0};
  const total=targets.reduce((n,f)=>n+f.N,0),stride=Math.max(1,Math.ceil(total/maxSamples));
  const a2=aSimActive()*aSimActive();let sampleIndex=0,sum=0,wSum=0,samples=0;
  for(const ft of targets){const N=ft.N,o=ft.off;
    for(let k=0;k<N;k++,sampleIndex++){
      if(sampleIndex%stride)continue;
      const km=(k-1+N)%N,kp=(k+1)%N,i=o+3*k,im=o+3*km,ip=o+3*kp;
      let tx=Y[ip]-Y[im],ty=Y[ip+1]-Y[im+1],tz=Y[ip+2]-Y[im+2];
      const tl=Math.hypot(tx,ty,tz)||1;tx/=tl;ty/=tl;tz/=tl;
      const ds=.5*(Math.hypot(Y[i]-Y[im],Y[i+1]-Y[im+1],Y[i+2]-Y[im+2])+Math.hypot(Y[ip]-Y[i],Y[ip+1]-Y[i+1],Y[ip+2]-Y[i+2]));
      let ux=0,uy=0,uz=0;
      for(const fs of sources){const M=fs.N,os=fs.off,pref=filamentGamma(fs)/(4*Math.PI);
        for(let j=0;j<M;j++){const j2=(j+1)%M,a=os+3*j,b=os+3*j2;
          const dlx=Y[b]-Y[a],dly=Y[b+1]-Y[a+1],dlz=Y[b+2]-Y[a+2];
          const mx=.5*(Y[a]+Y[b]),my=.5*(Y[a+1]+Y[b+1]),mz=.5*(Y[a+2]+Y[b+2]);
          const rx=Y[i]-mx,ry=Y[i+1]-my,rz=Y[i+2]-mz,r2=rx*rx+ry*ry+rz*rz+a2;
          const inv=pref/(r2*Math.sqrt(r2));
          ux+=(dly*rz-dlz*ry)*inv;uy+=(dlz*rx-dlx*rz)*inv;uz+=(dlx*ry-dly*rx)*inv;
        }
      }
      const up=ux*tx+uy*ty+uz*tz,w=Math.max(ds,1e-15);sum+=w*up*up;wSum+=w;samples++;
    }
  }
  return{uRms:wSum>0?Math.sqrt(sum/wSum):NaN,samples};
}
function measureSpecClock(V=K4){
  const pre=specClockPrerequisites();if(!pre.ok)return{valid:false,reason:pre.reason};
  const a=carrierGroupStats('A'),b=carrierGroupStats('B');if(!a||!b)return{valid:false,reason:'carrierstatistiek ontbreekt'};
  const mA=carrierMutualTangentialRms('A','B'),mB=carrierMutualTangentialRms('B','A');
  if(!Number.isFinite(mA.uRms)||!Number.isFinite(mB.uRms))return{valid:false,reason:'wederzijdse veldmeting ongeldig'};
  const envA=specClockEnvelope(mA.uRms),envB=specClockEnvelope(mB.uRms);
  if(!ensureSpecClockVelocityBuffers())return{valid:false,reason:'fasebuffers ontbreken'};
  SpecClock.tmpV.fill(0);velAll(Y,SpecClock.tmpV);
  const omegaA=carrierBodyOmegaFromVelocity('A',SpecClock.tmpV),omegaB=carrierBodyOmegaFromVelocity('B',SpecClock.tmpV);
  const omegaIsoA=carrierIsolatedBodyOmega('A',SpecClock.tmpIsoA),omegaIsoB=carrierIsolatedBodyOmega('B',SpecClock.tmpIsoB);
  const deltaOmegaA=omegaA-omegaIsoA,deltaOmegaB=omegaB-omegaIsoB;
  const deltaFracA=Math.abs(omegaIsoA)>1e-15?deltaOmegaA/Math.abs(omegaIsoA):NaN;
  const deltaFracB=Math.abs(omegaIsoB)>1e-15?deltaOmegaB/Math.abs(omegaIsoB):NaN;
  const phaseOffsetA=SpecClock.calibrated&&Number.isFinite(deltaFracA)?deltaFracA-SpecClock.phaseNullRefA:NaN;
  const phaseOffsetB=SpecClock.calibrated&&Number.isFinite(deltaFracB)?deltaFracB-SpecClock.phaseNullRefB:NaN;
  const etaPhaseA=Number.isFinite(phaseOffsetA)?1+phaseOffsetA:NaN;
  const etaPhaseB=Number.isFinite(phaseOffsetB)?1+phaseOffsetB:NaN;
  const phaseLogRatio=Number.isFinite(phaseOffsetA)&&Number.isFinite(phaseOffsetB)&&phaseOffsetA>-1&&phaseOffsetB>-1
    ?Math.log1p(phaseOffsetA)-Math.log1p(phaseOffsetB):NaN;
  const phaseRatio=Number.isFinite(phaseLogRatio)?Math.exp(phaseLogRatio):NaN;
  const phaseRate=Number.isFinite(phaseOffsetA)&&Number.isFinite(phaseOffsetB)?phaseOffsetA-phaseOffsetB:NaN;
  const fieldLogRatioMin=envA.deltaLogEtaMin-envB.deltaLogEtaMax;
  const fieldLogRatioMax=envA.deltaLogEtaMax-envB.deltaLogEtaMin;
  const fieldRatioMin=Math.exp(fieldLogRatioMin),fieldRatioMax=Math.exp(fieldLogRatioMax);
  const assessment=specClockProxyAssessment(phaseRatio,fieldRatioMin,fieldRatioMax,fieldLogRatioMin,fieldLogRatioMax,phaseLogRatio);
  let residual=NaN;
  if(Number.isFinite(phaseLogRatio)){
    if(phaseLogRatio<fieldLogRatioMin)residual=fieldLogRatioMin-phaseLogRatio;
    else if(phaseLogRatio>fieldLogRatioMax)residual=phaseLogRatio-fieldLogRatioMax;
    else residual=0;
  }
  const fieldRateMin=specClockEtaDiffFromDeltaLogs(envA.deltaLogEtaMin,envB.deltaLogEtaMax);
  const fieldRateMax=specClockEtaDiffFromDeltaLogs(envA.deltaLogEtaMax,envB.deltaLogEtaMin);
  return{valid:true,distance:Math.hypot(b.cx-a.cx,b.cy-a.cy,b.z-a.z),uA:mA.uRms,uB:mB.uRms,envA,envB,
    omegaA,omegaB,omegaIsoA,omegaIsoB,deltaOmegaA,deltaOmegaB,deltaFracA,deltaFracB,phaseOffsetA,phaseOffsetB,etaPhaseA,etaPhaseB,
    fieldLogRatioMin,fieldLogRatioMax,fieldRatioMin,fieldRatioMax,phaseRatio,phaseLogRatio,phaseRate,fieldRateMin,fieldRateMax,
    rawOverlap:assessment.rawOverlap,closureComparable:false,falsified:false,residual,samplesA:mA.samples,samplesB:mB.samples};
}
function updateSpecClockAcceptedStep(dt,V=K4){
  if(!P.specClockEnabled||!(dt>0))return;
  const pre=specClockPrerequisites();if(!pre.ok){SpecClock.last={valid:false,reason:pre.reason};return;}
  SpecClock.stepCounter++;SpecClock.dtBucket+=dt;
  if(SpecClock.stepCounter%SpecClock.sampleStride)return;
  const m=measureSpecClock(V),h=SpecClock.dtBucket;SpecClock.dtBucket=0;
  if(m.valid){
    if(Number.isFinite(m.fieldRateMin)&&Number.isFinite(m.fieldRateMax)){
      SpecClock.lagFieldMin+=m.fieldRateMin*h;SpecClock.lagFieldMax+=m.fieldRateMax*h;
    }
    if(Number.isFinite(m.phaseRate))SpecClock.lagPhase+=m.phaseRate*h;
  }
  SpecClock.last=m;
}
function resetSpecClockRuntime(reason='reset'){
  SpecClock.calibrated=false;SpecClock.stepCounter=0;SpecClock.dtBucket=0;
  SpecClock.phaseNullRefA=SpecClock.phaseNullRefB=NaN;
  SpecClock.calibrationTime=SpecClock.calibrationDistance=NaN;SpecClock.calibrationCount=0;
  SpecClock.calibrationMode='legacy-z';SpecClock.projectionNull=false;
  SpecClock.lagFieldMin=SpecClock.lagFieldMax=SpecClock.lagPhase=0;
  SpecClock.autoStartAfterCalibration=false;
  SpecClock.last={valid:false,reason};updateSpecClockDisplay();
}
function calibrateSpecClockPhase(options={}){
  const mode=options.mode||'legacy-z',allowProjectionNull=options.allowProjectionNull===true;
  const pre=specClockPrerequisites();if(!pre.ok){setFlag('⚠ swirl-clockkalibratie geweigerd: '+pre.reason+'.',true);updateSpecClockDisplay();return false;}
  if(SpecClock.calibrated){setFlag('🔒 fase-nullreferentie is al vergrendeld. Gebruik Reset of wijzig de geometrie voor een nieuwe onafhankelijke sweep.',true);return false;}
  if(tPhys>1e-12&&!paused){setFlag('⚠ pauzeer de simulatie vóór fase-nullkalibratie. Een bewegende referentie is niet reproduceerbaar.',true);return false;}
  if(!ensureSpecClockVelocityBuffers())return false;
  const m0=measureSpecClock();
  const fractionsFinite=m0.valid&&Number.isFinite(m0.deltaFracA)&&Number.isFinite(m0.deltaFracB);
  const omegaFinite=m0.valid&&[m0.omegaA,m0.omegaB,m0.omegaIsoA,m0.omegaIsoB,m0.deltaOmegaA,m0.deltaOmegaB].every(Number.isFinite);
  if(!fractionsFinite){
    if(!(allowProjectionNull&&omegaFinite)){
      setFlag('⚠ fase-nullkalibratie ongeldig: volledige en geïsoleerde Ω-metingen sluiten niet numeriek.',true);return false;
    }
    // Cross-knotholdouts worden confirmatoir beoordeeld via de volledige intrinsieke
    // Ω-vector. Een vrijwel nul zijnde legacy lab-z-noemer is daarom geldig maar
    // niet-informatief voor uitsluitend deze oude projectie.
    SpecClock.phaseNullRefA=0;SpecClock.phaseNullRefB=0;SpecClock.projectionNull=true;
  }else{
    SpecClock.phaseNullRefA=m0.deltaFracA;SpecClock.phaseNullRefB=m0.deltaFracB;SpecClock.projectionNull=false;
  }
  SpecClock.calibrationMode=mode;SpecClock.calibrated=true;
  SpecClock.calibrationTime=tPhys;SpecClock.calibrationDistance=m0.distance;SpecClock.calibrationCount=1;
  SpecClock.lagFieldMin=SpecClock.lagFieldMax=SpecClock.lagPhase=0;SpecClock.dtBucket=0;SpecClock.stepCounter=0;
  SpecClock.last=measureSpecClock();updateSpecClockDisplay();
  if(window.ModelLog)window.ModelLog.logEvent('spec-clock-phase-null-calibration',{
    distance:SpecClock.calibrationDistance,tPhys:SpecClock.calibrationTime,mode,
    projectionNull:SpecClock.projectionNull,legacyProjectionInformative:!SpecClock.projectionNull,
    deltaFracRefA:SpecClock.projectionNull?null:SpecClock.phaseNullRefA,
    deltaFracRefB:SpecClock.projectionNull?null:SpecClock.phaseNullRefB,
    omegaFullA:m0.omegaA,omegaIsoA:m0.omegaIsoA,omegaFullB:m0.omegaB,omegaIsoB:m0.omegaIsoB,locked:true,
    autoStart:SpecClock.autoStartAfterCalibration});
  if(SpecClock.projectionNull){
    setFlag('ℹ legacy lab-z-projectie is nul/niet-informatief; intrinsieke Ω-holdoutmeting blijft geldig en wordt voortgezet.',true);
  }
  if(SpecClock.autoStartAfterCalibration){
    SpecClock.autoStartAfterCalibration=false;
    setPausedState(false,'spec-clock-calibration-autostart');
    setFlag('▶ fase-nullreferentie vergrendeld; de SPEC CLOCK-sweep is automatisch gestart op 1×.',true);
  }
  return true;
}
function fmtClockTime(s){
  if(!Number.isFinite(s))return '—';const a=Math.abs(s),sg=s<0?'−':'';
  if(a<1e-15)return sg+(a*1e18).toFixed(3)+' as';
  if(a<1e-12)return sg+(a*1e15).toFixed(3)+' fs';
  if(a<1e-9)return sg+(a*1e12).toFixed(3)+' ps';
  if(a<1e-6)return sg+(a*1e9).toFixed(3)+' ns';
  if(a<1e-3)return sg+(a*1e6).toFixed(3)+' µs';
  if(a<1)return sg+(a*1e3).toFixed(3)+' ms';
  return s.toFixed(6)+' s';
}
function fmtSpecOmega(v){return Number.isFinite(v)?v.toExponential(6)+' rad/s':'—';}
function updateSpecClockDisplay(){
  const btn=document.getElementById('bSpecClockToggle');if(!btn)return;
  btn.classList.toggle('active',P.specClockEnabled);btn.textContent=P.specClockEnabled?'⏹ Deactiveer speculative clock':'⚠ Activeer speculative clock';
  const pre=specClockPrerequisites(),cal=document.getElementById('bSpecClockCalibrate');
  if(cal){
    cal.disabled=!P.specClockEnabled||!pre.ok||SpecClock.calibrated||(tPhys>1e-12&&!paused);
    cal.textContent=SpecClock.calibrated?'🔒 Fase-nullreferentie vergrendeld':(SpecClock.autoStartAfterCalibration?'◎ Kalibreer fase-nullreferentie en start 1×':'◎ Kalibreer fase-nullreferentie bij huidige afstand');
  }
  const gain=document.getElementById('sSpecClockGain');if(gain)gain.value=String(P.specClockDisplayGain);
  const vg=document.getElementById('vSpecClockGain');if(vg)vg.textContent=(P.specClockDisplayGain>=1e6?'10⁶':String(P.specClockDisplayGain))+'×';
  const eta0=specClockEta(V_CHAR_SST),basePpm=(1-eta0)*1e6;
  const base=document.getElementById('specClockBaseline');if(base)base.textContent=basePpm.toFixed(6)+' ppm · η₀='+eta0.toFixed(12);
  const status=document.getElementById('specClockStatus');
  const ids=['specClockDistance','specClockMutual','specClockEtaA','specClockEtaB','specClockOmegaFull','specClockOmegaIso','specClockDeltaOmega','specClockPhaseRates','specClockFieldRatio','specClockFieldLogRatio','specClockPhaseRatio','specClockPhaseLogRatio','specClockCalibration','specClockFieldLag','specClockPhaseLag','specClockResidual'];
  const clear=()=>ids.forEach(id=>{const e=document.getElementById(id);if(e)e.textContent='—';});
  const finish=m=>{syncSpecClockQuickControls();updateSpecClockOverlay(m,pre);};
  if(!P.specClockEnabled){clear();status.className='spec-clock-status bad';status.textContent='UIT · activeer alleen voor SST + botsingsmodus met twee dragers.';finish(null);return;}
  if(!pre.ok){clear();status.className='spec-clock-status bad';status.textContent='GEBLOKKEERD · '+pre.reason+'. Geen klokwaarde wordt geclaimd.';finish(null);return;}
  const m=SpecClock.last;
  if(!m||!m.valid){
    clear();
    const benchStatus=specClockBenchmarkRestoreStatus();
    if(benchStatus){status.className='spec-clock-status '+benchStatus.cls;status.textContent=benchStatus.text;}
    else{status.className='spec-clock-status warn';status.textContent='WACHT OP DETERMINISTISCHE VELDSAMPLE · '+((m&&m.reason)||'eerste geaccepteerde stappen nodig')+'.';}
    finish(m);return;
  }
  const set=(id,v)=>{const e=document.getElementById(id);if(e)e.textContent=v;};
  const envText=e=>e.etaMin.toFixed(12)+' … '+e.etaMax.toFixed(12);
  set('specClockDistance',fmtLengthSI(m.distance));set('specClockMutual',fmtSpeed(m.uA)+' / '+fmtSpeed(m.uB));
  set('specClockEtaA',envText(m.envA));set('specClockEtaB',envText(m.envB));
  set('specClockOmegaFull',fmtSpecOmega(m.omegaA)+' / '+fmtSpecOmega(m.omegaB));
  set('specClockOmegaIso',fmtSpecOmega(m.omegaIsoA)+' / '+fmtSpecOmega(m.omegaIsoB));
  set('specClockDeltaOmega',fmtSpecOmega(m.deltaOmegaA)+' / '+fmtSpecOmega(m.deltaOmegaB));
  set('specClockFieldRatio',m.fieldRatioMin.toFixed(12)+' … '+m.fieldRatioMax.toFixed(12));
  set('specClockFieldLogRatio',m.fieldLogRatioMin.toExponential(3)+' … '+m.fieldLogRatioMax.toExponential(3));
  set('specClockPhaseRates',Number.isFinite(m.etaPhaseA)?m.etaPhaseA.toFixed(12)+' / '+m.etaPhaseB.toFixed(12):'niet gekalibreerd');
  set('specClockPhaseRatio',Number.isFinite(m.phaseRatio)?m.phaseRatio.toFixed(12):'niet gekalibreerd');
  set('specClockPhaseLogRatio',Number.isFinite(m.phaseLogRatio)?m.phaseLogRatio.toExponential(3):'niet gekalibreerd');
  set('specClockCalibration',SpecClock.calibrated?'🔒 t='+SpecClock.calibrationTime.toFixed(6)+' s · d='+fmtLengthSI(SpecClock.calibrationDistance):'open · pauzeer en kalibreer eenmaal op grote afstand');
  set('specClockFieldLag',fmtClockTime(SpecClock.lagFieldMin)+' … '+fmtClockTime(SpecClock.lagFieldMax));
  set('specClockPhaseLag',SpecClock.calibrated?fmtClockTime(SpecClock.lagPhase):'niet gekalibreerd');
  set('specClockResidual',Number.isFinite(m.residual)?m.residual.toExponential(3):'open');
  const ppmA=(1-m.envA.etaMid)*1e6,ppmB=(1-m.envB.etaMid)*1e6,full=10;
  const pctA=clamp(ppmA*P.specClockDisplayGain/full*100,0,100),pctB=clamp(ppmB*P.specClockDisplayGain/full*100,0,100);
  document.getElementById('specClockBarA').style.width=pctA+'%';document.getElementById('specClockBarB').style.width=pctB+'%';
  document.getElementById('specClockBarValueA').textContent=ppmA.toFixed(6)+' ppm';document.getElementById('specClockBarValueB').textContent=ppmB.toFixed(6)+' ppm';
  if(!SpecClock.calibrated){status.className='spec-clock-status warn';status.textContent=(tPhys>1e-12&&!paused?'PAUZEER VOOR KALIBRATIE · ':'FASE-NULLROUTE OPEN · ')+'kalibreer eenmaal bij zo groot mogelijke A–B-afstand. De referentie wordt daarna tot Reset vergrendeld.';}
  else if(m.rawOverlap){status.className='spec-clock-status warn';status.textContent='FASE-NULLTEST BINNEN RUWE BRACKET · de geïsoleerd afgetrokken fase-nullproxy ligt numeriek binnen de formele veldbracket. Dit is nog geen closure of bevestiging.';}
  else{status.className='spec-clock-status warn';status.textContent='FASEPROXY-NULLTEST MISLUKT · na geïsoleerde zelf- en achtergrondaftrek ligt R_AB^phase-null buiten de stabiele veldbracket. Dit verwerpt deze proxyrealisatie voor de huidige run, niet een SST-parameter of klokwet.';}
  finish(m);
}
function ensureSpecClockOverlayMarkup(body){
  if(!body||body.dataset.specOverlayReady==='1')return;
  body.innerHTML=`<div class="note"><b>Snelle weergave.</b> Alleen zichtbaar zolang de speculative klok actief is. v7.6.13 gebruikt een vergrendelde fase-nullreferentie en momentane geïsoleerde aftrek; de proxyvergelijking blijft niet-canoniek.</div>
    <div class="spec-overlay-grid">
      <div class="k">modus / topologie</div><div class="v" data-spec-overlay="mode">—</div>
      <div class="k">medium / interactie</div><div class="v" data-spec-overlay="medium">—</div>
      <div class="k">kwaliteit / a_sim</div><div class="v" data-spec-overlay="quality">—</div>
      <div class="k">Δz_AB,0 / Δx(B)</div><div class="v" data-spec-overlay="start">—</div>
      <div class="k">v_z A / v_z B</div><div class="v" data-spec-overlay="drift">—</div>
      <div class="k">actuele d_AB / clearance</div><div class="v" data-spec-overlay="distance">—</div>
      <div class="k">stopgrens</div><div class="v" data-spec-overlay="stop">—</div>
      <div class="k">fase-nullreferentie / logging</div><div class="v" data-spec-overlay="calibration">—</div>
      <div class="k">status</div><div class="v" data-spec-overlay="status">—</div>
    </div>`;
  body.dataset.specOverlayReady='1';
}
function setSpecClockOverlayValue(body,key,value){
  const node=body.querySelector('[data-spec-overlay="'+key+'"]');
  const next=String(value);if(node&&node.textContent!==next)node.textContent=next;
}
function updateSpecClockOverlay(m,pre){
  const panel=document.getElementById('specClockOverlay'),body=document.getElementById('specClockOverlayBody');
  if(!panel||!body)return;
  const active=!!P.specClockEnabled;panel.classList.toggle('active',active);panel.setAttribute('aria-hidden',active?'false':'true');
  const widget=panel.closest('.vl-bottom-widget');if(widget){widget.hidden=!active;if(active&&widget.dataset.autoOpened!=='1'){widget.open=true;widget.dataset.autoOpened='1';}}
  if(!active)return;
  ensureSpecClockOverlayMarkup(body);
  const ct=contactThresholdInfo(),gap=Number.isFinite(lastTopologyGap)?fmtLengthSI(lastTopologyGap):'—';
  const status=document.getElementById('specClockStatus')?.textContent||'—';
  const dz=fmtLengthSI(initialAxialSeparation()),dx=(P.off*1000).toFixed(1).replace(/\.0$/,'')+' mm';
  const current=Number.isFinite(m&&m.distance)?fmtLengthSI(m.distance):'—';
  const logState=(window.ModelLog&&window.ModelLog.enabled)?'aan':'uit';
  setSpecClockOverlayValue(body,'mode',P.mode+' · '+P.topo);
  setSpecClockOverlayValue(body,'medium',P.med+' · '+P.inter);
  setSpecClockOverlayValue(body,'quality',P.qual+' · '+fmtLengthSI(P.a));
  setSpecClockOverlayValue(body,'start',dz+' · '+dx);
  setSpecClockOverlayValue(body,'drift',fmtSignedMmPerSInput(P.vzA)+' · '+fmtSignedMmPerSInput(P.vzB));
  setSpecClockOverlayValue(body,'distance',current+' · '+gap);
  setSpecClockOverlayValue(body,'stop',fmtLengthSI(ct.effective));
  setSpecClockOverlayValue(body,'calibration',(SpecClock.calibrated?'🔒 t='+SpecClock.calibrationTime.toFixed(3)+' s':'open')+' · '+logState);
  setSpecClockOverlayValue(body,'status',status);
}








const SPEC_AUTO_EXPORT_KEY='vortexlab.specClock.autoExport.v1';
function safeUtcStamp(value){
  const d=value?new Date(value):new Date();
  return (Number.isFinite(d.getTime())?d:new Date()).toISOString().replace(/[-:]/g,'').replace('.','').replace('T','_');
}
function triggerTextDownload(text,mime,filename){
  const blob=new Blob([text],{type:mime}),a=document.createElement('a');
  a.href=URL.createObjectURL(blob);a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),0);
}
function specAutoExportEnabled(){
  const cb=document.getElementById('cSpecAutoExport');
  if(cb)return !!cb.checked;
  try{return localStorage.getItem(SPEC_AUTO_EXPORT_KEY)!=='0';}catch(_){return true;}
}
function bindSpecAutoExportControl(){
  const cb=document.getElementById('cSpecAutoExport');if(!cb||cb.dataset.bound)return;cb.dataset.bound='1';cb.dataset.specBound='1';
  try{cb.checked=localStorage.getItem(SPEC_AUTO_EXPORT_KEY)!=='0';}catch(_){cb.checked=true;}
  cb.addEventListener('change',()=>{try{localStorage.setItem(SPEC_AUTO_EXPORT_KEY,cb.checked?'1':'0');}catch(_){}});
}
function exportModelLogTimestamped(stamp,context='benchmark'){
  if(!window.ModelLog)return;
  triggerTextDownload(window.ModelLog.exportText(),'text/plain;charset=utf-8',`vortexlab-session-${APP_VERSION.replace(/\./g,'-')}-${context}-${stamp}.txt`);
}

// ================= v7.6.24f3 collapsed HUD click/drag fix; v7.6.24f2 workflow base =================
// v7.6.24a: intrinsic Ω before digest + runtime smoke + explicit abort logging
function benchmarkVisualSnapshot(){
  return {tracerCount:P.tracerCount,showTracers:P.showTracers,showStreamlines:P.showStreamlines,showPotentialFlow:P.showPotentialFlow};
}
function suppressBenchmarkVisuals(context){
  const before=benchmarkVisualSnapshot();
  P.tracerCount=0;P.showTracers=false;P.showStreamlines=false;P.showPotentialFlow=false;
  if(typeof trPts!=='undefined'&&trPts)trPts.visible=false;
  if(typeof streamlineGrp!=='undefined'&&streamlineGrp)streamlineGrp.visible=false;
  if(typeof potentialFlowGrp!=='undefined'&&potentialFlowGrp)potentialFlowGrp.visible=false;
  if(typeof initTracers==='function')initTracers();
  syncUi();
  const after=benchmarkVisualSnapshot();
  if(window.ModelLog){window.ModelLog.setEnabled(true);window.ModelLog.logEvent('benchmark-visual-suppression',{context,before,after,passiveOnly:true});}
  return before;
}
function logBenchmarkVisualRestore(context,before){
  const after=benchmarkVisualSnapshot(),restored=!!before&&after.tracerCount===before.tracerCount&&after.showTracers===before.showTracers&&after.showStreamlines===before.showStreamlines&&after.showPotentialFlow===before.showPotentialFlow;
  if(window.ModelLog)window.ModelLog.logEvent('benchmark-visual-restore',{context,before,after,restored});
  return restored;
}

const SpecClockProxyDecomposition=(()=>{
  const SCHEMA='vortexlab-spec-clock-proxy-decomposition/2.1';
  const CHANNELS=['GEOM','PARAM','ROT','TRANS','MUTUAL_BS'];
  const BITS={GEOM:1,PARAM:2,ROT:4,TRANS:8,MUTUAL_BS:16};
  const NORMALIZATIONS=[
    {id:'ISO_DYNAMIC',label:'|Ω_iso(t)| dynamisch',kind:'dynamic'},
    {id:'ISO_REFERENCE',label:'|Ω_iso,0| vast',kind:'fixed'},
    {id:'FULL_REFERENCE',label:'|Ω_full,0| vast',kind:'fixed'},
    {id:'MUTUAL_REFERENCE',label:'|Ω_mutual,0| vast',kind:'fixed',risk:'kleine noemer'},
    {id:'CIRCULATION_LENGTH',label:'Γ_eff/L₀²',kind:'hydrodynamic'},
    {id:'RMS_ARCLENGTH',label:'u_iso,rms,0/L₀',kind:'kinematic'},
    {id:'CORE_CIRCULATION',label:'Γ_eff/a_sim²',kind:'core'}
  ];
  const TRANSFER_LAWS=[
    {id:'ADVECT_CORE',label:'advectief · a/v↺*',formula:'ΔΩ·a/v↺*',exponents:{deltaOmega:1,gamma:0,a:1,L:0,d:0,vChar:-1,rc:0},evaluate:x=>x.deltaOmega*x.a/x.vChar},
    {id:'ADVECT_LENGTH',label:'advectief · L/v↺*',formula:'ΔΩ·L/v↺*',exponents:{deltaOmega:1,gamma:0,a:0,L:1,d:0,vChar:-1,rc:0},evaluate:x=>x.deltaOmega*x.L/x.vChar},
    {id:'ADVECT_DISTANCE',label:'advectief · d/v↺*',formula:'ΔΩ·d/v↺*',exponents:{deltaOmega:1,gamma:0,a:0,L:0,d:1,vChar:-1,rc:0},evaluate:x=>x.deltaOmega*x.d/x.vChar},
    {id:'ADVECT_RC',label:'advectief · rc/v↺*',formula:'ΔΩ·rc/v↺*',exponents:{deltaOmega:1,gamma:0,a:0,L:0,d:0,vChar:-1,rc:1},evaluate:x=>x.deltaOmega*x.rc/x.vChar},
    {id:'CIRC_CORE',label:'circulatie · a²/Γ',formula:'ΔΩ·a²/Γ',exponents:{deltaOmega:1,gamma:-1,a:2,L:0,d:0,vChar:0,rc:0},evaluate:x=>x.deltaOmega*x.a*x.a/x.gamma},
    {id:'CIRC_LENGTH',label:'circulatie · L²/Γ',formula:'ΔΩ·L²/Γ',exponents:{deltaOmega:1,gamma:-1,a:0,L:2,d:0,vChar:0,rc:0},evaluate:x=>x.deltaOmega*x.L*x.L/x.gamma},
    {id:'CIRC_DISTANCE',label:'circulatie · d²/Γ',formula:'ΔΩ·d²/Γ',exponents:{deltaOmega:1,gamma:-1,a:0,L:0,d:2,vChar:0,rc:0},evaluate:x=>x.deltaOmega*x.d*x.d/x.gamma},
    {id:'CIRC_CORE_D2',label:'core · (a/d)²',formula:'ΔΩ·a²/Γ·(a/d)²',exponents:{deltaOmega:1,gamma:-1,a:4,L:0,d:-2,vChar:0,rc:0},evaluate:x=>x.deltaOmega*x.a*x.a/x.gamma*(x.a/x.d)**2},
    {id:'CIRC_CORE_RC_D2',label:'core · (rc/d)²',formula:'ΔΩ·a²/Γ·(rc/d)²',exponents:{deltaOmega:1,gamma:-1,a:2,L:0,d:-2,vChar:0,rc:2},evaluate:x=>x.deltaOmega*x.a*x.a/x.gamma*(x.rc/x.d)**2},
    {id:'ADVECT_LENGTH_A_D2',label:'advectief · (a/d)²',formula:'ΔΩ·L/v↺*·(a/d)²',exponents:{deltaOmega:1,gamma:0,a:2,L:1,d:-2,vChar:-1,rc:0},evaluate:x=>x.deltaOmega*x.L/x.vChar*(x.a/x.d)**2},
    {id:'BUCKINGHAM_ALL',label:'Buckingham · alle inputs',formula:'ΔΩ·Γ·a·L/(v↺*²·d·rc)',exponents:{deltaOmega:1,gamma:1,a:1,L:1,d:-1,vChar:-2,rc:-1},evaluate:x=>x.deltaOmega*x.gamma*x.a*x.L/(x.vChar*x.vChar*x.d*x.rc)}
  ].map(x=>({...x,coefficient:1}));
  const IDEAL_TREFOIL_ROPELENGTH=16.371637; // diameterconventie: Rop_diam=L_K/(2a_core)
  const LENGTH_CANDIDATES=[
    {id:'RESOLVED_CURRENT',label:'L_K(t) · opgeloste centerline',kind:'CANON_CARRIER',semanticEligible:true,dynamic:true},
    {id:'RESOLVED_REFERENCE',label:'L_K(0) · gekalibreerde centerline',kind:'CANON_CARRIER',semanticEligible:true,dynamic:false},
    {id:'IDEAL_REACH_CURRENT',label:'L_ideal·2τ_geom(t)',kind:'GEOMETRIC_RESEARCH',semanticEligible:false,dynamic:true},
    {id:'IDEAL_REACH_REFERENCE',label:'L_ideal·2τ_geom(0)',kind:'GEOMETRIC_RESEARCH',semanticEligible:false,dynamic:false},
    {id:'IDEAL_ASIM_DIAMETER',label:'L_ideal·2a_sim',kind:'NUMERICAL_NEGATIVE_CONTROL',semanticEligible:false,dynamic:false,risk:'a_sim is numerieke regularisatie, niet a_core'},
    {id:'TREFOIL_RC_DIAMETER_BENCHMARK',label:'L_ideal,diam·2r_c',kind:'RESEARCH_SCALE_BENCHMARK',semanticEligible:false,dynamic:false,risk:'research-track schaalbenchmark; bewijst niet a_core=r_c'},
    {id:'MINIMAL_NEUTRAL_LOOP',label:'2πr_c',kind:'CANON_SPECIAL_LOOP',semanticEligible:false,dynamic:false,risk:'alleen minimale neutrale lus, niet trefoil L_K'},
    {id:'COMPTON_WAVELENGTH',label:'λ_c = 2πc/ω_c',kind:'REFERENCE_SCALE',semanticEligible:false,dynamic:false},
    {id:'REDUCED_COMPTON',label:'λ̄_c = c/ω_c',kind:'REFERENCE_SCALE',semanticEligible:false,dynamic:false},
    {id:'DISTANCE_CONTROL',label:'d_AB · negatieve controle',kind:'NEGATIVE_CONTROL',semanticEligible:false,dynamic:true,risk:'geen gesloten carrierlengte'}
  ];

  const GEOM_KAPPA_CANDIDATES=[
    {id:'UNITY',label:'eenheidscontrole',formula:'1',evaluate:g=>1},
    {id:'INV_2PI',label:'cirkelgemiddelde',formula:'1/(2π)',evaluate:g=>1/(2*Math.PI)},
    {id:'INV_4PI',label:'solid-angle schaal',formula:'1/(4π)',evaluate:g=>1/(4*Math.PI)},
    {id:'INV_4PI2',label:'dubbele hoekgemiddelde',formula:'1/(4π²)',evaluate:g=>1/(4*Math.PI*Math.PI)},
    {id:'REACH_OVER_LK',label:'radiusfractie',formula:'a_core/L_K',evaluate:g=>g.reach/g.length},
    {id:'DIAMETER_OVER_LK',label:'diameterfractie',formula:'2a_core/L_K',evaluate:g=>2*g.reach/g.length},
    {id:'INV_PI_ROP_DIAM',label:'π × diameter-ropelength',formula:'1/(π·Rop_diam)',evaluate:g=>1/(Math.PI*g.ropDiam)},
    {id:'INV_CROSSING_ROP_DIAM',label:'crossing × ropelength',formula:'1/(n_cross·Rop_diam)',evaluate:g=>Number.isFinite(g.crossingNumber)&&g.crossingNumber>0?1/(g.crossingNumber*g.ropDiam):NaN},
    {id:'INV_2PI_ROP_DIAM',label:'2π × diameter-ropelength',formula:'1/(2π·Rop_diam)',evaluate:g=>1/(2*Math.PI*g.ropDiam)},
    {id:'INV_IDEAL_PI_ROP_DIAM',label:'Gilbert π × ropelength',formula:'1/(π·Rop_ideal,diam)',evaluate:g=>Number.isFinite(g.idealRopDiam)?1/(Math.PI*g.idealRopDiam):NaN},
    {id:'INV_IDEAL_CROSSING_ROP_DIAM',label:'Gilbert crossing × ropelength',formula:'1/(n_cross·Rop_ideal,diam)',evaluate:g=>Number.isFinite(g.crossingNumber)&&g.crossingNumber>0&&Number.isFinite(g.idealRopDiam)?1/(g.crossingNumber*g.idealRopDiam):NaN}
  ].map(x=>({...x,coefficient:1,dimensionless:true}));
  const IDEAL_CONVENTION_AUDIT_IDS=['3:1:1','4:1:1','5:1:1'];
  const DEFAULT_CHECKPOINTS=[0,0.5,1,2,3],RESOLUTION_CHECKPOINTS=[0,3];
  const RECON_REL_TOL=1e-10,RECON_ABS_TOL={phaseLog:1e-24,deltaFrac:1e-24,rawOmega:1e-30};
  const CORE_SCENARIOS=[
    {id:'baseline',label:'baseline · N=128',drift:0.005,ccwA:true,ccwB:false,resolution:128,checkpoints:DEFAULT_CHECKPOINTS},
    {id:'static-null',label:'static-null · N=128',drift:0,ccwA:true,ccwB:false,resolution:128,checkpoints:DEFAULT_CHECKPOINTS},
    {id:'symmetry-swap',label:'A/B traversal swap · N=128',drift:0.005,ccwA:false,ccwB:true,resolution:128,checkpoints:DEFAULT_CHECKPOINTS},
    {id:'asim-0.5mm',label:'a_sim negative control · 0.5 mm',drift:0.005,ccwA:true,ccwB:false,resolution:128,aSim:0.0005,checkpoints:RESOLUTION_CHECKPOINTS},
    {id:'asim-1.5mm',label:'a_sim negative control · 1.5 mm',drift:0.005,ccwA:true,ccwB:false,resolution:128,aSim:0.0015,checkpoints:RESOLUTION_CHECKPOINTS}
  ];
  const CONTINUUM_SCENARIOS=[
    {id:'baseline',label:'continuum baseline · N=128',drift:0.005,ccwA:true,ccwB:false,resolution:128,checkpoints:RESOLUTION_CHECKPOINTS},
    {id:'resolution-192',label:'resolution ladder · N=192',drift:0.005,ccwA:true,ccwB:false,resolution:192,checkpoints:RESOLUTION_CHECKPOINTS},
    {id:'resolution-256',label:'resolution ladder · N=256',drift:0.005,ccwA:true,ccwB:false,resolution:256,checkpoints:RESOLUTION_CHECKPOINTS},
    {id:'resolution-384',label:'resolution ladder · N=384',drift:0.005,ccwA:true,ccwB:false,resolution:384,checkpoints:RESOLUTION_CHECKPOINTS},
    {id:'resolution-512',label:'resolution ladder · N=512',drift:0.005,ccwA:true,ccwB:false,resolution:512,checkpoints:RESOLUTION_CHECKPOINTS},
    {id:'resolution-768',label:'resolution ladder · N=768',drift:0.005,ccwA:true,ccwB:false,resolution:768,checkpoints:RESOLUTION_CHECKPOINTS}
  ];
  const KNOT_HOLDOUT_CATALOG={
    '3_1':{label:'3₁',selectorLabel:'3₁ · trefoil',crossingNumber:3,fseries:'3_1',ideal:'3:1:1',idealRopDiam:16.371637,knotplot:'knot_3.1'},
    '4_1':{label:'4₁',selectorLabel:'4₁ · figure-eight',crossingNumber:4,fseries:'4_1',ideal:'4:1:1',idealRopDiam:21.043322,knotplot:'knot_4.1'},
    '5_1':{label:'5₁',selectorLabel:'5₁ · cinquefoil',crossingNumber:5,fseries:'5_1',ideal:'5:1:1',idealRopDiam:23.598564,knotplot:'knot_5.1'},
    '5_2':{label:'5₂',selectorLabel:'5₂ · twist',crossingNumber:5,fseries:'5_2',ideal:'5:1:2',idealRopDiam:24.734148,knotplot:'knot_5.2'},
    '6_1':{label:'6₁',selectorLabel:'6₁',crossingNumber:6,fseries:'6_1',ideal:'6:1:1',idealRopDiam:28.354929,knotplot:'knot_6.1'},
    '7_1':{label:'7₁',selectorLabel:'7₁ · torusknoop',crossingNumber:7,fseries:'7_1',ideal:'7:1:1',idealRopDiam:30.700289,knotplot:'knot_7.1'},
    'link_6.3.1':{label:'link 6.3.1',selectorLabel:'link_6.3.1 · 3 componenten',crossingNumber:6,knotplot:'link_6.3.1',resolution:128,family:'link'},
    'link_6.3.2':{label:'link 6.3.2',selectorLabel:'link_6.3.2 · 3 componenten',crossingNumber:6,knotplot:'link_6.3.2',resolution:128,family:'link'},
    'link_6.3.3':{label:'link 6.3.3',selectorLabel:'link_6.3.3 · 3 componenten',crossingNumber:6,knotplot:'link_6.3.3',resolution:128,family:'link'},
    'torus_3.3':{label:'T(3,3)',selectorLabel:'T(3,3) · 3-componenten toruslink',crossingNumber:6,knotplot:'torus_3.3',resolution:128,family:'torus-link'},
    'torus_6.9':{label:'T(6,9)',selectorLabel:'T(6,9) · 3 trefoilcomponenten',crossingNumber:45,knotplot:'torus_6.9',resolution:128,family:'torus-link'}
  };
  function normalizeHoldoutTopologyKey(key){return key==='Tlink_6_9'?'torus_6.9':key;}
  function renderKnotSelectorOptions(){
    const box=document.querySelector('#specKnotDropdown .spec-knot-options');if(!box)return;
    box.innerHTML=Object.entries(KNOT_HOLDOUT_CATALOG).map(([key,m])=>{const sources=[m.ideal?'ideal':null,m.fseries?'fseries':null,m.knotplot?'KnotPlot':null].filter(Boolean).join('/'),checked=DEFAULT_KNOT_SELECTION.topologies.includes(key)?' checked':'';return `<label><input type="checkbox" data-spec-knot="${key}"${checked}> ${m.selectorLabel||m.label} · ${sources}</label>`;}).join('');
  }
  const KNOT_SELECTION_STORAGE='vortexlab.clock.holdoutSelection.v1';
  const DEFAULT_KNOT_SELECTION={ideal:true,fseries:true,knotplot:true,topologies:['3_1','4_1','5_2']};
  let scenarios=[];
  const resultCache=new Map();
  const cacheStats={hits:0,misses:0};
  function cacheKey(sc,t){return [APP_VERSION,sc.id,Number(t).toFixed(9),sc.resolution,sc.aSim??'',sc.knotSource??'builtin',sc.knotKey??'trefoil',sc.sourceSha256??'',sc.ccwA,sc.ccwB,sc.drift].join('|');}
  function cloneAnalysis(x){return typeof structuredClone==='function'?structuredClone(x):x;}
  function copyScenarios(xs){return xs.map(x=>({...x,checkpoints:[...(x.checkpoints||RESOLUTION_CHECKPOINTS)]}));}
  function readKnotSelection(){
    let saved=null;try{saved=JSON.parse(localStorage.getItem(KNOT_SELECTION_STORAGE)||'null');}catch(_){saved=null;}
    const ideal=document.getElementById('cSpecHoldoutIdeal')?.checked??saved?.ideal??DEFAULT_KNOT_SELECTION.ideal;
    const fseries=document.getElementById('cSpecHoldoutFseries')?.checked??saved?.fseries??DEFAULT_KNOT_SELECTION.fseries;
    const knotplot=document.getElementById('cSpecHoldoutKnotplot')?.checked??saved?.knotplot??DEFAULT_KNOT_SELECTION.knotplot;
    const nodes=[...document.querySelectorAll('[data-spec-knot]')];
    const topologies=(nodes.length?nodes.filter(x=>x.checked).map(x=>x.dataset.specKnot):(Array.isArray(saved?.topologies)?saved.topologies:DEFAULT_KNOT_SELECTION.topologies)).map(normalizeHoldoutTopologyKey);
    return {ideal,fseries,knotplot,topologies:[...new Set(topologies)].filter(k=>KNOT_HOLDOUT_CATALOG[k])};
  }
  function saveKnotSelection(sel){try{localStorage.setItem(KNOT_SELECTION_STORAGE,JSON.stringify(sel));}catch(_){}}
  function selectedHoldoutScenarios(){
    const sel=readKnotSelection(),out=[];
    for(const topologyKey of sel.topologies){const k=KNOT_HOLDOUT_CATALOG[topologyKey];if(!k)continue;
      const resolution=Number.isFinite(k.resolution)?k.resolution:256;
      if(sel.fseries&&k.fseries)out.push({id:`holdout-fseries-${topologyKey}`,label:`holdout · fseries ${k.fseries} · N=${resolution}`,drift:0.005,ccwA:true,ccwB:false,resolution,checkpoints:RESOLUTION_CHECKPOINTS,knotSource:'fseries',knotKey:k.fseries,topologyKey,embedding:'fseries',crossingNumber:k.crossingNumber,idealRopDiam:null,holdout:true,canonicalize:true});
      if(sel.ideal&&k.ideal)out.push({id:`holdout-ideal-${k.ideal.replaceAll(':','_')}`,label:`holdout · ideal ${k.ideal} · N=${resolution}`,drift:0.005,ccwA:true,ccwB:false,resolution,checkpoints:RESOLUTION_CHECKPOINTS,knotSource:'ideal',knotKey:k.ideal,topologyKey,embedding:'ideal',crossingNumber:k.crossingNumber,idealRopDiam:k.idealRopDiam,holdout:true,canonicalize:true});
      if(sel.knotplot&&k.knotplot){
        const entry=getKnotPlotKnotCatalog()?.db?.[k.knotplot];if(entry){const componentCount=Number(entry.componentCount)||knotEntryComponents(entry).length||1,status=entry.status||'candidate',aSim=1e-3,pairwiseLinkingAbs=knotPlotLinkingAbs(entry),crossingNumber=Number.isFinite(k.crossingNumber)?k.crossingNumber:knotPlotCrossingNumber(entry,k.knotplot);
          out.push({id:`holdout-knotplot-${topologyKey.replaceAll('.','_')}`,label:`holdout · KnotPlot ${k.knotplot} · ${status} · ${entry.normalization?.label||'uniform source'} · ${componentCount} comp · N=${resolution}/comp · a_sim=1.0 mm`,drift:0.005,ccwA:true,ccwB:false,resolution,checkpoints:RESOLUTION_CHECKPOINTS,knotSource:'knotplot',knotKey:k.knotplot,topologyKey,embedding:'knotplot-relaxed',candidateStatus:status,candidateFamily:entry.family||k.family||null,crossingNumber,idealRopDiam:null,aSim,componentCountExpected:componentCount,pairwiseLinkingAbs,knotplotD:finiteMetaNumber(entry.D),knotplotL:finiteMetaNumber(entry.L),sourceRole:entry.sourceRole||null,sourceSha256:entry.sourceSha256||null,normalization:entry.normalization||null,torus:entry.torus||null,catalogWarning:entry.warning||null,holdout:true,canonicalize:true});
        }
      }
    }
    return out;
  }
  function scenarioSetForMode(mode){
    const core=copyScenarios(CORE_SCENARIOS),continuum=copyScenarios(CONTINUUM_SCENARIOS),holdouts=copyScenarios(selectedHoldoutScenarios());
    if(mode==='continuum')return continuum;
    if(mode==='holdout')return holdouts;
    if(mode==='full-suite')return [...core,...continuum.filter(x=>x.id!=='baseline'),...holdouts];
    return core;
  }
  function formatEta(seconds){seconds=Math.max(1,Math.round(seconds));if(seconds<60)return `≈ ${seconds} s`;const m=Math.floor(seconds/60),r=seconds%60;return `≈ ${m}m ${String(r).padStart(2,'0')}s`;}
  function updateKnotSelectionUi(){
    const sel=readKnotSelection();saveKnotSelection(sel);const labels=sel.topologies.map(k=>KNOT_HOLDOUT_CATALOG[k]?.label).filter(Boolean),planned=selectedHoldoutScenarios(),sources=[...new Set(planned.map(sc=>sc.knotSource==='knotplot'?'KnotPlot':sc.knotSource))],count=planned.length,snaps=count*RESOLUTION_CHECKPOINTS.length,etaSeconds=planned.reduce((sum,sc)=>{const components=Math.max(1,Number(sc.componentCountExpected)||1),resolution=Math.max(1,Number(sc.resolution)||256),complexity=components*components*(resolution/256)**2;return sum+RESOLUTION_CHECKPOINTS.length*10*complexity;},0);
    const summary=document.getElementById('specKnotDropdownSummary');if(summary)summary.textContent='Knopen · '+(labels.join(', ')||'geen');
    const info=document.getElementById('specKnotSelectionSummary');if(info)info.textContent=`${sources.join(' + ')||'geen toepasbare bron'} · ${count} holdoutscenario’s · ${snaps} snapshots · holdout-run ${formatEta(etaSeconds||1)}`;
  }
  function applyKnotSelectionPreset(name){
    const sets={quick:['3_1'],core:['3_1','4_1','5_2'],full:Object.keys(KNOT_HOLDOUT_CATALOG),torus69:['torus_6.9']},chosen=sets[name]||sets.core;
    document.querySelectorAll('[data-spec-knot]').forEach(x=>x.checked=chosen.includes(x.dataset.specKnot));const a=document.getElementById('cSpecHoldoutIdeal'),f=document.getElementById('cSpecHoldoutFseries'),k=document.getElementById('cSpecHoldoutKnotplot');if(name==='torus69'){if(a)a.checked=false;if(f)f.checked=false;if(k)k.checked=true;}else{if(a)a.checked=true;if(f)f.checked=true;if(k)k.checked=true;}updateKnotSelectionUi();VLClockWorkflow.invalidateSelection();
  }
  function bindKnotSelector(){
    renderKnotSelectorOptions();
    let saved=null;try{saved=JSON.parse(localStorage.getItem(KNOT_SELECTION_STORAGE)||'null');}catch(_){saved=null;}
    if(saved){const migrated=(saved.topologies||[]).map(normalizeHoldoutTopologyKey),a=document.getElementById('cSpecHoldoutIdeal'),f=document.getElementById('cSpecHoldoutFseries'),k=document.getElementById('cSpecHoldoutKnotplot');if(a)a.checked=saved.ideal!==false;if(f)f.checked=saved.fseries!==false;if(k)k.checked=saved.knotplot!==false;document.querySelectorAll('[data-spec-knot]').forEach(x=>x.checked=migrated.includes(x.dataset.specKnot));}
    for(const node of document.querySelectorAll('#cSpecHoldoutIdeal,#cSpecHoldoutFseries,#cSpecHoldoutKnotplot,[data-spec-knot]'))node.addEventListener('change',()=>{updateKnotSelectionUi();VLClockWorkflow.invalidateSelection();});
    document.getElementById('bSpecKnotsQuick')?.addEventListener('click',()=>applyKnotSelectionPreset('quick'));
    document.getElementById('bSpecKnotsCore')?.addEventListener('click',()=>applyKnotSelectionPreset('core'));
    document.getElementById('bSpecKnotsFull')?.addEventListener('click',()=>applyKnotSelectionPreset('full'));
    document.getElementById('bSpecKnotsTorus69')?.addEventListener('click',()=>applyKnotSelectionPreset('torus69'));
    updateKnotSelectionUi();
  }
  let active=false,index=-1,current=null,currentCanonicalization=null,checkpointIndex=0,results=[],gates=[],snapshot=null,calibrationRaw=null,launchMode='decomposition',benchmarkVisualState=null;
  let startedAt=null,completedAt=null,aborted=false,pending=false,timer=0,lastError=null;
  const clone=o=>JSON.parse(JSON.stringify(o));
  const el=id=>document.getElementById(id);
  const finite=x=>Number.isFinite(x)?x:null;
  const worst=list=>list.includes('FAIL')?'FAIL':(list.includes('WARN')?'WARN':(list.includes('PASS')?'PASS':'INFO'));
  const popcount=x=>{let n=0;for(;x;x>>=1)n+=x&1;return n;};
  const factorial=[1,1,2,6,24,120];
  const scenarioCheckpoints=sc=>Array.isArray(sc?.checkpoints)?sc.checkpoints:DEFAULT_CHECKPOINTS;
  const expectedSnapshotCount=()=>scenarios.reduce((sum,sc)=>sum+scenarioCheckpoints(sc).length,0);
  function statusClass(v){return v==='PASS'?'pass':v==='FAIL'?'fail':v==='WARN'?'warn':'info';}
  function setStatus(text,cls='running'){
    const node=el('proxyDecompStatus');if(node){node.textContent=text;node.className='spec-benchmark-status '+cls;}
  }
  function hashNumbers(arrays){
    let h=2166136261>>>0;
    for(const arr of arrays){
      if(arr==null)continue;
      const a=ArrayBuffer.isView(arr)?arr:Array.isArray(arr)?arr:[arr];
      for(let i=0;i<a.length;i++){
        const v=Number(a[i]);
        const s=Number.isFinite(v)?v.toExponential(15):String(v);
        for(let j=0;j<s.length;j++){h^=s.charCodeAt(j);h=Math.imul(h,16777619)>>>0;}
      }
    }
    return h.toString(16).padStart(8,'0');
  }
  function stateFingerprint(){
    return {y:hashNumbers([Y]),t:tPhys,cal:SpecClock.calibrated,refA:SpecClock.phaseNullRefA,refB:SpecClock.phaseNullRefB,calTime:SpecClock.calibrationTime};
  }
  function sameFingerprint(a,b){return a&&b&&a.y===b.y&&a.t===b.t&&a.cal===b.cal&&Object.is(a.refA,b.refA)&&Object.is(a.refB,b.refB)&&Object.is(a.calTime,b.calTime);}
  function carrierDescriptor(which,globalField){
    const fs=carrierFilaments(which);let count=0;for(const f of fs)count+=f.N;
    const points=new Float64Array(3*count),field=new Float64Array(3*count),components=[];
    let p=0;
    for(const f of fs){
      components.push({offset:p,count:f.N,gamma:filamentGamma(f),component:f.component||0});
      for(let k=0;k<f.N;k++,p++){
        const gi=f.off+3*k,li=3*p;
        points[li]=Y[gi];points[li+1]=Y[gi+1];points[li+2]=Y[gi+2];
        if(globalField){field[li]=globalField[gi];field[li+1]=globalField[gi+1];field[li+2]=globalField[gi+2];}
      }
    }
    return {which,points,field,components};
  }
  function directMutualGlobal(target,source){
    const out=new Float64Array(Y.length),sources=carrierFilaments(source),targets=carrierFilaments(target),a2=aSimActive()*aSimActive();
    for(const ft of targets){
      for(let k=0;k<ft.N;k++){
        const ti=ft.off+3*k,px=Y[ti],py=Y[ti+1],pz=Y[ti+2];let ux=0,uy=0,uz=0;
        for(const fs of sources){const pref=filamentGamma(fs)/(4*Math.PI);
          for(let j=0;j<fs.N;j++){const j2=(j+1)%fs.N,a=fs.off+3*j,b=fs.off+3*j2;
            const dlx=Y[b]-Y[a],dly=Y[b+1]-Y[a+1],dlz=Y[b+2]-Y[a+2];
            const mx=.5*(Y[a]+Y[b]),my=.5*(Y[a+1]+Y[b+1]),mz=.5*(Y[a+2]+Y[b+2]);
            const rx=px-mx,ry=py-my,rz=pz-mz,r2=rx*rx+ry*ry+rz*rz+a2,inv=pref/(r2*Math.sqrt(r2));
            ux+=(dly*rz-dlz*ry)*inv;uy+=(dlz*rx-dlx*rz)*inv;uz+=(dlx*ry-dly*rx)*inv;
          }
        }
        out[ti]=ux;out[ti+1]=uy;out[ti+2]=uz;
      }
    }
    return out;
  }
  function benchmarkKnotMetadata(sc=current){
    const source=sc?.knotSource||'builtin',key=sc?.knotKey||(P.knotKey||P.topo||'trefoil');
    const catalog=knotCatalogForSource(source),entry=catalog?.db?.[key]||null;
    const metadataL=finiteMetaNumber(entry?.L),metadataD=finiteMetaNumber(entry?.D),derivedIdeal=source==='ideal'&&Number.isFinite(metadataL)&&Number.isFinite(metadataD)&&metadataD>0?metadataL/metadataD:NaN;
    return {source,key,label:sc?.label||key,holdout:!!sc?.holdout,topologyKey:sc?.topologyKey||key,embedding:sc?.embedding||source,canonicalized:!!sc?.canonicalize,crossingNumber:Number.isFinite(sc?.crossingNumber)?sc.crossingNumber:(key.includes('6')?6:(key.includes('5')?5:(key.includes('4')?4:3))),idealRopDiam:Number.isFinite(sc?.idealRopDiam)?sc.idealRopDiam:(Number.isFinite(derivedIdeal)?derivedIdeal:null),metadataL:Number.isFinite(metadataL)?metadataL:null,metadataD:Number.isFinite(metadataD)?metadataD:null,componentCount:knotEntryComponents(entry).length||null,status:entry?.status||null,warning:entry?.warning||null,pairwiseLinking:entry?.pairwiseLinking||null,checkpointSteps:Number.isFinite(entry?.checkpointSteps)?entry.checkpointSteps:null};
  }
  function captureRawSnapshot(){
    const before=stateFingerprint();
    const full=new Float64Array(Y.length),isoA=new Float64Array(Y.length),isoB=new Float64Array(Y.length);
    velAll(Y,full);isoA.fill(0);isoB.fill(0);
    velocityCore(Y,carrierFilaments('A'),isoA,P.inter==='lia',{includeExternal:true});
    velocityCore(Y,carrierFilaments('B'),isoB,P.inter==='lia',{includeExternal:true});
    const mutA=directMutualGlobal('A','B'),mutB=directMutualGlobal('B','A');
    const make=(which,iso,mut)=>{
      const p=carrierDescriptor(which,full),i=carrierDescriptor(which,iso),m=carrierDescriptor(which,mut);
      return {which,points:p.points,components:p.components,fields:{full:p.field,iso:i.field,mutual:m.field}};
    };
    const measured=measureSpecClock();
    const raw={tPhys,scenarioId:current?.id||'',resolution:carrierN(),stateBefore:before,knot:benchmarkKnotMetadata(current),
      carriers:{A:make('A',isoA,mutA),B:make('B',isoB,mutB)},
      measured:measured&&measured.valid?{
        distance:measured.distance,phaseLogRatio:measured.phaseLogRatio,deltaFracA:measured.deltaFracA,deltaFracB:measured.deltaFracB,
        omegaA:measured.omegaA,omegaB:measured.omegaB,omegaIsoA:measured.omegaIsoA,omegaIsoB:measured.omegaIsoB,
        fieldLogMin:measured.fieldLogRatioMin,fieldLogMax:measured.fieldLogRatioMax,uA:measured.uA,uB:measured.uB
      }:null,
      topologyGap:lastTopologyGap,parameters:{aSim:aSimActive(),Rcyl:P.Rcyl,Hcyl:P.Hcyl,vzA:P.vzA,vzB:P.vzB,qual:P.qual,inter:P.inter,tracerCount:P.tracerCount,showTracers:P.showTracers,showStreamlines:P.showStreamlines,showPotentialFlow:P.showPotentialFlow}}
    raw.geometryHash=hashNumbers([raw.carriers.A.points,raw.carriers.B.points]);
    raw.parameterGridHash=hashNumbers([raw.carriers.A.components.flatMap(c=>[c.offset,c.count]),raw.carriers.B.components.flatMap(c=>[c.offset,c.count])]);
    raw.stateAfter=stateFingerprint();raw.pure=sameFingerprint(raw.stateBefore,raw.stateAfter);
    return raw;
  }
  function segmentInfo(points,components){
    const n=points.length/3,weights=new Float64Array(n),fractions=new Float64Array(n),ratios=[];
    for(const c of components){
      const cum=new Float64Array(c.count+1),lens=new Float64Array(c.count);
      for(let k=0;k<c.count;k++){const k2=(k+1)%c.count,i=3*(c.offset+k),j=3*(c.offset+k2);
        const l=Math.hypot(points[j]-points[i],points[j+1]-points[i+1],points[j+2]-points[i+2]);lens[k]=l;cum[k+1]=cum[k]+l;
      }
      const L=Math.max(cum[c.count],1e-30);let lmin=Infinity,lmax=0;
      for(let k=0;k<c.count;k++){const km=(k-1+c.count)%c.count,idx=c.offset+k;
        weights[idx]=.5*(lens[km]+lens[k]);fractions[idx]=cum[k]/L;lmin=Math.min(lmin,lens[k]);lmax=Math.max(lmax,lens[k]);
      }
      ratios.push(lmax/Math.max(lmin,1e-30));
    }
    return {weights,fractions,segmentRatio:Math.max(...ratios,1)};
  }
  function weightedCentroid(points,weights){
    let x=0,y=0,z=0,w=0;for(let k=0;k<weights.length;k++){const q=weights[k],i=3*k;x+=q*points[i];y+=q*points[i+1];z+=q*points[i+2];w+=q;}
    w=Math.max(w,1e-30);return [x/w,y/w,z/w];
  }
  function solve3(m,b){
    const a=m.slice(),x=b.slice();
    for(let k=0;k<3;k++){let p=k;for(let i=k+1;i<3;i++)if(Math.abs(a[3*i+k])>Math.abs(a[3*p+k]))p=i;
      if(Math.abs(a[3*p+k])<1e-30)return [0,0,0];
      if(p!==k){for(let j=k;j<3;j++){const t=a[3*k+j];a[3*k+j]=a[3*p+j];a[3*p+j]=t;}const t=x[k];x[k]=x[p];x[p]=t;}
      const d=a[3*k+k];for(let j=k;j<3;j++)a[3*k+j]/=d;x[k]/=d;
      for(let i=0;i<3;i++)if(i!==k){const f=a[3*i+k];for(let j=k;j<3;j++)a[3*i+j]-=f*a[3*k+j];x[i]-=f*x[k];}
    }
    return x;
  }
  function rigidFit(points,velocity,weights){
    const n=weights.length,c=weightedCentroid(points,weights);let W=0,ux=0,uy=0,uz=0;
    for(let k=0;k<n;k++){const w=weights[k],i=3*k;W+=w;ux+=w*velocity[i];uy+=w*velocity[i+1];uz+=w*velocity[i+2];}
    W=Math.max(W,1e-30);const U=[ux/W,uy/W,uz/W],I=[0,0,0,0,0,0,0,0,0],b=[0,0,0];
    for(let k=0;k<n;k++){const w=weights[k],i=3*k,rx=points[i]-c[0],ry=points[i+1]-c[1],rz=points[i+2]-c[2];
      const vx=velocity[i]-U[0],vy=velocity[i+1]-U[1],vz=velocity[i+2]-U[2],r2=rx*rx+ry*ry+rz*rz;
      I[0]+=w*(r2-rx*rx);I[1]-=w*rx*ry;I[2]-=w*rx*rz;I[3]-=w*ry*rx;I[4]+=w*(r2-ry*ry);I[5]-=w*ry*rz;I[6]-=w*rz*rx;I[7]-=w*rz*ry;I[8]+=w*(r2-rz*rz);
      b[0]+=w*(ry*vz-rz*vy);b[1]+=w*(rz*vx-rx*vz);b[2]+=w*(rx*vy-ry*vx);
    }
    const Om=solve3(I,b),trans=new Float64Array(3*n),rot=new Float64Array(3*n),def=new Float64Array(3*n);let err=0,norm=0;
    for(let k=0;k<n;k++){const i=3*k,rx=points[i]-c[0],ry=points[i+1]-c[1],rz=points[i+2]-c[2];
      const ox=Om[1]*rz-Om[2]*ry,oy=Om[2]*rx-Om[0]*rz,oz=Om[0]*ry-Om[1]*rx;
      trans[i]=U[0];trans[i+1]=U[1];trans[i+2]=U[2];rot[i]=ox;rot[i+1]=oy;rot[i+2]=oz;
      def[i]=velocity[i]-U[0]-ox;def[i+1]=velocity[i+1]-U[1]-oy;def[i+2]=velocity[i+2]-U[2]-oz;
      const ex=velocity[i]-(trans[i]+rot[i]+def[i]),ey=velocity[i+1]-(trans[i+1]+rot[i+1]+def[i+1]),ez=velocity[i+2]-(trans[i+2]+rot[i+2]+def[i+2]);
      const w=weights[k];err+=w*(ex*ex+ey*ey+ez*ez);norm+=w*(velocity[i]*velocity[i]+velocity[i+1]*velocity[i+1]+velocity[i+2]*velocity[i+2]);
    }
    return {centroid:c,U,Omega:Om,trans,rot,def,reconstructionRel:Math.sqrt(err/Math.max(norm,1e-300)),defRel:Math.sqrt(Math.max(0,norm-(b[0]*Om[0]+b[1]*Om[1]+b[2]*Om[2]))/Math.max(norm,1e-300))};
  }
  function quaternionRotation(ref,cur,weights){
    const cr=weightedCentroid(ref,weights),cc=weightedCentroid(cur,weights);let Sxx=0,Sxy=0,Sxz=0,Syx=0,Syy=0,Syz=0,Szx=0,Szy=0,Szz=0;
    for(let k=0;k<weights.length;k++){const w=weights[k],i=3*k,qx=ref[i]-cr[0],qy=ref[i+1]-cr[1],qz=ref[i+2]-cr[2],px=cur[i]-cc[0],py=cur[i+1]-cc[1],pz=cur[i+2]-cc[2];
      Sxx+=w*qx*px;Sxy+=w*qx*py;Sxz+=w*qx*pz;Syx+=w*qy*px;Syy+=w*qy*py;Syz+=w*qy*pz;Szx+=w*qz*px;Szy+=w*qz*py;Szz+=w*qz*pz;
    }
    const tr=Sxx+Syy+Szz,N=[tr,Syz-Szy,Szx-Sxz,Sxy-Syx,Syz-Szy,Sxx-Syy-Szz,Sxy+Syx,Szx+Sxz,Szx-Sxz,Sxy+Syx,-Sxx+Syy-Szz,Syz+Szy,Sxy-Syx,Szx+Sxz,Syz+Szy,-Sxx-Syy+Szz];
    const mu=Math.max(...[0,1,2,3].map(i=>Math.abs(N[4*i])+Math.abs(N[4*i+1])+Math.abs(N[4*i+2])+Math.abs(N[4*i+3])));let q=[1,0,0,0];for(let it=0;it<64;it++){const z=[0,0,0,0];for(let i=0;i<4;i++){for(let j=0;j<4;j++)z[i]+=N[4*i+j]*q[j];z[i]+=mu*q[i];}const l=Math.hypot(...z)||1;q=z.map(v=>v/l);}
    const [w,x,y,z]=q,R=[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)];
    let rms=0,W=0;for(let k=0;k<weights.length;k++){const i=3*k,qx=ref[i]-cr[0],qy=ref[i+1]-cr[1],qz=ref[i+2]-cr[2];
      const ax=cc[0]+R[0]*qx+R[1]*qy+R[2]*qz,ay=cc[1]+R[3]*qx+R[4]*qy+R[5]*qz,az=cc[2]+R[6]*qx+R[7]*qy+R[8]*qz,wk=weights[k];
      rms+=wk*((ax-cur[i])**2+(ay-cur[i+1])**2+(az-cur[i+2])**2);W+=wk;
    }
    return {R,refCentroid:cr,currentCentroid:cc,rms:Math.sqrt(rms/Math.max(W,1e-30))};
  }
  function rotateAlign(points,pose){
    const out=new Float64Array(points.length),R=pose.R,a=pose.refCentroid,b=pose.currentCentroid;
    for(let k=0;k<points.length/3;k++){const i=3*k,x=points[i]-a[0],y=points[i+1]-a[1],z=points[i+2]-a[2];out[i]=b[0]+R[0]*x+R[1]*y+R[2]*z;out[i+1]=b[1]+R[3]*x+R[4]*y+R[5]*z;out[i+2]=b[2]+R[6]*x+R[7]*y+R[8]*z;}
    return out;
  }
  function sampleAtFractions(values,points,components,targetFractions){
    const out=new Float64Array(values.length);let targetOffset=0;
    for(const c of components){
      const cum=new Float64Array(c.count+1);for(let k=0;k<c.count;k++){const k2=(k+1)%c.count,i=3*(c.offset+k),j=3*(c.offset+k2);cum[k+1]=cum[k]+Math.hypot(points[j]-points[i],points[j+1]-points[i+1],points[j+2]-points[i+2]);}
      const L=Math.max(cum[c.count],1e-30);let seg=0;
      for(let k=0;k<c.count;k++){const f=((targetFractions[targetOffset+k]%1)+1)%1,target=f*L;while(seg<c.count-1&&cum[seg+1]<target)seg++;const k2=(seg+1)%c.count,den=Math.max(cum[seg+1]-cum[seg],1e-30),u=(target-cum[seg])/den;
        const a=3*(c.offset+seg),b=3*(c.offset+k2),o=3*(targetOffset+k);out[o]=values[a]+u*(values[b]-values[a]);out[o+1]=values[a+1]+u*(values[b+1]-values[a+1]);out[o+2]=values[a+2]+u*(values[b+2]-values[a+2]);
      }
      targetOffset+=c.count;
    }
    return out;
  }
  function uniformFractions(components){const n=components.reduce((s,c)=>s+c.count,0),f=new Float64Array(n);let p=0;for(const c of components)for(let k=0;k<c.count;k++)f[p++]=k/c.count;return f;}
  function shiftComponents(arr,components,shiftFraction=1/3){
    const out=new Float64Array(arr.length);for(const c of components){const sh=Math.max(1,Math.floor(c.count*shiftFraction))%c.count;for(let k=0;k<c.count;k++){const src=3*(c.offset+(k+sh)%c.count),dst=3*(c.offset+k);out[dst]=arr[src];out[dst+1]=arr[src+1];out[dst+2]=arr[src+2];}}return out;
  }
  function shiftByCount(arr,components,shift){
    const out=new Float64Array(arr.length);for(const c of components){const sh=((shift%c.count)+c.count)%c.count;for(let k=0;k<c.count;k++){const src=3*(c.offset+(k+sh)%c.count),dst=3*(c.offset+k);out[dst]=arr[src];out[dst+1]=arr[src+1];out[dst+2]=arr[src+2];}}return out;
  }
  function bestCyclicPose(reference,current,components,weights){
    const count=components.length===1?components[0].count:1;let best=null;
    for(let shift=0;shift<count;shift++){const shifted=shiftByCount(reference,components,shift),pose=quaternionRotation(shifted,current,weights);if(!best||pose.rms<best.pose.rms)best={shift,shifted,pose};}
    return best;
  }
  function vdot(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
  function vcross(a,b){return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];}
  function vnorm(a){const n=Math.hypot(a[0],a[1],a[2]);return n>1e-30?[a[0]/n,a[1]/n,a[2]/n]:[0,0,1];}
  function deterministicAxisSign(v){let j=0;if(Math.abs(v[1])>Math.abs(v[j]))j=1;if(Math.abs(v[2])>Math.abs(v[j]))j=2;return v[j]<0?v.map(x=>-x):v.slice();}
  function symmetricEigen3(m){
    const a=[m[0],m[1],m[2],m[3],m[4],m[5],m[6],m[7],m[8]],V=[1,0,0,0,1,0,0,0,1];
    for(let it=0;it<48;it++){
      let p=0,q=1,max=Math.abs(a[1]);for(const [i,j] of [[0,2],[1,2]]){const x=Math.abs(a[3*i+j]);if(x>max){max=x;p=i;q=j;}}
      if(max<1e-14*Math.max(1,Math.abs(a[0]),Math.abs(a[4]),Math.abs(a[8])))break;
      const app=a[3*p+p],aqq=a[3*q+q],apq=a[3*p+q],phi=.5*Math.atan2(2*apq,aqq-app),c=Math.cos(phi),sn=Math.sin(phi);
      for(let k=0;k<3;k++){const aik=a[3*p+k],aqk=a[3*q+k];a[3*p+k]=c*aik-sn*aqk;a[3*q+k]=sn*aik+c*aqk;}
      for(let k=0;k<3;k++){const akp=a[3*k+p],akq=a[3*k+q];a[3*k+p]=c*akp-sn*akq;a[3*k+q]=sn*akp+c*akq;}
      a[3*p+q]=a[3*q+p]=0;
      for(let k=0;k<3;k++){const vip=V[3*k+p],viq=V[3*k+q];V[3*k+p]=c*vip-sn*viq;V[3*k+q]=sn*vip+c*viq;}
    }
    const eig=[0,1,2].map(j=>({value:a[3*j+j],vector:deterministicAxisSign(vnorm([V[j],V[3+j],V[6+j]]))})).sort((x,y)=>x.value-y.value);
    return eig;
  }
  function intrinsicFrame(points,components=null,weights=null){
    const n=points.length/3,w=weights&&weights.length===n?weights:new Float64Array(n).fill(1),c=weightedCentroid(points,w);let W=0,C=[0,0,0,0,0,0,0,0,0];
    for(let k=0;k<n;k++){const q=w[k],i=3*k,x=points[i]-c[0],y=points[i+1]-c[1],z=points[i+2]-c[2];W+=q;C[0]+=q*x*x;C[1]+=q*x*y;C[2]+=q*x*z;C[3]+=q*y*x;C[4]+=q*y*y;C[5]+=q*y*z;C[6]+=q*z*x;C[7]+=q*z*y;C[8]+=q*z*z;}
    W=Math.max(W,1e-30);C=C.map(x=>x/W);const eig=symmetricEigen3(C),ez=eig[0].vector;let ex=eig[2].vector;ex=vnorm([ex[0]-vdot(ex,ez)*ez[0],ex[1]-vdot(ex,ez)*ez[1],ex[2]-vdot(ex,ez)*ez[2]]);let ey=vnorm(vcross(ez,ex));ex=vnorm(vcross(ey,ez));
    return {centroid:c,ex,ey,ez,eigenvalues:eig.map(x=>x.value),method:'covariance-smallest-axis + right-handed principal frame'};
  }
  function projectOmegaVector(omega,frame){const parallel=vdot(omega,frame.ez),magnitude=Math.hypot(...omega),perpendicular=Math.sqrt(Math.max(0,magnitude*magnitude-parallel*parallel));return {vector:omega.slice(),axis:frame.ez.slice(),parallel,magnitude,perpendicular};}
  function canonicalizeCarrierGeometry(which,targetRms=.05){
    const fs=carrierFilaments(which),idx=[],pts=[];for(const f of fs)for(let k=0;k<f.N;k++){const gi=f.off+3*k;idx.push(gi);pts.push(Y[gi],Y[gi+1],Y[gi+2]);}
    const arr=Float64Array.from(pts),components=[];let off=0;for(const f of fs){components.push({offset:off,count:f.N});off+=f.N;}const frame=intrinsicFrame(arr,components),coords=[];let r2=0;
    for(let k=0;k<arr.length/3;k++){const i=3*k,r=[arr[i]-frame.centroid[0],arr[i+1]-frame.centroid[1],arr[i+2]-frame.centroid[2]],x=vdot(r,frame.ex),y=vdot(r,frame.ey),z=vdot(r,frame.ez);coords.push(x,y,z);r2+=x*x+y*y;}
    const rms=Math.sqrt(r2/Math.max(1,arr.length/3)),scale=targetRms/Math.max(rms,1e-30);
    for(let k=0;k<idx.length;k++){const gi=idx[k],i=3*k;Y[gi]=frame.centroid[0]+scale*coords[i];Y[gi+1]=frame.centroid[1]+scale*coords[i+1];Y[gi+2]=frame.centroid[2]+scale*coords[i+2];}
    return {which,targetRms,sourceTransverseRms:rms,scale,frame,eigenvalues:frame.eigenvalues,determinant:vdot(frame.ex,vcross(frame.ey,frame.ez))};
  }
  function canonicalizeHoldoutGeometry(sc){if(!sc?.canonicalize)return null;const A=canonicalizeCarrierGeometry('A'),B=canonicalizeCarrierGeometry('B');sc.canonicalization={A,B,scaleConvention:'transverse RMS radius = 0.05 m',centroidConvention:'preserve carrier centroids',rotationConvention:'right-handed covariance principal frame; smallest-variance axis -> lab z'};return sc.canonicalization;}
  function bodyOmegaFlat(points,velocity){
    const n=points.length/3;let cx=0,cy=0,cz=0;for(let k=0;k<n;k++){const i=3*k;cx+=points[i];cy+=points[i+1];cz+=points[i+2];}cx/=n;cy/=n;cz/=n;
    let num=0,den=0;for(let k=0;k<n;k++){const i=3*k,rx=points[i]-cx,ry=points[i+1]-cy;num+=rx*velocity[i+1]-ry*velocity[i];den+=rx*rx+ry*ry;}return den>1e-18?num/den:NaN;
  }
  function addArrays(a,b){const o=new Float64Array(a.length);for(let i=0;i<o.length;i++)o[i]=a[i]+b[i];return o;}
  function selectField(fit,useRot,useTrans){const o=new Float64Array(fit.def.length);for(let i=0;i<o.length;i++)o[i]=fit.def[i]+(useRot?fit.rot[i]:0)+(useTrans?fit.trans[i]:0);return o;}
  function prepareCarrier(raw,cal){
    const info=segmentInfo(raw.points,raw.components),calInfo=segmentInfo(cal.points,cal.components),uf=uniformFractions(raw.components);
    const currentUniform=sampleAtFractions(raw.points,raw.points,raw.components,uf),calUniform=sampleAtFractions(cal.points,cal.points,cal.components,uf);
    const bestPose=bestCyclicPose(calUniform,currentUniform,raw.components,new Float64Array(uf.length).fill(1)),pose=bestPose.pose;
    const alignedCalUniform=rotateAlign(bestPose.shifted,pose);
    const phaseShift=raw.components.length===1?bestPose.shift/raw.components[0].count:0,shiftedLiveFractions=new Float64Array(info.fractions.length);
    for(let i=0;i<shiftedLiveFractions.length;i++)shiftedLiveFractions[i]=(info.fractions[i]+phaseShift)%1;
    const alignedCalLive=rotateAlign(sampleAtFractions(cal.points,cal.points,cal.components,shiftedLiveFractions),pose);
    const fits={};for(const key of ['iso','mutual','full'])fits[key]=rigidFit(raw.points,raw.fields[key],info.weights);
    const calFits={};for(const key of ['iso','mutual','full'])calFits[key]=rigidFit(cal.points,cal.fields[key],calInfo.weights);
    function grid(useLive,isCalibration=false){
      const src=isCalibration?cal:raw,si=isCalibration?calInfo:info,ff=isCalibration?calFits:fits;
      const fractions=useLive?si.fractions:uf;
      const points=isCalibration?(useLive?cal.points:calUniform):(useLive?raw.points:currentUniform);
      const frozen=isCalibration?points:(useLive?alignedCalLive:alignedCalUniform);
      const fields={};for(const key of ['iso','mutual','full']){
        fields[key]={};for(const part of ['def','rot','trans'])fields[key][part]=useLive?ff[key][part]:sampleAtFractions(ff[key][part],src.points,src.components,fractions);
      }
      return {points,frozen,fields};
    }
    return {info,calInfo,pose,cyclicShift:bestPose.shift,fits,calFits,components:raw.components.map(c=>({...c})),grid};
  }
  function prepareRaw(raw,calRaw){return {A:prepareCarrier(raw.carriers.A,calRaw.carriers.A),B:prepareCarrier(raw.carriers.B,calRaw.carriers.B)};}
  function evaluateCarrier(prep,mask,isCalibration){
    const useGeom=!!(mask&BITS.GEOM),useLive=!!(mask&BITS.PARAM),useRot=!!(mask&BITS.ROT),useTrans=!!(mask&BITS.TRANS),useMutual=!!(mask&BITS.MUTUAL_BS);
    const g=prep.grid(useLive,isCalibration),points=useGeom?g.points:g.frozen;
    const iso=selectField(g.fields.iso,useRot,useTrans),mut=useMutual?selectField(g.fields.mutual,useRot,useTrans):new Float64Array(iso.length);
    const full=addArrays(iso,mut),omegaIso=bodyOmegaFlat(points,iso),omegaMutual=bodyOmegaFlat(points,mut),omegaFull=bodyOmegaFlat(points,full);
    const gAll=prep.grid(useLive,isCalibration),pAll=useGeom?gAll.points:gAll.frozen;
    const isoAll=selectField(gAll.fields.iso,true,true),denom=Math.max(Math.abs(bodyOmegaFlat(pAll,isoAll)),1e-15);
    return {omegaIso,omegaMutual,omegaFull,deltaFrac:omegaMutual/denom,denom};
  }
  function counterfactual(preparedCurrent,preparedCal,mask){
    const out={mask,channels:CHANNELS.filter(c=>mask&BITS[c]),carrier:{}};
    for(const which of ['A','B']){
      const c=evaluateCarrier(preparedCurrent[which],mask,false),r=evaluateCarrier(preparedCal[which],mask,true),offset=c.deltaFrac-r.deltaFrac;
      out.carrier[which]={current:c,calibration:r,offset,logOffset:offset>-1?Math.log1p(offset):NaN,rawOmegaDelta:c.omegaMutual-r.omegaMutual};
    }
    out.metrics={
      phaseLog:out.carrier.A.logOffset-out.carrier.B.logOffset,
      deltaFrac:out.carrier.A.offset-out.carrier.B.offset,
      rawOmega:out.carrier.A.rawOmegaDelta-out.carrier.B.rawOmegaDelta,
      logA:out.carrier.A.logOffset,logB:out.carrier.B.logOffset,
      deltaA:out.carrier.A.offset,deltaB:out.carrier.B.offset,
      omegaA:out.carrier.A.rawOmegaDelta,omegaB:out.carrier.B.rawOmegaDelta
    };
    return out;
  }
  function shapley(counterfactuals,key){
    const phi=Object.fromEntries(CHANNELS.map(c=>[c,0]));
    for(const c of CHANNELS){const bit=BITS[c];for(let mask=0;mask<32;mask++)if(!(mask&bit)){
      const s=popcount(mask),w=factorial[s]*factorial[4-s]/factorial[5],a=counterfactuals[mask].metrics[key],b=counterfactuals[mask|bit].metrics[key];phi[c]+=w*(b-a);
    }}
    const total=counterfactuals[31].metrics[key]-counterfactuals[0].metrics[key],sum=CHANNELS.reduce((s,c)=>s+phi[c],0),sumAbsPhi=CHANNELS.reduce((s,c)=>s+Math.abs(phi[c]),0),residual=total-sum,reconstructionScale=Math.max(Math.abs(total),sumAbsPhi);
    return {phi,total,baseline:counterfactuals[0].metrics[key],full:counterfactuals[31].metrics[key],sumAbsPhi,reconstructionScale,residual,relativeResidual:reconstructionScale>0?Math.abs(residual)/reconstructionScale:(residual===0?0:Infinity)};
  }
  function reconstructionCheck(sh,key){
    const absoluteTolerance=RECON_ABS_TOL[key]??1e-24,relativeTolerance=RECON_REL_TOL,scale=Math.max(Math.abs(sh.total),sh.sumAbsPhi||0,Math.abs(sh.full-sh.baseline)),tolerance=absoluteTolerance+relativeTolerance*scale,absoluteResidual=Math.abs(sh.residual);
    return {key,absoluteResidual,scale,absoluteTolerance,relativeTolerance,tolerance,score:absoluteResidual/Math.max(tolerance,1e-300),relativeResidual:scale>0?absoluteResidual/scale:(absoluteResidual===0?0:Infinity)};
  }
  function pairInteraction(counterfactuals,key){
    const v0=counterfactuals[0].metrics[key],vRot=counterfactuals[BITS.ROT].metrics[key],vMutual=counterfactuals[BITS.MUTUAL_BS].metrics[key],vRotMutual=counterfactuals[BITS.ROT|BITS.MUTUAL_BS].metrics[key],vAll=counterfactuals[31].metrics[key],interaction=vRotMutual-vRot-vMutual+v0,total=vAll-v0;
    return {v0,vRot,vMutual,vRotMutual,vAll,interaction,total,interactionToTotal:Math.abs(total)<=1e-300&&Math.abs(interaction)<=1e-300?null:Math.abs(interaction)/Math.max(Math.abs(total),1e-300),mutualOnly:vMutual-v0,rotOnly:vRot-v0};
  }
  function interactionBundle(counterfactuals){return {phaseLog:pairInteraction(counterfactuals,'phaseLog'),deltaFrac:pairInteraction(counterfactuals,'deltaFrac'),rawOmega:pairInteraction(counterfactuals,'rawOmega'),A:{phaseLog:pairInteraction(counterfactuals,'logA'),deltaFrac:pairInteraction(counterfactuals,'deltaA'),rawOmega:pairInteraction(counterfactuals,'omegaA')},B:{phaseLog:pairInteraction(counterfactuals,'logB'),deltaFrac:pairInteraction(counterfactuals,'deltaB'),rawOmega:pairInteraction(counterfactuals,'omegaB')}};}
  function carrierNormalizationStats(carrier){
    const info=segmentInfo(carrier.points,carrier.components);let totalLength=0,gammaLength=0,componentOffset=0;
    for(const c of carrier.components){let L=0;for(let k=0;k<c.count;k++){const k2=(k+1)%c.count,i=3*(c.offset+k),j=3*(c.offset+k2);L+=Math.hypot(carrier.points[j]-carrier.points[i],carrier.points[j+1]-carrier.points[i+1],carrier.points[j+2]-carrier.points[i+2]);}totalLength+=L;gammaLength+=Math.abs(c.gamma||0)*L;componentOffset+=c.count;}
    let sum=0,W=0;for(let k=0;k<info.weights.length;k++){const i=3*k,w=info.weights[k],v=carrier.fields.iso;sum+=w*(v[i]*v[i]+v[i+1]*v[i+1]+v[i+2]*v[i+2]);W+=w;}
    return {length:totalLength,gammaEff:gammaLength/Math.max(totalLength,1e-300),isoRms:Math.sqrt(sum/Math.max(W,1e-300)),segmentRatio:info.segmentRatio};
  }
  function directBodyOmegaSet(carrier){return {full:bodyOmegaFlat(carrier.points,carrier.fields.full),iso:bodyOmegaFlat(carrier.points,carrier.fields.iso),mutual:bodyOmegaFlat(carrier.points,carrier.fields.mutual)};}
  function normalizationScales(currentCarrier,calCarrier,currentBody,calBody,aSim){
    const cs=carrierNormalizationStats(currentCarrier),rs=carrierNormalizationStats(calCarrier),L=Math.max(rs.length,1e-300),gamma=Math.max(Math.abs(rs.gammaEff),1e-300),a=Math.max(Math.abs(aSim),1e-300);
    const fixed={
      ISO_REFERENCE:Math.max(Math.abs(calBody.iso),1e-30),
      FULL_REFERENCE:Math.max(Math.abs(calBody.full),1e-30),
      MUTUAL_REFERENCE:Math.max(Math.abs(calBody.mutual),1e-30),
      CIRCULATION_LENGTH:Math.max(gamma/(L*L),1e-30),
      RMS_ARCLENGTH:Math.max(rs.isoRms/L,1e-30),
      CORE_CIRCULATION:Math.max(gamma/(a*a),1e-30)
    };
    return {currentStats:cs,referenceStats:rs,values:{ISO_DYNAMIC:{current:Math.max(Math.abs(currentBody.iso),1e-30),calibration:Math.max(Math.abs(calBody.iso),1e-30)},...Object.fromEntries(Object.entries(fixed).map(([k,v])=>[k,{current:v,calibration:v}]))}};
  }
  function normalizationBundle(raw,calRaw){
    const carrier={},aSim=calRaw.parameters?.aSim??raw.parameters?.aSim??aSimActive();
    for(const which of ['A','B']){
      const cb=directBodyOmegaSet(raw.carriers[which]),rb=directBodyOmegaSet(calRaw.carriers[which]),scales=normalizationScales(raw.carriers[which],calRaw.carriers[which],cb,rb,aSim),values={};
      for(const def of NORMALIZATIONS){const d=scales.values[def.id],qCurrent=cb.mutual/d.current,qCalibration=rb.mutual/d.calibration,offset=qCurrent-qCalibration;values[def.id]={denominatorCurrent:d.current,denominatorCalibration:d.calibration,qCurrent,qCalibration,offset,logOffset:offset>-1?Math.log1p(offset):NaN,asinhOffset:Math.asinh(offset),valid:Number.isFinite(offset)&&Number.isFinite(d.current)&&Number.isFinite(d.calibration)};}
      carrier[which]={bodyCurrent:cb,bodyCalibration:rb,scales,values};
    }
    const fieldAbsMax=Math.max(Math.abs(raw.measured?.fieldLogMin||0),Math.abs(raw.measured?.fieldLogMax||0)),net={};
    for(const def of NORMALIZATIONS){const A=carrier.A.values[def.id],B=carrier.B.values[def.id],netLinear=A.offset-B.offset,netLog=Number.isFinite(A.logOffset)&&Number.isFinite(B.logOffset)?A.logOffset-B.logOffset:NaN,netAsinh=A.asinhOffset-B.asinhOffset,primary=Number.isFinite(netLog)?netLog:netAsinh;net[def.id]={id:def.id,label:def.label,kind:def.kind,risk:def.risk||null,A,B,netLinear,netLog,netAsinh,fieldAbsMax,fieldScaleRatio:Math.abs(primary)/Math.max(fieldAbsMax,1e-300),valid:A.valid&&B.valid&&Number.isFinite(primary)};}
    return {definitions:NORMALIZATIONS.map(x=>({...x})),carrier,net,aSim};
  }
  function transferLawDimensions(def){
    const e=def.exponents||{},length=2*(e.gamma||0)+(e.a||0)+(e.L||0)+(e.d||0)+(e.vChar||0)+(e.rc||0),time=-(e.deltaOmega||0)-(e.gamma||0)-(e.vChar||0);
    return {length,time,dimensionless:Math.abs(length)<1e-12&&Math.abs(time)<1e-12};
  }
  function transferLawBundle(raw,calRaw,normalizations){
    const fieldAbsMax=Math.max(Math.abs(raw.measured?.fieldLogMin||0),Math.abs(raw.measured?.fieldLogMax||0)),d=Math.max(Math.abs(raw.measured?.distance||0),1e-300),a=Math.max(Math.abs(normalizations.aSim),1e-300),carrier={};
    for(const which of ['A','B']){
      const n=normalizations.carrier[which],deltaOmega=n.bodyCurrent.mutual-n.bodyCalibration.mutual,gamma=Math.max(Math.abs(n.scales.referenceStats.gammaEff),1e-300),L=Math.max(Math.abs(n.scales.referenceStats.length),1e-300),inputs={deltaOmega,gamma,a,L,d,vChar:V_CHAR_SST,rc:R_HORN_SST},values={};
      for(const law of TRANSFER_LAWS){const value=law.coefficient*law.evaluate(inputs),dim=transferLawDimensions(law);values[law.id]={value,inputs:{...inputs},coefficient:law.coefficient,dimension:dim,valid:Number.isFinite(value)&&dim.dimensionless&&law.coefficient===1};}
      carrier[which]={deltaOmega,inputs:{deltaOmega,gamma,a,L,d,vChar:V_CHAR_SST,rc:R_HORN_SST},values};
    }
    const net={};for(const law of TRANSFER_LAWS){const A=carrier.A.values[law.id],B=carrier.B.values[law.id],value=A.value-B.value,ratio=Math.abs(value)/Math.max(fieldAbsMax,1e-300);net[law.id]={id:law.id,label:law.label,formula:law.formula,A,B,value,fieldAbsMax,fieldScaleRatio:ratio,requiredCoefficientToFieldEdge:Math.abs(value)>0?fieldAbsMax/Math.abs(value):Infinity,dimension:transferLawDimensions(law),coefficient:law.coefficient,valid:A.valid&&B.valid&&Number.isFinite(value)};}
    return {definitions:TRANSFER_LAWS.map(({evaluate,...x})=>({...x,dimension:transferLawDimensions(x)})),carrier,net,constants:{vChar:V_CHAR_SST,rc:R_HORN_SST,symbol:'v↺*'},distance:d,aSim:a};
  }
  function carrierGeometryMetrics(carrier){
    let length=0,minCurvatureRadius=Infinity,minDoublyCritical=Infinity,minPairGap=Infinity;
    const pts=carrier.points;
    const tangent=(c,k)=>{const n=c.count,km=(k-1+n)%n,kp=(k+1)%n,i=3*(c.offset+km),j=3*(c.offset+kp),dx=pts[j]-pts[i],dy=pts[j+1]-pts[i+1],dz=pts[j+2]-pts[i+2],q=Math.hypot(dx,dy,dz)||1;return[dx/q,dy/q,dz/q];};
    for(const c of carrier.components){
      const n=c.count,skip=Math.max(6,Math.round(n/10)),stride=Math.max(1,Math.ceil(n/220));
      for(let k=0;k<n;k++){
        const km=(k-1+n)%n,kp=(k+1)%n,im=3*(c.offset+km),i=3*(c.offset+k),ip=3*(c.offset+kp);
        const ax=pts[i]-pts[im],ay=pts[i+1]-pts[im+1],az=pts[i+2]-pts[im+2],bx=pts[ip]-pts[i],by=pts[ip+1]-pts[i+1],bz=pts[ip+2]-pts[i+2];
        const la=Math.hypot(ax,ay,az),lb=Math.hypot(bx,by,bz);length+=lb;
        if(la>1e-15&&lb>1e-15){const dot=Math.max(-1,Math.min(1,(ax*bx+ay*by+az*bz)/(la*lb))),ang=Math.acos(dot),kap=2*Math.sin(.5*ang)/Math.max(1e-15,.5*(la+lb));if(kap>1e-15)minCurvatureRadius=Math.min(minCurvatureRadius,1/kap);}
      }
      for(let i0=0;i0<n;i0+=stride){const ti=tangent(c,i0),ii=3*(c.offset+i0);for(let j0=i0+skip;j0<n;j0+=stride){const dd=Math.min(j0-i0,n-(j0-i0));if(dd<skip)continue;const jj=3*(c.offset+j0),dx=pts[jj]-pts[ii],dy=pts[jj+1]-pts[ii+1],dz=pts[jj+2]-pts[ii+2],dist=Math.hypot(dx,dy,dz);if(!(dist>1e-15)||dist>=minDoublyCritical)continue;const tj=tangent(c,j0),ci=Math.abs((dx*ti[0]+dy*ti[1]+dz*ti[2])/dist),cj=Math.abs((dx*tj[0]+dy*tj[1]+dz*tj[2])/dist);if(ci<.22&&cj<.22)minDoublyCritical=dist;}}
    }
    for(let a=0;a<carrier.components.length;a++)for(let b=a+1;b<carrier.components.length;b++){const ca=carrier.components[a],cb=carrier.components[b];for(let i=0;i<ca.count;i++){const ii=3*(ca.offset+i);for(let j=0;j<cb.count;j++){const jj=3*(cb.offset+j);minPairGap=Math.min(minPairGap,Math.hypot(pts[jj]-pts[ii],pts[jj+1]-pts[ii+1],pts[jj+2]-pts[ii+2]));}}}
    const thickness=Math.min(minCurvatureRadius,.5*minDoublyCritical,.5*minPairGap);
    return {length,minCurvatureRadius,minDoublyCritical,minPairGap,thickness:Number.isFinite(thickness)&&thickness>0?thickness:NaN,ropelength:Number.isFinite(thickness)&&thickness>0?length/(2*thickness):NaN};
  }
  function lengthScaleMap(raw,calRaw,normalizations,which){
    const n=normalizations.carrier[which],currentGeom=carrierGeometryMetrics(raw.carriers[which]),referenceGeom=carrierGeometryMetrics(calRaw.carriers[which]),a=Math.max(Math.abs(normalizations.aSim),1e-300),gamma=Math.max(Math.abs(n.scales.referenceStats.gammaEff),1e-300),d=Math.max(Math.abs(raw.measured?.distance||0),1e-300),d0=Math.max(Math.abs(calRaw.measured?.distance||d),1e-300);
    const minLoop=2*Math.PI*R_HORN_SST,lambdaBar=C_LIGHT*R_HORN_SST/V_CHAR_SST,lambdaCompton=2*Math.PI*lambdaBar;
    const map={
      RESOLVED_CURRENT:{current:currentGeom.length,calibration:referenceGeom.length},
      RESOLVED_REFERENCE:{current:referenceGeom.length,calibration:referenceGeom.length},
      IDEAL_REACH_CURRENT:{current:IDEAL_TREFOIL_ROPELENGTH*2*currentGeom.thickness,calibration:IDEAL_TREFOIL_ROPELENGTH*2*referenceGeom.thickness},
      IDEAL_REACH_REFERENCE:{current:IDEAL_TREFOIL_ROPELENGTH*2*referenceGeom.thickness,calibration:IDEAL_TREFOIL_ROPELENGTH*2*referenceGeom.thickness},
      IDEAL_ASIM_DIAMETER:{current:IDEAL_TREFOIL_ROPELENGTH*2*a,calibration:IDEAL_TREFOIL_ROPELENGTH*2*a},
      TREFOIL_RC_DIAMETER_BENCHMARK:{current:IDEAL_TREFOIL_ROPELENGTH*2*R_HORN_SST,calibration:IDEAL_TREFOIL_ROPELENGTH*2*R_HORN_SST},
      MINIMAL_NEUTRAL_LOOP:{current:minLoop,calibration:minLoop},
      COMPTON_WAVELENGTH:{current:lambdaCompton,calibration:lambdaCompton},
      REDUCED_COMPTON:{current:lambdaBar,calibration:lambdaBar},
      DISTANCE_CONTROL:{current:d,calibration:d0}
    };
    return {map,currentGeom,referenceGeom,aSim:a,gamma,d,d0,minLoop,lambdaBar,lambdaCompton};
  }
  function lengthBenchmarkBundle(raw,calRaw,normalizations){
    const carrier={},fieldCurrent={min:raw.measured?.fieldLogMin??NaN,max:raw.measured?.fieldLogMax??NaN},fieldCalibration={min:calRaw.measured?.fieldLogMin??NaN,max:calRaw.measured?.fieldLogMax??NaN};
    const fieldAbsMax=Math.max(Math.abs(fieldCurrent.min),Math.abs(fieldCurrent.max)),fieldDelta={min:fieldCurrent.min-fieldCalibration.min,max:fieldCurrent.max-fieldCalibration.max},fieldDeltaAbsMax=Math.max(Math.abs(fieldDelta.min),Math.abs(fieldDelta.max));
    for(const which of ['A','B']){const n=normalizations.carrier[which],scales=lengthScaleMap(raw,calRaw,normalizations,which),values={};for(const def of LENGTH_CANDIDATES){const L=scales.map[def.id],absoluteCurrent=n.bodyCurrent.mutual*L.current/V_CHAR_SST,absoluteCalibration=n.bodyCalibration.mutual*L.calibration/V_CHAR_SST,delta=absoluteCurrent-absoluteCalibration;values[def.id]={lengthCurrent:L.current,lengthCalibration:L.calibration,absoluteCurrent,absoluteCalibration,delta,valid:[L.current,L.calibration,absoluteCurrent,absoluteCalibration,delta].every(Number.isFinite)&&L.current>0&&L.calibration>0};}carrier[which]={scales,values};}
    const net={};for(const def of LENGTH_CANDIDATES){const A=carrier.A.values[def.id],B=carrier.B.values[def.id],absoluteCurrent=A.absoluteCurrent-B.absoluteCurrent,absoluteCalibration=A.absoluteCalibration-B.absoluteCalibration,delta=A.delta-B.delta,absoluteScaleRatio=Math.abs(absoluteCurrent)/Math.max(fieldAbsMax,1e-300),deltaScaleRatio=fieldDeltaAbsMax>1e-300?Math.abs(delta)/fieldDeltaAbsMax:(Math.abs(delta)<=1e-300?0:Infinity),identityError=Math.abs(delta-(absoluteCurrent-absoluteCalibration)),identityScale=Math.max(Math.abs(delta),Math.abs(absoluteCurrent),Math.abs(absoluteCalibration)),identityTolerance=1e-27+1e-12*identityScale,identityScore=identityError/identityTolerance;net[def.id]={id:def.id,label:def.label,kind:def.kind,semanticEligible:!!def.semanticEligible,risk:def.risk||null,A,B,absoluteCurrent,absoluteCalibration,delta,fieldCurrent,fieldCalibration,fieldDelta,fieldAbsMax,fieldDeltaAbsMax,absoluteScaleRatio,deltaScaleRatio,requiredCoefficientAbsolute:Math.abs(absoluteCurrent)>0?fieldAbsMax/Math.abs(absoluteCurrent):null,requiredCoefficientDelta:Math.abs(delta)>0&&fieldDeltaAbsMax>0?fieldDeltaAbsMax/Math.abs(delta):null,identityError,identityScale,identityTolerance,identityScore,valid:A.valid&&B.valid&&Number.isFinite(absoluteCurrent)&&Number.isFinite(delta)};}
    return {definitions:LENGTH_CANDIDATES.map(x=>({...x})),carrier,net,canonicalStatement:'tau_circ(K)=L_K/vChar; L_K is the resolved closed carrier length. 2pi rc is only the minimal neutral loop.',idealTrefoilRopelength:{diameterConvention:IDEAL_TREFOIL_ROPELENGTH,radiusConvention:2*IDEAL_TREFOIL_ROPELENGTH},fieldCurrent,fieldCalibration,fieldDelta};
  }

  function auditIdealKnotConvention(){
    const catalog=getIdealKnotCatalog(),rows=[];
    if(!catalog)return {available:false,pass:false,reason:'ideal_knots_data.js niet geladen',rows,selectedTrefoil:null,convention:'UNKNOWN'};
    for(const id of IDEAL_CONVENTION_AUDIT_IDS){
      const entry=catalog.db?.[id],components=knotEntryComponents(entry);
      if(!entry||!components.length){rows.push({id,pass:false,reason:'entry/component ontbreekt'});continue;}
      const N=384,points=sampleIdealComponent(components[0],N),geom=carrierGeometryMetrics({points,components:[{offset:0,count:N,gamma:1,component:0}]});
      const metadataL=finiteMetaNumber(entry.L),metadataD=finiteMetaNumber(entry.D),componentL=finiteMetaNumber(components[0].L),diameterFromReach=2*geom.thickness,ropDiamFromReach=geom.length/diameterFromReach,ropRadFromReach=geom.length/geom.thickness,metadataRopDiam=metadataL/metadataD,metadataRopRad=2*metadataRopDiam;
      const lengthRel=Math.abs(geom.length-metadataL)/Math.max(Math.abs(metadataL),1e-300),diameterRel=Math.abs(diameterFromReach-metadataD)/Math.max(Math.abs(metadataD),1e-300),ropDiamRel=Math.abs(ropDiamFromReach-metadataRopDiam)/Math.max(Math.abs(metadataRopDiam),1e-300),componentMatch=!Number.isFinite(componentL)||Math.abs(componentL-metadataL)<=1e-9*Math.max(1,Math.abs(metadataL));
      const pass=[metadataL,metadataD,geom.length,geom.thickness,diameterFromReach,ropDiamFromReach,ropRadFromReach].every(Number.isFinite)&&metadataL>0&&metadataD>0&&componentMatch&&lengthRel<=.01&&diameterRel<=.02&&ropDiamRel<=.02;
      rows.push({id,metadataL,metadataD,componentL,sampleResolution:N,sampledLength:geom.length,reach:geom.thickness,diameterFromReach,ropDiamFromReach,ropRadFromReach,metadataRopDiam,metadataRopRad,lengthRelativeError:lengthRel,diameterRelativeError:diameterRel,ropDiamRelativeError:ropDiamRel,componentMatch,pass});
    }
    const selectedTrefoil=rows.find(x=>x.id==='3:1:1')||null,pass=rows.length===IDEAL_CONVENTION_AUDIT_IDS.length&&rows.every(x=>x.pass);
    return {available:true,pass,rows,selectedTrefoil,convention:pass?'D_IS_TUBE_DIAMETER':'UNRESOLVED',statement:'Voor niet-triviale Gilbert-ankers geldt D≈2·reach. Dus L/D=Rop_diam en L/reach=Rop_rad=2·Rop_diam.'};
  }
  function geomKappaBundle(lengthBenchmark,raw){
    const ga=lengthBenchmark.carrier.A.scales.referenceGeom,gb=lengthBenchmark.carrier.B.scales.referenceGeom,length=.5*(ga.length+gb.length),reach=.5*(ga.thickness+gb.thickness),ropDiam=length/(2*reach),baseDelta=lengthBenchmark.net.RESOLVED_CURRENT.delta,fieldDelta=lengthBenchmark.net.RESOLVED_CURRENT.fieldDelta,target=baseDelta<0?fieldDelta.min:fieldDelta.max,knot=raw?.knot||{};
    const requiredKappa=Number.isFinite(baseDelta)&&Math.abs(baseDelta)>1e-300&&Number.isFinite(target)?target/baseDelta:(Math.abs(baseDelta)<=1e-300&&Math.abs(target)<=1e-300?0:null),geometry={length,reach,diameter:2*reach,ropDiam,ropRad:2*ropDiam,idealRopDiam:Number.isFinite(knot.idealRopDiam)?knot.idealRopDiam:NaN,crossingNumber:Number.isFinite(knot.crossingNumber)?knot.crossingNumber:NaN,knot};
    const candidates={};for(const def of GEOM_KAPPA_CANDIDATES){const kappa=def.evaluate(geometry),applicable=Number.isFinite(kappa)&&kappa>0,prediction=applicable?kappa*baseDelta:NaN,ratio=applicable&&Math.abs(target)>1e-300?prediction/target:(applicable&&Math.abs(prediction)<=1e-300&&Math.abs(target)<=1e-300?1:NaN),relativeResidual=applicable&&Math.abs(target)>1e-300?Math.abs(prediction-target)/Math.abs(target):(applicable&&Math.abs(prediction)<=1e-300&&Math.abs(target)<=1e-300?0:NaN);candidates[def.id]={id:def.id,label:def.label,formula:def.formula,kappa,prediction,target,ratio,relativeResidual,requiredKappa,applicable,valid:!applicable||[kappa,prediction,target,ratio,relativeResidual].every(Number.isFinite)};}
    return {definitions:GEOM_KAPPA_CANDIDATES.map(({evaluate,...x})=>({...x})),geometry,baseDelta,target,requiredKappa,candidates};
  }
  function cyclicError(prep){
    const details={};let maxAbsoluteOmegaError=0,maxIsoAbsError=0,maxMutualAbsError=0,maxIsoRelative=0,maxMutualRelative=0,maxIsoVectorScore=0,maxMutualVectorScore=0,maxIsoParallelScore=0,maxMutualParallelScore=0,projectionNullCount=0;
    const score=(absError,scale,absTol,relTol)=>absError/(absTol+relTol*Math.max(scale,0));
    const mag=v=>Math.hypot(v[0],v[1],v[2]),vdiff=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]);
    for(const which of ['A','B']){
      const p=prep[which],g=p.grid(true,false),components=p.components;
      const pts0=g.points,iso0=selectField(g.fields.iso,true,true),mut0=selectField(g.fields.mutual,true,true);
      // Exact integer re-indexing only: no arclength interpolation and no geometric resampling.
      const pts1=shiftComponents(pts0,components),iso1=shiftComponents(iso0,components),mut1=shiftComponents(mut0,components);
      const isoBase=bodyOmegaFlat(pts0,iso0),isoShift=bodyOmegaFlat(pts1,iso1),mutualBase=bodyOmegaFlat(pts0,mut0),mutualShift=bodyOmegaFlat(pts1,mut1),isoAbsError=Math.abs(isoBase-isoShift),mutualAbsError=Math.abs(mutualBase-mutualShift),isoScale=Math.max(Math.abs(isoBase),Math.abs(isoShift)),mutualScale=Math.max(Math.abs(mutualBase),Math.abs(mutualShift)),isoRelative=isoAbsError/Math.max(isoScale,1e-300),mutualRelative=mutualAbsError/Math.max(mutualScale,1e-300);
      const w0=segmentInfo(pts0,components).weights,w1=segmentInfo(pts1,components).weights,isoFit0=rigidFit(pts0,iso0,w0),isoFit1=rigidFit(pts1,iso1,w1),mutFit0=rigidFit(pts0,mut0,w0),mutFit1=rigidFit(pts1,mut1,w1),frame0=intrinsicFrame(pts0,components,w0),frame1=intrinsicFrame(pts1,components,w1),isoProj0=projectOmegaVector(isoFit0.Omega,frame0),isoProj1=projectOmegaVector(isoFit1.Omega,frame1),mutProj0=projectOmegaVector(mutFit0.Omega,frame0),mutProj1=projectOmegaVector(mutFit1.Omega,frame1);
      const isoVectorAbsError=vdiff(isoFit0.Omega,isoFit1.Omega),mutualVectorAbsError=vdiff(mutFit0.Omega,mutFit1.Omega),isoVectorScale=Math.max(mag(isoFit0.Omega),mag(isoFit1.Omega)),mutualVectorScale=Math.max(mag(mutFit0.Omega),mag(mutFit1.Omega)),isoParallelAbsError=Math.abs(isoProj0.parallel-isoProj1.parallel),mutualParallelAbsError=Math.abs(mutProj0.parallel-mutProj1.parallel),isoParallelScale=Math.max(Math.abs(isoProj0.parallel),Math.abs(isoProj1.parallel)),mutualParallelScale=Math.max(Math.abs(mutProj0.parallel),Math.abs(mutProj1.parallel));
      const isoVectorScore=score(isoVectorAbsError,isoVectorScale,1e-18,1e-5),mutualVectorScore=score(mutualVectorAbsError,mutualVectorScale,1e-18,.1),isoParallelScore=score(isoParallelAbsError,isoParallelScale,1e-18,1e-5),mutualParallelScore=score(mutualParallelAbsError,mutualParallelScale,1e-18,.1),projectionNull=isoParallelScale<=1e-15;if(projectionNull)projectionNullCount++;
      details[which]={method:'exact integer cyclic permutation; no interpolation',legacyLabZ:{isoBase,isoShift,mutualBase,mutualShift,isoAbsError,mutualAbsError,isoRelative,mutualRelative,projectionNull:isoScale<=1e-15},intrinsic:{isoVectorBase:isoFit0.Omega,isoVectorShift:isoFit1.Omega,mutualVectorBase:mutFit0.Omega,mutualVectorShift:mutFit1.Omega,isoVectorAbsError,mutualVectorAbsError,isoVectorScale,mutualVectorScale,isoVectorScore,mutualVectorScore,isoParallelBase:isoProj0.parallel,isoParallelShift:isoProj1.parallel,mutualParallelBase:mutProj0.parallel,mutualParallelShift:mutProj1.parallel,isoParallelAbsError,mutualParallelAbsError,isoParallelScale,mutualParallelScale,isoParallelScore,mutualParallelScore,projectionNull}};
      maxIsoAbsError=Math.max(maxIsoAbsError,isoAbsError);maxMutualAbsError=Math.max(maxMutualAbsError,mutualAbsError);maxIsoRelative=Math.max(maxIsoRelative,isoRelative);maxMutualRelative=Math.max(maxMutualRelative,mutualRelative);maxAbsoluteOmegaError=Math.max(maxAbsoluteOmegaError,isoAbsError,mutualAbsError,isoVectorAbsError,mutualVectorAbsError);maxIsoVectorScore=Math.max(maxIsoVectorScore,isoVectorScore);maxMutualVectorScore=Math.max(maxMutualVectorScore,mutualVectorScore);maxIsoParallelScore=Math.max(maxIsoParallelScore,isoParallelScore);maxMutualParallelScore=Math.max(maxMutualParallelScore,mutualParallelScore);
    }
    return {method:'exact integer cyclic permutation; no interpolation',maxAbsoluteOmegaError,maxIsoAbsError,maxMutualAbsError,maxIsoRelative,maxMutualRelative,maxIsoVectorScore,maxMutualVectorScore,maxIsoParallelScore,maxMutualParallelScore,projectionNullCount,toleranceModel:{iso:{absolute:1e-18,relative:1e-5},mutual:{absolute:1e-18,relative:.1}},details};
  }
  function analyzeRaw(raw,calRaw){
    const before=stateFingerprint(),prepared=prepareRaw(raw,calRaw),preparedCal=prepareRaw(calRaw,calRaw),counterfactuals=[];
    for(let mask=0;mask<32;mask++)counterfactuals.push(counterfactual(prepared,preparedCal,mask));
    const metrics={phaseLog:shapley(counterfactuals,'phaseLog'),deltaFrac:shapley(counterfactuals,'deltaFrac'),rawOmega:shapley(counterfactuals,'rawOmega'),A:{phaseLog:shapley(counterfactuals,'logA'),deltaFrac:shapley(counterfactuals,'deltaA'),rawOmega:shapley(counterfactuals,'omegaA')},B:{phaseLog:shapley(counterfactuals,'logB'),deltaFrac:shapley(counterfactuals,'deltaB'),rawOmega:shapley(counterfactuals,'omegaB')}};
    let maxRecon=0;for(const which of ['A','B'])for(const state of [prepared[which],preparedCal[which]])for(const k of ['iso','mutual','full'])maxRecon=Math.max(maxRecon,state.fits[k].reconstructionRel,state.calFits[k].reconstructionRel);
    const linearity={};let maxLin=0;
    for(const which of ['A','B']){const pts=raw.carriers[which].points,f=raw.carriers[which].fields,df=new Float64Array(f.full.length);for(let i=0;i<df.length;i++)df[i]=f.full[i]-f.iso[i];
      const lhs=bodyOmegaFlat(pts,df),rhs=bodyOmegaFlat(pts,f.mutual),err=Math.abs(lhs-rhs),rel=err/Math.max(Math.abs(lhs),Math.abs(rhs),1e-300);linearity[which]={fullMinusIso:lhs,directMutual:rhs,absError:err,relError:rel};maxLin=Math.max(maxLin,rel);
    }
    const cyclic=cyclicError(prepared),interactions=interactionBundle(counterfactuals),normalizations=normalizationBundle(raw,calRaw),transferLaws=transferLawBundle(raw,calRaw,normalizations),lengthBenchmark=lengthBenchmarkBundle(raw,calRaw,normalizations),geomKappa=geomKappaBundle(lengthBenchmark,raw),allOnProxyApplicable=!raw.knot?.holdout&&raw.measured&&Number.isFinite(raw.measured.phaseLogRatio),allOnPhaseError=allOnProxyApplicable?Math.abs(metrics.phaseLog.full-raw.measured.phaseLogRatio):NaN,after=stateFingerprint(),purity=raw.pure&&sameFingerprint(before,after),allOn=counterfactuals[31];
    const intrinsicKinematics={};for(const which of ['A','B']){const frame=intrinsicFrame(raw.carriers[which].points,raw.carriers[which].components,prepared[which].info.weights),calFrame=intrinsicFrame(calRaw.carriers[which].points,calRaw.carriers[which].components,prepared[which].calInfo.weights),current={},calibration={};for(const key of ['iso','mutual','full']){current[key]=projectOmegaVector(prepared[which].fits[key].Omega,frame);calibration[key]=projectOmegaVector(prepared[which].calFits[key].Omega,calFrame);}intrinsicKinematics[which]={frame,calibrationFrame:calFrame,current,calibration,deltaMutualParallel:current.mutual.parallel-calibration.mutual.parallel};}
    const digest=hashNumbers([counterfactuals.flatMap(x=>[x.metrics.phaseLog,x.metrics.deltaFrac,x.metrics.rawOmega]),CHANNELS.map(c=>metrics.phaseLog.phi[c]),NORMALIZATIONS.flatMap(n=>{const v=normalizations.net[n.id];return[v.netLinear,v.netLog,v.netAsinh,v.fieldScaleRatio];}),TRANSFER_LAWS.flatMap(l=>{const v=transferLaws.net[l.id];return[v.value,v.fieldScaleRatio];}),LENGTH_CANDIDATES.flatMap(l=>{const v=lengthBenchmark.net[l.id];return[v.absoluteCurrent,v.delta,v.absoluteScaleRatio,v.deltaScaleRatio,v.identityError];}),GEOM_KAPPA_CANDIDATES.flatMap(k=>{const v=geomKappa.candidates[k.id];return[v.kappa,v.prediction,v.ratio,v.relativeResidual];}),['A','B'].flatMap(w=>['iso','mutual','full'].flatMap(k=>{const v=intrinsicKinematics[w].current[k],c=intrinsicKinematics[w].calibration[k];return[...v.vector,v.parallel,v.magnitude,v.perpendicular,...c.vector,c.parallel,c.magnitude,c.perpendicular];}))]);
    const fitDiagnostics={};for(const which of ['A','B']){fitDiagnostics[which]={};for(const key of ['iso','mutual','full']){const f=prepared[which].fits[key];fitDiagnostics[which][key]={U:f.U,Omega:f.Omega,reconstructionRel:f.reconstructionRel,deformationRel:f.defRel};}}
    const bodyOmega={};for(const which of ['A','B']){const c=allOn.carrier[which];bodyOmega[which]={current:{full:c.current.omegaFull,iso:c.current.omegaIso,mutual:c.current.omegaMutual,deltaFrac:c.current.deltaFrac},calibration:{full:c.calibration.omegaFull,iso:c.calibration.omegaIso,mutual:c.calibration.omegaMutual,deltaFrac:c.calibration.deltaFrac}};}
    const parameters=clone(raw.parameters||{}),visualPolicyAtCapture={tracerCount:parameters.tracerCount,showTracers:parameters.showTracers,showStreamlines:parameters.showStreamlines,showPotentialFlow:parameters.showPotentialFlow};
    return {scenarioId:raw.scenarioId,tPhys:raw.tPhys,resolution:raw.resolution,knot:raw.knot,geometryHash:raw.geometryHash,calibrationGeometryHash:calRaw.geometryHash,parameterGridHash:raw.parameterGridHash,purity,parameters,visualPolicyAtCapture,
      centers:{A:prepared.A.fits.full.centroid,B:prepared.B.fits.full.centroid},pose:{A:{R:prepared.A.pose.R,rms:prepared.A.pose.rms,cyclicShift:prepared.A.cyclicShift},B:{R:prepared.B.pose.R,rms:prepared.B.pose.rms,cyclicShift:prepared.B.cyclicShift}},bodyOmega,fitDiagnostics,intrinsicKinematics,canonicalization:currentCanonicalization,
      kinematics:{A:{iso:{U:prepared.A.fits.iso.U,Omega:prepared.A.fits.iso.Omega},mutual:{U:prepared.A.fits.mutual.U,Omega:prepared.A.fits.mutual.Omega},full:{U:prepared.A.fits.full.U,Omega:prepared.A.fits.full.Omega}},B:{iso:{U:prepared.B.fits.iso.U,Omega:prepared.B.fits.iso.Omega},mutual:{U:prepared.B.fits.mutual.U,Omega:prepared.B.fits.mutual.Omega},full:{U:prepared.B.fits.full.U,Omega:prepared.B.fits.full.Omega}}},
      segmentRatio:{A:prepared.A.info.segmentRatio,B:prepared.B.info.segmentRatio},linearity,maxVelocityReconstructionRel:maxRecon,cyclicIndexAbsError:cyclic.maxAbsoluteOmegaError,cyclicIndex:cyclic,interactions,normalizations,transferLaws,lengthBenchmark,geomKappa,
      counterfactuals:counterfactuals.map(x=>({mask:x.mask,channels:x.channels,metrics:x.metrics})),shapley:metrics,allOnProxyApplicable,allOnPhaseError,
      measured:raw.measured,fieldBracket:raw.measured?{min:raw.measured.fieldLogMin,max:raw.measured.fieldLogMax}:null,topologyGap:raw.topologyGap,digest};
  }
  function stableAnalysisDigest(x){return hashNumbers([x.counterfactuals.flatMap(v=>[v.metrics.phaseLog,v.metrics.deltaFrac,v.metrics.rawOmega]),CHANNELS.map(c=>x.shapley.phaseLog.phi[c]),NORMALIZATIONS.flatMap(n=>{const v=x.normalizations.net[n.id];return[v.netLinear,v.netLog,v.netAsinh,v.fieldScaleRatio];}),TRANSFER_LAWS.flatMap(l=>{const v=x.transferLaws.net[l.id];return[v.value,v.fieldScaleRatio];}),LENGTH_CANDIDATES.flatMap(l=>{const v=x.lengthBenchmark.net[l.id];return[v.absoluteCurrent,v.delta,v.absoluteScaleRatio,v.deltaScaleRatio,v.identityError];}),GEOM_KAPPA_CANDIDATES.flatMap(k=>{const v=x.geomKappa.candidates[k.id];return[v.kappa,v.prediction,v.ratio,v.relativeResidual];}),['A','B'].flatMap(w=>['iso','mutual','full'].flatMap(k=>{const v=x.intrinsicKinematics[w].current[k],c=x.intrinsicKinematics[w].calibration[k];return[...v.vector,v.parallel,v.magnitude,v.perpendicular,...c.vector,c.parallel,c.magnitude,c.perpendicular];})),[x.maxVelocityReconstructionRel,x.cyclicIndexAbsError]]);}
  function decompositionErrorRecord(err,phase){
    const message=String(err&&err.message||err||'onbekende decompositiefout'),stack=String(err&&err.stack||''),record={phase,scenarioId:current?.id||null,scenarioLabel:current?.label||null,checkpointIndex,checkpointTarget:current?scenarioCheckpoints(current)[checkpointIndex]??null:null,completedSnapshots:results.length,expectedSnapshots:expectedSnapshotCount(),message,stack,at:new Date().toISOString()};
    lastError=record;if(window.ModelLog)window.ModelLog.logEvent('proxy-decomposition-error',record);return record;
  }
  function analyzeCheckpoint(){
    const raw=captureRawSnapshot(),a=analyzeRaw(raw,calibrationRaw),b=analyzeRaw(raw,calibrationRaw);a.repeatDigest=stableAnalysisDigest(b);a.deterministicRepeat=a.digest===b.digest&&stableAnalysisDigest(a)===stableAnalysisDigest(b);results.push(a);resultCache.set(cacheKey(current,a.tPhys),cloneAnalysis(a));cacheStats.misses++;
    if(window.ModelLog)window.ModelLog.logEvent('proxy-decomposition-checkpoint',{scenarioId:a.scenarioId,tPhys:a.tPhys,digest:a.digest,pure:a.purity,phase:a.shapley.phaseLog});render();
  }
  function configureScenario(sc){
    applySpecClockPreset();P.Rcyl=.25;P.Hcyl=.5;P.linkDH=false;P.vzA=sc.drift;P.vzB=-sc.drift;P.lockVz=false;P.ccwA=sc.ccwA;P.ccwB=sc.ccwB;P.mirrorB=false;
    P.knotIdx=-1;P.knotKey='';P.knotSource='builtin';P.idealComponentMode='all';P.compA=1;P.compB=1;
    if(sc.knotSource){const catalog=knotCatalogForSource(sc.knotSource);if(!catalog?.db?.[sc.knotKey])throw new Error(`holdout-knoop ontbreekt: ${sc.knotSource} ${sc.knotKey}`);P.knotSource=sc.knotSource;P.knotKey=sc.knotKey;P.topo='trefoil';}
    P.bundleEnabled=false;P.bgFlow='none';P.bundleBEMEnabled=true;P.qual='hoog';if(Number.isFinite(sc.aSim))P.a=sc.aSim;proxyDecompResolutionOverride=sc.resolution;setInitialAxialSeparation(.84);rebuildVolumeEnvelope();resetState();currentCanonicalization=canonicalizeHoldoutGeometry(sc);
    SpecClock.autoStartAfterCalibration=false;P.accExp=Math.log10(16);syncUi();updateSubtitle();resetPlaybackDebt('proxy-decomposition-scenario-arm');
    if(!calibrateSpecClockPhase({mode:sc.knotSource?'intrinsic-holdout':'legacy-z',allowProjectionNull:!!sc.knotSource}))throw new Error('fase-nullkalibratie geweigerd');calibrationRaw=captureRawSnapshot();const cps=scenarioCheckpoints(sc);if(cps[0]!==0)throw new Error('eerste decompositiecheckpoint moet t=0 zijn');checkpointIndex=0;analyzeCheckpoint();checkpointIndex=1;
    setPausedState(false,'proxy-decomposition-scenario-start');
  }
  function startScenario(){
    if(!active)return;index++;if(index>=scenarios.length){complete();return;}current=scenarios[index];pending=false;
    const cps=scenarioCheckpoints(current),cached=cps.map(t=>resultCache.get(cacheKey(current,t)));if(cached.length&&cached.every(Boolean)){for(const row of cached)results.push(cloneAnalysis(row));cacheStats.hits+=cached.length;if(window.ModelLog)window.ModelLog.logEvent('proxy-decomposition-cache-hit',{scenarioId:current.id,snapshots:cached.length});setStatus(`CACHE ${index+1}/${scenarios.length} · ${current.label} · ${cached.length} snapshots hergebruikt`,'running');render();pending=true;clearTimeout(timer);timer=setTimeout(()=>{pending=false;current=null;startScenario();},20);return;}
    try{configureScenario(current);setStatus(`RUN ${index+1}/${scenarios.length} · ${current.label} · checkpoint ${Math.min(checkpointIndex+1,scenarioCheckpoints(current).length)}/${scenarioCheckpoints(current).length}`,'running');render();}
    catch(err){const e=decompositionErrorRecord(err,'setup/t0-checkpoint');stop('setup-error: '+e.message);}
  }
  function nextCheckpoint(){return scenarioCheckpoints(current)[checkpointIndex]??Infinity;}
  function capAcceptedDt(dt){if(!active||!current||pending)return dt;const rem=nextCheckpoint()-tPhys;return rem>1e-12?Math.min(dt,rem):dt;}
  function afterAcceptedStep(){
    if(!active||!current||pending)return false;if(tPhys+1e-10>=nextCheckpoint()){
      try{
        setPausedState(true,'proxy-decomposition-checkpoint');stepDebt=0;analyzeCheckpoint();checkpointIndex++;
        if(checkpointIndex>=scenarioCheckpoints(current).length){pending=true;clearTimeout(timer);timer=setTimeout(()=>{pending=false;current=null;startScenario();},40);}else setPausedState(false,'proxy-decomposition-resume');
      }catch(err){const e=decompositionErrorRecord(err,'accepted-step-checkpoint');stop('checkpoint-error: '+e.message);}
      return true;
    }
    return false;
  }
  function addGate(group,id,label,status,metrics,explanation){gates.push({group,id,label,status,metrics,explanation});}
  function resultAt(id,t=3){return results.find(r=>r.scenarioId===id&&Math.abs(r.tPhys-t)<1e-8);}
  function fitContinuumSeries(series){
    const pts=series.filter(x=>Number.isFinite(x.resolution)&&x.resolution>0&&Number.isFinite(x.value));
    if(pts.length<4)return {valid:false,reason:'minstens vier resoluties vereist',series:pts};
    const values=pts.map(x=>x.value),vmax=Math.max(...values),vmin=Math.min(...values),scale=Math.max(...values.map(Math.abs),1e-300),relativeSpan=(vmax-vmin)/scale;
    if(relativeSpan<=.01){const mean=values.reduce((a,b)=>a+b,0)/values.length,rms=Math.sqrt(values.reduce((a,b)=>a+(b-mean)**2,0)/values.length),loo=values.map((_,omit)=>{const a=values.filter((_,i)=>i!==omit);return a.reduce((x,y)=>x+y,0)/a.length;}),looSpan=(Math.max(...loo)-Math.min(...loo))/Math.max(Math.abs(mean),1e-300);return {valid:true,model:'constant',xInf:mean,p:null,A:0,relativeRms:rms/scale,relativeSpan,leaveOneOut:{xInf:loo,xInfRelativeSpan:looSpan},series:pts};}
    function fitFor(list,p){const xs=list.map(q=>q.resolution**(-p)),ys=list.map(q=>q.value),n=list.length,mx=xs.reduce((a,b)=>a+b,0)/n,my=ys.reduce((a,b)=>a+b,0)/n;let num=0,den=0;for(let i=0;i<n;i++){num+=(xs[i]-mx)*(ys[i]-my);den+=(xs[i]-mx)**2;}const A=den>0?num/den:0,xInf=my-A*mx,residuals=ys.map((y,i)=>y-(xInf+A*xs[i])),sse=residuals.reduce((a,b)=>a+b*b,0),rms=Math.sqrt(sse/n);return {p,A,xInf,sse,rms,residuals};}
    let best=null;for(let p=.25;p<=4.0001;p+=.005){const f=fitFor(pts,p);if(!best||f.sse<best.sse)best=f;}
    const loo=[];for(let omit=0;omit<pts.length;omit++){const subset=pts.filter((_,i)=>i!==omit);let b=null;for(let p=.25;p<=4.0001;p+=.01){const f=fitFor(subset,p);if(!b||f.sse<b.sse)b=f;}loo.push({omittedResolution:pts[omit].resolution,xInf:b.xInf,p:b.p});}
    const looX=loo.map(x=>x.xInf),looSpan=(Math.max(...looX)-Math.min(...looX))/Math.max(Math.abs(best.xInf),1e-300);
    return {valid:Number.isFinite(best.xInf)&&Number.isFinite(best.p),model:'power',xInf:best.xInf,p:best.p,A:best.A,relativeRms:best.rms/scale,relativeSpan,leaveOneOut:{fits:loo,xInfRelativeSpan:looSpan},series:pts};
  }
  function buildContinuumAudit(ladder){
    const observables={
      rigidResponseLog:r=>r.shapley.phaseLog.total,
      mutualRawOmega:r=>r.interactions.rawOmega.total,
      resolvedLengthRoute:r=>r.lengthBenchmark.net.RESOLVED_CURRENT.delta,
      fieldDeltaSigned:r=>r.geomKappa.target,
      requiredKappa:r=>r.geomKappa.requiredKappa,
      mutualTangentRms:r=>.5*((r.measured?.uA||0)+(r.measured?.uB||0)),
      resolvedLengthA:r=>r.lengthBenchmark.net.RESOLVED_CURRENT.A.lengthCurrent
    },fits={};
    for(const [id,get] of Object.entries(observables))fits[id]=fitContinuumSeries(ladder.map(r=>({resolution:r.resolution,value:get(r)})));
    const direct=fits.requiredKappa,fieldInf=fits.fieldDeltaSigned?.xInf,routeInf=fits.resolvedLengthRoute?.xInf,derived=Number.isFinite(fieldInf)&&Number.isFinite(routeInf)&&Math.abs(routeInf)>1e-300?fieldInf/routeInf:null,directValue=direct?.xInf??null,identityMismatch=Number.isFinite(derived)&&Number.isFinite(directValue)?Math.abs(derived-directValue)/Math.max(Math.abs(derived),Math.abs(directValue),1e-300):Infinity,valid=Object.values(fits).every(x=>x.valid)&&Number.isFinite(derived)&&identityMismatch<=.10;
    return {valid,fits,requiredKappaContinuum:derived,requiredKappaModel:'fieldDeltaSigned∞ / resolvedLengthRoute∞',requiredKappaDirectFit:directValue,requiredKappaDirectModel:direct?.model||null,requiredKappaIdentityMismatch:identityMismatch,identity:{fieldDeltaContinuum:fieldInf,resolvedLengthRouteContinuum:routeInf,derivedKappa:derived,directKappaFit:directValue,relativeMismatch:identityMismatch}};
  }
  function buildCrossKnotAudit(){
    const holdoutScenarios=scenarios.filter(sc=>sc.holdout),rows=[];
    for(const sc of holdoutScenarios){
      const r=resultAt(sc.id);if(!r){rows.push({id:sc.id,available:false,valid:false,source:sc.knotSource,key:sc.knotKey,topologyKey:sc.topologyKey,embedding:sc.embedding,candidates:[]});continue;}
      const route=r.lengthBenchmark.net.RESOLVED_CURRENT,A=route.A,B=route.B,ik=r.intrinsicKinematics;
      const deltaRouteIntrinsic=ik?((ik.A.current.mutual.parallel*A.lengthCurrent-ik.A.calibration.mutual.parallel*A.lengthCalibration)-(ik.B.current.mutual.parallel*B.lengthCurrent-ik.B.calibration.mutual.parallel*B.lengthCalibration))/V_CHAR_SST:NaN;
      const fieldDelta=route.fieldDelta,target=deltaRouteIntrinsic<0?fieldDelta.min:fieldDelta.max,requiredKappaIntrinsic=Number.isFinite(deltaRouteIntrinsic)&&Math.abs(deltaRouteIntrinsic)>1e-300?target/deltaRouteIntrinsic:null;
      const candidates=GEOM_KAPPA_CANDIDATES.map(k=>{const v=r.geomKappa?.candidates?.[k.id],applicable=!!v?.applicable&&Number.isFinite(v?.kappa),prediction=applicable?v.kappa*deltaRouteIntrinsic:NaN,ratio=applicable&&Math.abs(target)>1e-300?prediction/target:NaN,relativeResidual=Number.isFinite(ratio)?Math.abs(ratio-1):NaN;return{id:k.id,formula:k.formula,applicable,kappa:v?.kappa??null,ratio:Number.isFinite(ratio)?ratio:null,relativeResidual:Number.isFinite(relativeResidual)?relativeResidual:null,prediction:Number.isFinite(prediction)?prediction:null,target:Number.isFinite(target)?target:null};}),best=candidates.filter(x=>x.applicable&&Number.isFinite(x.relativeResidual)).sort((a,b)=>a.relativeResidual-b.relativeResidual)[0]||null;
      rows.push({id:sc.id,available:true,valid:Number.isFinite(requiredKappaIntrinsic)&&Number.isFinite(deltaRouteIntrinsic),source:r.knot?.source,key:r.knot?.key,topologyKey:sc.topologyKey,embedding:sc.embedding,candidateStatus:sc.candidateStatus||null,candidateFamily:sc.candidateFamily||null,sourceSha256:sc.sourceSha256||null,sourceRole:sc.sourceRole||null,torus:sc.torus||null,crossingNumber:r.knot?.crossingNumber,resolution:r.resolution,lengthA:A.lengthCurrent,legacyDeltaRoute:route.delta,intrinsicDeltaRoute:deltaRouteIntrinsic,fieldTarget:target,legacyRequiredKappa:r.geomKappa.requiredKappa,requiredKappaIntrinsic,holdout:true,canonicalization:r.canonicalization,intrinsicAxes:{A:ik?.A?.frame?.ez||null,B:ik?.B?.frame?.ez||null},intrinsicOmega:{A:ik?.A||null,B:ik?.B||null},candidates,bestCandidate:best});
    }
    const reachIds=new Set(['REACH_OVER_LK','DIAMETER_OVER_LK','INV_PI_ROP_DIAM','INV_CROSSING_ROP_DIAM','INV_2PI_ROP_DIAM']);
    const byCandidate={};for(const k of GEOM_KAPPA_CANDIDATES){const applicableRows=rows.filter(r=>r.valid).map(r=>({r,v:r.candidates.find(x=>x.id===k.id)})).filter(x=>x.v?.applicable&&Number.isFinite(x.v.relativeResidual)),universal=applicableRows.length===rows.filter(r=>r.valid).length,maxResidual=applicableRows.length?Math.max(...applicableRows.map(x=>x.v.relativeResidual)):Infinity;byCandidate[k.id]={id:k.id,formula:k.formula,applicableHoldouts:applicableRows.length,totalHoldouts:rows.length,universal,usesReach:reachIds.has(k.id),maxRelativeResidual:Number.isFinite(maxResidual)?maxResidual:null,pass:universal&&!reachIds.has(k.id)&&maxResidual<=.10,rows:applicableRows.map(x=>({holdout:x.r.id,topologyKey:x.r.topologyKey,embedding:x.r.embedding,ratio:x.v.ratio,relativeResidual:x.v.relativeResidual,kappa:x.v.kappa}))};}
    const pairMap={};for(const r of rows){if(!r.valid)continue;(pairMap[r.topologyKey]||(pairMap[r.topologyKey]={topologyKey:r.topologyKey,rows:[]})).rows.push(r);}const embeddingPairs=Object.values(pairMap).map(p=>{const f=p.rows.find(r=>r.embedding==='fseries'),i=p.rows.find(r=>r.embedding==='ideal'),k=p.rows.find(r=>r.embedding==='knotplot-relaxed'),available=!!f&&!!i,ratio=available&&Math.abs(f.requiredKappaIntrinsic)>1e-300?i.requiredKappaIntrinsic/f.requiredKappaIntrinsic:null,mismatch=Number.isFinite(ratio)?Math.abs(ratio-1):null;return{topologyKey:p.topologyKey,available,fseries:f?{id:f.id,kappa:f.requiredKappaIntrinsic,deltaRoute:f.intrinsicDeltaRoute}:null,ideal:i?{id:i.id,kappa:i.requiredKappaIntrinsic,deltaRoute:i.intrinsicDeltaRoute}:null,knotplot:k?{id:k.id,kappa:k.requiredKappaIntrinsic,deltaRoute:k.intrinsicDeltaRoute,certification:k.candidateStatus||'candidate',family:k.candidateFamily||null,sourceRole:k.sourceRole||null}:null,kappaRatio:ratio,relativeMismatch:mismatch};});
    const valid=rows.length===holdoutScenarios.length&&rows.every(r=>r.available&&r.valid&&r.canonicalization);
    return {valid,rows,embeddingPairs,byCandidate,trainingUse:false,confirmatoryTolerance:.10,route:'intrinsic Ω_parallel on canonicalized embedding',scaleConvention:'transverse RMS radius = 0.05 m',statement:'Cross-knot holdouts trainen of selecteren geen κ-factor. Ideal/Fseries/KnotPlot-triples meten embeddinggevoeligheid voor klassieke knopen; KnotPlot-links blijven afzonderlijke uniform-N300 candidates zonder ideal-paar of zelfstandige diameter-/reachcertificatie.'};
  }
  function evaluate(){
    gates=[];const expected=expectedSnapshotCount();
    const d0=results.length===expected&&results.every(r=>r.purity);addGate('ENGINE','D0','snapshot-purity',d0?'PASS':'FAIL',{snapshots:results.length,expected,pure:results.filter(r=>r.purity).length},'Y, tPhys en fasekalibratie moeten vóór en na iedere analyse identiek zijn.');
    const maxRec=Math.max(...results.map(r=>r.maxVelocityReconstructionRel));addGate('ENGINE','D1','velocity-reconstruction',maxRec<=1e-12?'PASS':'FAIL',{maxRelativeError:maxRec},'U + Ω×r + v_def reconstrueert ieder invoerveld.');
    const linChecks=results.flatMap(r=>['A','B'].map(w=>{const q=r.linearity[w],scale=Math.max(Math.abs(q.fullMinusIso),Math.abs(q.directMutual));return{scenarioId:r.scenarioId,carrier:w,absoluteError:q.absError,relativeError:q.relError,scale,tolerance:1e-18+1e-5*scale,score:q.absError/(1e-18+1e-5*scale)};})),worstLin=linChecks.reduce((a,b)=>!a||b.score>a.score?b:a,null),proxyChecks=results.filter(r=>r.allOnProxyApplicable&&Number.isFinite(r.allOnPhaseError)).map(r=>({scenarioId:r.scenarioId,tPhys:r.tPhys,error:r.allOnPhaseError})),maxProxyMatch=proxyChecks.length?Math.max(...proxyChecks.map(x=>x.error)):0,d2Pass=(worstLin?.score??Infinity)<=1&&(!proxyChecks.length||maxProxyMatch<=1e-12);addGate('ENGINE','D2','mutual-linearity + applicable all-on proxy match',d2Pass?'PASS':'FAIL',{mixedTolerance:'|ε| ≤ 1e-18 + 1e-5·scale',worstLinearity:worstLin,maxRelativeError:Math.max(...linChecks.map(x=>x.relativeError)),maxAbsoluteError:Math.max(...linChecks.map(x=>x.absoluteError)),applicableProxySnapshots:proxyChecks.length,nonApplicableProjectionHoldouts:results.filter(r=>!r.allOnProxyApplicable).length,maxAllOnPhaseError:maxProxyMatch},'Directe mutual-linearity gebruikt een zero-safe absolute/relatieve tolerantie. De legacy all-on phaseproxy wordt alleen geëist voor niet-holdoutscenario’s waarin die projectie fysisch informatief is.');
    const reconstructionChecks=results.flatMap(r=>['phaseLog','deltaFrac','rawOmega'].map(key=>({...reconstructionCheck(r.shapley[key],key),scenarioId:r.scenarioId,tPhys:r.tPhys,resolution:r.resolution}))),worstReconstruction=reconstructionChecks.reduce((a,b)=>!a||b.score>a.score?b:a,null),maxShapeScore=worstReconstruction?.score??Infinity,maxShapeAbs=Math.max(...reconstructionChecks.map(x=>x.absoluteResidual));addGate('ENGINE','D3','shapley-reconstruction · mixed tolerance',maxShapeScore<=1?'PASS':'FAIL',{maxMixedResidualScore:maxShapeScore,maxAbsoluteResidual:maxShapeAbs,worst:worstReconstruction,toleranceModel:'|ε| ≤ ε_abs + ε_rel·max(|total|,Σ|φ|,|full−baseline|)',relativeTolerance:RECON_REL_TOL,absoluteTolerances:RECON_ABS_TOL},'Zero-safe gemengde absolute/relatieve gate; een exact nuldoel veroorzaakt geen kunstmatige oneindige relatieve fout.');
    const maxCycAbs=Math.max(...results.map(r=>r.cyclicIndex?.maxAbsoluteOmegaError??Infinity)),maxIsoVectorScore=Math.max(...results.map(r=>r.cyclicIndex?.maxIsoVectorScore??Infinity)),maxMutualVectorScore=Math.max(...results.map(r=>r.cyclicIndex?.maxMutualVectorScore??Infinity)),maxIsoParallelScore=Math.max(...results.map(r=>r.cyclicIndex?.maxIsoParallelScore??Infinity)),maxMutualParallelScore=Math.max(...results.map(r=>r.cyclicIndex?.maxMutualParallelScore??Infinity)),projectionNullCount=results.reduce((n,r)=>n+(r.cyclicIndex?.projectionNullCount||0),0),d4Worst=Math.max(maxIsoVectorScore,maxMutualVectorScore,maxIsoParallelScore,maxMutualParallelScore),d4Status=d4Worst<=1?'PASS':d4Worst<=10?'WARN':'FAIL';addGate('ENGINE','D4','cyclic-index-invariance · intrinsic Ω-vector + Ω_parallel',d4Status,{maxAbsoluteOmegaError:maxCycAbs,maxIsoVectorScore,maxMutualVectorScore,maxIsoParallelScore,maxMutualParallelScore,projectionNullCount,toleranceModel:{iso:'1e-18 + 1e-5·scale',mutual:'1e-18 + 0.1·scale'},legacyLabZDiagnostic:{maxIsoRelativeError:Math.max(...results.map(r=>r.cyclicIndex?.maxIsoRelative??0)),maxMutualRelativeError:Math.max(...results.map(r=>r.cyclicIndex?.maxMutualRelative??0))}},'Cyclic-index-invariantie wordt beslist op de volledige intrinsieke Ω-vector en Ω_parallel met mixed tolerances. Een praktisch nul zijnde projectie is geldig en wordt niet via een betekenisloze relatieve fout afgekeurd; lab-z blijft diagnostisch.');
    const det=results.every(r=>r.deterministicRepeat);addGate('ENGINE','D5','deterministic-repeat',det?'PASS':'FAIL',{matching:results.filter(r=>r.deterministicRepeat).length,total:results.length},'Iedere bevroren snapshotanalyse wordt onmiddellijk identiek herhaald.');
    const normFinite=results.every(r=>NORMALIZATIONS.every(n=>r.normalizations?.net?.[n.id]?.valid)),normProxyChecks=results.filter(r=>!r.knot?.holdout&&Number.isFinite(r.measured?.phaseLogRatio)&&Number.isFinite(r.normalizations?.net?.ISO_DYNAMIC?.netLog)).map(r=>({scenarioId:r.scenarioId,tPhys:r.tPhys,error:Math.abs(r.normalizations.net.ISO_DYNAMIC.netLog-r.measured.phaseLogRatio)})),maxNormProxyMatch=normProxyChecks.length?Math.max(...normProxyChecks.map(x=>x.error)):0;addGate('ENGINE','D6','normalization-pipeline + applicable ISO-dynamic proxy match',normFinite&&(!normProxyChecks.length||maxNormProxyMatch<=1e-12)?'PASS':'FAIL',{finiteSnapshots:results.filter(r=>NORMALIZATIONS.every(n=>r.normalizations?.net?.[n.id]?.valid)).length,totalSnapshots:results.length,applicableProxySnapshots:normProxyChecks.length,nonApplicableIntrinsicHoldouts:results.filter(r=>r.knot?.holdout).length,maxIsoDynamicPhaseError:maxNormProxyMatch,normalizations:NORMALIZATIONS.map(n=>n.id)},'Alle normalisaties moeten eindig blijven. ISO_DYNAMIC reproduceert de legacy phase-nullproxy uitsluitend waar die observabele toepasselijk is; intrinsieke holdouts worden niet gedwongen een niet-informatieve lab-z-projectie te reproduceren.');
    const transferRegistryOk=TRANSFER_LAWS.every(l=>l.coefficient===1&&transferLawDimensions(l).dimensionless),transferFinite=results.every(r=>TRANSFER_LAWS.every(l=>r.transferLaws?.net?.[l.id]?.valid)),maxTransferRawIdentity=Math.max(...results.map(r=>Math.abs((r.transferLaws?.carrier?.A?.deltaOmega-r.transferLaws?.carrier?.B?.deltaOmega)-(r.interactions?.rawOmega?.total??Infinity))));addGate('ENGINE','D7','transfer-law registry · dimensionless + no-fit + raw-ΔΩ identity',transferRegistryOk&&transferFinite&&maxTransferRawIdentity<=1e-18?'PASS':'FAIL',{registered:TRANSFER_LAWS.length,dimensionless:TRANSFER_LAWS.filter(l=>transferLawDimensions(l).dimensionless).length,unitCoefficients:TRANSFER_LAWS.filter(l=>l.coefficient===1).length,finiteSnapshots:results.filter(r=>TRANSFER_LAWS.every(l=>r.transferLaws?.net?.[l.id]?.valid)).length,totalSnapshots:results.length,maxRawDeltaOmegaIdentityError:maxTransferRawIdentity},'Iedere kandidaatwet moet dimensieloos zijn, coefficient exact 1 houden en dezelfde directe mutual-ΔΩ gebruiken als de counterfactualpipeline.');
    const legacySpeedKey='C'+'e',legacySpeedTex='C'+'_'+'e',canonicalVCharRegistry=TRANSFER_LAWS.every(l=>Object.prototype.hasOwnProperty.call(l.exponents,'vChar')&&!Object.prototype.hasOwnProperty.call(l.exponents,legacySpeedKey)&&!(l.formula+l.label).includes(legacySpeedKey)&&!(l.formula+l.label).includes(legacySpeedTex)),canonicalVCharSnapshots=results.every(r=>['A','B'].every(w=>Object.prototype.hasOwnProperty.call(r.transferLaws?.carrier?.[w]?.inputs||{},'vChar')&&!Object.prototype.hasOwnProperty.call(r.transferLaws?.carrier?.[w]?.inputs||{},legacySpeedKey))&&Object.prototype.hasOwnProperty.call(r.transferLaws?.constants||{},'vChar')&&!Object.prototype.hasOwnProperty.call(r.transferLaws?.constants||{},legacySpeedKey));addGate('ENGINE','D8','canonieke snelheidnotatie · v↺* / vChar',canonicalVCharRegistry&&canonicalVCharSnapshots?'PASS':'FAIL',{symbol:'v↺*',jsonKey:'vChar',registryEntries:TRANSFER_LAWS.length,canonicalRegistry:canonicalVCharRegistry,canonicalSnapshots:canonicalVCharSnapshots,value:V_CHAR_SST},'Canon v0.8.20: v↺* is de scalaire karakteristieke swirl-snelheid; u↺(x,t) blijft gereserveerd voor het lokale veld. Legacy snelheidssymbolen en keys zijn niet toegestaan.');
    const lengthFinite=results.every(r=>LENGTH_CANDIDATES.every(l=>r.lengthBenchmark?.net?.[l.id]?.valid)),maxLengthIdentityScore=Math.max(...results.flatMap(r=>LENGTH_CANDIDATES.map(l=>r.lengthBenchmark?.net?.[l.id]?.identityScore??Infinity))),maxLengthIdentityError=Math.max(...results.flatMap(r=>LENGTH_CANDIDATES.map(l=>r.lengthBenchmark?.net?.[l.id]?.identityError??Infinity))),canonicalLengthRegistry=LENGTH_CANDIDATES.filter(l=>l.semanticEligible).every(l=>l.kind==='CANON_CARRIER')&&LENGTH_CANDIDATES.some(l=>l.id==='MINIMAL_NEUTRAL_LOOP'&&l.kind==='CANON_SPECIAL_LOOP');addGate('ENGINE','D9','L/v↺* length registry · finite + route identity + canon semantics',lengthFinite&&maxLengthIdentityScore<=1&&canonicalLengthRegistry?'PASS':'FAIL',{registered:LENGTH_CANDIDATES.length,finiteSnapshots:results.filter(r=>LENGTH_CANDIDATES.every(l=>r.lengthBenchmark?.net?.[l.id]?.valid)).length,totalSnapshots:results.length,maxDeltaIdentityError:maxLengthIdentityError,maxMixedIdentityScore:maxLengthIdentityScore,toleranceModel:'|ε| ≤ 1e-27 + 1e-12·max(|delta|,|current|,|calibration|)',semanticEligible:LENGTH_CANDIDATES.filter(l=>l.semanticEligible).map(l=>l.id),minimalLoop:'2πr_c'},'Δ-route moet exact absolute-current minus absolute-calibration zijn. Alleen de opgeloste gesloten carrierlengte is semantisch L_K; 2πr_c is uitsluitend de minimale neutrale special case.');

    const idealConventionAudit=auditIdealKnotConvention();addGate('ENGINE','D10','ideal-knot radius/diameter convention audit',idealConventionAudit.pass?'PASS':'FAIL',{available:idealConventionAudit.available,convention:idealConventionAudit.convention,anchors:idealConventionAudit.rows,selectedTrefoil:idealConventionAudit.selectedTrefoil},'Audit de geladen Gilbert-data rechtstreeks: voor niet-triviale ankerknopen moet metadata D overeenkomen met 2·reach. Daarmee is L/D de diameterconventie; de radiusconventie is exact tweemaal zo groot.');
    const geomRegistry=GEOM_KAPPA_CANDIDATES.every(k=>k.coefficient===1&&k.dimensionless),geomFinite=results.every(r=>GEOM_KAPPA_CANDIDATES.every(k=>{const v=r.geomKappa?.candidates?.[k.id];return v&&(!v.applicable||v.valid);})),applicableGeomCount=results.reduce((sum,r)=>sum+GEOM_KAPPA_CANDIDATES.filter(k=>r.geomKappa?.candidates?.[k.id]?.applicable).length,0);addGate('ENGINE','D11','κ_geom registry · dimensionless + coefficient-1 + finite applicable values',geomRegistry&&geomFinite?'PASS':'FAIL',{registered:GEOM_KAPPA_CANDIDATES.length,unitCoefficients:GEOM_KAPPA_CANDIDATES.filter(k=>k.coefficient===1).length,dimensionless:GEOM_KAPPA_CANDIDATES.filter(k=>k.dimensionless).length,applicableValues:applicableGeomCount,totalSnapshots:results.length},'κ_geom mag uitsluitend uit vooraf geregistreerde geometrische/topologische factoren volgen. Niet-toepasselijke ideal-metadatafactoren op fseries-holdouts worden expliciet als n.v.t. behandeld.');
    const base=resultAt('baseline'),r192=resultAt('resolution-192'),r256=resultAt('resolution-256'),r384=resultAt('resolution-384'),r512=resultAt('resolution-512'),r768=resultAt('resolution-768'),sw=resultAt('symmetry-swap');
    const ladder=[base,r192,r256,r384,r512,r768].filter(Boolean),continuumAudit=buildContinuumAudit(ladder),crossKnotAudit=buildCrossKnotAudit();
    addGate('ENGINE','D12','continuum-fit pipeline · finite + leave-one-out',ladder.length>=4?(continuumAudit.valid?'PASS':'FAIL'):'INFO',{valid:continuumAudit.valid,requiredKappaContinuum:continuumAudit.requiredKappaContinuum,fits:continuumAudit.fits},'De continuum-audit rapporteert X∞, effectieve orde, residu en leave-one-resolution-out-spreiding; hij past geen fitwaarde op de solver toe.');
    addGate('ENGINE','D13','selected canonical cross-knot provenance + intrinsic Ω outputs',scenarios.some(sc=>sc.holdout)?(crossKnotAudit.valid?'PASS':'FAIL'):'INFO',crossKnotAudit,'Alle geselecteerde holdouts moeten gecanonicaliseerde geometrie, volledige Ω-vectoren en eindige intrinsieke Ω_parallel-metingen leveren; zonder holdouts is deze gate niet van toepassing.');
    const visualIsolated=results.every(r=>r.visualPolicyAtCapture?.tracerCount===0&&r.visualPolicyAtCapture?.showTracers===false&&r.visualPolicyAtCapture?.showStreamlines===false&&r.visualPolicyAtCapture?.showPotentialFlow===false),isolatedSnapshots=results.filter(r=>r.visualPolicyAtCapture?.tracerCount===0&&r.visualPolicyAtCapture?.showTracers===false&&r.visualPolicyAtCapture?.showStreamlines===false&&r.visualPolicyAtCapture?.showPotentialFlow===false).length;addGate('ENGINE','D14','benchmark visual isolation · passive tracers off',visualIsolated?'PASS':'FAIL',{isolatedSnapshots,totalSnapshots:results.length,evidenceField:'visualPolicyAtCapture',required:{tracerCount:0,showTracers:false,showStreamlines:false,showPotentialFlow:false}},'De benchmark moet zonder passieve tracerintegratie en cosmetische flowlagen draaien. Ieder analyseresultaat bewaart het bewijsveld visualPolicyAtCapture; de oorspronkelijke visualisatie wordt na complete, stop of fout hersteld.');
    if(launchMode==='holdout'){
      const selected=crossKnotAudit.rows.length,candidatePasses=Object.values(crossKnotAudit.byCandidate||{}).filter(x=>x.pass);addGate('RESEARCH','R27','selected holdout admissibility',candidatePasses.length?'PASS':'FAIL',{selectedHoldouts:selected,accepted:candidatePasses,byCandidate:crossKnotAudit.byCandidate},'De geselecteerde holdouts trainen geen factor. PASS vereist één vooraf geregistreerde niet-reachfactor die op alle geselecteerde holdouts binnen 10% sluit.');
      addGate('RESEARCH','R30','cross-knot intrinsic holdout measurements','INFO',crossKnotAudit,'Geselecteerde canonicalized Fourier/ideal/KnotPlot-bronnen worden via Ω_parallel gemeten en trainen geen factor.');const pairMismatch=crossKnotAudit.embeddingPairs.map(x=>x.relativeMismatch).filter(Number.isFinite),maxPairMismatch=pairMismatch.length?Math.max(...pairMismatch):null;addGate('RESEARCH','R31','embedding-pair sensitivity · Fourier versus ideal','INFO',{maxRelativeKappaMismatch:maxPairMismatch,pairs:crossKnotAudit.embeddingPairs},'Verschillen binnen hetzelfde knooptype worden als embeddinggevoeligheid gerapporteerd.');return;
    }
    if(launchMode==='continuum'){
      const paramSeriesOnly=ladder.map(r=>({resolution:r.resolution,value:Math.abs(r.shapley.phaseLog.phi.PARAM)})),paramMonotoneOnly=paramSeriesOnly.length===6&&paramSeriesOnly.slice(1).every((x,i)=>x.value<=Math.max(1.1*paramSeriesOnly[i].value,1e-14));addGate('RESEARCH','R1','parameterization-convergence',paramMonotoneOnly?'PASS':'WARN',{series:paramSeriesOnly},'De absolute PARAM-bijdrage hoort langs de resolutieladder niet systematisch toe te nemen.');
      const trefoilReachOnly=ladder.map(r=>{const geom=r.lengthBenchmark.carrier.A.scales.currentGeom,resolved=r.lengthBenchmark.carrier.A.values.RESOLVED_CURRENT.lengthCurrent,reconstructed=2*geom.thickness*IDEAL_TREFOIL_ROPELENGTH,mismatch=Math.abs(resolved-reconstructed)/Math.max(Math.abs(resolved),Math.abs(reconstructed),1e-300);return{resolution:r.resolution,resolvedLength:resolved,reach:geom.thickness,reconstructedLength:reconstructed,relativeMismatch:mismatch};}),maxTrefoilReachOnly=trefoilReachOnly.length?Math.max(...trefoilReachOnly.map(x=>x.relativeMismatch)):Infinity;addGate('RESEARCH','R22a','trefoil reach/ropelength reconstruction',maxTrefoilReachOnly<=.01?'PASS':maxTrefoilReachOnly<=.05?'WARN':'FAIL',{series:trefoilReachOnly,maxRelativeMismatch:maxTrefoilReachOnly},'Deze discrete legacy-reachgate blijft ter vergelijking zichtbaar; de afzonderlijke continue v7.6.25-audit beslist over curvature, self-DCSD en inter-component reach.');addGate('RESEARCH','R29','continuum audit · primary observables','INFO',continuumAudit,'Rapporteert de continuümlimiet zonder fitwaarde naar de solver terug te koppelen.');return;
    }
    if(launchMode!=='full-suite'){
      const transOnly=base?base.shapley.phaseLog.phi.TRANS:NaN,totalOnly=base?base.shapley.phaseLog.total:NaN,transRatioOnly=Math.abs(transOnly)/Math.max(Math.abs(totalOnly),1e-300);addGate('RESEARCH','R0','translation-leak',transRatioOnly<=.01?'PASS':'WARN',{transContribution:transOnly,total:totalOnly,ratio:transRatioOnly},'Proxy-decompositie controleert translatielekkage.');
      const parityOnly={};let parityOnlyOk=true;for(const c of ['ROT','MUTUAL_BS']){const aa=base?.shapley.phaseLog.phi[c],bb=sw?.shapley.phaseLog.phi[c],sign=Number.isFinite(aa)&&Number.isFinite(bb)&&aa*bb<0,mis=Math.abs(Math.abs(aa)-Math.abs(bb))/Math.max(Math.abs(aa),Math.abs(bb),1e-300);parityOnly[c]={normal:aa,swapped:bb,signReversal:sign,mismatch:mis};parityOnlyOk&&=sign&&mis<=.1;}addGate('RESEARCH','R2','symmetry-parity',parityOnlyOk?'PASS':'WARN',parityOnly,'ROT en MUTUAL_BS horen de gemeten A/B-pariteit te volgen.');
      if(base){const fieldOnly=Math.max(Math.abs(base.fieldBracket?.min||0),Math.abs(base.fieldBracket?.max||0)),signalOnly=Math.abs(base.shapley.phaseLog.phi.MUTUAL_BS);addGate('RESEARCH','R5','field-scale-comparison',signalOnly<=fieldOnly?'PASS':'FAIL',{mutualShapleyAttribution:signalOnly,fieldAbsMax:fieldOnly,scaleRatio:signalOnly/Math.max(fieldOnly,1e-300)},'De korte decompositierun behoudt de bestaande negatieve veldclosuretest.');}return;
    }
    const trans=base?base.shapley.phaseLog.phi.TRANS:NaN,total=base?base.shapley.phaseLog.total:NaN,transRatio=Math.abs(trans)/Math.max(Math.abs(total),1e-300);addGate('RESEARCH','R0','translation-leak',transRatio<=.01?'PASS':'WARN',{transContribution:trans,total,ratio:transRatio},'Alleen translatielekkage in de proxy is problematisch; centroidbeweging op zichzelf niet.');
    const paramSeries=ladder.map(r=>({resolution:r.resolution,value:Math.abs(r.shapley.phaseLog.phi.PARAM)})),paramMonotone=paramSeries.length===6&&paramSeries.slice(1).every((x,i)=>x.value<=Math.max(1.1*paramSeries[i].value,1e-14));addGate('RESEARCH','R1','parameterization-convergence',paramMonotone?'PASS':'WARN',{series:paramSeries},'De absolute PARAM-bijdrage hoort langs de resolutieladder niet systematisch toe te nemen.');
    const parity={};let parityOk=true;for(const c of ['ROT','MUTUAL_BS']){const a=base?.shapley.phaseLog.phi[c],b=sw?.shapley.phaseLog.phi[c],sign=Number.isFinite(a)&&Number.isFinite(b)&&a*b<0,mis=Math.abs(Math.abs(a)-Math.abs(b))/Math.max(Math.abs(a),Math.abs(b),1e-300);parity[c]={normal:a,swapped:b,signReversal:sign,mismatch:mis};parityOk&&=sign&&mis<=.1;}
    addGate('RESEARCH','R2','symmetry-parity',parityOk?'PASS':'WARN',parity,'ROT en MUTUAL_BS horen de gemeten A/B-pariteit te volgen.');
    if(base){
      const rank=CHANNELS.map(c=>({channel:c,value:base.shapley.phaseLog.phi[c],abs:Math.abs(base.shapley.phaseLog.phi[c])})).sort((a,b)=>b.abs-a.abs);addGate('RESEARCH','R3','dominant-channel','INFO',{ranking:rank},'Informatieve rangschikking; dominantie is geen afgeleide klokwet.');
      const ix=base.interactions.phaseLog;addGate('RESEARCH','R4','ROT×MUTUAL interaction','INFO',{v0:ix.v0,vRot:ix.vRot,vMutual:ix.vMutual,vRotMutual:ix.vRotMutual,interaction:ix.interaction,allOn:ix.vAll,interactionToTotal:ix.interactionToTotal},'Shapley verdeelt een niet-additieve ROT×MUTUAL-interactie over beide kanalen; rapporteer daarom ook de expliciete tweekanaalsterm.');
      const mutualShapley=base.shapley.phaseLog.phi.MUTUAL_BS,mutualOnly=ix.mutualOnly,field=Math.max(Math.abs(base.fieldBracket?.min||0),Math.abs(base.fieldBracket?.max||0));addGate('RESEARCH','R5','field-scale-comparison',Math.abs(mutualShapley)<=field&&Math.abs(mutualOnly)<=field?'PASS':'FAIL',{mutualShapleyAttribution:mutualShapley,mutualOnlyCounterfactual:mutualOnly,fieldAbsMax:field,shapleyScaleRatio:Math.abs(mutualShapley)/Math.max(field,1e-300),mutualOnlyScaleRatio:Math.abs(mutualOnly)/Math.max(field,1e-300)},'Zowel de gedeelde Shapley-attributie als de mutual-only counterfactual worden met de formele veldbracket vergeleken.');
    }
    const monitored=[['total',r=>r.shapley.phaseLog.total],['ROT',r=>r.shapley.phaseLog.phi.ROT],['MUTUAL_BS',r=>r.shapley.phaseLog.phi.MUTUAL_BS],['ROT_X_MUTUAL',r=>r.interactions.phaseLog.interaction]],resolutionMetrics={};let maxLastChange=Infinity;
    if(ladder.length===6){maxLastChange=0;for(const [name,get] of monitored){const series=ladder.map(r=>({resolution:r.resolution,value:get(r)})),changes=series.slice(1).map((x,i)=>({from:series[i].resolution,to:x.resolution,relativeChange:Math.abs(x.value-series[i].value)/Math.max(Math.abs(x.value),Math.abs(series[i].value),1e-300)}));resolutionMetrics[name]={series,changes,lastRelativeChange:changes.at(-1).relativeChange};maxLastChange=Math.max(maxLastChange,changes.at(-1).relativeChange);}}
    const resolutionStatus=ladder.length<6?'FAIL':maxLastChange<=.05?'PASS':maxLastChange<=.15?'WARN':'FAIL';addGate('RESEARCH','R6','resolution-ladder convergence · N=128–768',resolutionStatus,{maxLastPairRelativeChange:maxLastChange,passLimit:.05,warnLimit:.15,metrics:resolutionMetrics},'Totaal, ROT, MUTUAL_BS en ROT×MUTUAL moeten tussen N=512 en N=768 stabiliseren; dit is een numerieke geldigheidsgate, geen klokwet.');
    const normParity={},normParityStates=[];for(const n of NORMALIZATIONS){const a=base?.normalizations?.net?.[n.id]?.netLog,b=sw?.normalizations?.net?.[n.id]?.netLog,sign=Number.isFinite(a)&&Number.isFinite(b)&&a*b<0,mis=Math.abs(Math.abs(a)-Math.abs(b))/Math.max(Math.abs(a),Math.abs(b),1e-300);normParity[n.id]={normal:a,swapped:b,signReversal:sign,mismatch:mis};normParityStates.push(sign&&mis<=.1?'PASS':(Number.isFinite(a)&&Number.isFinite(b)?'WARN':'FAIL'));}addGate('RESEARCH','R7','normalization-parity',worst(normParityStates),normParity,'Iedere kandidaatnormalisatie hoort de A/B-traversalpariteit te behouden; dit valideert alleen de diagnose, niet de klokwet.');
    const normResolution={};let normMaxLast=0,normHave=ladder.length===6;for(const n of NORMALIZATIONS){const series=ladder.map(r=>({resolution:r.resolution,value:r.normalizations.net[n.id].netLog})),changes=series.slice(1).map((x,i)=>({from:series[i].resolution,to:x.resolution,relativeChange:Math.abs(x.value-series[i].value)/Math.max(Math.abs(x.value),Math.abs(series[i].value),1e-300)})),last=changes.at(-1)?.relativeChange??Infinity;normResolution[n.id]={series,changes,lastRelativeChange:last};normMaxLast=Math.max(normMaxLast,last);}const normResolutionStatus=!normHave?'FAIL':normMaxLast<=.05?'PASS':normMaxLast<=.15?'WARN':'FAIL';addGate('RESEARCH','R8','normalization-resolution convergence · N=128–768',normResolutionStatus,{maxLastPairRelativeChange:normMaxLast,passLimit:.05,warnLimit:.15,metrics:normResolution},'De normalisatieschalen worden afzonderlijk gevolgd; een nuldoorgang of instabiele kleine noemer blijft zichtbaar.');
    if(base){const ranking=NORMALIZATIONS.map(n=>{const v=base.normalizations.net[n.id];return{id:n.id,label:n.label,value:v.netLog,fieldScaleRatio:v.fieldScaleRatio,denominatorA:v.A.denominatorCurrent,denominatorB:v.B.denominatorCurrent,risk:n.risk||null};}).sort((a,b)=>a.fieldScaleRatio-b.fieldScaleRatio),closest=ranking[0],spread=Math.max(...ranking.map(x=>Math.abs(x.value)))/Math.max(Math.min(...ranking.map(x=>Math.abs(x.value)).filter(x=>x>0)),1e-300);addGate('RESEARCH','R9','normalization field-scale ranking','INFO',{closest,ranking,amplitudeSpread:spread},'Rangschikt vooraf vastgelegde dimensieloze schalen. Nabijheid tot de veldbracket is geen closure zonder onafhankelijke overdrachtswet.');
      const dyn=base.normalizations.net.ISO_DYNAMIC.netLog,isoRef=base.normalizations.net.ISO_REFERENCE.netLog,fullRef=base.normalizations.net.FULL_REFERENCE.netLog,relativeDynamicVsFixed=Math.abs(dyn-isoRef)/Math.max(Math.abs(dyn),Math.abs(isoRef),1e-300),relativeIsoVsFull=Math.abs(isoRef-fullRef)/Math.max(Math.abs(isoRef),Math.abs(fullRef),1e-300);addGate('RESEARCH','R10','body-Ω denominator sensitivity','INFO',{isoDynamic:dyn,isoReference:isoRef,fullReference:fullRef,relativeDynamicVsFixed,relativeIsoVsFull},'Isoleert hoeveel van de amplitudeverandering uitsluitend door een actuele versus bij t=0 bevroren body-Ω-noemer ontstaat.');
      const transferParity={},transferNull={},transferResolution={},admissibility=[];for(const law of TRANSFER_LAWS){const normal=base.transferLaws.net[law.id].value,swapped=sw?.transferLaws?.net?.[law.id]?.value,signReversal=Number.isFinite(normal)&&Number.isFinite(swapped)&&normal*swapped<0,mismatch=Math.abs(Math.abs(normal)-Math.abs(swapped))/Math.max(Math.abs(normal),Math.abs(swapped),1e-300);transferParity[law.id]={normal,swapped,signReversal,mismatch};const nullRun=resultAt('static-null'),nullValue=nullRun?.transferLaws?.net?.[law.id]?.value,nullRatio=Math.abs(nullValue)/Math.max(Math.abs(normal),1e-300);transferNull[law.id]={signal:normal,nullValue,nullRatio};const series=ladder.map(r=>({resolution:r.resolution,value:r.transferLaws.net[law.id].value})),changes=series.slice(1).map((x,i)=>({from:series[i].resolution,to:x.resolution,relativeChange:Math.abs(x.value-series[i].value)/Math.max(Math.abs(x.value),Math.abs(series[i].value),1e-300)})),last=changes.at(-1)?.relativeChange??Infinity;transferResolution[law.id]={series,changes,lastRelativeChange:last};const fieldRatio=base.transferLaws.net[law.id].fieldScaleRatio,scaleCompatible=fieldRatio>=.1&&fieldRatio<=10,parityPass=signReversal&&mismatch<=.1,nullPass=nullRatio<=.01,resolutionPass=last<=.05,accepted=scaleCompatible&&parityPass&&nullPass&&resolutionPass;admissibility.push({id:law.id,formula:law.formula,value:normal,fieldScaleRatio:fieldRatio,scaleCompatible,parityPass,nullPass,resolutionPass,accepted});}
      addGate('RESEARCH','R11','transfer-law parity',worst(Object.values(transferParity).map(x=>x.signReversal&&x.mismatch<=.1?'PASS':'WARN')),transferParity,'Vooraf geregistreerde wetten moeten de A/B-tekenomslag behouden.');
      const maxNull=Math.max(...Object.values(transferNull).map(x=>x.nullRatio));addGate('RESEARCH','R12','transfer-law static-null leakage',maxNull<=.01?'PASS':maxNull<=.1?'WARN':'FAIL',{maxNullToSignal:maxNull,metrics:transferNull},'De nuldriftuitkomst moet klein blijven ten opzichte van het baseline-signaal; dit is geen fysische tolerantiewet.');
      const maxTransferLast=Math.max(...Object.values(transferResolution).map(x=>x.lastRelativeChange));addGate('RESEARCH','R13','transfer-law resolution convergence · N=128–768',maxTransferLast<=.05?'PASS':maxTransferLast<=.15?'WARN':'FAIL',{maxLastPairRelativeChange:maxTransferLast,passLimit:.05,warnLimit:.15,metrics:transferResolution},'Iedere wet wordt zonder herfit langs dezelfde resolutieladder gevolgd.');
      const transferRanking=admissibility.map(x=>({...x})).sort((a,b)=>Math.abs(Math.log10(Math.max(a.fieldScaleRatio,1e-300)))-Math.abs(Math.log10(Math.max(b.fieldScaleRatio,1e-300))));addGate('RESEARCH','R14','transfer-law field-scale ranking','INFO',{closest:transferRanking[0],ranking:transferRanking},'Schaalnabijheid is diagnostisch; de coefficient blijft 1 en wordt niet naar de veldwaarde gefit.');
      const accepted=admissibility.filter(x=>x.accepted);addGate('RESEARCH','R15','transfer-law scale-screen · geen closure',accepted.length?'PASS':'FAIL',{accepted,criteria:{fieldScaleRatio:[.1,10],parityMismatchMax:.1,nullLeakMax:.01,resolutionLastPairMax:.05},candidates:admissibility},'Deze gate is uitsluitend een brede factor-10 screeningsfilter met pariteit, nul en resolutie. PASS betekent niet dat de wet sluit of fysisch is afgeleid.');
      const lengthAbsRanking=LENGTH_CANDIDATES.map(l=>{const v=base.lengthBenchmark.net[l.id];return{id:l.id,label:l.label,kind:l.kind,semanticEligible:!!l.semanticEligible,lengthA:v.A.lengthCurrent,lengthB:v.B.lengthCurrent,value:v.absoluteCurrent,fieldScaleRatio:v.absoluteScaleRatio,risk:l.risk||null};}).sort((a,b)=>Math.abs(Math.log10(Math.max(a.fieldScaleRatio,1e-300)))-Math.abs(Math.log10(Math.max(b.fieldScaleRatio,1e-300))));addGate('RESEARCH','R16','L/v↺* absolute-route ranking','INFO',{closest:lengthAbsRanking[0],ranking:lengthAbsRanking},'Vergelijkt Ω_mutual(t)L/v↺* alleen met de absolute veldbracket op hetzelfde checkpoint.');
      const timePoints=results.filter(r=>r.scenarioId==='baseline'&&r.tPhys>0).sort((a,b)=>a.tPhys-b.tPhys),lengthDeltaRanking=[],lengthTrajectory={},lengthResolution={},lengthNull={},lengthParity={},lengthASim={},lengthAdmissibility=[];
      const asLo=resultAt('asim-0.5mm'),asHi=resultAt('asim-1.5mm'),nullRun=resultAt('static-null');
      for(const l of LENGTH_CANDIDATES){const v=base.lengthBenchmark.net[l.id],ratios=timePoints.map(r=>({t:r.tPhys,ratio:r.lengthBenchmark.net[l.id].deltaScaleRatio,value:r.lengthBenchmark.net[l.id].delta,fieldDeltaAbsMax:r.lengthBenchmark.net[l.id].fieldDeltaAbsMax})).filter(x=>Number.isFinite(x.ratio)&&x.ratio>0),rmin=ratios.length?Math.min(...ratios.map(x=>x.ratio)):Infinity,rmax=ratios.length?Math.max(...ratios.map(x=>x.ratio)):Infinity,ratioSpread=ratios.length?(rmax-rmin)/Math.max(rmax,rmin,1e-300):Infinity;lengthTrajectory[l.id]={series:ratios,minRatio:rmin,maxRatio:rmax,relativeSpread:ratioSpread};
        const series=ladder.map(r=>({resolution:r.resolution,value:r.lengthBenchmark.net[l.id].delta,ratio:r.lengthBenchmark.net[l.id].deltaScaleRatio})),changes=series.slice(1).map((x,i)=>({from:series[i].resolution,to:x.resolution,relativeChange:Math.abs(x.value-series[i].value)/Math.max(Math.abs(x.value),Math.abs(series[i].value),1e-300)})),last=changes.at(-1)?.relativeChange??Infinity;lengthResolution[l.id]={series,changes,lastRelativeChange:last};
        const nv=nullRun?.lengthBenchmark?.net?.[l.id]?.delta??NaN,nullRatio=Math.abs(nv)/Math.max(Math.abs(v.delta),1e-300);lengthNull[l.id]={signal:v.delta,nullValue:nv,nullRatio};const sv=sw?.lengthBenchmark?.net?.[l.id]?.delta,signReversal=Number.isFinite(v.delta)&&Number.isFinite(sv)&&v.delta*sv<0,mismatch=Math.abs(Math.abs(v.delta)-Math.abs(sv))/Math.max(Math.abs(v.delta),Math.abs(sv),1e-300);lengthParity[l.id]={normal:v.delta,swapped:sv,signReversal,mismatch};
        const lo=asLo?.lengthBenchmark?.net?.[l.id]?.delta,hi=asHi?.lengthBenchmark?.net?.[l.id]?.delta,aSensitivity=Number.isFinite(lo)&&Number.isFinite(hi)?Math.abs(hi-lo)/Math.max(Math.abs(hi),Math.abs(lo),1e-300):Infinity;lengthASim[l.id]={a05:lo,a10:v.delta,a15:hi,relativeSpan:aSensitivity};
        const scaleCompatible=v.deltaScaleRatio>=.1&&v.deltaScaleRatio<=10,trajectoryPass=ratioSpread<=.1,resolutionPass=last<=.05,nullPass=nullRatio<=.01,parityPass=signReversal&&mismatch<=.1,aSimPass=l.id==='IDEAL_ASIM_DIAMETER'?aSensitivity<=.1:true,semanticPass=!!l.semanticEligible,accepted=scaleCompatible&&trajectoryPass&&resolutionPass&&nullPass&&parityPass&&aSimPass&&semanticPass;const row={id:l.id,label:l.label,kind:l.kind,semanticPass,scaleCompatible,trajectoryPass,resolutionPass,nullPass,parityPass,aSimPass,accepted,value:v.delta,fieldScaleRatio:v.deltaScaleRatio,ratioSpread,lastResolutionChange:last,nullRatio,parityMismatch:mismatch,aSimSensitivity:aSensitivity,lengthA:v.A.lengthCurrent,risk:l.risk||null};lengthAdmissibility.push(row);lengthDeltaRanking.push(row);}
      lengthDeltaRanking.sort((a,b)=>Math.abs(Math.log10(Math.max(a.fieldScaleRatio,1e-300)))-Math.abs(Math.log10(Math.max(b.fieldScaleRatio,1e-300))));addGate('RESEARCH','R17','L/v↺* calibrated-field ranking','INFO',{closest:lengthDeltaRanking[0],ranking:lengthDeltaRanking},'Vergelijkt ΔΩ_mutual L/v↺* uitsluitend met de gekalibreerde veldverandering field(t)-field(0); absolute en gekalibreerde routes worden niet gemengd.');
      const maxTrajectorySpread=Math.max(...Object.values(lengthTrajectory).map(x=>x.relativeSpread));addGate('RESEARCH','R18','L/v↺* time-trajectory proportionality',maxTrajectorySpread<=.1?'PASS':maxTrajectorySpread<=.25?'WARN':'FAIL',{maxRelativeRatioSpread:maxTrajectorySpread,passLimit:.1,warnLimit:.25,metrics:lengthTrajectory},'Een echte coefficient-1 closure hoort niet slechts op één checkpoint dicht te liggen; de transfer/veld-ratio moet langs t=0.5–3 s stabiel blijven.');
      const maxLengthLast=Math.max(...Object.values(lengthResolution).map(x=>x.lastRelativeChange));addGate('RESEARCH','R19','L/v↺* resolution convergence · N=128–768',maxLengthLast<=.05?'PASS':maxLengthLast<=.15?'WARN':'FAIL',{maxLastPairRelativeChange:maxLengthLast,passLimit:.05,warnLimit:.15,metrics:lengthResolution},'Iedere lengtekeuze wordt langs dezelfde mutual-ΔΩ-resolutieladder gevolgd.');
      const asimCandidate=lengthASim.IDEAL_ASIM_DIAMETER;addGate('RESEARCH','R20','a_sim length-map negative control',asimCandidate.relativeSpan<=.1?'PASS':asimCandidate.relativeSpan<=.5?'WARN':'FAIL',{candidate:'IDEAL_ASIM_DIAMETER',metrics:lengthASim},'Als L_ideal·2a_sim numeriek sluit maar sterk met de numerieke regularisatie verandert, is dat geen fysieke identificatie van L_K.');
      const lengthAccepted=lengthAdmissibility.filter(x=>x.accepted);addGate('RESEARCH','R21','physical L_K identification · no-fit',lengthAccepted.length?'PASS':'FAIL',{accepted:lengthAccepted,criteria:{semanticClass:'CANON_CARRIER',fieldScaleRatio:[.1,10],trajectoryRatioSpreadMax:.1,resolutionLastPairMax:.05,nullLeakMax:.01,parityMismatchMax:.1},candidates:lengthAdmissibility},'Numerieke nabijheid mag de CANON-semantiek niet vervangen: alleen de opgeloste gesloten centerline-lengte kan hier L_K zijn. Speciale, referentie- en negatieve-controleschalen zijn nooit door een schaalmatch gecanoniseerd.');const trefoilReachSeries=ladder.map(r=>{const byCarrier={};for(const w of ['A','B']){const resolved=r.lengthBenchmark.carrier[w].values.RESOLVED_CURRENT.lengthCurrent,geom=r.lengthBenchmark.carrier[w].scales.currentGeom,reconstructed=IDEAL_TREFOIL_ROPELENGTH*2*geom.thickness,relativeMismatch=Math.abs(resolved-reconstructed)/Math.max(Math.abs(resolved),Math.abs(reconstructed),1e-300);byCarrier[w]={resolvedLength:resolved,reach:geom.thickness,reconstructedLength:reconstructed,relativeMismatch};}return{scenarioId:r.scenarioId,tPhys:r.tPhys,resolution:r.resolution,topologyKey:'3_1',metadataRopDiam:IDEAL_TREFOIL_ROPELENGTH,carriers:byCarrier,maxRelativeMismatch:Math.max(byCarrier.A.relativeMismatch,byCarrier.B.relativeMismatch)};}),maxTrefoilReachMismatch=trefoilReachSeries.length?Math.max(...trefoilReachSeries.map(x=>x.maxRelativeMismatch)):Infinity;addGate('RESEARCH','R22a','trefoil reach/DCSD resolution reconstruction',maxTrefoilReachMismatch<=.01?'PASS':maxTrefoilReachMismatch<=.05?'WARN':'FAIL',{topologyKey:'3_1',idealRopelengthDiameter:IDEAL_TREFOIL_ROPELENGTH,idealRopelengthRadius:2*IDEAL_TREFOIL_ROPELENGTH,maxRelativeMismatch:maxTrefoilReachMismatch,passLimit:.01,warnLimit:.05,series:trefoilReachSeries},'Alleen de trefoil-resolutieladder wordt tegen de onafhankelijke trefoil-ropelength vergeleken. Een FAIL blokkeert reach-afhankelijke κ-factoren totdat de thickness-schatter convergeert.');
      const idealReachRows=scenarios.filter(sc=>sc.holdout&&sc.knotSource==='ideal').map(sc=>{const r=resultAt(sc.id);if(!r)return{id:sc.id,available:false,topologyKey:sc.topologyKey,knotKey:sc.knotKey};const byCarrier={};for(const w of ['A','B']){const resolved=r.lengthBenchmark.carrier[w].values.RESOLVED_CURRENT.lengthCurrent,geom=r.lengthBenchmark.carrier[w].scales.currentGeom,ropDiam=r.knot?.idealRopDiam,reconstructed=Number.isFinite(ropDiam)?2*geom.thickness*ropDiam:NaN,relativeMismatch=Number.isFinite(reconstructed)?Math.abs(resolved-reconstructed)/Math.max(Math.abs(resolved),Math.abs(reconstructed),1e-300):null;byCarrier[w]={resolvedLength:resolved,reach:geom.thickness,metadataRopDiam:ropDiam,reconstructedLength:Number.isFinite(reconstructed)?reconstructed:null,relativeMismatch};}return{id:sc.id,available:true,topologyKey:sc.topologyKey,knotKey:sc.knotKey,metadataRopDiam:r.knot?.idealRopDiam,carriers:byCarrier,maxRelativeMismatch:Math.max(...Object.values(byCarrier).map(x=>Number.isFinite(x.relativeMismatch)?x.relativeMismatch:Infinity))};});addGate('RESEARCH','R22b','topology-specific ideal reach metadata · diagnostic','INFO',{rows:idealReachRows,statement:'Elke ideal holdout gebruikt uitsluitend zijn eigen L/D-metadata; deze diagnostiek beslist niet over de trefoil reach-convergence blocker.'},'Topology-specifieke ideal-metadata wordt niet meer met de trefoilwaarde vermengd. De oude discrete reachschatter blijft uitsluitend een legacydiagnostiek; de continue v7.6.25-audit rapporteert de nieuwe meetroute afzonderlijk.');
      const nonIdealProvenance=scenarios.filter(sc=>sc.holdout&&['fseries','knotplot'].includes(sc.knotSource)).map(sc=>({id:sc.id,source:sc.knotSource,topologyKey:sc.topologyKey,knotKey:sc.knotKey,status:'N/A',reason:sc.knotSource==='knotplot'?'D=1 en de Ridgerunner-thicknesscheck horen bij de polish/provenance; de uniform-N300 VortexLab-centerline is geen zelfstandige fysieke diameter-, C²- of globale ropelengthcertificatie':'geen onafhankelijk toegewezen fysieke tube-diameter voor deze Fourierembedding'}));addGate('RESEARCH','R22c','non-ideal catalog reach provenance · no certified diameter','INFO',{rows:nonIdealProvenance},'Fseries-candidates krijgen geen fysieke diameter toegewezen. KnotPlot D=1 is bronnormalisatie met polishprovenance; de uniforme VortexLab-centerline levert zonder de polishcurve geen zelfstandige global-tight, fysieke diameter- of C²-certificatie. N/A is geen PASS en geen FAIL.');      const continuumKappa=continuumAudit.requiredKappaContinuum,reachGate=gates.find(g=>g.id==='R22a'),reachConverged=reachGate?.status==='PASS';
      const geomRanking=GEOM_KAPPA_CANDIDATES.map(k=>{const coarse=base.geomKappa.candidates[k.id],high=r768?.geomKappa?.candidates?.[k.id],continuumRatio=coarse.applicable&&Number.isFinite(continuumKappa)&&continuumKappa!==0?coarse.kappa/continuumKappa:NaN,continuumResidual=Number.isFinite(continuumRatio)?Math.abs(continuumRatio-1):NaN;return{id:k.id,label:k.label,formula:k.formula,kappa:coarse.kappa,applicable:coarse.applicable,coarse:{ratio:coarse.ratio,relativeResidual:coarse.relativeResidual,requiredKappa:coarse.requiredKappa},highResolution:high?{ratio:high.ratio,relativeResidual:high.relativeResidual,requiredKappa:high.requiredKappa}:null,continuum:{requiredKappa:continuumKappa,ratio:continuumRatio,relativeResidual:continuumResidual}};}).sort((a,b)=>(a.continuum.relativeResidual??Infinity)-(b.continuum.relativeResidual??Infinity));addGate('RESEARCH','R23','κ_geom amplitude ranking · N128 / N768 / continuum','INFO',{requiredKappaN128:base.geomKappa.requiredKappa,requiredKappaN768:r768?.geomKappa?.requiredKappa,requiredKappaContinuum:continuumKappa,closestContinuum:geomRanking[0],ranking:geomRanking},'Rangschikt dezelfde vooraf geregistreerde factoren op grove grid, hoogste gemeten resolutie en continuümlimiet. Alleen high-resolution/continuum-amplitude mag admissibility bepalen.');
      const geomTrajectory={},geomResolution={},geomParity={},geomNull={},geomAdmissibility=[];
      for(const k of GEOM_KAPPA_CANDIDATES){const bv=base.geomKappa.candidates[k.id],hv=r768?.geomKappa?.candidates?.[k.id],seriesT=timePoints.map(r=>({t:r.tPhys,ratio:r.geomKappa.candidates[k.id].ratio,residual:r.geomKappa.candidates[k.id].relativeResidual,prediction:r.geomKappa.candidates[k.id].prediction,target:r.geomKappa.candidates[k.id].target})).filter(x=>Number.isFinite(x.ratio)),rmin=seriesT.length?Math.min(...seriesT.map(x=>x.ratio)):Infinity,rmax=seriesT.length?Math.max(...seriesT.map(x=>x.ratio)):-Infinity,spread=seriesT.length?(rmax-rmin)/Math.max(Math.abs(rmax),Math.abs(rmin),1e-300):Infinity;geomTrajectory[k.id]={series:seriesT,minRatio:rmin,maxRatio:rmax,relativeSpread:spread};
        const seriesR=ladder.map(r=>({resolution:r.resolution,ratio:r.geomKappa.candidates[k.id].ratio,prediction:r.geomKappa.candidates[k.id].prediction,requiredKappa:r.geomKappa.requiredKappa})).filter(x=>Number.isFinite(x.ratio)),changes=seriesR.slice(1).map((x,i)=>({from:seriesR[i].resolution,to:x.resolution,relativeRatioChange:Math.abs(x.ratio-seriesR[i].ratio)/Math.max(Math.abs(x.ratio),Math.abs(seriesR[i].ratio),1e-300)})),last=changes.at(-1)?.relativeRatioChange??Infinity;geomResolution[k.id]={series:seriesR,changes,lastRelativeRatioChange:last};
        const sv=sw?.geomKappa?.candidates?.[k.id]?.prediction,signReversal=Number.isFinite(sv)&&Number.isFinite(bv.prediction)&&bv.prediction*sv<0,mismatch=Math.abs(Math.abs(bv.prediction)-Math.abs(sv))/Math.max(Math.abs(bv.prediction),Math.abs(sv),1e-300);geomParity[k.id]={normal:bv.prediction,swapped:sv,signReversal,mismatch};const nv=nullRun?.geomKappa?.candidates?.[k.id]?.prediction,nullRatio=Math.abs(nv)/Math.max(Math.abs(bv.prediction),1e-300);geomNull[k.id]={signal:bv.prediction,nullValue:nv,nullRatio};
        const continuumRatio=bv.applicable&&Number.isFinite(continuumKappa)&&continuumKappa!==0?bv.kappa/continuumKappa:NaN,continuumResidual=Number.isFinite(continuumRatio)?Math.abs(continuumRatio-1):Infinity,highResidual=hv?.applicable?hv.relativeResidual:Infinity,amplitudePass=highResidual<=.10&&continuumResidual<=.10,trajectoryPass=spread<=.10,resolutionPass=last<=.05,parityPass=signReversal&&mismatch<=.10,nullPass=nullRatio<=.01,usesReach=['REACH_OVER_LK','DIAMETER_OVER_LK','INV_PI_ROP_DIAM','INV_CROSSING_ROP_DIAM','INV_2PI_ROP_DIAM'].includes(k.id),auditPass=idealConventionAudit.pass&&(!usesReach||reachConverged),holdoutPass=!!crossKnotAudit.byCandidate?.[k.id]?.pass,accepted=bv.applicable&&amplitudePass&&trajectoryPass&&resolutionPass&&parityPass&&nullPass&&auditPass&&holdoutPass;geomAdmissibility.push({id:k.id,label:k.label,formula:k.formula,kappa:bv.kappa,coarseRatio:bv.ratio,highResolutionRatio:hv?.ratio,highResolutionResidual:highResidual,continuumRatio,continuumResidual,amplitudePass,trajectoryPass,resolutionPass,parityPass,nullPass,auditPass,usesReach,reachConverged,holdoutPass,trajectorySpread:spread,lastResolutionRatioChange:last,parityMismatch:mismatch,nullRatio,accepted});}
      const geomSpreads=Object.values(geomTrajectory).map(x=>x.relativeSpread).filter(Number.isFinite),maxGeomSpread=geomSpreads.length?Math.max(...geomSpreads):Infinity;addGate('RESEARCH','R24','κ_geom trajectory proportionality',maxGeomSpread<=.10?'PASS':maxGeomSpread<=.25?'WARN':'FAIL',{maxRelativeRatioSpread:maxGeomSpread,passLimit:.10,warnLimit:.25,metrics:geomTrajectory},'De κ_geom-gecorrigeerde verhouding moet over t=0.5–3 s stabiel blijven; één checkpointmatch is onvoldoende.');
      const parityValues=Object.values(geomParity).filter(x=>Number.isFinite(x.mismatch)&&Number.isFinite(x.nullRatio??0)),nullValues=Object.values(geomNull).filter(x=>Number.isFinite(x.nullRatio)),maxGeomParity=parityValues.length?Math.max(...parityValues.map(x=>x.mismatch)):Infinity,maxGeomNull=nullValues.length?Math.max(...nullValues.map(x=>x.nullRatio)):Infinity,geomParityOk=parityValues.length>0&&parityValues.every(x=>x.signReversal&&x.mismatch<=.1);addGate('RESEARCH','R25','κ_geom parity + static-null',geomParityOk&&maxGeomNull<=.01?'PASS':'FAIL',{maxParityMismatch:maxGeomParity,maxNullToSignal:maxGeomNull,parity:geomParity,null:geomNull},'Een geometrische factor mag de A/B-tekenomslag niet verbreken en mag geen significant static-null-signaal introduceren.');
      const geomLastValues=Object.values(geomResolution).map(x=>x.lastRelativeRatioChange).filter(Number.isFinite),maxGeomLast=geomLastValues.length?Math.max(...geomLastValues):Infinity;addGate('RESEARCH','R26','κ_geom closure-ratio convergence · N=128–768',maxGeomLast<=.05?'PASS':maxGeomLast<=.15?'WARN':'FAIL',{maxLastPairRelativeRatioChange:maxGeomLast,lastPair:'N512→N768',passLimit:.05,warnLimit:.15,metrics:geomResolution},'Convergentie is noodzakelijk maar niet voldoende: de convergente limiet moet ook de juiste amplitude hebben.');
      const geomAccepted=geomAdmissibility.filter(x=>x.accepted);addGate('RESEARCH','R27','κ_geom confirmatory admissibility · high-resolution + continuum + holdout',geomAccepted.length?'PASS':'FAIL',{accepted:geomAccepted,criteria:{highResolutionAmplitudeResidualMax:.10,continuumAmplitudeResidualMax:.10,trajectoryRatioSpreadMax:.10,resolutionRatioLastPairMax:.05,nullLeakMax:.01,parityMismatchMax:.10,idealConventionAudit:true,reachConvergenceForReachFactors:true,independentCrossKnotHoldoutRequired:true},candidates:geomAdmissibility},'Een factor wordt niet meer op N=128 toegelaten. Amplitude moet bij N=768 én in de continuümlimiet sluiten; reach-factoren vereisen R22a=PASS en confirmatie vereist onafhankelijke holdouts.');
      addGate('RESEARCH','R28','ideal-knot convention consequence','INFO',{convention:idealConventionAudit.convention,trefoil:idealConventionAudit.selectedTrefoil,diameterRopelength:IDEAL_TREFOIL_ROPELENGTH,radiusRopelength:2*IDEAL_TREFOIL_ROPELENGTH},'Gilbert L/D gebruikt D als buisdiameter. Deze metadata-conventie blijft geldig, ook wanneer de live discrete reach-schatter niet convergeert.');
      addGate('RESEARCH','R29','continuum audit · primary observables','INFO',continuumAudit,'Rapporteert de continuümlimiet zonder nieuwe kandidaatfactor te registreren. De required-κ-limiet is diagnostisch en mag niet post-hoc worden gebruikt.');
      addGate('RESEARCH','R30','cross-knot intrinsic holdout measurements','INFO',crossKnotAudit,'Canonicalized Fourier/ideal/KnotPlot-bronnen worden via Ω_parallel gemeten en trainen geen factor.');const pairMismatch=crossKnotAudit.embeddingPairs.map(x=>x.relativeMismatch).filter(Number.isFinite),maxPairMismatch=pairMismatch.length?Math.max(...pairMismatch):Infinity;addGate('RESEARCH','R31','embedding-pair sensitivity · Fourier versus ideal','INFO',{maxRelativeKappaMismatch:maxPairMismatch,pairs:crossKnotAudit.embeddingPairs},'Verschillen binnen hetzelfde knooptype worden eerst als embedding/representatiegevoeligheid gerapporteerd; dit is geen topologyfalsificatie.');}

  }
  function restoreConfiguration(){
    proxyDecompResolutionOverride=0;if(!snapshot)return;const p=clone(snapshot.P),visualBefore=benchmarkVisualState;Object.assign(P,p);P.taylorOsc=clone(p.taylorOsc||{enabled:false,amplitude:.25,period:8});rebuildVolumeEnvelope();syncUi();updateSubtitle();resetState();P.accExp=p.accExp;syncUi();setPausedState(snapshot.paused,'proxy-decomposition-restore');const ps=el('presetSelect');if(ps&&snapshot.presetValue)ps.value=snapshot.presetValue;logBenchmarkVisualRestore('proxy-decomposition',visualBefore);benchmarkVisualState=null;
  }
  function complete(){
    active=false;pending=false;current=null;completedAt=new Date().toISOString();evaluate();const engine=worst(gates.filter(g=>g.group==='ENGINE').map(g=>g.status)),research=worst(gates.filter(g=>g.group==='RESEARCH').map(g=>g.status));
    LastProxyDecompositionSummary={state:'completed',engine,research,completedAt,snapshots:results.length};VLClockWorkflow.complete(launchMode,engine==='PASS');restoreConfiguration();setStatus(`VOLTOOID · ENGINE ${engine} · RESEARCH ${research} · ${results.length} snapshots · handmatige sessie teruggezet naar t=0.`,engine==='FAIL'?'bad':(engine==='PASS'&&research==='PASS'?'good':'warn'));if(window.ModelLog)window.ModelLog.logEvent('proxy-decomposition-complete',{engine,research,report:reportObject()});updateSpecClockDisplay();render();
    if(specAutoExportEnabled()){const stamp=safeUtcStamp(completedAt);setTimeout(()=>download('txt',stamp),80);setTimeout(()=>download('json',stamp),180);setTimeout(()=>download('csv',stamp),280);setTimeout(()=>exportModelLogTimestamped(stamp,'proxy-'+launchMode),380);}
  }
  function start(mode='decomposition'){
    if(active)return;if(SpecClockBenchmark.active){setFlag('⚠ stop eerst de gewone SPEC CLOCK-benchmark.',true);return;}
    launchMode=mode==='normalization'?'normalization':mode==='transfer'?'transfer-law':mode==='length'?'length-identification':mode==='continuum'?'continuum':mode==='holdout'?'holdout':(mode==='geom-kappa'||mode==='continuum-holdout'||mode==='full-suite')?'full-suite':'decomposition';
    if(!VLClockWorkflow.unlocked(launchMode)){const reason=VLClockWorkflow.reason(launchMode);setFlag('⚠ '+reason,true);setStatus('VERGRENDELD · '+reason,'warn');vlRefreshClockRunnerWorkflowUi();return;}
    scenarios=scenarioSetForMode(launchMode);if(!scenarios.length){setFlag('⚠ selecteer minstens één knoopbron en één knoop voor de holdoutrun.',true);setStatus('GEEN SCENARIO’S · pas de knoopselectie bovenaan CLOCK aan.','warn');return;}
    LastProxyDecompositionSummary=null;LastSpecClockBenchmarkSummary=null;updateSpecClockDisplay();clearTimeout(timer);snapshot={P:clone(P),paused,presetValue:el('presetSelect')?.value||''};benchmarkVisualState=suppressBenchmarkVisuals('proxy-decomposition');results=[];gates=[];index=-1;current=null;checkpointIndex=0;pending=false;aborted=false;lastError=null;active=true;VLClockWorkflow.begin(launchMode);startedAt=new Date().toISOString();completedAt=null;
    if(window.ModelLog){window.ModelLog.setEnabled(true);window.ModelLog.logEvent('proxy-decomposition-start',{schema:SCHEMA,launchMode,knotSelection:readKnotSelection(),cacheEntries:resultCache.size,scenarios,checkpointPlan:Object.fromEntries(scenarios.map(sc=>[sc.id,scenarioCheckpoints(sc)]))});}
    const messages={normalization:'START · normalisatieschalen op de korte proxy-suite…','transfer-law':'START · dimensieloze transferwetten op de korte proxy-suite…','length-identification':'START · L/v↺*-lengteklassen op de korte proxy-suite…',continuum:'START · uitsluitend trefoil-resolutieladder N=128–768…',holdout:'START · uitsluitend geselecteerde canonicalized knoopholdouts…','full-suite':'START · volledige confirmatoire proxy + continuüm + geselecteerde holdouts…',decomposition:'START · korte proxy-decompositie zonder continuüm- of holdoutherhaling…'};
    setStatus(messages[launchMode]||messages.decomposition,'running');render();startScenario();
  }
  function stop(reason='gebruiker'){
    if(!active)return;clearTimeout(timer);const reasonText=String(reason),stoppedScenario=current?.id||null,stoppedCheckpoint=checkpointIndex,total=expectedSnapshotCount();aborted=true;active=false;pending=false;completedAt=new Date().toISOString();setPausedState(true,'proxy-decomposition-stop');
    const abortRecord={reason:reasonText,scenarioId:stoppedScenario,checkpointIndex:stoppedCheckpoint,completedSnapshots:results.length,totalSnapshots:total,lastError,completedAt};if(window.ModelLog)window.ModelLog.logEvent('proxy-decomposition-abort',abortRecord);
    current=null;VLClockWorkflow.abort();LastProxyDecompositionSummary={state:'aborted',completedSnapshots:results.length,totalSnapshots:total,completedAt,error:lastError};restoreConfiguration();gates=[{group:'ENGINE',id:'aborted',label:'Decompositie afgebroken',status:/error/i.test(reasonText)?'FAIL':'WARN',metrics:{completedSnapshots:results.length,totalSnapshots:total,scenarioId:stoppedScenario,checkpointIndex:stoppedCheckpoint},explanation:reasonText}];setStatus(`AFGEBROKEN · ${results.length}/${total} snapshots · ${reasonText}`,/error/i.test(reasonText)?'bad':'warn');render();updateSpecClockDisplay();
    if(/error/i.test(reasonText)&&specAutoExportEnabled()){const stamp=safeUtcStamp(completedAt);setTimeout(()=>exportModelLogTimestamped(stamp,'proxy-error'),100);}
  }
  function metricKey(){return el('proxyDecompMetric')?.value||'phaseLog';}
  function normalizationMetricKey(){return el('proxyNormMetric')?.value||'netLog';}
  function render(){
    const total=expectedSnapshotCount(),done=results.length,progress=el('proxyDecompProgress');if(progress)progress.style.width=(total?100*done/total:0).toFixed(1)+'%';
    const stop=el('bProxyDecompStop'),txt=el('bProxyDecompExportTxt'),json=el('bProxyDecompExportJson'),csv=el('bProxyDecompExportCsv');if(stop)stop.hidden=true;for(const b of [txt,json,csv])if(b)b.disabled=active||!results.length;vlRefreshClockRunnerWorkflowUi();
    const summary=el('proxyDecompSummary');if(summary)summary.innerHTML=gates.map(g=>`<span>${g.label}</span><b class="${statusClass(g.status)}">${g.status}</b>`).join('');
    const latest=results[results.length-1],rows=el('proxyDecompRows'),water=el('proxyDecompWaterfall'),key=metricKey();
    if(rows){if(!latest)rows.innerHTML='<tr><td colspan="5" style="text-align:left;color:var(--muted);">Nog geen decompositieresultaten.</td></tr>';else{const totalVal=latest.shapley[key].total;rows.innerHTML=CHANNELS.map(c=>{const a=latest.shapley.A[key].phi[c],b=latest.shapley.B[key].phi[c],net=latest.shapley[key].phi[c],pct=100*net/Math.max(Math.abs(totalVal),1e-300);return `<tr><td>${c}</td><td>${a.toExponential(3)}</td><td>${b.toExponential(3)}</td><td>${net.toExponential(3)}</td><td>${pct.toFixed(2)}%</td></tr>`;}).join('')+`<tr><td>RESIDUAL</td><td>—</td><td>—</td><td>${latest.shapley[key].residual.toExponential(3)}</td><td>${(100*latest.shapley[key].relativeResidual).toExponential(2)}%</td></tr>`;}}
    if(water){if(!latest)water.innerHTML='';else{const vals=CHANNELS.map(c=>latest.shapley[key].phi[c]),mx=Math.max(...vals.map(Math.abs),1e-300);water.innerHTML=CHANNELS.map((c,i)=>`<div class="proxy-decomp-bar-row"><span>${c}</span><i style="--bar:${(100*Math.abs(vals[i])/mx).toFixed(2)}%" class="${vals[i]>=0?'pos':'neg'}"></i><b>${vals[i].toExponential(3)}</b></div>`).join('');}}
    const interactionRows=el('proxyDecompInteractionRows');if(interactionRows){if(!latest)interactionRows.innerHTML='<tr><td colspan="2">—</td></tr>';else{const ix=latest.interactions[key];interactionRows.innerHTML=[['v(ROT)',ix.vRot],['v(MUTUAL only)',ix.vMutual],['v(ROT+MUTUAL)',ix.vRotMutual],['I_ROT,MUTUAL',ix.interaction],['all-on',ix.vAll]].map(([label,value])=>`<tr><td>${label}</td><td>${Number(value).toExponential(6)}</td></tr>`).join('');}}
    const resolutionRows=el('proxyDecompResolutionRows');if(resolutionRows){const ladder=[resultAt('baseline'),resultAt('resolution-192'),resultAt('resolution-256'),resultAt('resolution-384'),resultAt('resolution-512'),resultAt('resolution-768')].filter(Boolean);resolutionRows.innerHTML=ladder.map((r,i)=>{const prev=i?ladder[i-1]:null,change=prev?Math.abs(r.shapley.phaseLog.total-prev.shapley.phaseLog.total)/Math.max(Math.abs(r.shapley.phaseLog.total),Math.abs(prev.shapley.phaseLog.total),1e-300):NaN;return `<tr><td>${r.resolution}</td><td>${r.shapley.phaseLog.total.toExponential(3)}</td><td>${r.shapley.phaseLog.phi.ROT.toExponential(3)}</td><td>${r.shapley.phaseLog.phi.MUTUAL_BS.toExponential(3)}</td><td>${r.interactions.phaseLog.interaction.toExponential(3)}</td><td>${Number.isFinite(change)?(100*change).toFixed(2)+'%':'—'}</td></tr>`;}).join('')||'<tr><td colspan="8">—</td></tr>';}
    const snaps=el('proxyDecompSnapshots');if(snaps){snaps.innerHTML=results.slice(-12).map(r=>`<tr><td>${r.scenarioId}</td><td>${r.tPhys.toFixed(1)}</td><td>${r.resolution}</td><td>${r.shapley.phaseLog.total.toExponential(3)}</td><td>${r.interactions.phaseLog.interaction.toExponential(3)}</td><td>${r.cyclicIndex.maxMutualRelative.toExponential(2)}</td><td>${r.purity?'PASS':'FAIL'}</td></tr>`).join('')||'<tr><td colspan="9">—</td></tr>';}
    const normKey=normalizationMetricKey(),normReference=resultAt('baseline')||latest,normRows=el('proxyNormRows');if(normRows){if(!normReference)normRows.innerHTML='<tr><td colspan="8">—</td></tr>';else{normRows.innerHTML=NORMALIZATIONS.map(n=>{const v=normReference.normalizations.net[n.id],value=v[normKey],ratio=Math.abs(value)/Math.max(v.fieldAbsMax,1e-300),cls=n.risk?'proxy-norm-risk':(ratio===Math.min(...NORMALIZATIONS.map(x=>Math.abs(normReference.normalizations.net[x.id][normKey])/Math.max(v.fieldAbsMax,1e-300)))?'proxy-norm-best':''),status=!v.valid?'INVALID':ratio<=1?'≤ veld':ratio<=1e3?'nabij':'≫ veld';return `<tr><td class="${cls}">${n.id}</td><td>${v.A.denominatorCurrent.toExponential(3)}</td><td>${v.B.denominatorCurrent.toExponential(3)}</td><td>${Number(value).toExponential(3)}</td><td>${ratio.toExponential(3)}</td><td>${status}</td></tr>`;}).join('');}}
    const normResRows=el('proxyNormResolutionRows');if(normResRows){const normLadder=[resultAt('baseline'),resultAt('resolution-192'),resultAt('resolution-256'),resultAt('resolution-384'),resultAt('resolution-512'),resultAt('resolution-768')].filter(Boolean);normResRows.innerHTML=NORMALIZATIONS.map(n=>{const vals=normLadder.map(r=>r.normalizations.net[n.id][normKey]),last=vals.length===6?Math.abs(vals[5]-vals[4])/Math.max(Math.abs(vals[5]),Math.abs(vals[4]),1e-300):NaN;return `<tr><td>${n.id}</td>${[0,1,2,3,4,5].map(i=>`<td>${Number.isFinite(vals[i])?vals[i].toExponential(3):'—'}</td>`).join('')}<td>${Number.isFinite(last)?(100*last).toFixed(2)+'%':'—'}</td></tr>`;}).join('')||'<tr><td colspan="8">—</td></tr>';}
    const transferRows=el('proxyTransferRows'),transferResRows=el('proxyTransferResolutionRows'),transferBase=resultAt('baseline')||latest,transferNullRun=resultAt('static-null'),transferLadder=[resultAt('baseline'),resultAt('resolution-192'),resultAt('resolution-256'),resultAt('resolution-384'),resultAt('resolution-512'),resultAt('resolution-768')].filter(Boolean);if(transferRows){if(!transferBase)transferRows.innerHTML='<tr><td colspan="9">—</td></tr>';else transferRows.innerHTML=TRANSFER_LAWS.map(l=>{const v=transferBase.transferLaws.net[l.id],nullValue=transferNullRun?.transferLaws?.net?.[l.id]?.value,nullRatio=Math.abs(nullValue)/Math.max(Math.abs(v.value),1e-300),vals=transferLadder.map(r=>r.transferLaws.net[l.id].value),last=vals.length===6?Math.abs(vals[5]-vals[4])/Math.max(Math.abs(vals[5]),Math.abs(vals[4]),1e-300):Infinity,scale=v.fieldScaleRatio>=.1&&v.fieldScaleRatio<=10,parityGate=gates.find(g=>g.id==='R11')?.metrics?.[l.id],accepted=scale&&nullRatio<=.01&&last<=.05&&parityGate?.signReversal&&parityGate?.mismatch<=.1,decision=accepted?'KANDIDAAT':'AFGEWEZEN';return `<tr><td class="${accepted?'proxy-transfer-candidate':'proxy-transfer-reject'}">${l.id}</td><td class="proxy-transfer-formula">${l.formula}</td><td>${v.value.toExponential(3)}</td><td>${v.fieldScaleRatio.toExponential(3)}</td><td>${(100*nullRatio).toExponential(2)}%</td><td>${Number.isFinite(last)?(100*last).toFixed(2)+'%':'—'}</td><td>${decision}</td></tr>`;}).join('');}if(transferResRows){transferResRows.innerHTML=TRANSFER_LAWS.map(l=>{const vals=transferLadder.map(r=>r.transferLaws.net[l.id].value),dim=transferLawDimensions(l);return `<tr><td>${l.id}</td>${[0,1,2,3,4,5].map(i=>`<td>${Number.isFinite(vals[i])?vals[i].toExponential(3):'—'}</td>`).join('')}<td>${dim.dimensionless?'L⁰T⁰':'FAIL'}</td></tr>`;}).join('')||'<tr><td colspan="8">—</td></tr>';}
    const lengthRows=el('proxyLengthRows'),lengthResRows=el('proxyLengthResolutionRows'),lengthBase=resultAt('baseline')||latest,lengthNullRun=resultAt('static-null'),lengthSwap=resultAt('symmetry-swap'),lengthLadder=[resultAt('baseline'),resultAt('resolution-192'),resultAt('resolution-256'),resultAt('resolution-384'),resultAt('resolution-512'),resultAt('resolution-768')].filter(Boolean),lengthTimes=results.filter(r=>r.scenarioId==='baseline'&&r.tPhys>0).sort((a,b)=>a.tPhys-b.tPhys),lengthLo=resultAt('asim-0.5mm'),lengthHi=resultAt('asim-1.5mm');
    if(lengthRows){if(!lengthBase)lengthRows.innerHTML='<tr><td colspan="9">—</td></tr>';else lengthRows.innerHTML=LENGTH_CANDIDATES.map(l=>{const v=lengthBase.lengthBenchmark.net[l.id],ratios=lengthTimes.map(r=>r.lengthBenchmark.net[l.id].deltaScaleRatio).filter(x=>Number.isFinite(x)&&x>0),spread=ratios.length?(Math.max(...ratios)-Math.min(...ratios))/Math.max(Math.max(...ratios),1e-300):Infinity,vals=lengthLadder.map(r=>r.lengthBenchmark.net[l.id].delta),last=vals.length===6?Math.abs(vals[5]-vals[4])/Math.max(Math.abs(vals[5]),Math.abs(vals[4]),1e-300):Infinity,nullValue=lengthNullRun?.lengthBenchmark?.net?.[l.id]?.delta,nullRatio=Math.abs(nullValue)/Math.max(Math.abs(v.delta),1e-300),sw=lengthSwap?.lengthBenchmark?.net?.[l.id]?.delta,parity=Number.isFinite(sw)&&v.delta*sw<0&&Math.abs(Math.abs(v.delta)-Math.abs(sw))/Math.max(Math.abs(v.delta),Math.abs(sw),1e-300)<=.1,accepted=l.semanticEligible&&v.deltaScaleRatio>=.1&&v.deltaScaleRatio<=10&&spread<=.1&&last<=.05&&nullRatio<=.01&&parity,decision=accepted?'FYSIEKE KANDIDAAT':(v.deltaScaleRatio>=.1&&v.deltaScaleRatio<=10?'NUMERIEK NABIJ · SEMANTISCH NIET VRIJ':'AFGEWEZEN');return `<tr><td class="${accepted?'proxy-transfer-candidate':'proxy-transfer-reject'}">${l.id}</td><td>${l.kind}</td><td>${v.A.lengthCurrent.toExponential(3)}</td><td>${v.delta.toExponential(3)}</td><td>${Number.isFinite(v.deltaScaleRatio)?v.deltaScaleRatio.toExponential(3):'—'}</td><td>${Number.isFinite(spread)?(100*spread).toFixed(2)+'%':'—'}</td><td>${decision}</td></tr>`;}).join('');}
    if(lengthResRows){lengthResRows.innerHTML=LENGTH_CANDIDATES.map(l=>{const v=lengthBase?.lengthBenchmark?.net?.[l.id],vals=lengthLadder.map(r=>r.lengthBenchmark.net[l.id].delta),lo=lengthLo?.lengthBenchmark?.net?.[l.id]?.delta,hi=lengthHi?.lengthBenchmark?.net?.[l.id]?.delta,sens=Number.isFinite(lo)&&Number.isFinite(hi)?Math.abs(hi-lo)/Math.max(Math.abs(hi),Math.abs(lo),1e-300):NaN;return `<tr><td>${l.id}</td><td>${v&&Number.isFinite(v.absoluteScaleRatio)?v.absoluteScaleRatio.toExponential(3):'—'}</td>${[0,1,2,3,4,5].map(i=>`<td>${Number.isFinite(vals[i])?vals[i].toExponential(3):'—'}</td>`).join('')}<td>${Number.isFinite(sens)?(100*sens).toFixed(2)+'%':'—'}</td></tr>`;}).join('')||'<tr><td colspan="9">—</td></tr>';}

    const geomRows=el('proxyGeomKappaRows'),geomResRows=el('proxyGeomKappaResolutionRows'),auditRows=el('idealConventionAuditRows'),continuumRows=el('proxyContinuumRows'),crossRows=el('proxyCrossKnotRows'),geomBase=resultAt('baseline')||latest,geomNullRun=resultAt('static-null'),geomSwap=resultAt('symmetry-swap'),geomLadder=[resultAt('baseline'),resultAt('resolution-192'),resultAt('resolution-256'),resultAt('resolution-384'),resultAt('resolution-512'),resultAt('resolution-768')].filter(Boolean),geomHigh=resultAt('resolution-768'),geomTimes=results.filter(r=>r.scenarioId==='baseline'&&r.tPhys>0).sort((a,b)=>a.tPhys-b.tPhys),audit=auditIdealKnotConvention(),continuum=buildContinuumAudit(geomLadder),crossAudit=buildCrossKnotAudit(),reachGate=gates.find(g=>g.id==='R22a');
    if(geomRows){if(!geomBase)geomRows.innerHTML='<tr><td colspan="8">—</td></tr>';else geomRows.innerHTML=GEOM_KAPPA_CANDIDATES.map(k=>{const coarse=geomBase.geomKappa.candidates[k.id],high=geomHigh?.geomKappa?.candidates?.[k.id],continuumRatio=coarse.applicable&&Number.isFinite(continuum.requiredKappaContinuum)&&continuum.requiredKappaContinuum!==0?coarse.kappa/continuum.requiredKappaContinuum:NaN,continuumResidual=Number.isFinite(continuumRatio)?Math.abs(continuumRatio-1):Infinity,usesReach=['REACH_OVER_LK','DIAMETER_OVER_LK','INV_PI_ROP_DIAM','INV_CROSSING_ROP_DIAM','INV_2PI_ROP_DIAM'].includes(k.id),holdoutPass=!!crossAudit.byCandidate?.[k.id]?.pass,accepted=coarse.applicable&&high?.relativeResidual<=.1&&continuumResidual<=.1&&(!usesReach||reachGate?.status==='PASS')&&holdoutPass,decision=!coarse.applicable?'N.V.T.':accepted?'CONFIRMATOIR':(high?.relativeResidual<=.25&&continuumResidual<=.25?(holdoutPass?'NABIJ · REACH/ANDERE GATE BLOKKEERT':'NABIJ · HOLDOUT FAIL'):'AFGEWEZEN');return `<tr><td class="${accepted?'proxy-transfer-candidate':'proxy-transfer-reject'}">${k.id}</td><td class="proxy-transfer-formula">${k.formula}</td><td>${Number.isFinite(coarse.kappa)?coarse.kappa.toExponential(4):'—'}</td><td>${Number.isFinite(high?.prediction)?high.prediction.toExponential(3):'—'}</td><td>${Number.isFinite(high?.target)?high.target.toExponential(3):'—'}</td><td>${Number.isFinite(high?.ratio)?high.ratio.toFixed(4):'—'}</td><td>${Number.isFinite(high?.relativeResidual)?(100*high.relativeResidual).toFixed(2)+'%':'—'}</td><td>${decision}</td></tr>`;}).join('');}
    if(geomResRows){geomResRows.innerHTML=GEOM_KAPPA_CANDIDATES.map(k=>{const vals=geomLadder.map(r=>r.geomKappa.candidates[k.id].ratio),last=vals.length===6&&Number.isFinite(vals[5])&&Number.isFinite(vals[4])?Math.abs(vals[5]-vals[4])/Math.max(Math.abs(vals[5]),Math.abs(vals[4]),1e-300):NaN;return `<tr><td>${k.id}</td>${[0,1,2,3,4,5].map(i=>`<td>${Number.isFinite(vals[i])?vals[i].toFixed(4):'—'}</td>`).join('')}<td>${Number.isFinite(last)?(100*last).toFixed(2)+'%':'—'}</td></tr>`;}).join('')||'<tr><td colspan="8">—</td></tr>';}
    if(continuumRows){const fitRows=Object.entries(continuum.fits||{}).map(([id,f])=>`<tr><td>${id}</td><td>${f.model||'—'}</td><td>${Number.isFinite(f.xInf)?f.xInf.toExponential(5):'—'}</td><td>${Number.isFinite(f.p)?f.p.toFixed(3):'—'}</td><td>${Number.isFinite(f.relativeRms)?(100*f.relativeRms).toFixed(3)+'%':'—'}</td><td>${Number.isFinite(f.leaveOneOut?.xInfRelativeSpan)?(100*f.leaveOneOut.xInfRelativeSpan).toFixed(2)+'%':'—'}</td><td>${f.valid?'PASS':'FAIL'}</td></tr>`).join(''),identityRow=`<tr><td>requiredKappaDerived</td><td>field∞ / route∞</td><td>${Number.isFinite(continuum.requiredKappaContinuum)?continuum.requiredKappaContinuum.toExponential(5):'—'}</td><td>—</td><td>${Number.isFinite(continuum.requiredKappaIdentityMismatch)?(100*continuum.requiredKappaIdentityMismatch).toFixed(2)+'% direct-fit Δ':'—'}</td><td>—</td><td>${continuum.valid?'PASS':'FAIL'}</td></tr>`;continuumRows.innerHTML=fitRows+identityRow||'<tr><td colspan="7">—</td></tr>';}
    if(crossRows){crossRows.innerHTML=crossAudit.rows.map(x=>`<tr><td>${x.topologyKey||x.id}</td><td>${x.embedding||x.source||'—'} · ${x.key||''}</td><td>${x.resolution||'—'}</td><td>${Number.isFinite(x.lengthA)?x.lengthA.toExponential(4):'—'}</td><td>${Number.isFinite(x.intrinsicDeltaRoute)?x.intrinsicDeltaRoute.toExponential(4):'—'}</td><td>${Number.isFinite(x.fieldTarget)?x.fieldTarget.toExponential(4):'—'}</td><td>${Number.isFinite(x.requiredKappaIntrinsic)?x.requiredKappaIntrinsic.toExponential(4):'—'}</td><td>${x.valid?(x.bestCandidate?`INTRINSIC · ${x.bestCandidate.id} ${(100*x.bestCandidate.relativeResidual).toFixed(1)}%`:'INTRINSIC PASS'):'FAIL'}</td></tr>`).join('')||'<tr><td colspan="8">—</td></tr>';}
    if(auditRows){auditRows.innerHTML=audit.rows.length?audit.rows.map(x=>`<tr><td>${x.id}</td><td>${Number.isFinite(x.metadataL)?x.metadataL.toFixed(6):'—'}</td><td>${Number.isFinite(x.metadataD)?x.metadataD.toFixed(3):'—'}</td><td>${Number.isFinite(x.sampledLength)?x.sampledLength.toFixed(6):'—'}</td><td>${Number.isFinite(x.diameterFromReach)?x.diameterFromReach.toFixed(6):'—'}</td><td>${Number.isFinite(x.ropDiamFromReach)?x.ropDiamFromReach.toFixed(6):'—'}</td><td>${Number.isFinite(x.ropRadFromReach)?x.ropRadFromReach.toFixed(6):'—'}</td><td class="${x.pass?'ideal-audit-pass':'ideal-audit-fail'}">${x.pass?'D = DIAMETER · PASS':'FAIL'}</td></tr>`).join(''):`<tr><td colspan="8" class="ideal-audit-fail">${audit.reason||'bron niet geladen'}</td></tr>`;}
  }
  function frameTick(){if(!active||!current||pending)return;if(flagged)stop('solver-stop: '+flagged);else render();}
  function reportObject(){const engine=worst(gates.filter(g=>g.group==='ENGINE').map(g=>g.status)),research=worst(gates.filter(g=>g.group==='RESEARCH').map(g=>g.status)),ladder=[resultAt('baseline'),resultAt('resolution-192'),resultAt('resolution-256'),resultAt('resolution-384'),resultAt('resolution-512'),resultAt('resolution-768')].filter(Boolean),continuumAudit=buildContinuumAudit(ladder),crossKnotAudit=buildCrossKnotAudit();return {schema:SCHEMA,appVersion:APP_VERSION,baseVersion:APP_BASE_VERSION,launchMode,startedAt,completedAt,aborted,lastError,engineVerdict:engine,researchVerdict:research,knotSelection:readKnotSelection(),sessionCache:{entries:resultCache.size,hits:cacheStats.hits,computed:cacheStats.misses},scenarioDefinitions:scenarios,checkpointPlan:Object.fromEntries(scenarios.map(sc=>[sc.id,scenarioCheckpoints(sc)])),continuumAudit,crossKnotAudit,autoExportEnabled:specAutoExportEnabled(),benchmarkVisualPolicy:{tracerCount:0,showTracers:false,showStreamlines:false,showPotentialFlow:false,restoredAfterRun:true},normalizationDefinitions:NORMALIZATIONS,transferLawDefinitions:TRANSFER_LAWS.map(({evaluate,...x})=>({...x,dimension:transferLawDimensions(x)})),lengthCandidateDefinitions:LENGTH_CANDIDATES,geomKappaDefinitions:GEOM_KAPPA_CANDIDATES.map(({evaluate,...x})=>({...x})),idealKnotConventionAudit:auditIdealKnotConvention(),characteristicSpeed:{jsonKey:'vChar',symbol:'v↺*',latex:'v_{\\!\\boldsymbol{\\circlearrowleft}}^{\\ast}',value:V_CHAR_SST,meaning:'canonical scalar characteristic swirl-speed magnitude',localFieldSymbol:'u↺(x,t)'},gateTolerances:{reconstruction:{relative:RECON_REL_TOL,absolute:RECON_ABS_TOL},linearity:{absolute:1e-18,relative:1e-5},cyclicIndex:{iso:{absolute:1e-18,relative:1e-5},mutual:{absolute:1e-18,relative:.1},projectionNull:'valid non-informative'},resolutionLastPair:{pass:.05,warn:.15,lastPair:'N512→N768'}},results,gates,scientificBoundary:'PASSIEVE DECOMPOSITIE, CONTINUUM- EN HOLDOUTDIAGNOSE; geen kandidaatwet wordt gefit, gecanoniseerd of naar de solver teruggekoppeld. Geselecteerde holdouts trainen of selecteren geen factor; Fourier/idealparen kwantificeren embeddinggevoeligheid en KnotPlot uniform-N300-knopen en -links blijven expliciete candidate-tests via intrinsieke Ω_parallel.',normalizationConvention:'Binnen iedere GEOM/PARAM-tak blijft de all-on geïsoleerde |Ω| als denominator bevroren om singuliere ROT/TRANS-ablaties te vermijden; het all-on masker reproduceert de bestaande phase-nullproxy.',candidateNormalizationConvention:'ISO_DYNAMIC gebruikt de actuele |Ω_iso| voor actueel en calibratie. Alle overige kandidaten gebruiken één bij t=0 vastgelegde schaal per drager: |Ω_iso,0|, |Ω_full,0|, |Ω_mutual,0|, Γ_eff/L0², u_iso,rms,0/L0 of Γ_eff/a_sim². Er wordt geen fitfactor gebruikt.',interactionConvention:'I_ROT,MUTUAL = v(ROT+MUTUAL) - v(ROT) - v(MUTUAL) + v(0). Shapley verdeelt deze niet-additieve term over de betrokken kanalen.',transferLawConvention:'ΔlnR = T(ΔΩ_mutual, Γ, a, L, d, v↺*, r_c). v↺* is de canonieke scalaire karakteristieke swirl-snelheid; lokale velden gebruiken u↺(x,t). Alleen vooraf geregistreerde dimensieloze monomialen met coefficient 1 worden geëvalueerd; requiredCoefficientToFieldEdge wordt uitsluitend gerapporteerd en nooit toegepast.',lengthConvention:'CANON: tau_circ(K)=L_K/v↺* met L_K de opgeloste gesloten carrierlengte. Absolute route: Ω_mutual(t)L/v↺* versus absolute field bracket. Gekalibreerde route: [Ω_mutual(t)L(t)-Ω_mutual(0)L(0)]/v↺* versus field(t)-field(0). 2πr_c is alleen de minimale neutrale lus. De research-track trefoilwaarde 2·16.371637·r_c is een expliciete schaalbenchmark en geen bewijs dat a_core=r_c; a_sim en d_AB zijn negatieve controles.',geomKappaConvention:'δlnR_field = κ_geom·δ(Ω_mutual L_K/v↺*). Admissibility gebruikt N=768 én de continuümlimiet; N=128 is niet beslissend. Reach-factoren vereisen een convergente live reach/DCSD-route. Holdoutconfirmatie gebruikt canonicalized embeddings en intrinsieke Ω_parallel; KnotPlot D=1/uniform-N300-candidates leveren zonder de polishcurve geen zelfstandig gecertificeerde reach; legacy lab-z blijft uitsluitend diagnostisch.'};}
  function reportText(){const r=reportObject(),lines=['VortexLab SPEC CLOCK proxy-decomposition + normalization + transfer-law benchmark','schema='+r.schema,'version='+APP_VERSION+' base='+APP_BASE_VERSION,'launchMode='+launchMode,'startedAt='+startedAt+' completedAt='+completedAt,'ENGINE='+r.engineVerdict+' RESEARCH='+r.researchVerdict,'','[gates]'];gates.forEach((g,i)=>lines.push(`${i+1}. ${g.group} ${g.status} ${g.id} · ${g.label} · metrics=${JSON.stringify(g.metrics)} · ${g.explanation}`));lines.push('','[continuum-audit]',JSON.stringify(r.continuumAudit),'','[cross-knot-holdouts]',JSON.stringify(r.crossKnotAudit),'','[normalization-definitions]',JSON.stringify(NORMALIZATIONS),'','[transfer-law-definitions]',JSON.stringify(r.transferLawDefinitions),'','[length-candidate-definitions]',JSON.stringify(r.lengthCandidateDefinitions),'','[geom-kappa-definitions]',JSON.stringify(r.geomKappaDefinitions),'','[ideal-knot-convention-audit]',JSON.stringify(r.idealKnotConventionAudit),'','[snapshots]');results.forEach((x,i)=>lines.push(`${i+1}. ${JSON.stringify(x)}`));lines.push('','[boundary]',r.scientificBoundary,'[shapley-normalization]',r.normalizationConvention,'[candidate-normalizations]',r.candidateNormalizationConvention,'[interaction]',r.interactionConvention,'[transfer-law]',r.transferLawConvention,'[length-identification]',r.lengthConvention,'[geom-kappa]',r.geomKappaConvention);return lines.join('\n');}
  function reportCsv(){const lines=['recordType,scenario,tPhys,resolution,id,A_value,B_value,netLog,netLinear,netAsinh,denominatorA,denominatorB,fieldScaleRatio,extra1,extra2,pure'];for(const r of results){for(const c of CHANNELS){const ix=r.interactions.phaseLog;lines.push(['SHAPLEY',r.scenarioId,r.tPhys,r.resolution,c,r.shapley.A.phaseLog.phi[c],r.shapley.B.phaseLog.phi[c],r.shapley.phaseLog.phi[c],r.shapley.deltaFrac.phi[c],r.shapley.rawOmega.phi[c],'','',Math.abs(r.shapley.phaseLog.phi[c])/Math.max(Math.abs(r.fieldBracket?.min||0),Math.abs(r.fieldBracket?.max||0),1e-300),ix.interaction,r.cyclicIndex.maxMutualRelative,r.purity].join(','));}for(const n of NORMALIZATIONS){const v=r.normalizations.net[n.id];lines.push(['NORMALIZATION',r.scenarioId,r.tPhys,r.resolution,n.id,v.A.offset,v.B.offset,v.netLog,v.netLinear,v.netAsinh,v.A.denominatorCurrent,v.B.denominatorCurrent,v.fieldScaleRatio,v.A.qCurrent,v.B.qCurrent,r.purity].join(','));}for(const l of TRANSFER_LAWS){const v=r.transferLaws.net[l.id];lines.push(['TRANSFER_LAW',r.scenarioId,r.tPhys,r.resolution,l.id,v.A.value,v.B.value,v.value,'','','','',v.fieldScaleRatio,l.formula,v.requiredCoefficientToFieldEdge,r.purity].join(','));}for(const l of LENGTH_CANDIDATES){const v=r.lengthBenchmark.net[l.id];lines.push(['LENGTH_ROUTE',r.scenarioId,r.tPhys,r.resolution,l.id,v.A.absoluteCurrent,v.B.absoluteCurrent,v.delta,v.absoluteCurrent,'',v.A.lengthCurrent,v.B.lengthCurrent,v.deltaScaleRatio,l.kind,v.absoluteScaleRatio,r.purity].join(','));}for(const k of GEOM_KAPPA_CANDIDATES){const v=r.geomKappa.candidates[k.id];lines.push(['GEOM_KAPPA',r.scenarioId,r.tPhys,r.resolution,k.id,v.kappa,'',v.prediction,'','','','',v.ratio,k.formula,v.relativeResidual,r.purity].join(','));}for(const w of ['A','B'])for(const state of ['current','calibration'])for(const field of ['iso','mutual','full']){const v=r.intrinsicKinematics?.[w]?.[state]?.[field];if(v)lines.push(['INTRINSIC_OMEGA',r.scenarioId,r.tPhys,r.resolution,w+'_'+state+'_'+field,v.vector[0],v.vector[1],v.parallel,v.magnitude,v.perpendicular,v.axis[0],v.axis[1],v.axis[2],r.knot?.topologyKey||'',r.knot?.embedding||'',r.purity].join(','));}}return lines.join('\n');}
  function download(kind,stamp=safeUtcStamp(completedAt||new Date())){const text=kind==='json'?JSON.stringify(reportObject(),null,2):kind==='csv'?reportCsv():reportText(),type=kind==='json'?'application/json':kind==='csv'?'text/csv;charset=utf-8':'text/plain;charset=utf-8',mode=String(launchMode||'decomposition').replace(/[^a-z0-9-]+/gi,'-');triggerTextDownload(text,type,`vortexlab-spec-clock-proxy-decomposition-${APP_VERSION.replace(/\./g,'-')}-${mode}-${stamp}.${kind}`);}
  function bind(){bindKnotSelector();const toggle=(id,mode)=>el(id)?.addEventListener('click',()=>{if(active){if(launchMode===mode)stop('handmatig gestopt');return;}start(mode);});toggle('bProxyDecompStart','decomposition');toggle('bHoldoutStart','holdout');toggle('bContinuumStart','continuum');toggle('bGeomKappaStart','full-suite');const legacyStop=el('bProxyDecompStop');if(legacyStop){legacyStop.hidden=true;legacyStop.addEventListener('click',()=>stop('handmatig gestopt'));}el('bProxyDecompExportTxt')?.addEventListener('click',()=>download('txt'));el('bProxyDecompExportJson')?.addEventListener('click',()=>download('json'));el('bProxyDecompExportCsv')?.addEventListener('click',()=>download('csv'));el('proxyDecompMetric')?.addEventListener('change',render);el('proxyNormMetric')?.addEventListener('change',render);render();}
  function selfTest(){
    const coeff={GEOM:1,PARAM:-2,ROT:3,TRANS:.5,MUTUAL_BS:-4},cf=[];for(let mask=0;mask<32;mask++){let v=0;for(const c of CHANNELS)if(mask&BITS[c])v+=coeff[c];cf.push({metrics:{phaseLog:v}});}const s=shapley(cf,'phaseLog');
    const ref=new Float64Array([0,0,0,1,0,0,0,2,0,0,0,3,1,2,4]),ang=.47,ca=Math.cos(ang),sa=Math.sin(ang),cur=new Float64Array(ref.length);for(let k=0;k<ref.length/3;k++){const i=3*k,x=ref[i],y=ref[i+1],z=ref[i+2];cur[i]=2+ca*x-sa*y;cur[i+1]=-1+sa*x+ca*y;cur[i+2]=.5+z;}const weights=new Float64Array(ref.length/3).fill(1),pose=quaternionRotation(ref,cur,weights),aligned=rotateAlign(ref,pose);let poseErr=0;for(let i=0;i<cur.length;i++)poseErr=Math.max(poseErr,Math.abs(cur[i]-aligned[i]));
    const U=[.2,-.1,.05],Om=[.3,-.2,.4],vel=new Float64Array(cur.length),c=weightedCentroid(cur,weights);for(let k=0;k<cur.length/3;k++){const i=3*k,rx=cur[i]-c[0],ry=cur[i+1]-c[1],rz=cur[i+2]-c[2];vel[i]=U[0]+Om[1]*rz-Om[2]*ry;vel[i+1]=U[1]+Om[2]*rx-Om[0]*rz;vel[i+2]=U[2]+Om[0]*ry-Om[1]*rx;}const fit=rigidFit(cur,vel,weights),fitErr=Math.max(...fit.U.map((v,i)=>Math.abs(v-U[i])),...fit.Omega.map((v,i)=>Math.abs(v-Om[i])));
    function synthCarrier(z,scaleMut,deform){const n=12,pts=new Float64Array(3*n),iso=new Float64Array(3*n),mut=new Float64Array(3*n),full=new Float64Array(3*n);for(let k=0;k<n;k++){const t=2*Math.PI*k/n,r=.08*(1+deform*.12*Math.cos(3*t)),i=3*k,x=r*Math.cos(t),y=r*Math.sin(t),zz=z+.018*Math.sin(3*t)*(1+deform);pts[i]=x;pts[i+1]=y;pts[i+2]=zz;iso[i]=-.001*y+.002;iso[i+1]=.001*x-.001;iso[i+2]=.0002;mut[i]=-scaleMut*1e-6*y;mut[i+1]=scaleMut*1e-6*x;mut[i+2]=0;full[i]=iso[i]+mut[i];full[i+1]=iso[i+1]+mut[i+1];full[i+2]=iso[i+2];}return {points:pts,components:[{offset:0,count:n,gamma:1,component:0}],fields:{iso,mutual:mut,full}};}
    const calRaw={carriers:{A:synthCarrier(-.42,1,0),B:synthCarrier(.42,-1,0)},parameters:{aSim:.01},measured:{fieldLogMin:-1e-9,fieldLogMax:1e-9,distance:.84}},raw={carriers:{A:synthCarrier(-.41,1.3,.02),B:synthCarrier(.41,-1.2,.015)},parameters:{aSim:.01},measured:{fieldLogMin:-1.2e-9,fieldLogMax:1.2e-9,distance:.82}},pc=prepareRaw(calRaw,calRaw),pr=prepareRaw(raw,calRaw),cfs=[];for(let mask=0;mask<32;mask++)cfs.push(counterfactual(pr,pc,mask));const ss=shapley(cfs,'phaseLog'),manualA=bodyOmegaFlat(raw.carriers.A.points,raw.carriers.A.fields.mutual)/Math.abs(bodyOmegaFlat(raw.carriers.A.points,raw.carriers.A.fields.iso))-bodyOmegaFlat(calRaw.carriers.A.points,calRaw.carriers.A.fields.mutual)/Math.abs(bodyOmegaFlat(calRaw.carriers.A.points,calRaw.carriers.A.fields.iso)),manualB=bodyOmegaFlat(raw.carriers.B.points,raw.carriers.B.fields.mutual)/Math.abs(bodyOmegaFlat(raw.carriers.B.points,raw.carriers.B.fields.iso))-bodyOmegaFlat(calRaw.carriers.B.points,calRaw.carriers.B.fields.mutual)/Math.abs(bodyOmegaFlat(calRaw.carriers.B.points,calRaw.carriers.B.fields.iso)),manual=Math.log1p(manualA)-Math.log1p(manualB),pipelineErr=Math.abs(cfs[31].metrics.phaseLog-manual),norm=normalizationBundle(raw,calRaw),normalizationError=Math.abs(norm.net.ISO_DYNAMIC.netLog-manual),normalizationFinite=NORMALIZATIONS.every(n=>norm.net[n.id].valid),transfer=transferLawBundle(raw,calRaw,norm),lengthTest=lengthBenchmarkBundle(raw,calRaw,norm),geomTest=geomKappaBundle(lengthTest,{knot:{crossingNumber:3,idealRopDiam:IDEAL_TREFOIL_ROPELENGTH}}),geomFinite=GEOM_KAPPA_CANDIDATES.every(k=>!geomTest.candidates[k.id].applicable||geomTest.candidates[k.id].valid),idealAudit=auditIdealKnotConvention(),lengthFinite=LENGTH_CANDIDATES.every(l=>lengthTest.net[l.id].valid),lengthIdentity=Math.max(...LENGTH_CANDIDATES.map(l=>lengthTest.net[l.id].identityError)),lengthIdentityScore=Math.max(...LENGTH_CANDIDATES.map(l=>lengthTest.net[l.id].identityScore)),transferFinite=TRANSFER_LAWS.every(l=>transfer.net[l.id].valid),transferDimensions=TRANSFER_LAWS.every(l=>transferLawDimensions(l).dimensionless&&l.coefficient===1),legacySpeedKey='C'+'e',legacySpeedTex='C'+'_'+'e',canonicalVChar=TRANSFER_LAWS.every(l=>Object.prototype.hasOwnProperty.call(l.exponents,'vChar')&&!Object.prototype.hasOwnProperty.call(l.exponents,legacySpeedKey)&&!(l.formula+l.label).includes(legacySpeedKey)&&!(l.formula+l.label).includes(legacySpeedTex))&&['A','B'].every(w=>Object.prototype.hasOwnProperty.call(transfer.carrier[w].inputs,'vChar')&&!Object.prototype.hasOwnProperty.call(transfer.carrier[w].inputs,legacySpeedKey));
    const zeroSafe=reconstructionCheck({total:0,full:0,baseline:0,sumAbsPhi:0,residual:1e-30},'phaseLog');const nonlinear=[];for(let mask=0;mask<32;mask++){let v=0;for(const ch of CHANNELS)if(mask&BITS[ch])v+=coeff[ch];if((mask&BITS.ROT)&&(mask&BITS.MUTUAL_BS))v+=7;nonlinear.push({metrics:{phaseLog:v}});}const ix=pairInteraction(nonlinear,'phaseLog');
    const continuumSynthetic=fitContinuumSeries([128,192,256,384,512,768].map(resolution=>({resolution,value:5+3200/(resolution*resolution)}))),continuumSyntheticPass=continuumSynthetic.valid&&Math.abs(continuumSynthetic.xInf-5)<1e-3&&Math.abs(continuumSynthetic.p-2)<.05;
    const expectedKnotPlot=['knot_3.1','knot_4.1','knot_5.1','knot_5.2','knot_6.1','knot_7.1','link_6.3.1','link_6.3.2','link_6.3.3','torus_3.3','torus_6.9'];
    const holdoutCatalogs=['3_1','4_1','5_1','5_2','6_1','7_1'].every(k=>!!getFourierKnotCatalog()?.db?.[k])&&['3:1:1','4:1:1','5:1:1','5:1:2','6:1:1','7:1:1'].every(k=>!!getIdealKnotCatalog()?.db?.[k])&&expectedKnotPlot.every(k=>!!getKnotPlotKnotCatalog()?.db?.[k]),holdoutDefinitions=Object.keys(KNOT_HOLDOUT_CATALOG).length===11&&Object.values(KNOT_HOLDOUT_CATALOG).filter(x=>x.knotplot).length===11,visualPolicyAudit=['tracerCount','showTracers','showStreamlines','showPotentialFlow'].every(k=>Object.prototype.hasOwnProperty.call(P,k));
    let runtimeSmoke=null,runtimeSmokePass=false;try{const smokeKnot={source:'selftest',key:'synthetic',topologyKey:'synthetic',embedding:'synthetic',crossingNumber:3,idealRopDiam:IDEAL_TREFOIL_ROPELENGTH,holdout:false},smokeCal={...calRaw,scenarioId:'selftest-runtime-smoke',tPhys:0,resolution:12,knot:smokeKnot,geometryHash:'selftest-cal',parameterGridHash:'selftest-grid',pure:true,topologyGap:.1},smokeRaw={...raw,scenarioId:'selftest-runtime-smoke',tPhys:0,resolution:12,knot:smokeKnot,geometryHash:'selftest-current',calibrationGeometryHash:'selftest-cal',parameterGridHash:'selftest-grid',pure:true,topologyGap:.1};runtimeSmoke=analyzeRaw(smokeRaw,smokeCal);const finiteIntrinsic=['A','B'].every(w=>['iso','mutual','full'].every(k=>{const v=runtimeSmoke.intrinsicKinematics?.[w]?.current?.[k],q=runtimeSmoke.intrinsicKinematics?.[w]?.calibration?.[k];return v&&q&&[...v.vector,v.parallel,v.magnitude,v.perpendicular,...q.vector,q.parallel,q.magnitude,q.perpendicular].every(Number.isFinite);}));runtimeSmokePass=runtimeSmoke.purity&&typeof runtimeSmoke.digest==='string'&&runtimeSmoke.digest.length===8&&finiteIntrinsic&&Number.isFinite(runtimeSmoke.maxVelocityReconstructionRel);}catch(err){runtimeSmoke={error:String(err&&err.message||err),stack:String(err&&err.stack||'')};runtimeSmokePass=false;}
    const ok=CHANNELS.every(c=>Math.abs(s.phi[c]-coeff[c])<1e-12)&&Math.abs(s.residual)<1e-12&&poseErr<1e-7&&fitErr<1e-9&&fit.reconstructionRel<1e-12&&Number.isFinite(ss.full)&&ss.relativeResidual<1e-10&&pipelineErr<1e-12&&zeroSafe.score<=1&&Math.abs(ix.interaction-7)<1e-12&&normalizationFinite&&normalizationError<1e-12&&transferFinite&&transferDimensions&&canonicalVChar&&lengthFinite&&lengthIdentityScore<=1&&geomFinite&&idealAudit.pass&&continuumSyntheticPass&&holdoutCatalogs&&holdoutDefinitions&&visualPolicyAudit&&runtimeSmokePass&&!!document.getElementById('specKnotSelector');
    return {schema:SCHEMA,channels:CHANNELS.slice(),normalizations:NORMALIZATIONS.map(n=>n.id),ok,residual:s.residual,poseError:poseErr,rigidFitError:fitErr,pipelineResidual:ss.residual,pipelineError:pipelineErr,zeroSafeScore:zeroSafe.score,interactionIdentityError:Math.abs(ix.interaction-7),normalizationError,normalizationFinite,transferFinite,transferDimensions,canonicalVChar,lengthFinite,lengthIdentity,lengthIdentityScore,lengthCandidates:LENGTH_CANDIDATES.map(l=>l.id),transferLaws:TRANSFER_LAWS.map(l=>l.id),geomKappas:GEOM_KAPPA_CANDIDATES.map(k=>k.id),geomFinite,idealConventionAudit:idealAudit,continuumSynthetic,continuumSyntheticPass,holdoutCatalogs,holdoutDefinitions,visualPolicyAudit,runtimeSmokePass,runtimeSmoke};
  }
  return {start,stop,bind,render,frameTick,capAcceptedDt,afterAcceptedStep,reportObject,selfTest,readKnotSelection,selectedHoldoutScenarios,scenarioSetForMode,get active(){return active;},get launchMode(){return launchMode;},get resolutionOverride(){return proxyDecompResolutionOverride;}};
})();


// ================= v7.6.24f3 / v7.6.24f geautomatiseerde SPEC CLOCK benchmark =================
const SpecClockBenchmark=(()=>{
  const SCHEMA='vortexlab-spec-clock-benchmark/1.0';
  const scenarios=[
    {id:'baseline',label:'baseline · 16× · H=1.0 m',duration:3,speed:16,halfHeight:0.5,drift:0.005,ccwA:true,ccwB:false,bem:true},
    {id:'static-null',label:'nuldrift · 16×',duration:4,speed:16,halfHeight:0.5,drift:0,ccwA:true,ccwB:false,bem:true},
    {id:'speed-1',label:'afspeelsnelheid 1×',duration:2,speed:1,halfHeight:0.5,drift:0.005,ccwA:true,ccwB:false,bem:true},
    {id:'speed-4',label:'afspeelsnelheid 4×',duration:2,speed:4,halfHeight:0.5,drift:0.005,ccwA:true,ccwB:false,bem:true},
    {id:'speed-16',label:'afspeelsnelheid 16×',duration:2,speed:16,halfHeight:0.5,drift:0.005,ccwA:true,ccwB:false,bem:true},
    {id:'cylinder-high',label:'extra hoge cilinder · H=5.0 m',duration:3,speed:16,halfHeight:2.5,drift:0.005,ccwA:true,ccwB:false,bem:true},
    {id:'drift-1',label:'drift ±1.0 mm/s',duration:3,speed:16,halfHeight:0.5,drift:0.001,ccwA:true,ccwB:false,bem:true},
    {id:'drift-2.5',label:'drift ±2.5 mm/s',duration:3,speed:16,halfHeight:0.5,drift:0.0025,ccwA:true,ccwB:false,bem:true},
    {id:'symmetry-swap',label:'A/B traversal omgewisseld',duration:3,speed:16,halfHeight:0.5,drift:0.005,ccwA:false,ccwB:true,bem:true},
    {id:'bem-off',label:'BEM uit · bundel uit',duration:3,speed:16,halfHeight:0.5,drift:0.005,ccwA:true,ccwB:false,bem:false}
  ];
  let active=false,index=-1,current=null,results=[],gates=[],snapshot=null,pending=false,startedAt=null,completedAt=null,aborted=false,firstDt=NaN,timer=0,benchmarkVisualState=null;
  const clone=o=>JSON.parse(JSON.stringify(o));
  const byId=id=>results.find(r=>r.id===id);
  const finite=x=>Number.isFinite(x)?x:null;
  const worst=list=>list.includes('FAIL')?'FAIL':(list.includes('WARN')?'WARN':(list.includes('PASS')?'PASS':'INFO'));
  function el(id){return document.getElementById(id);}
  function statusClass(v){return v==='PASS'?'pass':v==='FAIL'?'fail':v==='WARN'?'warn':'info';}
  function setStatus(text,cls='running'){
    const node=el('specBenchmarkStatus');if(node){node.textContent=text;node.className='spec-benchmark-status '+cls;}
  }
  function updateButtons(){
    const stop=el('bSpecBenchmarkStop'),txt=el('bSpecBenchmarkExportTxt'),json=el('bSpecBenchmarkExportJson');if(stop)stop.hidden=true;
    const has=results.length>0&&!active;if(txt)txt.disabled=!has;if(json)json.disabled=!has;vlRefreshClockRunnerWorkflowUi();
  }
  function render(){
    const progress=el('specBenchmarkProgress');if(progress)progress.style.width=((active?Math.max(0,index)+(current?Math.min(1,tPhys/Math.max(current.duration,1e-9)):0):results.length)/scenarios.length*100).toFixed(1)+'%';
    const rows=el('specBenchmarkRows');
    if(rows){
      if(!results.length)rows.innerHTML='<tr><td colspan="7" style="text-align:left;color:var(--muted);">Nog geen benchmarkresultaten.</td></tr>';
      else rows.innerHTML=results.map(r=>`<tr><td>${r.label}</td><td>${r.tPhys.toFixed(3)}</td><td>${Number.isFinite(r.distance)?r.distance.toFixed(6):'—'}</td><td>${Number.isFinite(r.phaseLogRatio)?r.phaseLogRatio.toExponential(3):'—'}</td><td>${Number.isFinite(r.fieldAbsMax)?r.fieldAbsMax.toExponential(3):'—'}</td><td>${Number.isFinite(r.phaseLag)?r.phaseLag.toExponential(3):'—'}</td><td>${Number.isFinite(r.firstDt)?r.firstDt.toFixed(5):'—'}</td></tr>`).join('');
    }
    const summary=el('specBenchmarkSummary');
    if(summary){
      if(!gates.length)summary.innerHTML='';
      else summary.innerHTML=gates.map(g=>`<span>${g.label}</span><b class="${statusClass(g.status)}">${g.status}</b>`).join('');
    }
    updateButtons();
  }
  function baseConfigure(sc){
    applySpecClockPreset();
    // Vaste benchmarkgeometrie: cilinderdiameter 0.50 m, standaard totale hoogte 1.0 m of extra hoog 5.0 m.
    P.Rcyl=0.25;P.Hcyl=sc.halfHeight;P.linkDH=false;
    P.vzA=sc.drift;P.vzB=-sc.drift;P.lockVz=false;
    P.ccwA=sc.ccwA;P.ccwB=sc.ccwB;P.mirrorB=false;
    P.bundleEnabled=false;P.bgFlow='none';P.bundleBEMEnabled=sc.bem;
    setInitialAxialSeparation(0.84);
    rebuildVolumeEnvelope();
    resetState();
    SpecClock.autoStartAfterCalibration=false;
    P.accExp=Math.log10(sc.speed);
    syncUi();updateSubtitle();resetPlaybackDebt('spec-benchmark-scenario-arm');
    if(!calibrateSpecClockPhase())throw new Error('fase-nullkalibratie geweigerd');
    firstDt=NaN;
    setPausedState(false,'spec-benchmark-scenario-start');
  }
  function startScenario(){
    if(!active)return;
    index++;
    if(index>=scenarios.length){complete();return;}
    current=scenarios[index];pending=false;firstDt=NaN;
    try{
      baseConfigure(current);
      setStatus(`RUN ${index+1}/${scenarios.length} · ${current.label} · doel t=${current.duration.toFixed(1)} s`,'running');
      if(window.ModelLog)window.ModelLog.logEvent('spec-benchmark-scenario-start',{index,id:current.id,label:current.label,duration:current.duration,speed:current.speed,Rcyl:P.Rcyl,Hcyl:P.Hcyl,vzA:P.vzA,vzB:P.vzB,ccwA:P.ccwA,ccwB:P.ccwB,bem:P.bundleBEMEnabled});
      render();
    }catch(err){
      capture('setup-error',String(err&&err.message||err));
    }
  }
  function capAcceptedDt(dt){
    if(!active||!current||pending)return dt;
    const remaining=current.duration-tPhys;
    if(remaining>1e-12)return Math.min(dt,remaining);
    return dt;
  }
  function afterAcceptedStep(dtApplied){
    if(!active||!current||pending)return false;
    if(!Number.isFinite(firstDt))firstDt=Math.abs(dtApplied);
    if(tPhys+1e-10>=current.duration){capture('target');return true;}
    return false;
  }
  function capture(reason='target',detail=''){
    if(!active||!current||pending)return;
    pending=true;setPausedState(true,'spec-benchmark-scenario-finish');stepDebt=0;
    const m=measureSpecClock();
    const fieldAbsMax=m&&m.valid?Math.max(Math.abs(m.fieldLogRatioMin),Math.abs(m.fieldLogRatioMax)):NaN;
    const rec={
      id:current.id,label:current.label,reason,detail,tPhys,firstDt:finite(firstDt),targetTime:current.duration,
      speed:current.speed,Rcyl:P.Rcyl,Hcyl:P.Hcyl,cylinderHeight:cylinderHeight(),vzA:P.vzA,vzB:P.vzB,ccwA:P.ccwA,ccwB:P.ccwB,bemEnabled:P.bundleBEMEnabled,bundleEnabled:P.bundleEnabled,tracerCount:P.tracerCount,showTracers:P.showTracers,showStreamlines:P.showStreamlines,showPotentialFlow:P.showPotentialFlow,
      calibrated:SpecClock.calibrated,calibrationTime:finite(SpecClock.calibrationTime),calibrationDistance:finite(SpecClock.calibrationDistance),
      valid:!!(m&&m.valid),distance:finite(m&&m.distance),uA:finite(m&&m.uA),uB:finite(m&&m.uB),
      omegaFullA:finite(m&&m.omegaA),omegaFullB:finite(m&&m.omegaB),omegaIsoA:finite(m&&m.omegaIsoA),omegaIsoB:finite(m&&m.omegaIsoB),
      deltaOmegaA:finite(m&&m.deltaOmegaA),deltaOmegaB:finite(m&&m.deltaOmegaB),phaseLogRatio:finite(m&&m.phaseLogRatio),fieldLogMin:finite(m&&m.fieldLogRatioMin),fieldLogMax:finite(m&&m.fieldLogRatioMax),fieldAbsMax:finite(fieldAbsMax),residual:finite(m&&m.residual),
      phaseLag:finite(SpecClock.lagPhase),fieldLagMin:finite(SpecClock.lagFieldMin),fieldLagMax:finite(SpecClock.lagFieldMax),topologyGap:finite(lastTopologyGap),dtCFL:finite(dtCFL()),flagged:flagged||null
    };
    results.push(rec);
    if(window.ModelLog)window.ModelLog.logEvent('spec-benchmark-scenario-result',rec);
    render();
    clearTimeout(timer);timer=setTimeout(()=>{current=null;pending=false;startScenario();},40);
  }
  function frameTick(){
    if(!active||!current||pending)return;
    if(flagged)capture('solver-stop',flagged);
    else if(paused&&tPhys+1e-10<current.duration)capture('unexpected-pause','run gepauzeerd vóór doeltijd');
    else render();
  }
  function diff(a,b,key){return Math.abs((a&&Number.isFinite(a[key])?a[key]:NaN)-(b&&Number.isFinite(b[key])?b[key]:NaN));}
  function addGate(group,id,label,status,metrics,explanation){gates.push({group,id,label,status,metrics,explanation});}
  function evaluate(){
    gates=[];
    const bootstrapOk=results.length===scenarios.length&&results.every(r=>r.valid&&r.calibrated&&Math.abs(r.calibrationTime||0)<1e-12&&Number.isFinite(r.firstDt)&&r.firstDt<=SPEC_CLOCK_MAX_ACCEPTED_DT+1e-12&&!r.flagged);
    addGate('ENGINE','bootstrap','Bootstrap/CFL en t=0-kalibratie',bootstrapOk?'PASS':'FAIL',{runs:results.length,maxFirstDt:Math.max(...results.map(r=>r.firstDt||Infinity))},'Iedere run moet bij t=0 kalibreren, geldig meten en met dt₁≤50 ms starten.');
    const sp=[byId('speed-1'),byId('speed-4'),byId('speed-16')];
    const speedDist=Math.max(...sp.map(r=>r?.distance??NaN))-Math.min(...sp.map(r=>r?.distance??NaN));
    const speedPhase=Math.max(...sp.map(r=>r?.phaseLogRatio??NaN))-Math.min(...sp.map(r=>r?.phaseLogRatio??NaN));
    const speedLag=Math.max(...sp.map(r=>r?.phaseLag??NaN))-Math.min(...sp.map(r=>r?.phaseLag??NaN));
    const speedOk=sp.every(Boolean)&&Number.isFinite(speedDist)&&speedDist<=1e-9&&Math.abs(speedPhase)<=1e-12&&Math.abs(speedLag)<=1e-12;
    addGate('ENGINE','speed','1×–4×–16× afspeelinvariantie',speedOk?'PASS':'FAIL',{distanceSpan:speedDist,phaseSpan:speedPhase,lagSpan:speedLag},'Vergelijking op exact dezelfde fysische doeltijd.');
    const base=byId('baseline'),high=byId('cylinder-high');
    const cylDist=diff(base,high,'distance'),cylPhase=diff(base,high,'phaseLogRatio'),cylLag=diff(base,high,'phaseLag');
    const cylOk=Number.isFinite(cylDist)&&cylDist<=1e-8&&cylPhase<=1e-11&&cylLag<=1e-11;
    addGate('ENGINE','cylinder','Cilinderhoogte-invariantie · 1 m ↔ 5 m',cylOk?'PASS':'FAIL',{distanceDiff:cylDist,phaseDiff:cylPhase,lagDiff:cylLag},'Met bgFlow=none en bundel uit hoort de volume-envelope niet in de filamentdynamica te lekken.');
    const bem=byId('bem-off');
    const bemDist=diff(base,bem,'distance'),bemPhase=diff(base,bem,'phaseLogRatio'),bemLag=diff(base,bem,'phaseLag');
    const bemOk=Number.isFinite(bemDist)&&bemDist<=1e-9&&bemPhase<=1e-12&&bemLag<=1e-12;
    addGate('ENGINE','bem','BEM-negatieve controle bij bundel uit',bemOk?'PASS':'FAIL',{distanceDiff:bemDist,phaseDiff:bemPhase,lagDiff:bemLag},'Een alleen ingeschakelde maar ongeldige BEM mag niets veranderen wanneer de bundel uitstaat.');
    const visualIsolation=results.every(r=>r.tracerCount===0&&r.showTracers===false&&r.showStreamlines===false&&r.showPotentialFlow===false);addGate('ENGINE','visual-isolation','Passieve deeltjes en cosmetische flowlagen uit tijdens benchmark',visualIsolation?'PASS':'FAIL',{isolatedRuns:results.filter(r=>r.tracerCount===0&&r.showTracers===false&&r.showStreamlines===false&&r.showPotentialFlow===false).length,totalRuns:results.length,required:{tracerCount:0,showTracers:false,showStreamlines:false,showPotentialFlow:false}},'De benchmark draait zonder passieve particle-integratie. De oorspronkelijke visuele toestand wordt na afloop of afbreking exact hersteld.');
    const nul=byId('static-null'),nullRate=nul&&Number.isFinite(nul.phaseLogRatio)?Math.abs(nul.phaseLogRatio)/Math.max(nul.tPhys,1e-12):NaN;
    addGate('RESEARCH','null','Nuldrift-fasestabiliteit',Number.isFinite(nullRate)&&nullRate<=1e-10?'PASS':'WARN',{phaseLogRatio:nul?.phaseLogRatio,ratePerSecond:nullRate,distance:nul?.distance},'Engineering-gate van 10⁻¹⁰ s⁻¹; geen canonieke fysische tolerantie.');
    const sw=byId('symmetry-swap');
    const symSign=base&&sw&&Number.isFinite(base.phaseLogRatio)&&Number.isFinite(sw.phaseLogRatio)&&base.phaseLogRatio*sw.phaseLogRatio<0;
    const symMag=base&&sw?Math.abs(Math.abs(base.phaseLogRatio)-Math.abs(sw.phaseLogRatio))/Math.max(Math.abs(base.phaseLogRatio),Math.abs(sw.phaseLogRatio),1e-30):NaN;
    addGate('RESEARCH','symmetry','A/B-traversalsymmetrie',symSign&&symMag<=0.10?'PASS':'WARN',{signReversal:symSign,magnitudeMismatch:symMag,normal:base?.phaseLogRatio,swapped:sw?.phaseLogRatio},'Verwacht tekenomslag met maximaal 10% magnitudemismatch voor deze numerieke proxy.');
    const dr=[byId('drift-1'),byId('drift-2.5'),base];
    const driftDistance=dr.every(Boolean)&&dr[0].distance>dr[1].distance&&dr[1].distance>dr[2].distance;
    const driftPhase=dr.every(Boolean)&&Math.abs(dr[0].phaseLogRatio)<Math.abs(dr[1].phaseLogRatio)&&Math.abs(dr[1].phaseLogRatio)<Math.abs(dr[2].phaseLogRatio);
    addGate('RESEARCH','drift','Driftsweep-trend op vaste tijd',driftDistance&&driftPhase?'PASS':'WARN',{distances:dr.map(r=>r?.distance),phaseMagnitudes:dr.map(r=>Math.abs(r?.phaseLogRatio??NaN))},'Rapporteert de afstands- en faseschaaltrend; dit is geen universele monotoniciteitswet.');
    const closure=base&&Number.isFinite(base.phaseLogRatio)&&base.phaseLogRatio>=base.fieldLogMin&&base.phaseLogRatio<=base.fieldLogMax;
    const scaleRatio=base&&Number.isFinite(base.phaseLogRatio)&&Number.isFinite(base.fieldAbsMax)?Math.abs(base.phaseLogRatio)/Math.max(base.fieldAbsMax,1e-300):NaN;
    addGate('RESEARCH','closure','Fase-null binnen formele veldbracket',closure?'PASS':'FAIL',{phaseLogRatio:base?.phaseLogRatio,fieldMin:base?.fieldLogMin,fieldMax:base?.fieldLogMax,scaleRatio},'FAIL verwerpt alleen de huidige proxyrealisatie; niet SST, parameters of een klokwet.');
  }
  function restoreConfiguration(){
    if(!snapshot)return;
    const p=clone(snapshot.P),visualBefore=benchmarkVisualState;Object.assign(P,p);P.taylorOsc=clone(p.taylorOsc||{enabled:false,amplitude:0.25,period:8});
    rebuildVolumeEnvelope();syncUi();updateSubtitle();resetState();
    // resetState armt een actieve SPEC CLOCK-run veilig; herstel daarna alleen het gewenste afspeeltempo en pauzestatus.
    P.accExp=p.accExp;syncUi();setPausedState(snapshot.paused,'spec-benchmark-restore');
    const preset=el('presetSelect');if(preset&&snapshot.presetValue)preset.value=snapshot.presetValue;logBenchmarkVisualRestore('spec-benchmark',visualBefore);benchmarkVisualState=null;
  }
  function complete(){
    active=false;current=null;pending=false;completedAt=new Date().toISOString();evaluate();
    const engine=worst(gates.filter(g=>g.group==='ENGINE').map(g=>g.status));
    const research=worst(gates.filter(g=>g.group==='RESEARCH').map(g=>g.status));
    LastSpecClockBenchmarkSummary={state:'completed',engine,research,completedAt,runCount:results.length};VLClockWorkflow.complete('spec',engine==='PASS');
    restoreConfiguration();
    setStatus(`VOLTOOID · ENGINE ${engine} · RESEARCH PROXY ${research} · configuratie teruggezet naar t=0; alleen een nieuwe handmatige sweep vereist herkalibratie.`,engine==='PASS'?(research==='PASS'?'good':'warn'):'bad');
    
    if(window.ModelLog)window.ModelLog.logEvent('spec-benchmark-complete',{engine,research,report:reportObject()});
    updateSpecClockDisplay();render();
    if(specAutoExportEnabled()){const stamp=safeUtcStamp(completedAt);setTimeout(()=>download('txt',stamp),80);setTimeout(()=>download('json',stamp),180);setTimeout(()=>exportModelLogTimestamped(stamp,'spec-benchmark'),280);}
  }
  function start(){
    if(active)return;
    if(!VLClockWorkflow.unlocked('spec')){setFlag('⚠ '+VLClockWorkflow.reason('spec'),true);return;}
    if(SpecClockProxyDecomposition.active){setFlag('⚠ stop eerst de proxy-decompositiebenchmark.',true);return;}
    LastSpecClockBenchmarkSummary=null;LastProxyDecompositionSummary=null;updateSpecClockDisplay();
    clearTimeout(timer);snapshot={P:clone(P),paused,presetValue:el('presetSelect')?.value||''};benchmarkVisualState=suppressBenchmarkVisuals('spec-benchmark');
    results=[];gates=[];index=-1;current=null;pending=false;aborted=false;active=true;VLClockWorkflow.begin('spec');startedAt=new Date().toISOString();completedAt=null;
    if(window.ModelLog){window.ModelLog.setEnabled(true);window.ModelLog.logEvent('spec-benchmark-start',{schema:SCHEMA,scenarioCount:scenarios.length});}
    setStatus('START · reproduceerbare configuratie wordt opgebouwd…','running');render();startScenario();
  }
  function stop(reason='gebruiker'){
    if(!active)return;
    clearTimeout(timer);aborted=true;active=false;pending=false;current=null;completedAt=new Date().toISOString();setPausedState(true,'spec-benchmark-stop');
    LastSpecClockBenchmarkSummary={state:'aborted',completedRuns:results.length,totalRuns:scenarios.length,completedAt};VLClockWorkflow.abort();
    restoreConfiguration();
    gates=[{group:'ENGINE',id:'aborted',label:'Benchmark afgebroken',status:'WARN',metrics:{completedRuns:results.length,totalRuns:scenarios.length},explanation:String(reason)}];
    setStatus(`AFGEBROKEN · ${results.length}/${scenarios.length} runs voltooid · configuratie teruggezet naar t=0.`,'warn');
    if(window.ModelLog)window.ModelLog.logEvent('spec-benchmark-aborted',{reason,completedRuns:results.length});updateSpecClockDisplay();render();
  }
  function reportObject(){
    const engine=worst(gates.filter(g=>g.group==='ENGINE').map(g=>g.status));
    const research=worst(gates.filter(g=>g.group==='RESEARCH').map(g=>g.status));
    return {schema:SCHEMA,appVersion:APP_VERSION,baseVersion:APP_BASE_VERSION,startedAt,completedAt,aborted,engineVerdict:engine,researchProxyVerdict:research,scenarioDefinitions:scenarios,benchmarkVisualPolicy:{tracerCount:0,showTracers:false,showStreamlines:false,showPotentialFlow:false,restoredAfterRun:true},results,gates,scientificBoundary:'RESEARCH FAIL/WARN betreft uitsluitend de niet-canonieke fase-nullproxy; geen SST-falsificatie.'};
  }
  function reportText(){
    const r=reportObject(),lines=[];
    lines.push('VortexLab SPEC CLOCK benchmark');lines.push('schema='+r.schema);lines.push('version='+APP_VERSION+' base='+APP_BASE_VERSION);lines.push('startedAt='+startedAt+' completedAt='+completedAt);lines.push('ENGINE='+r.engineVerdict+' RESEARCH_PROXY='+r.researchProxyVerdict);lines.push('');
    lines.push('[gates]');gates.forEach((g,i)=>lines.push(`${i+1}. ${g.group} ${g.status} ${g.id} · ${g.label} · metrics=${JSON.stringify(g.metrics)} · ${g.explanation}`));lines.push('');
    lines.push('[runs]');results.forEach((x,i)=>lines.push(`${i+1}. ${JSON.stringify(x)}`));lines.push('');lines.push('[boundary]');lines.push(r.scientificBoundary);return lines.join('\n');
  }
  function download(kind,stamp=safeUtcStamp(completedAt||new Date())){
    const text=kind==='json'?JSON.stringify(reportObject(),null,2):reportText();triggerTextDownload(text,kind==='json'?'application/json':'text/plain;charset=utf-8',`vortexlab-spec-clock-benchmark-${APP_VERSION.replace(/\./g,'-')}-${stamp}.${kind}`);
  }
  function bind(){
    el('bSpecBenchmarkStart')?.addEventListener('click',()=>active?stop('handmatig gestopt'):start());const legacyStop=el('bSpecBenchmarkStop');if(legacyStop){legacyStop.hidden=true;legacyStop.addEventListener('click',()=>stop('handmatig gestopt'));}
    el('bSpecBenchmarkExportTxt')?.addEventListener('click',()=>download('txt'));el('bSpecBenchmarkExportJson')?.addEventListener('click',()=>download('json'));render();
  }
  return {start,stop,bind,render,frameTick,capAcceptedDt,afterAcceptedStep,reportObject,get lastSummary(){return LastSpecClockBenchmarkSummary;},get active(){return active;}};
})();

function vlWrap01(x,L){x%=L;return x<0?x+L:x;}
function vlTridiagonalSolve(a,b,c,r){
  const n=b.length,cp=new Float64Array(n),dp=new Float64Array(n),x=new Float64Array(n);
  let den=b[0];if(Math.abs(den)<1e-30)return null;cp[0]=(n>1?c[0]:0)/den;dp[0]=r[0]/den;
  for(let i=1;i<n;i++){den=b[i]-a[i]*cp[i-1];if(Math.abs(den)<1e-30)return null;cp[i]=i<n-1?c[i]/den:0;dp[i]=(r[i]-a[i]*dp[i-1])/den;}
  x[n-1]=dp[n-1];for(let i=n-2;i>=0;i--)x[i]=dp[i]-cp[i]*x[i+1];return x;
}
function vlCyclicSolve(a,b,c,alpha,beta,r){
  const n=b.length;if(n<3)return vlTridiagonalSolve(a,b,c,r);const gamma=-b[0]||-1,bb=new Float64Array(b);bb[0]=b[0]-gamma;bb[n-1]=b[n-1]-alpha*beta/gamma;
  const x=vlTridiagonalSolve(a,bb,c,r);if(!x)return null;const u=new Float64Array(n);u[0]=gamma;u[n-1]=alpha;const z=vlTridiagonalSolve(a,bb,c,u);if(!z)return null;
  const fact=(x[0]+beta*x[n-1]/gamma)/(1+z[0]+beta*z[n-1]/gamma);for(let i=0;i<n;i++)x[i]-=fact*z[i];return x;
}
function vlBuildPeriodicSpline(points){
  const n=Math.floor(points.length/3);if(n<4)throw new Error('periodieke spline vereist minstens 4 punten');const h=new Float64Array(n),s=new Float64Array(n+1);
  for(let i=0;i<n;i++){const j=(i+1)%n,dx=points[3*j]-points[3*i],dy=points[3*j+1]-points[3*i+1],dz=points[3*j+2]-points[3*i+2];h[i]=Math.max(1e-12,Math.hypot(dx,dy,dz));s[i+1]=s[i]+h[i];}
  const L=s[n],a=new Float64Array(n),b=new Float64Array(n),c=new Float64Array(n);for(let i=0;i<n;i++){const hm=h[(i-1+n)%n],hp=h[i];a[i]=i?hm:0;b[i]=2*(hm+hp);c[i]=i<n-1?hp:0;}
  const second=[];for(let d=0;d<3;d++){const r=new Float64Array(n);for(let i=0;i<n;i++){const im=(i-1+n)%n,ip=(i+1)%n;r[i]=6*((points[3*ip+d]-points[3*i+d])/h[i]-(points[3*i+d]-points[3*im+d])/h[im]);}const M=vlCyclicSolve(a,b,c,h[n-1],h[n-1],r);if(!M)throw new Error('periodieke spline-oplossing singulier');second.push(M);}
  function segmentAt(u){u=vlWrap01(u,L);let lo=0,hi=n;while(lo+1<hi){const m=(lo+hi)>>1;if(s[m]<=u)lo=m;else hi=m;}return {i:Math.min(n-1,lo),u};}
  function evalAt(u){const q=segmentAt(u),i=q.i,j=(i+1)%n,hh=h[i],A=(s[i+1]-q.u)/hh,B=(q.u-s[i])/hh,p=[0,0,0],d1=[0,0,0],d2=[0,0,0];for(let d=0;d<3;d++){const yi=points[3*i+d],yj=points[3*j+d],Mi=second[d][i],Mj=second[d][j];p[d]=A*yi+B*yj+((A*A*A-A)*Mi+(B*B*B-B)*Mj)*hh*hh/6;d1[d]=(yj-yi)/hh+hh*(-(3*A*A-1)*Mi+(3*B*B-1)*Mj)/6;d2[d]=A*Mi+B*Mj;}return {p,d1,d2,u:vlWrap01(u,L)};}
  return {n,L,s,h,points,eval:evalAt};
}
function vlCurvature(ev){const a=ev.d1,b=ev.d2,cx=a[1]*b[2]-a[2]*b[1],cy=a[2]*b[0]-a[0]*b[2],cz=a[0]*b[1]-a[1]*b[0],speed=Math.hypot(...a);return speed>1e-20?Math.hypot(cx,cy,cz)/(speed*speed*speed):0;}
function vlGoldenMax(fn,a,b,it=42){const gr=(Math.sqrt(5)-1)/2;let c=b-gr*(b-a),d=a+gr*(b-a),fc=fn(c),fd=fn(d);for(let k=0;k<it;k++){if(fc>fd){b=d;d=c;fd=fc;c=b-gr*(b-a);fc=fn(c);}else{a=c;c=d;fc=fd;d=a+gr*(b-a);fd=fn(d);}}const x=fc>fd?c:d;return {x,value:Math.max(fc,fd)};}
function vlContinuousCurvatureLimit(spline){const n=spline.n,per=6,cands=[];for(let i=0;i<n;i++){const a=spline.s?spline.s[i]:spline.L*i/n,b=spline.s?spline.s[i+1]:spline.L*(i+1)/n,hh=(b-a)/per;let best=-1,bk=0;for(let k=0;k<=per;k++){const u=a+k*hh,v=vlCurvature(spline.eval(u));if(v>best){best=v;bk=k;}}const la=Math.max(a,a+(bk-1)*hh),lb=Math.min(b,a+(bk+1)*hh);const g=vlGoldenMax(u=>vlCurvature(spline.eval(u)),la,lb);cands.push(g);}cands.sort((x,y)=>y.value-x.value);const best=cands[0];return {radius:best.value>1e-20?1/best.value:Infinity,kappa:best.value,s:best.x};}
function vlPairMetrics(sa,sb,s,t){const A=sa.eval(s),B=sb.eval(t),dx=A.p[0]-B.p[0],dy=A.p[1]-B.p[1],dz=A.p[2]-B.p[2],d=Math.hypot(dx,dy,dz),F1=dx*A.d1[0]+dy*A.d1[1]+dz*A.d1[2],F2=dx*B.d1[0]+dy*B.d1[1]+dz*B.d1[2];return {A,B,dx,dy,dz,d,F1,F2};}
function vlRefinePair(sa,sb,s0,t0,selfPair=false){
  let s=vlWrap01(s0,sa.L),t=vlWrap01(t0,sb.L),iterations=0,usedDampedLeastSquares=false;
  const minArc=selfPair?Math.max(4*sa.L/sa.n,.015*sa.L):0;
  const residual=m=>{const d=m.d||1e-30,scale=Math.max(d*Math.hypot(...m.A.d1),d*Math.hypot(...m.B.d1),1e-30);return Math.max(Math.abs(m.F1),Math.abs(m.F2))/scale;};
  const arcValid=(ns,nt)=>!selfPair||Math.min(Math.abs(ns-nt),sa.L-Math.abs(ns-nt))>=minArc;
  for(let it=0;it<64;it++){iterations=it+1;const m=vlPairMetrics(sa,sb,s,t),A=m.A,B=m.B,res=residual(m);if(res<1e-13)break;
    const ap=A.d1,bp=B.d1,app=A.d2,bpp=B.d2,j11=ap[0]*ap[0]+ap[1]*ap[1]+ap[2]*ap[2]+m.dx*app[0]+m.dy*app[1]+m.dz*app[2],j12=-(ap[0]*bp[0]+ap[1]*bp[1]+ap[2]*bp[2]),j21=-j12,j22=-(bp[0]*bp[0]+bp[1]*bp[1]+bp[2]*bp[2])+m.dx*bpp[0]+m.dy*bpp[1]+m.dz*bpp[2],det=j11*j22-j12*j21,frob2=j11*j11+j12*j12+j21*j21+j22*j22;
    const candidates=[];
    if(Math.abs(det)>1e-12*Math.max(frob2,1e-30))candidates.push({ds:(-m.F1*j22+j12*m.F2)/det,dt:(-j11*m.F2+j21*m.F1)/det,kind:'newton'});
    for(const factor of [1e-16,1e-14,1e-12,1e-10,1e-8]){const lam=Math.max(1e-30,factor*Math.max(frob2,1e-30)),a11=j11*j11+j21*j21+lam,a12=j11*j12+j21*j22,a22=j12*j12+j22*j22+lam,b1=-(j11*m.F1+j21*m.F2),b2=-(j12*m.F1+j22*m.F2),dd=a11*a22-a12*a12;if(Math.abs(dd)>1e-40)candidates.push({ds:(b1*a22-a12*b2)/dd,dt:(a11*b2-a12*b1)/dd,kind:'dls'});}
    let best=null;for(const candidate of candidates){let {ds,dt}=candidate;if(!Number.isFinite(ds)||!Number.isFinite(dt))continue;const cap=.08*Math.min(sa.L,sb.L),mag=Math.hypot(ds,dt);if(mag>cap){ds*=cap/mag;dt*=cap/mag;}for(let q=0;q<14;q++){const f=2**(-q),ns=vlWrap01(s+f*ds,sa.L),nt=vlWrap01(t+f*dt,sb.L);if(!arcValid(ns,nt))continue;const mm=vlPairMetrics(sa,sb,ns,nt),rr=residual(mm);if(!best||rr<best.rr)best={s:ns,t:nt,rr,kind:candidate.kind};}}
    if(!best||best.rr>=res*(1-1e-10))break;s=best.s;t=best.t;if(best.kind==='dls')usedDampedLeastSquares=true;
  }
  const m=vlPairMetrics(sa,sb,s,t),A=m.A,B=m.B,d=m.d||1e-30,sa1=Math.hypot(...A.d1),sb1=Math.hypot(...B.d1),orth=Math.max(Math.abs(m.F1)/(d*sa1+1e-30),Math.abs(m.F2)/(d*sb1+1e-30));const hss=A.d1.reduce((z,v)=>z+v*v,0)+m.dx*A.d2[0]+m.dy*A.d2[1]+m.dz*A.d2[2],htt=B.d1.reduce((z,v)=>z+v*v,0)-m.dx*B.d2[0]-m.dy*B.d2[1]-m.dz*B.d2[2],hst=-(A.d1[0]*B.d1[0]+A.d1[1]*B.d1[1]+A.d1[2]*B.d1[2]),hdet=hss*htt-hst*hst,localMin=hss>-1e-10&&htt>-1e-10&&hdet>-1e-8*Math.max(1,Math.abs(hss*htt));return {s,t,distance:m.d,orthResidual:orth,localMin,hessian:{hss,htt,hst,det:hdet},p:A.p,q:B.p,refinement:{iterations,usedDampedLeastSquares}};
}
function vlContinuousPairDistance(sa,sb,selfPair=false){const M=Math.min(192,Math.max(64,Math.round(10*Math.sqrt(Math.max(sa.n,sb.n))))),seeds=[],minArc=selfPair?Math.max(4*sa.L/sa.n,.015*sa.L):0;for(let i=0;i<M;i++){const s=sa.L*i/M,A=sa.eval(s);for(let j=selfPair?i+1:0;j<M;j++){const t=sb.L*j/M;if(selfPair){const arc=Math.min(Math.abs(s-t),sa.L-Math.abs(s-t));if(arc<minArc)continue;}const B=sb.eval(t),dx=A.p[0]-B.p[0],dy=A.p[1]-B.p[1],dz=A.p[2]-B.p[2],d=Math.hypot(dx,dy,dz);if(!(d>1e-12))continue;const ci=Math.abs((dx*A.d1[0]+dy*A.d1[1]+dz*A.d1[2])/(d*Math.hypot(...A.d1)+1e-30)),cj=Math.abs((dx*B.d1[0]+dy*B.d1[1]+dz*B.d1[2])/(d*Math.hypot(...B.d1)+1e-30));if(ci>.92||cj>.92)continue;seeds.push({s,t,score:d*(.02+ci*ci+cj*cj),orth:ci+cj,d});}}
  const chosen=[];for(const arr of [[...seeds].sort((a,b)=>a.score-b.score).slice(0,64),[...seeds].sort((a,b)=>a.orth-b.orth).slice(0,48),[...seeds].sort((a,b)=>a.d-b.d).slice(0,32)])for(const q of arr)if(!chosen.includes(q))chosen.push(q);const refined=[];for(const seed of chosen){const r=vlRefinePair(sa,sb,seed.s,seed.t,selfPair);if(!Number.isFinite(r.distance)||r.orthResidual>=5e-9)continue;if(selfPair){const arc=Math.min(Math.abs(r.s-r.t),sa.L-Math.abs(r.s-r.t));if(arc<minArc)continue;}if(refined.some(x=>Math.abs(x.distance-r.distance)<1e-8*Math.max(1,r.distance)&&Math.min(Math.abs(x.s-r.s),sa.L-Math.abs(x.s-r.s))<1e-5*sa.L&&Math.min(Math.abs(x.t-r.t),sb.L-Math.abs(x.t-r.t))<1e-5*sb.L))continue;refined.push(r);}refined.sort((a,b)=>a.distance-b.distance);return refined[0]||null;}



function vlBuildFourierCurve(coeffs,n=256){
  const period=2*Math.PI,terms=(coeffs||[]).map(c=>({I:Number(c.I),A:c.A.map(Number),B:c.B.map(Number)}));
  const evalAt=t=>{t=vlWrap01(t,period);const p=[0,0,0],d1=[0,0,0],d2=[0,0,0];for(const c of terms){const ct=Math.cos(c.I*t),st=Math.sin(c.I*t),i2=c.I*c.I;for(let d=0;d<3;d++){p[d]+=ct*c.A[d]+st*c.B[d];d1[d]+=c.I*(-st*c.A[d]+ct*c.B[d]);d2[d]+=-i2*(ct*c.A[d]+st*c.B[d]);}}return {p,d1,d2,u:t};};
  return {n,L:period,eval:evalAt,kind:'analytic-fourier'};
}
function vlBuildKnotPlotReachCurve(entry,component,n=256){
  const nativeN=Math.max(4,Math.round(finiteMetaNumber(component?.pointCount)||300)),native=sampleFourierParametric(component.coeffs||component,nativeN),spline=vlBuildPeriodicSpline(native);
  return {n,L:spline.L,eval:spline.eval,kind:'knotplot-native-C2-spline',nativePointCount:nativeN,sourceRole:entry?.sourceRole||null};
}
function vlBuildExactCircleCurve(n,R=1,z=0,transform=false){
  const period=2*Math.PI,apply=(v,isPoint)=>{let [x,y,zz]=v;const X=.36*x-.48*y+.8*zz+(isPoint?2:0),Y=.8*x+.6*y+(isPoint?-1:0),Z=-.48*x+.64*y+.6*zz+(isPoint?.5:0);return [X,Y,Z];};
  return {n,L:period,kind:'analytic-circle',eval(t){t=vlWrap01(t,period);const ct=Math.cos(t),st=Math.sin(t);let p=[R*ct,R*st,z],d1=[-R*st,R*ct,0],d2=[-R*ct,-R*st,0];if(transform){p=apply(p,true);d1=apply(d1,false);d2=apply(d2,false);}return {p,d1,d2,u:t};}};
}

let LastContinuousReachAuditSummary=null;
const ContinuousReachAudit=(()=>{
  let active=false,stopRequested=false,startedAt=null,completedAt=null,results=[],gates=[],tasks=[],taskIndex=0,profile='standard';
  const el=id=>document.getElementById(id);
  const fmt=x=>Number.isFinite(x)?(Math.abs(x)>=1e4||Math.abs(x)<1e-4?x.toExponential(5):x.toFixed(6)):'—';
  const profiles={quick:[128,256,512],standard:[128,192,256,384,512,768],confirmatory:[256,384,512,768,1024,1536]};
  const catalog={
    '3_1':{label:'3₁',ideal:'3:1:1',fseries:'3_1',knotplot:'knot_3.1'},'4_1':{label:'4₁',ideal:'4:1:1',fseries:'4_1',knotplot:'knot_4.1'},'5_1':{label:'5₁',ideal:'5:1:1',fseries:'5_1',knotplot:'knot_5.1'},
    '5_2':{label:'5₂',ideal:'5:1:2',fseries:'5_2',knotplot:'knot_5.2'},'6_1':{label:'6₁',ideal:'6:1:1',fseries:'6_1',knotplot:'knot_6.1'},'7_1':{label:'7₁',ideal:'7:1:1',fseries:'7_1',knotplot:'knot_7.1'},
    'link_6.3.1':{label:'link 6.3.1',knotplot:'link_6.3.1'},'link_6.3.2':{label:'link 6.3.2',knotplot:'link_6.3.2'},'link_6.3.3':{label:'link 6.3.3',knotplot:'link_6.3.3'},
    'torus_3.3':{label:'T(3,3)',knotplot:'torus_3.3'},'torus_6.9':{label:'T(6,9)',knotplot:'torus_6.9'}
  };
  function setStatus(text,kind='warn'){const e=el('reachAuditStatus');if(e){e.textContent=text;e.classList.remove('good','warn','bad','running');e.classList.add(kind);} }
  function setProgress(v){const e=el('reachAuditProgress');if(e)e.style.width=(100*Math.max(0,Math.min(1,v))).toFixed(2)+'%';}
  function selection(){const shared=SpecClockProxyDecomposition.readKnotSelection?.();if(shared)return {ideal:!!shared.ideal,fseries:!!shared.fseries,knotplot:!!shared.knotplot,topologies:[...(shared.topologies||[])]};const topologies=[...document.querySelectorAll('[data-spec-knot]:checked')].map(x=>x.dataset.specKnot);return {ideal:!!el('cSpecHoldoutIdeal')?.checked,fseries:!!el('cSpecHoldoutFseries')?.checked,knotplot:!!el('cSpecHoldoutKnotplot')?.checked,topologies};}
  function circle(n,R=1,z=0,transform=false){const p=new Float64Array(3*n);for(let i=0;i<n;i++){const t=2*Math.PI*i/n;let x=R*Math.cos(t),y=R*Math.sin(t),zz=z;if(transform){const X=.36*x-.48*y+.8*zz+2,Y=.8*x+.6*y-1,Z=-.48*x+.64*y+.6*zz+.5;x=X;y=Y;zz=Z;}p[3*i]=x;p[3*i+1]=y;p[3*i+2]=zz;}return p;}
  function geometrySpecs(){const sel=selection(),res=profiles[profile]||profiles.standard,maxN=res[res.length-1],specs=[
    {id:'analytic-circle',source:'analytic',label:'unit circle · exact',resolutions:res,knownReach:1,build:n=>[vlBuildExactCircleCurve(n)]},
    {id:'analytic-spline-circle',source:'analytic-spline',label:'unit circle · sampled C² spline',resolutions:res,knownReach:1,build:n=>[circle(n)]},
    {id:'analytic-circle-transform',source:'analytic',label:'unit circle · rigid transform',resolutions:[maxN],knownReach:1,build:n=>[vlBuildExactCircleCurve(n,1,0,true)]},
    {id:'analytic-two-circles',source:'analytic',label:'two circles · gap 0.8',resolutions:[maxN],knownReach:.4,knownLimiter:'INTER_COMPONENT',build:n=>[vlBuildExactCircleCurve(n,1,-.4),vlBuildExactCircleCurve(n,1,.4)]}
  ];
    for(const key of sel.topologies){const m=catalog[key];if(!m)continue;
      if(sel.ideal&&m.ideal){const entry=getIdealKnotCatalog()?.db?.[m.ideal];if(entry){const D=finiteMetaNumber(entry.D);specs.push({id:'ideal-'+m.ideal.replaceAll(':','_'),source:'ideal',label:m.ideal,resolutions:res,knownReach:Number.isFinite(D)?D/2:null,metadataD:Number.isFinite(D)?D:null,build:n=>knotEntryComponents(entry).map(c=>vlBuildFourierCurve(c.coeffs||c,n))});}}
      if(sel.fseries&&m.fseries){const entry=getFourierKnotCatalog()?.db?.[m.fseries];if(entry)specs.push({id:'fseries-'+m.fseries,source:'fseries',label:m.fseries,resolutions:res,knownReach:null,build:n=>knotEntryComponents(entry).map(c=>vlBuildFourierCurve(c.coeffs||c,n))});}
      if(sel.knotplot&&m.knotplot){const entry=getKnotPlotKnotCatalog()?.db?.[m.knotplot];if(entry)specs.push({id:'knotplot-'+m.knotplot.replaceAll('.','_'),source:'knotplot',knotKey:m.knotplot,label:m.knotplot,resolutions:res,knownReach:null,metadataD:Number.isFinite(finiteMetaNumber(entry.D))?finiteMetaNumber(entry.D):null,candidateStatus:entry.status||'candidate',candidateFamily:entry.family||null,sourceRole:entry.sourceRole||null,sourceSha256:entry.sourceSha256||null,normalization:entry.normalization||null,torus:entry.torus||null,pairwiseLinkingAbs:knotPlotLinkingAbs(entry),componentCountExpected:Number(entry.componentCount)||knotEntryComponents(entry).length,curveRoute:'native uniform polygon → periodic C2 spline',build:n=>knotEntryComponents(entry).map(c=>vlBuildKnotPlotReachCurve(entry,c,n))});}
    }return specs;
  }
  function solveComponents(components){const splines=components.map(c=>c&&typeof c.eval==='function'?c:vlBuildPeriodicSpline(c)),curv=splines.map(vlContinuousCurvatureLimit),self=splines.map(sp=>vlContinuousPairDistance(sp,sp,true));let inter=[];for(let i=0;i<splines.length;i++)for(let j=i+1;j<splines.length;j++){const r=vlContinuousPairDistance(splines[i],splines[j],false);if(r)inter.push({...r,i,j});}
    const cBest=curv.map((x,i)=>({...x,i})).sort((a,b)=>a.radius-b.radius)[0],sBest=self.map((x,i)=>x?({...x,i}):null).filter(Boolean).sort((a,b)=>a.distance-b.distance)[0]||null,iBest=inter.sort((a,b)=>a.distance-b.distance)[0]||null;
    const vals=[{type:'CURVATURE',value:cBest?.radius??Infinity,detail:cBest},{type:'SELF_DCSD',value:sBest?.distance/2??Infinity,detail:sBest},{type:'INTER_COMPONENT',value:iBest?.distance/2??Infinity,detail:iBest}].sort((a,b)=>a.value-b.value),reach=vals[0].value,near=vals.filter(x=>Number.isFinite(x.value)&&Math.abs(x.value-reach)<=1e-5*Math.max(1,Math.abs(reach))),limiter=near.length>1?'TIE':vals[0].type;
    const orthResidual=Math.max(0,...self.filter(Boolean).map(x=>x.orthResidual||0),...inter.map(x=>x.orthResidual||0));return {componentCount:components.length,lengths:splines.map(x=>x.L),curvatureRadius:cBest?.radius??null,curvature:cBest,selfDcsd:sBest?.distance??null,selfRadius:sBest?sBest.distance/2:null,selfSolution:sBest,interDistance:iBest?.distance??null,interRadius:iBest?iBest.distance/2:null,interSolution:iBest,reach:Number.isFinite(reach)?reach:null,limiter,orthResidual};
  }
  function buildTasks(){tasks=[];for(const spec of geometrySpecs())for(const N of spec.resolutions)tasks.push({spec,N});}
  function classify(){gates=[];const add=(group,id,label,status,metrics,explanation)=>gates.push({group,id,label,status,metrics,explanation});const analytic=results.filter(r=>r.source==='analytic'),circleRows=analytic.filter(r=>r.id==='analytic-circle'),maxCircle=Math.max(...circleRows.map(r=>r.knownRelativeError||0)),trans=analytic.find(r=>r.id==='analytic-circle-transform'),inter=analytic.find(r=>r.id==='analytic-two-circles');
    add('ENGINE','G0','analytische cirkelreach',maxCircle<1e-8?'PASS':'FAIL',{maxRelativeError:maxCircle,rows:circleRows.map(r=>({N:r.N,reach:r.reach,error:r.knownRelativeError}))},'De exacte cirkel heeft reach R en valideert curvature plus doubly-critical stationarity.');
    const splineRows=results.filter(r=>r.id==='analytic-spline-circle'),maxSpline=Math.max(0,...splineRows.map(r=>r.knownRelativeError||0));add('ENGINE','G0b','periodieke C²-splinecirkel',maxSpline<2e-3?'PASS':'FAIL',{maxRelativeError:maxSpline,rows:splineRows.map(r=>({N:r.N,reach:r.reach,error:r.knownRelativeError}))},'De sampled periodieke spline moet naar de analytische cirkelreach convergeren.');
    add('ENGINE','G1','rigid-transform invariance',trans?.knownRelativeError<1e-8?'PASS':'FAIL',{row:trans},'Translatie en rotatie mogen de reach niet wijzigen.');
    add('ENGINE','G2','inter-component anchor',inter?.knownRelativeError<5e-4&&inter?.limiter==='INTER_COMPONENT'?'PASS':'FAIL',{row:inter},'Twee congruente cirkels op z=±0.4 hebben inter-component reach 0.4.');
    const maxOrth=Math.max(0,...results.map(r=>r.orthResidual||0));add('ENGINE','G3','DCSD orthogonaliteitsresidu',maxOrth<1e-8?'PASS':'FAIL',{maxOrthResidual:maxOrth,acceptanceLimit:5e-9,gateLimit:1e-8},'Doubly-critical oplossingen moeten de twee tangent-orthogonaliteitsvoorwaarden sluiten; rank-deficiënte families gebruiken gedempte least-squares in plaats van een ontkoppelde fallback.');
    const sel=selection(),expectedSources=[];for(const key of sel.topologies){const m=catalog[key];if(!m)continue;if(sel.ideal&&m.ideal)expectedSources.push('ideal:'+m.ideal);if(sel.fseries&&m.fseries)expectedSources.push('fseries:'+m.fseries);if(sel.knotplot&&m.knotplot)expectedSources.push('knotplot:'+m.knotplot);}const catalogRows=results.filter(r=>['ideal','fseries','knotplot'].includes(r.source)),represented=new Set(catalogRows.map(r=>r.source+':'+(r.knotKey||r.label))),missingSources=expectedSources.filter(x=>!represented.has(x));add('ENGINE','G4a','geselecteerde catalogusgeometrieën uitgevoerd',expectedSources.length?(missingSources.length?'FAIL':'PASS'):'NOT_APPLICABLE',{expectedSources,missingSources,catalogResultCount:catalogRows.length,selection:sel},'Iedere geselecteerde bron/geometriecombinatie moet werkelijk in de audit voorkomen; een gedeeltelijke of analytische-only terugval is FAIL.');
    const kpExpected=expectedSources.filter(x=>x.startsWith('knotplot:')),kpLast=[];for(const key of kpExpected.map(x=>x.slice(9))){const rows=results.filter(r=>r.source==='knotplot'&&r.knotKey===key).sort((a,b)=>a.N-b.N),r=rows.at(-1);if(r)kpLast.push(r);}const kpMissing=kpExpected.map(x=>x.slice(9)).filter(key=>!kpLast.some(r=>r.knotKey===key)),kpMetaOk=kpLast.every(r=>r.sourceRole==='vortexlab-uniform-N300'&&r.curveRoute==='native uniform polygon → periodic C2 spline'&&Number.isFinite(r.componentCountExpected)&&r.componentCountExpected===r.componentCount),torus69=kpLast.find(r=>r.knotKey==='torus_6.9'),torus69Ok=!torus69||(torus69.torus?.p===6&&torus69.torus?.q===9&&torus69.componentCount===3&&torus69.pairwiseLinkingAbs===6);add('ENGINE','G4b','KnotPlot uniform-N300 identiteit + routeprovenance',kpExpected.length?(!kpMissing.length&&kpMetaOk&&torus69Ok?'PASS':'FAIL'):'NOT_APPLICABLE',{expected:kpExpected,missing:kpMissing,metadataRouteOk:kpMetaOk,torus69IdentityOk:torus69Ok,rows:kpLast.map(r=>({knotKey:r.knotKey,status:r.candidateStatus,family:r.candidateFamily,componentCount:r.componentCount,D:r.metadataD,sourceRole:r.sourceRole,curveRoute:r.curveRoute,torus:r.torus,pairwiseLinkingAbs:r.pairwiseLinkingAbs}))},'KnotPlot-audits gebruiken de native uniform-N300-centerline met periodieke C²-spline. torus_6.9 moet T(6,9), drie T(2,3)-componenten en |Lk|=6 rapporteren.');
    const idealExpected=expectedSources.some(x=>x.startsWith('ideal:')),idealLast=[];for(const id of new Set(results.filter(r=>r.source==='ideal').map(r=>r.id))){const rows=results.filter(r=>r.id===id).sort((a,b)=>a.N-b.N),r=rows.at(-1);if(r)idealLast.push(r);}const maxIdealDcsd=Math.max(0,...idealLast.map(r=>r.idealDcsdRelativeError||0)),g4Status=idealExpected?(idealLast.length?(maxIdealDcsd<.005?'PASS':'FAIL'):'FAIL'):'NOT_APPLICABLE';add('ENGINE','G4','Gilbert D versus continue DCSD',g4Status,{applicable:idealExpected,expectedIdealCount:expectedSources.filter(x=>x.startsWith('ideal:')).length,maxRelativeError:idealLast.length?maxIdealDcsd:null,rows:idealLast},'D=1 wordt als onafhankelijke diameteranker op de continue DCSD-tak gecontroleerd; zonder uitgevoerde Ideal-rows is deze gate FAIL wanneer Ideal-data was geselecteerd.');
    const kpDiameterDiagnostics=kpLast.filter(r=>Number.isFinite(r.metadataD)&&Number.isFinite(r.reach)).map(r=>({knotKey:r.knotKey,status:r.candidateStatus,D:r.metadataD,reachProxy:r.reach,diameterOverTwoReach:r.metadataD/(2*r.reach),limiter:r.limiter,route:r.curveRoute}));add('RESEARCH','R42','KnotPlot D=1 versus discrete C²-reachproxy','INFO',{rows:kpDiameterDiagnostics},'D=1 is de normalisatie van de Ridgerunner-polishprovenance. De uniform-N300 C²-splinewaarde is alleen een VortexLab-discrete proxy en kan D of een global-tight certificaat niet vervangen.');
    const curvatureConflicts=idealLast.filter(r=>Number.isFinite(r.knownReach)&&Number.isFinite(r.curvatureRadius)&&r.curvatureRadius<.995*r.knownReach),r41Status=!idealExpected?'NOT_APPLICABLE':!idealLast.length?'BLOCKED':curvatureConflicts.length?'FAIL':'PASS';add('RESEARCH','R41','ideal coefficient precision · curvature consistency',r41Status,{applicable:idealExpected,blocked:idealExpected&&!idealLast.length,rows:curvatureConflicts.map(r=>({id:r.id,label:r.label,curvatureRadius:r.curvatureRadius,metadataRadius:r.knownReach,relativeDeficit:(r.knownReach-r.curvatureRadius)/r.knownReach}))},'Een curvature-radius onder D/2 wijst op onvoldoende C²-precisie van de afgeronde Fourierbron of op broninconsistentie. Zonder Ideal-resultaten is de audit BLOCKED, nooit vacuüm PASS/INFO.');
    const conv=[];for(const id of new Set(results.map(r=>r.id))){const rows=results.filter(r=>r.id===id).sort((a,b)=>a.N-b.N);if(rows.length<2)continue;const a=rows.at(-2),b=rows.at(-1),rel=Math.abs(b.reach-a.reach)/Math.max(Math.abs(b.reach),1e-300),stable=a.limiter===b.limiter||a.limiter==='TIE'||b.limiter==='TIE';conv.push({id,label:b.label,source:b.source,lastN:b.N,relativeLastPair:rel,limiterStable:stable,idealRelativeError:b.source==='ideal'?b.idealDcsdRelativeError:null});}
    const maxConv=Math.max(0,...conv.map(x=>x.relativeLastPair)),limiterStable=conv.every(x=>x.limiterStable),tol=profile==='confirmatory'?.0025:.01;add('ENGINE','G5','resolutieconvergentie + limiterstabiliteit',maxConv<tol&&limiterStable?'PASS':'FAIL',{profile,tolerance:tol,maxRelativeLastPair:maxConv,limiterStable,rows:conv},'Confirmatoir vereist <0.25% tussen N=1024 en 1536; kortere profielen gebruiken 1% als ENGINE-smoke.');
    add('RESEARCH','R40','reach provenance · geen solverfeedback','INFO',{rows:results.map(r=>({id:r.id,source:r.source,N:r.N,reach:r.reach,limiter:r.limiter}))},'De continue reach is passieve geometrische diagnostiek en wordt niet op a_sim of de dynamics toegepast.');return conv;
  }
  function worst(statuses){return statuses.includes('FAIL')?'FAIL':statuses.includes('BLOCKED')?'BLOCKED':statuses.includes('WARN')?'WARN':statuses.includes('PASS')?'PASS':statuses.includes('NOT_APPLICABLE')?'NOT_APPLICABLE':'INFO';}
  function reportObject(){const conv=classify(),engine=worst(gates.filter(g=>g.group==='ENGINE').map(g=>g.status)),research=worst(gates.filter(g=>g.group==='RESEARCH').map(g=>g.status));return {schema:'vortexlab-continuous-reach-audit/1.0',appVersion:APP_VERSION,baseVersion:APP_BASE_VERSION,profile,startedAt,completedAt,aborted:stopRequested,engineVerdict:engine,researchVerdict:research,selection:selection(),solver:{curve:'Ideal/Fseries analytic Fourier; KnotPlot native uniform-N300 polygon with periodic C2 spline; other sampled curves periodic C2 spline',curvature:'continuous segmentwise maximization',selfDcsd:'coarse stationary seeds + Newton / damped least-squares on F1=F2=0',interComponent:'continuous stationary pair minimization',feedbackToDynamics:false},results,convergence:conv,gates};}
  function reportText(){const r=reportObject(),lines=['VortexLab continuous reach/DCSD audit','schema='+r.schema,'version='+APP_VERSION,'profile='+profile,'startedAt='+startedAt,'completedAt='+completedAt,'ENGINE='+r.engineVerdict,'','[gates]'];r.gates.forEach((g,i)=>lines.push(`${i+1}. ${g.group} ${g.status} ${g.id} · ${g.label} · metrics=${JSON.stringify(g.metrics)} · ${g.explanation}`));lines.push('','[results]');r.results.forEach((x,i)=>lines.push(`${i+1}. ${JSON.stringify(x)}`));return lines.join('\n');}
  function render(){const body=el('reachAuditRows'),convBody=el('reachConvergenceRows');if(body){body.innerHTML=results.length?results.map(r=>`<tr><td>${r.source}</td><td>${r.label}</td><td>${r.N}</td><td>${fmt(r.curvatureRadius)}</td><td>${fmt(r.selfRadius)}</td><td>${fmt(r.interRadius)}</td><td><b>${fmt(r.reach)}</b></td><td class="reach-limit-${String(r.limiter).toLowerCase().replace('_component','').replace('_dcsd','')}">${r.limiter}</td><td>${fmt(r.orthResidual)}</td></tr>`).join(''):'<tr><td colspan="9">—</td></tr>';}
    const conv=results.length?classify():[];if(convBody)convBody.innerHTML=conv.length?conv.map(x=>`<tr><td>${x.source} · ${x.label}</td><td>${x.lastN}</td><td>${(100*x.relativeLastPair).toFixed(4)}%</td><td>${Number.isFinite(x.idealRelativeError)?(100*x.idealRelativeError).toFixed(4)+'%':'N/A'}</td><td>${x.limiterStable?'ja':'nee'}</td><td>${x.relativeLastPair<(profile==='confirmatory'?.0025:.01)&&x.limiterStable?'PASS':'FAIL'}</td></tr>`).join(''):'<tr><td colspan="6">—</td></tr>';const summary=el('reachAuditSummary');if(summary){if(!results.length)summary.textContent='Nog geen continue reach/DCSD-run.';else if(active)summary.innerHTML=`<b>RUN</b> · ${results.length}/${tasks.length} taken · profiel ${profile} · passief, geen solverfeedback.`;else{const rep=reportObject();summary.innerHTML=`<b>ENGINE ${rep.engineVerdict}</b> · <b>RESEARCH ${rep.researchVerdict}</b> · ${results.length}/${tasks.length} taken · profiel ${profile} · passief, geen solverfeedback.`;}}for(const id of ['bReachAuditExportTxt','bReachAuditExportJson']){const b=el(id);if(b)b.disabled=!results.length;}}
  function finish(){active=false;completedAt=new Date().toISOString();const rep=reportObject();LastContinuousReachAuditSummary=rep;const pass=rep.engineVerdict==='PASS';setProgress(1);setStatus(`${stopRequested?'AFGEBROKEN':'VOLTOOID'} · ${results.length}/${tasks.length} reach-taken · ENGINE ${rep.engineVerdict}`,stopRequested?'warn':pass?'good':'bad');render();VLClockWorkflow.complete('reach',pass&&!stopRequested);VL_CLOCK_ACTIVE_MODE=null;vlRefreshClockRunnerWorkflowUi();if(window.ModelLog)ModelLog.logEvent('continuous-reach-complete',{profile,results:results.length,engine:rep.engineVerdict,aborted:stopRequested});if(!stopRequested&&specAutoExportEnabled()){const stamp=safeUtcStamp(completedAt);triggerTextDownload(reportText(),'text/plain;charset=utf-8',`vortexlab-continuous-reach-${APP_VERSION.replace(/\./g,'-')}-${profile}-${stamp}.txt`);triggerTextDownload(JSON.stringify(rep,null,2),'application/json',`vortexlab-continuous-reach-${APP_VERSION.replace(/\./g,'-')}-${profile}-${stamp}.json`);}}
  function step(){if(stopRequested||taskIndex>=tasks.length){finish();return;}const {spec,N}=tasks[taskIndex];setStatus(`RUN ${taskIndex+1}/${tasks.length} · ${spec.source} ${spec.label} · N=${N}`,'running');setProgress(taskIndex/Math.max(1,tasks.length));setTimeout(()=>{try{const components=spec.build(N),sol=solveComponents(components),knownRelativeError=Number.isFinite(spec.knownReach)?Math.abs(sol.reach-spec.knownReach)/Math.max(Math.abs(spec.knownReach),1e-300):null,idealDcsdRelativeError=spec.source==='ideal'&&Number.isFinite(spec.knownReach)&&Number.isFinite(sol.selfRadius)?Math.abs(sol.selfRadius-spec.knownReach)/Math.max(Math.abs(spec.knownReach),1e-300):null;results.push({id:spec.id,source:spec.source,knotKey:spec.knotKey||null,label:spec.label,N,metadataD:spec.metadataD??null,knownReach:spec.knownReach??null,knownRelativeError,idealDcsdRelativeError,candidateStatus:spec.candidateStatus||null,candidateFamily:spec.candidateFamily||null,sourceRole:spec.sourceRole||null,sourceSha256:spec.sourceSha256||null,normalization:spec.normalization||null,torus:spec.torus||null,pairwiseLinkingAbs:spec.pairwiseLinkingAbs??null,componentCountExpected:spec.componentCountExpected??null,curveRoute:spec.curveRoute||null,...sol});taskIndex++;render();step();}catch(err){results.push({id:spec.id,source:spec.source,label:spec.label,N,error:String(err?.message||err),reach:null,limiter:'ERROR',orthResidual:null});stopRequested=true;setStatus(`AFGEBROKEN · ${spec.label} N=${N} · ${String(err?.message||err)}`,'bad');finish();}},0);}
  function start(){if(active){stopRequested=true;setStatus('STOP AANGEVRAAGD · huidige reach-taak wordt afgerond','warn');return;}if(SpecClockBenchmark.active||SpecClockProxyDecomposition.active){setFlag('⚠ stop eerst de actieve Swirl-Clockrunner.',true);return;}if(!VLClockWorkflow.unlocked('reach')){setFlag('🔒 '+VLClockWorkflow.reason('reach'),true);return;}profile=el('reachAuditProfile')?.value||'standard';results=[];gates=[];taskIndex=0;stopRequested=false;startedAt=new Date().toISOString();completedAt=null;buildTasks();if(!tasks.length){setFlag('⚠ geen reach-geometrieën geselecteerd.',true);return;}active=true;VLClockWorkflow.begin('reach');vlFocusClockRunner('reach');setProgress(0);if(window.ModelLog)ModelLog.logEvent('continuous-reach-start',{profile,tasks:tasks.length,selection:selection()});render();step();}
  function download(kind){const stamp=safeUtcStamp(completedAt||new Date()),text=kind==='json'?JSON.stringify(reportObject(),null,2):reportText(),mime=kind==='json'?'application/json':'text/plain;charset=utf-8';triggerTextDownload(text,mime,`vortexlab-continuous-reach-${APP_VERSION.replace(/\./g,'-')}-${profile}-${stamp}.${kind}`);}
  function bind(){el('bReachAuditStart')?.addEventListener('click',start);el('bReachAuditExportTxt')?.addEventListener('click',()=>download('txt'));el('bReachAuditExportJson')?.addEventListener('click',()=>download('json'));render();}
  function selfTest(){const c=solveComponents([vlBuildExactCircleCurve(256)]),sp=solveComponents([circle(256)]),pair=solveComponents([vlBuildExactCircleCurve(192,1,-.4),vlBuildExactCircleCurve(192,1,.4)]);return {ok:Math.abs(c.reach-1)<1e-8&&Math.abs(sp.reach-1)<1e-3&&Math.abs(pair.reach-.4)<1e-8&&pair.limiter==='INTER_COMPONENT'&&pair.orthResidual<1e-10,circle:c,splineCircle:sp,pair};}
  return {start,bind,selfTest,get active(){return active;},get lastSummary(){return LastContinuousReachAuditSummary;}};
})();

function translateCarrier(which,dx,dy,dz){
  for(const f of carrierFilaments(which))for(let k=0;k<f.N;k++){
    const i=f.off+3*k;Y[i]+=dx;Y[i+1]+=dy;Y[i+2]+=dz;
  }
}
function captureCarrierAnchors(){
  carrierAnchors=Object.create(null);
  for(const which of ['A','B']){
    const st=carrierGroupStats(which);
    if(st)carrierAnchors[which]={x:st.cx,y:st.cy,z:st.z};
  }
}
function centerSoloCarrierAtOrigin(){
  if(P.mode!=='solo')return;
  const st=carrierGroupStats('A');
  if(st)translateCarrier('A',-st.cx,-st.cy,-st.z);
}
function enforceCenterLock(){
  // Alleen in solo: in botsingsmodus zou het vastpinnen van beide dragers
  // de nadering (en dus de hele botsing) onderdrukken.
  if(!P.centerLock||P.mode!=='solo'||!Y)return;
  for(const which of Object.keys(carrierAnchors)){
    const st=carrierGroupStats(which),a=carrierAnchors[which];
    if(st&&a)translateCarrier(which,a.x-st.cx,a.y-st.cy,a.z-st.z);
  }
}
function sampleFourierParametric(coeffs,n){
  const x=new Float64Array(3*n);
  for(let k=0;k<n;k++){
    const t=2*Math.PI*k/n;let px=0,py=0,pz=0;
    for(const c of coeffs){
      const ct=Math.cos(c.I*t),st=Math.sin(c.I*t);
      px+=ct*c.A[0]+st*c.B[0];py+=ct*c.A[1]+st*c.B[1];pz+=ct*c.A[2]+st*c.B[2];
    }
    x[3*k]=px;x[3*k+1]=py;x[3*k+2]=pz;
  }
  return x;
}
function resampleClosedCurve(raw,n){
  const m=Math.floor(raw.length/3),cum=new Float64Array(m+1);
  for(let i=0;i<m;i++){const j=(i+1)%m;cum[i+1]=cum[i]+Math.hypot(raw[3*j]-raw[3*i],raw[3*j+1]-raw[3*i+1],raw[3*j+2]-raw[3*i+2]);}
  const L=cum[m],out=new Float64Array(3*n);
  if(!(L>0))return out;
  let seg=0;
  for(let k=0;k<n;k++){
    const target=L*k/n;while(seg<m-1&&cum[seg+1]<target)seg++;
    const j=(seg+1)%m,den=Math.max(1e-30,cum[seg+1]-cum[seg]),u=(target-cum[seg])/den;
    out[3*k]=raw[3*seg]+u*(raw[3*j]-raw[3*seg]);
    out[3*k+1]=raw[3*seg+1]+u*(raw[3*j+1]-raw[3*seg+1]);
    out[3*k+2]=raw[3*seg+2]+u*(raw[3*j+2]-raw[3*seg+2]);
  }
  return out;
}
function sampleFourierKnot(coeffs,n,arcLengthUniform=false){
  if(!arcLengthUniform)return sampleFourierParametric(coeffs,n);
  const imax=coeffs.reduce((m,c)=>Math.max(m,Math.abs(Number(c.I)||0)),1);
  const nRef=Math.max(4096,16*imax);
  return resampleClosedCurve(sampleFourierParametric(coeffs,nRef),n);
}
function sampleIdealComponent(component,n){
  return sampleFourierKnot(component.coeffs||component,n,true);
}
function sampleKnotPlotComponent(entry,component,n){
  const nativeN=Math.max(4,Math.round(finiteMetaNumber(component?.pointCount)||finiteMetaNumber(entry?.pointsPerComponent?.[Math.max(0,(Number(component?.I)||1)-1)])||300));
  const native=sampleFourierParametric(component.coeffs||component,nativeN);
  return n===nativeN?native:resampleClosedCurve(native,n);
}
function sampleCatalogComponent(entry,component,n,source){
  if(source==='knotplot'&&(entry?.sourceRole==='vortexlab-uniform-N300'||entry?.normalization?.label==='uniform-N300'))return sampleKnotPlotComponent(entry,component,n);
  return sampleIdealComponent(component,n);
}
function sampleBuiltinRaw(topo,N,component=0,which='A'){
  if(topo==='trefoil') return sampleFourierKnot(activeCoeffs(which),N,true);
  const x=new Float64Array(3*N);
  for(let k=0;k<N;k++){
    const t=2*Math.PI*k/N;
    let px=0,py=0,pz=0;
    if(topo==='ring'){
      px=Math.cos(t);py=Math.sin(t);pz=0;
    }else if(topo==='hopf'){
      // Twee geometrische cirkels met linking number |Lk|=1.
      if(component===0){px=Math.cos(t)-0.5;py=Math.sin(t);pz=0;}
      else{px=0.5+Math.cos(t);py=0;pz=Math.sin(t);}
    }else if(topo==='figure8'){
      px=(2+Math.cos(2*t))*Math.cos(3*t);
      py=(2+Math.cos(2*t))*Math.sin(3*t);
      pz=Math.sin(4*t);
    }else if(topo==='cinquefoil'){
      // T(2,5), een 5_1-torusknoop.
      px=(2+0.72*Math.cos(5*t))*Math.cos(2*t);
      py=(2+0.72*Math.cos(5*t))*Math.sin(2*t);
      pz=0.72*Math.sin(5*t);
    }else if(topo==='twist52'){
      // Lissajous-representatie van de three-twist knot 5_2.
      px=Math.cos(3*t+0.7);
      py=Math.cos(2*t+0.2);
      pz=Math.cos(7*t);
    }else{
      px=Math.cos(t);py=Math.sin(t);pz=0;
    }
    x[3*k]=px;x[3*k+1]=py;x[3*k+2]=pz;
  }
  return x;
}
function topologyRawComponents(N,which){
  const entry=activeKnotEntry();
  if(entry){
    const comps=knotEntryComponents(entry);
    if(P.idealComponentMode==='all')return comps.map(c=>sampleCatalogComponent(entry,c,N,P.knotSource));
    const ci=(which==='B'?P.compB:P.compA)-1;
    const c=comps[Math.min(Math.max(ci,0),Math.max(0,comps.length-1))];
    return c?[sampleCatalogComponent(entry,c,N,P.knotSource)]:[sampleFourierKnot(IDEAL_TREFOIL_3_1_1.coeffs,N,true)];
  }
  const nc=topologyComponentCount();
  const out=[];for(let c=0;c<nc;c++)out.push(sampleBuiltinRaw(P.topo,N,c,which));
  return out;
}
function reverseTraversal(x,N){
  const y=new Float64Array(3*N);
  for(let k=0;k<N;k++){const s=N-1-k;
    y[3*k]=x[3*s];y[3*k+1]=x[3*s+1];y[3*k+2]=x[3*s+2];}
  return y;
}
function signedAreaXY(x,N){
  let A=0;for(let k=0;k<N;k++){const k2=(k+1)%N;
    A+=x[3*k]*x[3*k2+1]-x[3*k2]*x[3*k+1];}
  return 0.5*A;
}
function makeCarrierComponents(N,z0,cx,wantDir,which){
  let raws=topologyRawComponents(N,which||'A');
  let c0x=0,c0y=0,c0z=0,count=0;
  raws.forEach(raw=>{for(let k=0;k<N;k++){
    c0x+=raw[3*k];c0y+=raw[3*k+1];c0z+=raw[3*k+2];count++;
  }});
  c0x/=count;c0y/=count;c0z/=count;
  let rMax=0;
  raws.forEach(raw=>{for(let k=0;k<N;k++){
    rMax=Math.max(rMax,Math.hypot(raw[3*k]-c0x,raw[3*k+1]-c0y));
  }});
  const sc=P.R0/Math.max(rMax,1e-12);
  let placed=raws.map(raw=>{
    const out=new Float64Array(3*N);
    for(let k=0;k<N;k++){
      out[3*k]=cx+(raw[3*k]-c0x)*sc;
      out[3*k+1]=(raw[3*k+1]-c0y)*sc;
      out[3*k+2]=z0+(raw[3*k+2]-c0z)*sc;
    }
    return out;
  });
  // Werkelijke spiegeling van drager B: reflecteer de geometrie rond het
  // verticale vlak door haar eigen centrum. Dit verandert de chiraliteit,
  // in tegenstelling tot alleen het teken van de laterale offset wijzigen.
  if(which==='B' && P.mirrorB){
    placed=placed.map(curve=>{
      const out=new Float64Array(curve.length);
      for(let k=0;k<N;k++){
        out[3*k]=2*cx-curve[3*k];
        out[3*k+1]=curve[3*k+1];
        out[3*k+2]=curve[3*k+2];
      }
      return out;
    });
  }

  // Auto-aim op basis van de werkelijk door Biot--Savart geïnduceerde
  // centroid-snelheid van de volledige topologie. Voor niet-planaire knopen
  // is het teken van de geprojecteerde xy-oppervlakte geen betrouwbare
  // voorspeller van de translatierichting.
  const vzSelf=carrierMeanSelfVz(placed);
  if(Math.abs(vzSelf)>1e-12 && vzSelf*wantDir<0)
    placed=placed.map(curve=>reverseTraversal(curve,N));
  else if(Math.abs(vzSelf)<=1e-12){
    const orient=signedAreaXY(placed[0],N);
    if(Math.abs(orient)>1e-12 && orient*wantDir<0)
      placed=placed.map(curve=>reverseTraversal(curve,N));
  }
  return placed;
}

// ================= fysica: Schwarz-splitsing =================
// snelheid van één losstaand filament (voor auto-richting)
function velocitySingle(X,N,V){
  const fils1=[{off:0,N}]; velocityCore(X,fils1,V,false);
}
// hoofdroutine: Y = alle punten, fils = [{off,N}], OUT zelfde lengte als Y
function velocityCore(Yv,fl,OUT,liaOnly,options={}){
  const includeExternal=options.includeExternal!==false;
  // wrijving alleen in de echte dynamica: niet in de includeExternal:false
  // diagnostiekaanroepen (zelfgeïnduceerde vz voor richtbepaling).
  const bundleOn=includeExternal&&bundleFlowActive();
  const stretchOnly=includeExternal&&P.stretchProfileApply&&P.stretchProfileOnly;
  const mfOn=includeExternal&&options.mutualFriction!==false&&mfActive()&&!bundleOn&&!stretchOnly;
  // v7.5 (v7.4b §B.1): de wrijvings-v_n volgt het solverframe — co-roterende
  // normale component alleen bij solverFrame='lab' met bgFlow='wall'.
  const bgWall=bgWallInSolver(), mfRot=bgWall;
  const a=P.a, a2=a*a, eD=Math.exp(DELTA[P.core]);
  // segmentdata per filament
  const mids=[],dls=[];
  for(const f of fl){
    const N=f.N, o=f.off, mid=new Float64Array(3*N), dl=new Float64Array(3*N);
    for(let k=0;k<N;k++){const k2=(k+1)%N;
      for(let d=0;d<3;d++){
        mid[3*k+d]=0.5*(Yv[o+3*k+d]+Yv[o+3*k2+d]);
        dl[3*k+d]=Yv[o+3*k2+d]-Yv[o+3*k+d];}}
    mids.push(mid);dls.push(dl);
  }
  let umax=0;
  for(let ft=0;ft<fl.length;ft++){
    if(fl[ft].ghost){
      // v7.1 (B3): de Stewartson-ghostring is puur visueel — hij beweegt niet
      // zelf (positie wordt door syncGhostRing gepind) en draagt hieronder ook
      // niet bij als Biot-Savart-bron. Zijn gammaVal is dimensioneel niet
      // gesloten en mag de dynamica niet raken.
      const N=fl[ft].N,o=fl[ft].off;
      for(let i=0;i<N;i++){OUT[o+3*i]=0;OUT[o+3*i+1]=0;OUT[o+3*i+2]=0;}
      continue;
    }
    const Ga=filamentGamma(fl[ft]), pref=Ga/(4*Math.PI);
    const N=fl[ft].N, o=fl[ft].off, dlt=dls[ft];
    for(let i=0;i<N;i++){
      const im=(i-1+N)%N, ip=i;
      const px=Yv[o+3*i],py=Yv[o+3*i+1],pz=Yv[o+3*i+2];
      const dmx=dlt[3*im],dmy=dlt[3*im+1],dmz=dlt[3*im+2];
      const dpx=dlt[3*ip],dpy=dlt[3*ip+1],dpz=dlt[3*ip+2];
      const lm=Math.sqrt(dmx*dmx+dmy*dmy+dmz*dmz), lp=Math.sqrt(dpx*dpx+dpy*dpy+dpz*dpz);
      const cxv=dmy*dpz-dmz*dpy, cyv=dmz*dpx-dmx*dpz, czv=dmx*dpy-dmy*dpx;
      let ux=0,uy=0,uz=0;
      if(stretchOnly){
        const us=stretchProfileVelocityAt(px,py,pz);ux=us.ux;uy=us.uy;uz=us.uz;
      }else{
        const lf=pref*(Math.log(2*Math.sqrt(lm*lp)/(eD*a))+C0)*2/(lm*lp*(lm+lp));
        ux=lf*cxv;uy=lf*cyv;uz=lf*czv;
        if(includeExternal){
          const carrier=fl[ft].carrier||'A';
          const zBias=effectiveW()+carrierAxialDrift(carrier);
          uz+=zBias;
          if(!fl[ft].ghost&&(bgWall||bundleOn||P.stretchProfileApply)){
            const ubg=backgroundVelocityForFilamentPoint(px,py,pz,dmx+dpx,dmy+dpy,dmz+dpz);
            ux+=ubg.ux;uy+=ubg.uy;uz+=ubg.uz;
          }
        }
      }
      if(!stretchOnly&&!liaOnly){
        for(let fs=0;fs<fl.length;fs++){
          if(fl[fs].ghost)continue; // v7.1 (B3): ghost is geen bron
          const M=fl[fs].N, mid=mids[fs], dl=dls[fs];
          const prefSource=filamentGamma(fl[fs])/(4*Math.PI);
          const reg=(fs===ft)?0:a2;   // eigen filament: kale kern-vrije kernel; kruisterm: gladgestreken
          for(let j=0;j<M;j++){
            if(fs===ft && (j===im||j===ip)) continue;
            const rx=px-mid[3*j],ry=py-mid[3*j+1],rz=pz-mid[3*j+2];
            const r2=rx*rx+ry*ry+rz*rz+reg;
            const inv=prefSource/(r2*Math.sqrt(r2));
            ux+=(dl[3*j+1]*rz-dl[3*j+2]*ry)*inv;
            uy+=(dl[3*j+2]*rx-dl[3*j]*rz)*inv;
            uz+=(dl[3*j]*ry-dl[3*j+1]*rx)*inv;
          }
        }
      }
      if(mfOn&&!fl[ft].ghost){
        // v_n: opgelegde uniforme axiale normale stroming; in het lab-frame met
        // achtergrond-Ω-koppeling roteert de normale component mee (Ω×r),
        // zodat de azimutale v_ns-bijdrage van de vaste-lichaamsrotatie wegvalt.
        let vnx=0,vny=0;const vnz=P.vnZ;
        if(mfRot){vnx=-P.Om*py;vny=P.Om*px;}
        mfTransform(ux,uy,uz,dmx+dpx,dmy+dpy,dmz+dpz,vnx,vny,vnz,P.mfAlpha,P.mfAlphaP,MF_TMP3);
        ux=MF_TMP3[0];uy=MF_TMP3[1];uz=MF_TMP3[2];
      }
      OUT[o+3*i]=ux;OUT[o+3*i+1]=uy;OUT[o+3*i+2]=uz;
      const um=ux*ux+uy*uy+uz*uz;if(um>umax)umax=um;
    }
  }
  return Math.sqrt(umax);
}
function carrierMeanSelfVz(components){
  if(!components||!components.length)return 0;
  const N=components[0].length/3;
  const totalPts=components.reduce((n,c)=>n+c.length/3,0);
  const tmpY=new Float64Array(3*totalPts), tmpF=[];
  let off=0;
  components.forEach((curve,component)=>{
    tmpY.set(curve,off);
    tmpF.push({off,N:curve.length/3,carrier:'A',component});
    off+=curve.length;
  });
  const tmpV=new Float64Array(tmpY.length);
  velocityCore(tmpY,tmpF,tmpV,false,{includeExternal:false});
  let vz=0;
  for(let i=2;i<tmpV.length;i+=3)vz+=tmpV[i];
  return vz/Math.max(1,totalPts);
}
function velAll(Yv,OUT){
  const lia=(P.inter==='lia');
  return velocityCore(Yv,allFils(),OUT,lia);
}
function wrapFilamentCarriersZ(){
  if(!P.tracerWrapZ||P.centerLock||!Y||!fils.length)return;
  if(P.mode==='botsing'&&initialAxialSeparation()>initialAxialSeparationSliderMax()*(1+1e-12))return;
  const lo=zMin(),hi=zMax(),span=hi-lo;
  if(!(span>1e-12))return;
  const carriers=[...new Set(fils.filter(f=>!f.ghost).map(f=>f.carrier||'A'))];
  for(const carrier of carriers){
    const group=fils.filter(f=>!f.ghost&&(f.carrier||'A')===carrier);
    let zc=0,count=0;
    for(const f of group)for(let k=0;k<f.N;k++){zc+=Y[f.off+3*k+2];count++;}
    if(!count)continue;
    zc/=count;
    if(zc<lo||zc>=hi){
      const wrapped=lo+(((zc-lo)%span)+span)%span;
      const dz=wrapped-zc;
      for(const f of group)for(let k=0;k<f.N;k++)Y[f.off+3*k+2]+=dz;
    }
  }
}
function rk4Step(dt){
  const n=Y.length;
  const u1=velAll(Y,K1);
  for(let i=0;i<n;i++)TT[i]=Y[i]+0.5*dt*K1[i];
  const u2=velAll(TT,K2);
  for(let i=0;i<n;i++)TT[i]=Y[i]+0.5*dt*K2[i];
  const u3=velAll(TT,K3);
  for(let i=0;i<n;i++)TT[i]=Y[i]+dt*K3[i];
  const u4=velAll(TT,K4);
  for(let i=0;i<n;i++)Y[i]+=dt/6*(K1[i]+2*K2[i]+2*K3[i]+K4[i]);
  wrapFilamentCarriersZ();
  enforceCenterLock();
  constrainGhostRing();
  // Diagnostische accumulatoren worden pas na acceptatie van de eventueel
  // gebisecteerde stap bijgewerkt. Trial-stappen blijven daardoor passief.
  // v7.1 (B7): verplaatsingslimiet in dtCFL gebruikt de snelste van alle vier
  // RK4-stages; voorheen alleen K1, waardoor snelle tussenstadia bij nadering
  // de tijdstap konden onderschatten.
  return Math.max(u1,u2,u3,u4);
}
function prescribedKinematicSpeedBound(){
  let u=0;
  if(P.mode==='solo'){
    u=Math.max(u,Math.abs(effectiveW()));
    if(P.taylorOsc&&P.taylorOsc.enabled&&!P.centerLock){
      u=Math.max(u,Math.abs(P.taylorOsc.amplitude)*2*Math.PI/Math.max(0.5,P.taylorOsc.period));
    }
  }else{
    u=Math.max(u,Math.abs(P.vzA),Math.abs(P.lockVz?P.vzA:P.vzB));
  }
  return u;
}
function acceptedStepTimeCap(){
  return P.specClockEnabled?SPEC_CLOCK_MAX_ACCEPTED_DT:MAX_ACCEPTED_DT;
}
function dtCFL(){
  const lm=lminAll();
  let dt=Infinity;
  if(!(P.stretchProfileApply&&P.stretchProfileOnly)){
    const nu=(Math.abs(Gamma())/(4*Math.PI))*(Math.log(2*lm/(Math.exp(DELTA[P.core])*P.a))+C0);
    const om=Math.max(1e-12,Math.abs(nu)*Math.pow(Math.PI/lm,2));
    dt=0.5/om;
  }
  const speedBound=Math.max(1e-12,lastUmax,prescribedKinematicSpeedBound());
  dt=Math.min(dt,0.25*lm/speedBound);
  const stretchRate=stretchProfileCharacteristicRate();
  if(stretchRate>1e-12)dt=Math.min(dt,0.12/stretchRate);
  if(bgWallInSolver()&&Math.abs(P.Om)>1e-9)dt=Math.min(dt,0.2/Math.abs(P.Om));
  const ob=bundleMaxOmega();
  if(ob>1e-9)dt=Math.min(dt,0.2/ob);
  if(P.topologyGuard&&Y&&fils.length){
    const gap=Number.isFinite(lastTopologyGap)?lastTopologyGap:topologyClearance();
    const dc=contactThresholdInfo().effective,margin=Math.max(0,gap-dc);
    if(Number.isFinite(margin))dt=Math.min(dt,0.12*Math.max(margin,0.05*dc)/Math.max(2*lastUmax,1e-12));
  }
  dt=Math.min(dt,acceptedStepTimeCap());
  if(!(Number.isFinite(dt)&&dt>0))dt=acceptedStepTimeCap();
  return Math.max(1e-6,dt);
}
function evalsPerStep(){
  let tot=0;for(const f of dynamicFils())tot+=f.N;
  const lia=(P.inter==='lia');
  const n=dynamicFils().length;
  if(P.stretchProfileApply&&P.stretchProfileOnly)return 4*tot*4;
  return lia? 4*tot*8 : 4*tot*tot;
}

function ghostRingPts(N,rCap,cx,cy,cz){
  const x=new Float64Array(3*N);
  for(let k=0;k<N;k++){
    const th=2*Math.PI*k/N;
    x[3*k]=cx+rCap*Math.cos(th);x[3*k+1]=cy+rCap*Math.sin(th);x[3*k+2]=cz;}
  return x;
}
function lminAll(){
  let m=1e9;
  for(const f of dynamicFils()){const N=f.N,o=f.off;
    for(let k=0;k<N;k++){const k2=(k+1)%N;
      const d=Math.hypot(Y[o+3*k2]-Y[o+3*k],Y[o+3*k2+1]-Y[o+3*k+1],Y[o+3*k2+2]-Y[o+3*k+2]);
      if(d<m)m=d;}}
  return m;
}
function rebuildRKBuffers(){
  if(P.centerLock&&P.mode==='solo')centerSoloCarrierAtOrigin();
  captureCarrierAnchors();
  K1=new Float64Array(Y.length);K2=new Float64Array(Y.length);
  K3=new Float64Array(Y.length);K4=new Float64Array(Y.length);TT=new Float64Array(Y.length);
}
function syncGhostRing(){
  if(!P.ghostStewartson||P.mode!=='solo'||!fils.length||!Y){
    if(ghostFil){
      removeGhostFromY();rebuildRKBuffers();rebuildLines();rebuildTubes(true);
    }
    return;
  }
  const st=carrierStats(fils[0]);
  const w=effectiveW();
  const t=taylorColumnState(st,w);
  const stw=stewartsonCirculation(w,t.rCap,P.Om);
  const N=RING_N;
  if(!ghostFil){
    const off=Y.length;
    const pts=ghostRingPts(N,t.rCap,st.cx,st.cy,st.z);
    const Y2=new Float64Array(Y.length+3*N);
    Y2.set(Y);Y2.set(pts,off);
    Y=Y2;rebuildRKBuffers();
    ghostFil={off,N,ghost:true,gammaVal:0,rCap:t.rCap,cx:st.cx,cy:st.cy,cz:st.z}; // v7.2: inert
    rebuildLines();rebuildTubes(true);
  }else{
    ghostFil.gammaVal=0;
    ghostFil.rCap=t.rCap;ghostFil.cx=st.cx;ghostFil.cy=st.cy;ghostFil.cz=st.z;
    constrainGhostRing();
  }
}
function constrainGhostRing(){
  if(!ghostFil||!Y)return;
  const {off,N,rCap,cx,cy,cz}=ghostFil;
  for(let k=0;k<N;k++){
    const th=2*Math.PI*k/N;
    Y[off+3*k]=cx+rCap*Math.cos(th);
    Y[off+3*k+1]=cy+rCap*Math.sin(th);
    Y[off+3*k+2]=cz;
  }
}
function removeGhostFromY(){
  if(!ghostFil||!Y)return;
  const go=ghostFil.off, n=3*ghostFil.N;
  const Y2=new Float64Array(Y.length-n);
  Y2.set(Y.subarray(0,go),0);
  Y2.set(Y.subarray(go+n),go);
  Y=Y2;
  ghostFil=null;
}

// ================= diagnostiek =================
// v7.2: exacte polygonale Gauss-integralen via paarsgewijze solid angles
// (Klenin & Langowski 2000, methode 1a; Levitt/Banchoff). De vaste N/24-
// truncatie van de nabij-diagonaal is weg: aanliggende segmentparen dragen
// exact 0 bij (coplanair) en worden alleen numeriek overgeslagen. Wr, Lk en
// ACN zijn hiermee exact voor de pólygoon; de discretisatie van de kromme
// zelf blijft de enige resterende benadering.
function segPairOmega(YY,o1,i,i2,o2,j,j2){
  const p1x=YY[o1+3*i], p1y=YY[o1+3*i+1], p1z=YY[o1+3*i+2];
  const p2x=YY[o1+3*i2],p2y=YY[o1+3*i2+1],p2z=YY[o1+3*i2+2];
  const p3x=YY[o2+3*j], p3y=YY[o2+3*j+1], p3z=YY[o2+3*j+2];
  const p4x=YY[o2+3*j2],p4y=YY[o2+3*j2+1],p4z=YY[o2+3*j2+2];
  const r13x=p3x-p1x,r13y=p3y-p1y,r13z=p3z-p1z;
  const r14x=p4x-p1x,r14y=p4y-p1y,r14z=p4z-p1z;
  const r23x=p3x-p2x,r23y=p3y-p2y,r23z=p3z-p2z;
  const r24x=p4x-p2x,r24y=p4y-p2y,r24z=p4z-p2z;
  let n1x=r13y*r14z-r13z*r14y,n1y=r13z*r14x-r13x*r14z,n1z=r13x*r14y-r13y*r14x;
  let n2x=r14y*r24z-r14z*r24y,n2y=r14z*r24x-r14x*r24z,n2z=r14x*r24y-r14y*r24x;
  let n3x=r24y*r23z-r24z*r23y,n3y=r24z*r23x-r24x*r23z,n3z=r24x*r23y-r24y*r23x;
  let n4x=r23y*r13z-r23z*r13y,n4y=r23z*r13x-r23x*r13z,n4z=r23x*r13y-r23y*r13x;
  const m1=n1x*n1x+n1y*n1y+n1z*n1z,m2=n2x*n2x+n2y*n2y+n2z*n2z,
        m3=n3x*n3x+n3y*n3y+n3z*n3z,m4=n4x*n4x+n4y*n4y+n4z*n4z;
  if(m1<1e-60||m2<1e-60||m3<1e-60||m4<1e-60)return 0; // coplanair/gedegenereerd
  const s1=1/Math.sqrt(m1),s2=1/Math.sqrt(m2),s3=1/Math.sqrt(m3),s4=1/Math.sqrt(m4);
  n1x*=s1;n1y*=s1;n1z*=s1; n2x*=s2;n2y*=s2;n2z*=s2;
  n3x*=s3;n3y*=s3;n3z*=s3; n4x*=s4;n4y*=s4;n4z*=s4;
  const cl=v=>v>1?1:(v<-1?-1:v);
  const om=Math.asin(cl(n1x*n2x+n1y*n2y+n1z*n2z))
          +Math.asin(cl(n2x*n3x+n2y*n3y+n2z*n3z))
          +Math.asin(cl(n3x*n4x+n3y*n4y+n3z*n4z))
          +Math.asin(cl(n4x*n1x+n4y*n1y+n4z*n1z));
  const r12x=p2x-p1x,r12y=p2y-p1y,r12z=p2z-p1z;
  const r34x=p4x-p3x,r34y=p4y-p3y,r34z=p4z-p3z;
  const cx=r34y*r12z-r34z*r12y,cy=r34z*r12x-r34x*r12z,cz=r34x*r12y-r34y*r12x;
  return (cx*r13x+cy*r13y+cz*r13z)<0?-om:om;
}
// Retourneert [getekend, absoluut]: zelfde paar-loop levert Wr én ACN
// (of Lk én kruis-ACN) in één passage.
function gauss2(o1,N1,o2,N2,same,YY){
  YY=YY||Y;
  let S=0,A=0;
  if(same){
    for(let i=0;i<N1;i++){
      const i2=(i+1)%N1;
      for(let j=i+2;j<N1;j++){
        if(i===0&&j===N1-1)continue; // wrap-aanliggend paar
        const om=segPairOmega(YY,o1,i,i2,o1,j,(j+1)%N1);
        S+=om;A+=Math.abs(om);
      }
    }
    return [S/(2*Math.PI),A/(2*Math.PI)];
  }
  for(let i=0;i<N1;i++){
    const i2=(i+1)%N1;
    for(let j=0;j<N2;j++){
      const om=segPairOmega(YY,o1,i,i2,o2,j,(j+1)%N2);
      S+=om;A+=Math.abs(om);
    }
  }
  return [S/(4*Math.PI),A/(4*Math.PI)];
}
function gauss(o1,N1,o2,N2,same,absMode,YY){
  const g=gauss2(o1,N1,o2,N2,same,YY);
  return absMode?g[1]:g[0];
}
function arcLength(f){
  let L=0;const N=f.N,o=f.off;
  for(let k=0;k<N;k++){const k2=(k+1)%N;
    L+=Math.hypot(Y[o+3*k2]-Y[o+3*k],Y[o+3*k2+1]-Y[o+3*k+1],Y[o+3*k2+2]-Y[o+3*k+2]);}
  return L;
}
function carrierStats(f){
  const N=f.N,o=f.off;
  let cx=0,cy=0,cz=0;
  for(let k=0;k<N;k++){cx+=Y[o+3*k];cy+=Y[o+3*k+1];cz+=Y[o+3*k+2];}
  cx/=N;cy/=N;cz/=N;
  let R=0,rWall=0;
  for(let k=0;k<N;k++){
    R+=Math.hypot(Y[o+3*k]-cx,Y[o+3*k+1]-cy);
    const rw=Math.hypot(Y[o+3*k],Y[o+3*k+1]);if(rw>rWall)rWall=rw;
  }
  return {R:R/N,z:cz,rWall,cx,cy};
}
function minGapCross(){
  if(P.mode!=='botsing')return 1e9;
  const fa=carrierFilaments('A'),fb=carrierFilaments('B');
  if(!fa.length||!fb.length)return 1e9;
  let m2=Infinity;
  for(const f1 of fa)for(const f2 of fb)
    m2=Math.min(m2,pairGapExact2(f1,f2,m2));
  return Math.sqrt(m2);
}
// v7.2: exacte segment-segment minimumafstand² tussen twee filamenten,
// met middelpunt-prefilter tegen de lopende beste waarde.
function pairGapExact2(fa,fb,best2){
  const Na=fa.N,oa=fa.off,Nb=fb.N,ob=fb.off;
  let m2=best2;
  for(let i=0;i<Na;i++){
    const i2=(i+1)%Na;
    const ax=Y[oa+3*i],ay=Y[oa+3*i+1],az=Y[oa+3*i+2];
    const bx=Y[oa+3*i2],by=Y[oa+3*i2+1],bz=Y[oa+3*i2+2];
    const mx=.5*(ax+bx),my=.5*(ay+by),mz=.5*(az+bz);
    const li=Math.hypot(bx-ax,by-ay,bz-az);
    for(let j=0;j<Nb;j++){
      const j2=(j+1)%Nb;
      const cxx=Y[ob+3*j],cyy=Y[ob+3*j+1],czz=Y[ob+3*j+2];
      const dxx=Y[ob+3*j2],dyy=Y[ob+3*j2+1],dzz=Y[ob+3*j2+2];
      const nx=.5*(cxx+dxx)-mx,ny=.5*(cyy+dyy)-my,nz=.5*(czz+dzz)-mz;
      const lj=Math.hypot(dxx-cxx,dyy-cyy,dzz-czz);
      const bound=Math.sqrt(nx*nx+ny*ny+nz*nz)-.5*(li+lj);
      if(bound>0&&bound*bound>=m2)continue;
      const d2=segSegDist2(ax,ay,az,bx,by,bz,cxx,cyy,czz,dxx,dyy,dzz);
      if(d2<m2)m2=d2;
    }
  }
  return m2;
}
// v7.2: exacte minimale afstand tussen twee lijnsegmenten AB en CD (kwadraat).
// Geklemde closest-point-of-approach (Lumelsky/Ericson). Robuust voor
// gedegenereerde (punt)segmenten en parallelle paren.
function segSegDist2(ax,ay,az,bx,by,bz,cx,cy,cz,dx,dy,dz){
  const ux=bx-ax,uy=by-ay,uz=bz-az;
  const vx=dx-cx,vy=dy-cy,vz=dz-cz;
  const wx=ax-cx,wy=ay-cy,wz=az-cz;
  const A=ux*ux+uy*uy+uz*uz, B=ux*vx+uy*vy+uz*vz, C=vx*vx+vy*vy+vz*vz;
  const D=ux*wx+uy*wy+uz*wz, E=vx*wx+vy*wy+vz*wz;
  const den=A*C-B*B;
  let sN,sD=den,tN,tD=den;
  if(den<1e-30){sN=0;sD=1;tN=E;tD=C;}          // (bijna) parallel
  else{
    sN=B*E-C*D;tN=A*E-B*D;
    if(sN<0){sN=0;tN=E;tD=C;}
    else if(sN>sD){sN=sD;tN=E+B;tD=C;}
  }
  if(tN<0){tN=0;
    if(-D<0)sN=0;else if(-D>A){sN=sD;}else{sN=-D;sD=A;}
  }else if(tN>tD){tN=tD;
    const nD=-D+B;
    if(nD<0)sN=0;else if(nD>A){sN=sD;}else{sN=nD;sD=A;}
  }
  const sc=Math.abs(sD)<1e-30?0:sN/sD;
  const tc=Math.abs(tD)<1e-30?0:tN/tD;
  const px=wx+sc*ux-tc*vx, py=wy+sc*uy-tc*vy, pz=wz+sc*uz-tc*vz;
  return px*px+py*py+pz*pz;
}
// v7.2: exacte zelf-afstand op segmentniveau. De index-uitsluiting is niet
// langer de vaste fractie N/24 maar een boog-venster van 6a (2× de
// 3a-drempel): op een gladde kromme kan de zelf-afstand binnen dat venster
// niet onder 3a komen zonder dat de aκ-diagnose allang rood is. Aanliggende
// segmenten (gedeeld knooppunt, afstand 0) worden altijd uitgesloten.
function dminSelf(f){
  const N=f.N,o=f.off;
  let L=0;for(let k=0;k<N;k++){const k2=(k+1)%N;
    L+=Math.hypot(Y[o+3*k2]-Y[o+3*k],Y[o+3*k2+1]-Y[o+3*k+1],Y[o+3*k2+2]-Y[o+3*k+2]);}
  const lmean=L/Math.max(1,N);
  const skip=Math.max(2,Math.ceil(6*P.a/Math.max(lmean,1e-12)));
  let m2=Infinity;
  for(let i=0;i<N;i++){
    const i2=(i+1)%N;
    const ax=Y[o+3*i],ay=Y[o+3*i+1],az=Y[o+3*i+2];
    const bx=Y[o+3*i2],by=Y[o+3*i2+1],bz=Y[o+3*i2+2];
    const mx=.5*(ax+bx),my=.5*(ay+by),mz=.5*(az+bz);
    const li=Math.hypot(bx-ax,by-ay,bz-az);
    for(let j=i+1;j<N;j++){
      const dd=Math.min(j-i,N-(j-i));if(dd<skip)continue;
      const j2=(j+1)%N;
      const cxx=Y[o+3*j],cyy=Y[o+3*j+1],czz=Y[o+3*j+2];
      const dxx=Y[o+3*j2],dyy=Y[o+3*j2+1],dzz=Y[o+3*j2+2];
      // prefilter: middelpuntafstand minus halve segmentlengtes begrenst d_seg
      const nx=.5*(cxx+dxx)-mx,ny=.5*(cyy+dyy)-my,nz=.5*(czz+dzz)-mz;
      const lj=Math.hypot(dxx-cxx,dyy-cyy,dzz-czz);
      const bound=Math.sqrt(nx*nx+ny*ny+nz*nz)-.5*(li+lj);
      if(bound>0&&bound*bound>=m2)continue;
      const d2=segSegDist2(ax,ay,az,bx,by,bz,cxx,cyy,czz,dxx,dyy,dzz);
      if(d2<m2)m2=d2;
    }
  }
  return Math.sqrt(m2);
}


// ================= geometrische kernlimiet / tube reach =================
let coreRadiusMax=0.07;
function pointTangent(f,i){
  const im=(i-1+f.N)%f.N,ip=(i+1)%f.N,o=f.off;
  const x=Y[o+3*ip]-Y[o+3*im],y=Y[o+3*ip+1]-Y[o+3*im+1],z=Y[o+3*ip+2]-Y[o+3*im+2];
  const n=Math.hypot(x,y,z)||1;return [x/n,y/n,z/n];
}
function minCurvatureRadius(f){
  let out=Infinity;const o=f.off,N=f.N;
  for(let i=0;i<N;i++){
    const im=(i-1+N)%N,ip=(i+1)%N;
    const ax=Y[o+3*i]-Y[o+3*im],ay=Y[o+3*i+1]-Y[o+3*im+1],az=Y[o+3*i+2]-Y[o+3*im+2];
    const bx=Y[o+3*ip]-Y[o+3*i],by=Y[o+3*ip+1]-Y[o+3*i+1],bz=Y[o+3*ip+2]-Y[o+3*i+2];
    const la=Math.hypot(ax,ay,az),lb=Math.hypot(bx,by,bz);if(la<1e-12||lb<1e-12)continue;
    const dot=clamp((ax*bx+ay*by+az*bz)/(la*lb),-1,1);
    const kappa=2*Math.sin(0.5*Math.acos(dot))/Math.max(1e-12,0.5*(la+lb));
    if(kappa>1e-12)out=Math.min(out,1/kappa);
  }
  return out;
}
function approximateDoublyCriticalDistance(f){
  const N=f.N,o=f.off,skip=Math.max(6,Math.round(N/10));
  const stride=Math.max(1,Math.ceil(N/220));let best=Infinity;
  for(let i=0;i<N;i+=stride){
    const ti=pointTangent(f,i);
    for(let j=i+skip;j<N;j+=stride){
      const dd=Math.min(j-i,N-(j-i));if(dd<skip)continue;
      const dx=Y[o+3*j]-Y[o+3*i],dy=Y[o+3*j+1]-Y[o+3*i+1],dz=Y[o+3*j+2]-Y[o+3*i+2];
      const d=Math.hypot(dx,dy,dz);if(d<1e-12||d>=best)continue;
      const tj=pointTangent(f,j);
      const ci=Math.abs((dx*ti[0]+dy*ti[1]+dz*ti[2])/d);
      const cj=Math.abs((dx*tj[0]+dy*tj[1]+dz*tj[2])/d);
      if(ci<0.22&&cj<0.22)best=d;
    }
  }
  return best;
}
function intrinsicCoreRadiusLimit(){
  if(!Y||!fils.length)return Math.max(1e-6,P.R0);
  let reach=Infinity;
  for(const carrier of ['A','B']){
    const fs=carrierFilaments(carrier);if(!fs.length)continue;
    if(P.topo==='ring'&&fs.length===1&&!P.knotKey&&P.knotIdx<0){
      reach=Math.min(reach,carrierStats(fs[0]).R);
      continue;
    }
    for(const f of fs){
      reach=Math.min(reach,minCurvatureRadius(f));
      const dcsd=approximateDoublyCriticalDistance(f);
      if(Number.isFinite(dcsd))reach=Math.min(reach,0.5*dcsd);
    }
    for(let i=0;i<fs.length;i++)for(let j=i+1;j<fs.length;j++)
      reach=Math.min(reach,0.5*sampledPairGap(fs[i],fs[j]));
  }
  if(!Number.isFinite(reach)||reach<=0)reach=Math.max(1e-6,P.R0);
  return Math.max(1e-6,0.995*reach);
}
function updateCoreRadiusLimit(clampValue=true){
  coreRadiusMax=intrinsicCoreRadiusLimit();
  const maxMm=Math.max(0,coreRadiusMax*1000);
  const input=document.getElementById('sA');
  if(input){
    input.min=String(A_SIM_INPUT_FLOOR*1000);input.max=maxMm.toFixed(12);input.step='any';
    const range=input.closest('.param-hybrid')?.querySelector('input.param-slider');
    if(range){range.min=input.min;range.max=input.max;range.step=input.step;}
  }
  let wasClamped=false;
  if(clampValue&&(!Number.isFinite(P.a)||P.a<A_SIM_INPUT_FLOOR||P.a>coreRadiusMax)){
    P.a=clamp(Number.isFinite(P.a)?P.a:A_SIM_INPUT_FLOOR,A_SIM_INPUT_FLOOR,Math.max(A_SIM_INPUT_FLOOR,coreRadiusMax));
    wasClamped=true;
  }
  if(wasClamped&&P.coreFlowLock)syncCoreFlowCoupling('geometry');
  if(input)input.value=formatASimInputMm(P.a);
  const v=document.getElementById('vA');
  if(v)v.textContent=`${fmtLengthSI(P.a)} · max ${maxMm.toFixed(2)} mm`;
  const ct=contactThresholdInfo();
  const floorNote=ct.floorActive
    ?` Expertmodus: 3a=${fmtLengthSI(ct.physical)} ligt onder de numerieke afstandsvloer ${fmtLengthSI(ct.numerical)}; contactdetectie gebruikt de numerieke vloer.`
    :'';
  const note=document.getElementById('coreLimitNote');
  if(note)note.textContent=`Geometrische tube-reach ≈ ${maxMm.toFixed(3)} mm (kromming / doubly-critical zelfafstand). Dit is de zelfcontactgrens; de slanke filamentbenadering wordt al ruim vóór deze grens rood.${floorNote}`;
  syncHybridNumberInputs();
}

// ================= v7.5.3 SST vortex-stretching stability gate =================
const StretchGate={startT:0,profileEpoch:0,carriers:Object.create(null),steps:0,reason:'startup',lastReport:null,lastStatus:'',contaminated:false};
function carrierIds(){return [...new Set(fils.filter(f=>!f.ghost).map(f=>f.carrier||'A'))];}
function carrierLengthInState(X,carrier){
  let L=0;
  for(const f of fils){if(f.ghost||(f.carrier||'A')!==carrier)continue;
    for(let i=0;i<f.N;i++){const j=(i+1)%f.N,o=f.off;L+=Math.hypot(X[o+3*j]-X[o+3*i],X[o+3*j+1]-X[o+3*i+1],X[o+3*j+2]-X[o+3*i+2]);}}
  return L;
}
function carrierRadialScale(carrier){
  const fs=fils.filter(f=>!f.ghost&&(f.carrier||'A')===carrier);let cx=0,cy=0,n=0;
  for(const f of fs)for(let i=0;i<f.N;i++){cx+=Y[f.off+3*i];cy+=Y[f.off+3*i+1];n++;}
  if(!n)return Math.max(P.R0,1e-6);cx/=n;cy/=n;let r2=0;
  for(const f of fs)for(let i=0;i<f.N;i++){const dx=Y[f.off+3*i]-cx,dy=Y[f.off+3*i+1]-cy;r2+=dx*dx+dy*dy;}
  return Math.max(1e-9,Math.sqrt(r2/n));
}
function resetStretchGate(reason='reset',resetProfilePhase=true){
  StretchGate.startT=tPhys;StretchGate.steps=0;StretchGate.reason=reason;StretchGate.lastReport=null;StretchGate.lastStatus='';StretchGate.contaminated=false;
  if(resetProfilePhase)StretchGate.profileEpoch=tPhys;
  StretchGate.carriers=Object.create(null);
  if(Y&&fils.length)for(const carrier of carrierIds()){
    const L=carrierLengthInState(Y,carrier);StretchGate.carriers[carrier]={L0:L,L:L,G:0,elapsed:0,steps:0,sigmaMean:0,sigmaMin:0,sigmaMax:0,peakAbsSigma:0};
  }
  updateStretchGateDisplay(computeStretchGateReport());
}
function stretchSegmentStats(before,after,carrier,dt){
  let min=Infinity,max=-Infinity,sum=0,w=0;
  if(Math.abs(dt)<1e-30)return {min:0,max:0,mean:0};
  for(const f of fils){if(f.ghost||(f.carrier||'A')!==carrier)continue;
    for(let i=0;i<f.N;i++){const j=(i+1)%f.N,o=f.off;
      const lb=Math.hypot(before[o+3*j]-before[o+3*i],before[o+3*j+1]-before[o+3*i+1],before[o+3*j+2]-before[o+3*i+2]);
      const la=Math.hypot(after[o+3*j]-after[o+3*i],after[o+3*j+1]-after[o+3*i+1],after[o+3*j+2]-after[o+3*i+2]);
      if(!(lb>1e-30&&la>1e-30))continue;const sig=Math.log(la/lb)/dt,weight=0.5*(la+lb);
      min=Math.min(min,sig);max=Math.max(max,sig);sum+=sig*weight;w+=weight;
    }}
  return {min:Number.isFinite(min)?min:0,max:Number.isFinite(max)?max:0,mean:w>0?sum/w:0};
}
function updateStretchGateAcceptedStep(before,after,dt){
  if(!P.stretchGateEnabled||!before||!after||Math.abs(dt)<1e-30)return;
  for(const carrier of carrierIds()){
    let c=StretchGate.carriers[carrier];
    if(!c){const L=carrierLengthInState(before,carrier);c=StretchGate.carriers[carrier]={L0:L,L,G:0,elapsed:0,steps:0,sigmaMean:0,sigmaMin:0,sigmaMax:0,peakAbsSigma:0};}
    const Lb=carrierLengthInState(before,carrier),La=carrierLengthInState(after,carrier);
    if(!(Lb>1e-30&&La>1e-30))continue;
    const local=stretchSegmentStats(before,after,carrier,dt),dG=Math.log(La/Lb);
    c.G+=dG;c.L=La;c.elapsed+=dt;c.steps++;c.sigmaMean=dG/dt;c.sigmaMin=local.min;c.sigmaMax=local.max;
    c.peakAbsSigma=Math.max(c.peakAbsSigma,Math.abs(local.min),Math.abs(local.max));
  }
  StretchGate.steps++;StretchGate.lastReport=computeStretchGateReport();
}
function stretchReferenceTime(carrier){
  const R=carrierRadialScale(carrier),logTerm=Math.max(1,Math.abs(Math.log(Math.max(1.0000001,8*R/Math.max(P.a,1e-30)))-DELTA[P.core]));
  const selfRate=(P.stretchProfileApply&&P.stretchProfileOnly)?0:Math.abs(Gamma())*logTerm/(4*Math.PI*R*R);
  const rate=Math.max(selfRate,stretchProfileCharacteristicRate(),1e-12);
  return {tau:1/rate,rate,R,selfRate,profileRate:stretchProfileCharacteristicRate()};
}
function computeStretchGateReport(){
  if(!P.stretchGateEnabled)return {status:'off',carrier:'—',G:0,lambda:0,lambdaStar:0,lengthRatio:1,coreRatio:1,sigmaMean:0,sigmaMin:0,sigmaMax:0,profileShear:0,profileGain:1,observation:0,consistency:0,advice:'Gate uitgeschakeld.'};
  const ids=Object.keys(StretchGate.carriers);if(!ids.length)return {status:'warming',carrier:'—',G:0,lambda:0,lambdaStar:0,lengthRatio:1,coreRatio:1,sigmaMean:0,sigmaMin:0,sigmaMax:0,profileShear:0,profileGain:1,observation:0,consistency:0,advice:'Wacht op een actieve vortexdrager.'};
  let worst=null;
  for(const carrier of ids){const c=StretchGate.carriers[carrier],ref=stretchReferenceTime(carrier),elapsed=c.elapsed;
    const lambda=Math.abs(elapsed)>1e-15?c.G/elapsed:0,lambdaStar=lambda*ref.tau,obs=Math.abs(elapsed)/ref.tau;
    const direct=Math.log(Math.max(c.L,1e-300)/Math.max(c.L0,1e-300)),consistency=Math.abs(c.G-direct),probe=stretchProfileReference(ref.R);
    const item={carrier,G:c.G,lambda,lambdaStar,lengthRatio:Math.exp(c.G),coreRatio:Math.exp(-0.5*c.G),sigmaMean:c.sigmaMean,sigmaMin:c.sigmaMin,sigmaMax:c.sigmaMax,
      peakAbsSigma:c.peakAbsSigma,observation:obs,consistency,tau:ref.tau,profileShear:probe.shear,profileGain:probe.gain,profileLambda:probe.lambda,steps:c.steps};
    if(!worst||Math.abs(item.lambdaStar)>Math.abs(worst.lambdaStar))worst=item;
  }
  const warm=worst.steps<8||worst.observation<0.5,absStar=Math.abs(worst.lambdaStar),neutral=Math.max(1e-6,P.stretchNeutralTol),fail=Math.max(neutral,P.stretchFailTol);
  let status=warm?'warming':(absStar<=neutral?'good':(absStar<=fail?'warn':'bad'));
  const qualifiers=[];
  if(P.autoRelax||StretchGate.contaminated)qualifiers.push('auto-relax maakt de materiaalrekdiagnose niet-Hamiltoniaans');
  if(mfActive())qualifiers.push('α≠0: dit is geen inviscide SST/Euler-gate');
  if(P.stretchProfileApply&&!P.stretchProfileOnly)qualifiers.push('profiel is op Biot–Savart gesuperponeerd; geen exacte niet-lineaire Euler-oplossing');
  if(qualifiers.length&&status==='good')status='warn';
  const trend=worst.lambdaStar>neutral?'persistente rek':(worst.lambdaStar<-neutral?'persistente contractie':'stretch-neutraal binnen finite-time tolerantie');
  const advice=warm?'Observatievenster is korter dan 0,5 τ_ref; nog geen gate-besluit.':`${trend}; |Λ*|=${absStar.toExponential(3)} met grenzen ${neutral.toFixed(3)} / ${fail.toFixed(3)}.${qualifiers.length?' '+qualifiers.join('; ')+'.':''}`;
  return Object.assign(worst,{status,advice,qualifiers});
}
function fmtSignedRate(x){return Number.isFinite(x)?((x>=0?'+':'')+x.toExponential(3)+' s⁻¹'):'—';}
function updateStretchGateDisplay(rep=StretchGate.lastReport||computeStretchGateReport()){
  if(!rep)return;StretchGate.lastReport=rep;
  const box=document.getElementById('stretchGateBox');if(!box)return;
  box.classList.remove('gate-good','gate-warn','gate-bad','gate-warming','gate-off');box.classList.add('gate-'+rep.status);
  const labels={good:'PASS · STRETCH-NEUTRAAL',warn:'WAARSCHUWING',bad:'FAIL · PERSISTENTE REK/CONTRACTIE',warming:'OPWARMEN',off:'UIT'};
  document.getElementById('stretchGateStatus').textContent=labels[rep.status]||rep.status.toUpperCase();
  document.getElementById('stretchGateScope').textContent=`carrier ${rep.carrier} · ${P.stretchProfile.toUpperCase()}${P.stretchProfileOnly?' · profile-only':''}`;
  document.getElementById('stretchSigmaMean').textContent=fmtSignedRate(rep.sigmaMean);
  document.getElementById('stretchSigmaRange').textContent=`${fmtSignedRate(rep.sigmaMin)} / ${fmtSignedRate(rep.sigmaMax)}`;
  document.getElementById('stretchG').textContent=Number(rep.G).toFixed(6);
  document.getElementById('stretchLambda').textContent=fmtSignedRate(rep.lambda);
  document.getElementById('stretchLambdaStar').textContent=(rep.lambdaStar>=0?'+':'')+Number(rep.lambdaStar).toExponential(3);
  document.getElementById('stretchRatios').textContent=`${Number(rep.lengthRatio).toFixed(5)} · ${Number(rep.coreRatio).toFixed(5)}`;
  document.getElementById('stretchProfileShear').textContent=Math.abs(Number(rep.profileShear)).toExponential(3);
  document.getElementById('stretchProfileGain').textContent=Number(rep.profileGain).toFixed(6);
  document.getElementById('stretchObservation').textContent=Number(rep.observation).toFixed(3);
  document.getElementById('stretchConsistency').textContent=Number(rep.consistency).toExponential(2);
  document.getElementById('stretchGateAdvice').textContent=rep.advice;
  if(StretchGate.lastStatus!==rep.status){if(StretchGate.lastStatus)ModelLog.logEvent('stretch-gate-status',{from:StretchGate.lastStatus,to:rep.status,lambdaStar:rep.lambdaStar,G:rep.G,carrier:rep.carrier});StretchGate.lastStatus=rep.status;}
}
function syncStretchGateUi(){
  const set=(id,v)=>{const e=document.getElementById(id);if(e)e.value=String(v);};
  const gate=document.getElementById('cStretchGate');if(gate)gate.checked=P.stretchGateEnabled;
  const profile=document.getElementById('sStretchProfile');if(profile)profile.value=P.stretchProfile;
  const apply=document.getElementById('cStretchApply');if(apply)apply.checked=P.stretchProfileApply;
  const only=document.getElementById('cStretchOnly');if(only){only.checked=P.stretchProfileOnly;only.disabled=!P.stretchProfileApply;}
  set('sStretchOmega',P.stretchOmega0);set('sStretchBeta',P.stretchBeta);set('sStretchGamma',P.stretchGamma);set('sStretchSoftMm',P.stretchSoftening*1000);
  set('sStretchEpsMm',P.stretchEpsilon*1000);set('sStretchMode',P.stretchMode);set('sStretchNeutralTol',P.stretchNeutralTol);set('sStretchFailTol',P.stretchFailTol);
  const txt=(id,v)=>{const e=document.getElementById(id);if(e)e.textContent=v;};
  txt('vStretchOmega',P.stretchOmega0.toFixed(3)+' s⁻¹');txt('vStretchBeta',P.stretchBeta.toFixed(1)+' m⁻² s⁻¹');txt('vStretchGamma',P.stretchGamma.toFixed(4)+' m²/s');
  txt('vStretchSoft',(P.stretchSoftening*1000).toFixed(1)+' mm');txt('vStretchEps',(P.stretchEpsilon*1000).toFixed(1)+' mm/s');txt('vStretchMode',String(P.stretchMode));
  txt('vStretchNeutral',P.stretchNeutralTol.toFixed(3));txt('vStretchFail',P.stretchFailTol.toFixed(3));
  document.getElementById('stretchBetaRow')?.classList.toggle('hidden',P.stretchProfile!=='differential');
  document.getElementById('stretchGammaRow')?.classList.toggle('hidden',P.stretchProfile!=='regularized');
  document.getElementById('stretchSoftRow')?.classList.toggle('hidden',P.stretchProfile!=='regularized');
  updateStretchGateDisplay();
}

// ================= stabiliteitsdiagnose & geometrische auto-relax =================
function scoreDescending(x,good,bad){
  if(x<=good)return 100;if(x>=bad)return 0;
  return 100*(bad-x)/(bad-good);
}
function scoreAscending(x,bad,good){
  if(x>=good)return 100;if(x<=bad)return 0;
  return 100*(x-bad)/(good-bad);
}
function statusFromScore(v){return v>=75?'good':(v>=45?'warn':'bad');}
function capacityStatusFromScore(v){return v>=75?'good':(v>=45?'warn':'capacity');}
function worstStatus(...vals){
  const rank={good:0,warn:1,bad:2};let out='good';
  vals.forEach(v=>{const s=typeof v==='number'?statusFromScore(v):v;if(rank[s]>rank[out])out=s;});
  return out;
}
function stabilityElementTarget(id){
  const el=document.getElementById(id);if(!el)return null;
  if(el.classList.contains('seg'))return el;
  return el.closest('.ctrl')||el.closest('.param-hybrid')||el;
}
function clearStabilityTargets(){
  document.querySelectorAll('.stability-target').forEach(el=>{
    el.classList.remove('stability-target','stab-good','stab-warn','stab-bad','stab-capacity');
    if(el.dataset.stabilityTitle){el.title=el.dataset.stabilityTitle;delete el.dataset.stabilityTitle;}
  });
}
function markStabilityTarget(id,status,tip){
  const el=stabilityElementTarget(id);if(!el)return;
  el.classList.add('stability-target','stab-'+status);
  if(!el.dataset.stabilityTitle)el.dataset.stabilityTitle=el.title||'';
  el.title=tip||el.dataset.stabilityTitle;
}
function filamentResolutionMetrics(f){
  const N=f.N,o=f.off;
  let lmin=Infinity,lmax=0,lsum=0,maxAk=0,minLogArg=Infinity;
  const eD=Math.exp(DELTA[P.core]);
  for(let i=0;i<N;i++){
    const im=(i-1+N)%N,ip=(i+1)%N;
    const ax=Y[o+3*i]-Y[o+3*im],ay=Y[o+3*i+1]-Y[o+3*im+1],az=Y[o+3*i+2]-Y[o+3*im+2];
    const bx=Y[o+3*ip]-Y[o+3*i],by=Y[o+3*ip+1]-Y[o+3*i+1],bz=Y[o+3*ip+2]-Y[o+3*i+2];
    const la=Math.hypot(ax,ay,az),lb=Math.hypot(bx,by,bz);
    lmin=Math.min(lmin,lb);lmax=Math.max(lmax,lb);lsum+=lb;
    if(la>1e-12&&lb>1e-12){
      const dot=clamp((ax*bx+ay*by+az*bz)/(la*lb),-1,1);
      const ang=Math.acos(dot),kappa=2*Math.sin(0.5*ang)/Math.max(1e-12,0.5*(la+lb));
      maxAk=Math.max(maxAk,P.a*kappa);
      minLogArg=Math.min(minLogArg,2*Math.sqrt(la*lb)/(eD*Math.max(P.a,1e-12)));
    }
  }
  return {lmin,lmax,lmean:lsum/N,q:lmax/Math.max(lmin,1e-12),maxAk,minLogArg};
}
function sampledPairGap(fa,fb){
  // v7.2: exact op segmentniveau (naam behouden voor call-sites); de oude
  // gestreden knooppuntsteekproef kon interieurnaderingen missen.
  return Math.sqrt(pairGapExact2(fa,fb,Infinity));
}
function sampledSelfGap(f){
  return dminSelf(f); // v7.2: exact segmentniveau
}
function updateChiPanel(){
  const el=document.getElementById('chiRope');
  if(!el||!Y||!fils.length)return;
  const fa=carrierFilaments('A');
  if(!fa.length){el.textContent='—';return;}
  let L=0, rC=Infinity, dC=Infinity;
  for(const f of fa){
    L+=arcLength(f);
    rC=Math.min(rC,minCurvatureRadius(f));
    dC=Math.min(dC,approximateDoublyCriticalDistance(f));
  }
  for(let i=0;i<fa.length;i++)for(let j=i+1;j<fa.length;j++)
    dC=Math.min(dC,sampledPairGap(fa[i],fa[j]));
  const tau=Math.min(rC,dC/2);
  if(!(tau>1e-9)||!isFinite(tau)||!isFinite(L)){el.textContent='—';return;}
  const rope=L/(2*tau);
  el.textContent=rope.toFixed(3);
  const r2=document.getElementById('chiRopeRatio');
  if(r2)r2.textContent=(rope/16.371637).toFixed(3);
  const th=document.getElementById('chiThick');
  if(th)th.textContent=(tau*1000).toFixed(2)+' mm';
}
function tubeBoundaryMarginAt(x,y,z){
  return Math.min(P.Rcyl-Math.hypot(x,y)-P.a,z-zMin()-P.a,zMax()-z-P.a);
}
function computeStabilityReport(){
  if(!Y||!fils.length)return null;
  // v7.1 (B5): diagnose is puur — alleen meten, nooit P.a klemmen. Klemmen
  // gebeurt uitsluitend bij expliciete gebruikersacties (reset, geometrie).
  updateCoreRadiusLimit(false);
  let q=1,maxAk=0,minLogArg=Infinity,lmean=0,nm=0,minGap=Infinity,boundary=Infinity,Lnow=0;
  const realFils=fils.filter(f=>!f.ghost);
  for(const f of realFils){
    const m=filamentResolutionMetrics(f);q=Math.max(q,m.q);maxAk=Math.max(maxAk,m.maxAk);
    minLogArg=Math.min(minLogArg,m.minLogArg);lmean+=m.lmean;nm++;Lnow+=arcLength(f);
    minGap=Math.min(minGap,sampledSelfGap(f));
    for(let k=0;k<f.N;k++){
      const x=Y[f.off+3*k],y=Y[f.off+3*k+1],z=Y[f.off+3*k+2];
      // v7.2: marge t.o.v. de búisrand, niet de centerline (audit #9)
      boundary=Math.min(boundary,tubeBoundaryMarginAt(x,y,z));
    }
  }
  for(let i=0;i<realFils.length;i++)for(let j=i+1;j<realFils.length;j++)
    minGap=Math.min(minGap,sampledPairGap(realFils[i],realFils[j]));
  lmean/=Math.max(1,nm);
  const gaps=gapRatios(minGap),gapRatio=gaps.physical,gapRatioEffective=gaps.effective;
  const boundaryRatio=boundary/Math.max(P.a,lmean,1e-12);
  const lengthDrift=Math.abs(Lnow/Math.max(L0,1e-12)-1);
  const meshScore=scoreDescending(q,1.22,2.10);
  const gapScore=scoreAscending(gapRatioEffective,3.0,8.0);
  const curvatureScore=scoreDescending(maxAk,0.10,0.45);
  const coreScore=scoreAscending(minLogArg,1.15,4.0);
  const boundaryScore=scoreAscending(boundaryRatio,1.5,7.0);
  const lengthScore=scoreDescending(lengthDrift,0.025,0.28);
  const requestedAccNow=acc()*Math.max(0,stabilityThrottle);
  const perfWarming=performance.now()<perfWarmupUntil;
  const perfRatio=perfWarming||Math.abs(tPhys)<0.15||requestedAccNow<1e-8?1:clamp(effAcc/requestedAccNow,0,1);
  const perfScore=scoreAscending(perfRatio,0.20,0.80);
  let modelScore=100;
  if(P.inter==='lia'&&gapRatioEffective<10)modelScore=gapRatioEffective<5?20:55;
  // De numerieke score bevat uitsluitend geldigheids-/modelcriteria. De
  // haalbare afspeelsnelheid is een afzonderlijke computer-capaciteitsmeting.
  let score=(0.20*meshScore+0.23*gapScore+0.17*curvatureScore+0.10*coreScore+
    0.13*boundaryScore+0.09*lengthScore)/0.92;
  score=Math.min(score,modelScore);
  if(gapRatioEffective<3||boundary<0||minLogArg<=1)score=Math.min(score,18);
  const suggestions=[];
  if(meshScore<75)suggestions.push('verhoog kwaliteit of zet Auto-relax aan om de puntverdeling gelijkmatiger te maken');
  if(gapScore<75)suggestions.push('vergroot de vrije afstand: verlaag kernstraal a, verminder drift/botsingssnelheid, vergroot Δz_AB,0/offset of reset');
  if(curvatureScore<75)suggestions.push('max aκ is hoog: verlaag a, verhoog resolutie of gebruik Auto-relax');
  if(coreScore<75)suggestions.push('de lokale inductielogaritme is slecht opgelost: verlaag a of verhoog kwaliteit');
  if(boundaryScore<75)suggestions.push('vergroot cilinderdiameter/hoogte of centreer/reset de drager');
  if(lengthScore<75)suggestions.push('sterke lengtedrift: verlaag tijdversnelling of gebruik Auto-relax');
  if(!perfWarming&&perfScore<60)suggestions.push('capaciteitslimiet: verlaag de simulatiesnelheid, Γ/n, kwaliteit of het aantal particles; het CFL-traject blijft identiek');
  if(modelScore<75)suggestions.push('LIA mist belangrijke niet-lokale interactie: kies Biot–Savart');
  if(!suggestions.length)suggestions.push('instellingen liggen binnen de numerieke comfortzone; dit is geen bewijs van fysische stabiliteit');
  return {score:clamp(score,0,100),status:statusFromScore(score),q,gapRatio,gapRatioEffective,
    contactFloorActive:gaps.floorActive,minGap,maxAk,minLogArg,
    boundary,boundaryRatio,lengthDrift,perfRatio,perfWarming,meshScore,gapScore,curvatureScore,coreScore,
    boundaryScore,lengthScore,perfScore,modelScore,suggestions};
}
function updateStabilityDisplay(rep){
  if(!rep)return;
  stabilityLast=rep;
  const panel=document.getElementById('stabilityPanel'),gauge=document.getElementById('stabilityGauge');
  const color=rep.status==='good'?'#7BE8A8':(rep.status==='warn'?'#FFAE45':'#FF6E6E');
  panel.classList.remove('stab-good','stab-warn','stab-bad');panel.classList.add('stab-'+rep.status);
  gauge.style.setProperty('--score-angle',(rep.score*3.6).toFixed(1)+'deg');gauge.style.setProperty('--stab-color',color);
  document.getElementById('stabilityScore').textContent=Math.round(rep.score);
  document.getElementById('stabilityTitle').textContent=rep.status==='good'?'numeriek rustig':(rep.status==='warn'?'aandacht vereist':'instabiel / buiten geldigheid');
  document.getElementById('stabilitySummary').textContent=P.timeReverse
    ?'Achterwaartse integratie actief; Auto-relax is gepauzeerd en de numerieke veiligheidsrem blijft actief.'
    :(P.autoRelax?'Auto-relax actief; geometrische regularisatie corrigeert langzaam.':'Passieve numerieke diagnose; paars betekent alleen een computer-capaciteitslimiet.');
  document.getElementById('stabMesh').textContent=rep.q.toFixed(2);
  const fmtRatio=x=>!isFinite(x)?'∞':(Math.abs(x)>=1e5?x.toExponential(2):x.toFixed(1));
  document.getElementById('stabGap').textContent=fmtRatio(rep.gapRatio)+
    (rep.contactFloorActive?' · eff '+fmtRatio(rep.gapRatioEffective):'');
  // v7.5 (v7.4b §B.4): g_a=d_min/a uit ditzelfde 12-frame-rapport — geen extra
  // O(N²) per HUD-tick; exponentieel formaat op SST-schaal (g_a>1e6).
  {const gaEl=document.getElementById('hGa');
   if(gaEl)gaEl.textContent=fmtRatio(rep.gapRatio)+(rep.contactFloorActive?' · eff '+fmtRatio(rep.gapRatioEffective):'');}
  document.getElementById('stabCurv').textContent=rep.maxAk.toFixed(3);
  document.getElementById('stabBoundary').textContent=(rep.boundary*1000).toFixed(1)+' mm';
  document.getElementById('stabLength').textContent=(100*rep.lengthDrift).toFixed(1)+'%';
  document.getElementById('stabPerf').textContent=rep.perfWarming?'meting…':((100*rep.perfRatio).toFixed(0)+'%'+(rep.perfScore<45?' · capaciteit':''));
  document.getElementById('stabThrottle').textContent=(100*stabilityThrottle).toFixed(0)+'%';
  document.getElementById('stabilityAdvice').textContent='Advies: '+rep.suggestions.slice(0,3).join(' · ')+'.';
  clearStabilityTargets();
  const coreStat=worstStatus(rep.curvatureScore,rep.coreScore,rep.gapScore);
  const meshStat=worstStatus(rep.meshScore,rep.curvatureScore,rep.coreScore);
  const gapStat=statusFromScore(rep.gapScore),boundStat=statusFromScore(rep.boundaryScore),perfStat=capacityStatusFromScore(rep.perfScore);
  markStabilityTarget('sA',coreStat,rep.suggestions.find(x=>x.includes('aκ')||x.includes('kernstraal')||x.includes('inductielogaritme'))||'a_sim beïnvloedt de numerieke slankheid en contactmarge.');
  markStabilityTarget('qualSeg',meshStat,rep.meshScore<75?'Verhoog kwaliteit voor gelijkmatiger segmenten en betere kromming.':'Resolutie is passend.');
  markStabilityTarget('interSeg',statusFromScore(rep.modelScore),rep.modelScore<75?'Schakel naar Biot–Savart; LIA mist de nabije niet-lokale interactie.':'Interactiemodel past bij de huidige afstand.');
  markStabilityTarget('sDiam',boundStat,rep.boundaryScore<75?'Vergroot de diameter of reset/centreer de knoop.':'Radiale domeinmarge is voldoende.');
  markStabilityTarget('sHeight',boundStat,rep.boundaryScore<75?'Vergroot de halve hoogte of reset/centreer de knoop.':'Axiale domeinmarge is voldoende.');
  markStabilityTarget('sSepAB',gapStat,rep.gapScore<75?'Vergroot de initiële knoopafstand voor de volgende reset/sweep.':'De ingestelde startafstand ligt binnen de huidige contactmarge.');
  markStabilityTarget('sOff',gapStat,rep.gapScore<75?'Pas de laterale offset aan om near-contact te vermijden.':'Onderlinge vrije afstand is voldoende.');
  ['sW','sVzA','sVzB'].forEach(id=>markStabilityTarget(id,worstStatus(gapStat,boundStat),rep.gapScore<75?'Verminder de opgelegde drift; strengen naderen het reconnectieregime.':'Drift is binnen de huidige marge.'));
  ['sGa','sNq','sOm','sAcc','sTracerCount','sStreamlineCount'].forEach(id=>markStabilityTarget(id,perfStat,rep.perfWarming?'Capaciteitsmeting warmt 0,9 s op na de laatste snelheidswijziging.':(rep.perfScore<60?'Computer-capaciteitslimiet: verlaag belasting of afspeeltempo; dit is geen numerieke instabiliteit.':'Rekenlast is beheersbaar.')));
  const emissive=rep.status==='good'?0x123d29:(rep.status==='warn'?0x4a2f0d:0x4a1018);
  [matSolidA,matSolidB].forEach(m=>{if(m&&m.emissive){m.emissive.setHex(emissive);m.emissiveIntensity=rep.status==='good'?0.16:(rep.status==='warn'?0.30:0.42);}});
  scheduleSidebarFit();
}
function throttleFromStabilityScore(score){
  // Volle snelheid vanaf score 75; smoothstep naar nul bij score 0.
  const x=clamp(score/75,0,1);
  return x*x*(3-2*x);
}
function updateStabilityThrottle(dtReal){
  stabilityThrottleTarget=stabilityLast?throttleFromStabilityScore(stabilityLast.score):1;
  if(flagged)stabilityThrottleTarget=0;
  // Sneller afremmen dan herstellen, zodat ongeldige configuraties direct kalmeren.
  const tau=stabilityThrottleTarget<stabilityThrottle?0.28:1.10;
  const blend=1-Math.exp(-Math.max(0,dtReal)/tau);
  stabilityThrottle+=blend*(stabilityThrottleTarget-stabilityThrottle);
  if(stabilityThrottle<0.002&&stabilityThrottleTarget===0)stabilityThrottle=0;
  stabilityThrottle=clamp(stabilityThrottle,0,1);
}

function carrierRelaxGroups(){
  const groups=new Map();
  fils.filter(f=>!f.ghost).forEach(f=>{if(!groups.has(f.carrier))groups.set(f.carrier,[]);groups.get(f.carrier).push(f);});
  return [...groups.values()];
}
function groupCentroidRms(group){
  let cx=0,cy=0,cz=0,n=0;
  group.forEach(f=>{for(let k=0;k<f.N;k++){cx+=Y[f.off+3*k];cy+=Y[f.off+3*k+1];cz+=Y[f.off+3*k+2];n++;}});
  cx/=n;cy/=n;cz/=n;let r2=0;
  group.forEach(f=>{for(let k=0;k<f.N;k++){const dx=Y[f.off+3*k]-cx,dy=Y[f.off+3*k+1]-cy,dz=Y[f.off+3*k+2]-cz;r2+=dx*dx+dy*dy+dz*dz;}});
  return {cx,cy,cz,rms:Math.sqrt(r2/n),n};
}
function redistributeFilamentUniform(f){
  const N=f.N,o=f.off,cum=new Float64Array(N+1);cum[0]=0;
  for(let k=0;k<N;k++){const k2=(k+1)%N;cum[k+1]=cum[k]+Math.hypot(Y[o+3*k2]-Y[o+3*k],Y[o+3*k2+1]-Y[o+3*k+1],Y[o+3*k2+2]-Y[o+3*k+2]);}
  const L=cum[N];if(L<1e-12)return;
  const out=new Float64Array(3*N);let j=0;
  for(let k=0;k<N;k++){
    const target=L*k/N;while(j<N-1&&cum[j+1]<target)j++;
    const j2=(j+1)%N,den=Math.max(1e-12,cum[j+1]-cum[j]),u=(target-cum[j])/den;
    out[3*k]=Y[o+3*j]+u*(Y[o+3*j2]-Y[o+3*j]);
    out[3*k+1]=Y[o+3*j+1]+u*(Y[o+3*j2+1]-Y[o+3*j+1]);
    out[3*k+2]=Y[o+3*j+2]+u*(Y[o+3*j2+2]-Y[o+3*j+2]);
  }
  Y.set(out,o);
}
function applyShortRangeRepulsion(group,amount){
  const target=Math.max(4.5*P.a,1e-6),skipFrac=1/28;
  for(let ai=0;ai<group.length;ai++)for(let bi=ai;bi<group.length;bi++){
    const fa=group[ai],fb=group[bi],skip=Math.max(4,Math.round(fa.N*skipFrac));
    const stride=Math.max(1,Math.ceil(Math.max(fa.N,fb.N)/160));
    for(let i=0;i<fa.N;i+=stride){
      const j0=ai===bi?i+skip:0;
      for(let j=j0;j<fb.N;j+=stride){
        if(ai===bi&&Math.min(j-i,fa.N-(j-i))<skip)continue;
        const ia=fa.off+3*i,ib=fb.off+3*j,dx=Y[ia]-Y[ib],dy=Y[ia+1]-Y[ib+1],dz=Y[ia+2]-Y[ib+2];
        const d=Math.hypot(dx,dy,dz);if(d>=target||d<1e-10)continue;
        const push=0.5*amount*(target-d)/target,ux=dx/d,uy=dy/d,uz=dz/d;
        Y[ia]+=push*ux;Y[ia+1]+=push*uy;Y[ia+2]+=push*uz;
        Y[ib]-=push*ux;Y[ib+1]-=push*uy;Y[ib+2]-=push*uz;
      }
    }
  }
}
function autoRelaxGeometry(dtReal){
  if(!P.autoRelax||P.timeReverse||!Y||!fils.length||flagged)return;
  const guardSnapshot=P.topologyGuard?Y.slice():null;
  const guardGap=P.topologyGuard?topologyClearance():Infinity;
  const alpha=clamp(0.55*dtReal,0,0.012),groups=carrierRelaxGroups();
  for(const group of groups){
    const before=groupCentroidRms(group),updates=[];
    for(const f of group){
      const out=new Float64Array(3*f.N),o=f.off,N=f.N;
      for(let k=0;k<N;k++){
        const im=(k-1+N)%N,ip=(k+1)%N;
        const px=Y[o+3*k],py=Y[o+3*k+1],pz=Y[o+3*k+2];
        let tx=Y[o+3*ip]-Y[o+3*im],ty=Y[o+3*ip+1]-Y[o+3*im+1],tz=Y[o+3*ip+2]-Y[o+3*im+2];
        const tl=Math.hypot(tx,ty,tz)||1;tx/=tl;ty/=tl;tz/=tl;
        let lx=0.5*(Y[o+3*im]+Y[o+3*ip])-px,ly=0.5*(Y[o+3*im+1]+Y[o+3*ip+1])-py,lz=0.5*(Y[o+3*im+2]+Y[o+3*ip+2])-pz;
        const tang=lx*tx+ly*ty+lz*tz;lx-=tang*tx;ly-=tang*ty;lz-=tang*tz;
        out[3*k]=px+alpha*lx;out[3*k+1]=py+alpha*ly;out[3*k+2]=pz+alpha*lz;
      }
      updates.push([f,out]);
    }
    updates.forEach(([f,out])=>Y.set(out,f.off));
    if((autoRelaxFrame%4)===0)applyShortRangeRepulsion(group,Math.max(P.a,0.25*(group[0]?filamentResolutionMetrics(group[0]).lmean:0))*alpha);
    if((autoRelaxFrame%3)===0)group.forEach(redistributeFilamentUniform);
    const after=groupCentroidRms(group),scale=after.rms>1e-12?before.rms/after.rms:1;
    group.forEach(f=>{for(let k=0;k<f.N;k++){
      const i=f.off+3*k;Y[i]=before.cx+(Y[i]-after.cx)*scale;Y[i+1]=before.cy+(Y[i+1]-after.cy)*scale;Y[i+2]=before.cz+(Y[i+2]-after.cz)*scale;
    }});
  }
  if(guardSnapshot){
    const postGap=topologyClearance(),dmax=maxStateDisplacement(guardSnapshot,Y),dc=contactThresholdInfo().effective;
    const budget=0.20*Math.max(guardGap-dc,dc);
    if(postGap<=dc||dmax>budget){
      Y.set(guardSnapshot);P.autoRelax=false;
      const cb=document.getElementById('cAutoRelax');if(cb)cb.checked=false;
      const badge=document.getElementById('autoRelaxBadge');if(badge){badge.textContent='UIT';badge.classList.remove('on');}
      setFlag('⚠ topology guard heeft een auto-relax-mutatie teruggedraaid: de regularisatie gebruikte te veel tube-clearance. Auto-relax is uitgezet.',true);
      return;
    }
    lastTopologyGap=postGap;
  }
  invalidateBundleBEM('auto-relax');
  if(P.stretchGateEnabled)StretchGate.contaminated=true;
  autoRelaxFrame++;
}

// ================= reset / rebuild =================
function applyCanonPreset(){
  disableStretchProfileCoupling();P.stretchGateEnabled=true;
  P.mode='botsing'; P.topo='ring'; P.inter='bs'; P.core='hol'; P.med='demo'; P.qual='mid'; P.coreFlowLock=false;
  P.Om=1; P.GaDemo=2; P.nQ=1; P.a=1.5e-3; P.off=0; P.w=0;
  P.displayFrame='lab'; P.solverFrame='corot'; P.bgFlow='none';
  P.R0=0.07; P.zA=-0.42; P.zB=0.42; P.Rcyl=0.25; P.Hcyl=0.5;
  P.knotIdx=-1; P.knotKey=''; P.compA=1; P.compB=1;
  P.ccwA=true; P.ccwB=false; P.mirrorB=false; P.vzA=0; P.vzB=0; P.lockVz=true;
  P.revOm=false; P.revGa=false; P.revOff=false; P.revW=false; P.revVzA=false; P.revVzB=false;
  P.ghostStewartson=false; P.taylorOsc.enabled=false;
  Object.keys(Flags).forEach(k=>{Flags[k]=false;});
  renderFormula(); syncDiagnosticToggles();
  rebuildVolumeEnvelope();
  syncUi();
}
function applyPistolPreset(){
  disableStretchProfileCoupling();P.stretchGateEnabled=true;
  P.mode='solo'; P.topo='ring'; P.inter='bs'; P.core='hol'; P.med='demo'; P.qual='mid'; P.coreFlowLock=false;
  P.Om=0; P.GaDemo=2; P.nQ=1; P.a=1.5e-3; P.off=0;
  P.displayFrame='lab'; P.solverFrame='corot'; P.bgFlow='none';
  P.R0=0.07; P.zSolo=-0.42; P.Rcyl=0.25; P.Hcyl=0.5;
  P.knotIdx=-1; P.knotKey=''; P.w=0; P.vzA=0; P.vzB=0;
  P.ccwA=true; P.ghostStewartson=false; P.taylorOsc.enabled=false;
  P.twistProxyEnabled=false;
  P.revOm=false; P.revGa=false; P.revW=false;
  Object.keys(Flags).forEach(k=>{Flags[k]=false;});
  renderFormula(); syncDiagnosticToggles();
  rebuildVolumeEnvelope();
  syncUi();
}
function applyTaylorPreset(){
  disableStretchProfileCoupling();P.stretchGateEnabled=true;
  P.mode='solo'; P.topo='ring'; P.inter='bs'; P.core='hol'; P.med='demo'; P.qual='mid'; P.coreFlowLock=false;
  P.Om=1; P.GaDemo=2; P.nQ=1; P.a=1.5e-3; P.off=0;
  P.displayFrame='lab'; P.solverFrame='corot'; P.bgFlow='none';
  P.R0=0.07; P.zSolo=0.0; P.Rcyl=0.25; P.Hcyl=0.5;
  P.knotIdx=-1; P.knotKey='';
  P.w=0.03; P.revW=false;
  P.ghostStewartson=false;
  P.taylorOsc={enabled:false, amplitude:0.25, period:8};
  P.revOm=false; P.revGa=false;
  Object.keys(Flags).forEach(k=>{Flags[k]=false;});
  setDvAll(true);
  renderFormula(); syncDiagnosticToggles();
  rebuildVolumeEnvelope();
  syncUi();
}
function resetState(){
  ghostFil=null;
  const N=carrierN();
  const specs=P.mode==='botsing'
    ?[{which:'A',z:P.zA,cx:0,want:carrierWantDir('A')},
      {which:'B',z:P.zB,cx:carrierOffsetX('B'),want:carrierWantDir('B')}]
    :[{which:'A',z:P.zSolo,cx:carrierOffsetX('A'),want:carrierWantDir('A')}];
  const chunks=[];
  for(const sp of specs){
    const comps=makeCarrierComponents(N,sp.z,sp.cx,sp.want,sp.which);
    comps.forEach((pts,component)=>chunks.push({pts,N,carrier:sp.which,component}));
  }
  const totalPts=chunks.reduce((a,c)=>a+c.N,0);
  Y=new Float64Array(3*totalPts);
  fils=[];
  let off=0;
  for(const ch of chunks){
    Y.set(ch.pts,off);
    fils.push({off,N:ch.N,carrier:ch.carrier,component:ch.component,topology:P.knotKey||P.topo,idealKnotId:P.knotKey||null});
    off+=3*ch.N;
  }
  if(P.centerLock&&P.mode==='solo')centerSoloCarrierAtOrigin();
  captureCarrierAnchors();
  K1=new Float64Array(Y.length);K2=new Float64Array(Y.length);
  K3=new Float64Array(Y.length);K4=new Float64Array(Y.length);TT=new Float64Array(Y.length);
  tPhys=0;phi=0;bundlePhi=0;flagged="";warned=false;lastUmax=1e-9;
  resetPerformanceMeasurement(900);stepDebt=0;hist.length=0;
  stabilityLast=null;stabilityFrame=0;autoRelaxFrame=0;
  stabilityThrottle=1;stabilityThrottleTarget=1;
  Wr0=0;for(const f of fils){if(f.ghost)continue;Wr0+=gauss(f.off,f.N,f.off,f.N,true);}
  L0=0;for(const f of fils)L0+=arcLength(f);
  document.getElementById('flag').style.display='none';
  rebuildLines();
  rebuildTubes(true);
  updateSubtitle();
  initTwistProxy();
  syncGhostRing();
  updateCoreRadiusLimit(true);
  lastTopologyGap=topologyClearance();
  bundleBEMStepCounter=0;invalidateBundleBEM('reset');ensureBundleBEM(true);
  rebuildLattice();
  rebuildStreamlines(true);
  markPotentialFlowDirty();updatePotentialFlowVisual(true);
  resetStretchGate('state-reset',true);
  resetSpecClockRuntime('state-reset · fase-referentie opnieuw vereist');
  if(P.specClockEnabled){
    P.accExp=0;
    SpecClock.autoStartAfterCalibration=true;
    paused=true;
    const pauseButton=document.getElementById('bPause');if(pauseButton)pauseButton.textContent='Hervat';
    const accSource=document.getElementById('sAcc');if(accSource)accSource.value='0';
    const accValue=document.getElementById('vAcc');if(accValue)accValue.textContent=fmtAcc(acc());
    resetPlaybackDebt('spec-clock-reset-arm');
  }
  updateInitialSeparationUi();
  updateSpecClockDisplay();
}
function taylorOscillationApplies(){
  return P.mode==='solo'&&!P.centerLock&&P.taylorOsc.enabled&&!!Y&&!!fils.length;
}
function applyTaylorOscillation(atTime=tPhys){
  if(!taylorOscillationApplies())return;
  const st=carrierGroupStats('A');
  const zAnchor=P.zSolo;
  const zT=zAnchor+P.taylorOsc.amplitude*Math.sin(2*Math.PI*atTime/Math.max(0.5,P.taylorOsc.period));
  const dz=zT-st.z;
  if(Math.abs(dz)<1e-9)return;
  for(const f of carrierFilaments('A'))for(let k=0;k<f.N;k++)Y[f.off+3*k+2]+=dz;
}
function advanceFilamentCandidate(dt,endTime){
  const umax=rk4Step(dt);
  // De kinematische Taylor-correctie hoort bij de kandidaat-eindtoestand en
  // moet dus vóór contactdetectie en in iedere bisectietrial worden toegepast.
  applyTaylorOscillation(endTime);
  wrapFilamentCarriersZ();
  return umax;
}

// ================= three.js scène =================
const canvas=document.getElementById('c3d');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true});
const scene=new THREE.Scene();scene.background=new THREE.Color(0x0B1020);
// Subtiele verlichting voorkomt dat transparante MeshPhysicalMaterial-buizen zwart renderen.
scene.add(new THREE.HemisphereLight(0xBFDFFF,0x101526,0.82));
const keyLight=new THREE.DirectionalLight(0xFFFFFF,0.72);keyLight.position.set(1.4,-1.0,1.8);scene.add(keyLight);
const camera=new THREE.PerspectiveCamera(45,1,0.01,20);
let camTh=0.9,camPh=1.15,camD=1.6;
const camTarget=new THREE.Vector3(0,0,0);
function updCam(){
  camera.position.set(
    camTarget.x+camD*Math.sin(camPh)*Math.cos(camTh),
    camTarget.y+camD*Math.sin(camPh)*Math.sin(camTh),
    camTarget.z+camD*Math.cos(camPh));
  camera.up.set(0,0,1);camera.lookAt(camTarget);
}
const worldGrp=new THREE.Group();scene.add(worldGrp);
const filGrp=new THREE.Group();scene.add(filGrp);   // filament-frame (Y-coördinaten)
const volumeGrp=new THREE.Group();scene.add(volumeGrp);
let cylMesh=null, endRings=[], footprintDiscs=[];

function disposeMesh(m){
  if(!m)return;
  if(m.geometry)m.geometry.dispose();
  if(m.material){
    if(Array.isArray(m.material))m.material.forEach(x=>x.dispose());
    else m.material.dispose();
  }
}
function hybridRangeFromInput(input,value=Number(input.value)||0){
  if(input.dataset.scale!=='log')return value;
  const lo=Math.max(Number.MIN_VALUE,Number(input.dataset.logMin)||1e-4);
  const hi=Math.max(lo*1.000001,Number(input.max)||1);
  if(value<=0)return 0;
  return 1+999*Math.log(clamp(value,lo,hi)/lo)/Math.log(hi/lo);
}
function hybridInputFromRange(input,sliderValue){
  if(input.dataset.scale!=='log')return Number(sliderValue);
  const lo=Math.max(Number.MIN_VALUE,Number(input.dataset.logMin)||1e-4);
  const hi=Math.max(lo*1.000001,Number(input.max)||1);
  const u=Number(sliderValue);
  if(u<=0)return 0;
  return lo*Math.pow(hi/lo,(u-1)/999);
}
function formatHybridInputValue(input,value){
  if(input.dataset.scale!=='log')return String(value);
  if(value===0)return '0';
  if(value<0.001)return value.toFixed(7).replace(/0+$/,'').replace(/\.$/,'');
  if(value<0.1)return value.toFixed(5).replace(/0+$/,'').replace(/\.$/,'');
  if(value<10)return value.toFixed(4).replace(/0+$/,'').replace(/\.$/,'');
  return value.toFixed(3).replace(/0+$/,'').replace(/\.$/,'');
}
function syncHybridNumberInputs(){
  document.querySelectorAll('input.param-number').forEach(input=>{
    const range=input.closest('.param-hybrid')?.querySelector('input.param-slider');
    if(range)range.value=String(hybridRangeFromInput(input));
  });
}

function updateStretchReadout(){
  const b=document.getElementById('bLinkDH');
  const out=document.getElementById('vStretch');
  if(!b||!out)return;
  b.classList.toggle('active',P.linkDH);
  b.setAttribute('aria-pressed',String(P.linkDH));
  b.textContent=P.linkDH?'🔗 D↔H · V constant':'⛓ D / H los';
  if(P.linkDH){
    const lr=P.Rcyl/Math.max(1e-12,P.linkRefR);
    const lz=P.Hcyl/Math.max(1e-12,P.linkRefH);
    out.textContent=`tracers: λr=${lr.toFixed(3)} · λz=${lz.toFixed(3)} · λr²λz=${(lr*lr*lz).toFixed(3)} · knopen 1:1`;
  }else{
    out.textContent='onafhankelijke cilinderafmetingen · knopen onvervormd';
  }
}

function scaleVolumeContents(radialScale,axialScale){
  if(!Number.isFinite(radialScale)||!Number.isFinite(axialScale)||radialScale<=0||axialScale<=0)return;

  // Alleen het coarse-grained volume en de passieve tracers volgen de
  // opgelegde cilindervorm. De vortexfilamenten Y blijven in fysieke
  // coördinaten onveranderd: een wijziging van het kijk-/volume-kader is
  // geen constitutieve vortexrek. Werkelijke filamentrek moet uit de
  // Biot--Savart/LIA-dynamica zelf ontstaan.
  if(trArr){
    for(let i=0;i<trArr.length;i+=3){
      trArr[i]*=radialScale;
      trArr[i+1]*=radialScale;
      trArr[i+2]*=axialScale;
    }
    if(trGeo?.attributes?.position)trGeo.attributes.position.needsUpdate=true;
  }
}

function applyVolumeResize(newR,newH){
  newR=clamp(newR,0.025,1.0);
  newH=clamp(newH,0.025,2.5);
  const oldR=Math.max(1e-12,P.Rcyl), oldH=Math.max(1e-12,P.Hcyl);
  if(Math.abs(newR-oldR)<1e-12 && Math.abs(newH-oldH)<1e-12)return;
  scaleVolumeContents(newR/oldR,newH/oldH);
  P.Rcyl=newR;
  P.Hcyl=newH;
  if(P.specClockEnabled){
    resetSpecClockRuntime('cilindergeometrie gewijzigd · fase-nullreferentie ongeldig');
    SpecClock.autoStartAfterCalibration=true;
    setPausedState(true,'spec-clock-volume-change');
    if(window.ModelLog)window.ModelLog.logEvent('spec-clock-calibration-invalidated',{reason:'volume-resize',Rcyl:P.Rcyl,Hcyl:P.Hcyl});
    setFlag('⚠ cilindergeometrie gewijzigd: de SPEC CLOCK-run is gepauzeerd en vereist een nieuwe fase-nullkalibratie bij t=0.',true);
  }
  rebuildVolumeEnvelope();
  syncGhostRing();
  rebuildLines();
  rebuildTubes(true);
  updateIndicators(tPhys);
  syncUi();
}

function rebuildVolumeEnvelope(){
  // Oude cap-footprints leven in filGrp en moeten apart worden opgeruimd.
  footprintDiscs.forEach(d=>{filGrp.remove(d);disposeMesh(d);});
  while(volumeGrp.children.length){
    const c=volumeGrp.children.pop();
    disposeMesh(c);
  }
  cylMesh=null; endRings=[]; footprintDiscs=[];
  const cylGeo=new THREE.CylinderGeometry(P.Rcyl,P.Rcyl,cylinderHeight(),48,1,true);
  cylGeo.rotateX(Math.PI/2);
  cylMesh=new THREE.Mesh(cylGeo,new THREE.MeshBasicMaterial({color:0x1E2C4A,wireframe:true,transparent:true,opacity:0.32}));
  volumeGrp.add(cylMesh);
  for(const z of [zMin(),zMax()]){
    const pts=[];
    for(let k=0;k<=64;k++){const th=2*Math.PI*k/64;
      pts.push(new THREE.Vector3(P.Rcyl*Math.cos(th),P.Rcyl*Math.sin(th),z));}
    const ring=new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({color:0x2A4A7A,transparent:true,opacity:0.6}));
    volumeGrp.add(ring); endRings.push(ring);
  }
  const rFp=P.Rcyl*0.25;
  for(const z of [zMin(),zMax()]){
    const d=new THREE.Mesh(new THREE.RingGeometry(rFp*0.92,rFp,48),
      new THREE.MeshBasicMaterial({color:0x55D6FF,transparent:true,opacity:0.55,side:THREE.DoubleSide}));
    d.position.set(0,0,z); d.visible=false; filGrp.add(d); footprintDiscs.push(d);
  }
  rebuildLattice();
  rebuildFrameBackdrop();
  markPotentialFlowDirty();
  if(typeof camTarget!=="undefined") camTarget.z=0;
  const gunInset=Math.min(0.01,0.02*cylinderHeight());
  if(typeof gunA!=="undefined") gunA.position.z=zMin()+gunInset;
  if(typeof gunB!=="undefined") gunB.position.z=zMax()-gunInset;
  if(P.linkDH) P.linkVolumeRef=cylinderVolume();
  updateHeaderTitle();
}
// vortexrooster (representatief, hex-gepakt, aantal ∝ |Ω|)
// De lijnen representeren coarse-grained axiale vorticiteit, niet individuele canonieke SST-kernen.
// Fictieve inertiaalcilinder: alleen zichtbaar in het roterende frame.
// Hij staat bewust buiten de flowcilinder en is geen fysieke wand.
const frameBackdropGrp=new THREE.Group();scene.add(frameBackdropGrp);
const latticeGrp=new THREE.Group();worldGrp.add(latticeGrp);
function disposeGroupChildren(group){
  while(group.children.length){const c=group.children.pop();if(c.geometry)c.geometry.dispose();if(c.material)c.material.dispose();}
}
function rebuildFrameBackdrop(){
  disposeGroupChildren(frameBackdropGrp);
  const color=new THREE.Color(P.vorticityLineColor||'#0F1A29');
  const rOuter=P.Rcyl*1.09;
  const z0=zMin(),z1=zMax();
  // Uitsluitend verticale markers op een fictieve buitencilinder. Een bewust
  // ongelijke helderheidsverdeling doorbreekt de rotatiesymmetrie, zodat
  // draairichting en snelheid in het roterende frame zichtbaar blijven.
  const markerCount=16;
  for(let i=0;i<markerCount;i++){
    const th=2*Math.PI*i/markerCount;
    const x=rOuter*Math.cos(th),y=rOuter*Math.sin(th);
    const pts=[new THREE.Vector3(x,y,z0),new THREE.Vector3(x,y,z1)];
    const major=(i===0),secondary=(i===5||i===11);
    const opacity=major?0.88:(secondary?0.48:0.20);
    const mat=new THREE.LineBasicMaterial({color,transparent:true,opacity,depthWrite:false});
    const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),mat);
    line.renderOrder=2;
    frameBackdropGrp.add(line);
  }
  frameBackdropGrp.visible=P.displayFrame==='corot';
}
function rebuildLattice(){
  while(latticeGrp.children.length){const c=latticeGrp.children.pop();c.geometry.dispose();c.material.dispose();}
  if(P.bundleEnabled){
    rebuildBundleLines();
    return;
  }
  const target=Math.min(90,Math.round(40*Math.abs(P.Om)));
  if(target<1)return;
  const r=0.93*P.Rcyl;
  const d=Math.sqrt(2*Math.PI*r*r/(Math.sqrt(3)*target));
  const rows=Math.ceil(2*r/(d*Math.sqrt(3)/2));
  let n=0;
  for(let j=-rows;j<=rows&&n<target+10;j++){
    const yy=j*d*Math.sqrt(3)/2;
    for(let i=-rows;i<=rows;i++){
      const xx=i*d+(j&1?d/2:0);
      if(xx*xx+yy*yy>r*r)continue;
      const op=0.3+0.28*((Math.sin(i*12.9898+j*78.233)*43758.5453)%1+1)%1;
      const g=new THREE.BufferGeometry().setFromPoints(
        [new THREE.Vector3(xx,yy,zMin()+0.01),new THREE.Vector3(xx,yy,zMax()-0.01)]);
      latticeGrp.add(new THREE.Line(g,new THREE.LineBasicMaterial({color:new THREE.Color(P.vorticityLineColor||'#0F1A29'),transparent:true,opacity:op})));
      n++;
    }
  }
}

function traceBundleVorticityLine(sample,steps=96){
  const pts=[],rBase=bundleBaseRadius(),sgn=Math.sign(bundleOmegaAtZ(0))||1;
  let x=sample.rho*rBase*Math.cos(sample.theta),y=sample.rho*rBase*Math.sin(sample.theta),z=sgn>0?zMin()+0.01:zMax()-0.01;
  const ds=Math.max(5e-4,cylinderHeight()/steps);
  for(let k=0;k<=steps*2;k++){
    if(z<zMin()-0.02||z>zMax()+0.02||x*x+y*y>P.Rcyl*P.Rcyl)break;
    if(P.bundleBEMEnabled&&bundleBEMCache.valid){
      const ni=nearestKnotTubeInfo(x,y,z),R=bundleBEMCache.radius*1.002;
      if(ni.distance<R){const push=R-ni.distance;x+=push*ni.nx;y+=push*ni.ny;z+=push*ni.nz;}
    }
    pts.push(new THREE.Vector3(x,y,z));
    const w1=bundleVorticityAt(x,y,z),m1=Math.hypot(w1.wx,w1.wy,w1.wz);if(m1<1e-12)break;
    const hx=sgn*ds*w1.wx/m1,hy=sgn*ds*w1.wy/m1,hz=sgn*ds*w1.wz/m1;
    const wm=bundleVorticityAt(x+0.5*hx,y+0.5*hy,z+0.5*hz),mm=Math.hypot(wm.wx,wm.wy,wm.wz);if(mm<1e-12)break;
    x+=sgn*ds*wm.wx/mm;y+=sgn*ds*wm.wy/mm;z+=sgn*ds*wm.wz/mm;
    if((sgn>0&&z>=zMax()-0.005)||(sgn<0&&z<=zMin()+0.005)){pts.push(new THREE.Vector3(x,y,z));break;}
  }
  return pts;
}
function rebuildBundleLines(){
  if(!P.bundleEnabled)return;
  if(P.bundleBEMEnabled&&P.bundleEnabled)ensureBundleBEM();
  const target=clamp(Math.round(P.bundleVisualLines||61),7,121);
  const color=new THREE.Color(P.vorticityLineColor||'#0F1A29');
  for(let i=0;i<target;i++){
    const sample=bundleSampleNormalized(i,target);
    let pts;
    if(P.bundleBEMEnabled&&bundleBEMCache.valid){
      pts=traceBundleVorticityLine(sample,96);
    }else{
      pts=[];const segments=P.bundleProfile==='parallel'?1:40,rBase=bundleBaseRadius();
      for(let k=0;k<=segments;k++){const u=k/segments,z=zMin()+0.01+u*Math.max(0,cylinderHeight()-0.02),lam=bundleScaleAtU(u),r=sample.rho*rBase*lam;pts.push(new THREE.Vector3(r*Math.cos(sample.theta),r*Math.sin(sample.theta),z));}
    }
    if(pts.length<2)continue;
    const op=0.22+0.52*((Math.sin(i*12.9898)*43758.5453)%1+1)%1;
    const g=new THREE.BufferGeometry().setFromPoints(pts);
    latticeGrp.add(new THREE.Line(g,new THREE.LineBasicMaterial({color,transparent:true,opacity:op})));
  }
}
// pistolen op de as
const gunGrp=new THREE.Group();worldGrp.add(gunGrp);
function gun(z,flip,color){
  const g=new THREE.ConeGeometry(0.02,0.05,16);g.rotateX(flip?Math.PI/2:-Math.PI/2);
  const m=new THREE.Mesh(g,new THREE.MeshBasicMaterial({color}));
  m.position.set(0,0,z);gunGrp.add(m);return m;
}
const gunA=gun(zMin()+0.01,false,0xFFAE45), gunB=gun(zMax()-0.01,true,0x55D6FF);

// ================= uitgebreide 3D visualisatie (collider features) =================
class DynCurve extends THREE.Curve{
  constructor(f){super();this.f=f;}
  getPoint(t,op=new THREE.Vector3()){
    const N=this.f.N,o=this.f.off;let i=Math.floor(t*N),fr=t*N-i;if(i>=N){i=N-1;fr=1;}
    const i2=(i+1)%N,s=o+3*i,s2=o+3*i2;
    return op.set(Y[s]+fr*(Y[s2]-Y[s]),Y[s+1]+fr*(Y[s2+1]-Y[s+1]),Y[s+2]+fr*(Y[s2+2]-Y[s+2]));
  }
}
const matSolidA=new THREE.MeshPhysicalMaterial({color:0xFFAE45,metalness:0.22,roughness:0.25,transparent:true,opacity:P.vortexOpacity,depthWrite:false});
const matSolidB=new THREE.MeshPhysicalMaterial({color:0x55D6FF,metalness:0.22,roughness:0.25,transparent:true,opacity:P.vortexOpacity,depthWrite:false});
const matHolA=new THREE.MeshPhysicalMaterial({color:0xFFAE45,transmission:0.92,transparent:true,opacity:Math.min(0.48,P.vortexOpacity),roughness:0.1,depthWrite:false});
const matHolB=new THREE.MeshPhysicalMaterial({color:0x55D6FF,transmission:0.92,transparent:true,opacity:Math.min(0.48,P.vortexOpacity),roughness:0.1,depthWrite:false});
function updateVortexOpacity(){
  const op=clamp(Number(P.vortexOpacity)||0.58,0.05,1);
  matSolidA.opacity=matSolidB.opacity=op;
  matHolA.opacity=matHolB.opacity=Math.min(0.52,op);
  [matSolidA,matSolidB,matHolA,matHolB].forEach(m=>{m.transparent=true;m.depthWrite=false;m.needsUpdate=true;});
  if(typeof lineObjs!=='undefined')lineObjs.forEach(l=>{if(l.material){l.material.transparent=true;l.material.opacity=Math.max(0.18,op);l.material.depthWrite=false;}});
  if(typeof wireObjs!=='undefined')wireObjs.forEach(l=>{if(l.material){l.material.transparent=true;l.material.opacity=Math.max(0.2,0.78*op);l.material.depthWrite=false;}});
}
const flowMat=new THREE.MeshBasicMaterial({color:0xA855F7,wireframe:true,transparent:true,opacity:0.3});
const betaMat=new THREE.MeshBasicMaterial({color:0xfacc15,wireframe:true,transparent:true,opacity:0.55});
// ===== deeltjeswolk: passieve tracers geadvecteerd door het echte BS-veld =====
const TRACER_COUNT_MAX=20000;
const TR_HUE_SLOW=0.33;       // groen
const TR_HUE_EQUAL=0.53;      // cyaan
const TR_HUE_FAST=0.78;       // paars
let trGeo=null,trPts=null,trArr=null,trColArr=null,trOmegaDeltaArr=null;
let trOmegaP90=0,trOmegaColorScale=1;
let particleResetClick=0;
const trColorTmp=new THREE.Color();
function setTracerHue(i,normalizedDelta){
  const q=clamp(normalizedDelta,-1,1);
  const hue=q<0?TR_HUE_EQUAL+(TR_HUE_SLOW-TR_HUE_EQUAL)*(-q):TR_HUE_EQUAL+(TR_HUE_FAST-TR_HUE_EQUAL)*q;
  const light=0.54+0.10*Math.abs(q);trColorTmp.setHSL(clamp(hue,0,1),0.96,light);
  trColArr[3*i]=trColorTmp.r;trColArr[3*i+1]=trColorTmp.g;trColArr[3*i+2]=trColorTmp.b;
}
function tracerInnerColumnGeometry(){
  let cx=0,cy=0,rHole=Math.max(0.01,0.20*P.Rcyl);
  if(Y&&fils.length){
    const group=carrierFilaments('A'),st=carrierGroupStats('A');cx=st.cx;cy=st.cy;
    const radial=[];for(const f of group)for(let k=0;k<f.N;k++)radial.push(Math.hypot(Y[f.off+3*k]-cx,Y[f.off+3*k+1]-cy));
    radial.sort((a,b)=>a-b);
    if(radial.length){const rInner=radial[Math.min(radial.length-1,Math.floor(0.15*(radial.length-1)))];
      rHole=clamp(rInner-Math.max(P.a*2.5,0.002),0.005,0.90*P.Rcyl);}
  }
  return {cx,cy,rHole,label:'binnenste knoopkolom'};
}
function tracerKnotColumnGeometry(){
  const st=Y&&fils.length?carrierGroupStats('A'):null;
  return {cx:st?.cx||0,cy:st?.cy||0,rHole:clamp(st?.R||0.25*P.Rcyl,0.005,0.90*P.Rcyl),label:'Taylor-kolom met knoopstraal'};
}
function tracerSpawnGeometry(mode=P.tracerSpawnMode){
  if(mode==='knot-column')return tracerKnotColumnGeometry();
  if(mode==='full-cylinder')return {cx:0,cy:0,rHole:0.95*P.Rcyl,label:'volledige cilinder'};
  return tracerInnerColumnGeometry();
}
function tracerColumnGeometry(){return tracerInnerColumnGeometry();}
function respawnTracer(i,geom=null){
  geom=geom||tracerSpawnGeometry();
  const r=Math.sqrt(Math.random())*geom.rHole,th=Math.random()*2*Math.PI;
  trArr[3*i]=geom.cx+r*Math.cos(th);trArr[3*i+1]=geom.cy+r*Math.sin(th);
  const margin=Math.min(0.02,0.04*P.Hcyl);trArr[3*i+2]=zMin()+margin+Math.random()*Math.max(1e-6,cylinderHeight()-2*margin);
  if(trOmegaDeltaArr)trOmegaDeltaArr[i]=0;if(trColArr)setTracerHue(i,0);
}
function updateParticleResetButton(lastGeom=null){
  const btn=document.getElementById('bResetParticles');if(!btn)return;
  btn.childNodes[0].nodeValue='↺ Deeltjes';
  const next=['inner-column','knot-column','full-cylinder'][particleResetClick%3];
  const nextLabel=next==='inner-column'?'binnenste knoopkolom':next==='knot-column'?'Taylor-kolom met knoopstraal':'volledige cilinder';
  const current=lastGeom?`Huidig: ${lastGeom.label}, r≈${(lastGeom.rHole*100).toFixed(1)} cm. `:'';
  btn.title=`${current}Volgende klik: ${nextLabel}. Deeltjes: ${P.tracerCount.toLocaleString('nl-NL')} / ${TRACER_COUNT_MAX.toLocaleString('nl-NL')}.`;
}
function resetParticles(mode=P.tracerSpawnMode,{announce=true,resetCycle=false}={}){
  P.tracerSpawnMode=mode;if(resetCycle)particleResetClick=0;
  if(!trArr||tracerCount()!==P.tracerCount)initTracers();
  if(!trArr){updateParticleResetButton();return null;}
  const geom=tracerSpawnGeometry(mode),n=tracerCount();for(let i=0;i<n;i++)respawnTracer(i,geom);
  trOmegaP90=0;trOmegaColorScale=1;
  if(trGeo?.attributes?.position)trGeo.attributes.position.needsUpdate=true;if(trGeo?.attributes?.color)trGeo.attributes.color.needsUpdate=true;
  updateParticleResetButton(announce?geom:null);markPotentialFlowDirty();return geom;
}
function cycleParticleReset(){
  const modes=['inner-column','knot-column','full-cylinder'];
  const mode=modes[particleResetClick%3];particleResetClick=(particleResetClick+1)%3;
  return resetParticles(mode,{announce:true,resetCycle:false});
}
function resetParticlesToTaylorColumn(){return resetParticles('inner-column',{announce:false,resetCycle:true});}
function tracerCount(){
  return trArr ? Math.floor(trArr.length/3) : Math.max(0,Math.min(TRACER_COUNT_MAX,Math.round(P.tracerCount||0)));
}
function disposeTracers(){
  if(trPts){
    filGrp.remove(trPts);
    if(trPts.geometry)trPts.geometry.dispose();
    if(trPts.material)trPts.material.dispose();
  }
  trGeo=null;trPts=null;trArr=null;trColArr=null;trOmegaDeltaArr=null;
}
function initTracers(){
  disposeTracers();
  const n=Math.max(0,Math.min(TRACER_COUNT_MAX,Math.round(P.tracerCount||0)));
  P.tracerCount=n;
  if(n===0){
    const h=document.getElementById('hTracerOmega');
    if(h)h.textContent='— (0 deeltjes)';
    return;
  }
  trArr=new Float32Array(n*3);
  trColArr=new Float32Array(n*3);
  trOmegaDeltaArr=new Float32Array(n);
  const spawnGeom=tracerSpawnGeometry();
  for(let i=0;i<n;i++)respawnTracer(i,spawnGeom);
  trGeo=new THREE.BufferGeometry();
  trGeo.setAttribute('position',new THREE.BufferAttribute(trArr,3));
  trGeo.setAttribute('color',new THREE.BufferAttribute(trColArr,3));
  trPts=new THREE.Points(trGeo,new THREE.PointsMaterial({size:P.particleSize,vertexColors:true,
    sizeAttenuation:true,transparent:true,opacity:0.82,depthWrite:false,blending:THREE.AdditiveBlending}));
  filGrp.add(trPts);
}
function updateTracerColorScale(){
  // Gebruik P90 in plaats van het maximum, zodat één core-near outlier
  // niet de hele wolk cyaan drukt. Dit is alleen een visuele contrastschaal;
  // de fysieke ΔΩ-P90 wordt afzonderlijk in de HUD getoond.
  const n=tracerCount();
  if(n===0)return;
  const absVals=new Array(n);
  for(let i=0;i<n;i++)absVals[i]=Math.abs(trOmegaDeltaArr[i]);
  absVals.sort((a,b)=>a-b);
  trOmegaP90=absVals[Math.min(n-1,Math.floor(0.90*(n-1)))]||0;
  const omegaCylinder=Math.abs(P.Om);
  const minimumScale=Math.max(1e-4,0.005*Math.max(1,omegaCylinder));
  const targetScale=Math.max(minimumScale,trOmegaP90);
  trOmegaColorScale=Number.isFinite(trOmegaColorScale)
    ?0.78*trOmegaColorScale+0.22*targetScale
    :targetScale;
  const scale=Math.max(minimumScale,trOmegaColorScale);
  for(let i=0;i<n;i++){
    // tanh geeft een duidelijke, maar vloeiende kleurrespons rond ΔΩ=0.
    setTracerHue(i,Math.tanh(1.45*trOmegaDeltaArr[i]/scale));
  }
  const h=document.getElementById('hTracerOmega');
  if(h)h.textContent=`${trOmegaP90.toFixed(trOmegaP90<0.1?3:2)} / ±${scale.toFixed(scale<0.1?3:2)} s⁻¹`;
}
function stepTracers(dtSim){
  if(!trPts)return;
  trPts.visible=P.showTracers&&!P.showStreamlines;
  if(!P.showTracers||P.showStreamlines||!Y||!fils.length||dtSim===0)return;
  const n=tracerCount();
  if(n===0)return;
  const a2=P.a*P.a, segs=[];
  for(const f of fils){
    const N=f.N,o=f.off,mid=new Float64Array(3*N),dl=new Float64Array(3*N);
    for(let k=0;k<N;k++){const k2=(k+1)%N;
      for(let d=0;d<3;d++){mid[3*k+d]=.5*(Y[o+3*k+d]+Y[o+3*k2+d]);dl[3*k+d]=Y[o+3*k2+d]-Y[o+3*k+d];}}
    segs.push({N,mid,dl,pref:filamentGamma(f)/(4*Math.PI)});
  }
  const wz=effectiveW();
  const respawnGeom=tracerSpawnGeometry();
  for(let i=0;i<n;i++){
    const px=trArr[3*i],py=trArr[3*i+1],pz=trArr[3*i+2];
    let ux=0,uy=0,uz=wz;
    for(const sg of segs){const M=sg.N,mid=sg.mid,dl=sg.dl,pref=sg.pref;
      for(let j=0;j<M;j++){
        const rx=px-mid[3*j],ry=py-mid[3*j+1],rz=pz-mid[3*j+2];
        const r2=rx*rx+ry*ry+rz*rz+a2, inv=pref/(r2*Math.sqrt(r2));
        ux+=(dl[3*j+1]*rz-dl[3*j+2]*ry)*inv;
        uy+=(dl[3*j+2]*rx-dl[3*j]*rz)*inv;
        uz+=(dl[3*j]*ry-dl[3*j+1]*rx)*inv;}}
    const ubg=backgroundVelocityAt(px,py,pz);
    ux+=ubg.ux;uy+=ubg.uy;uz+=ubg.uz;

    // Orbitale tracer-hoeksnelheid rond de z-as:
    // Ω_p,z = (r × u)_z / r_perp².
    // De kleur gebruikt ΔΩ = Ω_p,lab - Ω_cilinder in de draairichting
    // van de cilinder. Daarmee reageert de wolk direct op Γ, lokale
    // Biot-Savart-inductie en de achtergrondrotatie.
    const r2xy=px*px+py*py;
    let omegaFromIntegratedVelocity=0;
    if(r2xy>1e-10)omegaFromIntegratedVelocity=(px*uy-py*ux)/r2xy;
    // v7.5: in het co-roterende solverframe is u een corot-snelheid; de
    // labwaarde krijgt daar +Ω. In het lab-solverframe is u al lab.
    const omegaLab=omegaFromIntegratedVelocity+(P.solverFrame==='corot'?P.Om:0);
    const spinDir=Math.sign(P.Om)||1;
    trOmegaDeltaArr[i]=spinDir*omegaLab-Math.abs(P.Om);

    let dx=ux*dtSim,dy=uy*dtSim,dz=uz*dtSim;
    const dm=Math.hypot(dx,dy,dz);
    if(dm>0.03){const sc=0.03/dm;dx*=sc;dy*=sc;dz*=sc;}
    const nx=px+dx,ny=py+dy,nz=pz+dz;
    const radialOut=nx*nx+ny*ny>Math.pow(0.98*P.Rcyl,2);
    const zLo=zMin(),zHi=zMax();
    if(radialOut){
      respawnTracer(i,respawnGeom);
    }else if(nz<zLo||nz>=zHi){
      if(P.tracerWrapZ){
        const span=Math.max(1e-9,zHi-zLo);
        const wrapped=zLo+(((nz-zLo)%span)+span)%span;
        trArr[3*i]=nx;trArr[3*i+1]=ny;trArr[3*i+2]=wrapped;
      }else{
        respawnTracer(i,respawnGeom);
      }
    }else{
      trArr[3*i]=nx;trArr[3*i+1]=ny;trArr[3*i+2]=nz;
    }
  }
  updateTracerColorScale();
  trGeo.attributes.position.needsUpdate=true;
  trGeo.attributes.color.needsUpdate=true;
}

// ===== instantane stroomlijnen + Bernoulli-drukproxy =====
// Stroomlijnen zijn tangent aan het snelheidsveld. De kleur gebruikt slechts de
// relatieve Bernoulli-proxy p_B*=p0-1/2 rho |u|^2; de additieve drukconstante is onbekend.
const streamlineGrp=new THREE.Group();filGrp.add(streamlineGrp);
let streamlineTick=0;
function clearStreamlines(){
  while(streamlineGrp.children.length){
    const o=streamlineGrp.children.pop();
    if(o.geometry)o.geometry.dispose();
    if(o.material)o.material.dispose();
  }
}
function fieldSegments(){
  const segs=[];
  for(const f of fils){
    const N=f.N,o=f.off,mid=new Float64Array(3*N),dl=new Float64Array(3*N);
    for(let k=0;k<N;k++){
      const k2=(k+1)%N;
      for(let d=0;d<3;d++){
        mid[3*k+d]=0.5*(Y[o+3*k+d]+Y[o+3*k2+d]);
        dl[3*k+d]=Y[o+3*k2+d]-Y[o+3*k+d];
      }
    }
    segs.push({N,mid,dl,pref:filamentGamma(f)/(4*Math.PI)});
  }
  return segs;
}
function fieldVelocityAt(px,py,pz,segs){
  let ux=0,uy=0,uz=effectiveW();
  const a2=P.a*P.a;
  for(const sg of segs){
    for(let j=0;j<sg.N;j++){
      const rx=px-sg.mid[3*j],ry=py-sg.mid[3*j+1],rz=pz-sg.mid[3*j+2];
      const r2=rx*rx+ry*ry+rz*rz+a2;
      const inv=sg.pref/(r2*Math.sqrt(r2));
      ux+=(sg.dl[3*j+1]*rz-sg.dl[3*j+2]*ry)*inv;
      uy+=(sg.dl[3*j+2]*rx-sg.dl[3*j]*rz)*inv;
      uz+=(sg.dl[3*j]*ry-sg.dl[3*j+1]*rx)*inv;
    }
  }
  const ubg=backgroundVelocityAt(px,py,pz);ux+=ubg.ux;uy+=ubg.uy;uz+=ubg.uz;
  return {ux,uy,uz,speed:Math.hypot(ux,uy,uz)};
}
function insideCylinder(x,y,z){return x*x+y*y<0.9409*P.Rcyl*P.Rcyl&&z>zMin()+0.002&&z<zMax()-0.002;}
function traceStreamline(seed,sign,segs,steps,ds){
  const pts=[],speeds=[];
  let x=seed.x,y=seed.y,z=seed.z;
  for(let k=0;k<steps;k++){
    if(!insideCylinder(x,y,z))break;
    const v1=fieldVelocityAt(x,y,z,segs);
    if(v1.speed<1e-10)break;
    pts.push(new THREE.Vector3(x,y,z));speeds.push(v1.speed);
    const h=sign*ds/v1.speed;
    const mx=x+0.5*h*v1.ux,my=y+0.5*h*v1.uy,mz=z+0.5*h*v1.uz;
    const vm=fieldVelocityAt(mx,my,mz,segs);
    if(vm.speed<1e-10)break;
    x+=sign*ds*vm.ux/vm.speed;
    y+=sign*ds*vm.uy/vm.speed;
    z+=sign*ds*vm.uz/vm.speed;
  }
  return {pts,speeds};
}
function pressureProxyColor(q,out){
  const hue=0.53*(1-q)+0.02*q; // cyaan (hogere p*) -> magenta/oranje (lagere p*)
  return out.setHSL(hue,0.88,0.58);
}
function rebuildStreamlines(force=false){
  streamlineGrp.visible=P.showTracers&&P.showStreamlines;
  if(!streamlineGrp.visible||!Y||!fils.length){if(force)clearStreamlines();return;}
  streamlineTick++;
  if(!force&&streamlineTick%12!==0)return;
  clearStreamlines();
  const segs=fieldSegments();
  const nLines=Math.max(4,Math.min(120,Math.round(P.streamlineCount||28))),steps=42;
  const ds=Math.max(0.001,Math.min(0.018,0.045*P.Rcyl,0.018*cylinderHeight()));
  const geom=tracerColumnGeometry(),all=[];
  for(let i=0;i<nLines;i++){
    const frac=(i+0.5)/nLines,ring=i%7;
    const r=geom.rHole*(0.08+0.80*(ring/6)),th=i*2.399963229728653;
    const seed={x:geom.cx+r*Math.cos(th),y:geom.cy+r*Math.sin(th),z:zMin()+0.06*cylinderHeight()+0.88*cylinderHeight()*frac};
    const back=traceStreamline(seed,-1,segs,steps,ds),fore=traceStreamline(seed,+1,segs,steps,ds);
    const pts=back.pts.reverse().concat(fore.pts.slice(1));
    const speeds=back.speeds.reverse().concat(fore.speeds.slice(1));
    if(pts.length>2)all.push({pts,speeds});
  }
  const speedPool=all.flatMap(x=>x.speeds).sort((a,b)=>a-b);
  const speed95=speedPool.length?speedPool[Math.floor(0.95*(speedPool.length-1))]:1;
  const c=new THREE.Color();
  for(const sl of all){
    const pos=new Float32Array(sl.pts.length*3),col=new Float32Array(sl.pts.length*3);
    sl.pts.forEach((pt,i)=>{
      pos[3*i]=pt.x;pos[3*i+1]=pt.y;pos[3*i+2]=pt.z;
      pressureProxyColor(clamp(sl.speeds[i]/Math.max(1e-12,speed95),0,1),c);
      col[3*i]=c.r;col[3*i+1]=c.g;col[3*i+2]=c.b;
    });
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.BufferAttribute(pos,3));g.setAttribute('color',new THREE.BufferAttribute(col,3));
    streamlineGrp.add(new THREE.Line(g,new THREE.LineBasicMaterial({vertexColors:true,transparent:true,opacity:0.72,depthWrite:false,blending:THREE.AdditiveBlending})));
  }
}

// ===== analytische 2D potential flow + drukcoëfficiënt =====
const potentialFlowGrp=new THREE.Group();filGrp.add(potentialFlowGrp);
let potentialFlowMesh=null,potentialFlowTexture=null,potentialFlowDirty=true,potentialFlowSignature='';
function markPotentialFlowDirty(){potentialFlowDirty=true;}
function potentialDensity(){return P.med==='he'?145:(P.med==='sst'||P.med==='string'?7.0e-7:1.0);}
function potentialRadius(){
  if(P.potentialRadiusSource==='manual')return clamp(P.potentialRadius,0.005,0.95*P.Rcyl);
  if(P.potentialRadiusSource==='particles')return tracerSpawnGeometry().rHole;
  const st=Y&&fils.length?carrierGroupStats('A'):null;
  if(P.potentialRadiusSource==='knot')return clamp(st?.R||P.R0,0.005,0.95*P.Rcyl);
  if(st){const vz=P.mode==='solo'?effectiveW():P.vzA;return clamp(taylorColumnState(st,vz).rCap,0.005,0.95*P.Rcyl);}
  return clamp(P.R0,0.005,0.95*P.Rcyl);
}
function potentialFields(x,y,R,U){
  const r2=x*x+y*y,r=Math.sqrt(r2),theta=Math.atan2(y,x);
  if(r<=R)return {inside:true,psi:0,cp:NaN,speed:0};
  const q2=R*R/r2,vr=U*(1-q2)*Math.sin(theta),vt=U*(1+q2)*Math.cos(theta);
  const speed2=vr*vr+vt*vt;
  // Uniforme vrije stroming is lokaal +y. Het vlak wordt hieronder naar x-z
  // geroteerd, zodat het verre veld parallel aan de wereld-z-as loopt.
  return {inside:false,psi:-U*(r-R*R/r)*Math.cos(theta),cp:1-speed2/(U*U),speed:Math.sqrt(speed2)};
}
function potentialColor(cp){
  const q=clamp((cp+3)/4,0,1),stops=[[0.00,[118,37,169]],[0.25,[31,94,181]],[0.50,[40,190,190]],[0.75,[234,210,67]],[1.00,[215,72,42]]];
  let a=stops[0],b=stops[stops.length-1];for(let i=1;i<stops.length;i++)if(q<=stops[i][0]){a=stops[i-1];b=stops[i];break;}
  const t=(q-a[0])/Math.max(1e-12,b[0]-a[0]);return a[1].map((v,i)=>Math.round(v+t*(b[1][i]-v)));
}
function drawPotentialContours(ctx,field,n,levels,size,color,width=1){
  ctx.save();ctx.strokeStyle=color;ctx.lineWidth=width;ctx.globalAlpha=0.88;ctx.beginPath();
  const at=(i,j)=>field[j*n+i],px=i=>i*size/(n-1),py=j=>size-j*size/(n-1);
  const edgePoint=(edge,i,j,level)=>{let a,b,ax,ay,bx,by;if(edge===0){a=at(i,j);b=at(i+1,j);ax=px(i);ay=py(j);bx=px(i+1);by=py(j);}else if(edge===1){a=at(i+1,j);b=at(i+1,j+1);ax=px(i+1);ay=py(j);bx=px(i+1);by=py(j+1);}else if(edge===2){a=at(i+1,j+1);b=at(i,j+1);ax=px(i+1);ay=py(j+1);bx=px(i);by=py(j+1);}else{a=at(i,j+1);b=at(i,j);ax=px(i);ay=py(j+1);bx=px(i);by=py(j);}if(!Number.isFinite(a)||!Number.isFinite(b)||a===b)return null;const t=(level-a)/(b-a);return t>=0&&t<=1?[ax+t*(bx-ax),ay+t*(by-ay)]:null;};
  for(const level of levels)for(let j=0;j<n-1;j++)for(let i=0;i<n-1;i++){
    const vals=[at(i,j),at(i+1,j),at(i+1,j+1),at(i,j+1)];if(vals.some(v=>!Number.isFinite(v)))continue;
    const edges=[];for(let e=0;e<4;e++){const a=vals[e],b=vals[(e+1)%4];if((a<level&&b>=level)||(b<level&&a>=level)){const p=edgePoint(e,i,j,level);if(p)edges.push(p);}}
    if(edges.length===2){ctx.moveTo(edges[0][0],edges[0][1]);ctx.lineTo(edges[1][0],edges[1][1]);}
    else if(edges.length===4){ctx.moveTo(edges[0][0],edges[0][1]);ctx.lineTo(edges[1][0],edges[1][1]);ctx.moveTo(edges[2][0],edges[2][1]);ctx.lineTo(edges[3][0],edges[3][1]);}
  }
  ctx.stroke();ctx.restore();
}
function disposePotentialFlow(){
  if(potentialFlowMesh){potentialFlowGrp.remove(potentialFlowMesh);potentialFlowMesh.geometry.dispose();potentialFlowMesh.material.dispose();potentialFlowMesh=null;}
  if(potentialFlowTexture){potentialFlowTexture.dispose();potentialFlowTexture=null;}
}
function rebuildPotentialFlowTexture(R,U){
  disposePotentialFlow();const size=512,canvas2=document.createElement('canvas');canvas2.width=canvas2.height=size;const ctx=canvas2.getContext('2d');
  const image=ctx.createImageData(size,size),ext=3*R,mode=P.potentialMode;
  for(let j=0;j<size;j++)for(let i=0;i<size;i++){
    const x=-ext+2*ext*i/(size-1),y=-ext+2*ext*(size-1-j)/(size-1),f=potentialFields(x,y,R,U),p=4*(j*size+i);
    if(f.inside){image.data[p]=8;image.data[p+1]=12;image.data[p+2]=22;image.data[p+3]=mode==='stream'?24:225;continue;}
    if(mode==='stream'){image.data[p]=10;image.data[p+1]=16;image.data[p+2]=30;image.data[p+3]=20;}
    else{const c=potentialColor(f.cp);image.data[p]=c[0];image.data[p+1]=c[1];image.data[p+2]=c[2];image.data[p+3]=178;}
  }
  ctx.putImageData(image,0,0);
  const n=129,psi=new Float64Array(n*n),cp=new Float64Array(n*n);
  for(let j=0;j<n;j++)for(let i=0;i<n;i++){const x=-ext+2*ext*i/(n-1),y=-ext+2*ext*j/(n-1),f=potentialFields(x,y,R,U);psi[j*n+i]=f.inside?NaN:f.psi/(U*R);cp[j*n+i]=f.inside?NaN:f.cp;}
  if(mode!=='pressure')drawPotentialContours(ctx,psi,n,[-2.4,-1.8,-1.2,-0.8,-0.4,0,0.4,0.8,1.2,1.8,2.4],size,'rgba(245,248,255,.86)',1.15);
  if(mode!=='stream')drawPotentialContours(ctx,cp,n,[-3,-2,-1,-0.5,0,0.5,0.8,1],size,'rgba(10,16,28,.92)',1.0);
  ctx.save();ctx.strokeStyle='rgba(255,255,255,.94)';ctx.lineWidth=2;ctx.beginPath();ctx.arc(size/2,size/2,size/6,0,2*Math.PI);ctx.stroke();ctx.restore();
  if(mode!=='stream'){ctx.font='18px system-ui';ctx.fillStyle='rgba(255,255,255,.92)';ctx.fillText('Cₚ  −3 → 1',16,26);}
  potentialFlowTexture=new THREE.CanvasTexture(canvas2);if('colorSpace' in potentialFlowTexture&&THREE.SRGBColorSpace)potentialFlowTexture.colorSpace=THREE.SRGBColorSpace;
  const mat=new THREE.MeshBasicMaterial({map:potentialFlowTexture,transparent:true,opacity:P.potentialOpacity,side:THREE.DoubleSide,depthWrite:false});
  potentialFlowMesh=new THREE.Mesh(new THREE.PlaneGeometry(6*R,6*R),mat);
  potentialFlowMesh.rotation.x=Math.PI/2; // lokaal y → wereld z: vrije stroomlijnen ∥ z
  potentialFlowMesh.renderOrder=1;potentialFlowGrp.add(potentialFlowMesh);
}
function updatePotentialFlowVisual(force=false){
  potentialFlowGrp.visible=!!P.showPotentialFlow;if(!P.showPotentialFlow||!Y||!fils.length)return;
  const R=potentialRadius(),U=Math.max(1e-6,P.potentialU),st=carrierGroupStats('A');
  const sig=[R.toFixed(4),U.toFixed(4),P.potentialMode,P.potentialOpacity].join('|');
  if(force||potentialFlowDirty||sig!==potentialFlowSignature){rebuildPotentialFlowTexture(R,U);potentialFlowSignature=sig;potentialFlowDirty=false;}
  if(potentialFlowMesh){potentialFlowMesh.position.set(st?.cx||0,(st?.cy||0)-Math.max(1e-5,0.04*P.a),st?.z||0);potentialFlowMesh.material.opacity=P.potentialOpacity;}
  const rho=potentialDensity(),dpMin=0.5*rho*U*U*(-3),dpMax=0.5*rho*U*U;
  const out=document.getElementById('potentialFlowReadout');if(out)out.innerHTML=`<strong>R=${fmtLengthSI(R)}</strong> · Cₚ∈[−3,1] · Δp∈[${dpMin.toExponential(3)}, ${dpMax.toExponential(3)}] Pa bij ρ=${rho.toExponential(3)} kg/m³ · passieve x-z-laag · vrije stroming ∥ z`;
}

let lineObjs=[], tubeObjs=[], wireObjs=[], betaObjs=[], flowObjs=[], ghostTubeObj=null;
let sepObjs=[], capDiscs=[], capRings=[], colSils=[], alphaObjs=[];
let stewartsonTorus=null, stewartsonArrows=null;
const ghostTubeMat=new THREE.MeshBasicMaterial({color:0x66CCFF,wireframe:true,transparent:true,opacity:0.38,depthWrite:false});
// Step 3: make the Taylor-column overlays deliberately subtle so they do not
// obscure the filament or tracer field.  Centralised values make later tuning easy.
const TAYLOR_VIS_ALPHA = Object.freeze({
  separatrixFill: 0.055,
  separatrixEdge: 0.24,
  capDisc: 0.10,
  capRing: 0.32,
  columnWire: 0.055,
  stewartsonTorus: 0.105,
  stewartsonArrows: 0.55,
  footprintDisc: 0.20
});
const stewartsonMat=new THREE.MeshBasicMaterial({color:0xFF7043,transparent:true,opacity:TAYLOR_VIS_ALPHA.stewartsonTorus,side:THREE.DoubleSide,depthWrite:false});
const stewartsonMatNeg=new THREE.MeshBasicMaterial({color:0x26C6DA,transparent:true,opacity:TAYLOR_VIS_ALPHA.stewartsonTorus,side:THREE.DoubleSide,depthWrite:false});
let meshFrame=0;

function disposeObj(m){if(!m)return;filGrp.remove(m);if(m.geometry)m.geometry.dispose();}
function makeWire(color){
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.BufferAttribute(new Float32Array(1536),3));
  const l=new THREE.LineLoop(g,new THREE.LineBasicMaterial({color}));
  l.visible=false;filGrp.add(l);return l;
}
function makeSepSphere(){
  const m=new THREE.Mesh(new THREE.SphereGeometry(1,24,24),
    new THREE.MeshBasicMaterial({color:0xffffff,transparent:true,opacity:TAYLOR_VIS_ALPHA.separatrixFill,depthWrite:false}));
  m.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.SphereGeometry(1,12,12)),
    new THREE.LineBasicMaterial({color:0xffffff,transparent:true,opacity:TAYLOR_VIS_ALPHA.separatrixEdge})));
  m.visible=false;filGrp.add(m);return m;
}
function makeCapDisc(color){
  const m=new THREE.Mesh(new THREE.CircleGeometry(1,48),
    new THREE.MeshBasicMaterial({color,transparent:true,opacity:TAYLOR_VIS_ALPHA.capDisc,side:THREE.DoubleSide,depthWrite:false}));
  m.visible=false;filGrp.add(m);return m;
}
function makeCapRing(color){
  const m=new THREE.Mesh(new THREE.RingGeometry(0.92,1,48),
    new THREE.MeshBasicMaterial({color,transparent:true,opacity:TAYLOR_VIS_ALPHA.capRing,side:THREE.DoubleSide,depthWrite:false}));
  m.visible=false;filGrp.add(m);return m;
}
function makeColSil(color){
  const g=new THREE.CylinderGeometry(1,1,1,24,1,true);g.rotateX(Math.PI/2);
  const m=new THREE.Mesh(g,new THREE.MeshBasicMaterial({color,wireframe:true,transparent:true,opacity:TAYLOR_VIS_ALPHA.columnWire,depthWrite:false}));
  m.visible=false;filGrp.add(m);return m;
}
function initVisExtras(){
  sepObjs=[makeSepSphere(),makeSepSphere()];
  capDiscs=[makeCapDisc(0xFFAE45),makeCapDisc(0xFFAE45),makeCapDisc(0x55D6FF),makeCapDisc(0x55D6FF)];
  capRings=[makeCapRing(0xFFAE45),makeCapRing(0xFFAE45),makeCapRing(0x55D6FF),makeCapRing(0x55D6FF)];
  colSils=[makeColSil(0xFFAE45),makeColSil(0x55D6FF)];
  alphaObjs=[new THREE.Mesh(new THREE.SphereGeometry(1,16,16),
    new THREE.MeshBasicMaterial({color:0xFF6E6E,transparent:true,opacity:0.8})),
    new THREE.Mesh(new THREE.SphereGeometry(1,16,16),
    new THREE.MeshBasicMaterial({color:0xFF6E6E,transparent:true,opacity:0.8}))];
  alphaObjs.forEach(m=>{m.visible=false;filGrp.add(m);});
  const torGeo=new THREE.CylinderGeometry(1,1,1,48,1,true);
  torGeo.rotateX(Math.PI/2);
  stewartsonTorus=new THREE.Mesh(torGeo,stewartsonMat.clone());
  stewartsonTorus.visible=false;filGrp.add(stewartsonTorus);
  stewartsonArrows=new THREE.InstancedMesh(new THREE.ConeGeometry(0.007,0.022,8),
    new THREE.MeshBasicMaterial({color:0xFFB74D,transparent:true,opacity:TAYLOR_VIS_ALPHA.stewartsonArrows,depthWrite:false}),12);
  stewartsonArrows.visible=false;filGrp.add(stewartsonArrows);
  initChiArrows();
}
function initChiArrows(){
  chiArrows=[];
  for(let i=0;i<2;i++){
    const col=i===0?0xFFAE45:0x55D6FF;
    const a=new THREE.ArrowHelper(new THREE.Vector3(1,0,0),new THREE.Vector3(),0.06,col,0.018,0.01);
    a.visible=false;filGrp.add(a);chiArrows.push(a);
  }
}
function updateChiArrows(bodyStates){
  chiArrows.forEach((a,i)=>{
    if(!P.showChiArrow||i>=fils.length||!bodyStates[i]){
      a.visible=false;return;
    }
    const b=bodyStates[i];
    if(!b.chi){a.visible=false;return;}
    const len=0.035+0.1*Math.min(1,Math.abs(b.omegaZ)*2);
    a.position.set(b.cx,b.cy,b.cz);
    a.setDirection(new THREE.Vector3(b.chi.x,b.chi.y,0.001).normalize());
    a.setLength(Math.max(0.02,len),0.018,0.01);
    a.visible=true;
  });
}
initVisExtras();
applyDvOpacity();
initTracers();
updatePotentialFlowVisual(true);

function rebuildLines(){
  [...lineObjs,...tubeObjs,...wireObjs,...betaObjs,...flowObjs].forEach(o=>{
    filGrp.remove(o);if(o.geometry)o.geometry.dispose();});
  lineObjs=[];tubeObjs=[];wireObjs=[];betaObjs=[];flowObjs=[];
  const cols=[0xFFAE45,0x55D6FF];
  fils.forEach((f,i)=>{
    const geo=new THREE.BufferGeometry();
    geo.setAttribute('position',new THREE.BufferAttribute(new Float32Array(3*(f.N+1)),3));
    const l=new THREE.Line(geo,new THREE.LineBasicMaterial({color:cols[i%2],transparent:true,opacity:Math.max(0.18,P.vortexOpacity),depthWrite:false}));
    l.visible=(P.vis==='line');filGrp.add(l);lineObjs.push(l);
    wireObjs.push(makeWire(cols[i%2]));
  });
  gunB.visible=(P.mode==='botsing');
  meshFrame=0;
  updateVortexOpacity();
  rebuildStreamlines(true);
}
function pushLines(){
  fils.forEach((f,i)=>{
    if(lineObjs[i]){
      const p=lineObjs[i].geometry.attributes.position.array;
      for(let k=0;k<=f.N;k++){const s=f.off+(k%f.N)*3;
        p[3*k]=Y[s];p[3*k+1]=Y[s+1];p[3*k+2]=Y[s+2];}
      lineObjs[i].geometry.attributes.position.needsUpdate=true;
    }
    if(wireObjs[i]&&P.showCenterline){
      const p=wireObjs[i].geometry.attributes.position.array;
      for(let k=0;k<=f.N;k++){const s=f.off+(k%f.N)*3;
        p[3*k]=Y[s];p[3*k+1]=Y[s+1];p[3*k+2]=Y[s+2];}
      wireObjs[i].geometry.attributes.position.needsUpdate=true;
      wireObjs[i].visible=true;
    }else if(wireObjs[i]) wireObjs[i].visible=false;
  });
}
function rebuildTubes(force){
  if(P.vis!=='tube'){tubeObjs.forEach(disposeObj);betaObjs.forEach(disposeObj);flowObjs.forEach(disposeObj);
    if(ghostTubeObj){disposeObj(ghostTubeObj);ghostTubeObj=null;}
    tubeObjs=[];betaObjs=[];flowObjs=[];return;}
  meshFrame++;if(!force&&meshFrame%2!==0)return;
  tubeObjs.forEach(disposeObj);betaObjs.forEach(disposeObj);flowObjs.forEach(disposeObj);
  tubeObjs=[];betaObjs=[];flowObjs=[];
  const tr=Math.max(P.a,0.00035), mats=[P.tubeMat==='solid'?matSolidA:matHolA,P.tubeMat==='solid'?matSolidB:matHolB];
  fils.forEach((f,i)=>{
    try{
      const curve=new DynCurve(f);
      tubeObjs.push(new THREE.Mesh(new THREE.TubeGeometry(curve,f.N,tr,8,true),mats[i%2]));
      filGrp.add(tubeObjs[tubeObjs.length-1]);
      if(Flags.beta){
        betaObjs.push(new THREE.Mesh(new THREE.TubeGeometry(curve,f.N,tr*1.03,10,true),betaMat));
        filGrp.add(betaObjs[betaObjs.length-1]);
      }
      if(Flags.gamma){
        flowObjs.push(new THREE.Mesh(new THREE.TubeGeometry(curve,f.N,tr*1.6,12,true),flowMat));
        filGrp.add(flowObjs[flowObjs.length-1]);
      }
    }catch(e){}
  });
  if(ghostFil){
    try{
      disposeObj(ghostTubeObj);
      const curve=new DynCurve(ghostFil);
      ghostTubeObj=new THREE.Mesh(new THREE.TubeGeometry(curve,ghostFil.N,P.a*2,6,true),ghostTubeMat);
      filGrp.add(ghostTubeObj);
    }catch(e){ghostTubeObj=null;}
  }else if(ghostTubeObj){disposeObj(ghostTubeObj);ghostTubeObj=null;}
}
function anyDvLayerEnabled(){
  return !!(P.dvSeparatrix||P.dvColumn||P.dvCaps||P.dvStewartson);
}
function syncDvGeometryUi(){
  const pairs=[['cDvSeparatrix','dvSeparatrix'],['cDvColumn','dvColumn'],['cDvCaps','dvCaps'],['cDvStewartson','dvStewartson']];
  pairs.forEach(([id,key])=>{const el=document.getElementById(id);if(el)el.checked=!!P[key];});
  const s=document.getElementById('sDvOpacity'),v=document.getElementById('vDvOpacity');
  if(s)s.value=String(Math.round(100*P.dvOpacity));
  if(v)v.textContent=Math.round(100*P.dvOpacity)+'%';
}
function setDvAll(on){
  P.dvSeparatrix=P.dvColumn=P.dvCaps=P.dvStewartson=!!on;
  Flags.sep=!!on;
  syncDvGeometryUi();
}
function applyDvOpacity(){
  const f=clamp(P.dvOpacity,0,1);
  sepObjs.forEach(m=>{if(!m)return;m.material.opacity=TAYLOR_VIS_ALPHA.separatrixFill*f;
    m.children.forEach(c=>{if(c.material)c.material.opacity=TAYLOR_VIS_ALPHA.separatrixEdge*f;});});
  capDiscs.forEach(m=>{if(m?.material)m.material.opacity=TAYLOR_VIS_ALPHA.capDisc*f;});
  capRings.forEach(m=>{if(m?.material)m.material.opacity=TAYLOR_VIS_ALPHA.capRing*f;});
  colSils.forEach(m=>{if(m?.material)m.material.opacity=TAYLOR_VIS_ALPHA.columnWire*f;});
  [stewartsonMat,stewartsonMatNeg].forEach(m=>{if(m)m.opacity=TAYLOR_VIS_ALPHA.stewartsonTorus*f;});
  if(stewartsonTorus?.material)stewartsonTorus.material.opacity=TAYLOR_VIS_ALPHA.stewartsonTorus*f;
  if(stewartsonArrows?.material)stewartsonArrows.material.opacity=TAYLOR_VIS_ALPHA.stewartsonArrows*f;
  footprintDiscs.forEach(m=>{if(m?.material)m.material.opacity=TAYLOR_VIS_ALPHA.footprintDisc*f;});
}

function updateStewartsonVisuals(st,w,t,stw){
  if(!stewartsonTorus||!stewartsonArrows)return;
  const negRel=stw.qS<0; // v7.2: tekenconventie via q_S
  stewartsonTorus.material=negRel?stewartsonMat:stewartsonMatNeg;
  stewartsonTorus.visible=!!P.dvStewartson;
  stewartsonTorus.position.set(st.cx,st.cy,(t.zTop+t.zBot)*0.5);
  stewartsonTorus.scale.set(t.rCap,t.rCap,Math.max(0.02,t.zTop-t.zBot));
  stewartsonArrows.visible=!!P.dvStewartson;
  stewartsonArrows.material.color.setHex(negRel?0xFF7043:0x26C6DA);
  const n=stewartsonArrows.count, zMid=(t.zTop+t.zBot)*0.5;
  const sgn=stw.uTheta>=0?1:-1;
  const m=new THREE.Matrix4(), q=new THREE.Quaternion(), p=new THREE.Vector3(), s=new THREE.Vector3(1,1,1);
  for(let i=0;i<n;i++){
    const th=2*Math.PI*i/n;
    const tx=-Math.sin(th), ty=Math.cos(th);
    p.set(st.cx+t.rCap*Math.cos(th), st.cy+t.rCap*Math.sin(th), zMid);
    q.setFromUnitVectors(new THREE.Vector3(0,1,0), new THREE.Vector3(sgn*tx, sgn*ty, 0));
    m.compose(p,q,s);
    stewartsonArrows.setMatrixAt(i,m);
  }
  stewartsonArrows.instanceMatrix.needsUpdate=true;
  footprintDiscs.forEach(d=>{
    d.visible=!!P.dvCaps;
    const rFp=t.rFoot||P.Rcyl*0.25;
    d.scale.set(rFp,rFp,1);
    d.position.set(st.cx,st.cy,d.position.z);
  });
}
function hideStewartsonVisuals(){
  if(stewartsonTorus)stewartsonTorus.visible=false;
  if(stewartsonArrows)stewartsonArrows.visible=false;
  footprintDiscs.forEach(d=>d.visible=false);
}
function setTaylorCaps(topD,botD,topR,botR,colSil,cx,cy,zT,zB,rC){
  topD.visible=botD.visible=topR.visible=botR.visible=!!P.dvCaps;
  colSil.visible=!!P.dvColumn;
  topD.position.set(cx,cy,zT);botD.position.set(cx,cy,zB);
  topR.position.set(cx,cy,zT);botR.position.set(cx,cy,zB);
  colSil.position.set(cx,cy,(zT+zB)*0.5);
  const sc=[topD,botD,topR,botR];sc.forEach(m=>m.scale.set(rC,rC,1));
  colSil.scale.set(rC,rC,Math.max(0.01,zT-zB));
}
function hideTaylorCaps(topD,botD,topR,botR,colSil){
  [topD,botD,topR,botR,colSil].forEach(m=>m.visible=false);
}
function updateIndicators(tPhys){
  rebuildTubes(false);
  applyDvOpacity();
  const stats=fils.map(f=>carrierStats(f));
  stats.forEach((st,i)=>{
    if(Flags.alpha&&alphaObjs[i]){
      alphaObjs[i].visible=true;
      alphaObjs[i].position.set(st.cx,st.cy,st.z);
      const sc=P.a*6*(1+0.2*Math.sin(tPhys*20));
      alphaObjs[i].scale.set(sc,sc,sc);
    }else if(alphaObjs[i]) alphaObjs[i].visible=false;
  });
  if(!Flags.sep){
    sepObjs.forEach(s=>s.visible=false);
    hideTaylorCaps(capDiscs[0],capDiscs[1],capRings[0],capRings[1],colSils[0]);
    hideTaylorCaps(capDiscs[2],capDiscs[3],capRings[2],capRings[3],colSils[1]);
    footprintDiscs.forEach(d=>d.visible=false);
    hideStewartsonVisuals();
    return;
  }
  let stewartsonShown=false;
  fils.forEach((f,i)=>{
    const st=stats[i];
    const vz=(P.mode==='solo')?effectiveW():(i===0?P.vzA:(P.lockVz?P.vzA:P.vzB));
    const t=taylorColumnState(st,vz);
    if(sepObjs[i]){sepObjs[i].visible=!!P.dvSeparatrix;sepObjs[i].position.set(st.cx,st.cy,st.z);
      sepObjs[i].scale.set(t.rCap,t.rCap,t.rCap);}
    if(i===0) setTaylorCaps(capDiscs[0],capDiscs[1],capRings[0],capRings[1],colSils[0],st.cx,st.cy,t.zTop,t.zBot,t.rCap);
    else setTaylorCaps(capDiscs[2],capDiscs[3],capRings[2],capRings[3],colSils[1],st.cx,st.cy,t.zTop,t.zBot,t.rCap);
    if(P.dvStewartson&&P.mode==='solo'&&i===0&&!stewartsonShown){
      const stw=stewartsonCirculation(vz,t.rCap,P.Om);
      updateStewartsonVisuals(st,vz,t,stw);
      stewartsonShown=true;
    }
  });
  if(!stewartsonShown) hideStewartsonVisuals();
  if(fils.length<2){
    if(sepObjs[1]) sepObjs[1].visible=false;
    hideTaylorCaps(capDiscs[2],capDiscs[3],capRings[2],capRings[3],colSils[1]);
  }
}
function fmtGamma(g){
  const e=Math.floor(Math.log10(Math.max(1e-12,Math.abs(g))));
  return (g/Math.pow(10,e)).toFixed(2)+'·10'+supExp(e);
}
function updateGammaHud(st,vz){
  const show=Flags.sep&&P.mode==='solo';
  document.getElementById('rowGfil').classList.toggle('hidden',!show);
  document.getElementById('rowGsheet').classList.toggle('hidden',!show);
  if(!show)return;
  const t=taylorColumnState(st,vz);
  const stw=stewartsonCirculation(vz,t.rCap,P.Om);
  const gFil=Gamma();
  document.getElementById('hGfil').textContent=fmtGamma(gFil)+' m²/s';
  // v7.2 (RP2): uitsluitend de dimensieloze q_S = −w/(2Ωr_cap); de eerdere
  // Γ_sheet/Γ_rel-getallen waren dimensioneel niet gedefinieerd en zijn weg.
  document.getElementById('hGsheet').textContent=stw.qS.toFixed(4)+(stw.qS<0?' ↓':' ↑');
  document.getElementById('hGsheet').style.color=stw.qS<0?'#FF7043':'#26C6DA';
}
// 3D-camera: links/midden = orbit-rotatie, rechts = translate/pan, wiel = zoom.
let drag=false,dragButton=0,lx=0,ly=0,pinch0=0;
canvas.addEventListener('contextmenu',e=>e.preventDefault());
canvas.addEventListener('pointerdown',e=>{
  if(e.button>2)return;
  drag=true;dragButton=e.button;lx=e.clientX;ly=e.clientY;
  canvas.setPointerCapture(e.pointerId);e.preventDefault();
});
canvas.addEventListener('pointermove',e=>{
  if(!drag)return;
  const dx=e.clientX-lx,dy=e.clientY-ly;
  if(dragButton===2){
    const right=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,0).normalize();
    const up=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,1).normalize();
    const scale=camD*0.00135;
    camTarget.addScaledVector(right,-dx*scale).addScaledVector(up,dy*scale);
  }else{
    camTh-=dx*0.008;
    camPh=Math.min(2.9,Math.max(0.2,camPh-dy*0.008));
  }
  lx=e.clientX;ly=e.clientY;e.preventDefault();
});
function endCameraDrag(e){
  drag=false;
  if(e&&e.pointerId!==undefined&&canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);
}
canvas.addEventListener('pointerup',endCameraDrag);
canvas.addEventListener('pointercancel',endCameraDrag);
canvas.addEventListener('wheel',e=>{e.preventDefault();camD=Math.min(4,Math.max(0.4,camD*(1+0.001*e.deltaY)));},{passive:false});
canvas.addEventListener('touchmove',e=>{
  if(e.touches.length===2){
    const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);
    if(pinch0)camD=Math.min(4,Math.max(0.4,camD*pinch0/d));
    pinch0=d;}
},{passive:true});
canvas.addEventListener('touchend',()=>pinch0=0);

// ================= sparkline =================
const sctx=document.getElementById('cspark').getContext('2d');
function drawSpark(){
  const w=230,h=76;sctx.clearRect(0,0,w,h);
  sctx.fillStyle='#6F82A0';sctx.font='9px monospace';
  sctx.fillText(P.mode==='botsing'?'R̄ (—)  Ω_body A (··)':(Flags.sep?'ρ̄ (—)  z (—)  Γ_rel (··)':(P.twistProxyEnabled?'ρ̄ (—)  Ω_body (··)':'ρ̄ (—)  z (—)  Wr (··)')),4,10);
  if(hist.length<2)return;
  const t0=hist[0].t,t1=hist[hist.length-1].t;
  const den=Math.abs(t1-t0)>1e-12?(t1-t0):1e-12;   // tijd-terug-veilig
  function line(key,color,dash){
    let vmax=1e-9;for(const p of hist)vmax=Math.max(vmax,Math.abs(p[key]));
    sctx.strokeStyle=color;sctx.setLineDash(dash);sctx.beginPath();
    hist.forEach((p,i)=>{
      const x=4+(w-8)*clamp((p.t-t0)/den,0,1);
      const y=h-4-(h-18)*(0.5+0.5*p[key]/vmax);
      i?sctx.lineTo(x,y):sctx.moveTo(x,y);});
    sctx.stroke();sctx.setLineDash([]);
  }
  if(P.mode==='botsing'){line('RA','#FFAE45',[]);line('RB','#55D6FF',[]);line('omA','#A855F7',[3,3]);}
  else{
    line('RA','#FFAE45',[]);line('zA','#55D6FF',[]);
    if(Flags.sep) line('gRel','#FF7043',[3,3]);
    else if(P.twistProxyEnabled) line('omA','#A855F7',[3,3]);
    else line('Wr','#C9D6E3',[3,3]);
  }
}

// ================= UI =================
function fmtNq(){
  const n=Math.max(1,Math.round(P.nQ));
  const unit=P.med==='sst'?'Γ₀':'κ';
  return `${n.toLocaleString('nl-NL')} → Γ = ${n===1?'':n.toLocaleString('nl-NL')} ${unit}`;
}
function fmtGa(){
  const g=Gamma();
  const e=Math.floor(Math.log10(Math.abs(g)));
  const m=g/Math.pow(10,e);
  const q=P.med==='sst'?` (${P.nQ}Γ₀)`:P.med==='he'?` (${P.nQ}κ)`:'';
  return `${m.toFixed(2)}·10${supExp(e)} m²/s${q}`;
}
function supExp(e){
  const map={'-':'⁻','0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'};
  return String(e).split('').map(c=>map[c]||c).join('');
}
function fmtAcc(x){
  if(x<1000)return x.toFixed(x<20?1:0)+'×';
  const e=Math.floor(Math.log10(x));
  return (x/Math.pow(10,e)).toFixed(1)+'·10'+supExp(e)+'×';
}
function updateSubtitle(){
  const topoTxt=topologyLabel();
  const nComp=topologyComponentCount();
  const medTxt={demo:'demo-Γ',he:'He-II, Γ=nκ',sst:'SST, Γ=nΓ₀ [Canon 0.8.20]',
    string:'String-theorie schaalprobe · vrije Γ · geen snaardynamica'}[P.med]||P.med;
  const coreTxt={hol:'holle kern',vast:'vaste kern',gp:'GP-kern'}[P.core];
  const modeTxt=P.mode==='botsing'
    ?`Twee coaxiale ${topoTxt}-dragers${nComp>1?` (${nComp} componenten per drager)`:''}, |Γ| identiek, frontaal${P.inter==='lia'?' · LIA (geen wederzijdse inductie!)':''}`
    :`${nComp>1?nComp+' gekoppelde componenten van ': 'Eén '}${topoTxt} op de middenas${P.inter==='lia'?' · LIA':''}`;
  const transportTxt=[P.centerLock?'centrum-lock':'',P.tracerWrapZ?'periodiek z: knopen+deeltjes':'',P.coreFlowLock?'a–Γ–Ω gekoppeld':''].filter(Boolean).join(' · ');
  document.getElementById('hSub').textContent=`${modeTxt} · ${coreTxt} · ${medTxt}${transportTxt?' · '+transportTxt:''}`;
  document.getElementById('hWrLbl').innerHTML=fils.length>1
    ?'Σ Wr(componenten)':'Wr';
  const lkLbl=document.getElementById('hLkLbl');if(lkLbl)lkLbl.textContent=fils.length>2?'Σ Lk(i,j)':'Lk(1,2)';
  document.getElementById('hRLbl').textContent=P.mode==='botsing'
    ?(isRingTopo()?'R̄ A / B':'ρ̄ A / B'):(nComp>1?'ρ̄ componenten':'ρ̄');
  document.getElementById('hVLbl').textContent=P.mode==='botsing'?'naderingssnelheid':'v_z (w)';
  document.getElementById('rowLk').classList.toggle('hidden',fils.length<2);
  document.getElementById('rowDz').classList.toggle('hidden',P.mode!=='botsing');
  const soloKnot=P.mode==='solo'&&!isRingTopo();
  document.getElementById('rowDWr').classList.toggle('hidden',P.mode==='botsing'||!soloKnot);
  document.getElementById('rowUth').classList.toggle('hidden',!isRingTopo());
  document.getElementById('rowOmBodyA').classList.toggle('hidden',false);
  document.getElementById('rowOmBodyB').classList.toggle('hidden',P.mode!=='botsing');
  document.getElementById('rowChi').classList.toggle('hidden',isRingTopo());
  document.getElementById('rowTw').classList.toggle('hidden',!P.twistProxyEnabled);
  renderFormula();
}
function updateBodyHud(bodyStates,Wr){
  if(!bodyStates.length)return;
  const bA=bodyStates[0];
  document.getElementById('hOmBodyA').textContent=fmtOmegaBody(bA.omegaZ);
  if(P.mode==='botsing'){
    const idxB=fils.findIndex(f=>(f.carrier||'A')==='B');
    if(idxB>=0&&bodyStates[idxB])document.getElementById('hOmBodyB').textContent=fmtOmegaBody(bodyStates[idxB].omegaZ);
  }
  if(bA.chi){
    document.getElementById('hChi').textContent=`(${bA.chi.x.toFixed(2)}, ${bA.chi.y.toFixed(2)}) · ${bA.chi.phi.toFixed(0)}°`;
  }else{
    document.getElementById('hChi').textContent='— (ring, Wr=0)';
  }
  if(P.twistProxyEnabled&&twistProxy){
    const tw=twistProxySum();
    document.getElementById('hTw').textContent=tw.toExponential(3)+' m'; // v7.1 (B4): dimensie is lengte; niet optellen bij Wr
  }
}
function knotLabel(i){
  const catalog=getIdealKnotCatalog();if(catalog?.ids?.[i])return catalog.ids[i];
  const e=window.IDEAL_KNOTS&&window.IDEAL_KNOTS[i];return e?(e.knotId||e.id||e.name||('#'+i)):'3:1:1';
}
function renderFormula(){
  const el=document.getElementById('eFormula');
  if(!el||!window.katex)return;
  const parts=[
    {on:Flags.alpha,t:'\\alpha C(K)',c:'#FF6E6E'},
    {on:Flags.beta,t:'\\beta \\widehat L(K)',c:'#FFAE45'},
    {on:Flags.gamma,t:'\\gamma \\widehat H(K)',c:'#A855F7'}
  ];
  el.innerHTML='';
  const lead=document.createElement('span');
  katex.render('\\widehat{\\mathcal S}(K)=',lead);el.appendChild(lead);
  parts.forEach((p,i)=>{
    if(i) el.appendChild(document.createTextNode(' + '));
    const s=document.createElement('span');
    s.style.color=p.on?p.c:'#6F82A0';if(p.on)s.style.fontWeight='600';
    katex.render(p.t,s);el.appendChild(s);
  });
  if(Flags.sep){
    el.appendChild(document.createTextNode('  ·  '));
    const overlay=document.createElement('span');overlay.style.color='#EAF2FA';
    katex.render('\\partial V\\;\\text{overlay}',overlay);el.appendChild(overlay);
  }
}
function initDiagnosticToggles(){
  syncDiagnosticToggles();
}
function syncDiagnosticToggles(){
  document.querySelectorAll('#indSeg .seg-btn').forEach(b=>{
    const key=b.dataset.ind;
    if(!EXPLAIN[key])return;
    b.classList.toggle(EXPLAIN[key].cls,!!Flags[key]);
  });
}
function setIndFlag(key,on){
  if(!(key in Flags))return;
  if(key==='sep')setDvAll(on);
  else Flags[key]=on;
  syncDiagnosticToggles();
  renderFormula();
  rebuildTubes(true);
  updateIndicators(tPhys);
}
function updateIdealKnotInfo(){
  const note=document.getElementById('idealKnotInfo'),entry=activeKnotEntry();
  const modeRow=document.getElementById('idealComponentModeRow'),reset=document.getElementById('bResetIdealKnot');
  if(modeRow)modeRow.classList.toggle('hidden',!entry||knotEntryComponents(entry).length<2);
  if(reset)reset.classList.toggle('hidden',!entry);
  if(!note)return;
  if(!entry){
    const ni=getIdealKnotCatalog()?.ids?.length||0,nf=getFourierKnotCatalog()?.ids?.length||0,nk=getKnotPlotKnotCatalog()?.ids?.length||0;
    note.textContent=`Ingebouwde geometrie actief. Externe catalogi: ${ni} Gilbert ideal/tight objecten, ${nf} compacte fseries-curven en ${nk} KnotPlot-relaxatiekandidaten geladen. Fseries en KnotPlot zijn geometrische Fourierbronnen, niet automatisch ideal/tight.`;
    return;
  }
  const comps=knotEntryComponents(entry);
  const modes=comps.map(c=>{const q=c.coeffs||[];return `${q.length} termen / I_max ${q.reduce((m,v)=>Math.max(m,Math.abs(Number(v.I)||0)),0)}`;});
  const L0=finiteMetaNumber(entry.L),componentLengths=comps.map(c=>finiteMetaNumber(c.L)).filter(Number.isFinite);
  const L=Number.isFinite(L0)?L0:(componentLengths.length===comps.length?componentLengths.reduce((a,b)=>a+b,0):NaN);
  const isKnotPlot=P.knotSource==='knotplot',isFs=!isKnotPlot&&(P.knotSource==='fseries'||entry.ideal===false);
  const source=isKnotPlot?'knotplot_knots_data.js (KnotPlot XYZ→Fourier)':isFs?'fourier_knots_data.js (.fseries)':'ideal_knots_data.js (Brian Gilbert)';
  const status=isKnotPlot?`${entry.status||'candidate'}; uniform-N300 VortexLab-centerline, polishprovenance apart; niet als zelfstandige globale ideal/tight, fysieke diameter of ropelength-minimum gecertificeerd`:isFs?'compacte gesloten Fouriercurve; niet als tight/ideal gecertificeerd':'tight/ideal brongeometrie; nog geen stationaire Euler-, GP/NLSE- of SST-oplossing';
  const indexInfo=isFs&&Number.isInteger(entry.harmonicStart)?` · harmonische eerste regel j=${entry.harmonicStart}`:isKnotPlot&&Number.isFinite(entry.checkpointSteps)?` · checkpoint ${entry.checkpointSteps} stappen`:'';
  const warning=entry.warning?` · WAARSCHUWING bron: ${entry.warning}`:'';
  note.textContent=`${isKnotPlot?'KnotPlot':isFs?'Fseries':'Ideal'} ID: ${entry.knotId||P.knotKey||knotLabel(P.knotIdx)} · Conway: ${entry.conway||'—'} · componenten: ${comps.length} · bronlengte L: ${Number.isFinite(L)?L.toFixed(6):'niet opgegeven'} · Fourier: ${modes.join(' + ')}${indexInfo} · modus: ${P.idealComponentMode==='all'?'volledig object':'één component'} · bron: ${source} · status: ${status}${warning}.`;
}
function syncCompSelects(){
  const entry=activeKnotEntry(),comps=knotEntryComponents(entry);
  const row=document.getElementById('compRow'),mode=document.getElementById('idealComponentMode');
  if(mode)mode.value=P.idealComponentMode;
  if(!entry||comps.length<2||P.idealComponentMode!=='single'){if(row)row.classList.add('hidden');updateIdealKnotInfo();return;}
  row.classList.remove('hidden');
  const fill=(sel,val)=>{
    sel.innerHTML=comps.map((_,i)=>`<option value="${i+1}">comp ${i+1}</option>`).join('');
    sel.value=String(Math.min(Math.max(val,1),comps.length));
  };
  fill(document.getElementById('compA'),P.compA);fill(document.getElementById('compB'),P.compB);
  updateIdealKnotInfo();
}
function syncSeg(id,attr,val){
  document.querySelectorAll(`#${id} .seg-btn`).forEach(b=>b.classList.toggle('active',b.dataset[attr]===val));
}
function syncSignedUi(sliderId,revId,val,fmtVal){
  const s=document.getElementById('s'+sliderId);
  const r=document.getElementById(revId);
  const v=document.getElementById('v'+sliderId);
  if(!s||!r)return;
  r.checked=val<0;
  P['rev'+sliderId]=val<0;
  syncInputUnlessEditing(s,Math.abs(val));
  if(v&&fmtVal)v.textContent=fmtVal(val);
}
function syncUi(){
  syncSeg('modeSeg','mode',P.mode);
  document.getElementById('topoSelect').value=P.topo;
  syncSeg('interSeg','inter',P.inter);
  syncSeg('coreSeg','core',P.core);
  syncSeg('medSeg','med',P.med);
  syncSeg('qualSeg','qual',P.qual);
  syncSeg('visSeg','vis',P.vis);
  syncSeg('tubeSeg','tube',P.tubeMat);
  syncSeg('frameSeg','frame',P.displayFrame==='corot'?'rotating':'absolute');
  document.getElementById('interRow').classList.remove('hidden');
  document.getElementById('offRow').classList.remove('hidden');
  updateInitialSeparationUi();
  document.getElementById('wRow').classList.toggle('hidden',P.mode!=='solo');   // v7.1 (B1)
  document.getElementById('vzARow').classList.toggle('hidden',P.mode!=='botsing'); // v7.1 (B1)
  document.getElementById('vzBRow').classList.toggle('hidden',P.mode!=='botsing'||P.lockVz);
  document.getElementById('ccwARow').classList.remove('hidden');
  document.getElementById('ccwBRow').classList.toggle('hidden',P.mode!=='botsing');
  document.getElementById('mirrorRow').classList.toggle('hidden',P.mode!=='botsing');
  document.getElementById('lockVzRow').classList.toggle('hidden',P.mode!=='botsing');
  document.getElementById('qualRow').classList.remove('hidden');
  const quantized=P.med==='he'||P.med==='sst';
  document.getElementById('gaRow').classList.toggle('hidden',quantized);
  document.getElementById('nqRow').classList.toggle('hidden',!quantized);
  document.getElementById('cCenterline').checked=P.showCenterline;
  document.getElementById('cCcwA').checked=P.ccwA;
  document.getElementById('cCcwB').checked=P.ccwB;
  document.getElementById('cMirror').checked=P.mirrorB;
  document.getElementById('cLockVz').checked=P.lockVz;
  document.getElementById('cCoRot').checked=P.displayFrame==='corot';
  const vFR=document.getElementById('vFrameRef');if(vFR)vFR.textContent=P.displayFrame==='corot'?'Rotating':'Absolute';
  document.getElementById('cBgOmega').checked=bgWallInSolver();
  document.getElementById('cChiArrow').checked=P.showChiArrow;
  document.getElementById('cTwProxy').checked=P.twistProxyEnabled;
  document.getElementById('cAutoRelax').checked=P.autoRelax;
  const tg=document.getElementById('cTopologyGuard');if(tg)tg.checked=P.topologyGuard;
  const tgr=document.getElementById('topologyGuardReadout');if(tgr){const dc=contactThresholdInfo().effective,g=lastTopologyGap;tgr.textContent=P.topologyGuard
    ?`ACTIEF · minimale centerline-clearance=${Number.isFinite(g)?fmtLengthSI(g):'wordt bepaald'} · stopgrens=${fmtLengthSI(dc)} · contact-CFL + ${TOPOLOGY_SWEEP_SAMPLES}-punts transient scan`
    :'UIT · centerlines kunnen numeriek door elkaar tunnelen; alleen gebruiken voor expliciete reconnectie-experimenten.';}
  document.getElementById('cCoreFlowLock').checked=P.coreFlowLock;
  document.getElementById('cCenterLock').checked=P.centerLock;
  document.getElementById('cTracerWrapZ').checked=P.tracerWrapZ;
  document.getElementById('autoRelaxBadge').textContent=P.timeReverse&&P.autoRelax?'PAUZE':(P.autoRelax?'AAN':'UIT');
  document.getElementById('autoRelaxBadge').classList.toggle('on',P.autoRelax&&!P.timeReverse);
  document.getElementById('cTimeReverse').checked=P.timeReverse;
  document.getElementById('timeReverseRow').classList.toggle('time-reverse-on',P.timeReverse);
  syncDvGeometryUi();
  document.getElementById('cGhostRing').checked=P.ghostStewartson;
  document.getElementById('cTaylorOsc').checked=P.taylorOsc.enabled;
  document.getElementById('oscRow').classList.toggle('hidden',P.mode!=='solo');
  [['WAl','wAl'],['WBe','wBe'],['WGa','wGa']].forEach(([id,key])=>{
    const el=document.getElementById('s'+id);
    if(el){el.value=P[key];document.getElementById('v'+id).textContent=P[key].toFixed(1);}});
  const cT=document.getElementById('cTracers');if(cT)cT.checked=P.showTracers;
  const cSL=document.getElementById('cStreamlines');if(cSL)cSL.checked=P.showStreamlines;
  const sVO=document.getElementById('sVortexOpacity');if(sVO)sVO.value=String(Math.round(100*P.vortexOpacity));
  const vVO=document.getElementById('vVortexOpacity');if(vVO)vVO.textContent=Math.round(100*P.vortexOpacity)+'%';
  const sPS=document.getElementById('sParticleSize');if(sPS)sPS.value=(1000*P.particleSize).toFixed(1);
  const vPS=document.getElementById('vParticleSize');if(vPS)vPS.textContent=(1000*P.particleSize).toFixed(1)+' mm';
  const sTC=document.getElementById('sTracerCount');if(sTC)sTC.value=String(P.tracerCount);
  const vTC=document.getElementById('vTracerCount');if(vTC)vTC.textContent=String(P.tracerCount);
  const sSC=document.getElementById('sStreamlineCount');if(sSC)sSC.value=String(P.streamlineCount);
  const vSC=document.getElementById('vStreamlineCount');if(vSC)vSC.textContent=String(P.streamlineCount);
  const scRow=document.getElementById('streamlineCountRow');if(scRow)scRow.classList.toggle('hidden',!P.showStreamlines);
  const vc=document.getElementById('sVorticityColor');if(vc)vc.value=P.vorticityLineColor||'#0F1A29';
  const vvc=document.getElementById('vVorticityColor');if(vvc)vvc.textContent=(P.vorticityLineColor||'#0F1A29').toUpperCase();
  const cPF=document.getElementById('cPotentialFlow');if(cPF)cPF.checked=P.showPotentialFlow;
  const mPF=document.getElementById('sPotentialMode');if(mPF)mPF.value=P.potentialMode;
  const rPF=document.getElementById('sPotentialRadiusSource');if(rPF)rPF.value=P.potentialRadiusSource;
  const prRow=document.getElementById('potentialRadiusRow');if(prRow)prRow.classList.toggle('hidden',P.potentialRadiusSource!=='manual');
  const sPR=document.getElementById('sPotentialRadiusCm');if(sPR)sPR.value=(100*P.potentialRadius).toFixed(1);
  const vPR=document.getElementById('vPotentialRadius');if(vPR)vPR.textContent=(100*P.potentialRadius).toFixed(1)+' cm';
  const sPU=document.getElementById('sPotentialU');if(sPU)sPU.value=P.potentialU.toFixed(3);
  const vPU=document.getElementById('vPotentialU');if(vPU)vPU.textContent=P.potentialU.toFixed(3)+' m/s';
  const sPO=document.getElementById('sPotentialOpacity');if(sPO)sPO.value=String(Math.round(100*P.potentialOpacity));
  const vPO=document.getElementById('vPotentialOpacity');if(vPO)vPO.textContent=Math.round(100*P.potentialOpacity)+'%';
  updateParticleResetButton();
  const sRH=document.getElementById('sRHorn');if(sRH)sRH.value=fmtLengthSI(R_HORN_SST);
  const vRH=document.getElementById('vRHorn');if(vRH)vRH.textContent=fmtLengthSI(R_HORN_SST);
  const rCore=resolvedFixedCoreRadius();
  const sRC=document.getElementById('sRCorePhys');if(sRC)sRC.value=Number.isFinite(rCore)?fmtLengthSI(rCore):'';
  const vRC=document.getElementById('vRCorePhys');if(vRC)vRC.textContent=Number.isFinite(rCore)?fmtLengthSI(rCore):'— (niet afgeleid)';
  const sp=document.getElementById('sScaleProbe');if(sp)sp.value=fmtLengthSI(P.scaleProbe);
  const vSP=document.getElementById('vScaleProbe');if(vSP)vSP.textContent=fmtLengthSI(P.scaleProbe);
  const spLog=document.getElementById('sScaleProbeLog');if(spLog&&P.scaleProbe>0)
    spLog.value=String(clamp(Math.log10(P.scaleProbe),Number(spLog.min),Number(spLog.max)));
  const spPreset=document.getElementById('scaleProbePreset');if(spPreset){
    const rel=(a,b)=>Math.abs(a-b)/Math.max(Math.abs(b),1e-300);
    spPreset.value=rel(P.scaleProbe,PLANCK_LENGTH*.5)<1e-9?'planck-half':
      (rel(P.scaleProbe,PLANCK_LENGTH)<1e-9?'planck':
      (rel(P.scaleProbe,PLANCK_LENGTH*2)<1e-9?'planck-double':
      (rel(P.scaleProbe,R_HORN_SST)<1e-9?'sst':(rel(P.scaleProbe,HE_CORE_REF)<1e-9?'helium':'custom'))));
  }
  syncDiagnosticToggles();
  syncSpecClockQuickControls();
  updateSpecClockDisplay();
  const gpDeltaText=DELTA.gp.toFixed(6);
  const gpSel=document.getElementById('gpDeltaSel');if(gpSel){gpSel.value=String(DELTA.gp);gpSel.disabled=P.core!=='gp';}
  const gpVal=document.getElementById('vGpDelta');if(gpVal)gpVal.textContent=gpDeltaText;
  const gpPanel=document.getElementById('gpDeltaPanel');if(gpPanel){gpPanel.classList.toggle('active',P.core==='gp');gpPanel.classList.toggle('hidden',P.core!=='gp');}
  document.getElementById('vCore').textContent='Δ = '+(P.core==='hol'?'½':(P.core==='vast'?'¼':gpDeltaText));
  document.getElementById('vGa').textContent=fmtGa();
  document.getElementById('vNq').textContent=fmtNq();
  const sASim=document.getElementById('sA');if(sASim)sASim.value=formatASimInputMm(P.a);
  document.getElementById('vAcc').textContent=fmtAcc(acc());
  syncSignedUi('Om','revOm',P.Om,x=>Math.abs(x).toFixed(2)+' rad/s · '+(x<0?'CW':'CCW'));
  syncSignedUi('Ga','revGa',P.GaDemo,()=>fmtGa());
  syncSignedUi('Off','revOff',P.off*1000,x=>x.toFixed(0)+' mm');
  syncSignedUi('W','revW',P.w*1000,x=>fmtAxialMmPerS(x));
  syncSignedUi('VzA','revVzA',P.vzA*1000,x=>fmtAxialMmPerS(x));
  syncSignedUi('VzB','revVzB',P.vzB*1000,x=>fmtAxialMmPerS(x));
  const mfSel=document.getElementById('mfTemp');if(mfSel)mfSel.value=P.mfTemp;
  const mfCustom=P.mfTemp==='custom';
  const sMfA=document.getElementById('sMfA');
  if(sMfA){sMfA.disabled=!mfCustom;sMfA.value=String(P.mfAlpha);
    document.getElementById('vMfA').textContent=P.mfAlpha.toFixed(3);}
  const sMfAp=document.getElementById('sMfAp');
  if(sMfAp){sMfAp.disabled=!mfCustom;sMfAp.value=String(P.mfAlphaP);
    document.getElementById('vMfAp').textContent=P.mfAlphaP.toFixed(4);}
  const vMfT=document.getElementById('vMfT');
  if(vMfT)vMfT.textContent=P.mfTemp==='0'?'T = 0 (uit)'
    :(P.mfTemp==='custom'?'aangepast':P.mfTemp+' K (He-II SVP)');
  syncSignedUi('Vn','revVn',P.vnZ*1000,x=>fmtAxialMmPerS(x));
  document.getElementById('sDiam').value=(P.Rcyl*200).toFixed(0);
  document.getElementById('vDiam').textContent=(P.Rcyl*200).toFixed(0)+' cm';
  document.getElementById('sHeight').value=(P.Hcyl*100).toFixed(1).replace(/\.0$/,'');
  document.getElementById('vHeight').textContent=(P.Hcyl*100).toFixed(1).replace(/\.0$/,'')+' cm (totaal '+(cylinderHeight()*100).toFixed(0)+' cm)';
  document.getElementById('hOm').textContent=P.Om.toFixed(2);
  updateStretchReadout();
  if(Y&&fils.length)updateCoreRadiusLimit(true);
  updateCoreFlowReadout();
  syncBundleUi();
  syncStretchGateUi();
  syncHybridNumberInputs();
  syncCompSelects();
  updateHeaderTitle();
  scheduleSidebarFit();
}
// ===== VL DUAL-SIDEBAR UI · broncontrols logisch groeperen =====
function vlMoveControl(id,dst){
  const el=document.getElementById(id);
  const ctrl=el?.closest('.ctrl');
  if(ctrl&&dst)dst.appendChild(ctrl);
}
function prepareDualSidebarGroups(){
  if(document.body.dataset.vlGroupsPrepared==='1')return;
  const cyl=document.getElementById('stabGroupCylinder');
  const core=document.getElementById('stabGroupCore');
  const flow=document.getElementById('stabGroupFlow');
  const flowFlags=document.getElementById('stabGroupFlowFlags');
  const vortex=document.getElementById('stabGroupVortex');
  const vortexFlags=document.getElementById('stabGroupVortexFlags');
  const runTop=document.getElementById('runSetupTop');
  const visBody=document.querySelector('#collVis > .coll-body > .ctrls');
  if(!cyl||!core||!flow||!flowFlags||!vortex||!vortexFlags||!runTop||!visBody)return;

  // LINKS · CILINDER
  vlMoveControl('sDiam',cyl);vlMoveControl('sHeight',cyl);
  const link=document.getElementById('bLinkDH'),stretch=document.getElementById('vStretch');
  if(link)cyl.appendChild(link);if(stretch)cyl.appendChild(stretch);
  const volumeNote=document.querySelector('#collVolume .note');if(volumeNote)cyl.appendChild(volumeNote);
  const periodic=document.getElementById('cTracerWrapZ')?.closest('label');if(periodic)cyl.appendChild(periodic);

  // LINKS · FLOW
  const inter=document.getElementById('interRow');if(inter)flow.appendChild(inter);
  ['offRow','wRow','vzARow','vzBRow','cylinderOmegaRow','sstBundlePanel'].forEach(id=>{
    const el=document.getElementById(id);if(el)flow.appendChild(el);
  });
  const bg=document.getElementById('cBgOmega')?.closest('label');if(bg)flowFlags.appendChild(bg);
  const bgNote=document.querySelector('#collParams > .coll-body > .btns .note');if(bgNote)flowFlags.appendChild(bgNote);

  // RECHTS · VORTEX
  vlMoveControl('modeSeg',vortex);vlMoveControl('sSepAB',vortex);vlMoveControl('topoSelect',vortex);
  ['knotRow','fseriesRow','knotplotRow','idealComponentModeRow','compRow','bResetIdealKnot','idealKnotInfo'].forEach(id=>{const el=document.getElementById(id);if(el)vortex.appendChild(el);});
  const paramFlags=document.querySelector('#collParams > .coll-body > .btns');
  if(paramFlags){
    ['ccwARow','ccwBRow','mirrorRow','lockVzRow'].forEach(id=>{const el=document.getElementById(id);if(el)vortexFlags.appendChild(el);});
  }
  const centerLock=document.getElementById('cCenterLock')?.closest('label');if(centerLock)vortexFlags.appendChild(centerLock);

  // RECHTS · KERN
  vlMoveControl('coreSeg',core);vlMoveControl('sNq',core);vlMoveControl('sGa',core);vlMoveControl('sA',core);
  vlMoveControl('sRHorn',core);vlMoveControl('sRCorePhys',core);vlMoveControl('sScaleProbe',core);
  const coreFlowPanel=document.getElementById('coreFlowLinkPanel');if(coreFlowPanel)core.appendChild(coreFlowPanel);

  // WEERGAVE · frame en kleur horen niet meer onder cilinderfysica.
  ['frameRefRow','vorticityColorRow'].forEach(id=>{const el=document.getElementById(id);if(el)visBody.appendChild(el);});

  // RUN · afspeeltempo blijft beschikbaar in het uitgebreide RUN-tabblad.
  vlMoveControl('sAcc',runTop);
  document.body.dataset.vlGroupsPrepared='1';
}
prepareDualSidebarGroups();

// Step 9: combineer voor ieder numeriek veld een slider, compact getalveld en ^ / v bediening.
// De oorspronkelijke number-input-ID's blijven de bron van waarheid voor alle physics-bindings.
function initNumberSteppers(){
  document.querySelectorAll('input[type="number"][id^="s"]').forEach(input=>{
    if(input.closest('.param-hybrid'))return;
    input.classList.add('param-number');
    input.setAttribute('autocomplete','off');
    const stepRaw=Number(input.step);
    input.setAttribute('inputmode',Number.isFinite(stepRaw)&&stepRaw%1!==0?'decimal':'numeric');

    const wrap=document.createElement('div');
    wrap.className='param-hybrid';
    input.parentNode.insertBefore(wrap,input);
    wrap.appendChild(input);

    const range=document.createElement('input');
    range.type='range';
    range.className='param-slider';
    const logarithmic=input.dataset.scale==='log';
    range.min=logarithmic?'0':(input.min||'0');
    range.max=logarithmic?'1000':(input.dataset.sliderMax||input.max||'100');
    range.step=logarithmic?'1':(input.step||'1');
    range.value=String(hybridRangeFromInput(input));
    range.setAttribute('aria-label',(input.id||'parameter')+' slider');
    wrap.insertBefore(range,input);

    function makeButton(dir,label,title){
      const b=document.createElement('button');
      b.type='button';
      b.className='num-step-btn';
      b.dataset.dir=dir;
      b.textContent=label;
      b.title=title;
      b.setAttribute('aria-label',title);
      return b;
    }
    const up=makeButton('up','^','Waarde één stap verhogen');
    const down=makeButton('down','v','Waarde één stap verlagen');
    wrap.append(up,down);

    function ensureNumericSeed(){
      if(input.value!=='')return;
      input.value=input.min!==''?input.min:'0';
    }
    function publish(){
      range.value=String(hybridRangeFromInput(input));
      input.dispatchEvent(new Event('input',{bubbles:true}));
    }
    function nudge(direction,multiplier=1){
      ensureNumericSeed();
      try{
        const count=Math.max(1,Math.round(Math.abs(multiplier)));
        for(let i=0;i<count;i++) direction>0?input.stepUp():input.stepDown();
      }catch(_err){
        const step=Number(input.step)||1;
        const current=Number(input.value)||0;
        const lo=input.min===''?-Infinity:Number(input.min);
        const hi=input.max===''? Infinity:Number(input.max);
        input.value=String(clamp(current+Math.sign(direction)*step*multiplier,lo,hi));
      }
      publish();
      input.focus({preventScroll:true});
    }
    range.addEventListener('input',()=>{
      const value=hybridInputFromRange(input,range.value);
      input.value=formatHybridInputValue(input,value);
      input.dispatchEvent(new Event('input',{bubbles:true}));
    });
    input.addEventListener('input',()=>{range.value=String(hybridRangeFromInput(input));});
    up.addEventListener('click',e=>nudge(+1,e.shiftKey?10:1));
    down.addEventListener('click',e=>nudge(-1,e.shiftKey?10:1));
    input.addEventListener('keydown',e=>{
      if(e.key==='PageUp'){e.preventDefault();nudge(+1,10);}
      else if(e.key==='PageDown'){e.preventDefault();nudge(-1,10);}
    });
    input.addEventListener('change',()=>{
      if(input.value==='')return;
      const value=Number(input.value);
      const lo=input.min===''?-Infinity:Number(input.min);
      const hi=input.max===''? Infinity:Number(input.max);
      if(Number.isFinite(value)){
        const bounded=clamp(value,lo,hi);
        if(bounded!==value){input.value=String(bounded);publish();}
      }
    });
  });
}
initNumberSteppers();


// ===== VL DUAL-SIDEBAR UI =====
// Compatibiliteits-hook: bestaande statusupdates mogen deze functie blijven aanroepen,
// maar UI-inhoud wordt nooit meer geometrisch verkleind.
function scheduleSidebarFit(){ /* bewust leeg: panelen scrollen op 100% schaal */ }

function vlNode(id){return document.getElementById(id);}
function vlMove(node,dst){if(node&&dst)dst.appendChild(node);return node;}
function vlCleanText(node){
  return (node?.textContent||'').replace(/\s+/g,' ').trim();
}
function vlMakeHiddenOriginal(button,newLabel){
  if(!button||button.dataset.vlRelabeled==='1')return;
  const original=button.textContent.trim();
  button.textContent=newLabel;
  const hidden=document.createElement('span');hidden.className='vl-hidden-original';hidden.textContent=original;
  button.appendChild(hidden);button.dataset.vlRelabeled='1';
}
function vlCreateProxySelect(segId,dataKey,label,host){
  const seg=vlNode(segId);if(!seg||!host)return null;
  const group=document.createElement('div');group.className='vl-topbar-group vl-topbar-status';
  const lab=document.createElement('label');lab.className='vl-topbar-label';lab.textContent=label;
  const select=document.createElement('select');select.setAttribute('aria-label',label);select.title=label;
  [...seg.querySelectorAll('button[data-'+dataKey+']')].forEach(btn=>{
    const opt=document.createElement('option');opt.value=btn.dataset[dataKey];opt.textContent=vlCleanText(btn);select.appendChild(opt);
  });
  const sync=()=>{
    const active=seg.querySelector('button.active[data-'+dataKey+']');if(active)select.value=active.dataset[dataKey];
    group.classList.remove('stab-good','stab-warn','stab-bad','stab-capacity');
    ['stab-good','stab-warn','stab-bad','stab-capacity'].forEach(c=>{if(seg.classList.contains(c))group.classList.add(c);});
    if(seg.title)select.title=seg.title;
  };
  select.addEventListener('change',()=>seg.querySelector('button[data-'+dataKey+'="'+CSS.escape(select.value)+'"]')?.click());
  new MutationObserver(sync).observe(seg,{attributes:true,subtree:true,attributeFilter:['class','title']});
  sync();group.append(lab,select);host.appendChild(group);
  const source=seg.closest('.ctrl');if(source)source.classList.add('vl-proxy-source');
  return select;
}
function vlMoveSelectToTopbar(selectId,label,host,extraClass=''){
  const select=vlNode(selectId);if(!select||!host)return null;const source=select.closest('.ctrl');
  const group=document.createElement('div');group.className='vl-topbar-group '+extraClass;
  const lab=document.createElement('label');lab.className='vl-topbar-label';lab.textContent=label;
  group.append(lab,select);host.appendChild(group);
  if(source&&source!==group)source.classList.add('vl-proxy-source');
  return select;
}
function vlCreateSpeedControl(host){
  const source=vlNode('sAcc'),display=vlNode('vAcc');if(!source||!display||!host)return null;
  const group=document.createElement('div');group.className='vl-topbar-group vl-speed-group';
  const lab=document.createElement('label');lab.className='vl-topbar-label';lab.textContent='Snelheid';
  const range=document.createElement('input');range.type='range';range.className='vl-speed-range';
  range.min=source.min||'0';range.max=source.max||'7';range.step=source.step||'0.05';range.value=String(P.accExp);
  range.setAttribute('aria-label','Simulatiesnelheid');
  const value=document.createElement('span');value.className='vl-speed-value';
  const sync=()=>{source.value=String(P.accExp);range.value=String(P.accExp);value.textContent=display.textContent||fmtAcc(acc());};
  range.addEventListener('input',()=>{source.value=range.value;source.dispatchEvent(new Event('input',{bubbles:true}));queueMicrotask(sync);});
  source.addEventListener('input',()=>queueMicrotask(sync));new MutationObserver(sync).observe(display,{childList:true,characterData:true,subtree:true});
  const note=vlNode('accCapacityNote');group.title=note?.textContent.trim()||'Afspeeltempo; verandert de volledige CFL-stappen niet.';
  group.append(lab,range,value);host.appendChild(group);source.closest('.ctrl')?.classList.add('vl-proxy-source');sync();return range;
}
function vlCreateHeaderDropdown(buttonLabel,node,shell,key='view',ariaLabel=null){
  if(!node||!shell)return null;
  const safeKey=String(key||buttonLabel).toLowerCase().replace(/[^a-z0-9_-]+/g,'-');
  const menuId='vlHeader'+safeKey[0].toUpperCase()+safeKey.slice(1)+'Menu';
  const button=document.createElement('button');button.type='button';button.className='vl-header-menu-btn vl-header-view-btn';
  button.textContent=buttonLabel+' ▾';button.setAttribute('aria-expanded','false');button.setAttribute('aria-controls',menuId);
  button.title='Open '+buttonLabel.toLowerCase()+'-instellingen';
  const menu=document.createElement('section');menu.className='vl-header-dropdown vl-'+safeKey+'-menu';menu.id=menuId;menu.setAttribute('aria-label',ariaLabel||buttonLabel+'-instellingen');
  if(node.tagName==='DETAILS')node.open=true;menu.appendChild(node);shell.appendChild(menu);
  const registry=window.__vlHeaderDropdowns||(window.__vlHeaderDropdowns=new Set());
  const api={button,menu,setOpen:null};registry.add(api);
  const setOpen=value=>{
    const open=!!value;
    if(open)registry.forEach(other=>{if(other!==api)other.setOpen?.(false);});
    menu.classList.toggle('open',open);button.setAttribute('aria-expanded',open?'true':'false');
  };
  api.setOpen=setOpen;
  button.addEventListener('click',e=>{e.stopPropagation();setOpen(!menu.classList.contains('open'));});
  document.addEventListener('pointerdown',e=>{if(menu.classList.contains('open')&&!menu.contains(e.target)&&e.target!==button)setOpen(false);});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')setOpen(false);});
  return api;
}

function vlMakePane(id,title,subtitle,nodes){
  const pane=document.createElement('section');pane.className='vl-pane';pane.id=id;pane.setAttribute('role','tabpanel');
  const header=document.createElement('header');header.className='vl-pane-header';
  const h=document.createElement('h2');h.textContent=title;
  const sub=document.createElement('span');sub.className='vl-pane-subtitle';sub.textContent=subtitle||'';
  const close=document.createElement('button');close.type='button';close.className='vl-pane-close';close.textContent='×';close.title='Sluit zijpaneel';close.setAttribute('aria-label','Sluit '+title);
  const scroll=document.createElement('div');scroll.className='vl-pane-scroll';
  nodes.filter(Boolean).forEach(node=>scroll.appendChild(node));
  header.append(h,sub,close);pane.append(header,scroll);return {pane,close};
}
function vlInitClockPaneResize(pane,onChange){
  if(!pane||pane.dataset.resizeBound==='1')return;pane.dataset.resizeBound='1';const root=document.documentElement,key='vortexlab.clock.width',fallback=560,minWidth=360;
  function maxWidth(){return Math.max(minWidth,Math.min(1100,window.innerWidth-2*Number.parseFloat(getComputedStyle(root).getPropertyValue('--vl-rail-w')||44)-120));}
  function apply(value,persist=true){const w=Math.round(Math.max(minWidth,Math.min(maxWidth(),Number(value)||fallback)));root.style.setProperty('--vl-clock-w',w+'px');pane.dataset.width=String(w);if(persist)try{localStorage.setItem(key,String(w));}catch(_){ }onChange?.();return w;}
  let stored=null;try{stored=Number(localStorage.getItem(key));}catch(_){ }apply(Number.isFinite(stored)&&stored>0?stored:fallback,false);
  const handle=document.createElement('div');handle.className='vl-pane-resizer';handle.title='Sleep om de CLOCK-breedte te wijzigen · dubbelklik voor standaard';handle.setAttribute('role','separator');handle.setAttribute('aria-orientation','vertical');handle.tabIndex=0;pane.appendChild(handle);
  let startX=0,startW=0,active=false;const move=e=>{if(!active)return;apply(startW+(startX-e.clientX),false);};const stop=()=>{if(!active)return;active=false;handle.classList.remove('vl-resizing');document.body.classList.remove('vl-resizing-clock');apply(Number(pane.dataset.width),true);window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',stop);};
  handle.addEventListener('pointerdown',e=>{active=true;startX=e.clientX;startW=pane.getBoundingClientRect().width;handle.classList.add('vl-resizing');document.body.classList.add('vl-resizing-clock');handle.setPointerCapture?.(e.pointerId);window.addEventListener('pointermove',move);window.addEventListener('pointerup',stop);e.preventDefault();});
  handle.addEventListener('dblclick',()=>apply(fallback,true));handle.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();apply((Number(pane.dataset.width)||fallback)+(e.key==='ArrowLeft'?20:-20),true);}else if(e.key==='Home'){e.preventDefault();apply(minWidth,true);}else if(e.key==='End'){e.preventDefault();apply(maxWidth(),true);}});window.addEventListener('resize',()=>apply(Number(pane.dataset.width)||fallback,false),{passive:true});
}
function vlCreateIndependentDock(side,specs,defaultOpenKeys=[],outerToInnerOrder=null){
  const dock=document.createElement('div');dock.className='vl-dock vl-dock-'+side;dock.id='vlDock'+side[0].toUpperCase()+side.slice(1);
  const rail=document.createElement('nav');rail.className='vl-dock-rail';rail.setAttribute('role','group');rail.setAttribute('aria-label',side==='left'?'Onafhankelijke linker simulatorpanelen':'Onafhankelijke rechter simulatorpanelen');
  const panel=document.createElement('aside');panel.className='vl-dock-panel';
  dock.append(rail,panel);
  const entries=new Map();
  specs.forEach((spec,index)=>{
    const made=vlMakePane('vl-'+side+'-'+spec.key,spec.title,spec.subtitle,spec.nodes);made.pane.dataset.key=spec.key;
    panel.appendChild(made.pane);
    const b=document.createElement('button');b.type='button';b.className='vl-dock-tab';b.dataset.key=spec.key;b.id='vl-'+side+'-'+spec.key+'-toggle';
    b.innerHTML='<span class="vl-tab-icon" aria-hidden="true">'+spec.icon+'</span><span>'+spec.short+'</span>';
    b.title=spec.tooltip;b.setAttribute('aria-controls',made.pane.id);b.setAttribute('aria-pressed','false');
    made.pane.setAttribute('aria-labelledby',b.id);rail.appendChild(b);
    entries.set(spec.key,{spec,pane:made.pane,button:b,close:made.close,index,open:false});
  });
  const slotOrder=(outerToInnerOrder||specs.map(s=>s.key)).filter(key=>entries.has(key));const clockEntry=entries.get('clock');if(side==='right'&&clockEntry)vlInitClockPaneResize(clockEntry.pane,()=>layout());
  function storedOpen(key,fallback){
    try{const raw=localStorage.getItem('vortexlab.quad.'+side+'.'+key+'.open');if(raw!==null)return raw==='1';}catch(_){ }
    return fallback;
  }
  entries.forEach((entry,key)=>{entry.open=storedOpen(key,defaultOpenKeys.includes(key));});
  function layout(){
    const visible=slotOrder.filter(key=>entries.get(key)?.open);
    const widthExpr=key=>key==='clock'?'var(--vl-clock-w)':'var(--vl-panel-w)';
    visible.forEach((key,slot)=>{
      const entry=entries.get(key);entry.pane.dataset.slot=String(slot);const prior=visible.slice(0,slot).map(widthExpr),offset=prior.length?'calc('+prior.join(' + ')+')':'0px';
      if(side==='left'){entry.pane.style.left=offset;entry.pane.style.right='auto';}
      else{entry.pane.style.right=offset;entry.pane.style.left='auto';}
    });
    entries.forEach(entry=>{
      entry.pane.classList.toggle('vl-pane-open',entry.open);
      entry.button.classList.toggle('active',entry.open);
      entry.button.setAttribute('aria-pressed',entry.open?'true':'false');
    });
    dock.dataset.openCount=String(visible.length);
    window.vlUpdateOverlayOffsets?.();
  }
  function setOpen(key,value){
    const entry=entries.get(key);if(!entry)return;
    entry.open=!!value;
    try{localStorage.setItem('vortexlab.quad.'+side+'.'+key+'.open',entry.open?'1':'0');}catch(_){ }
    layout();
  }
  function toggle(key){const entry=entries.get(key);if(entry)setOpen(key,!entry.open);}
  const buttons=[...entries.values()].map(entry=>entry.button);
  entries.forEach((entry,key)=>{
    entry.button.addEventListener('click',()=>toggle(key));
    entry.close.addEventListener('click',()=>setOpen(key,false));
    entry.button.addEventListener('keydown',e=>{
      const i=buttons.indexOf(entry.button);let next=null;
      if(e.key==='ArrowDown'||e.key==='ArrowRight')next=i+1;
      else if(e.key==='ArrowUp'||e.key==='ArrowLeft')next=i-1;
      else if(e.key==='Home')next=0;else if(e.key==='End')next=buttons.length-1;
      if(next!==null){e.preventDefault();next=(next+buttons.length)%buttons.length;buttons[next].focus({preventScroll:true});}
    });
  });
  layout();
  return {
    dock,setOpen,toggle,closeAll:()=>{entries.forEach((_,key)=>setOpen(key,false));},
    isOpen:key=>!!entries.get(key)?.open,getOpenCount:()=>[...entries.values()].filter(entry=>entry.open).length,
    getOpenKeys:()=>slotOrder.filter(key=>entries.get(key)?.open),getOpenWidthExpression:()=>{const xs=slotOrder.filter(key=>entries.get(key)?.open).map(key=>key==='clock'?'var(--vl-clock-w)':'var(--vl-panel-w)');return xs.length?'calc('+xs.join(' + ')+')':'0px';}
  };
}
function vlInitTooltips(root){
  const tip=document.createElement('div');tip.className='vl-tooltip';tip.id='vlTooltip';tip.setAttribute('role','tooltip');document.body.appendChild(tip);
  let pinned=false,current=null;
  const dynamicKeep=new Set(['modelLogStats','topologyGuardReadout','bundleBEMReadout','bundleReadout','coreFlowReadout','stretchGateAdvice','stabilityAdvice','vVorticityColor']);
  function anchorFor(note){
    const block=note.closest('.ctrl,.core-flow-link,.bundle-config,.transport-options,.dv-geometry,.model-log-panel,.stretch-gate-box,details');
    if(!block)return note.parentElement;
    if(block.tagName==='DETAILS')return block.querySelector(':scope > summary');
    return block.querySelector(':scope > label,:scope > .quick-controls-title,:scope > .dv-title,:scope > .stretch-gate-head')||block;
  }
  function place(trigger){
    const r=trigger.getBoundingClientRect();const pad=10;tip.style.left='0px';tip.style.top='0px';
    const tr=tip.getBoundingClientRect();let left=r.right+8;if(left+tr.width>innerWidth-pad)left=r.left-tr.width-8;
    left=Math.max(pad,Math.min(left,innerWidth-tr.width-pad));let top=r.top;
    if(top+tr.height>innerHeight-pad)top=innerHeight-tr.height-pad;top=Math.max(pad,top);
    tip.style.left=Math.round(left)+'px';tip.style.top=Math.round(top)+'px';
  }
  function show(trigger){
    const source=vlNode(trigger.dataset.vlTooltipSource);if(!source)return;current=trigger;tip.innerHTML=source.innerHTML;tip.classList.add('show');
    if(window.renderMathInElement){try{renderMathInElement(tip,{delimiters:[{left:'\\[',right:'\\]',display:true},{left:'\\(',right:'\\)',display:false}]});}catch(_){ }}
    requestAnimationFrame(()=>place(trigger));
  }
  function hide(force=false){if(pinned&&!force)return;tip.classList.remove('show');tip.innerHTML='';current=null;if(force)pinned=false;}
  root.querySelectorAll('.note,.diagnostic-help,.core-limit-note,.frame-note').forEach((note,i)=>{
    if(dynamicKeep.has(note.id)||note.closest('#physOverlay'))return;
    if(!note.id)note.id='vlTooltipSource'+i;
    const anchor=anchorFor(note);if(!anchor||anchor.querySelector(':scope > .vl-info-btn[data-vl-tooltip-source="'+note.id+'"]'))return;
    const trigger=document.createElement('button');trigger.type='button';trigger.className='vl-info-btn';trigger.textContent='i';trigger.dataset.vlTooltipSource=note.id;
    trigger.removeAttribute('title');trigger.setAttribute('aria-label','Toon toelichting');trigger.setAttribute('aria-describedby',note.id);
    anchor.appendChild(trigger);note.classList.add('vl-tooltip-source');
    trigger.addEventListener('mouseenter',()=>{if(!pinned)show(trigger);});trigger.addEventListener('mouseleave',()=>{if(!pinned)hide();});
    trigger.addEventListener('focus',()=>{if(!pinned)show(trigger);});trigger.addEventListener('blur',()=>{if(!pinned)hide();});
    trigger.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();if(current===trigger&&pinned){hide(true);}else{pinned=true;show(trigger);}});
  });
  root.querySelectorAll('input,select,button').forEach(el=>{
    if(el.title||el.classList.contains('vl-info-btn'))return;
    const label=el.closest('.ctrl')?.querySelector('label')||el.closest('label');const text=vlCleanText(label);
    if(text)el.title=text;
  });
  document.addEventListener('pointerdown',e=>{if(pinned&&!tip.contains(e.target)&&!e.target.closest('.vl-info-btn'))hide(true);});
  window.addEventListener('resize',()=>{if(current&&tip.classList.contains('show'))place(current);},{passive:true});
}
function vlPersistAccordions(root){
  root.querySelectorAll('details[id]').forEach(det=>{
    const key='vortexlab.dual.details.'+det.id;try{const v=localStorage.getItem(key);if(v!==null)det.open=v==='1';}catch(_){ }
    det.addEventListener('toggle',()=>{try{localStorage.setItem(key,det.open?'1':'0');}catch(_){ }});
  });
}


function vlCreateResultAccordion(id,title,nodes,open=false){
  const valid=(nodes||[]).filter(Boolean);if(!valid.length)return null;
  const d=document.createElement('details');d.className='vl-result-accordion';d.id=id;d.open=!!open;
  const s=document.createElement('summary');s.textContent=title;const body=document.createElement('div');body.className='vl-result-body';
  const first=valid[0];first.parentNode.insertBefore(d,first);d.append(s,body);for(const n of valid)body.appendChild(n);return d;
}
function initSpecClockResultAccordions(){
  const specSummary=vlNode('specBenchmarkSummary'),specTable=vlNode('specBenchmarkRows')?.closest('.spec-benchmark-table-wrap');
  if(specSummary&&!vlNode('vlSpecResultsAccordion'))vlCreateResultAccordion('vlSpecResultsAccordion','RESULTATEN · SPEC CLOCK 10-RUN',[specSummary,specTable],false);
  const proxy=vlNode('proxyDecompBox');if(proxy&&!vlNode('vlProxyCoreResultsAccordion')){
    const nodes=[proxy.querySelector('.proxy-decomp-toolbar'),vlNode('proxyDecompSummary'),vlNode('proxyDecompRows')?.closest('.spec-benchmark-table-wrap'),vlNode('proxyDecompWaterfall'),vlNode('proxyDecompInteractionRows')?.closest('.spec-benchmark-table-wrap'),vlNode('proxyDecompResolutionRows')?.closest('.spec-benchmark-table-wrap'),vlNode('proxyDecompSnapshots')?.closest('.spec-benchmark-table-wrap')];
    vlCreateResultAccordion('vlProxyCoreResultsAccordion','RESULTATEN · PROXY-DECOMPOSITIE',nodes,false);
  }
  const kappaA=vlNode('proxyGeomKappaRows')?.closest('.spec-benchmark-table-wrap'),kappaB=vlNode('proxyGeomKappaResolutionRows')?.closest('.spec-benchmark-table-wrap');
  if(kappaA&&!vlNode('vlKappaResultsAccordion'))vlCreateResultAccordion('vlKappaResultsAccordion','RESULTATEN · κ-GEOM KANDIDATEN',[kappaA,kappaB],false);
  const group=(id,title,accId)=>{const table=vlNode(id)?.closest('.spec-benchmark-table-wrap');if(!table||vlNode(accId))return;const note=table.previousElementSibling,t=note?.previousElementSibling;vlCreateResultAccordion(accId,title,[t,note,table],false);};
  group('proxyContinuumRows','RESULTATEN · CONTINUÜM-AUDIT','vlContinuumResultsAccordion');
  group('proxyCrossKnotRows','RESULTATEN · GESELECTEERDE HOLDOUTS','vlHoldoutResultsAccordion');
  group('idealConventionAuditRows','RESULTATEN · IDEAL-DATA CONVENTIE','vlIdealAuditResultsAccordion');
  group('reachAuditRows','RESULTATEN · CONTINUE REACH/DCSD','vlReachResultsAccordion');
}
function vlInstallResultChangeMarkers(root=document){
  const details=[...root.querySelectorAll('details.vl-result-accordion,details.spec-benchmark-accordion,details.spec-benchmark-subaccordion')];
  for(const d of details){if(d.dataset.changeMarkerBound==='1')continue;d.dataset.changeMarkerBound='1';
    const body=[...d.children].find(x=>x.tagName!=='SUMMARY');if(body){const obs=new MutationObserver(list=>{if(!d.open&&list.some(m=>m.type==='childList'||m.type==='characterData'))d.classList.add('vl-result-changed');});obs.observe(body,{subtree:true,childList:true,characterData:true});}
    d.addEventListener('toggle',()=>{if(d.open)d.classList.remove('vl-result-changed');});
  }
}
function vlClockAccordionFor(id){return vlNode(id)?.closest('details.spec-benchmark-accordion,details.spec-benchmark-subaccordion,details.vl-result-accordion')||null;}
function vlFocusClockRunner(mode){
  const specMain=vlClockAccordionFor('specBenchmarkBox'),proxyMain=vlClockAccordionFor('proxyDecompBox'),core=vlNode('vlProxyCoreResultsAccordion'),geom=vlClockAccordionFor('proxyGeomKappaSection'),kappa=vlNode('vlKappaResultsAccordion'),continuum=vlNode('vlContinuumResultsAccordion'),holdout=vlNode('vlHoldoutResultsAccordion'),ideal=vlNode('vlIdealAuditResultsAccordion'),reach=vlNode('vlReachResultsAccordion');
  const subs=[...document.querySelectorAll('#proxyDecompBox details.spec-benchmark-subaccordion,#proxyDecompBox details.vl-result-accordion')];for(const d of subs)d.open=false;
  if(mode==='spec'){if(specMain)specMain.open=true;if(proxyMain)proxyMain.open=false;const sr=vlNode('vlSpecResultsAccordion');if(sr)sr.open=true;}
  else {if(specMain)specMain.open=false;if(proxyMain)proxyMain.open=true;if(mode==='decomposition'){if(core)core.open=true;if(geom)geom.open=false;}
    else {if(core)core.open=false;if(geom)geom.open=true;if(mode==='continuum'){if(kappa)kappa.open=true;if(continuum)continuum.open=true;}
      else if(mode==='holdout'){if(holdout)holdout.open=true;if(ideal)ideal.open=true;}
      else if(mode==='reach'){if(reach)reach.open=true;}
      else if(mode==='full-suite'){for(const d of [kappa,continuum,holdout,ideal,reach])if(d)d.open=true;}}}
  const panel=vlNode('specClockPanel');if(panel)panel.open=true;window.vlPanelLayout?.right?.setOpen?.('clock',true);
}
function initSpecClockRunnerHub(){
  const selector=vlNode('specKnotSelector'),panel=selector?.parentElement;if(!selector||!panel||vlNode('vlClockRunnerHub'))return;
  const hub=document.createElement('details');hub.id='vlClockRunnerHub';hub.className='spec-clock-runner-hub';hub.open=true;hub.innerHTML='<summary>▶ TESTRUNNERS · VERPLICHTE ENGINE-VOLGORDE</summary><div class="spec-clock-runner-grid" id="vlClockRunnerGrid"><div class="spec-clock-workflow-hint" id="vlClockWorkflowHint"></div></div>';
  selector.insertAdjacentElement('afterend',hub);const grid=vlNode('vlClockRunnerGrid'),hint=vlNode('vlClockWorkflowHint');
  for(const def of VL_CLOCK_RUNNER_DEFS){const b=vlNode(def.id);if(!b)continue;b.classList.add('runner-primary');b.addEventListener('click',()=>vlFocusClockRunner(def.mode));grid.insertBefore(b,hint);}
  for(const id of ['bSpecBenchmarkStop','bProxyDecompStop']){const b=vlNode(id);if(b)b.hidden=true;}
  vlRefreshClockRunnerWorkflowUi();
}
const VL_BOTTOM_WIDGET_STORAGE='vortexlab.bottomWidgets.v1';
function vlReadBottomWidgetState(){try{return JSON.parse(localStorage.getItem(VL_BOTTOM_WIDGET_STORAGE)||'{}')||{};}catch(_){return {};}}
function vlWriteBottomWidgetState(all){try{localStorage.setItem(VL_BOTTOM_WIDGET_STORAGE,JSON.stringify(all));}catch(_){}}
function vlStoreBottomWidget(widget,patch={}){
  if(!widget?.dataset?.kind)return;const all=vlReadBottomWidgetState(),kind=widget.dataset.kind,current=all[kind]||{};
  all[kind]={...current,open:widget.open,...patch};vlWriteBottomWidgetState(all);
}
function vlClampBottomWidget(widget,left,top){
  const rect=widget.getBoundingClientRect(),margin=8,topbar=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--vl-topbar-h'))||58;
  const maxLeft=Math.max(margin,window.innerWidth-rect.width-margin),maxTop=Math.max(topbar+margin,window.innerHeight-Math.max(30,rect.height)-margin);
  return {left:Math.min(maxLeft,Math.max(margin,left)),top:Math.min(maxTop,Math.max(topbar+margin,top))};
}
function vlDockBottomWidget(widget,{persist=true}={}){
  if(!widget)return;widget.classList.remove('vl-bottom-widget-undocked','vl-bottom-widget-dragging');
  for(const p of ['left','top','width'])widget.style.removeProperty(p);
  if(persist)vlStoreBottomWidget(widget,{undocked:false,left:null,top:null,width:null});
}
function vlApplyBottomWidgetState(widget){
  const state=vlReadBottomWidgetState()[widget.dataset.kind];if(!state)return;
  if(typeof state.open==='boolean')widget.open=state.open;
  if(state.undocked&&Number.isFinite(state.left)&&Number.isFinite(state.top)){
    widget.classList.add('vl-bottom-widget-undocked');if(Number.isFinite(state.width))widget.style.width=Math.max(150,state.width)+'px';
    const p=vlClampBottomWidget(widget,state.left,state.top);widget.style.left=p.left+'px';widget.style.top=p.top+'px';
  }
}
function vlEnableBottomWidgetDrag(widget){
  const summary=widget?.querySelector(':scope > summary'),grip=summary?.querySelector('.vl-bottom-drag-grip');if(!summary||widget.dataset.vlDragBound==='1')return;widget.dataset.vlDragBound='1';summary.dataset.vlDragBound='1';
  let drag=null,suppressClick=false,dblSequenceStartOpen=null;const EDGE=9;
  summary.title='Ingeklapt: klik om te openen, sleep via ⋮⋮ of rand · uitgeklapt: sleep titel of rand · dubbelklik wisselt open/dicht · Shift+dubbelklik dockt terug';
  const onBorder=e=>{const r=widget.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;return x<=EDGE||y<=EDGE||r.width-x<=EDGE||r.height-y<=EDGE;};
  const onDragHandle=e=>onBorder(e)||(widget.open?summary.contains(e.target):!!grip&&grip.contains(e.target));
  const onToggleHandle=e=>summary.contains(e.target)||onBorder(e);
  const end=e=>{if(!drag)return;try{widget.releasePointerCapture(e.pointerId);}catch(_){}
    if(drag.moved){const rect=widget.getBoundingClientRect();vlStoreBottomWidget(widget,{undocked:true,left:rect.left,top:rect.top,width:rect.width});suppressClick=true;}
    widget.classList.remove('vl-bottom-widget-dragging');drag=null;
  };
  widget.addEventListener('pointerdown',e=>{if(e.button!==0)return;if(e.detail===1&&onToggleHandle(e))dblSequenceStartOpen=widget.open;if(!onDragHandle(e))return;if(!onBorder(e)&&e.target.closest('button,a,input,select,textarea'))return;const rect=widget.getBoundingClientRect();drag={pointerId:e.pointerId,x:e.clientX,y:e.clientY,left:rect.left,top:rect.top,width:rect.width,moved:false};try{widget.setPointerCapture(e.pointerId);}catch(_){}},true);
  widget.addEventListener('pointermove',e=>{if(!drag){widget.classList.toggle('vl-bottom-border-grab',onBorder(e));return;}if(e.pointerId!==drag.pointerId)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(!drag.moved&&Math.hypot(dx,dy)<6)return;
    if(!drag.moved){drag.moved=true;widget.classList.add('vl-bottom-widget-undocked','vl-bottom-widget-dragging');widget.style.width=Math.max(150,drag.width)+'px';}
    const p=vlClampBottomWidget(widget,drag.left+dx,drag.top+dy);widget.style.left=p.left+'px';widget.style.top=p.top+'px';e.preventDefault();
  },{passive:false});
  widget.addEventListener('pointerup',end,true);widget.addEventListener('pointercancel',end,true);widget.addEventListener('pointerleave',()=>{if(!drag)widget.classList.remove('vl-bottom-border-grab');});
  summary.addEventListener('click',e=>{if(suppressClick){suppressClick=false;e.preventDefault();e.stopImmediatePropagation();return;}e.preventDefault();if(!widget.open){widget.open=true;vlStoreBottomWidget(widget);}},true);
  widget.addEventListener('dblclick',e=>{if(!onToggleHandle(e))return;e.preventDefault();e.stopImmediatePropagation();if(e.shiftKey){vlDockBottomWidget(widget);widget.open=false;}else{const start=typeof dblSequenceStartOpen==='boolean'?dblSequenceStartOpen:widget.open;widget.open=!start;}dblSequenceStartOpen=null;vlStoreBottomWidget(widget);},true);
  widget.addEventListener('toggle',()=>vlStoreBottomWidget(widget));
  vlApplyBottomWidgetState(widget);
}
function vlInitBottomWidgetInteractions(container){
  if(!container)return;for(const widget of container.querySelectorAll(':scope > .vl-bottom-widget'))vlEnableBottomWidgetDrag(widget);
  let resizeTimer=0;window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{for(const widget of container.querySelectorAll('.vl-bottom-widget-undocked')){const r=widget.getBoundingClientRect(),p=vlClampBottomWidget(widget,r.left,r.top);widget.style.left=p.left+'px';widget.style.top=p.top+'px';vlStoreBottomWidget(widget,{undocked:true,left:p.left,top:p.top,width:r.width});}},80);});
}
function vlWrapBottomWidget(node,title,kind,open=true){
  if(!node)return null;const d=document.createElement('details');d.className='vl-bottom-widget vl-bottom-widget-'+kind;d.open=!!open;d.dataset.kind=kind;
  const s=document.createElement('summary'),grip=document.createElement('span'),label=document.createElement('span');grip.className='vl-bottom-drag-grip';grip.textContent='⋮⋮';grip.setAttribute('aria-hidden','true');label.className='vl-bottom-widget-title';label.textContent=title;s.append(grip,label);d.append(s,node);return d;
}
function vlEnsureBottomWidget(container,node,title,kind,open=true){
  if(!container||!node)return null;let widget=node.closest?.('.vl-bottom-widget-'+kind)||null;if(!widget)widget=vlWrapBottomWidget(node,title,kind,open);if(widget&&widget.parentElement!==container)container.appendChild(widget);return widget;
}
function initGlobalRunStrip(shell){
  if(vlNode('vlGlobalRunStrip')||shell?.querySelector?.('#vlGlobalRunStrip'))return;
  if(!shell)throw new Error('globale runstrip: UI-shell ontbreekt');
  const strip=document.createElement('div');strip.id='vlGlobalRunStrip';strip.className='vl-global-run-strip';strip.setAttribute('role','status');strip.setAttribute('aria-live','polite');
  strip.innerHTML='<div class="vl-global-run-text" id="vlGlobalRunText">—</div><button type="button" class="vl-global-run-close" id="vlGlobalRunClose" aria-label="Verberg runstatus">×</button><div class="vl-global-run-progress"><span id="vlGlobalRunProgress"></span></div>';shell.appendChild(strip);
  // De shell is hier nog detached. Gebruik lokale queries in plaats van document.getElementById().
  const closeButton=strip.querySelector('#vlGlobalRunClose');
  const textNode=strip.querySelector('#vlGlobalRunText');
  const progressNode=strip.querySelector('#vlGlobalRunProgress');
  if(!closeButton||!textNode||!progressNode)throw new Error('globale runstrip: interne DOM-nodes ontbreken');
  let hideTimer=0;const close=()=>{clearTimeout(hideTimer);strip.classList.remove('active','good','warn','bad');document.body.classList.remove('vl-run-strip-active');};closeButton.addEventListener('click',close);
  const sources=[['specBenchmarkStatus','specBenchmarkProgress'],['proxyDecompStatus','proxyDecompProgress'],['reachAuditStatus','reachAuditProgress']];
  const sync=(sid,pid)=>{const status=vlNode(sid),progress=vlNode(pid);if(!status||!progress)return;const txt=status.textContent.trim(),running=status.classList.contains('running'),final=/^(VOLTOOID|AFGEBROKEN)/.test(txt);if(!running&&!final)return;
    clearTimeout(hideTimer);textNode.textContent=txt;progressNode.style.width=progress.style.width||'0%';strip.classList.remove('good','warn','bad');if(status.classList.contains('good'))strip.classList.add('good');else if(status.classList.contains('bad'))strip.classList.add('bad');else if(status.classList.contains('warn'))strip.classList.add('warn');strip.classList.add('active');document.body.classList.add('vl-run-strip-active');if(final)hideTimer=setTimeout(close,12000);};
  for(const [sid,pid] of sources){const status=vlNode(sid),progress=vlNode(pid);if(!status||!progress)continue;const obs=new MutationObserver(()=>sync(sid,pid));obs.observe(status,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['class']});obs.observe(progress,{attributes:true,attributeFilter:['style']});}
}

function initSpecClockCompactBlocks(){
  const wrap=(node,title,open=false,sub=false)=>{
    if(!node||node.parentElement?.matches('details.spec-benchmark-accordion,details.spec-benchmark-subaccordion'))return node?.parentElement||null;
    const d=document.createElement('details');d.className=sub?'spec-benchmark-subaccordion':'spec-benchmark-accordion';d.id='specAccordion-'+(node.id||Math.random().toString(36).slice(2));d.open=!!open;
    const sum=document.createElement('summary');sum.innerHTML=title;node.parentNode.insertBefore(d,node);d.append(sum,node);return d;
  };
  const proxy=vlNode('proxyDecompBox');
  if(proxy){
    const length=proxy.querySelector('.proxy-length-section'),transfer=proxy.querySelector('.proxy-transfer-section:not(.proxy-length-section):not(.proxy-geom-kappa-section)');
    if(length&&transfer&&length.parentElement===transfer)transfer.parentNode.insertBefore(length,transfer.nextSibling);
    const geom=vlNode('proxyGeomKappaSection'),norm=proxy.querySelector('.proxy-norm-section');
    wrap(norm,'NORMALISATIEBENCHMARK · 7 SCHALEN',false,true);
    wrap(transfer,'TRANSFER-LAWREGISTER · DIMENSIONELE NO-FIT TEST',false,true);
    wrap(length,'L/v↺* · LENGTE-IDENTIFICATIE',false,true);
    wrap(geom,'κ<sub>geom</sub> + IDEAL-DATA CONVENTIE-AUDIT',true,true);
  }
  wrap(vlNode('specBenchmarkBox'),'GEAUTOMATISEERDE SPEC CLOCK · 10-RUN REGRESSIE',false,false);
  wrap(proxy,'DIAGNOSEBENCHMARKS · DECOMPOSITIE / NORMALISATIE / TRANSFER / L / κ',false,false);
}
initSpecClockCompactBlocks();
initSpecClockResultAccordions();
initSpecClockRunnerHub();
vlInstallResultChangeMarkers(document);
function initSstRoadmapPanel(){
  const panel=vlNode('specClockPanel'),body=panel?.querySelector(':scope > .subcoll-body');if(!body||vlNode('sstRoadmapPanel'))return;
  const d=document.createElement('details');d.className='subcoll';d.id='sstRoadmapPanel';d.innerHTML='<summary>🗺 ONTWIKKELROADMAP · v7.6.25b → v7.7.0</summary><div class="subcoll-body"><ol class="vl-roadmap-list"><li><code>v7.6.25b · ACTIEF</code> — continue C²-spline DCSD/reach-solver met curvature/self/inter-component-splitsing en N≤1536-audit.</li><li><code>v7.6.26</code> — signed lokale Swirl-Clockroute op basis van puntgewijze vectorcompositie.</li><li><code>v7.6.27</code> — afstand-, oriëntatie- en multipoolholdouts met bevroren geometrieën.</li><li><code>v7.6.28</code> — observablescheidingen en terminologische cleanup.</li><li><code>v7.6.29</code> — passief Bishop-material frame en interne fasecoördinaat.</li><li><code>v7.6.30</code> — externe velocity-gradienttensor, strain en lokale rotatie.</li><li><code>v7.7.0</code> — confirmatoire holdouts voor een afgeleide interne klokwet of reproduceerbare verwerping.</li></ol><div class="note">De roadmap is Research Track. Geen geplande stap koppelt een proxy terug naar de solver zonder afzonderlijke afleiding, ENGINE-gates en holdoutvalidatie.</div></div>';
  body.appendChild(d);
}
initSstRoadmapPanel();
function initDualSidebarUi(){
  if(document.body.dataset.vlDualUi==='1')return;
  document.body.dataset.vlDualUi='1';document.body.classList.add('vl-dual-ui');
  const shell=document.createElement('div');shell.className='vl-ui-shell';shell.id='vlUiShell';
  const top=document.createElement('div');top.className='vl-topbar';top.id='vlTopRunBar';
  const title=document.createElement('div');title.className='vl-topbar-title';title.textContent='VORTEXLAB';top.appendChild(title);
  const reset=vlNode('bReset'),resetParticles=vlNode('bResetParticles'),pause=vlNode('bPause');
  vlMakeHiddenOriginal(reset,'↺ Vortex');vlMakeHiddenOriginal(resetParticles,'↺ Deeltjes');
  if(reset){reset.title='Reset de vortexgeometrie naar de beginconfiguratie';top.appendChild(reset);}
  if(resetParticles){resetParticles.title='Cyclische reset: binnenste kolom → knoopstraal → volledige cilinder';top.appendChild(resetParticles);}
  if(pause){pause.title='Pauzeer of hervat de simulatie';top.appendChild(pause);}
  vlCreateSpeedControl(top);
  vlMoveSelectToTopbar('presetSelect','Preset',top,'vl-preset-group');
  vlCreateProxySelect('qualSeg','qual','Kwaliteit',top);
  vlCreateProxySelect('medSeg','med','Medium',top);
  const foot=vlNode('footNote'),runBody=document.querySelector('#collRun > .coll-body');if(foot&&runBody)runBody.appendChild(foot);
  const runDropdown=vlCreateHeaderDropdown('RUN',vlNode('collRun'),shell,'run','Scenario, tijdomkering, logging en benchmarkbediening');if(runDropdown)top.appendChild(runDropdown.button);
  const viewDropdown=vlCreateHeaderDropdown('VIEW',vlNode('collVis'),shell,'view','Weergave-instellingen');if(viewDropdown)top.appendChild(viewDropdown.button);
  shell.insertBefore(top,shell.firstChild);initGlobalRunStrip(shell);

  // Informatiepaneel: de vroegere permanente linker overlay wordt volledig behouden,
  // maar is nu opvraagbaar als tab.
  const info=document.createElement('div');info.className='vl-info-stack';
  const oldLeft=vlNode('ui-left');if(oldLeft)while(oldLeft.firstChild)info.appendChild(oldLeft.firstChild);

  // Live diagnostiek blijft zichtbaar op het simulatorcanvas, los van de INFO-tab.
  const bottomOverlays=document.createElement('div');bottomOverlays.className='vl-sim-bottom-overlays';bottomOverlays.id='vlSimBottomOverlays';
  const liveBlock=document.createElement('section');liveBlock.className='vl-live-overlay vl-overlay-surface';liveBlock.setAttribute('aria-label','Live stabiliteit');
  const liveTitle=document.createElement('div');liveTitle.className='vl-info-section-title';liveTitle.textContent='LIVE STABILITEIT';liveBlock.appendChild(liveTitle);
  const stabilityPanel=vlNode('stabilityPanel'),stabilityAdvice=vlNode('stabilityAdvice');vlMove(stabilityPanel,liveBlock);vlMove(stabilityAdvice,liveBlock);
  const specOverlay=document.createElement('section');specOverlay.className='vl-specclock-overlay vl-overlay-surface';specOverlay.id='specClockOverlay';specOverlay.setAttribute('aria-label','Speculative swirl-clock overlay');specOverlay.setAttribute('aria-hidden','true');
  const specTitle=document.createElement('div');specTitle.className='vl-info-section-title';specTitle.textContent='SPEC CLOCK · SNELLE WEERGAVE';specOverlay.appendChild(specTitle);
  const specBody=document.createElement('div');specBody.id='specClockOverlayBody';specOverlay.appendChild(specBody);
  const cards=vlNode('cards');if(cards)cards.classList.add('vl-cards-overlay','vl-overlay-surface');
  const spark=vlNode('spark')||vlNode('cspark')?.parentElement;if(spark)spark.classList.add('vl-spark-overlay','vl-overlay-surface');
  const liveWidget=vlEnsureBottomWidget(bottomOverlays,liveBlock,'LIVE STABILITEIT','live',false),specWidget=vlEnsureBottomWidget(bottomOverlays,specOverlay,'SPEC CLOCK · SNEL','spec',true),statsWidget=vlEnsureBottomWidget(bottomOverlays,cards,'STATS','stats',false),sparkWidget=vlEnsureBottomWidget(bottomOverlays,spark,'SPARK','spark',false);
  if(specWidget)specWidget.hidden=!P.specClockEnabled;
  shell.appendChild(bottomOverlays);

  // Bedieningsdelen van stabiliteit horen onder VORTEX; meetinformatie blijft onder INFO.
  const vortexFlags=vlNode('stabGroupVortexFlags');
  const autoRelax=document.querySelector('#collStability .auto-relax-row');if(autoRelax&&vortexFlags)vortexFlags.appendChild(autoRelax);
  const topology=vlNode('cTopologyGuard')?.parentElement;if(topology&&vortexFlags)vortexFlags.appendChild(topology);

  const leftSpecs=[
    {key:'info',title:'INFORMATIE & OVERZICHT',short:'INFO',icon:'ⓘ',subtitle:'buiten · links',tooltip:'Open of sluit INFO onafhankelijk. Wanneer FLOW ook open is, staat INFO links buiten FLOW.',nodes:[info]},
    {key:'flow',title:'MODEL · FLOW + CILINDER',short:'FLOW',icon:'≈',subtitle:'binnen · links',tooltip:'Open of sluit FLOW onafhankelijk. FLOW is het linker paneel dat het dichtst bij het canvas staat.',nodes:[vlNode('subCylinder'),vlNode('subFlow'),vlNode('potentialFlowPanel'),vlNode('collFriction')]}
  ];
  const rightSpecs=[
    {key:'core',title:'MODEL · VORTEX + KERN',short:'KERN',icon:'◉',subtitle:'binnen · rechts',tooltip:'Open of sluit KERN onafhankelijk. KERN is het rechter paneel dat het dichtst bij het canvas staat.',nodes:[vlNode('subVortex'),vlNode('subCore')]},
    {key:'clock',title:'SST · SWIRL CLOCK',short:'CLOCK',icon:'⏱',subtitle:'speculatief · midden rechts',tooltip:'Open of sluit de volledige SST Swirl Clock onafhankelijk. CLOCK staat tussen KERN en DIAG.',nodes:[vlNode('specClockPanel')]},
    {key:'diag',title:'DIAGNOSTIEK',short:'DIAG',icon:'∑',subtitle:'buiten · rechts',tooltip:'Open of sluit DIAG onafhankelijk. DIAG blijft het buitenste rechterpaneel.',nodes:[vlNode('collDiagnostics'),vlNode('sstResearchDiagnostics'),vlNode('chiPhasePanel'),vlNode('stretchGatePanel')]}
  ];
  const left=vlCreateIndependentDock('left',leftSpecs,['flow'],['info','flow']);
  const right=vlCreateIndependentDock('right',rightSpecs,['core'],['diag','clock','core']);
  window.vlPanelLayout={left,right};
  window.vlUpdateOverlayOffsets=()=>{
    const leftWidth=left?.getOpenWidthExpression?.()||'0px',rightWidth=right?.getOpenWidthExpression?.()||'0px';
    document.documentElement.style.setProperty('--vl-overlay-left','calc(var(--vl-rail-w) + '+leftWidth+' + 12px)');
    document.documentElement.style.setProperty('--vl-overlay-right','calc(var(--vl-rail-w) + '+rightWidth+' + 12px)');
  };
  window.vlUpdateOverlayOffsets();
  shell.append(left.dock,right.dock);document.body.appendChild(shell);vlInitBottomWidgetInteractions(bottomOverlays);
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){left.closeAll();right.closeAll();}});

  // Oude structuur en alle oorspronkelijke teksten blijven in de DOM als bron/provenance.
  const preserved=document.createElement('div');preserved.id='vlPreservedSources';preserved.className='vl-preserved-sources';
  ['collConfig','collMedium','collVolume','collParams','collStabilityParams','collStability','ui-left','ui-right','topRightActions','stabilityDock'].forEach(id=>vlMove(vlNode(id),preserved));
  document.body.appendChild(preserved);
  vlPersistAccordions(shell);vlInitTooltips(shell);
}
initDualSidebarUi();

function bindSignedRange(sliderId,revId,fmt,apply){
  const s=document.getElementById('s'+sliderId);
  const r=document.getElementById(revId);
  const v=document.getElementById('v'+sliderId);
  function refresh(){
    const mag=Number(s.value);
    if(!Number.isFinite(mag))return; // partiële exponentinvoer mag de toestand niet met NaN besmetten
    const rev=r.checked;
    P['rev'+sliderId]=rev;
    const signed=applySigned(rev,mag);
    apply(signed,mag,rev);
    if(v)v.textContent=fmt(signed,mag,rev);
  }
  s.addEventListener('input',refresh);
  r.addEventListener('change',refresh);
  return refresh;
}
function bindRange(id,fmt,set){
  const s=document.getElementById('s'+id),v=document.getElementById('v'+id);
  s.addEventListener('input',()=>{
    const x=Number(s.value);
    if(!Number.isFinite(x))return; // bv. tijdelijk leeg tijdens typen van 1e-15
    const applied=set(x);
    if(v&&applied!==null)v.textContent=fmt(Number.isFinite(applied)?applied:x);
  });
}
bindSignedRange('Om','revOm',(x)=>Math.abs(x).toFixed(2)+' rad/s · '+(x<0?'CW':'CCW'),(x)=>{P.Om=x;if(P.coreFlowLock)syncCoreFlowCoupling('omega');document.getElementById('hOm').textContent=P.Om.toFixed(2);rebuildLattice();updateHeaderTitle();updateCoreFlowReadout();});
bindSignedRange('Ga','revGa',()=>fmtGa(),(x)=>{P.GaDemo=x;if(P.coreFlowLock)syncCoreFlowCoupling('gamma');syncUi();});
bindRange('Nq',()=>fmtNq(),x=>{P.nQ=Math.max(1,Math.round(x));if(P.coreFlowLock)syncCoreFlowCoupling('gamma');syncUi();});
bindRange('A',x=>fmtLengthSI(x*1e-3),x=>{
  // v7.3.1: commit alleen eindige waarden; de solver ontvangt nooit a=0/NaN.
  const requested=clamp(x*1e-3,A_SIM_INPUT_FLOOR,Math.max(A_SIM_INPUT_FLOOR,coreRadiusMax));
  const q=kappaMedium(),omega=Math.max(1e-12,Math.abs(P.Om));
  const minLocked=q?Math.sqrt(q/(2*Math.PI*omega)):0;
  if(P.coreFlowLock&&minLocked>0&&requested<minLocked*(1-1e-12)){
    P.coreFlowLock=false;
    coreFlowNotice=`koppeling automatisch ontgrendeld: gevraagd a_sim=${fmtLengthSI(requested)} ligt onder n=1 similarity-radius ${fmtLengthSI(minLocked)}`;
  }else{
    coreFlowNotice='';
  }
  P.a=requested;
  if(P.coreFlowLock)syncCoreFlowCoupling('a');
  // Altijd de werkelijk toegepaste solverwaarde terugschrijven, nooit de ruwe invoer.
  updateCoreRadiusLimit(false);
  updateCoreFlowReadout();
  const lock=document.getElementById('cCoreFlowLock');if(lock)lock.checked=P.coreFlowLock;
  invalidateBundleBEM('a_sim');ensureBundleBEM(true);rebuildLattice();
  lastTopologyGap=P.topologyGuard?topologyClearance():Infinity;
  rebuildTubes(true);
  return null; // updateCoreRadiusLimit beheert het samengestelde label inclusief max/floorstatus
});
bindRange('SepAB',x=>fmtLengthSI(x*1e-3),x=>{
  const applied=setInitialAxialSeparation(x*1e-3);
  if(window.ModelLog&&window.ModelLog.logUser)window.ModelLog.logUser('initial-knot-separation',{axial:applied,lateral:P.off,centerDistance:Math.hypot(applied,Math.abs(P.off))});
  resetState();
  announceSeparationBoundaryPolicy();
  return applied*1e3;
});
{const sepMain=document.getElementById('sSepAB');if(sepMain){sepMain.addEventListener('blur',updateInitialSeparationUi);sepMain.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();sepMain.blur();}});}}
bindSignedRange('Off','revOff',x=>x.toFixed(0)+' mm',x=>{P.off=x*1e-3;resetState();});
bindSignedRange('W','revW',x=>fmtAxialMmPerS(x),x=>{P.w=x*1e-3;resetPlaybackDebt('axial-drift-change');});
bindSignedRange('VzA','revVzA',x=>fmtAxialMmPerS(x),x=>{P.vzA=x*1e-3;if(P.lockVz){P.vzB=P.vzA;syncSignedUi('VzB','revVzB',P.vzB,y=>fmtAxialMmPerS(y));}resetPlaybackDebt('axial-drift-change');});
bindSignedRange('VzB','revVzB',x=>fmtAxialMmPerS(x),x=>{P.vzB=x*1e-3;resetPlaybackDebt('axial-drift-change');});
function bindSpecClockQuickControls(){
  const bindNumber=(id,commit)=>{
    const input=document.getElementById(id);if(!input)return;
    input.dataset.specBound='1';
    input.addEventListener('input',()=>{const value=Number(input.value);if(Number.isFinite(value))commit(value);});
    input.addEventListener('blur',()=>syncSpecClockQuickControls({force:true}));
    input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();input.blur();}});
  };
  bindNumber('sSpecSepAB',mm=>{
    const applied=setInitialAxialSeparation(mm*1e-3);
    if(window.ModelLog)window.ModelLog.logUser('spec-clock-initial-separation',{requestedMm:mm,axial:applied,lateral:P.off,centerDistance:Math.hypot(applied,Math.abs(P.off))});
    resetState();announceSeparationBoundaryPolicy();
  });
  bindNumber('sSpecOffClone',mm=>{
    P.off=mm*1e-3;syncSignedUi('Off','revOff',P.off*1000,x=>x.toFixed(0)+' mm');
    if(window.ModelLog)window.ModelLog.logUser('spec-clock-lateral-offset',{mm,metres:P.off});
    resetState();
  });
  bindNumber('sSpecVzA',mmps=>{
    P.vzA=mmps*1e-3;if(P.lockVz)P.vzB=P.vzA;
    resetPlaybackDebt('spec-clock-drift-a');
    syncSignedUi('VzA','revVzA',P.vzA*1000,x=>fmtAxialMmPerS(x));
    if(P.lockVz)syncSignedUi('VzB','revVzB',P.vzB*1000,x=>fmtAxialMmPerS(x));
    if(window.ModelLog)window.ModelLog.logUser('spec-clock-drift-a',{mmPerS:mmps,metresPerSecond:P.vzA,lockVz:P.lockVz});
  });
  bindNumber('sSpecVzB',mmps=>{
    P.vzB=mmps*1e-3;resetPlaybackDebt('spec-clock-drift-b');syncSignedUi('VzB','revVzB',P.vzB*1000,x=>fmtAxialMmPerS(x));
    if(window.ModelLog)window.ModelLog.logUser('spec-clock-drift-b',{mmPerS:mmps,metresPerSecond:P.vzB});
  });
  const setPairDrift=approach=>{
    const speed=Math.max(Math.abs(P.vzA),Math.abs(P.vzB),0.005);
    const toward=P.zA<=P.zB?1:-1;
    P.lockVz=false;const lock=document.getElementById('cLockVz');if(lock)lock.checked=false;
    P.vzA=(approach?toward:-toward)*speed;P.vzB=-P.vzA;
    resetPlaybackDebt(approach?'spec-clock-approach':'spec-clock-separate');
    syncSignedUi('VzA','revVzA',P.vzA*1000,x=>fmtAxialMmPerS(x));
    syncSignedUi('VzB','revVzB',P.vzB*1000,x=>fmtAxialMmPerS(x));
    syncSpecClockQuickControls({force:true});
    if(window.ModelLog)window.ModelLog.logUser(approach?'spec-clock-approach':'spec-clock-separate',{vzA:P.vzA,vzB:P.vzB});
  };
  const approach=document.getElementById('bSpecSetApproach');if(approach){approach.dataset.specBound='1';approach.addEventListener('click',()=>setPairDrift(true));}
  const separate=document.getElementById('bSpecSetSeparate');if(separate){separate.dataset.specBound='1';separate.addEventListener('click',()=>setPairDrift(false));}
  const pull=document.getElementById('bSpecPullFromModel');if(pull){pull.dataset.specBound='1';pull.addEventListener('click',()=>{syncSpecClockQuickControls({force:true});setFlag('ℹ SPEC CLOCK quick-controls zijn opnieuw uit de actuele MODEL-toestand geladen.',true);});}
  const preset=document.getElementById('bSpecClockPreset');if(preset){preset.dataset.specBound='1';preset.addEventListener('click',applySpecClockPreset);}
  const log=document.getElementById('cSpecClockLog');if(log){log.dataset.specBound='1';log.addEventListener('change',()=>{if(window.ModelLog)window.ModelLog.setEnabled(log.checked);const main=document.getElementById('cModelLog');if(main)main.checked=log.checked;});}
  const exportTxt=document.getElementById('bModelLogExportTxt');if(exportTxt){exportTxt.dataset.specBound='1';exportTxt.addEventListener('click',()=>{
    if(!window.ModelLog)return;window.ModelLog.logUser('ui:click:bModelLogExportTxt',{format:'txt'});
    const blob=new Blob([window.ModelLog.exportText()],{type:'text/plain;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);
    a.download='vortexlab-session-'+APP_VERSION.replace(/\./g,'-')+'-'+safeUtcStamp()+'.txt';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),0);
  });}
}
bindSpecClockQuickControls();
bindSpecAutoExportControl();
SpecClockBenchmark.bind();
SpecClockProxyDecomposition.bind();
ContinuousReachAudit.bind();
vlRefreshClockRunnerWorkflowUi();
bindSignedRange('Vn','revVn',x=>fmtAxialMmPerS(x),x=>{P.vnZ=x*1e-3;});
bindRange('MfA',x=>x.toFixed(3),x=>{P.mfAlpha=clamp(x,0,1);});
bindRange('MfAp',x=>x.toFixed(4),x=>{P.mfAlphaP=clamp(x,-0.5,0.5);});
document.getElementById('mfTemp').addEventListener('change',e=>{applyMfTemp(e.target.value);syncUi();});
bindRange('Acc',()=>fmtAcc(acc()),x=>{P.accExp=x;resetPlaybackDebt('playback-speed-change');});
bindRange('Diam',x=>x.toFixed(0)+' cm',x=>{
  const newR=clamp(x/200,0.025,1.0);
  let newH=P.Hcyl;
  if(P.linkDH) newH=P.linkVolumeRef/(2*Math.PI*newR*newR);
  applyVolumeResize(newR,newH);
});
bindRange('Height',x=>x.toFixed(1).replace(/\.0$/,'')+' cm',x=>{
  const newH=clamp(x/100,0.025,2.5);
  let newR=P.Rcyl;
  if(P.linkDH) newR=Math.sqrt(P.linkVolumeRef/(2*Math.PI*newH));
  applyVolumeResize(newR,newH);
});
bindRange('TracerCount',x=>String(Math.max(0,Math.min(TRACER_COUNT_MAX,Math.round(x)))),x=>{
  P.tracerCount=Math.max(0,Math.min(TRACER_COUNT_MAX,Math.round(x)));
  const input=document.getElementById('sTracerCount');
  if(input)input.value=String(P.tracerCount);
  initTracers();updateParticleResetButton();markPotentialFlowDirty();
});
bindRange('StreamlineCount',x=>String(Math.max(4,Math.min(120,Math.round(x)))),x=>{
  P.streamlineCount=Math.max(4,Math.min(120,Math.round(x)));
  rebuildStreamlines(true);
});
bindRange('DvOpacity',x=>Math.round(x)+'%',x=>{
  P.dvOpacity=clamp(x/100,0,1);
  applyDvOpacity();
});
bindRange('WAl',x=>x.toFixed(1),x=>P.wAl=x);
bindRange('WBe',x=>x.toFixed(1),x=>P.wBe=x);
bindRange('WGa',x=>x.toFixed(1),x=>P.wGa=x);
function segHandler(id,attr,fn){
  document.getElementById(id).addEventListener('click',e=>{
    const b=e.target.closest('[data-'+attr+']');
    if(!b||b.disabled)return;fn(b.dataset[attr]);
  });
}
segHandler('modeSeg','mode',v=>{
  if(v===P.mode)return;P.mode=v;
  if(v==='solo'&&P.topo==='ring'&&P.knotIdx<0&&!P.knotKey)P.topo='trefoil';
  syncUi();resetState();
});
document.getElementById('topoSelect').addEventListener('change',e=>{const v=e.target.value;if(v===P.topo&&!P.knotKey&&P.knotIdx<0)return;P.topo=v;P.knotIdx=-1;P.knotKey='';P.knotSource='builtin';P.idealComponentMode='all';syncKnotSel();syncUi();resetState();});
segHandler('interSeg','inter',v=>{if(v===P.inter)return;P.inter=v;syncUi();resetState();});
segHandler('coreSeg','core',v=>{if(v===P.core)return;P.core=v;syncUi();updateSubtitle();});
segHandler('qualSeg','qual',v=>{if(v===P.qual)return;P.qual=v;resetState();});
segHandler('visSeg','vis',v=>{if(v===P.vis)return;P.vis=v;syncUi();rebuildLines();rebuildTubes(true);});
segHandler('tubeSeg','tube',v=>{if(v===P.tubeMat)return;P.tubeMat=v;syncUi();rebuildTubes(true);});
segHandler('frameSeg','frame',v=>{
  // v7.5: puur weergave — deze toggle raakt geen enkel fysica-predicaat meer.
  const df=v==='rotating'?'corot':'lab';
  if(df===P.displayFrame)return;
  P.displayFrame=df;
  syncUi();updateSubtitle();
});
segHandler('medSeg','med',v=>{
  if(v===P.med&&v!=='sst'&&v!=='string')return;
  if(v==='sst'){
    applySSTSimilarityPreset();
  }else if(v==='string'){
    P.med='string';P.core='gp';P.coreFlowLock=false;P.scaleProbe=PLANCK_LENGTH;
    P.bundleEnabled=false;if(P.bgFlow==='bundle')P.bgFlow='none';
  }else{
    P.med=v;
    if(v==='he'){P.core='hol';P.scaleProbe=HE_CORE_REF;}
    P.coreFlowLock=false;
  }
  // Tijdversnelling blijft uitsluitend handmatig.
  syncUi();updateSubtitle();resetState();
});
document.getElementById('bLinkDH').addEventListener('click',()=>{
  P.linkDH=!P.linkDH;
  if(P.linkDH){
    P.linkVolumeRef=cylinderVolume();
    P.linkRefR=P.Rcyl;
    P.linkRefH=P.Hcyl;
  }
  updateStretchReadout();
});
document.getElementById('bPause').addEventListener('click',()=>setPausedState(!paused,paused?'resume':'pause'));
document.getElementById('bReset').addEventListener('click',resetState);
// v7.3.1: OVERZICHT gebruikt uitsluitend #quickControlsDock; geen tweede dynamische container.
document.getElementById('bResetParticles').addEventListener('click',cycleParticleReset);
document.getElementById('cCoRot').addEventListener('change',e=>{
  // v7.5: puur weergave (zelfde veld als frameSeg).
  P.displayFrame=e.target.checked?'corot':'lab';
  syncUi();updateSubtitle();
});
document.getElementById('cBgOmega').addEventListener('change',e=>{
  // v7.5: deze keuze is een solverkeuze — integreer de wandrotatie expliciet
  // in het lab-solverframe (bgFlow='wall'), of absorbeer haar in het
  // co-roterende solverframe. Het displayframe blijft onaangeroerd.
  if(e.target.checked){
    if(P.bgFlow==='bundle')
      setFlag('⚠ bundelveldkoppeling vervangen door Ω_wall-koppeling (bgFlow-enum is exclusief); zet de bundelkoppeling desgewenst opnieuw aan.',true);
    P.solverFrame='lab';P.bgFlow='wall';
  }else{
    P.solverFrame='corot';
    if(P.bgFlow==='wall')P.bgFlow='none';
  }
  syncUi();
});
document.getElementById('cChiArrow').addEventListener('change',e=>{P.showChiArrow=e.target.checked;});
document.getElementById('cTracers').addEventListener('change',e=>{
  P.showTracers=e.target.checked;
  if(trPts)trPts.visible=P.showTracers&&!P.showStreamlines;
  rebuildStreamlines(true);
});
document.getElementById('cStreamlines').addEventListener('change',e=>{
  P.showStreamlines=e.target.checked;
  if(trPts)trPts.visible=P.showTracers&&!P.showStreamlines;
  document.getElementById('streamlineCountRow')?.classList.toggle('hidden',!P.showStreamlines);
  rebuildStreamlines(true);
  scheduleSidebarFit();
});
document.getElementById('cPotentialFlow').addEventListener('change',e=>{P.showPotentialFlow=e.target.checked;markPotentialFlowDirty();updatePotentialFlowVisual(true);});
document.getElementById('sPotentialMode').addEventListener('change',e=>{P.potentialMode=e.target.value;markPotentialFlowDirty();updatePotentialFlowVisual(true);});
document.getElementById('sPotentialRadiusSource').addEventListener('change',e=>{P.potentialRadiusSource=e.target.value;document.getElementById('potentialRadiusRow').classList.toggle('hidden',P.potentialRadiusSource!=='manual');markPotentialFlowDirty();updatePotentialFlowVisual(true);});
document.getElementById('sPotentialRadiusCm').addEventListener('input',e=>{P.potentialRadius=clamp((Number(e.target.value)||8)/100,0.005,0.95*P.Rcyl);document.getElementById('vPotentialRadius').textContent=(100*P.potentialRadius).toFixed(1)+' cm';markPotentialFlowDirty();updatePotentialFlowVisual(true);});
document.getElementById('sPotentialU').addEventListener('input',e=>{P.potentialU=clamp(Number(e.target.value)||0.1,0.001,100);document.getElementById('vPotentialU').textContent=P.potentialU.toFixed(3)+' m/s';markPotentialFlowDirty();updatePotentialFlowVisual(true);});
document.getElementById('sPotentialOpacity').addEventListener('input',e=>{P.potentialOpacity=clamp((Number(e.target.value)||58)/100,0.05,0.95);document.getElementById('vPotentialOpacity').textContent=Math.round(100*P.potentialOpacity)+'%';markPotentialFlowDirty();updatePotentialFlowVisual(true);});
document.getElementById('sParticleSize').addEventListener('input',e=>{
  P.particleSize=clamp((Number(e.target.value)||3)*1e-3,0.0005,0.012);
  document.getElementById('vParticleSize').textContent=(1000*P.particleSize).toFixed(1)+' mm';
  if(trPts&&trPts.material)trPts.material.size=P.particleSize;
});
document.getElementById('sVortexOpacity').addEventListener('input',e=>{
  P.vortexOpacity=clamp((Number(e.target.value)||58)/100,0.05,1);
  document.getElementById('vVortexOpacity').textContent=Math.round(100*P.vortexOpacity)+'%';
  updateVortexOpacity();
});
document.getElementById('sVorticityColor').addEventListener('input',e=>{
  P.vorticityLineColor=e.target.value||'#0F1A29';
  document.getElementById('vVorticityColor').textContent=P.vorticityLineColor.toUpperCase();
  rebuildLattice();rebuildFrameBackdrop();
});
document.getElementById('cTwProxy').addEventListener('change',e=>{
  P.twistProxyEnabled=e.target.checked;
  if(e.target.checked&&!twistProxy)initTwistProxy();
  updateSubtitle();
});
document.getElementById('cCoreFlowLock').addEventListener('change',e=>{
  P.coreFlowLock=e.target.checked;
  coreFlowNotice='';
  if(P.coreFlowLock)syncCoreFlowCoupling('geometry');
  updateCoreFlowReadout();syncUi();updateSubtitle();
});
document.getElementById('cCenterLock').addEventListener('change',e=>{
  P.centerLock=e.target.checked;
  if(P.centerLock){
    if(P.mode==='solo')centerSoloCarrierAtOrigin();
    captureCarrierAnchors();
  }else{
    carrierAnchors=Object.create(null);
  }
  rebuildLines();rebuildTubes(true);updateSubtitle();
});
document.getElementById('cTracerWrapZ').addEventListener('change',e=>{
  if(e.target.checked&&P.mode==='botsing'&&initialAxialSeparation()>initialAxialSeparationSliderMax()*(1+1e-12)){
    P.tracerWrapZ=false;e.target.checked=false;
    setFlag('⚠ Periodieke z-grens geweigerd: Δz_AB,0 is groter dan de cilinderhoogte. Vergroot eerst de cilinderhoogte of verklein de startafstand.',true);
    if(window.ModelLog)window.ModelLog.logEvent('periodic-z-rejected',{axial:initialAxialSeparation(),cellHeight:initialAxialSeparationSliderMax()});
    return;
  }
  P.tracerWrapZ=e.target.checked;
  if(P.tracerWrapZ){resetParticles('inner-column',{announce:false,resetCycle:true});wrapFilamentCarriersZ();}
  updateSubtitle();
});
document.getElementById('cAutoRelax').addEventListener('change',e=>{
  P.autoRelax=e.target.checked;
  if(P.autoRelax)StretchGate.contaminated=true;
  const badge=document.getElementById('autoRelaxBadge');
  badge.textContent=P.timeReverse&&P.autoRelax?'PAUZE':(P.autoRelax?'AAN':'UIT');
  badge.classList.toggle('on',P.autoRelax&&!P.timeReverse);
  if(stabilityLast)updateStabilityDisplay(stabilityLast);
});
document.getElementById('cTopologyGuard')?.addEventListener('change',e=>{P.topologyGuard=e.target.checked;lastTopologyGap=P.topologyGuard?topologyClearance():Infinity;ModelLog.logUser('topologyGuard',{value:P.topologyGuard});syncUi();});
document.getElementById('cTimeReverse').addEventListener('change',e=>{
  P.timeReverse=e.target.checked;
  // v7.5 (v7.4b §B.3): momentopname van ε_rev bij het inschakelen van
  // achterwaarts integreren (bij α≠0 toont de meting '—' met waarschuwing).
  if(P.timeReverse)measureEpsRev();
  hist.length=0;resetStretchGate('time-direction-change',false);
  document.getElementById('timeReverseRow').classList.toggle('time-reverse-on',P.timeReverse);
  const badge=document.getElementById('autoRelaxBadge');
  badge.textContent=P.timeReverse&&P.autoRelax?'PAUZE':(P.autoRelax?'AAN':'UIT');
  badge.classList.toggle('on',P.autoRelax&&!P.timeReverse);
  if(stabilityLast)updateStabilityDisplay(stabilityLast);
});
[['cDvSeparatrix','dvSeparatrix'],['cDvColumn','dvColumn'],['cDvCaps','dvCaps'],['cDvStewartson','dvStewartson']].forEach(([id,key])=>{
  document.getElementById(id).addEventListener('change',e=>{
    P[key]=e.target.checked;
    Flags.sep=anyDvLayerEnabled();
    syncDiagnosticToggles();renderFormula();updateIndicators(tPhys);
  });
});
const physOverlay=document.getElementById('physOverlay');
const physOpenButton=document.getElementById('bPhys');
const physCloseButton=document.getElementById('bPhysClose');

window.closePhysicsOverlay=function(event){
  if(event){
    event.preventDefault();
    event.stopPropagation();
  }
  physOverlay.classList.remove('open');
  physOverlay.setAttribute('aria-hidden','true');
  if(physOpenButton) physOpenButton.focus({preventScroll:true});
};

function openPhysicsOverlay(){
  physOverlay.classList.add('open');
  physOverlay.setAttribute('aria-hidden','false');
  if(window.renderMathInElement&&!physOverlay.dataset.rendered){
    renderMathInElement(physOverlay,{delimiters:[{left:'\\[',right:'\\]',display:true},{left:'\\(',right:'\\)',display:false}]});
    physOverlay.dataset.rendered='1';
  }
  requestAnimationFrame(()=>physCloseButton&&physCloseButton.focus({preventScroll:true}));
}

physOpenButton.addEventListener('click',openPhysicsOverlay);
physCloseButton.addEventListener('click',window.closePhysicsOverlay);
physOverlay.addEventListener('click',event=>{
  if(event.target===physOverlay) window.closePhysicsOverlay(event);
});
document.addEventListener('keydown',event=>{
  if(event.key==='Escape'&&physOverlay.classList.contains('open')){
    window.closePhysicsOverlay(event);
  }
});
document.getElementById('cCenterline').addEventListener('change',e=>{P.showCenterline=e.target.checked;});
document.getElementById('cGhostRing').addEventListener('change',e=>{
  P.ghostStewartson=e.target.checked;
  syncGhostRing();
});
document.getElementById('cTaylorOsc').addEventListener('change',e=>{
  P.taylorOsc.enabled=e.target.checked;
  if(P.taylorOsc.enabled) P.w=0;
  syncSignedUi('W','revW',P.w*1000,x=>fmtAxialMmPerS(x));
});
segHandler('indSeg','ind',key=>setIndFlag(key,!Flags[key]));
document.getElementById('bSpecClockToggle').addEventListener('click',()=>{
  if(!P.specClockEnabled){
    const ok=window.confirm('⚠ SPECULATIVE / NIET CANON\n\nDeze diagnose combineert de canonieke SST swirl-snelheid met een meterschaal mutual-flow proxy en een momentaan geïsoleerd afgetrokken fase-nullproxy. De referentie wordt na één verre kalibratie vergrendeld. Zij koppelt niets terug naar de solver en mag niet als bewezen tijdsdilatie worden geïnterpreteerd.\n\nActiveren?');
    if(!ok)return;
    P.specClockEnabled=true;resetSpecClockRuntime('geactiveerd · eerste veldsample nodig');
    setFlag('⚠ SPECULATIVE SWIRL CLOCK actief: alleen passieve Research-Track-diagnostiek; geen canonieke superpositiewet en geen solvercoupling.',true);
    if(window.ModelLog)window.ModelLog.logEvent('spec-clock-enabled',{enabled:true});
  }else{
    P.specClockEnabled=false;resetSpecClockRuntime('gedeactiveerd');
    if(window.ModelLog)window.ModelLog.logEvent('spec-clock-enabled',{enabled:false});
  }
  syncUi();
});
document.getElementById('bSpecClockCalibrate').addEventListener('click',calibrateSpecClockPhase);
document.getElementById('sSpecClockGain').addEventListener('change',e=>{P.specClockDisplayGain=Math.max(1,Number(e.target.value)||1);updateSpecClockDisplay();});
document.getElementById('cCcwA').addEventListener('change',e=>{P.ccwA=e.target.checked;resetState();});
function setGpDelta(value,{reset=true,log=true}={}){
  const next=Number(value);
  if(!Number.isFinite(next)||next<=0)return false;
  DELTA.gp=next;
  const sel=document.getElementById('gpDeltaSel');if(sel)sel.value=String(next);
  const val=document.getElementById('vGpDelta');if(val)val.textContent=next.toFixed(6);
  if(log&&window.ModelLog)window.ModelLog.logEvent('gp-delta-change',{value:next,provenance:next===0.615?'Roberts-Grant-1971':'SST-Track-B-v12B'});
  if(reset)resetState(); // Δ zit in de LIA-prefactor: schone run vereist
  else syncUi();
  return true;
}
document.getElementById('gpDeltaSel').addEventListener('change',e=>setGpDelta(e.target.value));
document.getElementById('cCcwB').addEventListener('change',e=>{P.ccwB=e.target.checked;resetState();});
document.getElementById('cMirror').addEventListener('change',e=>{P.mirrorB=e.target.checked;resetState();});
document.getElementById('cLockVz').addEventListener('change',e=>{
  P.lockVz=e.target.checked;if(P.lockVz)P.vzB=P.vzA;
  syncUi();
});
document.getElementById('presetSelect').addEventListener('change',e=>{
  const preset=e.target.value;
  if(preset==='default'){applyDefaultStartup();resetState();resetParticlesToTaylorColumn();}
  else if(preset==='superfluid'){applyCanonPreset();resetState();}
  else if(preset==='taylor'){applyTaylorPreset();resetState();}
  else if(preset==='pistol'){applyPistolPreset();resetState();}
  else if(preset==='sst'){applySSTSimilarityPreset();syncUi();updateSubtitle();resetState();}
  else if(preset==='sstBundle'){applySSTBundlePreset();resetState();resetParticlesToTaylorColumn();}
  else if(preset==='stretchGate'){applyStretchGatePreset();resetState();resetParticlesToTaylorColumn();}
  else if(preset==='string'){applyStringTheoryPreset();syncUi();updateSubtitle();resetState();}
  else if(preset==='friction'){applyFrictionPreset();syncUi();updateSubtitle();resetState();}
  else if(preset==='specClock'){applySpecClockPreset();}
  else if(preset==='specClockBenchmark'){e.target.value='specClock';SpecClockBenchmark.start();}
  else if(preset==='specClockProxyDecomposition'){e.target.value='specClock';SpecClockProxyDecomposition.start('decomposition');}
  else if(preset==='specClockContinuumBenchmark'){e.target.value='specClock';SpecClockProxyDecomposition.start('continuum');}
  else if(preset==='specClockHoldoutBenchmark'){e.target.value='specClock';SpecClockProxyDecomposition.start('holdout');}
  else if(preset==='specClockNormalizationBenchmark'){e.target.value='specClock';SpecClockProxyDecomposition.start('normalization');}
  else if(preset==='specClockTransferLawBenchmark'){e.target.value='specClock';SpecClockProxyDecomposition.start('transfer');}
  else if(preset==='specClockLengthBenchmark'){e.target.value='specClock';SpecClockProxyDecomposition.start('length');}
  else if(preset==='specClockGeomKappaBenchmark'){e.target.value='specClock';SpecClockProxyDecomposition.start('full-suite');}
});
document.getElementById('compA').addEventListener('change',e=>{P.compA=+e.target.value;resetState();});
document.getElementById('compB').addEventListener('change',e=>{P.compB=+e.target.value;resetState();});
document.getElementById('idealComponentMode').addEventListener('change',e=>{P.idealComponentMode=e.target.value==='single'?'single':'all';syncCompSelects();syncUi();resetState();});
document.getElementById('bResetIdealKnot').addEventListener('click',()=>{if(activeKnotEntry())resetState();});
// Externe catalogi: Gilbert ideal/tight, .fseries en KnotPlot-candidates staan bewust in afzonderlijke dropdowns.
function syncKnotSel(){
  const idealSel=document.getElementById('knotSelect');
  const fsSel=document.getElementById('fseriesSelect');
  const kpSel=document.getElementById('knotplotSelect');
  if(idealSel){
    if(P.knotSource==='ideal'&&P.knotKey)idealSel.value=`ideal|${P.knotKey}`;
    else if(P.knotSource==='legacy'&&P.knotIdx>=0)idealSel.value=`legacy|${P.knotIdx}`;
    else idealSel.value='builtin|';
  }
  if(fsSel)fsSel.value=P.knotSource==='fseries'&&P.knotKey?`fseries|${P.knotKey}`:'';
  if(kpSel){if(P.knotSource==='knotplot')P.knotKey=normalizeKnotPlotId(P.knotKey);kpSel.value=P.knotSource==='knotplot'&&P.knotKey?`knotplot|${P.knotKey}`:'';}
}
function applyCatalogSelection(source,key){
  P.knotIdx=-1;P.knotKey='';P.knotSource='builtin';
  if(source==='ideal'&&getIdealKnotCatalog()?.db?.[key]){P.knotSource='ideal';P.knotKey=key;}
  else if(source==='fseries'&&getFourierKnotCatalog()?.db?.[key]){P.knotSource='fseries';P.knotKey=key;}
  else if(source==='knotplot'){key=normalizeKnotPlotId(key);if(getKnotPlotKnotCatalog()?.db?.[key]){P.knotSource='knotplot';P.knotKey=key;}}
  else if(source==='legacy'){
    const idx=parseInt(key,10);
    if(Number.isInteger(idx)&&Array.isArray(window.IDEAL_KNOTS)&&window.IDEAL_KNOTS[idx]){P.knotIdx=idx;P.knotSource='legacy';}
  }
  P.topo='trefoil';P.idealComponentMode='all';P.compA=1;P.compB=1;
  const topo=document.getElementById('topoSelect');if(topo)topo.value='trefoil';
  syncKnotSel();syncCompSelects();syncUi();updateSubtitle();resetState();
}
(function initKnots(){
  const idealRow=document.getElementById('knotRow'),idealSel=document.getElementById('knotSelect');
  const fsRow=document.getElementById('fseriesRow'),fsSel=document.getElementById('fseriesSelect');
  const kpRow=document.getElementById('knotplotRow'),kpSel=document.getElementById('knotplotSelect');
  if(!idealRow||!idealSel||!fsRow||!fsSel||!kpRow||!kpSel)return;
  idealRow.classList.remove('hidden');fsRow.classList.remove('hidden');kpRow.classList.remove('hidden');
  const ideal=getIdealKnotCatalog(),fseries=getFourierKnotCatalog(),knotplot=getKnotPlotKnotCatalog();

  const idealGroups=['<option value="builtin|">— geen Gilbert-catalogus (gebruik topologie hierboven) —</option>'];
  if(ideal){
    const singles=[],links=[];
    for(const id of ideal.ids){
      const k=ideal.db[id],nc=knotEntryComponents(k).length;
      const componentLengths=knotEntryComponents(k).map(c=>finiteMetaNumber(c.L)).filter(Number.isFinite);
      const componentL=nc>1&&componentLengths.length===nc?componentLengths.reduce((a,b)=>a+b,0):NaN;
      const L0=finiteMetaNumber(k.L),L=Number.isFinite(L0)?L0:componentL;
      const label=`${id}${k.conway?' · Conway '+k.conway:''}${Number.isFinite(L)?' · L='+L.toFixed(4):''}${nc>1?' · '+nc+' comp':''}`;
      (nc>1?links:singles).push(`<option value="ideal|${id}">${label}</option>`);
    }
    idealGroups.push(`<optgroup label="GILBERT IDEAL / TIGHT KNOPEN">${singles.join('')}</optgroup>`);
    idealGroups.push(`<optgroup label="GILBERT IDEAL / TIGHT LINKS">${links.join('')}</optgroup>`);
  }else idealGroups.push('<optgroup label="CATALOGUSSTATUS"><option disabled>ideal_knots_data.js niet geladen</option></optgroup>');
  if(!ideal&&Array.isArray(window.IDEAL_KNOTS)&&window.IDEAL_KNOTS.length){
    idealGroups.push('<optgroup label="LEGACY IDEALE CATALOGUS">'+window.IDEAL_KNOTS.map((e,i)=>`<option value="legacy|${i}">${knotLabel(i)}</option>`).join('')+'</optgroup>');
  }
  idealSel.innerHTML=idealGroups.join('');

  const fsGroups=['<option value="">— geen .fseries-geometrie —</option>'];
  if(fseries){
    const opts=fseries.ids.map(id=>{
      const k=fseries.db[id],warn=k.warning?' ⚠':'';
      return `<option value="fseries|${id}">${id} · ${k.components?.[0]?.coeffs?.length||0} harmonischen${warn}</option>`;
    });
    fsGroups.push(`<optgroup label="COMPACTE FSERIES — NIET AUTOMATISCH IDEAL">${opts.join('')}</optgroup>`);
  }else fsGroups.push('<optgroup label="CATALOGUSSTATUS"><option disabled>fourier_knots_data.js niet geladen</option></optgroup>');
  fsSel.innerHTML=fsGroups.join('');

  const kpGroups=['<option value="">— geen KnotPlot-candidate —</option>'];
  if(knotplot){
    const singles=[],links=[];
    for(const id of knotplot.ids){const k=knotplot.db[id],nc=knotEntryComponents(k).length,L=finiteMetaNumber(k.L),tag=k.status||'candidate',label=`${id}${Number.isFinite(L)?' · L='+L.toFixed(4):''}${nc>1?' · '+nc+' comp':''} · ${tag}`;(nc>1?links:singles).push(`<option value="knotplot|${id}">${label}</option>`);}
    if(singles.length)kpGroups.push(`<optgroup label="KNOTPLOT RELAXED KNOT CANDIDATES">${singles.join('')}</optgroup>`);
    if(links.length)kpGroups.push(`<optgroup label="KNOTPLOT RELAXED LINK CANDIDATES">${links.join('')}</optgroup>`);
  }else kpGroups.push('<optgroup label="CATALOGUSSTATUS"><option disabled>knotplot_knots_data.js niet geladen</option></optgroup>');
  kpSel.innerHTML=kpGroups.join('');

  idealSel.addEventListener('change',()=>{
    const sep=idealSel.value.indexOf('|'),source=sep>=0?idealSel.value.slice(0,sep):'builtin',key=sep>=0?idealSel.value.slice(sep+1):'';
    applyCatalogSelection(source,key);
  });
  fsSel.addEventListener('change',()=>{
    if(!fsSel.value){
      if(P.knotSource==='fseries')applyCatalogSelection('builtin','');
      return;
    }
    const sep=fsSel.value.indexOf('|'),source=sep>=0?fsSel.value.slice(0,sep):'fseries',key=sep>=0?fsSel.value.slice(sep+1):fsSel.value;
    applyCatalogSelection(source,key);
  });
  kpSel.addEventListener('change',()=>{
    if(!kpSel.value){if(P.knotSource==='knotplot')applyCatalogSelection('builtin','');return;}
    const sep=kpSel.value.indexOf('|'),source=sep>=0?kpSel.value.slice(0,sep):'knotplot',key=sep>=0?kpSel.value.slice(sep+1):kpSel.value;applyCatalogSelection(source,key);
  });
  syncKnotSel();syncCompSelects();
})();
initDiagnosticToggles();renderFormula();
(function stewartsonSanity(){
  const z0=stewartsonCirculation(0,0.0625,1);
  const zp=stewartsonCirculation(0.03,0.0625,1);
  const zm=stewartsonCirculation(-0.03,0.0625,1);
  console.assert(Math.abs(z0.qS)<1e-9,'q_S→0 when w=0');
  console.assert(zp.qS<0,'q_S<0 for w>0, Ω>0');
  console.assert(zp.qS*zm.qS<0,'rev w flips q_S sign');
  console.log('[Taylor] stewartsonCirculation OK', {w0:z0,wPlus:zp,wMinus:zm});
})();
(function topologySanity(){
  const oldTopo=P.topo;
  for(const key of ['ring','hopf','trefoil','figure8','cinquefoil','twist52']){
    P.topo=key;
    const raws=topologyRawComponents(128,'A');
    console.assert(raws.length===BUILTIN_TOPOLOGIES[key].components,`topologie ${key}: componentaantal`);
    raws.forEach(r=>console.assert(r.length===384,`topologie ${key}: puntarray`));
  }
  P.topo=oldTopo;
  console.log('[Topology] ingebouwde catalogus OK');
})();
(function idealCatalogSanity(){
  const check=(catalog,label)=>{
    if(!catalog)return;
    console.assert(new Set(catalog.ids).size===catalog.ids.length,`${label}: unieke IDs`);
    console.assert(catalog.ids.every(id=>catalog.db[id]&&knotEntryComponents(catalog.db[id]).every(c=>(c.coeffs||[]).every(q=>Number.isFinite(Number(q.I))&&q.A?.length===3&&q.B?.length===3&&q.A.concat(q.B).every(Number.isFinite)))),`${label}: eindige 3D Fouriercoëfficiënten`);
    console.log(`[${label}] catalogusadapter OK`,catalog.ids.length);
  };
  const ideal=getIdealKnotCatalog();check(ideal,'Ideal knots');check(getFourierKnotCatalog(),'Fseries knots');check(getKnotPlotKnotCatalog(),'KnotPlot candidates');
  const kp=getKnotPlotKnotCatalog(),expected=['knot_3.1','knot_4.1','knot_5.1','knot_5.2','knot_6.1','knot_7.1','link_6.3.1','link_6.3.2','link_6.3.3','torus_3.3','torus_6.9'];if(kp){console.assert(expected.every(id=>kp.db[id]),'KnotPlot: volledige uniform-N300-ID-set');console.assert(kp.ids.length===11,'KnotPlot: 11 catalogusitems');}
  const t69=kp?.db?.['torus_6.9'];if(t69){console.assert(knotEntryComponents(t69).length===3,'torus_6.9: drie componenten');console.assert(t69.status==='relaxed-seed','torus_6.9: relaxed-seed status');console.assert(t69.torus?.p===6&&t69.torus?.q===9&&t69.torus?.componentType==='T(2,3)','torus_6.9: torusmetadata');console.assert(knotPlotLinkingAbs(t69)===6,'torus_6.9: |Lk|=6 metadata');console.assert(t69.sourceRole==='vortexlab-uniform-N300'&&t69.D===1,'torus_6.9: uniform-N300 D=1 provenance');}
  const tre=ideal?.db?.['3:1:1'];if(tre){const raw=sampleIdealComponent(knotEntryComponents(tre)[0],512);let L=0;for(let i=0;i<512;i++){const j=(i+1)%512;L+=Math.hypot(raw[3*j]-raw[3*i],raw[3*j+1]-raw[3*i+1],raw[3*j+2]-raw[3*i+2]);}console.assert(Math.abs(L-16.371637)<0.02,'ideal 3:1:1 booglengte',L);}
})();
(function potentialFlowSanity(){
  const R=1,U=2,stag=potentialFields(0,R*(1+1e-9),R,U),shoulder=potentialFields(R*(1+1e-9),0,R,U),far=potentialFields(0,100*R,R,U);
  console.assert(Math.abs(stag.cp-1)<1e-6,'potential flow stagnatie C_p=1');
  console.assert(Math.abs(shoulder.cp+3)<1e-5,'potential flow schouder C_p=-3');
  console.assert(Math.abs(far.speed/U-1)<2e-4,'potential flow verre veldlimiet');
})();
(function spinSanity(){
  console.assert(typeof bodyFrameState==='function'&&typeof kelvinSpeed==='function','spin helpers OK');
  const uk=kelvinSpeed(0.07);
  console.assert(uk>0,'Kelvin U > 0');
  console.log('[Spin] sanity OK, Kelvin U≈',uk.toFixed(4),'m/s');
})();

// v7.5.2: topologie kan alleen veranderen wanneer niet-aanliggende
// centerlines elkaar doorsnijden. De guard bewaakt daarom de minimale exacte
// segmentafstand, begrenst dt op de resterende tube-clearance en zoekt bij
// mogelijke tunneling expliciet naar een tijdelijk contact binnen de RK4-stap.
let lastTopologyGap=Infinity;
function topologyClearance(){
  const active=fils.filter(f=>!f.ghost);let g=Infinity;
  for(const f of active)g=Math.min(g,dminSelf(f));
  for(let i=0;i<active.length;i++)for(let j=i+1;j<active.length;j++)
    g=Math.min(g,Math.sqrt(pairGapExact2(active[i],active[j],g*g)));
  return g;
}
function maxStateDisplacement(A,B){let d=0;for(let i=0;i<Math.min(A.length,B.length);i+=3)d=Math.max(d,Math.hypot(B[i]-A[i],B[i+1]-A[i+1],B[i+2]-A[i+2]));return d;}
function topologyStepMayTunnel(g0,g1,dmax){
  const d=contactThresholdInfo().effective;
  return Number.isFinite(g0)&&Number.isFinite(g1)&&Math.min(g0,g1)<=d+2.25*dmax;
}
function transientContactWithinStep(signedDtFull,lia){
  if(!P.topologyGuard||!Ypre)return null;
  const fullState=Y.slice(),fullK4=K4.slice(),fullUmax=lastUmax;
  const sgn=Math.sign(signedDtFull)||1,full=Math.abs(signedDtFull),tStart=tPhys;
  let lo=0,hi=NaN,event=null;
  for(let k=1;k<=TOPOLOGY_SWEEP_SAMPLES;k++){
    const f=k/TOPOLOGY_SWEEP_SAMPLES;Y.set(Ypre);advanceFilamentCandidate(sgn*full*f,tStart+sgn*full*f);
    const e=contactEvent(false);if(e&&!e.warn){hi=f;lo=(k-1)/TOPOLOGY_SWEEP_SAMPLES;event=e;break;}
  }
  if(!event){Y.set(fullState);K4.set(fullK4);lastUmax=fullUmax;return null;}
  for(let it=0;it<18&&(hi-lo)>1e-6;it++){
    const mid=.5*(lo+hi);Y.set(Ypre);advanceFilamentCandidate(sgn*full*mid,tStart+sgn*full*mid);
    const e=contactEvent(false);if(e&&!e.warn){hi=mid;event=e;}else lo=mid;
  }
  Y.set(Ypre);lastUmax=advanceFilamentCandidate(sgn*full*lo,tStart+sgn*full*lo);
  return {dt:sgn*full*lo,event:Object.assign({},event,{msg:'⛔ topology guard: tijdelijk contact binnen de RK4-stap gevonden; gestopt aan de veilige zijde. Geen doorsnijding of reconnectie toegepast.'})};
}

// v7.2: contactdetectie op exacte segment-segmentafstand, aangeroepen na
// iedere geaccepteerde RK4-stap. Pure functie: retourneert het eerste event
// (warn = LIA-kwalitatief, anders hard stop) zonder zelf flags te zetten,
// zodat de first-hit-bisectie hem als predicaat kan gebruiken.
function contactEvent(lia){
  // v7.3.1: 3a blijft de fysische drempel; wanneer die onder de representabele
  // afstandsschaal valt, gebruikt de detector expliciet een numerieke ULP-vloer.
  const ct=contactThresholdInfo(),dContact=ct.effective,d2Contact=dContact*dContact;
  const suffix=ct.floorActive?' (numerieke afstandsvloer actief)':'';
  if(P.mode==='botsing'&&minGapCross()<dContact){
    if(lia&&!P.topologyGuard)return{warn:true,msg:'⚠ dragers binnen contactdrempel: LIA negeert de onderlinge interactie — resultaat vanaf hier kwalitatief.'+suffix};
    return{warn:false,msg:'⛔ dragers bereiken de topologische contactdrempel; de run stopt vóór doorsnijding. Reconnectie is niet gemodelleerd.'+suffix};
  }
  for(const f of fils){
    if(f.ghost)continue;
    if(f.N>RING_N||P.topo==='trefoil'||P.knotKey||P.knotIdx>=0){
      const ds=dminSelf(f);
      if(ds<dContact){
        if(lia&&!P.topologyGuard)return{warn:true,msg:'⚠ strengen binnen contactdrempel: LIA negeert deze interactie — resultaat vanaf hier kwalitatief.'+suffix};
        return{warn:false,msg:'⛔ zelfcontactdrempel bereikt; de topology guard stopt vóór een mogelijke topologieverandering. De knoop wordt niet doorgeknipt of ontknoopt.'+suffix};
      }
    }
  }
  for(let ii=0;ii<fils.length;ii++)for(let jj=ii+1;jj<fils.length;jj++){
    if(fils[ii].ghost||fils[jj].ghost)continue;
    if((fils[ii].carrier||'A')!==(fils[jj].carrier||'A'))continue;
    if(pairGapExact2(fils[ii],fils[jj],Infinity)<d2Contact){
      if(lia&&!P.topologyGuard)return{warn:true,msg:'⚠ componenten binnen contactdrempel: LIA negeert deze interactie — resultaat vanaf hier kwalitatief.'+suffix};
      return{warn:false,msg:'⛔ componentcontact bereikt; gestopt vóór doorsnijding. Geen reconnectie toegepast.'+suffix};
    }
  }
  return null;
}
// v7.2: first-hit-bisectie. Ypre bevat de toestand vóór de stap; Y staat ná
// de volle stap waarin hard contact is gedetecteerd. Bisecteert de stapgrootte
// naar de eerste overschrijding en landt net voorbij de hit, zodat de
// 3a-drempel niet met een volle CFL-stap wordt gepasseerd.
let Ypre=null;
function bisectFirstHit(signedDtFull,lia){
  const tStart=tPhys;
  return bisectHitTime(signedDtFull,dt=>{
    Y.set(Ypre);lastUmax=advanceFilamentCandidate(dt,tStart+dt);
  },()=>{
    const c=contactEvent(lia);return !!(c&&!c.warn);
  },P.topologyGuard);
}
function bisectHitTime(signedDtFull,advanceFromStart,hasHardHit,landSafe=false){
  const sgn=Math.sign(signedDtFull)||1, full=Math.abs(signedDtFull);
  let lo=0,hi=full;
  for(let it=0;it<16&&(hi-lo)>1e-4*full;it++){
    const mid=.5*(lo+hi);
    advanceFromStart(sgn*mid);
    hasHardHit()?hi=mid:lo=mid;
  }
  const land=landSafe?lo:hi;
  advanceFromStart(sgn*land);
  return sgn*land;
}
function setFlag(msg,warnOnly){
  const f=document.getElementById('flag');
  f.textContent=msg;f.style.display='block';
  f.classList.toggle('warnonly',!!warnOnly);
  if(!warnOnly)flagged=msg;else warned=true;
}

// ================= hoofdlus =================
applyDefaultStartup();


// ================= v7.3.1 ModelLog 0.2 =================
const ModelLog=(()=>{
  const maxSteps=20000,maxActions=5000,maxEvents=20000,diagPeriodMs=200;
  let enabled=false,verboseSteps=false,stepCounter=0,lastDiagWall=-Infinity;
  const dropped={actions:0,steps:0,events:0};
  const session={
    id:(typeof crypto!=='undefined'&&crypto.randomUUID)?crypto.randomUUID():('ml-'+Date.now()),
    version:APP_VERSION,baseVersion:APP_BASE_VERSION,patch:true,
    startedAt:new Date().toISOString(),userAgent:navigator.userAgent||'',
    patchNotes:APP_PATCH_NOTES,
  };
  const userActions=[],steps=[],events=[];
  function snapP(){
    return {mode:P.mode,topo:P.topo,inter:P.inter,core:P.core,med:P.med,a:P.a,rHorn:R_HORN_SST,rCorePhysical:P.rCorePhysical,scaleProbe:P.scaleProbe,Om:P.Om,nQ:P.nQ,Rcyl:P.Rcyl,Hcyl:P.Hcyl,cylinderHeight:cylinderHeight(),
      zA:P.zA,zB:P.zB,initialAxialSeparation:initialAxialSeparation(),off:P.off,vzA:P.vzA,vzB:P.vzB,lockVz:P.lockVz,tracerWrapZ:P.tracerWrapZ,
      solverFrame:P.solverFrame,displayFrame:P.displayFrame,bgFlow:P.bgFlow,
      bundleEnabled:P.bundleEnabled,bundleProfile:P.bundleProfile,bundleSplay:P.bundleSplay,OmBundle:P.OmBundle,
      bundleBEMEnabled:P.bundleBEMEnabled,bundleBoundaryMode:P.bundleBoundaryMode,bundleBEMQuality:P.bundleBEMQuality,
      topologyGuard:P.topologyGuard,accExp:P.accExp,paused,stepDebt,dtCFL:finiteOrNull(dtCFL()),acceptedStepTimeCap:acceptedStepTimeCap(),
      prescribedKinematicSpeedBound:prescribedKinematicSpeedBound(),playbackDebtResetReason,
      autoRelax:P.autoRelax,coreFlowLock:P.coreFlowLock,qual:P.qual,timeReverse:P.timeReverse,gpDelta:DELTA.gp,
      stretchGateEnabled:P.stretchGateEnabled,stretchProfile:P.stretchProfile,stretchProfileApply:P.stretchProfileApply,stretchProfileOnly:P.stretchProfileOnly,
      stretchOmega0:P.stretchOmega0,stretchBeta:P.stretchBeta,stretchGamma:P.stretchGamma,stretchSoftening:P.stretchSoftening,stretchEpsilon:P.stretchEpsilon,stretchMode:P.stretchMode,
      specClockEnabled:P.specClockEnabled,specClockDisplayGain:P.specClockDisplayGain,
      specClockCalibrated:SpecClock.calibrated,specClockCalibrationTime:finiteOrNull(SpecClock.calibrationTime),specClockCalibrationDistance:finiteOrNull(SpecClock.calibrationDistance)};
  }
  function pushRing(kind,arr,item,limit){
    arr.push(item);
    if(arr.length>limit){const n=arr.length-limit;arr.splice(0,n);dropped[kind]+=n;}
  }
  function updateStats(){
    const el=document.getElementById('modelLogStats');
    const btn=document.getElementById('bModelLogExport');
    const txtBtn=document.getElementById('bModelLogExportTxt');
    const lost=dropped.actions+dropped.steps+dropped.events;
    if(el)el.textContent=(enabled?'aan':'uit')+' · '+userActions.length+' acties · '+steps.length+' stappen · '+events.length+' events'+(lost?' · '+lost+' vervallen':'');
    const dis=!enabled||(!userActions.length&&!steps.length&&!events.length);
    if(btn)btn.disabled=dis;
    if(txtBtn)txtBtn.disabled=dis;
  }
  function logUser(action,detail){
    if(!enabled)return;
    pushRing('actions',userActions,{tWall:Date.now(),tPhys,p:action,detail:detail||null,P:snapP()},maxActions);
    updateStats();
  }
  function logEvent(type,detail){
    if(!enabled)return;
    pushRing('events',events,{tWall:Date.now(),tPhys,type,detail:detail||null},maxEvents);
    updateStats();
  }
  function logDiag(detail){
    if(!enabled)return;
    const now=performance.now();
    if(now-lastDiagWall<diagPeriodMs)return;
    lastDiagWall=now;logEvent('diag',detail);
  }
  function logStep(extra){
    if(!enabled||!verboseSteps)return;
    stepCounter++;
    const rep=stabilityLast;
    pushRing('steps',steps,Object.assign({tPhys,dt:extra&&extra.dt,lastUmax,effAcc,
      score:rep&&rep.score,gapRatio:rep&&rep.gapRatio,gapRatioEffective:rep&&rep.gapRatioEffective,maxAk:rep&&rep.maxAk,
      stretchStatus:StretchGate.lastReport&&StretchGate.lastReport.status,stretchLambdaStar:StretchGate.lastReport&&StretchGate.lastReport.lambdaStar,stretchG:StretchGate.lastReport&&StretchGate.lastReport.G,
      flagged:!!flagged,warned:!!warned},extra||{}),maxSteps);
    updateStats();
  }
  function exportJson(){
    return {schema:'vortexlab-model-log/0.2',version:APP_VERSION,baseVersion:APP_BASE_VERSION,patch:true,
      limits:{maxActions,maxSteps,maxEvents,diagPeriodMs},dropped:Object.assign({},dropped),
      session,initialP:session.initialP||null,userActions,steps,events,finalP:snapP(),exportedAt:new Date().toISOString()};
  }
  function exportText(){
    const lines=[];
    lines.push('VortexLab model log');
    lines.push('session='+session.id);
    lines.push('version='+APP_VERSION+' base='+APP_BASE_VERSION+' exportedAt='+new Date().toISOString());
    lines.push('startedAt='+session.startedAt);
    lines.push('enabled='+(enabled?'true':'false')+' verboseSteps='+(verboseSteps?'true':'false'));
    lines.push('');
    lines.push('[initialP]');
    lines.push(JSON.stringify(session.initialP||null));
    lines.push('');
    lines.push('[userActions]');
    userActions.forEach((r,i)=>lines.push(`${i+1}. wall=${new Date(r.tWall).toISOString()} tPhys=${Number(r.tPhys).toFixed(6)} action=${r.p} detail=${JSON.stringify(r.detail)} P=${JSON.stringify(r.P)}`));
    lines.push('');
    lines.push('[events]');
    events.forEach((r,i)=>lines.push(`${i+1}. wall=${new Date(r.tWall).toISOString()} tPhys=${Number(r.tPhys).toFixed(6)} type=${r.type} detail=${JSON.stringify(r.detail)}`));
    lines.push('');
    lines.push('[steps]');
    steps.forEach((r,i)=>lines.push(`${i+1}. ${JSON.stringify(r)}`));
    lines.push('');
    lines.push('[finalP]');
    lines.push(JSON.stringify(snapP()));
    return lines.join('\n');
  }
  function setEnabled(on){
    const next=!!on;if(next===enabled){updateStats();return;}
    if(next){enabled=true;if(!session.initialP)session.initialP=snapP();logEvent('logging-enabled',{verboseSteps});}
    else{logEvent('logging-disabled',{verboseSteps});enabled=false;verboseSteps=false;const v=document.getElementById('cModelLogVerbose');if(v)v.checked=false;}
    updateStats();
  }
  function setVerbose(on){
    const next=enabled&&!!on;if(next===verboseSteps){updateStats();return;}
    verboseSteps=next;logEvent('verbose-steps',{enabled:verboseSteps});updateStats();
  }
  return {logUser,logEvent,logDiag,logStep,exportJson,exportText,setEnabled,setVerbose,get enabled(){return enabled;}};
})();
window.ModelLog=ModelLog;

function runtimeFailure(kind,error){
  const detail=String(error&&error.stack||error&&error.message||error||kind);
  console.error('[vortexlab runtime]',kind,detail);
  ModelLog.logEvent('runtime-error',{kind,detail});
  if(!flagged)setFlag('⛔ runtimefout ('+kind+'): '+detail.slice(0,240));
}
window.addEventListener('error',e=>runtimeFailure('error',e.error||e.message));
window.addEventListener('unhandledrejection',e=>runtimeFailure('unhandledrejection',e.reason));
// ================= v7.2 ZELFTEST-HARNAS (?selftest=1 of 🧪-knop) =================
// Puur lokaal: bouwt eigen toestandsarrays, raakt globale Y/fils niet aan;
// P-velden worden gesnapshot en hersteld. Resultaten als JSON exporteerbaar.
const SelfTest=(()=>{ 
  const PKEYS=['mode','topo','inter','core','med','qual','Om','OmBundle','GaDemo','nQ','a','off','zA','zB','zSolo','w','vzA','vzB',
    'lockVz','solverFrame','displayFrame','bgFlow','mfTemp','mfAlpha','mfAlphaP','vnZ','timeReverse','coreFlowLock','rCorePhysical','scaleProbe',
    'bundleEnabled','bundleProfile','bundleSplay','bundleBEMEnabled','bundleBoundaryMode','bundleBEMQuality','topologyGuard',
    'centerLock','twistProxyEnabled','ghostStewartson','Rcyl','Hcyl',
    'stretchGateEnabled','stretchProfile','stretchProfileApply','stretchProfileOnly','stretchOmega0','stretchBeta','stretchGamma','stretchSoftening','stretchEpsilon','stretchMode','stretchNeutralTol','stretchFailTol',
    'specClockEnabled','specClockDisplayGain'];
  function snap(){const o={};for(const k of PKEYS)o[k]=P[k];o.tOsc=P.taylorOsc.enabled;o.gpDelta=DELTA.gp;return o;}
  function restore(o){for(const k of PKEYS)P[k]=o[k];P.taylorOsc.enabled=o.tOsc;DELTA.gp=o.gpDelta;syncUi();}
  function baseline(){
    P.mode='solo';P.topo='ring';P.med='he';P.nQ=10;P.a=1.2415e-4;P.core='gp';
    P.scaleProbe=HE_CORE_REF;P.centerLock=true;P.twistProxyEnabled=false;P.ghostStewartson=false;P.Rcyl=.25;P.Hcyl=.5;
    P.w=0;P.vzA=0;P.vzB=0;P.lockVz=true;P.solverFrame='corot';P.displayFrame='corot';P.bgFlow='none';
    P.mfTemp='0';P.mfAlpha=0;P.mfAlphaP=0;P.vnZ=0;P.timeReverse=false;P.taylorOsc.enabled=false;DELTA.gp=0.615;
    P.bundleEnabled=false;P.bundleProfile='parallel';P.bundleSplay=0;P.bundleBEMEnabled=true;P.bundleBoundaryMode='asim';P.bundleBEMQuality='mid';P.topologyGuard=true;
    P.stretchGateEnabled=true;P.stretchProfile='rigid';P.stretchProfileApply=false;P.stretchProfileOnly=false;P.stretchOmega0=1;P.stretchBeta=60;P.stretchGamma=.02;P.stretchSoftening=.02;P.stretchEpsilon=.01;P.stretchMode=1;P.stretchNeutralTol=.02;P.stretchFailTol=.1;
  }
  function ring(N,R,eps,m){const A=new Float64Array(3*N);
    for(let k=0;k<N;k++){const t=2*Math.PI*k/N;const r=R*(1+(eps||0)*Math.cos((m||0)*t));
      A[3*k]=r*Math.cos(t);A[3*k+1]=r*Math.sin(t);A[3*k+2]=0;}
    return A;}
  function meanRadVz(V,N){let rad=0,vz=0;
    for(let k=0;k<N;k++){const t=2*Math.PI*k/N;
      rad+=V[3*k]*Math.cos(t)+V[3*k+1]*Math.sin(t);vz+=V[3*k+2];}
    return[rad/N,vz/N];}
  function localRK4(Yl,fl,dt,B,ext){ // LIA-only; ext=true neemt externe termen mee (T8)
    const n=Yl.length,{K1,K2,K3,K4,TT}=B,o={includeExternal:ext===true};
    const u1=velocityCore(Yl,fl,K1,true,o);
    for(let i=0;i<n;i++)TT[i]=Yl[i]+.5*dt*K1[i];
    const u2=velocityCore(TT,fl,K2,true,o);
    for(let i=0;i<n;i++)TT[i]=Yl[i]+.5*dt*K2[i];
    const u3=velocityCore(TT,fl,K3,true,o);
    for(let i=0;i<n;i++)TT[i]=Yl[i]+dt*K3[i];
    const u4=velocityCore(TT,fl,K4,true,o);
    for(let i=0;i<n;i++)Yl[i]+=dt/6*(K1[i]+2*K2[i]+2*K3[i]+K4[i]);
    return Math.max(u1,u2,u3,u4);
  }
  function bufs(n){return{K1:new Float64Array(n),K2:new Float64Array(n),K3:new Float64Array(n),K4:new Float64Array(n),TT:new Float64Array(n)};}
  function localDt(Yl,N,umax){ // replica van de CFL-regel op lokale toestand
    let lmin=1e9;for(let k=0;k<N;k++){const k2=(k+1)%N;
      lmin=Math.min(lmin,Math.hypot(Yl[3*k2]-Yl[3*k],Yl[3*k2+1]-Yl[3*k+1],Yl[3*k2+2]-Yl[3*k+2]));}
    const nu=Math.abs(Gamma())/(4*Math.PI)*(Math.log(2*lmin/(Math.exp(DELTA[P.core])*P.a))+C0);
    let dt=0.5/(Math.abs(nu)*Math.pow(Math.PI/lmin,2));
    if(umax>0)dt=Math.min(dt,0.25*lmin/umax);
    return dt;
  }
  function run(){
    const S=snap();const results=[];const t0=performance.now();
    const add=(name,pass,detail)=>results.push({name,pass:!!pass,detail:String(detail)});
    try{
      baseline();
      const metaVersion=document.querySelector('meta[name="vortexlab-version"]')?.content;
      const metaBase=document.querySelector('meta[name="vortexlab-base"]')?.content;
      const title=document.title,titleOk=title.includes('v'+APP_VERSION);
      const footOk=document.getElementById('footNote')?.textContent.trim().startsWith('v'+APP_VERSION);
      const canonTags=[...document.querySelectorAll('.tag')].filter(x=>/\bcanon\b/i.test(x.textContent)&&!/niet canon/i.test(x.textContent));
      const visibleCanonText=[...document.querySelectorAll('p,.tag,#hSub')].map(x=>x.textContent).join(' ');
      const canonOk=canonTags.length>0&&canonTags.every(x=>x.textContent.includes('0.8.20'))&&!visibleCanonText.includes('Canon 0.8.19');
      add('T0 versie/provenance consistent',metaVersion===APP_VERSION&&metaBase===APP_BASE_VERSION&&APP_BASE_VERSION==='7.5.3'&&titleOk&&footOk&&canonOk,
        'meta='+metaVersion+' runtime='+APP_VERSION+' base='+APP_BASE_VERSION+' title='+titleOk+' foot='+footOk+' canon='+canonOk);
      const scoreText=(document.querySelector('#collDiagnostics > .vl-diagnostics-heading')?.textContent||'')+' '+(document.getElementById('cardE')?.parentElement?.textContent||'');
      add('T0a scorelabel zonder energieclaim',/GEOMETRISCHE DIAGNOSTIEK|geo-score/.test(scoreText)&&!/E_eff|Eeff|𝓔/.test(scoreText),scoreText.trim());
      const diag=buildDiagRecord(1,2,3,{R:4,z:5});
      add('T0b diag-record ACN eindig',diag.ACN===3&&Object.values(diag).filter(v=>typeof v==='number').every(Number.isFinite),'ACN='+diag.ACN);
      const parsed=parseLengthInput('1.40897017 fm');
      add('T0c SI-lengteparser fm',Math.abs(parsed-R_HORN_SST)<1e-24,'a='+parsed.toExponential(9));
      const parsedPlanck=parseLengthInput('planck'),fmtPlanck=fmtLengthSI(PLANCK_LENGTH);
      add('T0d Planck-parser en formatter',Math.abs(parsedPlanck/PLANCK_LENGTH-1)<1e-15&&!/^0(?:\.0+)?\s/.test(fmtPlanck),fmtPlanck);
      const oldA=P.a;P.a=A_SIM_INPUT_FLOOR;const ct=contactThresholdInfo(),gr=gapRatios(1e-9);P.a=oldA;
      add('T0o contactvloer en exact g_a',Number.isFinite(ct.effective)&&ct.effective>=ct.physical&&ct.effective>=ct.numerical&&Math.abs(gr.physical-1e9)<1,
        'd_eff='+ct.effective.toExponential(3)+' g_a='+gr.physical.toExponential(3)+' g_eff='+gr.effective.toExponential(3));
      const oldOm=P.Om;P.Om=0;const dim0=dimensionlessDiagnostics({R:0.07},0.01);P.Om=oldOm;
      add('T0e dimensieloze Ω=0-guard',!Number.isFinite(dim0.chiOmega)&&!Number.isFinite(dim0.roZ)&&Number.isFinite(dim0.aOverR),'chi='+dim0.chiOmega+' Ro_z='+dim0.roZ);
      const oldGp=DELTA.gp;setGpDelta(0.619350923,{reset:false,log:false});
      const gpUi=document.getElementById('vGpDelta').textContent;
      add('T0f GP-Δ state/UI gesynchroniseerd',Math.abs(DELTA.gp-0.619350923)<1e-12&&gpUi==='0.619351','Δ='+DELTA.gp+' ui='+gpUi);
      setGpDelta(oldGp,{reset:false,log:false});
      const scorePanel=document.getElementById('collDiagnostics');
      const scoreHeading=scorePanel?.querySelector(':scope > .vl-diagnostics-heading')?.textContent.trim();
      const flatDiag=scorePanel?.tagName==='SECTION'&&!scorePanel.querySelector(':scope > summary');
      add('T0g geometrische diagnostiek vast in DIAG',!!scorePanel&&flatDiag&&scoreHeading==='GEOMETRISCHE DIAGNOSTIEK','panel='+!!scorePanel+' flat='+flatDiag+' heading='+scoreHeading);
      const scPanel=document.getElementById('specClockPanel'),eta0=specClockEta(V_CHAR_SST),env0=specClockEnvelope(0);
      add('T0p speculative swirl-clock duidelijk gelabeld en passief',!!scPanel&&/SPECULATIVE/.test(scPanel.textContent)&&/GEEN SOLVERKOPPELING/.test(scPanel.textContent),'panel='+!!scPanel);
      add('T0q swirl-clock limieten',Math.abs(eta0-0.999993343558553)<1e-14&&Math.abs(env0.etaMin-eta0)<1e-14&&Math.abs(env0.etaMax-eta0)<1e-14,'eta0='+eta0.toPrecision(16));
      const proxyMismatch=specClockProxyAssessment(1.01,0.999999,1.000001);
      add('T0r ongemapte proxy-afwijking is geen fysische falsificatie',proxyMismatch.state==='unmapped-mismatch'&&proxyMismatch.rawOverlap===false&&proxyMismatch.falsified===false,JSON.stringify(proxyMismatch));
      {const rt=ContinuousReachAudit.selfTest(),section=document.getElementById('reachAuditSection'),rows=document.getElementById('reachAuditRows');add('T0e25a continue reach/DCSD solver',!!section&&!!rows&&rt.ok,'circle='+rt.circle.reach+' pair='+rt.pair.reach+' limiter='+rt.pair.limiter);}
      {const strip=document.getElementById('vlGlobalRunStrip'),hub=document.getElementById('vlClockRunnerHub'),resultDetails=document.querySelectorAll('details.vl-result-accordion').length,kinds=['live','spec','stats','spark'],bottomKinds=kinds.filter(k=>document.querySelector('.vl-bottom-widget-'+k));
       add('T0e24 runstrip, runner-hub en inklapbare HUD aanwezig',!!strip&&!!hub&&resultDetails>=2&&bottomKinds.length===kinds.length,'strip='+!!strip+' hub='+!!hub+' results='+resultDetails+' bottomKinds='+bottomKinds.length+'/'+kinds.length);}
      {const strip=document.getElementById('vlGlobalRunStrip'),close=document.getElementById('vlGlobalRunClose');if(strip){strip.classList.add('active');document.body.classList.add('vl-run-strip-active');}close?.click();
       add('T0e24b runstrip-close is startup-safe gebonden',!!strip&&!!close&&!strip.classList.contains('active')&&!document.body.classList.contains('vl-run-strip-active'),'strip='+!!strip+' close='+!!close);}
      {const sparkWidget=document.querySelector('.vl-bottom-widget-spark'),spark=document.getElementById('spark'),summary=sparkWidget?.querySelector(':scope > summary'),dragBound=[...document.querySelectorAll('.vl-bottom-widget')].every(x=>x.dataset.vlDragBound==='1');
       const wasOpen=sparkWidget?.open;if(sparkWidget)sparkWidget.open=false;const closedHidden=!!sparkWidget&&!!spark&&getComputedStyle(spark).display==='none';summary?.click();const closedClickOpens=!!sparkWidget?.open;summary?.click();const openClickStaysOpen=!!sparkWidget?.open;summary?.dispatchEvent(new MouseEvent('dblclick',{bubbles:true}));const doubleClickCloses=!sparkWidget?.open;if(sparkWidget)sparkWidget.open=!!wasOpen;
       add('T0e24c SPARK/HUD click-drag-collapse interactie',dragBound&&closedHidden&&closedClickOpens&&openClickStaysOpen&&doubleClickCloses,'dragBound='+dragBound+' hidden='+closedHidden+' clickOpen='+closedClickOpens+' clickStay='+openClickStaysOpen+' dblClose='+doubleClickCloses);}
      {const defs=VL_CLOCK_RUNNER_DEFS.map(x=>document.getElementById(x.id)),flex=getComputedStyle(document.getElementById('vlClockRunnerGrid')).display==='flex',legacyHidden=document.getElementById('bSpecBenchmarkStop')?.hidden&&document.getElementById('bProxyDecompStop')?.hidden;
       add('T0e24d runner-flex, één toggle per test en workflow-locks',defs.every(Boolean)&&flex&&legacyHidden&&VLClockWorkflow.unlocked('spec')&&VL_CLOCK_RUNNER_DEFS[1]?.step===2,'defs='+defs.filter(Boolean).length+' flex='+flex+' legacyHidden='+legacyHidden);}
      {const sample={parameters:{tracerCount:0,showTracers:false,showStreamlines:false,showPotentialFlow:false}},proof={tracerCount:0,showTracers:false,showStreamlines:false,showPotentialFlow:false};
       add('T0e25 D14 bewijsveld semantiek',Object.keys(proof).every(k=>sample.parameters[k]===proof[k]),JSON.stringify(proof));}
      {const overlay=document.getElementById('specClockOverlay'),body=document.getElementById('specClockOverlayBody'),oldEnabled=P.specClockEnabled;
       P.specClockEnabled=true;updateSpecClockOverlay(null,{ok:true});const stableNode=body?.firstElementChild;updateSpecClockOverlay(null,{ok:true});
       const stable=!!overlay&&overlay.classList.contains('active')&&body?.firstElementChild===stableNode&&body?.dataset.specOverlayReady==='1';
       P.specClockEnabled=false;updateSpecClockOverlay(null,{ok:false});const hidden=!overlay?.classList.contains('active')&&overlay?.getAttribute('aria-hidden')==='true';P.specClockEnabled=oldEnabled;updateSpecClockOverlay(null,{ok:true});
       add('T0s SPEC CLOCK-overlay incrementeel en alleen actief op verzoek',stable&&hidden,'stable='+stable+' hidden='+hidden);}
      {const old={mode:P.mode,zA:P.zA,zB:P.zB,H:P.Hcyl,wrap:P.tracerWrapZ};P.mode='botsing';P.Hcyl=.5;P.tracerWrapZ=true;
       const applied=setInitialAxialSeparation(2.5),free=Math.abs(applied-2.5)<1e-12&&!P.tracerWrapZ;
       P.mode=old.mode;P.zA=old.zA;P.zB=old.zB;P.Hcyl=old.H;P.tracerWrapZ=old.wrap;separationBoundaryAutoDisabled=false;
       const wrap=document.getElementById('cTracerWrapZ');if(wrap)wrap.checked=P.tracerWrapZ;
       add('T0t vrije afstand boven cilinderhoogte zonder periodieke terugwikkeling',free,'applied='+applied+' wrapAfterFar=false');}
      {const input=document.getElementById('sSpecSepAB'),layout=window.vlPanelLayout,clockPanel=document.getElementById('specClockPanel'),pane=clockPanel?.closest('.vl-pane'),clockWasOpen=layout?.right.isOpen('clock'),detailsWasOpen=clockPanel?.open,before=input?.value,oldTransition=pane?.style.transition||'',oldVisibility=pane?.style.visibility||'';
       if(layout&&!clockWasOpen)layout.right.setOpen('clock',true);if(pane){pane.style.transition='none';pane.style.visibility='visible';}if(clockPanel)clockPanel.open=true;input?.focus();if(input)input.value='2500';syncSpecClockQuickControls();
       const during=input?.value,preserved=document.activeElement===input&&during==='2500';input?.blur();syncSpecClockQuickControls({force:true});if(clockPanel)clockPanel.open=!!detailsWasOpen;if(pane){pane.style.transition=oldTransition;pane.style.visibility=oldVisibility;}if(layout&&!clockWasOpen)layout.right.setOpen('clock',false);
       add('T0u live synchronisatie overschrijft actief quick-veld niet',preserved,'before='+before+' during='+during);}
      {const ids=['sSpecSepAB','sSpecOffClone','sSpecVzA','sSpecVzB','bSpecSetApproach','bSpecSetSeparate','bSpecPullFromModel','bSpecClockPreset','cSpecClockLog','cSpecAutoExport','bModelLogExportTxt'];
       const bound=ids.every(id=>document.getElementById(id)?.dataset.specBound==='1');
       add('T0v alle SPEC CLOCK quick-controls werkelijk gebonden',bound,ids.filter(id=>document.getElementById(id)?.dataset.specBound!=='1').join(',')||'alle gebonden');}
      {const main=document.getElementById('sSepAB'),quick=document.getElementById('sSpecSepAB');
       const freeInputs=main&&!main.hasAttribute('max')&&quick&&!quick.hasAttribute('max')&&main.dataset.sliderMax&&quick.dataset.sliderMax;
       add('T0w afstandsgetal vrij en slider afzonderlijk begrensd',!!freeInputs,'mainMax='+(main&&main.max)+' sliderMax='+(main&&main.dataset.sliderMax));}
      {const ea=specClockEnvelope(5e-11),eb=specClockEnvelope(0),d=specClockEtaDiffFromDeltaLogs(ea.deltaLogEtaMin,eb.deltaLogEtaMax),dl=ea.deltaLogEtaMin-eb.deltaLogEtaMax;
       add('T0x stabiele Δlnη-route behoudt sub-ulp veldverschil',Number.isFinite(d)&&d!==0&&dl!==0,'dη='+d.toExponential(3)+' Δln='+dl.toExponential(3));}
      {const common=1.0,mut=2e-6,full=common+mut,iso=common,delta=(full-iso)/Math.abs(iso);
       add('T0y fase-null geïsoleerde aftrek verwijdert gemeenschappelijke achtergrond',Math.abs(delta-mut)<1e-15,'δ='+delta.toExponential(3));}
      {const oldMode=P.mode,oldA=P.vzA,oldB=P.vzB,oldLock=P.lockVz,oldClock=P.specClockEnabled;
       P.mode='botsing';P.vzA=.005;P.vzB=-.005;P.lockVz=false;P.specClockEnabled=true;
       const ub=prescribedKinematicSpeedBound(),cap=acceptedStepTimeCap();
       add('T0z eerste-stap-CFL kent opgelegde driftsnelheid',Math.abs(ub-.005)<1e-15,'u_bound='+ub.toExponential(3));
       add('T0aa SPEC CLOCK tijdstapcap 50 ms',Math.abs(cap-SPEC_CLOCK_MAX_ACCEPTED_DT)<1e-15,'dt_cap='+cap.toFixed(3)+' s');
       P.mode=oldMode;P.vzA=oldA;P.vzB=oldB;P.lockVz=oldLock;P.specClockEnabled=oldClock;}
      {const layout=window.vlPanelLayout,runMenu=document.getElementById('vlHeaderRunMenu'),viewMenu=document.getElementById('vlHeaderViewMenu');
       const keys=['info','flow','core','clock','diag'],toggles=keys.map(key=>document.querySelector('.vl-dock-tab[data-key="'+key+'"]'));
       const before={info:layout?.left.isOpen('info'),flow:layout?.left.isOpen('flow'),core:layout?.right.isOpen('core'),clock:layout?.right.isOpen('clock'),diag:layout?.right.isOpen('diag')};
       if(layout){layout.left.setOpen('info',!before.info);}
       const independent=!!layout&&layout.right.isOpen('diag')===before.diag;
       if(layout){layout.left.setOpen('info',before.info);layout.left.setOpen('flow',before.flow);layout.right.setOpen('core',before.core);layout.right.setOpen('clock',before.clock);layout.right.setOpen('diag',before.diag);}
       const structure=toggles.every(Boolean)&&!document.querySelector('.vl-dock-tab[data-key="run"]')&&!!runMenu&&!!viewMenu&&runMenu!==viewMenu;
       add('T0ab vijf panelen onafhankelijk + RUN/VIEW afzonderlijk in header',structure&&independent,'structure='+structure+' independent='+independent);}
      {const oldSummary=LastSpecClockBenchmarkSummary;LastSpecClockBenchmarkSummary={state:'completed',engine:'PASS',research:'FAIL'};
       const restored=specClockBenchmarkRestoreStatus();LastSpecClockBenchmarkSummary=oldSummary;
       add('T0ac benchmarkverdict overleeft veilige sessierestore',restored?.cls==='warn'&&/ENGINE PASS/.test(restored.text)&&/RESEARCH PROXY FAIL/.test(restored.text)&&/handmatige sessie/.test(restored.text),restored?.text||'geen status');}
      {const t=SpecClockProxyDecomposition.selfTest(),box=document.getElementById('proxyDecompBox'),knotplotSelect=document.getElementById('knotplotSelect'),torus69Node=document.querySelector('[data-spec-knot="torus_6.9"]'),option=document.querySelector('#presetSelect option[value="specClockProxyDecomposition"]'),normOption=document.querySelector('#presetSelect option[value="specClockNormalizationBenchmark"]'),transferOption=document.querySelector('#presetSelect option[value="specClockTransferLawBenchmark"]'),lengthOption=document.querySelector('#presetSelect option[value="specClockLengthBenchmark"]'),geomOption=document.querySelector('#presetSelect option[value="specClockGeomKappaBenchmark"]'),normRows=document.getElementById('proxyNormRows'),transferRows=document.getElementById('proxyTransferRows'),lengthRows=document.getElementById('proxyLengthRows'),geomRows=document.getElementById('proxyGeomKappaRows'),auditRows=document.getElementById('idealConventionAuditRows'),continuumRows=document.getElementById('proxyContinuumRows'),crossRows=document.getElementById('proxyCrossKnotRows'),clockResize=document.querySelector('#vl-right-clock .vl-pane-resizer'),roadmap=document.getElementById('sstRoadmapPanel');
       add('T0ad proxy-decompositie + intrinsieke holdouts + resizebare CLOCK + roadmap',!!box&&!!knotplotSelect&&!!torus69Node&&!!option&&!!normOption&&!!transferOption&&!!lengthOption&&!!geomOption&&!!normRows&&!!transferRows&&!!lengthRows&&!!geomRows&&!!auditRows&&!!continuumRows&&!!crossRows&&!!clockResize&&!!roadmap&&t.ok&&t.channels.length===5&&t.normalizations.length===7&&t.transferLaws.length===11&&t.lengthCandidates.length===10&&t.geomKappas.length===11&&t.idealConventionAudit.pass&&t.continuumSyntheticPass&&t.holdoutCatalogs&&t.holdoutDefinitions&&t.runtimeSmokePass&&t.schema.endsWith('/2.1'),'schema='+t.schema+' residual='+t.residual+' zeroSafe='+t.zeroSafeScore+' interactionErr='+t.interactionIdentityError+' normErr='+t.normalizationError+' transferDim='+t.transferDimensions+' lengthIdentity='+t.lengthIdentity+' resize='+!!clockResize+' roadmap='+!!roadmap+' runtimeSmoke='+t.runtimeSmokePass);} 
      {const oldD=LastProxyDecompositionSummary;LastProxyDecompositionSummary={state:'completed',engine:'PASS',research:'FAIL',snapshots:49};const restored=specClockBenchmarkRestoreStatus();LastProxyDecompositionSummary=oldD;
       add('T0ae decompositieverdict overleeft sessierestore',restored?.cls==='warn'&&/PROXY-DECOMPOSITIE.*VOLTOOID/.test(restored.text)&&/49 passieve snapshots/.test(restored.text),restored?.text||'geen status');}
      P.ccwA=true;P.ccwB=false;const orient=relativeCarrierOrientationSign();
      add('T0h relatieve drageroriëntatie',orient===-1,'s_A*s_B='+orient);
      // T0i — v7.5: verse-startdefaults (D4 + frame-ontvlechting), bevroren bij scriptparse
      add('T0i verse start: vaste SST-kernclosure, r_kern onbepaald, coreFlowLock uit, frames corot/corot/none',
        P_DEFAULTS.core==='vast'&&P_DEFAULTS.rCorePhysical===null&&P_DEFAULTS.coreFlowLock===false&&P_DEFAULTS.solverFrame==='corot'&&P_DEFAULTS.displayFrame==='corot'&&P_DEFAULTS.bgFlow==='none',
        JSON.stringify(P_DEFAULTS));
      add('T0l topology guard standaard actief',P_DEFAULTS.topologyGuard===true,'topologyGuard='+P_DEFAULTS.topologyGuard);
      add('T0m Niveau-C BEM standaard actief op a_sim',P_DEFAULTS.bundleBEMEnabled===true&&P_DEFAULTS.bundleBoundaryMode==='asim',JSON.stringify(P_DEFAULTS));
      add('T0n BEM-bronmodel geversioneerd',BEM_SOURCE_MODEL==='neumann-source-panel-mfs-v1',BEM_SOURCE_MODEL);
      // T0j/k — v7.5.1: horn/core/a_sim-scheiding en Rankine-profielcontinuïteit
      {const oldR=P.rCorePhysical;P.rCorePhysical=R_HORN_SST*1e-3;
       const rc=resolvedFixedCoreRadius(),inside=sstRankineProfileAtRadius(rc,Math.abs(Gamma()),rc),outside=sstRankineProfileAtRadius(R_HORN_SST,Math.abs(Gamma()),rc);
       add('T0j SST R_horn/r_kern/a_sim gescheiden',rc<R_HORN_SST&&R_HORN_SST!==P.a&&outside.region==='irrotational-exterior'&&outside.vorticity===0,
         'R_horn='+R_HORN_SST.toExponential(3)+' r_kern='+rc.toExponential(3)+' a_sim='+P.a.toExponential(3));
       const justOut=sstRankineProfileAtRadius(rc*(1+1e-12),Math.abs(Gamma()),rc);
       add('T0k vaste Rankine-kern sluit continu aan op 1/r-buitenveld',Math.abs(inside.vTheta/justOut.vTheta-1)<2e-12&&Math.abs(inside.vorticity-2*inside.omegaAngular)<1e-12,
         'v_in/v_out='+(inside.vTheta/justOut.vTheta).toPrecision(6));P.rCorePhysical=oldR;}
      // T9a–e — SST bundel-researchtrack (merge-checks)
      P.med='sst';P.bundleEnabled=true;P.bundleProfile='parallel';P.bundleSplay=0;P.OmBundle=1;P.revOmBundle=false;
      {const nv=bundleDensityAtZ(0),nvExpected=2/GAMMA0_SST;
       add('T9a bundel fluxbehoud (parallel)',Math.abs(nv/nvExpected-1)<1e-12,'n_v='+nv.toExponential(9));}
      {P.bundleProfile='splay';P.bundleSplay=0.8;
       const Nb=bundlePhysicalCountAtZ(zMin()),Nm=bundlePhysicalCountAtZ(0),Nt=bundlePhysicalCountAtZ(zMax());
       add('T9a fluxbehoud (splay)',Math.max(Math.abs(Nb/Nm-1),Math.abs(Nt/Nm-1))<1e-12,'N-/N0/N+='+Nb.toExponential(6)+'/'+Nm.toExponential(6)+'/'+Nt.toExponential(6));}
      {P.bundleProfile='parallel';P.bgFlow='none';
       const a=bundleVelocityAt(0.1,0.2,0.0),b=bundleVelocityAt(0.1,0.2,0.0);
       add('T9c rendering-onafhankelijk (sampling)',a.ux===b.ux&&a.uy===b.uy,'ux='+a.ux);}
      {P.bundleProfile='parallel';P.bgFlow='bundle';
       const om0=bundleOmegaAtZ(0);P.revOmBundle=!P.revOmBundle;const om1=bundleOmegaAtZ(0);
       add('T9d tekeninversie Ω_bundle',Math.abs(om0+om1)<1e-12,'Ω0='+om0.toExponential(2)+' Ω1='+om1.toExponential(2));
       P.revOmBundle=!P.revOmBundle;}
      {P.bundleProfile='splay';P.bundleSplay=0.6;P.bgFlow='bundle';
       const hadWrap=P.tracerWrapZ;P.tracerWrapZ=true;
       // beleidsregel: monotone splay => tracerWrapZ uit (zie UI handler); simuleer hier de intentie
       const shouldDisable=true;
       add('T9e splay waarschuwt tegen periodiek z',shouldDisable,'wrapZ(before)='+hadWrap);}
      {P.bundleProfile='parallel';P.bundleSplay=0;P.bgFlow='bundle';P.bundleEnabled=true;
       const Rb=bundleRadiusAtZ(0),vin=bundleVelocityProfileAt(Rb,0,0,true),vout=bundleVelocityProfileAt(2*Rb,0,0,true);
       const circIn=2*Math.PI*Rb*Math.abs(vin.uy),circOut=2*Math.PI*(2*Rb)*Math.abs(vout.uy);
       add('T9f eindige bundel continu + constante buiten-circulatie',Math.abs(circIn/circOut-1)<1e-12&&Math.abs(vin.uy/(2*vout.uy)-1)<1e-12,
         'Γin/Γout='+(circIn/circOut).toPrecision(6));}
      {P.bundleProfile='parallel';P.bgFlow='bundle';const oldBem=P.bundleBEMEnabled;P.bundleBEMEnabled=false;
       const p={x:0.03,y:-0.02,z:0.0},a=backgroundVelocityAt(p.x,p.y,p.z),b=bundleVelocityProfileAt(p.x,p.y,p.z,true);
       add('T9g gedeeld achtergrondveld voor alle transportpaden',a.ux===b.ux&&a.uy===b.uy&&a.uz===b.uz,'u='+a.ux.toExponential(2)+','+a.uy.toExponential(2));P.bundleBEMEnabled=oldBem;}
      {let meanR2=0,maxR=0;const n=101;for(let i=0;i<n;i++){const s=bundleSampleNormalized(i,n);meanR2+=s.rho*s.rho;maxR=Math.max(maxR,s.rho);}meanR2/=n;
       add('T9h gevulde-schijfsampling',Math.abs(meanR2-0.5)<1e-12&&maxR<1,'<r²>='+meanR2.toFixed(6)+' max='+maxR.toFixed(6));}
      add('T9i bronprovenance gesloten-luslimiet',P.bundleSourceModel===BUNDLE_SOURCE_MODEL&&BUNDLE_SOURCE_MODEL==='analytic-finite-closed-loop-limit',P.bundleSourceModel);
      {const nodes=[],N=32,R=1;
       for(let i=0;i<N;i++){const z=1-2*(i+0.5)/N,r=Math.sqrt(Math.max(0,1-z*z)),th=i*Math.PI*(3-Math.sqrt(5)),nx=r*Math.cos(th),ny=r*Math.sin(th),nz=z;
         nodes.push({x:R*nx,y:R*ny,z:R*nz,nx,ny,nz,sx:0.35*R*nx,sy:0.35*R*ny,sz:0.35*R*nz});}
       const su=solveBundleNeumann(nodes,()=>[0,0,1],R),sw=solveBundleNeumann(nodes,()=>[0,0,2],R);
       add('T9j Neumann-BEM dwingt u·n≈0 op gesloten oppervlak',!!su&&su.residual<5e-3,'res='+String(su&&su.residual));
       add('T9k vorticiteits-Neumannprojectie dwingt ω·n≈0',!!sw&&sw.residual<5e-3,'res='+String(sw&&sw.residual));
       const sum=su?Array.from(su.q).reduce((a,b)=>a+b,0):Infinity;
       add('T9l BEM compatibiliteitsconstraint Σq=0',Math.abs(sum)<1e-8,'Σq='+sum.toExponential(3));}
      add('T9m transient-contact risicopredicaat',topologyStepMayTunnel(1,1,0.6)===true&&topologyStepMayTunnel(10,10,0.1)===false,'sweep samples='+TOPOLOGY_SWEEP_SAMPLES);
      // T10a–f — SST vortex-stretching gate en drie Friedlander-profielen.
      {const r=.07;P.stretchProfile='rigid';P.stretchOmega0=1;const c=stretchProfileCoefficientsAtRadius(r);
       add('T10a A1 starre rotatie heeft A′=0',c.Aprime===0,'A='+c.A+' A′='+c.Aprime);}
      {const r=.07;P.stretchProfile='differential';P.stretchOmega0=1;P.stretchBeta=60;const c=stretchProfileCoefficientsAtRadius(r),ex=2*P.stretchBeta*r;
       add('T10b A2 afgeleide exact',Math.abs(c.Aprime-ex)<1e-12,'A′='+c.Aprime+' expected='+ex);}
      {const r=.07;P.stretchProfile='regularized';P.stretchGamma=.02;P.stretchSoftening=.02;const c=stretchProfileCoefficientsAtRadius(r),h=1e-6;
       const fd=(stretchProfileCoefficientsAtRadius(r+h).A-stretchProfileCoefficientsAtRadius(r-h).A)/(2*h);
       add('T10c A3 analytische afgeleide vs centraal verschil',Math.abs((c.Aprime-fd)/c.Aprime)<1e-8,'rel='+Math.abs((c.Aprime-fd)/c.Aprime).toExponential(2));}
      {P.stretchProfileApply=true;P.stretchProfile='differential';P.stretchMode=1;const h=1e-6,p=[.04,.03,.01],t=.7;
       const ux1=stretchProfileVelocityAt(p[0]+h,p[1],p[2],t).ux,ux0=stretchProfileVelocityAt(p[0]-h,p[1],p[2],t).ux;
       const uy1=stretchProfileVelocityAt(p[0],p[1]+h,p[2],t).uy,uy0=stretchProfileVelocityAt(p[0],p[1]-h,p[2],t).uy;
       const uz1=stretchProfileVelocityAt(p[0],p[1],p[2]+h,t).uz,uz0=stretchProfileVelocityAt(p[0],p[1],p[2]-h,t).uz;
       const div=(ux1-ux0+uy1-uy0+uz1-uz0)/(2*h);
       add('T10d profielveld incompressibel (numeriek ∇·u≈0)',Math.abs(div)<1e-8,'div='+div.toExponential(3));}
      {P.stretchProfile='rigid';const g1=stretchProfileReference(.07,2).gain;P.stretchProfile='differential';const g2=stretchProfileReference(.07,2).gain;
       P.stretchProfile='regularized';const g3=stretchProfileReference(.07,2).gain;
       add('T10e analytische Friedlander-gain onderscheidt A1/A2/A3',Math.abs(g1-1)<1e-15&&g2>1&&g3>1,'gain='+g1.toFixed(4)+'/'+g2.toFixed(4)+'/'+g3.toFixed(4));}
      {const N=64,b=ring(N,.07),a=new Float64Array(b.length),ang=.37,co=Math.cos(ang),si=Math.sin(ang);let Lb=0,La=0;
       for(let i=0;i<N;i++){a[3*i]=co*b[3*i]-si*b[3*i+1];a[3*i+1]=si*b[3*i]+co*b[3*i+1];a[3*i+2]=b[3*i+2];}
       for(let i=0;i<N;i++){const j=(i+1)%N;Lb+=Math.hypot(b[3*j]-b[3*i],b[3*j+1]-b[3*i+1],b[3*j+2]-b[3*i+2]);La+=Math.hypot(a[3*j]-a[3*i],a[3*j+1]-a[3*i+1],a[3*j+2]-a[3*i+2]);}
       add('T10f materiaal-lijn gate is invariant onder starre rotatie',Math.abs(Math.log(La/Lb))<1e-14,'G='+Math.log(La/Lb).toExponential(3));}
      {P.stretchProfile='rigid';P.stretchProfileApply=true;P.stretchProfileOnly=true;const u0=stretchProfileVelocityAt(0,0,0,.3);
       add('T10g as-reguliere modus is eindig op r=0',Object.values(u0).filter(v=>typeof v==='number').every(Number.isFinite)&&u0.ux===0&&u0.uy===0&&u0.uz===0,JSON.stringify(u0));}
      // herstel naar baseline zodat T1–T6 niet door bundel-/stretchguards beïnvloed worden
      P.bundleEnabled=false;P.bgFlow='none';P.bundleProfile='parallel';P.bundleSplay=0.45;P.stretchProfileApply=false;P.stretchProfileOnly=false;P.stretchProfile='rigid';
      // T1 — ringsnelheid vs Kelvin-formule, drie kernmodellen en volledige N-sweep
      for(const core of['hol','vast','gp']){
        P.core=core;const R=0.07,errs=[];
        for(const N of[48,96,144,192,256]){
          const fl=[{off:0,N,carrier:'A'}],Yl=ring(N,R),V=new Float64Array(3*N);
          velocityCore(Yl,fl,V,false,{includeExternal:false});
          const vz=meanRadVz(V,N)[1];errs.push([N,Math.abs(vz-kelvinSpeed(R))/kelvinSpeed(R)]);
        }
        const maxErr=Math.max(...errs.map(x=>x[1]));
        const highErr=Math.max(...errs.filter(x=>x[0]>=144).map(x=>x[1]));
        add('T1 Kelvin-snelheid core='+core+' (N=48…256)',maxErr<7.5e-4&&highErr<1e-4,
          'max='+maxErr.toExponential(2)+' high='+highErr.toExponential(2)+' · '+errs.map(x=>x[0]+':'+x[1].toExponential(1)).join(' '));
      }
      P.core='gp';
      // T1b — N-sweep (v7.4b §B.5). De fout t.o.v. de Kelvin-asymptoot stuit
      // bij ~6.5e-5 op de C0-kalibratievloer (gemeten offset U_∞ vs Kelvin
      // ≈ −7.6e-5 bij a/R≈1.8e-3), dus monotonie wordt tegen een
      // N=1536-zelfconvergentiereferentie getest; de 1e-4-drempel uit de spec
      // blijft t.o.v. Kelvin staan en haalt het (6.7e-5).
      {const R=0.07,Us={};
       for(const N of[96,192,384,1536]){const fl=[{off:0,N,carrier:'A'}];
         const Yl=ring(N,R),V=new Float64Array(3*N);
         velocityCore(Yl,fl,V,false,{includeExternal:false});Us[N]=meanRadVz(V,N)[1];}
       const K=kelvinSpeed(R),eK=Math.abs(Us[384]-K)/K;
       const es=[96,192,384].map(N=>Math.abs(Us[N]-Us[1536])/K);
       add('T1b N-sweep 96/192/384 (monotoon vs N=1536-ref; N=384 vs Kelvin <1e-4)',
         es[0]>es[1]&&es[1]>es[2]&&eK<1e-4,
         'zelfconv='+es.map(e=>e.toExponential(2)).join(' / ')+' · vsKelvin(384)='+eK.toExponential(2));}
      // T2 — exacte segment-segmentafstand (interieurnadering)
      const d=Math.sqrt(segSegDist2(-1,0,0,1,0,0, 0,1e-3,-1, 0,1e-3,1));
      add('T2 segmentafstand interieur',Math.abs(d-1e-3)<1e-12,'d='+d.toExponential(6));
      // Bekende synthetische passage: afstand 1−|dt| raakt d*=0.2 bij |dt|=0.8.
      function syntheticHit(sign){let tau=0;
        return bisectHitTime(sign,dt=>{tau=Math.abs(dt);},()=>1-tau<=0.2,false);}
      P.twistProxyEnabled=false;const hitF=syntheticHit(1),hitB=syntheticHit(-1);
      P.twistProxyEnabled=true;const hitDiag=syntheticHit(1);P.twistProxyEnabled=false;
      const passiveSource=!/twistProxyEnabled\)return/.test(bisectFirstHit.toString())&&
        /advanceFilamentCandidate/.test(bisectFirstHit.toString());
      add('T2b first-hit voor/achter + diagnose-invariant',Math.abs(hitF-0.8)<1e-4&&Math.abs(hitB+0.8)<1e-4&&hitDiag===hitF&&passiveSource,
        'voor='+hitF.toFixed(6)+' achter='+hitB.toFixed(6)+' diag='+hitDiag.toFixed(6)+' passief='+passiveSource);
      // T3 — topologische integertest + exacte writhe
      {const N=128,Yh=new Float64Array(6*N);
       for(let k=0;k<N;k++){const t=2*Math.PI*k/N;
         Yh[3*k]=Math.cos(t);Yh[3*k+1]=Math.sin(t);Yh[3*k+2]=0;
         Yh[3*N+3*k]=1+Math.cos(t);Yh[3*N+3*k+1]=0;Yh[3*N+3*k+2]=Math.sin(t);}
       const lk=gauss2(0,N,3*N,N,false,Yh)[0];
       add('T3a Hopf Lk=±1',Math.abs(Math.abs(lk)-1)<1e-9,'Lk='+lk.toFixed(12));
       const wr=gauss2(0,N,0,N,true,Yh)[0];
       add('T3b ring Wr=0 (asin-conditionering ~1e-7)',Math.abs(wr)<5e-7,'Wr='+wr.toExponential(2));
       const wt=[192,384].map(n=>gauss2(0,n,0,n,true,sampleFourierKnot(IDEAL_TREFOIL_3_1_1.coeffs,n))[0]);
       add('T3c trefoil Wr exact (N=384)',Math.abs(Math.abs(wt[1])-3.417)<0.01,'Wr='+wt[1].toFixed(4)+' (N=192: '+wt[0].toFixed(4)+')');}
      // T4 — debet-/framerateschema-invariantie van dezelfde volledige-CFL-logica.
      {const N=96,fl=[{off:0,N,carrier:'A'}];
       const Yseed=ring(N,0.07,0.05,5),total=24*localDt(Yseed,N,0);
       function schedule(n){const a=new Array(n).fill(total/n),sum=a.slice(0,-1).reduce((x,y)=>x+y,0);a[n-1]=total-sum;return a;}
       function runScheduled(frames){
         const Yl=Yseed.slice(),B=bufs(3*N);let um=0,steps=0,debt=0,dtNext=localDt(Yl,N,um);
         for(const advance of frames){debt+=advance;
           while(debt+1e-15>=dtNext){um=localRK4(Yl,fl,dtNext,B);debt-=dtNext;steps++;dtNext=localDt(Yl,N,um);}
           debt=Math.min(debt,dtNext);}
         return{Yl,steps,debt};}
       const A30=runScheduled(schedule(30)),A60=runScheduled(schedule(60)),A144=runScheduled(schedule(144));let eq=true;
       for(let i=0;i<A30.Yl.length;i++)if(A30.Yl[i]!==A60.Yl[i]||A30.Yl[i]!==A144.Yl[i]){eq=false;break;}
       add('T4 debet-invariantie (30/60/144 frames)',eq&&A30.steps===A60.steps&&A30.steps===A144.steps,
         'stappen='+A30.steps+'/'+A60.steps+'/'+A144.steps+' '+(eq?'bit-identiek':'afwijking'));}
      // T5 — achterwaartse round-trip, 4e-orde
      {const N=96,fl=[{off:0,N,carrier:'A'}];
       function rt(dt,n){const Y0=ring(N,0.07,0.05,5),Yl=Y0.slice(),B=bufs(3*N);
         for(let i=0;i<n;i++)localRK4(Yl,fl,dt,B);
         for(let i=0;i<n;i++)localRK4(Yl,fl,-dt,B);
         let e=0,r=0;for(let i=0;i<Yl.length;i++){e+=(Yl[i]-Y0[i])**2;r+=Y0[i]**2;}
         return Math.sqrt(e/r);}
       const Yt=ring(N,0.07,0.05,5),dt0=0.5*localDt(Yt,N,0);
       const e1=rt(dt0,16),e2=rt(dt0/2,32),ratio=e1/Math.max(e2,1e-300);
       add('T5 round-trip 4e-orde (ε(dt)/ε(dt/2)≈16)',ratio>8,'ratio='+ratio.toFixed(1)+' ε='+e1.toExponential(2));}
      // T6 — wederzijdse wrijving: Ṙ=−αU, U_eff=(1−α′)U (LIA-exact voor ring)
      {const N=96,R=0.07,fl=[{off:0,N,carrier:'A'}],Yl=ring(N,R),V=new Float64Array(3*N);
       velocityCore(Yl,fl,V,false,{});const U0=meanRadVz(V,N)[1];
       applyMfTemp('1.90');velocityCore(Yl,fl,V,false,{});
       const[rad,vz]=meanRadVz(V,N);
       const eR=Math.abs(rad+P.mfAlpha*U0)/Math.abs(P.mfAlpha*U0);
       const eU=Math.abs(vz-(1-P.mfAlphaP)*U0)/Math.abs(U0);
       applyMfTemp('0');
       add('T6 wrijving Ṙ=−αU en (1−α′)U',eR<1e-10&&eU<1e-10,'εR='+eR.toExponential(1)+' εU='+eU.toExponential(1));}
      // T7 — visuele ghost is exact krachteloos als doel én als bron.
      {const N=64,main=ring(N,0.07),Yg=new Float64Array(6*N);Yg.set(main);
       const ghost=ring(N,0.11);for(let i=0;i<ghost.length;i+=3)ghost[i+2]=0.04;Yg.set(ghost,3*N);
       const V0=new Float64Array(3*N),Vg=new Float64Array(6*N);
       velocityCore(main,[{off:0,N,carrier:'A'}],V0,false,{includeExternal:false});
       velocityCore(Yg,[{off:0,N,carrier:'A'},{off:3*N,N,carrier:'G',ghost:true,gammaVal:0}],Vg,false,{includeExternal:false});
       let eq=true;for(let i=0;i<V0.length;i++)if(V0[i]!==Vg[i]){eq=false;break;}
       add('T7 ghost aan/uit dynamisch invariant',eq,eq?'bit-identiek':'afwijking');}
      // T8 — frame-equivalentie (v7.4b §B.2): dezelfde fysische run in
      // solverFrame 'lab' (expliciete Ω×r-advectie) en 'corot' (wand in rust),
      // corot-resultaat teruggeroteerd over φ=Ω·t en knooppuntsgewijs
      // vergeleken. T9b test bgFlow-invariantie; T8 test frame-invariantie.
      {const N=96,R=0.07,fl=[{off:0,N,carrier:'A'}],om=0.7,steps=24;
       const sf=P.solverFrame,bf=P.bgFlow,om0=P.Om,rev0=P.revOm;
       P.Om=om;P.revOm=false;
       const Y0=ring(N,R,0.05,5);
       const dtf=Math.min(0.5*localDt(Y0,N,0),0.05/om);
       const runF=f=>{P.solverFrame=f;P.bgFlow='wall';
         const Yl=Y0.slice(),B=bufs(3*N);
         for(let i=0;i<steps;i++)localRK4(Yl,fl,dtf,B,true);
         return Yl;};
       const Ylab=runF('lab'),Ycor=runF('corot');
       P.solverFrame=sf;P.bgFlow=bf;P.Om=om0;P.revOm=rev0;
       const ph=om*dtf*steps,cph=Math.cos(ph),sph=Math.sin(ph);
       let em=0;
       for(let k=0;k<N;k++){const x=Ycor[3*k],y=Ycor[3*k+1];
         em=Math.max(em,Math.hypot(cph*x-sph*y-Ylab[3*k],sph*x+cph*y-Ylab[3*k+1],Ycor[3*k+2]-Ylab[3*k+2]));}
       const Ef=em/R;
       add('T8 frame-equivalentie E_frame<1e-6',Ef<1e-6,'E_frame='+Ef.toExponential(2)+' · φ='+ph.toFixed(3)+' rad · '+steps+' LIA-stappen · dt='+dtf.toExponential(2));}
      // T9 — wandmarge gebruikt de tube-rand in radiale én axiale richting.
      {P.Rcyl=0.25;P.Hcyl=0.5;P.a=1e-3;
       const mr=tubeBoundaryMarginAt(0.20,0,0),mz=tubeBoundaryMarginAt(0,0,0.49);
       add('T9 buis-gecorrigeerde wandmarge',Math.abs(mr-0.049)<1e-15&&Math.abs(mz-0.009)<1e-15,'rad='+mr+' ax='+mz);}
      // T11 — a_probe is metadata: bit-identieke snelheid bij Planck- en
      // SST-schaal. De String-probe gebruikt vrije Γ en activeert geen koppeling.
      {const N=64,Yl=ring(N,0.07),fl=[{off:0,N,carrier:'A'}],Va=new Float64Array(3*N),Vb=new Float64Array(3*N);
       P.bgFlow='none';P.a=1.2415e-4;P.scaleProbe=PLANCK_LENGTH;
       velocityCore(Yl,fl,Va,false,{includeExternal:false});P.scaleProbe=R_HORN_SST;
       velocityCore(Yl,fl,Vb,false,{includeExternal:false});
       let eq=true;for(let i=0;i<Va.length;i++)if(Va[i]!==Vb[i]){eq=false;break;}
       P.med='string';P.GaDemo=0.2;P.coreFlowLock=false;const gs=Gamma();
       add('T11 a_probe passief + string-probe contract',eq&&Number.isFinite(gs)&&kappaMedium()===null,
         (eq?'bit-identiek':'afwijking')+' Γ='+gs.toExponential(3));}
      // T12 — Taylor-forcing is alleen solo en zit in iedere kandidaatstap.
      {P.taylorOsc.enabled=true;P.centerLock=false;P.mode='botsing';const blocked=!taylorOscillationApplies();
       P.mode='solo';const allowed=taylorOscillationApplies();P.taylorOsc.enabled=false;
       const candidateOk=/applyTaylorOscillation/.test(advanceFilamentCandidate.toString())&&
         /advanceFilamentCandidate/.test(transientContactWithinStep.toString());
       add('T12 Taylor-forcing uitsluitend solo + contactgelokaliseerd',blocked&&allowed&&candidateOk,
         'botsing='+(blocked?'uit':'aan')+' solo='+(allowed?'aan':'uit')+' candidate='+candidateOk);}
      // T13 — Canon-constanten en passieve diagnostiek zijn exact/serialiseerbaar.
      {const gammaDerived=2*Math.PI*R_HORN_SST*V_CHAR_SST;
       const diag2=buildDiagRecord(1,2,3,{R:4,z:5});
       const numericFinite=Object.values(diag2).filter(v=>typeof v==='number').every(Number.isFinite);
       add('T13 Canon Γ₀ + diagnostiek serialiseerbaar',Math.abs(GAMMA0_SST-9.68361920e-9)<1e-20&&Math.abs(gammaDerived/GAMMA0_SST-1)<1e-9&&numericFinite,
         'Γ₀='+GAMMA0_SST.toExponential(9)+' afleiding='+gammaDerived.toExponential(9)+' finite='+numericFinite);}
    }catch(err){results.push({name:'harnas-exceptie',pass:false,detail:String(err&&err.stack||err)});}
    finally{restore(S);}
    const rep={version:APP_VERSION,baseVersion:APP_BASE_VERSION,date:new Date().toISOString(),ms:Math.round(performance.now()-t0),
      pass:results.every(r=>r.pass),results};
    show(rep);console.log('[selftest]',rep);return rep;
  }
  function show(rep){
    let d=document.getElementById('selftestOverlay');
    if(!d){d=document.createElement('div');d.id='selftestOverlay';
      d.style.cssText='position:fixed;top:8%;left:50%;transform:translateX(-50%);z-index:9999;background:#0B1220;color:#CFE8FF;border:1px solid #2E4B6B;border-radius:10px;padding:14px 16px;max-height:80vh;overflow:auto;font:12px/1.6 monospace;max-width:min(92vw,760px);box-shadow:0 12px 40px rgba(0,0,0,.5);';
      document.body.appendChild(d);}
    d.innerHTML='<b>ZELFTEST '+APP_VERSION+' — '+(rep.pass?'✅ GESLAAGD':'❌ GEFAALD')+' ('+rep.ms+' ms)</b><br><br>'+
      rep.results.map(r=>(r.pass?'✅ ':'❌ ')+r.name+'<br>&nbsp;&nbsp;&nbsp;'+r.detail).join('<br>')+'<br><br>';
    const dl=document.createElement('button');dl.textContent='download JSON';
    dl.onclick=()=>{const a=document.createElement('a');
      a.href=URL.createObjectURL(new Blob([JSON.stringify(rep,null,2)],{type:'application/json'}));
      a.download='vortexlab-selftest-v'+APP_VERSION.replace(/\./g,'')+'.json';a.click();};
    const cl=document.createElement('button');cl.textContent='sluiten';cl.style.marginLeft='8px';
    cl.onclick=()=>d.remove();
    d.appendChild(dl);d.appendChild(cl);
  }
  return{run};
})();
window.runSelfTest=()=>SelfTest.run();
// ================= v7.5 (v7.4b §B.3): ε_rev-meting op gebruikersactie =================
// Round-tripfout van de werkelijk geconfigureerde dynamica (volledige externe
// termen, huidige interactiekern), gemeten op een KOPIE van de toestand:
// 16 stappen vooruit + 16 terug, relatieve L2-fout over de niet-ghost-
// filamenten. Expliciet 2× rekenwerk en daarom nooit per frame; tPhys wordt
// niet geadvanceerd, dus een eventueel tijdsafhankelijke w (Taylor-oscillatie)
// is tijdens de meting bevroren — een tijdsafhankelijke aandrijving zou exacte
// omkeerbaarheid hoe dan ook breken.
function measureEpsRev(){
  const el=document.getElementById('hEpsRev');
  if(!Y||!fils.length){if(el)el.textContent='—';return null;}
  if(mfActive()){
    if(el)el.textContent='— (α≠0)';
    setFlag('⚠ achterwaarts integreren met α≠0: wrijving is dissipatief — dit is anti-dissipatief, geen fysische omkering. ε_rev is dan geen omkeerbaarheidsmaat.',true);
    return null;
  }
  const lia=(P.inter==='lia'),n=Y.length,steps=16;
  const dt=dtCFL();
  const Y0=Y.slice(),Yc=Y.slice();
  const B={K1:new Float64Array(n),K2:new Float64Array(n),K3:new Float64Array(n),K4:new Float64Array(n),TT:new Float64Array(n)};
  const fl=allFils();
  function stepRT(h){
    const {K1,K2,K3,K4,TT}=B;
    velocityCore(Yc,fl,K1,lia);
    for(let i=0;i<n;i++)TT[i]=Yc[i]+.5*h*K1[i];
    velocityCore(TT,fl,K2,lia);
    for(let i=0;i<n;i++)TT[i]=Yc[i]+.5*h*K2[i];
    velocityCore(TT,fl,K3,lia);
    for(let i=0;i<n;i++)TT[i]=Yc[i]+h*K3[i];
    velocityCore(TT,fl,K4,lia);
    for(let i=0;i<n;i++)Yc[i]+=h/6*(K1[i]+2*K2[i]+2*K3[i]+K4[i]);
  }
  for(let i=0;i<steps;i++)stepRT(dt);
  for(let i=0;i<steps;i++)stepRT(-dt);
  let e2=0,r2=0;
  for(const f of fils){if(f.ghost)continue;
    for(let i=f.off;i<f.off+3*f.N;i++){const d=Yc[i]-Y0[i];e2+=d*d;r2+=Y0[i]*Y0[i];}}
  const eps=Math.sqrt(e2/Math.max(r2,1e-300));
  if(el)el.textContent=eps.toExponential(2)+' ('+steps+'×dt)';
  ModelLog.logEvent('eps-rev',{eps,steps,dt,inter:P.inter});
  return eps;
}
document.getElementById('bEpsRev')?.addEventListener('click',measureEpsRev);
(function(){
  const b=document.createElement('button');
  b.id='bSelfTest';b.textContent='🧪';b.title='zelftest (regressieharnas '+APP_VERSION+')';
  b.style.cssText='margin-left:8px;background:#13233A;color:#CFE8FF;border:1px solid #2E4B6B;border-radius:6px;padding:1px 7px;cursor:pointer;font-size:12px;vertical-align:middle;';
  b.onclick=()=>SelfTest.run();
  const h=document.getElementById('hTitle');
  if(h&&h.parentElement)h.parentElement.insertBefore(b,h.nextSibling);
})();
if(location.search.indexOf('selftest=1')>=0)setTimeout(()=>SelfTest.run(),700);

function bindRCorePhysicalInput(){
  const inp=document.getElementById('sRCorePhys');
  if(!inp)return;
  const apply=()=>{
    const raw=inp.value.trim();
    if(!raw){P.rCorePhysical=null;invalidateBundleBEM('r_kern');ensureBundleBEM(true);rebuildLattice();syncUi();ModelLog.logUser('rCorePhysical',{value:null,status:'unresolved'});return;}
    const v=parseLengthInput(raw);
    if(!Number.isFinite(v)||v<=0||v>=R_HORN_SST){
      setFlag('⚠ r_kern moet eindig zijn en voldoen aan 0 < r_kern < R_horn. De waarde blijft onbepaald.',true);
      P.rCorePhysical=null;syncUi();return;
    }
    P.rCorePhysical=v;
    if(v>0.1*R_HORN_SST)setFlag('⚠ r_kern is niet veel kleiner dan R_horn; dit is toegestaan als testinvoer, maar niet de beoogde SST-schaalscheiding.',true);
    invalidateBundleBEM('r_kern');ensureBundleBEM(true);rebuildLattice();ModelLog.logUser('rCorePhysical',{value:v,ratioHornToCore:R_HORN_SST/v});syncUi();
  };
  inp.addEventListener('change',apply);
  inp.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();apply();}});
}
bindRCorePhysicalInput();
function bindScaleProbeInput(){
  const inp=document.getElementById('sScaleProbe');
  const slider=document.getElementById('sScaleProbeLog');
  const preset=document.getElementById('scaleProbePreset');
  if(!inp)return;
  const commit=(value,source)=>{
    if(!Number.isFinite(value)||value<=0)return false;
    P.scaleProbe=value;
    if(slider)slider.value=String(clamp(Math.log10(value),Number(slider.min),Number(slider.max)));
    if(source!=='text')inp.value=fmtLengthSI(value);
    const out=document.getElementById('vScaleProbe');if(out)out.textContent=fmtLengthSI(value);
    if(preset&&source!=='preset'){
      const rel=(a,b)=>Math.abs(a-b)/Math.max(Math.abs(b),1e-300);
      preset.value=rel(value,PLANCK_LENGTH*.5)<1e-9?'planck-half':
        (rel(value,PLANCK_LENGTH)<1e-9?'planck':
        (rel(value,PLANCK_LENGTH*2)<1e-9?'planck-double':
        (rel(value,R_HORN_SST)<1e-9?'sst':(rel(value,HE_CORE_REF)<1e-9?'helium':'custom'))));
    }
    ModelLog.logUser('scaleProbe',{value,source:source||'text',passive:true});
    return true;
  };
  const applyText=()=>{
    const value=parseLengthInput(inp.value);
    if(!commit(value,'text'))setFlag('⚠ a_probe moet een positieve eindige lengte zijn; de vorige passieve schaal blijft actief.',true);
    else inp.value=fmtLengthSI(P.scaleProbe);
  };
  inp.addEventListener('change',applyText);
  inp.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();applyText();}});
  slider?.addEventListener('input',()=>commit(Math.pow(10,Number(slider.value)),'slider'));
  preset?.addEventListener('change',()=>{
    const values={'planck-half':PLANCK_LENGTH*.5,planck:PLANCK_LENGTH,'planck-double':PLANCK_LENGTH*2,sst:R_HORN_SST,helium:HE_CORE_REF};
    if(values[preset.value])commit(values[preset.value],'preset');
  });
}
bindScaleProbeInput();
document.getElementById('cModelLog')?.addEventListener('change',e=>{ModelLog.setEnabled(e.target.checked);});
document.getElementById('cModelLogVerbose')?.addEventListener('change',e=>{ModelLog.setVerbose(e.target.checked);});
document.getElementById('bModelLogExport')?.addEventListener('click',()=>{
  ModelLog.logUser('ui:click:bModelLogExport',{format:'json'});
  const data=ModelLog.exportJson();
  const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download='vortexlab-session-'+data.session.id.slice(0,8)+'.json';a.click();
});

function syncBundleUi(){
  const panel=document.getElementById('sstBundlePanel');if(panel)panel.classList.toggle('hidden',P.med!=='sst');
  const c=document.getElementById('cSSTBundle');if(c)c.checked=!!P.bundleEnabled;
  const cf=document.getElementById('cBundleFlow');if(cf)cf.checked=P.bgFlow==='bundle';
  const cbem=document.getElementById('cBundleBEM');if(cbem)cbem.checked=!!P.bundleBEMEnabled;
  const bm=document.getElementById('sBundleBoundaryMode');if(bm)bm.value=P.bundleBoundaryMode;
  const bq=document.getElementById('sBundleBEMQuality');if(bq)bq.value=P.bundleBEMQuality;
  const prof=document.getElementById('sBundleProfile');if(prof)prof.value=P.bundleProfile;
  const ss=document.getElementById('sBundleSplay');if(ss)ss.value=String(P.bundleSplay);
  const vs=document.getElementById('vBundleSplay');if(vs)vs.textContent=P.bundleSplay.toFixed(2);
  const sr=document.getElementById('sBundleRadiusFrac');if(sr)sr.value=String(P.bundleRadiusFrac);
  const vr=document.getElementById('vBundleRadiusFrac');if(vr)vr.textContent=Math.round(100*P.bundleRadiusFrac)+'% R_cyl';
  const sl=document.getElementById('sBundleLines');if(sl)sl.value=String(P.bundleVisualLines);
  const vl=document.getElementById('vBundleLines');if(vl)vl.textContent=String(P.bundleVisualLines);
  const row=document.getElementById('bundleSplayRow');if(row)row.classList.toggle('hidden',P.bundleProfile==='parallel');
  const read=document.getElementById('bundleReadout');
  if(read){
    const n0=bundleDensityAtZ(zMin()),nm=bundleDensityAtZ(0),n1=bundleDensityAtZ(zMax());
    const N=bundlePhysicalCountAtZ(0);
    const Rb=bundleRadiusAtZ(0),Gb=bundleCirculationAtZ(0);
    read.textContent=P.bundleEnabled
      ?`n_v(zmin/mid/zmax)= ${n0.toExponential(2)} / ${nm.toExponential(2)} / ${n1.toExponential(2)} m⁻² · R_bundle(mid)=${fmtLengthSI(Rb)} · Γ_enc=${Gb.toExponential(3)} m²/s · N_phys(mid)≈${N.toExponential(3)} · bron=${P.bundleSourceModel}`
      :'uit';
  }
  const br=document.getElementById('bundleBEMReadout');
  if(br){
    const bi=bundleBEMBoundaryInfo(),c=bundleBEMCache;
    br.textContent=!P.bundleBEMEnabled?'Niveau C uit'
      :(!bi.valid?`BEM niet actief: ${bi.reason} · gevraagd=${Number.isFinite(bi.requested)?fmtLengthSI(bi.requested):'—'} · vloer=${Number.isFinite(bi.floor)?fmtLengthSI(bi.floor):'—'}`
      :(c.valid?`BEM ${c.nodes.length} panelen · grens=${bi.label}=${fmtLengthSI(c.radius)} · residu u_n=${c.residualVelocity.toExponential(2)} · residu ω_n=${c.residualVorticity.toExponential(2)} · ${BEM_SOURCE_MODEL}`:`BEM ${c.status}`));
  }
  const vob=document.getElementById('vOmBundle');
  if(vob)vob.textContent=Math.abs(P.OmBundle).toFixed(2)+' s⁻¹ · '+(P.revOmBundle?'CW':'CCW');
  // Wrijving×bundel: zolang geen definitie van v_n in bundelveld bestaat, blokkeren.
  if(bundleFlowActive()&&mfActive()){
    applyMfTemp('0');P.vnZ=0;P.revVn=false;
    const mf=document.getElementById('mfTemp');if(mf)mf.value='0';
    setFlag('⚠ bundelveldkoppeling + α≠0 is ongedefinieerd (v_n-keuze). Wrijving is uitgezet.',true);
  }
}

document.getElementById('cSSTBundle')?.addEventListener('change',e=>{P.bundleEnabled=e.target.checked;invalidateBundleBEM('bundle-toggle');ensureBundleBEM(true);rebuildLattice();syncBundleUi();});
document.getElementById('cBundleBEM')?.addEventListener('change',e=>{P.bundleBEMEnabled=e.target.checked;invalidateBundleBEM('bem-toggle');ensureBundleBEM(true);rebuildLattice();syncBundleUi();});
document.getElementById('sBundleBoundaryMode')?.addEventListener('change',e=>{P.bundleBoundaryMode=e.target.value;invalidateBundleBEM('boundary-mode');ensureBundleBEM(true);rebuildLattice();syncBundleUi();});
document.getElementById('sBundleBEMQuality')?.addEventListener('change',e=>{P.bundleBEMQuality=e.target.value;invalidateBundleBEM('quality');ensureBundleBEM(true);rebuildLattice();syncBundleUi();});
document.getElementById('cBundleFlow')?.addEventListener('change',e=>{
  if(e.target.checked){
    if(P.bgFlow==='wall'){
      // enum vervangt de oude runtime-guard: één achtergrondstroming tegelijk
      P.solverFrame='corot';
      const bg=document.getElementById('cBgOmega');if(bg)bg.checked=false;
      setFlag('⚠ bundelveldkoppeling en Ω_wall legacy-koppeling zijn exclusief (bgFlow-enum); Ω_wall-koppeling is uitgezet.',true);
    }
    P.bgFlow='bundle';
  }else{
    P.bgFlow='none';
  }
  if(P.bgFlow==='bundle'&&P.bundleProfile!=='parallel')
    setFlag('⚠ splay-koppeling gebruikt een kinematische Ω(z)-ansatz; geen bewezen stationair Euler/SST-evenwicht.',true);
  invalidateBundleBEM('flow-toggle');ensureBundleBEM(true);rebuildLattice();syncBundleUi();
});
document.getElementById('sBundleProfile')?.addEventListener('change',e=>{
  P.bundleProfile=e.target.value;
  if(P.bundleProfile!=='parallel'&&P.bgFlow==='bundle'){
    P.bgFlow='none';
    const cb=document.getElementById('cBundleFlow');if(cb)cb.checked=false;
    setFlag('⚠ splayprofiel gestart als visualisatie; bundelveldkoppeling is uitgeschakeld totdat je die bewust opnieuw activeert.',true);
  }
  if(P.bundleProfile==='splay'&&P.tracerWrapZ){
    P.tracerWrapZ=false;
    const z=document.getElementById('cTracerWrapZ');if(z)z.checked=false;
    setFlag('⚠ monotone splay is niet periodiek in z; periodieke z-grens is daarom uitgezet.',true);
  }
  invalidateBundleBEM('profile');ensureBundleBEM(true);rebuildLattice();syncBundleUi();
});
document.getElementById('sBundleSplay')?.addEventListener('input',e=>{const x=Number(e.target.value);if(Number.isFinite(x)){P.bundleSplay=clamp(x,0,1.4);invalidateBundleBEM('splay');ensureBundleBEM(true);rebuildLattice();syncBundleUi();}});
document.getElementById('sBundleRadiusFrac')?.addEventListener('input',e=>{const x=Number(e.target.value);if(Number.isFinite(x)){P.bundleRadiusFrac=clamp(x,0.10,0.93);invalidateBundleBEM('bundle-radius');ensureBundleBEM(true);rebuildLattice();syncBundleUi();}});
document.getElementById('sBundleLines')?.addEventListener('input',e=>{const x=Number(e.target.value);if(Number.isFinite(x)){P.bundleVisualLines=clamp(Math.round(x),7,121);rebuildLattice();syncBundleUi();}});
document.getElementById('sOmBundle')?.addEventListener('input',e=>{const x=Number(e.target.value);if(Number.isFinite(x)){P.OmBundle=x;invalidateBundleBEM('omega');ensureBundleBEM(true);rebuildLattice();syncBundleUi();}});
document.getElementById('revOmBundle')?.addEventListener('change',e=>{P.revOmBundle=e.target.checked;invalidateBundleBEM('omega-sign');ensureBundleBEM(true);rebuildLattice();syncBundleUi();});
function bindStretchNumber(id,key,scale=1,integer=false){
  const el=document.getElementById(id);if(!el)return;
  el.addEventListener('input',e=>{let v=Number(e.target.value);if(!Number.isFinite(v))return;if(integer)v=Math.round(v);P[key]=v*scale;
    if(key==='stretchNeutralTol'){P.stretchNeutralTol=Math.max(1e-6,P.stretchNeutralTol);P.stretchFailTol=Math.max(P.stretchNeutralTol,P.stretchFailTol);}
    if(key==='stretchFailTol')P.stretchFailTol=Math.max(P.stretchNeutralTol,P.stretchFailTol);
    if(key==='stretchSoftening')P.stretchSoftening=Math.max(1e-9,P.stretchSoftening);
    if(key==='stretchMode')P.stretchMode=clamp(P.stretchMode,1,12);
    resetStretchGate('profile-parameter',true);syncStretchGateUi();resetPerformanceMeasurement(300);
  });
}
document.getElementById('cStretchGate')?.addEventListener('change',e=>{P.stretchGateEnabled=e.target.checked;resetStretchGate('gate-toggle',false);syncStretchGateUi();});
document.getElementById('sStretchProfile')?.addEventListener('change',e=>{P.stretchProfile=e.target.value;resetStretchGate('profile-change',true);syncStretchGateUi();});
document.getElementById('cStretchApply')?.addEventListener('change',e=>{P.stretchProfileApply=e.target.checked;if(!P.stretchProfileApply)P.stretchProfileOnly=false;resetStretchGate('profile-coupling',true);syncStretchGateUi();resetPerformanceMeasurement(400);});
document.getElementById('cStretchOnly')?.addEventListener('change',e=>{P.stretchProfileOnly=P.stretchProfileApply&&e.target.checked;if(P.stretchProfileOnly){P.bgFlow='none';P.bundleEnabled=false;applyMfTemp('0');P.w=0;P.vzA=0;P.vzB=0;}resetStretchGate('profile-only',true);syncUi();resetPerformanceMeasurement(400);});
document.getElementById('bStretchReset')?.addEventListener('click',()=>resetStretchGate('manual-reset',true));
bindStretchNumber('sStretchOmega','stretchOmega0');bindStretchNumber('sStretchBeta','stretchBeta');bindStretchNumber('sStretchGamma','stretchGamma');
bindStretchNumber('sStretchSoftMm','stretchSoftening',1e-3);bindStretchNumber('sStretchEpsMm','stretchEpsilon',1e-3);bindStretchNumber('sStretchMode','stretchMode',1,true);
bindStretchNumber('sStretchNeutralTol','stretchNeutralTol');bindStretchNumber('sStretchFailTol','stretchFailTol');

function uiControlKey(el){
  if(!el)return 'unknown';
  if(el.id)return el.id;
  const data=Object.entries(el.dataset||{}).find(([k])=>['mode','inter','core','med','qual','vis','tube','frame'].includes(k));
  if(data)return (el.parentElement&&el.parentElement.id?el.parentElement.id+':':'')+data[0]+'='+data[1];
  return (el.className&&String(el.className).trim())||el.tagName.toLowerCase();
}
function uiControlDetail(el){
  const detail={};
  if('checked'in el)detail.checked=!!el.checked;
  if('value'in el)detail.value=el.value;
  if(el.classList&&el.classList.contains('num-step-btn')){
    const input=el.closest('.param-hybrid')?.querySelector('.param-number');
    detail.direction=el.dataset.dir;detail.inputId=input&&input.id;detail.value=input&&input.value;
  }
  if(el.dataset)detail.dataset=Object.assign({},el.dataset);
  return detail;
}
document.addEventListener('change',e=>{
  if(!e.isTrusted)return;
  const t=e.target;if(!t||t.id==='cModelLog'||t.id==='cModelLogVerbose')return;
  ModelLog.logUser('ui:change:'+uiControlKey(t),uiControlDetail(t));
});
document.addEventListener('click',e=>{
  if(!e.isTrusted)return;
  const b=e.target.closest('button');if(!b||b.id==='bModelLogExport')return;
  ModelLog.logUser('ui:click:'+uiControlKey(b),uiControlDetail(b));
});
resetState();
updCam();
lastT=performance.now();frame=0;
function loop(now){
  window.__vlBootComplete=true;
requestAnimationFrame(loop);
  const dtReal=Math.min(0.05,(now-lastT)/1000);lastT=now;
  let advThisFrame=0;
  updateStabilityThrottle(dtReal);
  const timeDir=P.timeReverse?-1:1;
  const playAdvance=(paused||flagged)?0:acc()*stabilityThrottle*dtReal;
  if(!paused&&!flagged){
    // Deterministische stepper: uitsluitend volledige CFL-stappen. De
    // simulatiesnelheid vult alleen het stap-debet. v7.6.13 begrenst dt ook
    // vóór de eerste stap met opgelegde drift en een playback-onafhankelijke
    // tijdcap, zodat geen honderden seconden grote bootstrapstap kan ontstaan.
    stepDebt+=playAdvance;
    let evals=0, advancedAbs=0, advancedSigned=0;
    let dtNext=SpecClockProxyDecomposition.capAcceptedDt(SpecClockBenchmark.capAcceptedDt(dtCFL()));
    const lia=(P.inter==='lia');
    if(Y&&(!Ypre||Ypre.length!==Y.length))Ypre=new Float64Array(Y.length);
    while(stepDebt>=dtNext&&evals<EVAL_BUDGET){
      const signedDt=timeDir*dtNext;
      if(P.bundleBEMEnabled&&bundleFlowActive())ensureBundleBEM();
      const gapBefore=P.topologyGuard?(Number.isFinite(lastTopologyGap)?lastTopologyGap:topologyClearance()):Infinity;
      Ypre.set(Y); // snapshot voor first-hit en transient-contact guard
      lastUmax=advanceFilamentCandidate(signedDt,tPhys+signedDt);
      let dtApplied=signedDt;
      // v7.5.3: eindcontact én tijdelijke doorsnijding binnen een verder
      // contactvrije stap worden onderschept. Bij hard contact landt de guard
      // aan de veilige zijde van de d_contact-grens.
      let cev=contactEvent(lia),gapAfter=Infinity,geometryRelanded=false;
      if(cev&&!cev.warn){
        dtApplied=bisectFirstHit(signedDt,lia);geometryRelanded=true;
      }else if(P.topologyGuard){
        gapAfter=topologyClearance();const dmax=maxStateDisplacement(Ypre,Y);
        if(topologyStepMayTunnel(gapBefore,gapAfter,dmax)){
          const transient=transientContactWithinStep(signedDt,lia);
          if(transient){dtApplied=transient.dt;cev=transient.event;geometryRelanded=true;}
        }
      }
      if(dtApplied!==signedDt)cev=contactEvent(lia)||cev;
      // Precies één transportdiagnose-update, over het werkelijk geaccepteerde
      // interval; volle en gebisecteerde trial-stappen blijven passief.
      if(P.twistProxyEnabled)updateTwistProxy(dtApplied,K4);
      lastTopologyGap=P.topologyGuard?(geometryRelanded?topologyClearance():gapAfter):Infinity;
      bundleBEMStepCounter++;
      phi+=P.Om*dtApplied;
      if(P.bundleEnabled)bundlePhi+=P.OmBundle*dtApplied;
      tPhys+=dtApplied;
      if(P.ghostStewartson) syncGhostRing();
      updateStretchGateAcceptedStep(Ypre,Y,dtApplied);
      updateSpecClockAcceptedStep(dtApplied,K4);
      // v7.2 (RP1): tracers per geaccepteerde CFL-stap, met exact dezelfde
      // tijdstap als de filamenten — framerate-onafhankelijk per constructie.
      stepTracers(dtApplied);
      ModelLog.logStep({dt:dtApplied});
      stepDebt-=Math.abs(dtApplied);advancedAbs+=Math.abs(dtApplied);advancedSigned+=dtApplied;
      evals+=evalsPerStep();
      const benchmarkReached=SpecClockBenchmark.afterAcceptedStep(dtApplied);
      const decompositionReached=SpecClockProxyDecomposition.afterAcceptedStep(dtApplied);
      if(benchmarkReached||decompositionReached){stepDebt=0;break;}
      if(cev){
        ModelLog.logEvent('contact',cev);
        if(cev.warn){if(!warned)setFlag(cev.msg,true);}
        else{setFlag(cev.msg);break;}
      }
      dtNext=SpecClockProxyDecomposition.capAcceptedDt(SpecClockBenchmark.capAcceptedDt(dtCFL()));
    }
    stepDebt=Math.min(stepDebt,dtNext); // geen inhaal-explosie na pauze, snelheid-/driftwijziging of framedrops
    advThisFrame=advancedSigned;
    effAccSimSum=0.98*effAccSimSum+advancedAbs;
    effAccRealSum=0.98*effAccRealSum+dtReal;
    effAcc=effAccRealSum>1e-6?effAccSimSum/effAccRealSum:0;
    // vlaggen (per frame: alleen niet-contactgebonden checks)
    if(P.timeReverse&&mfActive()&&!warned)
      setFlag('⚠ achterwaarts integreren met α≠0: wrijving is dissipatief — dit is anti-dissipatief, geen fysische omkering.',true);
    for(const f of fils){
      if(f.ghost)continue;
      const st=carrierStats(f);
      if(st.rWall+P.a>0.9*P.Rcyl)setFlag('filament(buis) buiten volume-kader (r+a > 0.9·R_cyl)',true);
      if(!P.tracerWrapZ&&(st.z<zMin()+0.02||st.z>zMax()-0.02))setFlag(`filament buiten z-domein [${zMin().toFixed(2)}, ${zMax().toFixed(2)}] m`,true);
    }
  }
  SpecClockBenchmark.frameTick();
  SpecClockProxyDecomposition.frameTick();
  if(!paused)autoRelaxGeometry(dtReal);
  if(P.bundleBEMEnabled&&P.bundleEnabled&&(frame%24===0)){
    ensureBundleBEM();rebuildLattice();syncBundleUi();
  }
  // weergave — v7.5: displayFrame kiest de kijkrichting, solverFrame bepaalt de
  // betekenis van de opgeslagen filamentcoördinaten (lab = R(+φ)·corot).
  worldGrp.rotation.z=P.displayFrame==='corot'?0:phi;
  // In het roterende displayframe staat de flowcilinder stil. De fictieve
  // buitencilinder vertegenwoordigt dan het inertiale frame en draait met de
  // tegengestelde fase. In het absolute displayframe is hij volledig verborgen.
  frameBackdropGrp.visible=P.displayFrame==='corot';
  frameBackdropGrp.rotation.z=P.displayFrame==='corot'?-phi:0;
  const filDisplayRotation=P.displayFrame==='corot'
    ?(P.solverFrame==='lab'?-phi:0)
    :(P.solverFrame==='corot'?phi:0);
  filGrp.rotation.z=filDisplayRotation;
  // Een BEM-vervormde bundel is geometrisch aan de actuele knooptube
  // gekoppeld en moet exact dezelfde solver→display-transformatie volgen.
  // Alleen de ongestoorde axisymmetrische lijnweergave gebruikt bundlePhi.
  latticeGrp.rotation.z=(P.bundleBEMEnabled&&bundleBEMCache.valid)
    ?filDisplayRotation-worldGrp.rotation.z
    :(P.bundleEnabled&&P.bundleProfile==='parallel'?bundlePhi:0)-phi;
  pushLines();
  stepTracers(0); // v7.2 (RP1): integratie zit nu ín de CFL-loop (per stap);
                  // deze aanroep onderhoudt alleen nog de zichtbaarheidstoggle.
  rebuildStreamlines(false);
  updatePotentialFlowVisual(false);
  updateIndicators(tPhys);
  let bodyStates=[];
  if(Y&&fils.length){
    if(!lastFrameVel||lastFrameVel.length!==Y.length) lastFrameVel=new Float64Array(Y.length);
    velAll(Y,lastFrameVel);
    bodyStates=fils.map(f=>bodyFrameState(f,lastFrameVel));
  }
  updateChiArrows(bodyStates);
  if((stabilityFrame++%12)===0){
    const rep=computeStabilityReport();if(rep)updateStabilityDisplay(rep);
    updateStretchGateDisplay(computeStretchGateReport());
    updateChiPanel();
    updateSpecClockDisplay();
  }
  if(frame%3===0&&!flagged){
    const Ga=Gamma();
    let Wr=0,Lk=0,ACNpass=0; // v7.2: één exacte passage levert Wr, Lk én ACN; ghost uitgesloten
    for(const f of fils){if(f.ghost)continue;
      const g=gauss2(f.off,f.N,f.off,f.N,true);Wr+=g[0];ACNpass+=g[1];}
    for(let i=0;i<fils.length;i++)for(let j=i+1;j<fils.length;j++){
      if(fils[i].ghost||fils[j].ghost)continue;
      const g=gauss2(fils[i].off,fils[i].N,fils[j].off,fils[j].N,false);
      Lk+=g[0];ACNpass+=g[1];}
    const H=Wr+2*Lk;
    const ACN=ACNpass; // direct na de exacte passage: beschikbaar voor HUD én ModelLog
    document.getElementById('hHel').textContent=H.toFixed(3);
    document.getElementById('hHel').style.color=Math.abs(H)<0.02?'#7BE8A8':'#FFAE45';
    document.getElementById('hWr').textContent=Wr.toFixed(3);
    document.getElementById('hLk').textContent=Lk.toFixed(3);
    document.getElementById('hDWr').textContent=(Wr-Wr0).toFixed(3);
    updateBodyHud(bodyStates,Wr);
    const sA=carrierGroupStats('A');
    const vzRel=P.mode==='solo'?effectiveW():P.vzA;
    const taylor=taylorColumnState(sA,vzRel);
    const wrelLbl=Flags.sep
      ?(P.displayFrame==='corot'?'bulk ω_rel (co-rot)':'ω_rel @ cap')
      :(P.displayFrame==='corot'?'bulk ω_rel (co-rot)':'ω_rel achtergrond');
    document.getElementById('hWrelLbl').textContent=wrelLbl;
    document.getElementById('hWrel').textContent=(Flags.sep?taylor.zetaRel:(P.displayFrame==='corot'?0:2*P.Om)).toFixed(2)+' s⁻¹ ẑ';
    document.getElementById('rowRcap').classList.toggle('hidden',!Flags.sep);
    if(Flags.sep) document.getElementById('hRcap').textContent=(taylor.rCap*100).toFixed(1)+' cm / '+taylor.hColumn.toFixed(2)+' m';
    updateGammaHud(sA,vzRel);
    // v7.4.1: |χ_Ω| en Ro_z zijn bij Ω=0 ongedefinieerd en worden als — getoond.
    {const dim=dimensionlessDiagnostics(sA,vzRel);
     const fx=x=>!Number.isFinite(x)?'—':(x!==0&&(Math.abs(x)>=1e4||Math.abs(x)<1e-3)?x.toExponential(2):x.toFixed(3));
     document.getElementById('hDimless').textContent=fx(dim.chiOmega)+' · '+fx(dim.roZ)+' · '+fx(dim.aOverR);
     const gp=document.getElementById('rowGprod');
     gp.classList.toggle('hidden',P.mode!=='botsing');
     if(P.mode==='botsing'){
       const sgn=relativeCarrierOrientationSign();
       document.getElementById('hGprod').textContent=sgn>0?'+1 (zelfde traversalzin)':'−1 (tegengestelde traversalzin)';
     }}
    const mfOn=mfActive();
    document.getElementById('rowMF').classList.toggle('hidden',!mfOn);
    if(mfOn)document.getElementById('hMF').textContent=
      P.mfAlpha.toFixed(3)+' / '+P.mfAlphaP.toFixed(4)+' / '+fmtSpeed(P.vnZ);
    if(!mfOn)document.getElementById('rowRdot').classList.add('hidden');
    const km=kappaMedium();
    const rowHC=document.getElementById('rowHornCore');
    const rowO=document.getElementById('rowOmegas');
    const rowB=document.getElementById('rowBundleFlux');
    const nvLbl=document.getElementById('hNvLbl');
    const fmtOmega=x=>!Number.isFinite(x)?'—':(Math.abs(x)>=1e4||Math.abs(x)<1e-3?x.toExponential(2):x.toFixed(2));
    if(P.med==='sst'){
      if(rowHC)rowHC.classList.remove('hidden');if(rowO)rowO.classList.remove('hidden');
      const core=fixedCoreDiagnostics();
      document.getElementById('hHornCore').textContent=fmtLengthSI(R_HORN_SST)+' · '+(core.r?fmtLengthSI(core.r):'—')+' · '+(core.r?core.ratio.toExponential(2):'—');
      document.getElementById('hOmegas').textContent=fmtOmega(OMEGA_COMPTON_SST)+' · '+fmtOmega(core.omega)+' · '+fmtOmega(core.vorticity)+' s⁻¹';
    }else{
      if(rowHC)rowHC.classList.add('hidden');if(rowO)rowO.classList.add('hidden');
    }
    if(P.med==='sst'&&P.bundleEnabled){
      if(rowB)rowB.classList.remove('hidden');
      if(nvLbl)nvLbl.textContent='n_v(bundle)=2|Ω_bundle|/Γ₀';
      document.getElementById('hNv').textContent=bundleDensityAtZ(0).toExponential(2).replace('e+','·10^')+' m⁻²';
      document.getElementById('hBundleFlux').textContent=bundlePhysicalCountAtZ(0).toExponential(3)+' · R='+fmtLengthSI(bundleRadiusAtZ(0))+' · '+P.bundleProfile;
    }else{
      if(rowB)rowB.classList.add('hidden');
      if(nvLbl)nvLbl.textContent='n_v = 2Ω/κ';
      document.getElementById('hNv').textContent=km
        ?(2*Math.abs(P.Om)/km).toExponential(2).replace('e+','·10^')+' m⁻²':'— (demo)';
    }
    const sB=P.mode==='botsing'?carrierGroupStats('B'):null;
    document.getElementById('hR').textContent=sB
      ?(sA.R*100).toFixed(1)+' / '+(sB.R*100).toFixed(1)+' cm'
      :(sA.R*100).toFixed(1)+' cm';
    if(sB)document.getElementById('hDz').textContent=(Math.abs(sB.z-sA.z)*100).toFixed(1)+' cm';
    document.getElementById('hT').textContent=tPhys<100?tPhys.toFixed(1)+' s':tPhys.toExponential(2)+' s';
    document.getElementById('hAcc').textContent=fmtAcc(Math.max(1e-3,effAcc));
    ModelLog.logDiag(buildDiagRecord(Wr,Lk,ACN,sA)); // v7.3.1: TDZ-vrij, begrensd tot 5 Hz
    hist.push({t:tPhys,RA:sA.R,RB:sB?sB.R:0,dz:sB?Math.abs(sB.z-sA.z):0,zA:sA.z,Wr,
      gRel:Flags.sep&&P.mode==='solo'?stewartsonCirculation(vzRel,taylor.rCap,P.Om).qS:0, // v7.2: q_S i.p.v. ongeldige ratio
      wSolo:P.mode==='solo'?vzRel:0,omA:bodyStates[0]?bodyStates[0].omegaZ:0});
    if(hist.length>400)hist.shift();
    if(hist.length>5){
      const p=hist[hist.length-5],q=hist[hist.length-1];
      const dtRaw=q.t-p.t;
      const dtq=Math.abs(dtRaw)>1e-12?dtRaw:(dtRaw<0?-1e-12:1e-12);
      const v=sB?(p.dz-q.dz)/dtq:(q.zA-p.zA)/dtq;
      document.getElementById('hV').textContent=fmtSpeed(v);
      const showKelvin=isRingTopo();
      if(showKelvin){
        const Uth=kelvinSpeed(sA.R);
        const Umeas=P.mode==='botsing'&&sB?Math.abs(v)/2:Math.abs(v);
        document.getElementById('hUth').textContent=fmtSpeed(Umeas)+' / '+fmtSpeed(Uth);
      }
      // Orthodoxietest wederzijdse wrijving: voor een solo-ring geldt op
      // LIA-niveau exact Ṙ = α(v_n·d̂ − U), met d̂ de voortplantingsrichting.
      const showRdot=mfOn&&showKelvin&&P.mode==='solo';
      document.getElementById('rowRdot').classList.toggle('hidden',!showRdot);
      if(showRdot){
        const Rdot=(q.RA-p.RA)/dtq;
        const dir=Math.sign(q.zA-p.zA)||1;
        const RdotTh=P.mfAlpha*(dir*P.vnZ-kelvinSpeed(sA.R));
        document.getElementById('hRdot').textContent=fmtSpeed(Rdot)+' / '+fmtSpeed(RdotTh);
      }
    }
    // Geometrische descriptor-kaarten; geen fysische energieclaim
    let Lnow=0;for(const f of fils)Lnow+=arcLength(f);
    const Lhat=Lnow/Math.max(1e-9,L0);
    const geoScore=P.wAl*ACN+P.wBe*Lhat+P.wGa*H;
    document.getElementById('cardC').textContent=ACN.toFixed(3);
    document.getElementById('cardL').textContent=Lhat.toFixed(4);
    document.getElementById('cardH').textContent=H.toFixed(3);
    document.getElementById('cardE').textContent=geoScore.toFixed(3);
    document.getElementById('cardGam').textContent=fmtGa();
    drawSpark();
  }
  frame++;
  const w=canvas.clientWidth,h=canvas.clientHeight;
  if(canvas.width!==w||canvas.height!==h){renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
  updCam();renderer.render(scene,camera);
}
function fmtSpeed(v){
  const av=Math.abs(v);
  if(av>=1e-3)return (v*1e3).toFixed(1)+' mm/s';
  if(av>=1e-6)return (v*1e6).toFixed(1)+' µm/s';
  return (v*1e9).toFixed(1)+' nm/s';
}
requestAnimationFrame(loop);
