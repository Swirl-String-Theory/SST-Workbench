from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from .gilbert import parse_gilbert,sample_entry
from .io_xyz import write_xyz,write_vect
from .table import static_campaign,convergence_campaign
from .native import build_native
from .ridgerunner import analyze_folder,make_bridge
from .order import dynamic_analyze
from .util import write_json
from .fresnel import (scan_fresnel_source, write_scan_outputs, fresnel_static_campaign,
                      fresnel_convergence_campaign, fresnel_export)

def cmd_list(a):
    for e in parse_gilbert(a.database): print(f'{e.catalog_id:10s} {e.topology_key:10s} comps={e.component_count} coeffs={e.coefficient_count} L={e.source_L} D={e.source_D} Conway={e.conway}')
def cmd_static(a): print(json.dumps(static_campaign(a.database,a.out,a.samples,a.ids,a.metadata,a.require_native),indent=2))
def cmd_export(a):
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True); wanted=set(a.ids); found=[]
    for e in parse_gilbert(a.database):
        if e.catalog_id not in wanted and e.topology_key not in wanted: continue
        comps=sample_entry(e,a.samples); base=out/e.topology_key
        if a.format in ('txt','both'): write_xyz(base.with_suffix('.txt'),comps)
        if a.format in ('vect','both'): write_vect(base.with_suffix('.vect'),comps)
        found.append(e.catalog_id)
    print(json.dumps({'exported':found,'out':str(out)},indent=2))
def cmd_dynamic(a):
    z=np.load(a.trajectory); points=z['points']; times=z['times'] if 'times' in z else None; phase=z['phase'] if 'phase' in z else None
    r=dynamic_analyze(points,times,phase,a.window,a.defect_threshold); r['time_unit']=a.time_unit; r['length_unit']=a.length_unit; out=Path(a.out); out.mkdir(parents=True,exist_ok=True); write_json(out/'dynamic_summary.json',r)
    import csv
    rows=r['rows']; keys=list(rows[0]) if rows else []
    with (out/'dynamic_timeseries.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)
    qg=[x['Q_geom'] for x in rows]; qp=[x['Q_phase'] for x in rows if x['Q_phase'] is not None]
    master={'schema':'sst21d.dynamic-master-row.v0.1','topology_key':a.topology_key,'dynamic_status':'TRAJECTORY_ANALYZED',
            'frame_count':len(set(x['frame'] for x in rows)),'component_count':len(set(x['component'] for x in rows)),
            'Q_geom_min':min(qg) if qg else None,'Q_geom_mean':float(np.mean(qg)) if qg else None,'Q_geom_final':qg[-1] if qg else None,
            'Q_phase_min':min(qp) if qp else None,'Q_phase_mean':float(np.mean(qp)) if qp else None,'Q_phase_final':qp[-1] if qp else None,
            'Dmin_projected_det1_max':max((x['dmin_max'] for x in rows),default=None),
            'Dmin_projected_det1_mean':float(np.mean([x['dmin_mean'] for x in rows])) if rows else None,
            'largest_defect_cluster_fraction_max':max((x['largest_defect_cluster_fraction'] for x in rows),default=None),
            'phase_structure_ir_exponent':r.get('phase_structure_ir_exponent'),'dispersion_exponent_p':r.get('dispersion_exponent_p'),
            'dispersion_prefactor_A':r.get('dispersion_prefactor_A'),'time_unit':a.time_unit,'length_unit':a.length_unit}
    write_json(out/'dynamic_master_row.json',master)
    with (out/'dynamic_master_row.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(master)); w.writeheader(); w.writerow(master)
    print(json.dumps({k:v for k,v in r.items() if k not in ('rows','phase_structure_factor')},indent=2))
def cmd_fresnel_scan(a):
    scan=scan_fresnel_source(a.input,a.origin_overrides)
    print(json.dumps(write_scan_outputs(scan,a.out),indent=2))

def cmd_fresnel_static(a):
    print(json.dumps(fresnel_static_campaign(a.input,a.out,a.samples,a.prefer,a.metadata,a.origin_overrides,a.require_native),indent=2))

def cmd_fresnel_convergence(a):
    print(json.dumps(fresnel_convergence_campaign(a.input,a.out,a.resolutions,a.representation,a.origin_overrides,a.require_native),indent=2))

def cmd_fresnel_export(a):
    print(json.dumps(fresnel_export(a.input,a.out,a.samples,a.representation,a.format,a.variants,a.origin_overrides),indent=2))

def cmd_demo(a):
    n=a.points; T=a.frames; x=np.linspace(0,2*np.pi,n,endpoint=False); ref=np.c_[np.cos(x),np.sin(x),np.zeros(n)]; frames=[]; phases=[]
    times=np.linspace(0,20.0,T,endpoint=False)
    for tau in times:
        q=tau/max(times[-1],1e-15); p=ref.copy(); p[:,2]=0.08*q*np.sin(3*x); frames.append(p)
        phases.append(x+0.7*tau+0.08*np.sin(2*x-1.6*tau)+0.06*np.sin(3*x-2.4*tau)+0.04*np.sin(5*x-4.0*tau))
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); np.savez(a.out,points=np.asarray(frames),times=times,phase=np.asarray(phases)); print(a.out)
def build_parser():
    p=argparse.ArgumentParser(prog='sst21d'); sp=p.add_subparsers(dest='cmd',required=True)
    q=sp.add_parser('build-native'); q.add_argument('--clean',action='store_true'); q.set_defaults(func=lambda a:print(build_native(a.clean)))
    q=sp.add_parser('list'); q.add_argument('--database',required=True); q.set_defaults(func=cmd_list)
    q=sp.add_parser('static'); q.add_argument('--database',required=True); q.add_argument('--samples',type=int,default=600); q.add_argument('--ids',nargs='*'); q.add_argument('--metadata'); q.add_argument('--out',required=True); q.add_argument('--require-native',action='store_true'); q.set_defaults(func=cmd_static)
    q=sp.add_parser('convergence'); q.add_argument('--database',required=True); q.add_argument('--resolutions',nargs='+',type=int,default=[128,256,512]); q.add_argument('--ids',nargs='*'); q.add_argument('--out',required=True); q.add_argument('--require-native',action='store_true'); q.set_defaults(func=lambda a:print(json.dumps(convergence_campaign(a.database,a.out,a.resolutions,a.ids,a.require_native),indent=2)))
    q=sp.add_parser('export'); q.add_argument('--database',required=True); q.add_argument('--ids',nargs='+',required=True); q.add_argument('--samples',type=int,default=300); q.add_argument('--format',choices=['txt','vect','both'],default='both'); q.add_argument('--out',required=True); q.set_defaults(func=cmd_export)
    q=sp.add_parser('analyze-xyz'); q.add_argument('--input',required=True); q.add_argument('--glob',default='**/*.txt'); q.add_argument('--samples',type=int,default=300); q.add_argument('--out',required=True); q.set_defaults(func=lambda a:print(json.dumps(analyze_folder(a.input,a.glob,a.out,a.samples),indent=2)))
    q=sp.add_parser('make-rr-bridge'); q.add_argument('--pipeline-cmd',required=True); q.add_argument('--out',required=True); q.set_defaults(func=lambda a:print(make_bridge(a.pipeline_cmd,a.out)))
    q=sp.add_parser('dynamic'); q.add_argument('--trajectory',required=True); q.add_argument('--topology-key',default='UNSPECIFIED'); q.add_argument('--time-unit',default='input_time_unit'); q.add_argument('--length-unit',default='input_length_unit'); q.add_argument('--window',type=int,default=3); q.add_argument('--defect-threshold',type=float,default=0.05); q.add_argument('--out',required=True); q.set_defaults(func=cmd_dynamic)
    q=sp.add_parser('fresnel-scan'); q.add_argument('--input',required=True); q.add_argument('--origin-overrides'); q.add_argument('--out',required=True); q.set_defaults(func=cmd_fresnel_scan)
    q=sp.add_parser('fresnel-static'); q.add_argument('--input',required=True); q.add_argument('--samples',type=int,default=600); q.add_argument('--prefer',choices=['short','fseries'],default='short'); q.add_argument('--metadata'); q.add_argument('--origin-overrides'); q.add_argument('--out',required=True); q.add_argument('--require-native',action='store_true'); q.set_defaults(func=cmd_fresnel_static)
    q=sp.add_parser('fresnel-convergence'); q.add_argument('--input',required=True); q.add_argument('--resolutions',nargs='+',type=int,default=[128,256,512,1024]); q.add_argument('--representation',choices=['short','fseries'],default='fseries'); q.add_argument('--origin-overrides'); q.add_argument('--out',required=True); q.add_argument('--require-native',action='store_true'); q.set_defaults(func=cmd_fresnel_convergence)
    q=sp.add_parser('fresnel-export'); q.add_argument('--input',required=True); q.add_argument('--samples',type=int,default=300); q.add_argument('--representation',choices=['short','fseries'],default='short'); q.add_argument('--format',choices=['txt','vect','both'],default='both'); q.add_argument('--variants',nargs='*'); q.add_argument('--origin-overrides'); q.add_argument('--out',required=True); q.set_defaults(func=cmd_fresnel_export)
    q=sp.add_parser('make-demo-trajectory'); q.add_argument('--out',default='examples/demo_trajectory.npz'); q.add_argument('--points',type=int,default=128); q.add_argument('--frames',type=int,default=120); q.set_defaults(func=cmd_demo)
    return p

def main():
    args=build_parser().parse_args(); args.func(args)
if __name__=='__main__': main()
