/* TwistKnot Flow Lab P4 — independent controls, live step observability, overlay tracers and 3D viewport, shared A003 numerical runtime.
 * No iframe, no secondary copy of the solver. The legacy controls remain hidden
 * solely as a compatibility API until the physics engine is separated from the UI.
 */
'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const mount = $('engineMount');
  let ready=false, pollTimer=null, syncing=false;
  let lastObservedTime=null, lastAdvanceWall=performance.now();
  // Legacy runtime moves its controls into body-level docks during startup.
  const byId = id => document.getElementById(id);
  const textOf = id => byId(id)?.textContent?.trim() || '—';
  const dispatch = (id, value, type='change') => {
    const el=byId(id);
    if(!el) return false;
    if(el.type==='checkbox')el.checked=!!value;
    else el.value=String(value);
    el.dispatchEvent(new Event(type,{bubbles:true}));
    return true;
  };
  const click = id => {const el=byId(id);if(!el)return false;el.click();return true;};
  const chooseSegment = (group,key,value) => {
    const button=byId(group)?.querySelector(`[data-${key}="${value}"]`);
    if(!button)return false;
    if(!button.classList.contains('active'))button.click();
    return true;
  };
  const checkbox = (id,checked) => {
    const el=byId(id);
    if(!el)return false;
    if(el.checked!==!!checked)return dispatch(id,!!checked);
    return true;
  };
  const inputs=['knot','modeBs','modeLia','freeTranslation','guard','core','motionMedium','demoGamma','playbackSpeed','runMotionDemo','fastPreview',
    'displayParticles','displayStreamlines','displayKnot','density','lines','tube','reseed','play','reset'];
  const status=(message,mode='idle')=>{
    const el=$('engineStatus');el.textContent='● '+message;el.dataset.status=mode;
    el.style.color=mode==='ok'?'#7debd0':mode==='error'?'#ffc087':'#e6c38a';
  };
  const enable=value=>inputs.forEach(id=>{$(id).disabled=!value;});
  const setSelected=(ids,selected)=>ids.forEach(id=>$(id).classList.toggle('selected',id===selected));
  function warning(message){$('warning').textContent=message;$('warning').hidden=!message;}
  function applyFlow(which){
    if(!ready)return;
    // Unlike P3, a streamline overlay does not freeze/passivate tracer advection.
    checkbox('cTracers',which!=='displayKnot');
    checkbox('cStreamlines',which==='displayStreamlines');
    setSelected(['displayParticles','displayStreamlines','displayKnot'],which);
  }
  function catalogEntries(){
    // Every entry is a SINGLE closed knot. Multi-component links are excluded.
    // Source families retain their provenance; the shared solver does the loading.
    const out=[];
    const twist=byId('twistSelect');
    if(twist)for(const option of twist.options){
      if(/^twist\|KNOT_/.test(option.value))
        out.push({value:option.value,label:option.textContent+' · A006 twist',family:'twist'});
    }
    const knotplot=byId('knotplotSelect');
    if(knotplot)for(const group of knotplot.querySelectorAll('optgroup')){
      if(!/KNOTPLOT RELAXED KNOT CANDIDATES/i.test(group.label))continue;
      for(const option of group.querySelectorAll('option'))
        if(/^knotplot\|/.test(option.value))
          out.push({value:option.value,label:option.textContent+' · KnotPlot relaxed',family:'knotplot'});
    }
    const ideal=byId('knotSelect');
    if(ideal)for(const group of ideal.querySelectorAll('optgroup')){
      if(!/GILBERT IDEAL \/ TIGHT KNOPEN/i.test(group.label))continue;
      for(const option of group.querySelectorAll('option'))
        if(/^ideal\|/.test(option.value))
          out.push({value:option.value,label:option.textContent+' · ideal candidate',family:'ideal'});
    }
    return out;
  }
  function selectKnot(value){
    if(!ready||!catalogEntries().some(x=>x.value===value))return;
    const family=value.slice(0,value.indexOf('|'));
    const sourceSelector={twist:'twistSelect',knotplot:'knotplotSelect',ideal:'knotSelect'}[family];
    if(!sourceSelector||!dispatch(sourceSelector,value))return;
    lastObservedTime=null;
    applyInteractiveMotionPolicy(value);
    updateReadouts();
  }
  function currentVertexCount(){
    const snap=window.__vlTwistFlowDiagnostics?.();
    if(snap&&Number(snap.totalVertices)>0)return Number(snap.totalVertices);
    const info=textOf('nativeResolutionInfo');
    const m=info.match(/totaal\s+(\d+)/i);
    return m?Number(m[1]):0;
  }
  /** Catalog / name hint for native XYZ point count (A006 / KnotPlot / ideal). */
  function catalogNativeHint(value){
    const m=String(value||'').match(/N(\d{2,5})\b/i);
    return m?Number(m[1]):0;
  }
  /**
   * High-N XYZ families need the honest interactive demo path.
   * Prefer catalog metadata (family + N#### in id), not fragile live vertex counts.
   */
  function needsInteractiveDemoPath(value){
    const family=String(value||'').slice(0,String(value||'').indexOf('|'));
    if(family==='twist'||family==='knotplot')return true;
    const hint=catalogNativeHint(value);
    if(hint>288)return true;
    return currentVertexCount()>288;
  }
  /** Reuse the existing demo-medium + Γ path (no new forces). */
  function applyDemoMediumForMotion(){
    $('motionMedium').value='demo';
    $('demoGammaRow').hidden=false;
    if(!chooseSegment('medSeg','med','demo'))return false;
    const gamma=Number($('demoGamma').value);
    if(Number.isFinite(gamma)&&gamma>0)dispatch('sGa',gamma*1000,'input');
    return true;
  }
  /**
   * Honest interactive path for KnotPlot / A006 (and other high-N XYZ):
   * LIA + N192 preview + demo-Γ + tracers. No fake velocities.
   */
  function applyInteractiveMotionPolicy(selectedValue){
    if(!ready||window.__vlTwistFlowOverlayParticles!==true)return;
    // Prefer tube thickness from a_sim so menu↔render coupling is visible.
    checkbox('cShowTubeThickness',true);
    chooseSegment('visSeg','vis','tube');
    const value=selectedValue||$('knot')?.value||'';
    if(!needsInteractiveDemoPath(value)){
      // Low-N ideal/Gilbert: keep native resolution and medium; tube viz only.
      return;
    }
    chooseSegment('interSeg','inter','lia');
    applyDemoMediumForMotion();
    // Always rebuild at preview N when switching knots (even if preview was already on).
    window.__vlTwistFlowPreviewN=192;
    click('bReset');
    checkbox('cTracers',true);
    checkbox('cStreamlines',false);
    applyFlow('displayParticles');
    click('bResetParticles');
    $('playbackSpeed').value='2';
    dispatch('sAcc',2,'input');
    warning('⚠ Interactieve weergave: LIA + N192-preview + demo-Γ (niet gecertificeerd). SST-Γ en native Biot–Savart blijven te traag voor zichtbare realtime tracers/tijd; herstel native via de preview-knop.');
  }
  async function injectSharedEngine(){
    // Opt in to P4's tracer+streamline visualization; original VortexLab stays unchanged.
    window.__vlTwistFlowOverlayParticles=true;
    window.__vlTwistFlowPreviewN=0; // opt-in only: native geometry is the default
    // Fetch only the legacy CONTROL DOM. No index page is rendered or navigated to.
    // Run exactly the same script URLs as the canonical VortexLab route, in order.
    const sourceUrl=new URL('../index.html',document.baseURI);
    const response=await fetch(sourceUrl,{cache:'no-store'});
    if(!response.ok)throw new Error(`Legacy engine-document niet beschikbaar (HTTP ${response.status}).`);
    const source=new DOMParser().parseFromString(await response.text(),'text/html');
    const stage=source.getElementById('stage');
    const controls=source.getElementById('ui-right');
    if(!stage||!stage.querySelector('#c3d')||!controls)
      throw new Error('Legacy engine-document mist #stage, #c3d of #ui-right.');
    // P2 imported only #stage; nearly all original controls live in the BODY
    // sibling #ui-right, causing null dereferences during runtime bootstrap.
    // Install the COMPLETE non-script legacy body before loading ANY script.
    // Keep only #stage in the live Twist Flow viewport; the other nodes are
    // offscreen (not display:none, so legacy layout measurements still work).
    const scripts=Array.from(source.querySelectorAll('script[src]'),el=>new URL(el.getAttribute('src'),sourceUrl));
    if(!scripts.some(u=>u.pathname.endsWith('/src/legacy/vortexlab-runtime.js')))
      throw new Error('De gedeelde numerieke VortexLab-engine ontbreekt.');
    const legacyHost=document.createElement('div');
    legacyHost.id='twistLegacyHost';
    const mountedStage=document.importNode(stage,true);
    mountedStage.querySelectorAll('script').forEach(el=>el.remove());
    mount.replaceChildren(mountedStage);
    for(const node of Array.from(source.body.children)){
      if(node.id==='stage'||node.tagName==='SCRIPT')continue;
      const clone=document.importNode(node,true);
      clone.querySelectorAll('script').forEach(el=>el.remove());
      legacyHost.appendChild(clone);
    }
    document.body.appendChild(legacyHost);
    const essential=['ui-right','modeSeg','interSeg','twistSelect','bPause','bReset',
      'cTopologyGuard','sA','sTracerCount','sStreamlineCount'];
    const missing=essential.filter(id=>!document.getElementById(id));
    if(missing.length)throw new Error('Legacy control-contract ontbreekt: '+missing.join(', '));
    for(const url of scripts){
      await new Promise((resolve,reject)=>{
        const script=document.createElement('script');
        script.src=url.href;
        script.async=false;
        script.onload=resolve;
        script.onerror=()=>reject(new Error('Benodigde bron kon niet worden geladen: '+url.pathname));
        document.body.appendChild(script);
      });
    }
    for(let retry=0;retry<400;retry++){
      if(window.__vlBootComplete===true)return;
      await new Promise(resolve=>setTimeout(resolve,100));
    }
    throw new Error('De gedeelde VortexLab-engine heeft de opstart niet bevestigd.');
  }
  function initialize(){
    if(!window.__vlBootComplete||!byId('bPause')||!byId('twistSelect'))
      throw new Error('VortexLab-controls zijn onvolledig na engine-opstart.');
    // Legacy P2 initializes playing. Pause before changing the chosen geometry.
    if(byId('bPause')?.textContent?.trim()==='Pauzeer')click('bPause');
    if(!chooseSegment('modeSeg','mode','solo'))throw new Error('Solo-mode niet beschikbaar.');
    checkbox('cAutoRelax',false);
    checkbox('cPotentialFlow',false);
    checkbox('cCoreFlowLock',false);
    checkbox('cTopologyGuard',true);
    checkbox('cCenterLock',false);
    checkbox('cBgOmega',false);
    for(const id of ['cDvSeparatrix','cDvColumn','cDvCaps','cDvStewartson']) checkbox(id,false);
    if(!chooseSegment('interSeg','inter','bs'))throw new Error('Biot–Savart-mode niet beschikbaar.');
    chooseSegment('visSeg','vis','tube');
    dispatch('sTracerCount',Number($('density').value),'input');
    dispatch('sStreamlineCount',Number($('lines').value),'input');
    dispatch('sAcc',Number($('playbackSpeed').value),'input');
    checkbox('cTracers',true);checkbox('cStreamlines',false);
    const options=catalogEntries();
    if(!options.length)throw new Error('Geen enkelvoudige knotgeometrieën in de beschikbare A006/KnotPlot/ideal-catalogi.');
    const select=$('knot');select.replaceChildren();
    let currentFamily=null,currentGroup=null;
    for(const option of options){
      if(option.family!==currentFamily){
        currentFamily=option.family;
        currentGroup=document.createElement('optgroup');
        currentGroup.label={twist:'A006 twistfamilie',knotplot:'KnotPlot relaxed-kandidaten',ideal:'Gilbert ideal/tight-knopen'}[option.family]||option.family;
        select.appendChild(currentGroup);
      }
      const item=document.createElement('option');item.value=option.value;
      item.textContent=option.label;
      currentGroup.appendChild(item);
    }
    const preferred='twist|KNOT_5_2_N1024_ORIG';
    select.value=options.some(x=>x.value===preferred)?preferred:options[0].value;
    // Default UI intent before selection; high-N policy may switch to demo-Γ.
    $('motionMedium').value='sst';
    $('demoGammaRow').hidden=true;
    ready=true;
    // Explicitly select the twist seed. No dependency on a query parameter to index.html.
    selectKnot(select.value);
    enable(true);$('engineLoading').hidden=true;
    setSelected(['modeBs','modeLia'],byId('interSeg')?.querySelector('[data-inter].active')?.dataset.inter==='bs'?'modeBs':'modeLia');
    $('freeTranslation').checked=!byId('cCenterLock')?.checked;
    $('guard').checked=!!byId('cTopologyGuard')?.checked;
    // Sync medium UI from what applyInteractiveMotionPolicy chose (do not force SST afterward).
    const demoActive=$('motionMedium').value==='demo'||byId('medSeg')?.querySelector('[data-med].active')?.dataset.med==='demo';
    $('motionMedium').value=demoActive?'demo':'sst';
    $('demoGammaRow').hidden=!demoActive;
    $('tube').checked=true;
    chooseSegment('visSeg','vis','tube');
    checkbox('cShowTubeThickness',true);
    $('fastPreview').textContent=Number(window.__vlTwistFlowPreviewN||0)>0
      ?'↩ Native bronresolutie herstellen'
      :'▶ Snelle bewegingspreview · N192 (niet gecertificeerd)';
    const a=Number(byId('sA')?.value)*1e-3;
    if(a>0&&Number.isFinite(a))$('core').value=String(a);
    status('Twist Flow · gedeelde engine gereed','ok');
    updateReadouts();
    pollTimer=setInterval(updateReadouts,500);
  }
  function updateReadouts(){
    if(!ready||syncing)return;
    syncing=true;
    try {
      $('metricTime').textContent=textOf('hT');
      $('metricLength').textContent=textOf('cardL');
      $('metricGamma').textContent=textOf('cardGam');
      $('metricGap').textContent=textOf('hGa');
      const t=textOf('nativeResolutionInfo');
      const count=t.match(/totaal\s+(\d+)/i);
      $('metricN').textContent=count?Number(count[1]).toLocaleString('nl-NL'):'—';
      $('seedStatus').textContent=t;
      $('tracerStatus').textContent=textOf('tracerBudgetInfo');
      $('fastPreview').textContent=Number(window.__vlTwistFlowPreviewN||0)>0
        ?'↩ Native bronresolutie herstellen'
        :'▶ Snelle bewegingspreview · N192 (niet gecertificeerd)';
      const qual=textOf('fluidCoreQualification');
      $('coreStatus').textContent=qual;
      $('coreStatus').classList.toggle('warn',/niet|floor|sub.precision|warning|ongeldig|onopgelost/i.test(qual));
      const flag=byId('flag');
      const message=flag?.style.display==='none'?'':flag?.textContent?.trim()||'';
      if(message)warning(message);
      else if($('warning').dataset.localError!=='true')warning('');
      const snap=window.__vlTwistFlowDiagnostics?.();
      const paused=snap? snap.paused : byId('bPause')?.textContent?.trim()==='Hervat';
      const halted=!!snap?.halted;
      $('play').textContent=paused?'▶ Start':'⏸ Pauze';
      if(halted)status('Twist Flow · VEILIGHEIDSSTOP','halted');
      else status(paused?'Twist Flow · gepauzeerd':'Twist Flow · actief','ok');
      if(snap){
        const current=Number(snap.timeSeconds);
        const now=performance.now();
        if(lastObservedTime===null || current!==lastObservedTime){
          lastObservedTime=current;
          lastAdvanceWall=now;
        }
        const stalled=!paused&&!halted&&now-lastAdvanceWall>3000;
        const details=$('motionDiagnostics');
        details.classList.toggle('stalled',stalled);
        details.classList.toggle('halted',halted);
        const dt=Number(snap.nextStepSeconds);
        const gam=Number(snap.gamma);
        const speed=Number(snap.acceleration);
        const knotTravel=Number(snap.referenceTravelMeters||0);
        const knotNet=Number(snap.referenceNetDisplacementMeters||0);
        const knotStep=Number(snap.lastStepMaximumDisplacementMeters||0);
        const actualSpeed=Number(snap.effectivePlaybackSpeed||0);
        const motionDetail=`Punt 0 afgelegd: ${knotTravel.toExponential(3)} m · netto ${knotNet.toExponential(3)} m · `+
          `maximale stapverplaatsing ${knotStep.toExponential(3)} m · `+
          `gemeten simulatietempo ${actualSpeed.toExponential(2)}×. `;
        const subMicro=Number.isFinite(dt)&&dt>0&&dt<1e-6;
        const needed=Number.isFinite(dt)&&dt>0?1/dt:NaN;
        const tinyStepNote=subMicro
          ?` · MICROSTAP TOEGESTAAN: 1 s simulatietijd vereist ongeveer ${Number.isFinite(needed)?needed.toExponential(2):'>1e308'} stappen; realtime niet gegarandeerd.`
          :'';
        details.textContent=`Geaccepteerde stappen: ${snap.acceptedSteps} · t=${current.toExponential(4)} s · `+
          `volgende Δt=${Number.isFinite(dt)?dt.toExponential(2):'ongeldig'} s · `+
          `Γ=${gam.toExponential(3)} m²/s · gevraagde klok ${speed.toPrecision(3)}×. `+
          tinyStepNote+motionDetail+
          (halted?'⛔ Integratie gestopt: '+snap.flag:
          paused?'Gepauzeerd: stroomlijnen worden ook zonder tijdstappen getekend.':
          stalled?'⚠ Geen geaccepteerde tijdstappen in 3 s. Controleer veiligheidsgate en CPU-belasting.':
          snap.acceptedSteps>0&&knotTravel===0?'⚠ De klok loopt, maar punt 0 is numeriek niet verplaatst. Onderzoek afronding en kernmodel.':
          snap.acceptedSteps>0&&knotTravel<1e-5?(
            (snap.medium==='sst'&&Math.abs(snap.gamma)<1e-6)
              ?'⚠ Kelvin-snelheid (SST Γ) is te klein t.o.v. de knoopschaal; kies demo-Γ / N192-preview of hogere playback — geen gefingeerde filament-snelheid.'
              :'⚠ Er worden echte knoopstappen geaccepteerd, maar de verplaatsing is klein en mogelijk niet zichtbaar bij deze zoom.'
          ):
          'Verplaatsingen zijn werkelijk uit de filamenttoestand gemeten, niet uit de weergave.');
        if(halted)warning('⛔ Veiligheidsstop uit gedeelde engine: '+snap.flag);
      }
      setSelected(['modeBs','modeLia'],byId('interSeg')?.querySelector('[data-inter].active')?.dataset.inter==='bs'?'modeBs':'modeLia');
    }finally{syncing=false;}
  }
  $('knot').addEventListener('change',e=>selectKnot(e.target.value));
  $('modeBs').addEventListener('click',()=>{chooseSegment('interSeg','inter','bs');updateReadouts();});
  $('modeLia').addEventListener('click',()=>{chooseSegment('interSeg','inter','lia');updateReadouts();});
  $('freeTranslation').addEventListener('change',e=>checkbox('cCenterLock',!e.target.checked));
  $('guard').addEventListener('change',e=>{if(!e.target.checked){e.target.checked=true;return;}checkbox('cTopologyGuard',true);});
  $('playbackSpeed').addEventListener('change',e=>{
    dispatch('sAcc',Number(e.target.value),'input');
    updateReadouts();
  });
  $('motionMedium').addEventListener('change',e=>{
    const demo=e.target.value==='demo';
    if(!chooseSegment('medSeg','med',demo?'demo':'sst')){
      warning('Mediumselectie niet beschikbaar in de gedeelde engine.');return;
    }
    // The existing model owns Γ. Do not implement or multiply any new force.
    $('demoGammaRow').hidden=!demo;
    if(demo){
      const gamma=Number($('demoGamma').value);
      if(Number.isFinite(gamma)&&gamma>0)dispatch('sGa',gamma*1000,'input');
    }
    // Reset of shared engine may change playback parameters.
    dispatch('sAcc',Number($('playbackSpeed').value),'input');
    lastObservedTime=null;
    updateReadouts();
  });
  $('runMotionDemo').addEventListener('click',()=>{
    // Explicit non-SST preview: reuse original demo-medium and LIA solver,
    // never multiply particle coordinates or simulate movement in the renderer.
    if(byId('bPause')?.textContent?.trim()==='Pauzeer')click('bPause');
    $('motionMedium').value='demo';
    $('motionMedium').dispatchEvent(new Event('change',{bubbles:true}));
    if(!chooseSegment('interSeg','inter','lia')){
      warning('LIA niet beschikbaar in gedeelde engine.');return;
    }
    $('playbackSpeed').value='2';
    dispatch('sAcc',2,'input');
    applyFlow('displayStreamlines');
    lastObservedTime=null;
    if(byId('bPause')?.textContent?.trim()==='Hervat')click('bPause');
    updateReadouts();
  });
  $('fastPreview').addEventListener('click',()=>{
    // Optional lower-N *dynamic* preview. A006/KnotPlot source files are not edited.
    // This may change the resolved knot topology; NEVER use as a qualified run.
    const activate=!(Number(window.__vlTwistFlowPreviewN||0)>0);
    if(byId('bPause')?.textContent?.trim()==='Pauzeer')click('bPause');
    window.__vlTwistFlowPreviewN=activate?192:0;
    click('bReset'); // explicit geometry rebuild and tracer reinitialization
    if(activate){
      $('runMotionDemo').click();
      warning('⚠ Snelle N192-preview: knoopklasse en fysica niet gevalideerd; native bronpunten blijven intact.');
    }
    lastObservedTime=null;
    updateReadouts();
  });
  $('demoGamma').addEventListener('change',e=>{
    const gamma=Number(e.target.value);
    if(!(Number.isFinite(gamma)&&gamma>=2e-4&&gamma<=1)){
      warning('Ongeldige demo-circulatie: kies 2×10⁻⁴ ≤ Γ ≤ 1 m²/s.');return;
    }
    if($('motionMedium').value==='demo')dispatch('sGa',gamma*1000,'input');
    updateReadouts();
  });
  $('core').addEventListener('change',e=>{
    const value=Number(e.target.value);
    if(!Number.isFinite(value)||value<=0||value>0.07){warning('Ongeldige kernstraal: kies 0 < a ≤ 0,07 m.');$('warning').dataset.localError='true';return;}
    $('warning').dataset.localError='false';
    dispatch('sA',value*1000,'input');
    const applied=Number(byId('sA')?.value)*1e-3;
    if(Number.isFinite(applied)&&applied>0)e.target.value=String(applied);
    updateReadouts();
  });
  for(const flow of ['displayParticles','displayStreamlines','displayKnot'])
    $(flow).addEventListener('click',()=>applyFlow(flow));
  $('density').addEventListener('input',e=>{$('densityOut').textContent=e.target.value;dispatch('sTracerCount',e.target.value,'input');});
  $('lines').addEventListener('input',e=>{$('linesOut').textContent=e.target.value;dispatch('sStreamlineCount',e.target.value,'input');});
  $('tube').addEventListener('change',e=>chooseSegment('visSeg','vis',e.target.checked?'tube':'line'));
  $('reseed').addEventListener('click',()=>click('bResetParticles'));
  $('play').addEventListener('click',()=>{click('bPause');updateReadouts();});
  $('reset').addEventListener('click',()=>{click('bReset');updateReadouts();});
  (async()=>{
    try{status('Engine laden');await injectSharedEngine();initialize();}
    catch(error){enable(false);status('Niet gestart','error');warning('Twist Flow kon niet starten: '+error.message);$('engineLoading').textContent='Start mislukt: '+error.message;console.error(error);}
  })();
  window.addEventListener('beforeunload',()=>{if(pollTimer)clearInterval(pollTimer)});
})();
