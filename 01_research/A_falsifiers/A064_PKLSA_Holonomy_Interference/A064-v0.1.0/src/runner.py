from __future__ import annotations
import argparse
import csv
import json
import datetime as dt
from pathlib import Path
import sys
import numpy as np
from holonomy import (load_points,split_native,sha256,gauss_link,meridian,
                       hopf_pair,unlink_pair,interference_visibility,arclength_perimeter,polygon_pair_min_clearance)

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'data'


def gate(name,passed,detail,required=True):
    return dict(id=name,status=('PASS' if passed else 'FAIL') if required else ('PASS' if passed else 'UNRESOLVED'),detail=detail,required=required)


def source_catalogue():
    obj=json.loads((INPUT/'registry.json').read_text())
    targets=('knot_3.1','knot_5.2','knot_6.1','link_6.3.3')
    objects={o['geometry_id']:o for o in obj['objects'] if o['geometry_id'] in targets}
    if len(objects)!=len(targets): raise ValueError('Missing registry entries')
    return obj,objects


def run(order=4,charge=0.5,out=None,external=None):
    out=Path(out or ROOT/'outputs');out.mkdir(parents=True,exist_ok=True)
    census,objects=source_catalogue()
    release=json.loads((INPUT/'RELEASE.json').read_text())
    campaign=json.loads((INPUT/'CAMPAIGN_INDEX.json').read_text())
    records=[]; gates=[]; provenance=[]
    for name,o in sorted(objects.items()):
        path=INPUT/'native_census'/f'{name}.txt'
        observed=sha256(path)
        ok=(observed==o['sha256_xyz'])
        gates.append(gate(f'G0_SHA256_{name}',ok,{'expected':o['sha256_xyz'],'observed':observed}))
        if not ok: continue
        try:
            comps=split_native(path,o['components'])
        except Exception as exc:
            gates.append(gate(f'G0_GEOMETRY_{name}',False,str(exc)))
            continue
        gates.append(gate(f'G0_GEOMETRY_{name}',len(comps)==o['component_count'] and sum(len(c) for c in comps)==o['n_beads'],{'components':len(comps),'counts':[len(c) for c in comps]}))
        provenance.append({'geometry_id':name,'source':'PKLSA_KnotPlot_Native_Census_v0.1.2','provider_group':census['independence_group'],'coordinate_units':census['units'],'geometry_sha256':observed,'topology_identity_verified':o['topology_identity_verified'],'classification':'GEOMETRY_ONLY_NOT_PUBLICATION_READY'})
        pairs=[(i,j,comps[i],comps[j],'pair_linking') for i in range(len(comps)) for j in range(i+1,len(comps))]
        if len(comps)==1:
            pairs=[(0,1,comps[0],meridian(comps[0]),'designed_meridian_probe')]
        for i,j,a,b,kind in pairs:
            try:
                clearance=polygon_pair_min_clearance(a,b)
                scale=min(np.min(np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1)),np.min(np.linalg.norm(np.roll(b,-1,axis=0)-b,axis=1)))
                gates.append(gate(f'G0_CLEARANCE_{name}_{i}_{j}',clearance>1.e-6*scale,{'clearance_native_units':clearance,'min_segment_native_units':scale,'not_certification_of_isotopy':True}))
                v2=gauss_link(a,b,order=2)
                v4=gauss_link(a,b,order=order)
                vn=round(v4)
                minerr=abs(v4-vn)
                per=arclength_perimeter(a)
                pi,ph=interference_visibility(v4,charge)
                # Regularization is a mathematical probe; length fraction is a source scale, not SI r_c.
                minseg=min(np.min(np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1)),np.min(np.linalg.norm(np.roll(b,-1,axis=0)-b,axis=1)))
                regularized=[gauss_link(a,b,order=order,core=f*minseg) for f in (0.0,0.025,0.05)]
                rec=dict(source=name,kind=kind,component_i=i,component_j=j,n_i=len(a),n_j=len(b),order2=v2,orderN=v4,linking_integer=vn,integer_error=minerr,order_difference=abs(v2-v4),holonomy_phase_rad=ph,toy_probability=pi,core_width_fractions=[0.,.025,.05],core_regulator_holonomy=regularized,perimeter_i_native_units=per,pair_min_clearance_native_units=clearance)
                records.append(rec)
                gates.append(gate(f'G1_INTEGER_{name}_{i}_{j}',minerr<0.035,{'integer_error':minerr,'order2_orderN_difference':abs(v2-v4),'computed':v4}))
                gates.append(gate(f'G2_QUADRATURE_{name}_{i}_{j}',abs(v2-v4)<0.035,{'difference':abs(v2-v4)}))
                # Detection of invariant under rigid transform, orientation reversal, basepoint shift
                if i==0 and j==1:
                    rev=gauss_link(a,b[::-1],order=order)
                    trans=gauss_link(a+np.array([3.,4.,-1.]),b+np.array([3.,4.,-1.]),order=order)
                    shift=gauss_link(np.roll(a,3,axis=0),b,order=order)
                    invmax=max(abs(rev+v4),abs(trans-v4),abs(shift-v4))
                    gates.append(gate(f'G3_TRANSFORM_{name}',invmax<1.e-8,{'max_error':invmax}))
            except Exception as exc:
                gates.append(gate(f'G1_PAIR_{name}_{i}_{j}',False,str(exc)))
    # Numerical controls are independent synthetic geometries.
    for label,pair,expected in [('synthetic_hopf',hopf_pair(),1),('synthetic_unlink',unlink_pair(),0)]:
        a,b=pair
        val=gauss_link(a,b,order=order)
        passed=abs(abs(val)-expected)<0.025 if expected==1 else abs(val)<0.025
        gates.append(gate('GCTRL_'+label,passed,{'computed':val,'abs_expected':expected}))
        pr,phi=interference_visibility(val,charge)
        records.append({'source':label,'kind':'synthetic_control','orderN':val,'linking_integer':round(val),'holonomy_phase_rad':phi,'toy_probability':pr})
    gates.append(gate('G4_TOY_INTERFERENCE', all(abs(r['toy_probability']-(0 if abs(r['linking_integer'])%2 else 1))<0.05 for r in records) if abs(charge-.5)<1e-12 else False,{'representation_charge':charge,'interpretation':'assigned, not derived; only q=1/2 is preregistered'}))
    external_result=None
    if external:
        try:
            from production_import import evaluate_external
            external_result=evaluate_external(external,order,charge)
            qualified=len(external_result['independence_qualified_topologies'])>0
            gates.append(gate('G5_INDEPENDENT_PROVIDER',qualified,{'admitted_pklsa_0_4_cases':external_result['geometry_count'],'provider_groups_per_topology':external_result['provider_groups_per_topology'],'qualification_rule':'at least two distinct provider groups for one topology; no generated providers'},required=False))
        except Exception as exc:
            gates.append(gate('G5_EXTERNAL_IMPORT',False,{'error':str(exc)}))
    else:
        gates.append(gate('G5_INDEPENDENT_PROVIDER',False,'Single KnotPlot provider only; no independent PKLSA 0.4 qualified provider measurements',required=False))
    gates.append(gate('G6_DYNAMIC_PHASE_CONNECTION',False,'No phase connection derived from Euler/finite-core fluid dynamics; Z2 representation is assigned',required=False))
    gates.append(gate('G7_PHYSICAL_INTERFERENCE',False,'No wave evolution measured or solved; toy P is an algebraic reference only',required=False))
    gates.append(gate('G8_TRIPLE_LINK_HOLONOMY',False,'Pairwise Gauss linking is blind to Brunnian three-component linkage; requires higher-order holonomy',required=False))
    gates.append(gate('G9_FRAMEWORK_107_RUNTIME',False,'Stand-alone validation; frozen v1.0.7 runtime not executable in this container and not falsely claimed',required=False))
    gates.append(gate('G10_PUBLISHED_PKLSA_RELEASE',release.get('publication_ready_geometry_layer',False),{'version':release['e010_version'],'full_campaign_gate_pass':release['full_campaign_gate_pass'],'failed_topologies':{n:(n in campaign['failed']) for n in ('3_1','5_2','6_1','L6a4')}},required=False))
    result=dict(schema='A064-HOLONOMY-INTERFERENCE-1',version='0.1.0',created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),source_policy='source-born native snapshot; not independent and not qualified 0.4.0 production data',source_versions={'native_census':census['dataset_version'],'pklsa_release':release['e010_version'],'framework_required':'1.0.7'},physics_claim_status='UNQUALIFIED',configuration={'quadrature_order':order,'toy_representation_charge':charge,'core_widths_relative_to_min_segment':[0,.025,.05]},sources=provenance,records=records,external_pklsa_0_4=external_result,gates=gates,summary={'passed_required_gates':sum(g['required'] and g['status']=='PASS' for g in gates),'failed_required_gates':sum(g['required'] and g['status']=='FAIL' for g in gates),'unresolved_science_gates':sum(g['status']=='UNRESOLVED' for g in gates)})
    (out/'run_results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    with (out/'geometry_measurements.csv').open('w',newline='',encoding='utf-8') as f:
        keys=['source','kind','component_i','component_j','n_i','n_j','order2','orderN','linking_integer','integer_error','order_difference','holonomy_phase_rad','toy_probability']
        wr=csv.DictWriter(f,fieldnames=keys);wr.writeheader();wr.writerows([{k:r.get(k,'') for k in keys} for r in records])
    with (out/'gates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['gate','status','required','detail']);w.writerows([[g['id'],g['status'],g['required'],json.dumps(g['detail'])] for g in gates])
    (out/'PILOT_REPORT.md').write_text('# A064 v0.1.0 — Source-aware numerical pilot\n\n'+f"Required gates PASS: {result['summary']['passed_required_gates']}; FAIL: {result['summary']['failed_required_gates']}. Unresolved scientific gates: {result['summary']['unresolved_science_gates']}.\n\nThis report is not a blind run or physical SST validation. The toy Z2 charge was fixed before looking at geometry. See gate records for independent numerical checks.\n",encoding='utf-8')
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',default=str(ROOT/'outputs'))
    ap.add_argument('--order',type=int,default=4,choices=[2,4,6])
    ap.add_argument('--charge',type=float,default=.5)
    ap.add_argument('--pklsa-manifest',default=None,help='Explicit admitted PKLSA 0.4.0 carrier manifest')
    args=ap.parse_args()
    obj=run(order=args.order,charge=args.charge,out=args.out,external=args.pklsa_manifest)
    print(json.dumps(obj['summary'],indent=2));print('See',args.out)
    sys.exit(1 if obj['summary']['failed_required_gates'] else 0)

if __name__=='__main__':main()
