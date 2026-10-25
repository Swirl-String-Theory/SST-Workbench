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
  const inputs=['knot','modeBs','modeLia','freeTranslation','guard','core','motionMedium','demoGamma','playbackSpeed','runMotionDemo',
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
    const sel=byId('twistSelect');
    return sel ? Array.from(sel.options).filter(o=>/^twist\|KNOT_/.test(o.value)) : [];
  }
  function selectKnot(value){
    if(!ready||!value.startsWith('twist|KNOT_')||!catalogEntries().some(x=>x.value===value))return;
    dispatch('twistSelect',value);
    updateReadouts();
  }
  async function injectSharedEngine(){
    // Opt in to P4's tracer+streamline visualization; original VortexLab stays unchanged.
    window.__vlTwistFlowOverlayParticles=true;
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
    if(!options.length)throw new Error('De A006-catalogus bevat geen losse KNOT-geometrieën.');
    const select=$('knot');select.replaceChildren();
    for(const option of options){
      const item=document.createElement('option');item.value=option.value;
      item.textContent=option.value.slice(6).replace(/^KNOT_/,'').replace(/_N(\d+)_ORIG$/,' · N$1').replace(/_ORIG$/,'')+' · A006';
      select.appendChild(item);
    }
    const preferred='twist|KNOT_5_2_N1024_ORIG';
    select.value=options.some(x=>x.value===preferred)?preferred:options[0].value;
    ready=true;
    // Explicitly select the twist seed. No dependency on a query parameter to index.html.
    selectKnot(select.value);
    enable(true);$('engineLoading').hidden=true;
    setSelected(['modeBs','modeLia'],'modeBs');
    $('freeTranslation').checked=!byId('cCenterLock')?.checked;
    $('guard').checked=!!byId('cTopologyGuard')?.checked;
    $('motionMedium').value='sst';
    $('demoGammaRow').hidden=true;
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
        details.textContent=`Geaccepteerde stappen: ${snap.acceptedSteps} · t=${current.toExponential(4)} s · `+
          `volgende Δt=${Number.isFinite(dt)?dt.toExponential(2):'ongeldig'} s · `+
          `Γ=${gam.toExponential(3)} m²/s · gevraagde klok ${speed.toPrecision(3)}×. `+
          (halted?'⛔ Integratie gestopt: '+snap.flag:
          paused?'Gepauzeerd: stroomlijnen worden ook zonder tijdstappen getekend.':
          stalled?'⚠ Geen geaccepteerde tijdstappen in 3 s. Controleer veiligheidsgate en CPU-belasting.':
          'De deeltjes bewegen alleen per geaccepteerde CFL-tijdstap.');
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
