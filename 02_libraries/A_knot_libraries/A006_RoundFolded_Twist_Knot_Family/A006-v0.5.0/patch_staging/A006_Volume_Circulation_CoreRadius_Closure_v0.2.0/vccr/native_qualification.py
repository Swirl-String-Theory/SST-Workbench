"""Read-only, deliberately non-certifying native-material-tracer interface.

Consumes measured polygons/velocities from an external solver. It never
reconstructs cross sections from VCCR closure or assigns material identities
based on KnotPlot bead index alone.
"""
from __future__ import annotations
import argparse,json,math,sys
from pathlib import Path
import numpy as np
from .euler_qualification import ring_measure, dump_json

SCHEMA='vccr.native.material.v1'


def _as_points(value,label,min_n):
    a=np.asarray(value,dtype=float)
    if a.ndim!=2 or a.shape[1]!=3 or a.shape[0]<min_n or not np.all(np.isfinite(a)):
        raise ValueError(f'{label} must contain >= {min_n} finite XYZ triplets')
    return a


def load_segment(s):
    required=['material_segment_id','material_marker_ids','axial_marker_ids','axial_points_m','ring_positions_m','ring_velocities_m_s']
    for k in required:
        if k not in s:raise ValueError(f'missing {k}')
    axis=_as_points(s['axial_points_m'],'axial_points_m',2)
    pts=_as_points(s['ring_positions_m'],'ring_positions_m',12)
    vel=_as_points(s['ring_velocities_m_s'],'ring_velocities_m_s',12)
    if pts.shape!=vel.shape:raise ValueError('ring_positions and ring_velocities shape mismatch')
    axial_ids=s['axial_marker_ids']
    if not isinstance(axial_ids,list) or len(axial_ids)!=len(axis) or len(set(map(str,axial_ids)))!=len(axis):raise ValueError('invalid axial_marker_ids')
    marker_ids=s['material_marker_ids']
    if not isinstance(marker_ids,list) or len(marker_ids)!=len(pts) or len(set(map(str,marker_ids)))!=len(pts):raise ValueError('invalid material_marker_ids')
    line_lengths=np.linalg.norm(np.diff(axis,axis=0),axis=1)
    if np.any(line_lengths<=0):raise ValueError('degenerate axial polyline')
    length=float(np.sum(line_lengths))
    tangent=(axis[-1]-axis[0]); tangent=tangent/np.linalg.norm(tangent)
    ring=ring_measure(pts,vel)
    alignment=abs(float(np.dot(ring['normal'],tangent)))
    flux=s.get('vorticity_flux_m2_s')
    if flux is not None and not math.isfinite(float(flux)):raise ValueError('invalid independent vorticity flux')
    return dict(material_segment_id=str(s['material_segment_id']),marker_ids=tuple(map(str,marker_ids)),
                axial_ids=tuple(map(str,axial_ids)),
                length_m=length,area_m2=ring['area'],radius_eff_m=ring['a_eff'],
                volume_proxy_m3=ring['area']*length, circulation_line_m2_s=ring['gamma'],
                flux_reported_m2_s=None if flux is None else float(flux),
                ring_alignment=alignment,planarity=ring['planarity'],roundness=ring['roundness'])


def analyze(doc):
    if doc.get('schema')!=SCHEMA:raise ValueError(f'schema must be {SCHEMA}')
    if doc.get('source_provenance') not in ('external_solver','synthetic_demo'):
        raise ValueError('source_provenance must be external_solver or synthetic_demo')
    frames=doc.get('frames')
    if not isinstance(frames,list) or len(frames)<2:raise ValueError('at least two material-time frames required')
    parsed=[];times=[]
    for i,f in enumerate(frames):
        t=float(f['t_s'])
        if not math.isfinite(t) or (times and t<=times[-1]):raise ValueError('times must strictly increase')
        times.append(t)
        ss=f.get('segments')
        if not isinstance(ss,list) or not ss:raise ValueError('each frame needs segments')
        segments=[load_segment(s) for s in ss]
        if len(set(s['material_segment_id'] for s in segments))!=len(segments):raise ValueError('duplicate segment ID')
        parsed.append({s['material_segment_id']:s for s in segments})
    base=parsed[0]
    rows=[]
    identity_ok=True
    for i,(t,frame) in enumerate(zip(times,parsed)):
        if frame.keys()!=base.keys():identity_ok=False;break
        for seg_id,s in frame.items():
            o=base[seg_id]
            if s['marker_ids']!=o['marker_ids'] or s['axial_ids']!=o['axial_ids']:identity_ok=False
            gamma0=o['circulation_line_m2_s']
            if abs(gamma0)<1e-30:raise ValueError('zero reference circulation cannot be relatively Kelvin-qualified')
            gamma_err=s['circulation_line_m2_s']/gamma0-1
            lam=s['length_m']/o['length_m']
            radius_rel=s['radius_eff_m']/o['radius_eff_m']
            flux_err=(s['circulation_line_m2_s']/s['flux_reported_m2_s']-1) if s['flux_reported_m2_s'] else None
            rows.append(dict(t_s=t,material_segment_id=seg_id,lambda_observed=lam,
                 radius_observed_ratio=radius_rel,radius_predicted_ratio=lam**-.5,
                 radius_relative_error=radius_rel*lam**.5-1,
                 volume_proxy_relative_error=s['volume_proxy_m3']/o['volume_proxy_m3']-1,
                 circulation_relative_error=gamma_err,
                 independently_supplied_flux_relative_error=flux_err,
                 ring_alignment=s['ring_alignment'],ring_planarity=s['planarity'],
                 roundness=s['roundness']))
    quality=identity_ok and all(r['ring_alignment']>0.99 and r['ring_planarity']<.02 for r in rows)
    residuals=[r for r in rows if r['t_s']>times[0]]
    def max_abs(field):
        v=[abs(float(r[field])) for r in residuals]
        return max(v) if v else float('inf')
    maxr=max_abs('radius_relative_error') if identity_ok else None
    maxv=max_abs('volume_proxy_relative_error') if identity_ok else None
    maxg=max_abs('circulation_relative_error') if identity_ok else None
    valid=bool(quality and all(math.isfinite(v) and v<5e-3 for v in (maxr,maxv,maxg)))
    source=doc['source_provenance']
    return dict(schema='vccr.native.qualification.v0.2.0',source_provenance=source,
      status='PASS_MEASUREMENTS_ONLY_NOT_EULER_CERTIFICATION' if valid else 'FAIL_OR_UNRESOLVED_MEASUREMENT_CHECKS',
      gate_results=dict(GN0_schema_and_material_ids='PASS' if identity_ok else 'FAIL',
        GN1_cross_section_planarity_alignment='PASS' if quality else 'FAIL',
        GN2_radius_volume_circulation_measured='PASS' if valid else 'FAIL',
        GN3_independently_computed_vorticity_flux='REPORTED_NOT_VERIFIED' if any(r['independently_supplied_flux_relative_error'] is not None for r in rows) else 'NOT_RUN',
        GN4_full_Euler_PDE_residual='NOT_RUN',GN5_space_time_refinement='NOT_RUN',
        GN6_topology_clearance_reconnection='NOT_RUN',GN7_physical_SST_calibration='UNRESOLVED'),
      maxima=dict(radius_relative=maxr,volume_proxy_relative=maxv,circulation_relative=maxg),
      note=('SYNTHETIC_DEMO_NOT_NATIVE_SOLVER' if source=='synthetic_demo' else
      'RAW_EXPORTED_DATA_NOT_INDEPENDENTLY_VERIFIED_AS_EULER_SOLVER'),
      assumptions=['IDs track exactly the same fluid material markers',
                   'rings approximate transverse cross sections to filament tangent',
                   'area*axis arclength is a slender-tube approximation for curved filaments',
                   'reported flux and numerical solver metadata are unverified',
                   'no mesh convergence or topology certification from two frames'],rows=rows)


def main(argv=None):
    ap=argparse.ArgumentParser(description='VCCR v0.2.0 external material Euler data intake; measurement qualification only')
    ap.add_argument('--input',required=True);ap.add_argument('--out',default='Output/VCCR_v0.2.0/native')
    ns=ap.parse_args(argv)
    try:
        j=json.loads(Path(ns.input).read_text(encoding='utf-8'))
        report=analyze(j)
        out=Path(ns.out);out.mkdir(parents=True,exist_ok=True)
        dump_json(out/'native_qualification.json',report)
        print('RESULT:',report['status'],'GATES:',report['gate_results'])
        print('WROTE:',out/'native_qualification.json')
        return 0 if report['status'].startswith('PASS_') else 2
    except (ValueError,KeyError,TypeError,OSError,OverflowError) as e:
        print('NATIVE INPUT REJECTED:',e,file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
