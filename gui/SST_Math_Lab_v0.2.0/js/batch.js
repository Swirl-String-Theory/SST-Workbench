(function(){
const Lab=window.SSTLab;
async function analyzeFile(file,settings,withStability=false){
  const text=await file.text(),raw=Lab.IO.parseXYZ(text),points=Lab.Geometry.uniformResampleClosed(raw,settings.sampleCount),geom=Lab.Geometry.differentialGeometry(points),analysis=Lab.Diagnostics.analyzeGeometry(geom,settings),physics=Lab.Physics.finiteCoreAnalysis(geom,settings);
  let stability=null;if(withStability)stability=Lab.Physics.reducedStability(physics,settings);
  return{file:file.name,path:file.webkitRelativePath||file.name,rawPoints:raw.length,geom,analysis,physics,stability};
}
function row(result){return{
  file:result.path,raw_points:result.rawPoints,resampled_points:result.geom.n,physics_points:result.physics.pointsM.length,
  L_m:result.analysis.L,L_over_rc:result.analysis.L_over_rc,kappa_rc_max:result.analysis.stats.kappaMax*Lab.CONSTANTS.r_c,
  torsion_rc_max_abs:Math.max(Math.abs(result.analysis.stats.tauMin*Lab.CONSTANTS.r_c),Math.abs(result.analysis.stats.tauMax*Lab.CONSTANTS.r_c)),
  biot_speed_mean_m_s:result.physics.stats.speedMean,biot_speed_max_m_s:result.physics.stats.speedMax,
  pressure_max_Pa:result.physics.stats.pressureMax,max_growth_s_1:result.stability?result.stability.maxGrowth:NaN,
  positive_growth_modes:result.stability?result.stability.positiveCount:NaN
};}
function csv(rows){if(!rows.length)return"";const keys=Object.keys(rows[0]);return [keys.join(","),...rows.map(r=>keys.map(k=>String(r[k])).join(","))].join("\n");}
Lab.Batch={analyzeFile,row,csv};
})();
