import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const policy = require(path.join(root,'apps/web/src/legacy/native-resolution-policy.js'));
const xyz = require(path.join(root,'apps/web/src/legacy/xyz-import.js'));
let pass=0;
function eq(a,b,msg) {if (a!==b) throw new Error(`${msg}: received ${a}, expected ${b}`);console.log('PASS',msg);pass++;}
function circle(n,z=0) {return Array.from({length:n},(_,i)=>`${Math.cos(2*Math.PI*i/n)} ${Math.sin(2*Math.PI*i/n)} ${z}`).join('\n');}
const one=xyz.parseXyzText(circle(1024),'knot-1024.xyz');
eq(one.ok,true,'parse 1024 native XYZ vertices');
eq(one.entry.components[0].points.length/3,1024,'actual vertex buffer count');
one.entry.components[0].pointCount=288; // deliberately stale metadata: raw XYZ bytes win
eq(policy.nativeComponentPoints(one.entry,one.entry.components[0],0,'xyz'),1024,'raw XYZ wins over stale metadata');
const sampled=xyz.sampleXyzComponent(one.entry.components[0],1024,()=>{throw new Error('should not resample');});
eq(sampled.length/3,1024,'source points cloned without resample');
eq(sampled[0],one.entry.components[0].points[0],'original coordinate retained');
const multi=xyz.parseXyzText(circle(512)+'\n\n'+circle(1024,1),'two-component.xyz');
eq(multi.entry.componentCount,2,'mixed-N link import');
eq(policy.nativeComponentPoints(multi.entry,multi.entry.components[0],0,'xyz'),512,'component A gets native 512');
eq(policy.nativeComponentPoints(multi.entry,multi.entry.components[1],1,'xyz'),1024,'component B gets native 1024');
const a006={pointsPerComponent:[1024,2048]};
eq(policy.nativeComponentPoints(a006,{I:1,pointCount:1024},0,'twist'),1024,'A006 native 1024 from converted XYZ metadata');
eq(policy.nativeComponentPoints(a006,{I:2},1,'knotplot'),2048,'KnotPlot converted XYZ component count');
eq(policy.nativeComponentPoints(a006,{pointCount:1024},0,'ideal'),null,'ideal/Fourier quality mode unchanged');
eq(policy.effectiveTracerCount(5000,96),5000,'legacy low-N tracers unchanged');
eq(policy.effectiveTracerCount(5000,288),5000,'legacy N288 tracers unchanged');
eq(policy.effectiveTracerCount(5000,512),2812,'N512 tracer safety budget');
eq(policy.effectiveTracerCount(5000,1024),1406,'N1024 tracer safety budget');
eq(policy.effectiveTracerCount(5000,2048),703,'N2048 tracer safety budget');
eq(policy.effectiveTracerCount(5000,4096),351,'N4096 tracer safety budget');
eq(policy.effectiveTracerCount(250,2048),250,'lower user preference is respected');
eq(policy.effectiveTracerCount(0,4096),0,'benchmark visual isolation remains zero');
eq(policy.effectiveTracerCount(999999,96),20000,'normal low-N requested tracer max remains 20000');
console.log(`\n${pass} native-resolution and tracer-budget checks PASS`);
