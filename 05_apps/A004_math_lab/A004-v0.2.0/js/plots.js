(function(){
const Lab=window.SSTLab;
const baseLayout=title=>({title:{text:title,font:{size:16}},margin:{l:66,r:46,t:54,b:62},paper_bgcolor:"#121821",plot_bgcolor:"#121821",font:{color:"#dce7f2"},xaxis:{gridcolor:"#2a3645",zerolinecolor:"#405064"},yaxis:{gridcolor:"#2a3645",zerolinecolor:"#405064"},legend:{orientation:"h",y:-0.18},hovermode:"closest"});
const config={responsive:true,displaylogo:false,scrollZoom:true};
function placeholder(title,text){const l=baseLayout(title);l.annotations=[{text,x:.5,y:.5,xref:"paper",yref:"paper",showarrow:false,font:{size:16,color:"#93a4b8"}}];Plotly.react("plot",[],l,config);}
function render(kind,state){
  const p=state.geom.points,a=state.analysis,ph=state.physics,k=state.kelvin,spec=state.spectrum;let traces=[],layout;
  if(kind==="trefoil"){
    traces=[{x:p.map(q=>q[0]),y:p.map(q=>q[1]),z:p.map(q=>q[2]),type:"scatter3d",mode:"lines+markers",name:state.sourceName,line:{width:5},marker:{size:2.1,color:a.kappaRc,colorscale:"Viridis",colorbar:{title:{text:"κ r_c"}}},customdata:a.sNorm,hovertemplate:"s/L=%{customdata:.5f}<br>x=%{x:.6g}<br>y=%{y:.6g}<br>z=%{z:.6g}<extra></extra>"}];
    layout=baseLayout("Centerline · colored by κ r_c");layout.scene={aspectmode:"data",bgcolor:"#121821",xaxis:{title:"x [coordinate units]",gridcolor:"#2a3645"},yaxis:{title:"y [coordinate units]",gridcolor:"#2a3645"},zaxis:{title:"z [coordinate units]",gridcolor:"#2a3645"}};
  }else if(kind==="geometry"){
    traces=[{x:a.sNorm,y:a.kappaRc,type:"scatter",mode:"lines",name:"κ r_c"},{x:a.sNorm,y:a.tauRc,type:"scatter",mode:"lines",name:"τ r_c",yaxis:"y2"}];layout=baseLayout("Differential geometry after uniform arclength resampling");layout.xaxis.title="s/L";layout.yaxis.title="κ r_c";layout.yaxis2={title:"τ r_c",overlaying:"y",side:"right",gridcolor:"#2a3645"};
  }else if(kind==="biot"){
    traces=[{x:ph.sNorm,y:ph.vt,type:"scatter",mode:"lines",name:"v_T"},{x:ph.sNorm,y:ph.vn,type:"scatter",mode:"lines",name:"v_N"},{x:ph.sNorm,y:ph.vb,type:"scatter",mode:"lines",name:"v_B"},{x:ph.sNorm,y:ph.shapeSpeed,type:"scatter",mode:"lines",name:"|v_shape|",line:{width:3}}];layout=baseLayout("Finite-core Biot–Savart velocity decomposition");layout.xaxis.title="s/L";layout.yaxis.title="velocity [m s⁻¹]";
  }else if(kind==="time"){
    traces=[{x:state.effective.sNorm,y:state.effective.timeDeficitPPM,type:"scatter",mode:"lines",name:`10⁶(1-dτ/dt) · ${state.effective.label}`}];layout=baseLayout("SST local time diagnostic");layout.xaxis.title="s/L";layout.yaxis.title="time deficit [ppm]";
  }else if(kind==="pressure"){
    traces=[{x:state.effective.sNorm,y:state.effective.pressure,type:"scatter",mode:"lines",name:"½ρ_f v²"}];
    if(state.effective.source.startsWith("biot"))traces.push({x:ph.sNorm,y:ph.pressurePoissonSource,type:"scatter",mode:"lines",name:"Euler pressure-Poisson source",yaxis:"y2"});
    layout=baseLayout("Pressure diagnostics");layout.xaxis.title="s/L";layout.yaxis.title="Δp [Pa]";if(traces.length>1)layout.yaxis2={title:"∇²p source [Pa m⁻²]",overlaying:"y",side:"right",gridcolor:"#2a3645"};
  }else if(kind==="kelvin"){
    const valid=k.rows.filter(r=>r.valid);traces=[{x:valid.map(r=>r.n),y:valid.map(r=>r.frequency),type:"scatter",mode:"lines+markers",name:"leading-log valid modes"}];layout=baseLayout("Leading-log Kelvin / LIA diagnostic");layout.xaxis.title="mode n";layout.yaxis.title="frequency [Hz]";layout.yaxis.type="log";
  }else if(kind==="spectrum"){
    traces=[{x:spec.discrete.map((_,i)=>i+1),y:spec.discrete.map(r=>r.k),type:"scatter",mode:"markers",name:"numeric periodic FD"},{x:spec.analytic.map((_,i)=>i+1),y:spec.analytic.map(r=>r.k),type:"scatter",mode:"lines+markers",name:"analytic k_n"}];layout=baseLayout("Periodic -∂²/∂s² numerical sanity gate");layout.xaxis.title="sorted non-zero eigenmode";layout.yaxis.title="k [m⁻¹]";layout.yaxis.type="log";
  }else if(kind==="stability"){
    if(!state.stability)return placeholder("Reduced Biot–Savart stability spectrum","Run ‘reduced stability’ from the left panel.");
    const z=state.stability.eigenvalues;traces=[{x:z.map(q=>q.re),y:z.map(q=>q.im),type:"scatter",mode:"markers+text",text:z.map((_,i)=>String(i+1)),textposition:"top center",name:"λ"}];layout=baseLayout("Frozen-geometry reduced Biot–Savart eigenspectrum");layout.xaxis.title="Re λ [s⁻¹] · growth/decay";layout.yaxis.title="Im λ [s⁻¹] · oscillation";layout.shapes=[{type:"line",x0:0,x1:0,y0:Math.min(...z.map(q=>q.im),-1),y1:Math.max(...z.map(q=>q.im),1),line:{dash:"dot",width:1}}];
  }
  Plotly.react("plot",traces,layout,config);
}
Lab.Plots={render};
})();
