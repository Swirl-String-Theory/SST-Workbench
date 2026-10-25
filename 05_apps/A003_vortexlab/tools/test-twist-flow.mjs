import assert from 'node:assert/strict';
import {readFileSync,openSync,readSync,closeSync} from 'node:fs';
import {spawn} from 'node:child_process';
import {setTimeout as delay} from 'node:timers/promises';
const html=readFileSync('apps/web/twist-flow/index.html','utf8');
const js=readFileSync('apps/web/twist-flow/twist-flow.js','utf8');
const css=readFileSync('apps/web/twist-flow/twist-flow.css','utf8');
const legacy=readFileSync('apps/web/index.html','utf8');
const native=readFileSync('apps/web/src/legacy/vortexlab-runtime.js','utf8');
const server=readFileSync('tools/serve.mjs','utf8');
const tests=[];
function check(name,fn){fn();tests.push(name);}
check('independent Twist HTML document',()=>assert.match(html,/<title>TwistKnot Flow Lab/));
check('no original VortexLab iframe',()=>{
  assert.doesNotMatch(html,/<iframe\b/i);
  assert.doesNotMatch(js,/(?:createElement\(['"]iframe|contentWindow|contentDocument|iframe\.src)/);
});
check('canonical control panel is stage sibling (the P2 regression)' ,()=>{
  assert.match(legacy,/<\/div>\s*<div id="ui-right">/);
  assert.match(legacy,/id="modeSeg"/);
  assert.match(legacy,/id="twistSelect"/);
});
check('full original body bootstrap: ui-right installed before scripts',()=>{
  assert.match(js,/source\.getElementById\('ui-right'\)/);
  assert.match(js,/Array\.from\(source\.body\.children\)/);
  assert.match(js,/legacyHost\.appendChild\(clone\)/);
  assert.match(js,/document\.body\.appendChild\(legacyHost\)/);
  assert.match(js,/missing=essential\.filter\(id=>!document\.getElementById\(id\)\)/);
  assert(js.indexOf('document.body.appendChild(legacyHost)')<js.indexOf('for(const url of scripts)'));
});
check('offscreen compatibility layout must not be display:none',()=>{
  assert.match(css,/#twistLegacyHost\{/);
  const rule=css.slice(css.indexOf('#twistLegacyHost{'),css.indexOf('}',css.indexOf('#twistLegacyHost{')));
  assert.match(rule,/visibility:hidden/);
  assert.doesNotMatch(rule,/display:none/);
});
check('independent canvas viewport' ,()=>assert.match(html,/id="engineMount"/));
check('legacy runtime compatibility host hidden',()=>assert.match(css,/#engineMount #stage > :not\(#c3d\)/));
check('migrated old panels hidden after runtime init',()=>{
  for(const id of ['vlUiShell','vlPreservedSources','vlTooltip'])
    assert(css.includes('body > #'+id),id+' not hidden');
});
check('runtime control access survives legacy sidebar migration',()=>{
  assert.match(js,/document\.getElementById\(id\)/);
  assert.match(native,/document\.body\.appendChild\(shell\)/);
});
check('shared original solver resource reuse',()=>{
  assert.match(js,/fetch\(sourceUrl/);
  assert.match(js,/document\.importNode\(stage,true\)/);
  assert.match(js,/src\/legacy\/vortexlab-runtime\.js/);
  assert.match(legacy,/\.\/src\/legacy\/vortexlab-runtime\.js/);
  assert.match(native,/function velocityCore\(/);
});
check('exact original script order',()=>assert.match(js,/for\(const url of scripts\)/));
check('solo filament hard requirement',()=>assert.match(js,/chooseSegment\('modeSeg','mode','solo'\)/));
check('A006 native twist catalog',()=>assert.match(js,/KNOT_5_2_N1024_ORIG/));
check('Biot-Savart and LIA shared modes',()=>{
  assert.match(js,/chooseSegment\('interSeg','inter','bs'\)/);
  assert.match(js,/chooseSegment\('interSeg','inter','lia'\)/);
});
check('topology guard and no auto-relax',()=>{
  assert.match(js,/checkbox\('cTopologyGuard',true\)/);
  assert.match(js,/checkbox\('cAutoRelax',false\)/);
});
check('passive tracers and independent streamlines',()=>{
  assert.match(js,/cTracers/);assert.match(js,/cStreamlines/);
  assert.match(js,/tracerBudgetInfo/);
});
check('numerical safety warning and native points diagnostics',()=>{
  assert.match(js,/fluidCoreQualification/);
  assert.match(js,/nativeResolutionInfo/);
  assert.match(js,/hT/);
});
check('all required legacy controls exist in canonical DOM',()=>{
  for(const id of ['stage','c3d','bPause','bReset','modeSeg','interSeg','twistSelect','nativeResolutionInfo','tracerBudgetInfo','cTopologyGuard','sA','sTracerCount','sStreamlineCount','cTracers','cStreamlines'])
    assert(legacy.includes(`id="${id}"`),`missing required control: ${id}`);
});
check('server has dedicated directory route',()=>assert.match(server,/info\.isDirectory\(\)/));
check('source catalog includes target',()=>{
  const fd=openSync('apps/web/data/twist_knot_data.js','r');const buffer=Buffer.alloc(8192);
  const bytes=readSync(fd,buffer,0,8192,0);closeSync(fd);
  assert.match(buffer.subarray(0,bytes).toString('utf8'),/KNOT_5_2_N1024_ORIG/);
});
const port=49083;
const proc=spawn(process.execPath,['tools/serve.mjs'],{env:{...process.env,PORT:String(port)},stdio:'ignore'});
try {
  let up=false;
  for(let i=0;i<50;i++){
    try{const r=await fetch(`http://127.0.0.1:${port}/twist-flow/`);if(r.ok){up=true;break;}}catch{}
    await delay(80);
  }
  assert(up,'standalone route did not start');
  const expected=[['/twist-flow/','text/html'],['/twist-flow/twist-flow.css','text/css'],['/twist-flow/twist-flow.js','text/javascript'],['/index.html','text/html'],['/styles/vortexlab.css','text/css'],['/src/legacy/vortexlab-runtime.js','text/javascript']];
  for(const [url,contentType] of expected){
    const r=await fetch(`http://127.0.0.1:${port}${url}`);
    assert.equal(r.status,200,url);assert(r.headers.get('content-type')?.startsWith(contentType),url);await r.body?.cancel();
  }
  tests.push('standalone URL and canonical shared assets respond 200');
  const r=await fetch(`http://127.0.0.1:${port}/twist-flow`,{redirect:'manual'});
  assert.equal(r.status,308);assert.equal(r.headers.get('location'),'/twist-flow/');
  tests.push('directory slash redirect');
  console.log(`PASS Twist Flow P3: ${tests.length} checks; independent UI, no iframe, source parity, routes, complete bootstrap DOM`);
}finally{proc.kill('SIGTERM');}
