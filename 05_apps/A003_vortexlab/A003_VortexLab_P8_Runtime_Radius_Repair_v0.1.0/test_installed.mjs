import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
const root=path.resolve(process.argv[2]||'.');
const manifest=JSON.parse(fs.readFileSync(new URL('./PATCH_MANIFEST.json',import.meta.url),'utf8'));
let count=0;
for(const row of manifest.files){
 const p=path.join(root,row.path);
 assert.equal(createHash('sha256').update(fs.readFileSync(p)).digest('hex'),row.patched_sha256,`${row.path} hash`);count++;
}
const runtime=fs.readFileSync(path.join(root,'apps/web/src/legacy/vortexlab-runtime.js'),'utf8');
const overlay=fs.readFileSync(path.join(root,'apps/web/twist-flow/twist-flow.js'),'utf8');
const html=fs.readFileSync(path.join(root,'apps/web/twist-flow/index.html'),'utf8');
const checks=[
 [/const step=Number\.isFinite\(explicitStep\)/,runtime,'small step-any fallback'],
 [/window\.__vlHudDiagnosticCache/,runtime,'HUD cache'],
 [/hudGaussCadence/,runtime,'visual-only Gauss diagnostic cadence'],
 [/window\.__vlNumericalTubeDisplayRequested/,runtime,'numerical tube switch'],
 [/console\.error\('\[VortexLab\] Buisweergave mislukt/,runtime,'visible tube render failure'],
 [/updateCoreRadiusLimit\(true\)/,runtime,'geometry core bound kept'],
 [/topologyStepMayTunnel/,runtime,'topology guard kept'],
 [/safeStep\(value/,runtime,'precision safety kept'],
 [/id="useNumericalTubeRadius"/,html,'explicit numerical visual checkbox'],
 [/Numerieke/i,overlay,'numeric display readout'],
];
for(const [pat,s,label] of checks){assert.match(s,pat,label);count++;}
console.log(`PASS P8 targeted structural assertions: ${count}`);
