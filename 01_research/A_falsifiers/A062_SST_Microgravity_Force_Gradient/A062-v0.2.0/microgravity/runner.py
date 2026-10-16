"""A062-v0.2.0 science-only execution; does NOT impersonate v1.0.7 certification."""
from __future__ import annotations
import argparse, hashlib, json, math, os, shutil, subprocess, sys, time, zipfile
from pathlib import Path
import numpy as np
from .geometry import providers
from .filament import R_C,RHO_F,V_SWIRL,GAMMA,rotate_x,interaction,sweep,exponent,gradient_fd
from .poisson import poisson_cross
ROOT=Path(__file__).resolve().parents[1]
NAME='A062_SST_Microgravity_Force_Gradient_v0.2.0'
OUT=ROOT/(NAME+'-outputs')
LOCK=ROOT/'preregistration'/'STANDALONE_PROTOCOL_SHA256.json'
SOURCE_FILES=['.sst_framework_root','falsifier.toml','gate_plan.json','source_contract.json',
 'science_contract.json','blind_policy.json','run_all.cmd','run_science.cmd','run_science.sh',
 'framework_bootstrap.py','run_instance.py','run_python.cmd','run_python.py',
 'experiment/pipeline.py','inputs/e011/provider_pins.json','inputs/e011/trefoil_STATIC_READY_SEEDSET.json',
 'inputs/raw/Ideal.txt.gz','inputs/raw/knot_3.1_trial_001k_rr_010k_coarse.final.vect',
 'microgravity/geometry.py','microgravity/filament.py','microgravity/poisson.py','microgravity/runner.py',
 'native/kelvin_exchange.cpp','tests/test_science.py','report/FALSIFIER_REPORT.tex']

def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for part in iter(lambda:f.read(1048576),b''):h.update(part)
 return h.hexdigest()
def dump(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False,ensure_ascii=False)+'\n',encoding='utf8')
def protocol_files():return {path:digest(ROOT/path) for path in SOURCE_FILES}
def freeze():
 items=protocol_files()
 if LOCK.exists():
  j=json.loads(LOCK.read_text());assert j['files']==items,'FROZEN FILES CHANGED. Bump version.'
  return j['bundle_sha256']
 sha=hashlib.sha256(json.dumps(items,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 dump(LOCK,{'schema':'A062-STANDALONE-COMMIT-2','files':items,'bundle_sha256':sha,
  'framework_certification':False,'published_reference_not_blind':True,
  'note':'Scientific source freeze only, does not replace framework-v1.0.7 protocol'})
 return sha
def verify_freeze():
 if not LOCK.exists():raise RuntimeError('Protocol not frozen: run run_science.cmd FREEZE')
 p=json.loads(LOCK.read_text())
 if p['files']!=protocol_files():raise RuntimeError('Protocol change after freeze; new version required')
 return p['bundle_sha256']

def compile_cpp():
 cc=next((x for x in ['g++','clang++'] if shutil.which(x)),None)
 OUT.mkdir(exist_ok=True)
 exe=OUT/('kelvin_native.exe' if os.name=='nt' else 'kelvin_native')
 if cc: cmd=[cc,'-std=c++17','-O3',str(ROOT/'native/kelvin_exchange.cpp'),'-o',str(exe)]
 elif shutil.which('cl'):
  cc='cl';cmd=['cl','/nologo','/O2','/std:c++17',str(ROOT/'native/kelvin_exchange.cpp'),'/Fe:'+str(exe)]
 else:return None,'compiler unavailable'
 r=subprocess.run(cmd,cwd=OUT,capture_output=True,text=True)
 if r.returncode or not exe.is_file():return None,'compile failed: '+(r.stderr+r.stdout)[-300:]
 return exe,cc

def native_compare(pa,pb,n=192):
 exe,compiler=compile_cpp()
 if exe is None:return {'status':'UNRESOLVED','compiler':compiler,'requested':True,'executed':False}
 paths=[]
 for provider,knot in [('gilbert',pa),('knotplot',pb)]:
  path=OUT/f'geometry_{provider}_N{n}.xyz'
  np.savetxt(path,knot['x'],fmt='%.17g')
  paths.append(path)
 ratios=[]; rows=[]
 for pidx,(pair,group) in enumerate([((pa,pa),'gilbert'),((pb,pb),'knotplot'),((pa,pb),'cross_provider')]):
  a,b=pair
  path_a=paths[0] if pidx!=1 else paths[1]
  path_b=paths[1] if pidx==2 or pidx==1 else paths[0]
  for R,theta in ((1.5,0.),(5.,0.),(12.,math.pi)):
   core=a['metadata']['reach'] if group!='cross_provider' else 0.5*(a['metadata']['reach']+b['metadata']['reach'])
   py=interaction(a['x'],b['x'],R,core,theta=theta)
   run=subprocess.run([str(exe),str(path_a),str(path_b),str(R),str(core),str(theta),'1'],capture_output=True,text=True)
   if run.returncode:return {'status':'UNRESOLVED','compiler':compiler,'executed':True,'error':run.stderr}
   cpp=np.array([float(s) for s in run.stdout.split()]);pref=np.r_[py['f_b_N'],py['f_a_N']]
   abs_err=np.linalg.norm(cpp-pref);rel=abs_err/max(np.linalg.norm(pref),1e-80)
   ratios.append(rel);rows.append({'pair':group,'R_over_L':R,'angle':theta,'relative_vector_error':float(rel)})
 return {'status':'PASS' if max(ratios)<2e-8 else 'FAIL', 'compiler':compiler,'executed':True,
         'max_relative_vector_error':float(max(ratios)),'comparisons':rows,'authority':'standalone numerical parity, not framework certification'}

def _plots(results):
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,ax=plt.subplots(figsize=(7.8,5.0),dpi=140)
 for provider,style in [('gilbert','o-'),('knotplot','s-')]:
  rows=[r for r in results['providers'][provider]['full_sweep'] if r['theta_rad']==0]
  ax.loglog([r['R_over_length'] for r in rows],[abs(r['F_b_z_N']) for r in rows],style,label=provider+' (theta=0)')
 xs=np.array([3,30.]);scale=abs(next(r for r in results['providers']['gilbert']['full_sweep'] if r['theta_rad']==0 and r['R_over_length']==5)['F_b_z_N'])*5**4
 ax.loglog(xs,scale/xs**4,'k--',alpha=.55,label='R^-4 guide')
 ax.set_xlabel('R / knot perimeter length');ax.set_ylabel('|d Kelvin impulse / dt| (N)');ax.grid(alpha=.2,which='both');ax.legend();fig.tight_layout();fig.savefig(OUT/'FORCE_DISTANCE.png');plt.close(fig)
 fig,ax=plt.subplots(figsize=(7.4,4.2),dpi=140)
 for provider in ('gilbert','knotplot'):
  d=results['providers'][provider]['full_sweep']
  axes=[0,math.pi/2,math.pi]; vals=[next(x['F_b_z_N'] for x in d if abs(x['theta_rad']-th)<1e-9 and x['R_over_length']==5) for th in axes]
  ax.plot([0,90,180],[q/1e-29 for q in vals],'-o',label=provider)
 ax.set_xlabel('Tilt angle (degrees)');ax.set_ylabel('Signed F_z / 10^-29 N at R/L=5');ax.grid(alpha=.25);ax.legend();fig.tight_layout();fig.savefig(OUT/'ORIENTATION.png');plt.close(fig)

def _pdf(result,gates):
 try:
  from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,KeepTogether
  from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
  from reportlab.lib.enums import TA_CENTER
  from reportlab.lib import colors
  from reportlab.lib.units import cm
 except ImportError as e:
  dump(OUT/'REPORT_RENDER.json',{'pdf_generated':False,'reason':str(e)});return
 styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name='SubtitleA',parent=styles['Normal'],fontSize=9,leading=13,textColor=colors.HexColor('#54647c'),spaceAfter=12))
 styles.add(ParagraphStyle(name='BodyA',parent=styles['Normal'],fontSize=9,leading=13,spaceAfter=8))
 path=ROOT.parent/(NAME+'_FALSIFIER_REPORT.pdf')
 doc=SimpleDocTemplate(str(path),pagesize=(21*cm,29.7*cm),leftMargin=2*cm,rightMargin=2*cm,topMargin=1.7*cm,bottomMargin=1.7*cm)
 flow=[]
 def text(s,style='BodyA'):flow.append(Paragraph(s,styles[style]))
 text('A062: SST Microgravity Force-Gradient v0.2.0','Title')
 text('Real PKLSA/E011 STATIC_READY trefoils | Rosenhead Biot-Savart | Kelvin impulse | CPU FP64 | 12 October 2026','SubtitleA')
 text('<b>Scope:</b> Two real source-hash verified trefoil carriers (Gilbert and KnotPlot). This is instantaneous vortex-filament impulse exchange, NOT a proof of gravity, material test-particle force, stable Euler dynamics, or full isolated-space pressure closure.')
 text('<b>Inputs:</b> rho_f = 7.0e-7 kg m^-3; core radius = 1.40897017e-15 m; swirl speed = 1.09384563e6 m s^-1. Core circulation Gamma = 2 pi r_c v_swirl. Each provider is assigned L_phys = r_c/reach_normalized; this identification is a model assumption.')
 text('Pre-registered scientific gates','Heading2')
 tdata=[['Gate','Result','Evidence']]+[[x['id'],x['status'],x['explanation'][:86]] for x in gates]
 t=Table(tdata,colWidths=[1.4*cm,2.7*cm,12.9*cm],repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eef8')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#d3d8dd')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('VALIGN',(0,0),(-1,-1),'TOP'),('FONTSIZE',(0,0),(-1,-1),7.0),('BOTTOMPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5)]))
 flow.append(t);flow.append(Spacer(1,.4*cm))
 text('Measured model outputs (not microgravity measurements)','Heading2')
 rows=[['Provider','Far-field exponent','Fz at R/L=5 [N]','L physical [m]']]
 for k in ['gilbert','knotplot']:
  v=result['providers'][k];rows.append([k,f"{v['farfield_exponent']:.7f}",f"{v['force_at_R5_N']:.5e}",f"{v['physical_length_m']:.5e}"])
 t=Table(rows,colWidths=[3*cm,4*cm,5*cm,5*cm]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eef8')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#d3d8dd')),('FONTSIZE',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),7)]));flow.append(t)
 text('<b>Primary finding:</b> The prescribed two-filament candidate has approximately R^-4 longitudinal exchange in its far field, not R^-2. Reversing the relative orientation changes force sign. The physical gravitational interpretation remains unresolved.')
 flow.append(Spacer(1,.25*cm))
 flow.append(Image(str(OUT/'FORCE_DISTANCE.png'),width=15.8*cm,height=10.1*cm))
 from reportlab.platypus import PageBreak
 flow.append(PageBreak())
 text('Geometry, orientation and limitations','Heading1')
 flow.append(Image(str(OUT/'ORIENTATION.png'),width=15.6*cm,height=8.9*cm))
 text('<b>Pressure-Poisson:</b> The exploratory periodic FFT inversion closes algebraically, but a 3D grid with fewer than two points per core cannot certify the physical pressure field. Its gate stays UNRESOLVED until an isolated-space resolved solver is available.')
 text('<b>Numerical independence:</b> A separate C++17 FP64 source computes the same regularized filament interactions. Agreement is a parity result, not independent physical evidence. Source data are two independent geometry providers, not two force experiments.')
 text('<b>Experiment:</b> Zhu et al. (2026) is a comparator for eventual force-gradient measurements. The published 1.2-g apparatus cannot be identified with an elementary trefoil pair without a separately validated mass and coarse-graining model.')
 text('<b>Bibliography:</b> Y. Zhu et al., Nature Nanotechnology (2026), doi:10.1038/s41565-026-02298-8; P. G. Saffman, Vortex Dynamics, CUP (1992), doi:10.1017/CBO9780511624063; G. K. Batchelor, An Introduction to Fluid Dynamics (1967), doi:10.1017/CBO9780511800955.')
 text('<b>Provenance:</b> E010/PKLSA v0.3.1 -&gt; E011/SKLSA v0.3.0. Source hashes, input descriptors, model parameters and numerical gate ledgers accompany this report as JSON. No v1.0.7 shared-framework certification was run in this environment.')
 doc.build(flow)
 shutil.copy2(path,OUT/'FALSIFIER_REPORT.pdf')
 dump(OUT/'REPORT_RENDER.json',{'pdf_generated':True,'path':str(path),'software':'reportlab'})

def run(mode='FULL'):
 stamp=time.perf_counter();freeze_id=verify_freeze();OUT.mkdir(exist_ok=True)
 segments=[48,96,192] if mode=='BASIC' else [48,96,192,384]
 Rvals=[1.,2.,3.,5.,8.,12.,18.,27.,40.]
 d={'schema':'A062-PKLSA-KELVIN-IMPULSE-1','mode':mode,'protocol_sha256':freeze_id,
   'framework_certification':False,'source':'E011 v0.3.0 upstream Gilbert and KnotPlot',
   'model':'Rosenhead_regularized_prescribed_filament_Kelvin_impulse_exchange',
   'constants':{'rho_f_kg_per_m3':RHO_F,'r_c_m':R_C,'v_swirl_m_per_s':V_SWIRL,'Gamma_m2_per_s':GAMMA},
   'distance_ratios':Rvals,'discretization_N':segments,'providers':{},'convergence':{},
   'framework_notes':['These results are standalone; local framework v1.0.7 is not present.',
     'Paper published comparator is not raw independent observation.']}
 gates=[]
 def gate(ident,status,value,explanation):gates.append({'id':ident,'status':status,'value':value,'explanation':explanation})
 gate('P0','PASS',freeze_id[:16],'Protocol hashes verified before execution')
 provider_data={}
 for N in segments:
  pp=providers(N)
  provider_data[N]=pp
 for k in ['gilbert','knotplot']:
  pp=provider_data[segments[-1]][k];x=pp['x'];reach=pp['metadata']['reach']
  records=sweep(x,x,Rvals,reach)
  result={'provider':k,'static_seed_id':pp['metadata']['static_seed_id'],
    'carrier_id':pp['metadata']['carrier_id'],'raw_sha256':pp['raw_sha256'],
    'writhe_metadata':pp['metadata']['writhe'],'writhe_discrete':pp['writhe_proxy'],
    'reach_normalized':reach,'core_ratio':reach,'physical_length_m':R_C/reach,
    'full_sweep':records,'farfield_exponent':exponent(records,0.,limit=8.),
    'force_at_R5_N':next(r['F_b_z_N'] for r in records if r['R_over_length']==5 and r['theta_rad']==0),
    'force_at_R5_pi_N':next(r['F_b_z_N'] for r in records if r['R_over_length']==5 and abs(r['theta_rad']-math.pi)<1e-8),
    'gradient_at_R5_N_per_m':gradient_fd(x,x,5,reach,h=.05)/(R_C/reach),
    'max_action_reaction_residual':max(v['third_law_residual'] for v in records),
    'area':pp['area']}
  d['providers'][k]=result
 for k in ['gilbert','knotplot']:
  core=d['providers'][k]['core_ratio']; perN={}
  for N in segments:
   x=provider_data[N][k]['x']
   perN[str(N)]={str(R):interaction(x,x,R,core)['f_parallel_N'] for R in (3.,5.,12.)}
  best=perN[str(segments[-1])];prev=perN[str(segments[-2])]
  relative={R:abs(prev[R]-best[R])/max(abs(best[R]),1e-100) for R in best}
  d['convergence'][k]={'forces_by_N':perN,'last_relative_difference':relative,
    'max_relative_difference':max(relative.values())}
 p=d['providers'];maxdiff=max(d['convergence'][k]['max_relative_difference'] for k in p)
 ratio=abs(p['gilbert']['force_at_R5_N']-p['knotplot']['force_at_R5_N'])/max(abs(p['gilbert']['force_at_R5_N']),abs(p['knotplot']['force_at_R5_N']))
 recip=max(p[k]['max_action_reaction_residual'] for k in p)
 gate('P1','PASS',2,'Two source hashes match E011 UPSTREAM_INDEPENDENT PRIMARY_REFERENCE anchors')
 gate('P2','PASS' if maxdiff<.025 else 'FAIL',maxdiff,'48/96/192/384 polygon sampling, last relative force difference < 2.5%')
 gate('P3','PASS' if recip<.002 else 'FAIL',recip,'Two-way Kelvin impulse exchange action-reaction residual <0.002')
 slopes={k:p[k]['farfield_exponent'] for k in p};slope_ok=all(abs(x-2)<=0.2 for x in slopes.values())
 gate('P4','PASS' if slope_ok else 'FAIL',slopes,'Requires independent-provider far-field exponent 2 +/-0.2')
 signs={k:p[k]['force_at_R5_N']*p[k]['force_at_R5_pi_N'] for k in p}
 orientation_ok=all(x>0 for x in signs.values())
 gate('P5','PASS' if orientation_ok else 'FAIL',signs,'Requires same signed attractive force at theta=0 and theta=pi for both anchors')
 gate('P6','PASS' if ratio<=.05 else 'FAIL',ratio,'Independent-provider force amplitude difference at R/L=5 <=5%')
 # Real pressure field would need grid spacings substantially smaller than rc.
 po=[]
 if mode!='BASIC':
  pa,pb=provider_data[192]['gilbert']['x'],provider_data[192]['knotplot']['x']
  for n in (24,36):po.append(poisson_cross(pa,pb,R=1.5,core=0.02817,n=n))
 d['poisson_diagnostic']=po
 gate('P7','UNRESOLVED',max([r['core_radius_grid_cells'] for r in po],default=None),
      'Periodic Poisson is only algebraically solved; core <1 cell, physical isolated-space pressure unresolved')
 cpp=native_compare(provider_data[192]['gilbert'],provider_data[192]['knotplot'],192)
 d['native_cpp_fp64']=cpp
 gate('P8',cpp['status'],cpp.get('max_relative_vector_error'), 'Real independent C++17 FP64 kernel, no fallback to Python')
 gate('P9','UNRESOLVED',None,'No time-resolved advected vortex solution nor full Euler stress/control-surface force')
 gate('P10','UNRESOLVED',None,'No derived SST mass closure, G identification, or many-body upscaling to 1.2g')
 gate('P11','UNRESOLVED',None,'No withheld force-distance experimental data or authorized reveal')
 d['provider_rel_force_amplitude_at_R5']=ratio
 d['max_reciprocity_residual']=recip
 d['overall_scientific_status']='RESTRICTED_TWO_FILAMENT_GRAVITY_CLOSURE_FAILED; FULL_SST_GRAVITY_UNRESOLVED'
 d['elapsed_wall_seconds_before_report']=time.perf_counter()-stamp
 d['local_gates']={k['id']:k['status'] for k in gates}
 dump(OUT/'SCIENCE_RESULTS.json',d)
 dump(OUT/'GATE_LEDGER.json',{'schema':'A062-LOCAL-GATES-2','not_framework_gate_ledger':True,'continue_after_failed_science_gate':True,'gates':gates})
 _plots(d);_pdf(d,gates)
 dump(OUT/'RUN_SUMMARY.json',{'schema':'A062-RUN-SUMMARY-2','framework_certification':False,'completed':True,
   'science_summary':d['overall_scientific_status'],'mode':mode,'N_max':segments[-1],
   'runtime_seconds':time.perf_counter()-stamp,'gate_status':d['local_gates'], 'C++_executed':cpp['executed']})
 dump(OUT/'OUTPUT_MANIFEST.json',{'schema':'A062-OUTPUT-MANIFEST-2','files':{str(f.relative_to(OUT)):digest(f) for f in OUT.rglob('*') if f.is_file() and f.name!='OUTPUT_MANIFEST.json'}})
 archive=ROOT.parent/(NAME+'-outputs_BLIND.zip')
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
  for f in sorted(OUT.rglob('*')):
   if f.is_file() and f.name not in ('kelvin_native','kelvin_native.exe'):
    z.write(f,arcname=f.relative_to(ROOT))
 print('A062 v0.2.0 standalone result')
 for g in gates:print(' ',g['id'],g['status'],str(g['value'])[:80])
 print('elapsed_s:',round(time.perf_counter()-stamp,2));print('science output:',OUT)
 return d

def main():
 ap=argparse.ArgumentParser();ap.add_argument('mode',nargs='?',default='FULL',choices=['FREEZE','SELFTEST','BASIC','FULL','CERTIFY'])
 args=ap.parse_args()
 if args.mode=='FREEZE':print('standalone frozen:',freeze());return 0
 if args.mode=='SELFTEST':return subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT).returncode
 d=run(args.mode)
 if args.mode=='CERTIFY' and d['native_cpp_fp64']['status']!='PASS':return 4
 return 0
if __name__=='__main__':raise SystemExit(main())
