from __future__ import annotations
from pathlib import Path
import json,math,os,traceback
import numpy as np
from a054_state.utils import write_json,append_jsonl,sha256_file,geometry_sha256,safe_cv
from a054_state.pklsa import discover_carriers
from a054_state.geometry import rigid_transform,normalize_by_reach,resample_closed,descriptors
from a054_state.energy import energy_matrix,relative_l2,total_kernel
from a054_state.selector import relax_variational,allocate_resample
from a054_state.analysis import provider_convergence
from a054_state.commitment import compute_implementation_bundle

SOFT={
 'G3':['G1','G2'],'G4':['G3'],'G5':['G2'],'G7':['G3'],'G8':['G3','G7'],'G10':['G7'],'G11':['G3'],'G12':['G7','G8','G11'],'G22':['G3','G4','G5','G7','G8','G10','G11','G12']
}

def _out(root,cfg):p=cfg['project'];return root/f"{p['name']}_{p['version']}-outputs"
def _load_config(root,mode):
    n='certify' if mode.upper()=='CERTIFY' else ('full' if mode.upper()=='FULL' else 'basic');return json.loads((root/'configs'/f'{n}.json').read_text(encoding='utf-8'))
def _wb():return Path(os.environ.get('SST_WORKBENCH_ROOT',r'C:\workspace\projects\SST-Workbench'))
def _record(ledger,gid,status,metrics=None,reason='',**kw):
    if ledger.status(gid) is None:ledger.record(gid,status,metrics=metrics or {},reason=reason,**kw)
def _run_gate(ledger,gid,fn):
    try:
        st,metrics,reason,extra=fn();_record(ledger,gid,st,metrics,reason,**(extra or {}));return metrics
    except Exception as ex:
        _record(ledger,gid,'UNRESOLVED',{'exception':type(ex).__name__},f'{type(ex).__name__}: {ex}');return None

def _soft_caveats(ledger):
    rows=[]
    for gid,deps in SOFT.items():
        bad=[{'gate':d,'status':ledger.status(d)} for d in deps if ledger.status(d) not in ('PASS',None)]
        rows.append({'gate':gid,'soft_dependencies':deps,'caveats':bad,'interpretation_limited':bool(bad)})
    return rows

def _save_npz(path,components):
    path.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(path,**{f'component_{i}':np.asarray(c,float) for i,c in enumerate(components)})

def run_scientific_pipeline(root:Path,cfg:dict,ledger,mode:str):
    out=_out(root,cfg);out.mkdir(parents=True,exist_ok=True); config=_load_config(root,mode)
    expected=json.loads((root/'science_contract.json').read_text(encoding='utf-8')).get('implementation_commitment',{}).get('bundle_sha256');actual,impl_rows=compute_implementation_bundle(root)
    if not expected or actual!=expected:raise RuntimeError(f'Implementation commitment mismatch before G0: expected={expected} actual={actual}')
    write_json(out/'A054_IMPLEMENTATION_VERIFICATION.json',{'schema':'A054-IMPLEMENTATION-VERIFICATION-1','expected':expected,'actual':actual,'ok':True,'files':impl_rows})
    _record(ledger,'G0','PASS',{'mode':mode,'diagnostic_continuation':True},'Framework protocol and implementation commitment verified before science.')
    ctx={'discovery':None,'rows':None,'provider':None}

    def g1():
        d=discover_carriers(_wb(),{'require_e013_manifest':True,'allow_direct_e010_fallback':False});ctx['discovery']=d;ok=[e for e in d['entries'] if e.get('ok')];bad=[e for e in d['entries'] if not e.get('ok')]
        write_json(out/'E013_CAMPAIGN_BINDING.json',{'schema':'A054-E013-CAMPAIGN-BINDING-1','campaign_id':d.get('campaign_id'),'selection_authority':d.get('selection_authority'),'cross_carrier_manifest_path':d.get('manifest_path'),'cross_carrier_manifest_sha256':d.get('manifest_sha256'),'sklsa_release_id':d.get('sklsa_release_id'),'topology_availability':d.get('topology_availability',[]),'legacy_falsifier_outputs_used_as_evidence':False})
        write_json(out/'A054_SOURCE_ADMISSION.json',{'schema':'A054-SOURCE-ADMISSION-1','evaluated':len(d['entries']),'admitted':len(ok),'rejected_or_error':[{'topology_id':e.get('topology_id'),'static_seed_id':e.get('carrier',{}).get('static_seed_id'),'error':e.get('error')} for e in bad]})
        hashes=all(e.get('verified_geometry_sha256')==e.get('carrier',{}).get('geometry_sha256') for e in ok);unique=len({e['carrier'].get('static_seed_id') for e in ok})==len(ok)
        return ('PASS' if ok and not bad and hashes and unique else 'FAIL'),{'admitted':len(ok),'rejected':len(bad),'geometry_hashes_verified':hashes,'unique_static_seed_ids':unique,'e013_manifest_sha256':d.get('manifest_sha256')},'Exact E013/E011 selection and source-native bytes are required; no legacy substitute is permitted.',{}
    _run_gate(ledger,'G1',g1)

    def g2():
        t=np.linspace(0,2*np.pi,96,endpoint=False);c=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)];norm,_,_=normalize_by_reach([c]);rt=rigid_transform(norm)
        e0=energy_matrix(norm,1.0);e1=energy_matrix(rt,1.0);err=relative_l2(e0,e1)
        rr=relax_variational(norm,{**config,'max_iterations':min(2,int(config['max_iterations']))})
        monotonic=rr['final_energy']<=rr['initial_energy']+1e-9*max(1,abs(rr['initial_energy']))
        return ('PASS' if err<=1e-12 and monotonic and rr['topology_proxy']['ok'] else 'FAIL'),{'rigid_energy_rel_l2':err,'circle_energy_nonincrease':monotonic,'circle_topology_proxy_ok':rr['topology_proxy']['ok']},'Synthetic controls validate objectivity and selector mechanics only.',{}
    _run_gate(ledger,'G2',g2)

    def compute_rows():
        if ctx['rows'] is not None:return ctx['rows']
        if not ctx['discovery']:raise RuntimeError('source discovery unavailable')
        rows=[];p=out/'A054_STATE_SELECTION_RESULTS.jsonl';p.unlink(missing_ok=True)
        canddir=out/'state_candidates';canddir.mkdir(parents=True,exist_ok=True)
        for ent in ctx['discovery']['entries']:
            car=ent.get('carrier',{});base={'topology_id':ent.get('topology_id'),'static_seed_id':car.get('static_seed_id'),'carrier_id':car.get('carrier_id'),'provider_group':car.get('provider_group'),'lineage_group':car.get('lineage_group'),'e011_static_status':car.get('e011_static_status'),'source_geometry_sha256':car.get('geometry_sha256')}
            if not ent.get('ok'):
                row={**base,'error':ent.get('error','source unavailable')};rows.append(row);append_jsonl(p,row);continue
            try:
                rr=relax_variational(ent['components'],config); comps=rr.pop('components');gh=geometry_sha256(comps);fn=f"{base['topology_id']}__{base['static_seed_id']}.npz".replace('/','_');fp=canddir/fn;_save_npz(fp,comps)
                row={**base,**rr,'selected_geometry_sha256':gh,'state_file':str(fp.relative_to(out)).replace('\\','/'),'state_file_sha256':sha256_file(fp)};row['_components_for_analysis']=comps
                rows.append(row);public={k:v for k,v in row.items() if k!='_components_for_analysis'};append_jsonl(p,public)
            except Exception as ex:
                row={**base,'error':f'{type(ex).__name__}: {ex}'};rows.append(row);append_jsonl(p,row)
        ctx['rows']=rows;return rows

    def g3():
        rr=[r for r in compute_rows() if 'error' not in r]
        if not rr:return 'UNRESOLVED',{},'No carrier completed state selection.',{}
        succ=[r for r in rr if r.get('stationary') and r.get('topology_proxy',{}).get('ok') and r['final_energy']<=r['initial_energy']+1e-9*max(1,abs(r['initial_energy']))]
        red=[1-r['final_stationarity']/max((r['history'][0]['stationarity'] if r.get('history') else r['final_stationarity']),1e-30) for r in rr]
        frac=len(succ)/len(rr);st='PASS' if frac>=float(config['carrier_success_fraction_min']) else 'FAIL'
        return st,{'completed_carriers':len(rr),'stationary_topology_preserved_carriers':len(succ),'success_fraction':frac,'required_fraction':config['carrier_success_fraction_min'],'median_stationarity_reduction_fraction':float(np.median(red)) if red else None},'This gate asks whether the fixed target-free selector can actually reach stationary states; failed carriers remain in later diagnostics.',{}
    _run_gate(ledger,'G3',g3)

    def g4():
        rr=[r for r in compute_rows() if 'error' not in r and r['topology_id'] in set(config.get('confirmation_topologies',[]))]
        if not rr:return 'UNRESOLVED',{'confirmation_topologies':config.get('confirmation_topologies',[])},'No registered confirmation topology is present in this E013 profile.',{}
        succ=sum(bool(r.get('stationary') and r.get('topology_proxy',{}).get('ok')) for r in rr);frac=succ/len(rr);st='PASS' if frac>=float(config['confirmation_success_fraction_min']) else 'FAIL'
        return st,{'confirmation_carriers':len(rr),'successes':succ,'success_fraction':frac,'required_fraction':config['confirmation_success_fraction_min'],'confirmation_topologies':config.get('confirmation_topologies',[])},'Selector parameters are frozen globally and are not refit on confirmation topologies.',{}
    _run_gate(ledger,'G4',g4)

    def g5():
        from a054_state.native import build_and_import
        rr=[r for r in compute_rows() if 'error' not in r]
        if not rr:raise RuntimeError('no completed carrier for native parity')
        mod=build_and_import(root);r=rr[0];comps=r['_components_for_analysis'];py=energy_matrix(comps,1.0);cpp=np.asarray(mod.energy_matrix(comps,1.0),float);err=relative_l2(py,cpp)
        return ('PASS' if err<=1e-10 else 'FAIL'),{'relative_l2':err,'threshold':1e-10},'C++/OpenMP FP64 is certification authority only for the shared energy kernel.',{'requested_backend':'cpp-openmp-fp64','actual_backend':'cpp-pybind11-fp64','authority':'CERTIFICATION'}
    _run_gate(ledger,'G5',g5)

    def g6():
        from framework_bootstrap import resolve_framework_root
        fr=resolve_framework_root();files=[fr/'build'/'BACKEND_SELFTEST.json',fr/'build'/'DD32_PARITY_SMOKE.json'];present=[str(p) for p in files if p.is_file()]
        if not present:return 'UNRESOLVED',{'screening_evidence_files':[]},'No framework GPU/DD32 screening evidence is present; CPU science remains authoritative.',{'requested_backend':'sycl-dd32','actual_backend':None,'authority':'SCREENING_ONLY'}
        return 'PASS',{'screening_evidence_files':present},'GPU/DD32 remains screening-only.',{'requested_backend':'sycl-dd32','actual_backend':'framework-screening-evidence','authority':'SCREENING_ONLY'}
    _run_gate(ledger,'G6',g6)

    def provider_details():
        if ctx['provider'] is None:
            rr=[r for r in compute_rows() if 'error' not in r];ctx['provider']=provider_convergence(rr,config)
            write_json(out/'A054_PROVIDER_CONVERGENCE.json',{'schema':'A054-PROVIDER-CONVERGENCE-1','details':ctx['provider']})
        return ctx['provider']

    def g7():
        det=provider_details();eligible=[x for x in det.values() if x.get('eligible')];passing=[x for x in eligible if x.get('provider_converged')]
        if not eligible:return 'UNRESOLVED',{'eligible_topologies':0},'BASIC may contain only one provider anchor per topology.',{}
        frac=len(passing)/len(eligible);st='PASS' if len(eligible)>=2 and frac>=float(config['provider_converged_fraction_min']) else 'FAIL'
        return st,{'eligible_topologies':len(eligible),'provider_converged_topologies':len(passing),'pass_fraction':frac,'required_fraction':config['provider_converged_fraction_min'],'details':det},'Provider convergence requires stationary endpoints plus energy/ropelength/writhe agreement; provider identity is never pooled away.',{}
    _run_gate(ledger,'G7',g7)

    def g8():
        rr=[r for r in compute_rows() if 'error' not in r and r.get('stationary')];
        if not rr:return 'UNRESOLVED',{'stationary_endpoints':0},'No stationary endpoint exists for stability qualification.',{}
        stable=[r for r in rr if r.get('stable_candidate') and r.get('ringdown_bounded')];frac=len(stable)/len(rr);st='PASS' if frac>=float(config['stable_fraction_min']) else 'FAIL'
        return st,{'stationary_endpoints':len(rr),'stable_ringdown_bounded_endpoints':len(stable),'stable_fraction':frac,'required_fraction':config['stable_fraction_min'],'min_hessian_eigenvalues':{r['static_seed_id']:(min(r['hessian_eigenvalues']) if r.get('hessian_eigenvalues') else None) for r in rr}},'Stationarity is necessary but not sufficient; stability requires a nonnegative Hessian within tolerance and bounded nonlinear reduced ringdown.',{}
    _run_gate(ledger,'G8',g8)

    def g10():
        det=provider_details();sens=[x for x in det.values() if x.get('eligible') and x.get('source_energy_cv') is not None and x['source_energy_cv']>float(config['sensitive_source_energy_cv_min'])]
        if not sens:return 'UNRESOLVED',{'source_sensitive_topologies':0},'No replicated topology exceeds the preregistered source-energy sensitivity threshold.',{}
        repaired=[x for x in sens if x.get('endpoint_energy_cv') is not None and x['endpoint_energy_cv']<=float(config['provider_energy_cv_max']) and (x.get('provider_cv_collapse_fraction') or -1)>=0.5];frac=len(repaired)/len(sens);st='PASS' if frac>=float(config['sensitive_repair_fraction_min']) else 'FAIL'
        return st,{'source_sensitive_topologies':len(sens),'repaired_topologies':len(repaired),'repair_fraction':frac,'required_fraction':config['sensitive_repair_fraction_min'],'details':sens},'This is the direct test of whether state selection collapses provider-dependent source energies toward a common topology state.',{}
    _run_gate(ledger,'G10',g10)

    def g11():
        rr=[r for r in compute_rows() if 'error' not in r]
        if not rr:return 'UNRESOLVED',{},'No path completed.',{}
        good=[r for r in rr if r.get('topology_proxy',{}).get('ok')];st='PASS' if len(good)==len(rr) else 'FAIL'
        return st,{'completed_paths':len(rr),'topology_proxy_preserved_paths':len(good),'violations':len(rr)-len(good)},'Continuous small-step evolution plus clearance and linking-drift checks is a topology-preservation proxy, not a complete knot-polynomial proof.',{}
    _run_gate(ledger,'G11',g11)

    def g12():
        det=provider_details();rr=[r for r in compute_rows() if 'error' not in r];eligible_t=[]
        for t,d in det.items():
            rs=[r for r in rr if r['topology_id']==t]
            if d.get('eligible') and d.get('provider_converged') and rs and all(r.get('stable_candidate') and r.get('ringdown_bounded') for r in rs):eligible_t.append(t)
        hand=out/'STATE_SELECTED_CARRIERS.jsonl';hand.unlink(missing_ok=True);entries=[]
        for r in rr:
            if r['topology_id'] not in eligible_t:continue
            row={k:r.get(k) for k in ['topology_id','static_seed_id','carrier_id','provider_group','lineage_group','e011_static_status','source_geometry_sha256','selected_geometry_sha256','state_file','state_file_sha256','final_energy','final_stationarity']};row['selection_authority']='A054-v0.5.0 E013 provider-convergent stable state';entries.append(row);append_jsonl(hand,row)
        files=[{'path':r['state_file'],'sha256':r['state_file_sha256']} for r in entries]
        write_json(out/'A054_STATE_SELECTION_HANDOFF.json',{'schema':'A054-STATE-SELECTION-HANDOFF-1','eligible_topologies':eligible_t,'entry_count':len(entries),'entries':entries,'state_files':files,'legacy_outputs_used':False})
        st='PASS' if eligible_t else 'FAIL'
        return st,{'eligible_topologies':eligible_t,'eligible_topology_count':len(eligible_t),'handoff_entries':len(entries)},'Only provider-converged, stationary, locally stable and ringdown-bounded states are promoted to a future A057 state-selected handoff.',{}
    _run_gate(ledger,'G12',g12)

    def g22():
        s={g:ledger.status(g) for g in ['G3','G4','G5','G7','G8','G10','G11','G12']}
        if s['G7']=='PASS' and s['G8']=='PASS' and s['G12']=='PASS':cl='PROVIDER_CONVERGENT_STABLE_STATE_SELECTION_SUPPORTED';st='PASS'
        elif s['G7']=='PASS' and s['G8']!='PASS':cl='PROVIDER_CONVERGENCE_WITHOUT_STABILITY';st='FAIL'
        elif s['G3']=='PASS' and s['G7']!='PASS':cl='STATE_SELECTION_NOT_PROVIDER_UNIVERSAL';st='FAIL'
        else:cl='STATE_SELECTION_NOT_ESTABLISHED';st='FAIL'
        write_json(out/'A054_CLASSIFICATION.json',{'schema':'A054-CLASSIFICATION-1','classification':cl,'gate_statuses':s})
        return st,{'classification':cl,'gate_statuses':s},'Overall classification is blind to mass targets and old falsifier results.',{}
    _run_gate(ledger,'G22',g22)

    # Remove private in-memory components before public dependency output.
    write_json(out/'DEPENDENCY_CAVEATS.json',{'schema':'A054-SOFT-DEPENDENCIES-1','rows':_soft_caveats(ledger)})
    return {'schema':'SST-BACKEND-MANIFEST-2','python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'REFERENCE'},'cpp_certification':{'gate_status':ledger.status('G5'),'authority':'CERTIFICATION'},'gpu_screening':{'gate_status':ledger.status('G6'),'authority':'SCREENING_ONLY'},'diagnostic_continuation':True,'scientific_gate_dependencies':'soft; see DEPENDENCY_CAVEATS.json'}
