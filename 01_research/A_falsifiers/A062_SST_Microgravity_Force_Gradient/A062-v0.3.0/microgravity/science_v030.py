"""A062-v0.3 standalone CPU diagnostics called inside v1.0.8 owned output root."""
from __future__ import annotations
import json,math,shutil,subprocess,time,hashlib
from pathlib import Path
import numpy as np
from .geometry import providers
from .monopole import force,force_pair,fit_slope,cross_stress_integral,source_gradient,source_potential,euler_pressure_monopole_analytic
ROOT=Path(__file__).resolve().parents[1]
def put(path,x):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(x,indent=2,sort_keys=True,default=float,allow_nan=False)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def cpp_parity(base,out):
 compiler=shutil.which('g++') or shutil.which('clang++')
 if not compiler:return {'status':'UNRESOLVED','compiler':None,'executed':False}
 binary=out/'scalar_cpp_check'
 p=subprocess.run([compiler,'-O2','-std=c++17',str(ROOT/'native/scalar_pair.cpp'),'-o',str(binary)],capture_output=True,text=True)
 if p.returncode:return {'status':'UNRESOLVED','compiler':compiler,'executed':False,'error':p.stderr[-900:]}
 discrepancies=[]
 for key in ('gilbert','knotplot'):
  x=base[key]['x'];pts=(x+np.roll(x,-1,axis=0))/2;ll=np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1);w=ll/ll.sum()
  f=force(x,x,5.,epsilon=0.)
  # native C++ reads segment midpoints & weights, computes double quadrature
  data=out/(key+'_scalar_points.txt');np.savetxt(data,np.column_stack((pts,w)),fmt='%.17e')
  r=subprocess.run([str(binary),str(data),'5'],capture_output=True,text=True)
  if r.returncode:return {'status':'UNRESOLVED','executed':True,'error':r.stderr[-900:]}
  q=np.array([float(s) for s in r.stdout.split()]);err=float(np.linalg.norm(q-f)/max(np.linalg.norm(f),1e-100))
  discrepancies.append({'provider':key,'relative_error':err})
 return {'status':'PASS' if max(q['relative_error'] for q in discrepancies)<2e-10 else 'FAIL','executed':True,'compiler':compiler,'comparisons':discrepancies,'max_relative_error':max(q['relative_error'] for q in discrepancies)}

def run(out:Path,mode:str='FULL'):
 stamp=time.perf_counter()
 # Replay geometry of each provider in two resolutions; preserve lineage
 levels=[48,96] if mode=='BASIC' else [48,96,192]
 geom={N:providers(N) for N in levels}
 high=geom[levels[-1]]
 data={'schema':'A062-V030-MONOPOLAR-CLOSURE-1','science_version':'0.3.0','mode':mode,'conclusion':'EULER_ONLY_MONOPOLE_ZERO; CONDITIONAL_SCALAR_R^-2; INTRINSIC_BRIDGE_UNRESOLVED','h0_euler':{},'h1_postulated_scalar':{},'h2_intrinsic_bridge':{},'native_cpp_fp64':{},'derived_G':False}
 # H0: structure theorem and previously executed filament-exchange result are different observables.
 previous=json.loads((ROOT/'inputs/baseline_v020_user_results.json').read_text())
 data['h0_euler']={'pressure_source_identity':'laplacian p = -rho_f partial_i partial_j(v_i v_j)','isolated_monopole':0,'hypotheses':['localized incompressible smooth velocity','boundary terms vanish'],'original_kelvin_results':previous['selected_results']['providers'],'note':'The theorem excludes a *pressure-Poisson monopole* for localized free-space Euler, not every clock scalar or every body force.'}
 distances=[3.,5.,8.,12.,18.,27.,40.];errors=[]
 for group in ('gilbert','knotplot'):
  x=high[group]['x'];meta=high[group]['metadata'];core=meta['reach']
  rows=[{'R_over_perimeter':R,'Fz_normalized':float(force(x,x,R,epsilon=0.)[2]),'Fz_pi':float(force(x,x,R,theta=math.pi,epsilon=0.)[2])} for R in distances]
  slope,_=fit_slope(x,x,epsilon=0.)
  ff=force(x,x,5.);fb,fa=force_pair(x,x,5.)
  err=float(np.linalg.norm(fb+fa)/max(np.linalg.norm(fb),np.linalg.norm(fa),1e-30))
  stress=cross_stress_integral(x,x,5.,nsurf=800,radius=.32)
  # For conservative scalar coupling choose attraction = +grad(tau) which is negative z.
  # Pure gradient quadratic stress traction on closed surface yields opposite sign; sign choice recorded.
  s_err=float(np.linalg.norm(stress+ff)/max(np.linalg.norm(ff),1e-100))
  conv=[]
  for N in levels:
   xx=geom[N][group]['x'];conv.append({'N':N,'force_at_R5':float(force(xx,xx,5.)[2])})
  conv_rel=abs(conv[-1]['force_at_R5']-conv[-2]['force_at_R5'])/abs(conv[-1]['force_at_R5'])
  test_farfield=(float(force(x,x,40.)[2])*(-4*np.pi*40**2))
  data['h1_postulated_scalar'][group]={'source_provider':group,'static_seed_id':meta['static_seed_id'],'source_sha256':high[group]['raw_sha256'],'normalized_charge_A':1,'normalized_charge_B':1,'kappa':1,'lambda':1,'scalar_force_sign':'attractive by chosen source/test action coupling','R_sweep':rows,'exponent_fit_ge_R8':slope,'R5_traction_cross_stress':stress.tolist(),'R5_scalar_force':ff.tolist(),'stress_sign_convention_residual':s_err,'action_reaction_residual':err,'N_convergence':conv,'last_relative_refinement':float(conv_rel),'farfield_charge_product_recovery':test_farfield}
  errors.append(s_err)
 # H2 no hidden optimization or fitting: direct pressure operator integrates to zero; no tested mechanism generates Qclock=mass
 data['h2_intrinsic_bridge']={'tested_direct_identification':'rho_clock = C*(-rho_f partial_i partial_j(v_i v_j)) with finite constant C','euler_pressure_multipole_charge':0,'required_nonzero_charge':True,'closure':'FAIL for this direct proportionality; all alternative condensate and clock-mode source closures remain UNRESOLVED','mass_mapping':'UNRESOLVED','coupling_normalization':'UNRESOLVED','equivalence_principle':'UNRESOLVED'}
 pp=data['h1_postulated_scalar'];relamp=abs(pp['gilbert']['R5_scalar_force'][2]-pp['knotplot']['R5_scalar_force'][2])/max(abs(pp['gilbert']['R5_scalar_force'][2]),abs(pp['knotplot']['R5_scalar_force'][2]))
 data['provider_amplitude_difference_R5']=relamp
 data['native_cpp_fp64']=cpp_parity(high,out)
 data['runtime_seconds']=time.perf_counter()-stamp
 gates=[]
 def gate(i,s,msg,val=None):gates.append({'gate':i,'status':s,'reason':msg,'metric':val})
 gate('M0','PASS','E011 raw original source hashes checked by provider loaders',2)
 maxerr=max(pp[g]['last_relative_refinement'] for g in ('gilbert','knotplot'))
 gate('M1','PASS' if maxerr<.005 else 'FAIL','Conditional scalar line integration convergence relative below .5%',maxerr)
 ex={g:pp[g]['exponent_fit_ge_R8'] for g in ('gilbert','knotplot')}
 gate('M2','PASS' if all(abs(n-2)<.05 for n in ex.values()) else 'FAIL','H1 normalized postulated source has far field inverse square (not SST prediction)',ex)
 gate('M3','PASS' if all(pp[g]['action_reaction_residual']<.002 for g in pp) else 'FAIL','H1 force reciprocity (postulated EFT)',{g:pp[g]['action_reaction_residual'] for g in pp})
 gate('M4','PASS' if all(pp[g]['stress_sign_convention_residual']<.07 for g in pp) else 'FAIL','Quadratic scalar cross-stress integrated over closed B surface; compare opposite attraction sign',max(errors))
 gate('M5','PASS' if relamp<.05 else 'FAIL','Independent geometry providers H1 normalized amplitude <5%',relamp)
 gate('M6','PASS','Localized Euler pressure-source monopole vanishes identically if boundary flux vanishes',0.)
 gate('M7','FAIL','Direct proportionality from Euler pressure source to Swirl Clock source has zero integrated monopole',0.)
 gate('M8','UNRESOLVED','No independent PKLSA derived clock mode, dimensional lambda/kappa, mass mapping, or equivalence',None)
 gate('M9',data['native_cpp_fp64']['status'],'Strict compiled C++17 FP64 evaluates independent line pair quadrature',data['native_cpp_fp64']['max_relative_error'] if data['native_cpp_fp64']['executed'] and 'max_relative_error' in data['native_cpp_fp64'] else None)
 gate('M10','UNRESOLVED','No withheld raw apparatus data or physical force transfer calibration',None)
 # retain failures of H1 stress until corrected, do not paper over.
 data['scientific_gates']=gates
 put(out/'SCIENCE_RESULTS.json',data);put(out/'LOCAL_SCIENCE_GATES.json',gates)
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,ax=plt.subplots(figsize=(7.5,4.6))
 for g in ('gilbert','knotplot'):
  rr=pp[g]['R_sweep'];ax.loglog([v['R_over_perimeter'] for v in rr],[abs(v['Fz_normalized']) for v in rr],'o-',label=g+' H1 imposed scalar')
 r=np.array(distances);ax.loglog(r,1/(4*np.pi*r*r),'k--',label='R^-2 unit-charge guide')
 ax.set(xlabel='R / normalized perimeter',ylabel='|Fz| (normalized EFT force units)');ax.grid(True,which='both',alpha=.2);ax.legend();fig.tight_layout();fig.savefig(out/'H1_SCALAR_FORCE_DISTANCE.png',dpi=140);plt.close(fig)
 return data
