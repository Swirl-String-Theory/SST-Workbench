(function(){
const Lab=window.SSTLab;
function parseXYZ(text){
  const rows=[];for(const raw of text.split(/\r?\n/)){const line=raw.trim();if(!line||line.startsWith("#")||line.startsWith("//"))continue;const toks=line.replace(/[;,]/g," ").split(/\s+/),nums=toks.map(Number);if(nums.length>=3&&Number.isFinite(nums[0])&&Number.isFinite(nums[1])&&Number.isFinite(nums[2]))rows.push(nums.filter(Number.isFinite))}
  if(rows.length<4)throw new Error("Could not find at least four XYZ rows.");
  const four=rows.filter(r=>r.length>=4);let useIndex=false;if(four.length>=.8*rows.length){let seq=0;for(let i=1;i<four.length;i++)if(Number.isInteger(four[i][0])&&Math.abs(four[i][0]-four[i-1][0]-1)<1e-9)seq++;useIndex=seq>=.8*Math.max(1,four.length-1)}
  return rows.map(r=>useIndex?[r[1],r[2],r[3]]:[r[0],r[1],r[2]]);
}
function csvFromState(state){
  const a=state.analysis,p=state.geom.points,lines=[["i","s_over_L","s_m","x","y","z","kappa_per_m","kappa_rc","torsion_per_m","torsion_rc","v_exploratory_m_s","dTau_dt_exploratory","pressure_exploratory_Pa"].join(",")];
  for(let i=0;i<p.length;i++)lines.push([i,a.sNorm[i],a.sPhysical[i],p[i][0],p[i][1],p[i][2],a.kappaPhysical[i],a.kappaRc[i],a.tauPhysical[i],a.tauRc[i],a.vLocal[i],a.timeFactor[i],a.pressure[i]].join(","));
  lines.push("","# finite-core Biot-Savart physics grid","i,s_over_L,vT_m_s,vN_m_s,vB_m_s,speed_m_s,shape_speed_m_s,pressure_Pa,dpds_Pa_per_m");
  const ph=state.physics;for(let i=0;i<ph.pointsM.length;i++)lines.push([i,ph.sNorm[i],ph.vt[i],ph.vn[i],ph.vb[i],ph.speed[i],ph.shapeSpeed[i],ph.pressureDeficit[i],ph.dpds[i]].join(","));
  return lines.join("\n");
}
function download(name,text,type="text/plain"){const blob=new Blob([text],{type}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
Lab.IO={parseXYZ,csvFromState,download};
})();
