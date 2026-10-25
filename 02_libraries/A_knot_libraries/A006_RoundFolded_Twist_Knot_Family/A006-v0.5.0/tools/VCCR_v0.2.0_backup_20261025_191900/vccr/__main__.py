"""CLI for VCCR v0.1.0. Commands never mutate input XYZ or A006 core."""
import argparse,csv,json,sys,math
from pathlib import Path
from dataclasses import asdict
from .core import (CORE_RADIUS,SWIRL_SPEED,TREFOIL_ROPELENGTH_DIAMETER,
                   reference_trefoil,stretch_table,dimension_checks,state_from_ropelength_saturated,knot_type_bounds)
from .geometry import measurements,material_pair


def persist(obj,out,stem):
    p=Path(out);p.mkdir(parents=True,exist_ok=True)
    dest=p/(stem+'.json')
    dest.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    return dest


def csv_table(rows,p):
    if not rows:return
    p=Path(p)
    with p.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)


def cli(argv=None):
    ap=argparse.ArgumentParser(description='VCCR v0.1.0 — conditional geometrical and vortex-tube closure')
    sub=ap.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('analytic',help='SI conservation states for dimensionless stretch factors')
    a.add_argument('--stretch',type=float,nargs='+',default=[1,1.25,1.5,2,3,4])
    a.add_argument('--a0',type=float,default=CORE_RADIUS,help='reference physical core radius in meters')
    a.add_argument('--v0',type=float,default=SWIRL_SPEED,help='reference core-edge swirl speed m/s, an SST calibration')
    a.add_argument('--R0-d',type=float,default=TREFOIL_ROPELENGTH_DIAMETER,help='reference diameter-convention ropelength')
    a.add_argument('--out',default='Output/VCCR_v0.1.0')
    g=sub.add_parser('geometry',help='inspect ASCII XYZ, including blank-separated link components')
    g.add_argument('files',nargs='+');g.add_argument('--out',default='Output/VCCR_v0.1.0')
    c=sub.add_parser('compare',help='material-segment bookkeeping; requires correspondence assertion')
    c.add_argument('--initial',required=True);c.add_argument('--final',required=True)
    c.add_argument('--assert-material-correspondence',action='store_true')
    c.add_argument('--meters-per-coordinate-unit',type=float,required=True)
    c.add_argument('--a0',type=float,default=CORE_RADIUS)
    c.add_argument('--v0',type=float,default=SWIRL_SPEED)
    c.add_argument('--out',default='Output/VCCR_v0.1.0')
    tr=sub.add_parser('trajectory',help='global lengths for corresponding material tube over different frames; NO bead correspondence required')
    tr.add_argument('frames',nargs='+',help='chronological ASCII XYZ snapshots of the SAME material tube(s)')
    tr.add_argument('--assert-same-material-tube',action='store_true')
    tr.add_argument('--a0',type=float,default=CORE_RADIUS)
    tr.add_argument('--v0',type=float,default=SWIRL_SPEED)
    tr.add_argument('--meters-per-coordinate-unit',type=float,default=None)
    tr.add_argument('--out',default='Output/VCCR_v0.1.0')
    r=sub.add_parser('saturated',help='hypothetical tube filling available geometric thickness; R-d externally supplied')
    r.add_argument('--R-d',type=float,nargs='+',required=True)
    r.add_argument('--out',default='Output/VCCR_v0.1.0')
    b=sub.add_parser('bounds',help='conditional knot lower-length / upper-core bound')
    b.add_argument('--Rmin-d',type=float,nargs='+',required=True,help='externally independently established min ropelength')
    b.add_argument('--out',default='Output/VCCR_v0.1.0')
    ns=ap.parse_args(argv)
    try:
        ref=reference_trefoil()
        if ns.cmd=='analytic':
            ref=reference_trefoil(a0=ns.a0,swirl_speed=ns.v0,R_d=ns.R0_d)
            rows=stretch_table(ns.stretch,ref)
            report=dict(version='0.1.0',status='ANALYTIC_CONDITIONAL',
                        calibration='Trefoil reference: assumed a0=r_c, R_d0 numerical ideal seed, v_edge0=swirl speed',
                        reference=asdict(ref),assumptions=['uniform circular tube','material incompressible tube volume constant',
                        'Kelvin circulation constant','same *single* vortex tube at different lengths',
                        'uniform stretch for omega scaling', 'reference SST inputs NOT independently derived'],
                        gates={'G0_dimensions': 'PASS' if all(dimension_checks(ref).values()) else 'FAIL',
                               'G1_volume_algebra':'PASS','G2_kelvin_assumed':'CONDITIONAL',
                               'G3_geometric_thickness':'UNRESOLVED','G4_topology':'NOT_TESTED',
                               'G5_euler_trajectory':'NOT_RUN'},rows=rows)
            dest=persist(report,ns.out,'analytic');csv_table(rows,Path(ns.out)/'analytic.csv')
        elif ns.cmd=='geometry':
            rows=[measurements(f) for f in ns.files]
            report=dict(version='0.1.0',status='GEOMETRY_ONLY',
                        gates={'geometry_parse':'PASS','geometric_thickness':'UNRESOLVED_NO_CERTIFIED_ALGORITHM',
                               'cross_knot_meter_scale':'UNRESOLVED','topology_invariants':'NOT_TESTED',
                               'circulation':'NOT_MEASURED'},geometry=rows)
            dest=persist(report,ns.out,'geometry')
            flatten=[]
            for x in rows:
                for i,subrow in enumerate(x['components']):
                    flatten.append(dict(path=x['path'],component_index=i,**{k:v for k,v in subrow.items() if k!='centroid_coordinate'}))
            csv_table(flatten,Path(ns.out)/'geometry.csv')
        elif ns.cmd=='trajectory':
            if not ns.assert_same_material_tube:
                ap.error('trajectory requires --assert-same-material-tube; snapshots must track same tubes with no flux loss/reconnection and common coordinate scale')
            from .core import finite_positive
            a0=finite_positive(ns.a0,'a0');v0=finite_positive(ns.v0,'v0')
            if ns.meters_per_coordinate_unit is not None:
                finite_positive(ns.meters_per_coordinate_unit,'meters_per_coordinate_unit')
            frames=[measurements(f) for f in ns.frames]
            n=frames[0]['n_components']
            if any(f['n_components']!=n for f in frames):
                raise ValueError('changing component count; not the same material tube ensemble')
            if len(frames)<2: raise ValueError('trajectory requires at least two frames')
            G=2*math.pi*a0*v0; omega0=G/(math.pi*a0*a0)
            rows=[]
            for frame_index,f in enumerate(frames):
                for j,cc in enumerate(f['components']):
                    initial_L=frames[0]['components'][j]['length_coordinate']
                    length_ratio=cc['length_coordinate']/initial_L
                    radius=a0/math.sqrt(length_ratio)
                    row=dict(frame_index=frame_index,path=f['path'],component_index=j,
                             length_ratio=length_ratio,radius_m=radius,
                             mean_omega_s1=omega0*length_ratio,
                             gamma_m2_s=G,swirl_edge_speed_m_s=G/(2*math.pi*radius),
                             volume_ratio=1.0,geometry_length_coordinate=cc['length_coordinate'],
                             physical_length_m=None,physical_volume_m3=None)
                    if ns.meters_per_coordinate_unit is not None:
                        scale=ns.meters_per_coordinate_unit
                        row.update(physical_length_m=cc['length_coordinate']*scale,
                                   physical_volume_m3=math.pi*a0*a0*initial_L*scale)
                    rows.append(row)
            report=dict(version='0.1.0',status='CONDITIONAL_LENGTH_BASED_CLOSURE',
                        assumption='assertion of same material tubes and unchanged XYZ unit scale is not independently verified',
                        gates={'G0_geometry':'PASS', 'G1_same_material_tube':'ASSERTED_NOT_VERIFIED',
                               'G2_circulation':'ASSUMED_NOT_MEASURED','G3_cross_section':'NOT_MEASURED',
                               'G4_euler':'NOT_RUN'},rows=rows)
            dest=persist(report,ns.out,'trajectory');csv_table(rows,Path(ns.out)/'trajectory.csv')
        elif ns.cmd=='compare':
            if not ns.assert_material_correspondence:
                ap.error('compare requires --assert-material-correspondence; bead indices are NOT automatically material labels')
            G=2*math.pi*ns.a0*ns.v0
            report=material_pair(ns.initial,ns.final,ns.a0,G,ns.meters_per_coordinate_unit)
            dest=persist(report,ns.out,'material_compare')
        elif ns.cmd in ('saturated','bounds'):
            rows=[]
            if ns.cmd=='saturated':
                for rd in ns.R_d:
                    s=state_from_ropelength_saturated(rd,ref.volume_m3,ref.circulation_m2_s)
                    rows.append(dict(R_d_input=rd,**asdict(s)))
                note='NOT automatically an Euler equilibrium; equal reference tube volume across shapes is assumed; radius=geometric thickness is additionally assumed.'
            else:
                for rd in ns.Rmin_d:
                    rows.append(knot_type_bounds(ref.volume_m3,rd))
                note='Bounds are conditional on independently validated knot-type minimal ropelength and shared volume; do not input arbitrary realized R as an exact minimum.'
            report=dict(version='0.1.0',status='HYPOTHESIS_DEPENDENT',note=note,rows=rows)
            dest=persist(report,ns.out,ns.cmd);csv_table(rows,Path(ns.out)/(ns.cmd+'.csv'))
        print(f'WROTE: {dest}')
        if 'gates' in report: print('GATES:',json.dumps(report['gates'],ensure_ascii=False))
        return 0
    except (ValueError,OSError,UnicodeDecodeError) as e:
        print(f'VCCR ERROR: {e}',file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(cli())
