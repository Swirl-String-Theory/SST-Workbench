from __future__ import annotations
import argparse,csv,json,math,os,sys,time
from datetime import datetime
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from native_ext import backend_info,polyline_stats,interaction_energy,interaction_force_gradient
from sst_maxwell_falsifier.geometry import load_centerline,resample_closed,center_components,characteristic_diameter,companion_metrics,discover

AX={'x':np.array([1.,0,0]),'y':np.array([0,1.,0]),'z':np.array([0,0,1.])}

def agg_energy(A,B,core,threads,force_python=False):
    return sum(interaction_energy(a,b,core,threads,force_python=force_python) for a in A for b in B)
def agg_force(A,B,core,threads,force_python=False):
    f=np.zeros(3)
    for a in A:
      for b in B:f+=interaction_force_gradient(a,b,core,threads,force_python=force_python)
    return f

def main():
    ap=argparse.ArgumentParser(description='Relaxed-knot intake + native reduced-kernel diagnostics for DFC v0.2.0')
    ap.add_argument('--knots-dir',type=Path,required=True);ap.add_argument('--config',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--threads',type=int,default=0);ap.add_argument('--require-native',action='store_true');ap.add_argument('--force-build',action='store_true')
    a=ap.parse_args(); cfg=json.loads(a.config.read_text()); a.out.mkdir(parents=True,exist_ok=True)
    bi=backend_info(force_build=a.force_build)
    if a.require_native and not bi['native_available']: raise SystemExit('Native C++ backend required but unavailable. Run run_00_install.cmd and install MSVC Build Tools if needed.')
    files=discover(a.knots_dir,cfg['include'])
    if not files: raise SystemExit(f'No matching centerlines found in {a.knots_dir}')
    geo=[]; pair=[]; parity=[]
    for fi,p in enumerate(files,1):
      comps=load_centerline(p); met=companion_metrics(p); totalL=0.; maxcv=0.; valid=True; reasons=[]; nverts=[]
      for c in comps:
        st=polyline_stats(c); totalL+=float(st['length']);maxcv=max(maxcv,float(st['edge_cv']));nverts.append(len(c))
        if len(c)<cfg['geometry_thresholds']['min_vertices_per_component']: valid=False;reasons.append('too_few_vertices')
      if maxcv>cfg['geometry_thresholds']['max_edge_cv']:valid=False;reasons.append('edge_cv')
      rel=None
      if met and 'length' in met:
        rel=abs(totalL-float(met['length']))/max(abs(float(met['length'])),1e-30)
        if rel>cfg['geometry_thresholds']['metrics_length_relative_error_max']:valid=False;reasons.append('metrics_length_mismatch')
      geo.append({'file':p.name,'components':len(comps),'vertices':sum(nverts),'vertices_per_component':nverts,'length_recomputed':totalL,'edge_cv_max':maxcv,'metrics_length_rel_error':rel,'status':'PASS' if valid else 'FAIL','reasons':';'.join(reasons)})
      rc=[resample_closed(c,int(cfg['resample_per_component'])) for c in comps];rc,_=center_components(rc);D=characteristic_diameter(rc);core=cfg['core_radius_fraction']*D
      # Native/Python parity on first geometry only at modest resolution.
      if fi<=3:
        small=[resample_closed(c,min(48,len(c))) for c in comps];small,_=center_components(small);shift=AX['x']*(2.5*characteristic_diameter(small));B=[x+shift for x in small]
        en=agg_energy(small,B,core,a.threads);ep=agg_energy(small,B,core,1,True);fn=agg_force(small,B,core,a.threads);fp=agg_force(small,B,core,1,True)
        parity.append({'file':p.name,'energy_rel':abs(en-ep)/max(abs(ep),1e-30),'force_rel':float(np.linalg.norm(fn-fp)/max(np.linalg.norm(fp),1e-30))})
      # Reduced-kernel self-copy scans. These are NOT canonical DFC-G evidence.
      for axisname in cfg['pair_axes']:
        axis=AX[axisname]
        for mult in cfg['separation_multipliers']:
          d=float(mult*D); B=[x+axis*d for x in rc]
          E=agg_energy(rc,B,core,a.threads);F_A=agg_force(rc,B,core,a.threads);Fax=float(np.dot(-F_A,axis))  # force on the translated copy B
          h=max(1.0e-5*D,1.0e-8)
          Eplus=agg_energy(rc,[x+axis*(d+h) for x in rc],core,a.threads)
          Eminus=agg_energy(rc,[x+axis*(d-h) for x in rc],core,a.threads)
          Ffd=float(-(Eplus-Eminus)/(2.0*h))
          perr=abs(Ffd-Fax)/max(abs(Fax),abs(Ffd),1e-30)
          pair.append({'file':p.name,'axis':axisname,'d_over_D':float(mult),'d':d,'core_radius':core,'interaction_proxy_same_orientation':E,'force_proxy_same_orientation':Fax,'minus_dU_dd_proxy':Ffd,'gradient_consistency_point_relative_error':perr,'interaction_proxy_reversed_orientation':-E,'force_proxy_reversed_orientation':-Fax})
      print(f'[{fi}/{len(files)}] {p.name}: geometry={geo[-1]["status"]}, components={len(comps)}, N={sum(nverts)}')
    # finite-difference energy/analytic gradient consistency by file+axis
    for key in sorted({(r['file'],r['axis']) for r in pair}):
      rows=[r for r in pair if (r['file'],r['axis'])==key];rows.sort(key=lambda r:r['d'])
      F=np.array([r['force_proxy_same_orientation'] for r in rows]);Fd=np.array([r['minus_dU_dd_proxy'] for r in rows])
      scale=max(float(np.sqrt(np.mean(F**2))),1e-30);err=float(np.sqrt(np.mean((Fd-F)**2))/scale)
      for r in rows:r['gradient_consistency_group_nrmse']=err
    def writecsv(name,rows):
      if not rows:return
      with (a.out/name).open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    writecsv('geometry_audit.csv',geo);writecsv('native_parity.csv',parity);writecsv('reduced_pair_scan.csv',pair)
    tol=float(cfg['native_parity_relative_tolerance']); parity_ok=all(r['energy_rel']<=tol and r['force_rel']<=tol for r in parity)
    summary={'protocol':'DFC-v0.2.0 relaxed-knot precondition and reduced-kernel diagnostics','mode':cfg['mode'],'knots_dir':str(a.knots_dir.resolve()),'backend':bi,'threads':a.threads,'n_files':len(files),'geometry_pass':sum(r['status']=='PASS' for r in geo),'geometry_fail':sum(r['status']=='FAIL' for r in geo),'native_parity_pass':parity_ok,'native_parity_tolerance':tol,'reduced_kernel_guard':'SURROGATE_ONLY: interaction/force proxies are centerline Neumann-like kernels and are NOT accepted as DFC-G because the force is not an independent SST stress/momentum-flux channel. Static centerlines cannot satisfy DFC-T or DFC-D.','outputs':['geometry_audit.csv','native_parity.csv','reduced_pair_scan.csv']}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2));return 0 if summary['geometry_fail']==0 and parity_ok else 2
if __name__=='__main__':raise SystemExit(main())
