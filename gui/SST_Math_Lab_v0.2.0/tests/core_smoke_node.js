// Optional developer smoke test. Requires Node.js, but no third-party JS packages.
global.window=global;
const fs=require('fs'),vm=require('vm'),path=require('path');
const root=path.resolve(__dirname,'..'),js=path.join(root,'js');
for(const f of ['constants.js','vector.js','geometry.js','diagnostics.js','physics.js'])vm.runInThisContext(fs.readFileSync(path.join(js,f),'utf8'),{filename:f});
const C=SSTLab.CONSTANTS;
const settings={physicalScale:C.r_c,physicsSamples:128,biotCoreFraction:1,circulationMultiplier:1,pressureProbeFraction:.25,velocityModel:'curvature',curvatureExponent:.5,speedMultiplier:1,kelvinCoreFraction:.1,kelvinModes:12,kaCutoff:.3};
const pts=SSTLab.Geometry.generateTrefoil(2.5,1,1200),geom=SSTLab.Geometry.differentialGeometry(pts),analysis=SSTLab.Diagnostics.analyzeGeometry(geom,settings),physics=SSTLab.Physics.finiteCoreAnalysis(geom,settings);
const checks=[
  ['L/r_c',Math.abs(analysis.L_over_rc-36.93933)<5e-4,analysis.L_over_rc],
  ['max kappa r_c',Math.abs(analysis.stats.kappaMax*C.r_c-.52801)<5e-4,analysis.stats.kappaMax*C.r_c],
  ['mean Biot speed',Math.abs(physics.stats.speedMean-7.7149e5)/7.7149e5<.01,physics.stats.speedMean],
  ['relative divergence',physics.stats.divergenceRelativeRms<.01,physics.stats.divergenceRelativeRms]
];
const circle=[];for(let i=0;i<512;i++){const t=2*Math.PI*i/512;circle.push([10*Math.cos(t),10*Math.sin(t),0]);}
const cg=SSTLab.Geometry.differentialGeometry(circle),cp=SSTLab.Physics.finiteCoreAnalysis(cg,settings),leak=(cp.stats.tangentRms+cp.stats.normalRms)/Math.max(cp.stats.binormalRms,1e-300);
checks.push(['circle transverse leakage',leak<1e-3,leak]);
for(const [name,ok,value] of checks)console.log(`${ok?'PASS':'FAIL'}  ${name}: ${value}`);
if(checks.some(x=>!x[1]))process.exit(1);
