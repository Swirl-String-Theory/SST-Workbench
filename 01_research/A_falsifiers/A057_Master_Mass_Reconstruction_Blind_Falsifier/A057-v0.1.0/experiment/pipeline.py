from __future__ import annotations
from pathlib import Path
import json,os,traceback,math
import numpy as np
from master_mass.utils import write_json,append_jsonl,relerr
from master_mass.pklsa import discover_carriers
from master_mass.geometry import resample_closed,normalize_by_reach,descriptors,rigid_transform
from master_mass.energy import energy_matrix,total_kernel,decomposition,coherence_metrics,relative_l2
from master_mass.dynamics import potential_factory,gradient_hessian,mass_matrix,spectrum,linear_trajectory,fft_peak,nonlinear_1d_trajectory
from master_mass.analysis import summarize_by_topology,variance_discriminator,model_competition,split_label
from master_mass.constants import SST
from master_mass.volume_energy import tube_energy_kernel

SOFT={
 'G3':['G1','G2'],'G4':['G1','G3'],'G5':['G2'],'G7':['G1'],'G8':['G1','G3'],'G10':['G3'],'G11':['G10'],'G12':['G3','G10'],'G13':['G12'],'G14':['G13','G7'],'G15':['G3'],'G16':['G8','G13','G15'],'G17':['G3'],'G18':['G15','G16'],'G19':['G17'],'G20':['G3','G12'],'G21':['G7','G14'],'G22':['G3','G7','G8','G10','G11','G12','G13','G15','G16','G17','G18','G19','G20','G21']}

def _out(root,cfg):p=cfg['project'];return root/f"{p['name']}_{p['version']}-outputs"
def _load_config(root,mode):
    name='certify' if mode.upper()=='CERTIFY' else ('full' if mode.upper()=='FULL' else 'basic')
    return json.loads((root/'configs'/f'{name}.json').read_text(encoding='utf-8'))
def _wb():return Path(os.environ.get('SST_WORKBENCH_ROOT',r'C:\workspace\projects\SST-Workbench'))

def _record(ledger,gid,status,metrics=None,reason='',**kw):
    if ledger.status(gid) is None:ledger.record(gid,status,metrics=metrics or {},reason=reason,**kw)

def _run_gate(ledger,gid,fn):
    try:
        status,metrics,reason,extra=fn();_record(ledger,gid,status,metrics,reason,**(extra or {}));return metrics
    except Exception as ex:
        _record(ledger,gid,'UNRESOLVED',{"exception":type(ex).__name__},f'{type(ex).__name__}: {ex}')
        return None

def _soft_caveats(ledger):
    rows=[]
    for gid,deps in SOFT.items():
        bad=[{"gate":d,"status":ledger.status(d)} for d in deps if ledger.status(d) not in ('PASS',None)]
        rows.append({"gate":gid,"soft_dependencies":deps,"caveats":bad,"interpretation_limited":bool(bad)})
    return rows

def _sample_rows(entries,config):
    rows=[];reslist=config['resolutions'];cores=config['core_scales']
    for ent in entries:
        if not ent.get('ok'):continue
        comps0=ent['components'];top=ent['topology_id'];car=ent['carrier'];group=car.get('independence_group') or car.get('provider_group') or car.get('source_family')
        for n in reslist:
            # preserve relative component length allocation
            Ls=[np.linalg.norm(np.roll(np.asarray(c),-1,axis=0)-np.asarray(c),axis=1).sum() for c in comps0];Lt=sum(Ls)
            comps=[resample_closed(c,max(24,int(round(n*L/Lt)))) for c,L in zip(comps0,Ls)]
            norm,scale,rd=normalize_by_reach(comps);geo=descriptors(norm)
            for core in cores:
                E=energy_matrix(norm,core=core);row={"topology_id":top,"carrier_id":car.get('carrier_id'),"independence_group":group,"provider_group":car.get('provider_group'),"source_family":car.get('source_family'),"lineage_group":car.get('lineage_group'),"resolution":n,"core_scale":core,"reach_source_units":scale,"geometry":geo,"topology_features":ent.get("topology_features",{}),"energy_kernel":total_kernel(E),"decomposition":decomposition(E),"coherence":coherence_metrics(E)};rows.append(row)
    return rows

def _finest_nominal(rows,config):
    n=max(config['resolutions']);core=min(config['core_scales'],key=lambda x:abs(x-1.0));return [r for r in rows if r['resolution']==n and abs(r['core_scale']-core)<1e-12]

def _implementation_bundle(root: Path):
    import hashlib
    pats=['experiment/**/*.py','master_mass/**/*.py','native_ext/*.cpp','native_ext/*.hpp','native_ext/*.py','configs/*.json','requirements.txt','data/HISTORICAL_MODEL_PUBLIC.json','post_reveal_analysis.py','tests/*.py']
    files=[]
    for pat in pats:
        files.extend([p for p in root.glob(pat) if p.is_file()])
    rows=[]
    for p in sorted(set(files)):
        rows.append({'path':p.relative_to(root).as_posix(),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    payload={'files':rows};raw=(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode('utf-8')
    return hashlib.sha256(raw).hexdigest(),rows

def run_scientific_pipeline(root: Path,cfg: dict,ledger,mode: str):
    out=_out(root,cfg);out.mkdir(parents=True,exist_ok=True); config=_load_config(root,mode)
    expected=json.loads((root/'science_contract.json').read_text(encoding='utf-8')).get('implementation_commitment',{}).get('bundle_sha256')
    actual,impl_rows=_implementation_bundle(root)
    if not expected or actual!=expected:
        raise RuntimeError(f'Implementation commitment mismatch before G0: expected={expected} actual={actual}')
    write_json(out/'A057_IMPLEMENTATION_VERIFICATION.json',{'schema':'A057-IMPLEMENTATION-VERIFICATION-1','expected':expected,'actual':actual,'ok':True,'files':impl_rows})
    _record(ledger,'G0','PASS',{"mode":mode,"diagnostic_continuation":True},'Frozen protocol was verified by framework before scientific entry.')
    context={"config":config,"discovery":None,"rows":[],"nominal":[],"summary":{},"dynamic":[]}

    def g1():
        d=discover_carriers(_wb(),config);context['discovery']=d;ok=[e for e in d['entries'] if e.get('ok')];bad=[e for e in d['entries'] if not e.get('ok')]
        write_json(out/'A057_SOURCE_ADMISSION.json',{"release":d['release'],"e010":d['e010'],"evaluated":len(d['entries']),"admitted":len(ok),"rejected_or_error":[{k:e.get(k) for k in ('topology_id','error')} for e in bad]})
        groups={str((e['carrier'].get('independence_group') or e['carrier'].get('provider_group') or e['carrier'].get('source_family'))) for e in ok}
        st='PASS' if ok else 'FAIL';return st,{"admitted":len(ok),"not_loaded":len(bad),"independence_groups":len(groups),"release_source_native_mode":bool(d['release'].get('source_native_mode'))},'Carrier-level admission is independent of the aggregate all-topology release flag.',{}
    _run_gate(ledger,'G1',g1)

    def g2():
        # synthetic circle: rotation invariance and SI scales
        t=np.linspace(0,2*np.pi,96,endpoint=False);c=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)];base=[c];rt=rigid_transform(base)
        E0=energy_matrix(base,1.0);E1=energy_matrix(rt,1.0);err=relative_l2(E0,E1)
        mass_bg=SST.line_mass_scale(SST.rho_f);mass_core=SST.line_mass_scale(SST.rho_core)
        ok=err<=1e-12 and mass_bg>0 and mass_core>mass_bg
        return ('PASS' if ok else 'FAIL'),{"rigid_energy_rel_l2":err,"circulation_m2_s":SST.circulation,"background_line_mass_scale_kg":mass_bg,"core_line_mass_scale_kg":mass_core},'Synthetic controls validate implementation only, not the physical hypothesis.',{}
    _run_gate(ledger,'G2',g2)

    def g3():
        if not context['discovery']:raise RuntimeError('source discovery unavailable')
        rows=_sample_rows(context['discovery']['entries'],config);context['rows']=rows
        p=out/'A057_CARRIER_RESULTS.jsonl';p.unlink(missing_ok=True)
        for r in rows:append_jsonl(p,r)
        nom=_finest_nominal(rows,config);context['nominal']=nom;summ=summarize_by_topology(nom);context['summary']=summ;disc=variance_discriminator(summ);write_json(out/'A057_TOPOLOGY_SUMMARY.json',{"summary":summ,"variance_discriminator":disc})
        # convergence: compare two finest resolutions at nominal core for matched carrier
        core=min(config['core_scales'],key=lambda x:abs(x-1));ns=sorted(config['resolutions']);errs=[]
        if len(ns)>=2:
            by={}
            for r in rows:
                if abs(r['core_scale']-core)<1e-12:by.setdefault((r['topology_id'],r['carrier_id']),{})[r['resolution']]=r['energy_kernel']
            for x in by.values():
                if ns[-1] in x and ns[-2] in x:errs.append(relerr(x[ns[-1]],x[ns[-2]]))
        med=float(np.median(errs)) if errs else None;stable=(disc.get('between_to_within') or 0)>1.0;conv=med is not None and med<=0.08
        st='PASS' if stable and conv and len(summ)>=2 else 'FAIL'
        return st,{"topology_count":len(summ),"nominal_carriers":len(nom),"median_two_finest_energy_rel_change":med,"between_to_within":disc.get('between_to_within'),"convergence_threshold":0.08},'PASS requires both numerical convergence and stronger between-topology than within-topology spread.',{}
    _run_gate(ledger,'G3',g3)

    def g4():
        summ=context['summary'];conf=[t for t in summ if split_label(t)=='confirmation'];disc=[t for t in summ if split_label(t)=='discovery'];
        if not conf or not disc:return 'UNRESOLVED',{"discovery_topologies":len(disc),"confirmation_topologies":len(conf)},'Insufficient deterministic split support.',{}
        cvs=[summ[t].get('cv') for t in conf if summ[t].get('cv') is not None];med=float(np.median(cvs)) if cvs else None;st='PASS' if med is not None and med<=0.15 else 'FAIL'
        return st,{"discovery_topologies":len(disc),"confirmation_topologies":len(conf),"confirmation_median_within_cv":med,"threshold":0.15},'This is target-free carrier confirmation, not observed-mass confirmation.',{}
    _run_gate(ledger,'G4',g4)

    def g5():
        from master_mass.native import build_and_import
        if not context['nominal']:raise RuntimeError('no carrier available for native parity')
        mod=build_and_import(root);r=context['nominal'][0];ent=next(e for e in context['discovery']['entries'] if e.get('ok') and e['topology_id']==r['topology_id'] and e['carrier'].get('carrier_id')==r['carrier_id'])
        Ls=[np.linalg.norm(np.roll(np.asarray(c),-1,axis=0)-np.asarray(c),axis=1).sum() for c in ent['components']];Lt=sum(Ls);n=max(config['resolutions']);comps=[resample_closed(c,max(24,int(round(n*L/Lt)))) for c,L in zip(ent['components'],Ls)];norm,_,_=normalize_by_reach(comps)
        py=energy_matrix(norm,1.0);cpp=np.asarray(mod.energy_matrix(norm,1.0),float);err=relative_l2(py,cpp);st='PASS' if err<=1e-10 else 'FAIL';return st,{"relative_l2":err,"threshold":1e-10},'Native lane is certification authority only when this gate passes.',{"requested_backend":"cpp-openmp-fp64","actual_backend":"cpp-pybind11-fp64","authority":"CERTIFICATION"}
    _run_gate(ledger,'G5',g5)

    def g6():
        # v1.0.6 intentionally keeps SYCL/DD32 screening separate. Inspect frozen framework selftest evidence when present.
        from framework_bootstrap import resolve_framework_root
        framework_root=resolve_framework_root()
        files=[framework_root/'build'/'BACKEND_SELFTEST.json',framework_root/'build'/'DD32_PARITY_SMOKE.json']
        present=[str(p) for p in files if p.is_file()]
        if not present:return 'UNRESOLVED',{"screening_evidence_files":[]},'No current framework GPU/DD32 selftest evidence is present; CPU science continues.',{"requested_backend":"sycl-dd32","actual_backend":None,"authority":"SCREENING_ONLY"}
        return 'PASS',{"screening_evidence_files":present},'Framework screening evidence exists; no GPU result is promoted to scientific certification.',{"requested_backend":"sycl-dd32","actual_backend":"framework-screening-evidence","authority":"SCREENING_ONLY"}
    _run_gate(ledger,'G6',g6)

    def g7():
        nom=context['nominal'];by={}
        for r in nom:by.setdefault(r['topology_id'],[]).append(r)
        eligible=0;passn=0;details={}
        for t,rs in by.items():
            groups={str(r.get('independence_group')) for r in rs if r.get('independence_group')}
            if len(groups)>=2:
                eligible+=1;vals=[r['energy_kernel'] for r in rs];cv=float(np.std(vals,ddof=1)/max(abs(np.mean(vals)),1e-30)) if len(vals)>1 else None;details[t]={"groups":len(groups),"cv":cv};passn+=int(cv is not None and cv<=0.15)
        st='PASS' if eligible>=2 and passn/eligible>=0.6 else ('UNRESOLVED' if eligible==0 else 'FAIL')
        return st,{"eligible_topologies":eligible,"passing_topologies":passn,"pass_fraction":passn/eligible if eligible else None,"details":details},'Independent carrier groups are never treated as discretization levels.',{}
    _run_gate(ledger,'G7',g7)

    def g8():
        links=[r for r in context['nominal'] if r['geometry'].get('component_count',1)>1]
        closure=max([r['decomposition']['closure_error'] for r in links],default=0.0)
        finite=all(all(np.isfinite(r['coherence']['eigenvalues'])) for r in links) if links else True
        # Independent volumetric core-tube quadrature on a bounded subset.  This is
        # intentionally diagnostic because it samples only the tube support, not all space.
        tube=[];seen=set()
        for r in context['nominal']:
            if r['topology_id'] in seen: continue
            if len(seen)>=int(config.get('tube_topology_limit',8)): break
            ent=next((e for e in context['discovery']['entries'] if e.get('ok') and e['topology_id']==r['topology_id'] and e['carrier'].get('carrier_id')==r['carrier_id']),None)
            if ent is None: continue
            try:
                n=min(max(config['resolutions']),144);Ls=[np.linalg.norm(np.roll(np.asarray(c),-1,axis=0)-np.asarray(c),axis=1).sum() for c in ent['components']];Lt=sum(Ls);comps=[resample_closed(c,max(24,int(round(n*L/Lt)))) for c,L in zip(ent['components'],Ls)];norm,_,_=normalize_by_reach(comps)
                te,meta=tube_energy_kernel(norm,1.0,int(config.get('tube_radial_bins',2)),int(config.get('tube_angular_bins',8)))
                tube.append({'topology_id':r['topology_id'],'carrier_id':r['carrier_id'],'line_kernel':r['energy_kernel'],'tube_kernel':te,'meta':meta});seen.add(r['topology_id'])
            except Exception as ex:tube.append({'topology_id':r['topology_id'],'carrier_id':r['carrier_id'],'error':f'{type(ex).__name__}: {ex}'});seen.add(r['topology_id'])
        write_json(out/'A057_TUBE_ENERGY_DIAGNOSTIC.json',{'schema':'A057-TUBE-ENERGY-1','rows':tube})
        pairs=[x for x in tube if x.get('tube_kernel') is not None and x['tube_kernel']>0 and x['line_kernel']>0]
        corr=float(np.corrcoef([[math.log(x['line_kernel']) for x in pairs],[math.log(x['tube_kernel']) for x in pairs]])[0,1]) if len(pairs)>=3 else None
        multistatus=(closure<=1e-12 and finite) if links else True
        tubestatus=(corr is not None and corr>=0.6) if len(pairs)>=3 else None
        if links and not multistatus: st='FAIL'
        elif tubestatus is False: st='FAIL'
        elif links or tubestatus is not None: st='PASS'
        else: st='UNRESOLVED'
        return st,{"multicomponent_carriers":len(links),"max_energy_decomposition_closure_error":closure if links else None,"finite_coherence_spectra":finite if links else None,"tube_energy_cases":len(pairs),"line_vs_core_tube_log_correlation":corr,"tube_correlation_threshold":0.6},'The core-tube quadrature is an independent reduced diagnostic and does not claim to integrate the complete exterior velocity field.',{}

    _run_gate(ledger,'G8',g8)

    # Dynamic lanes, deliberately independent of G3/G7 status.
    def dynamic_all():
        nom=context['nominal'];by={}
        for r in nom:by.setdefault(r['topology_id'],[]).append(r)
        selected=[]
        for t in sorted(by):
            selected.extend(by[t][:int(config['dynamic_carriers_per_topology'])])
            if len({x['topology_id'] for x in selected})>=int(config['dynamic_topology_limit']):break
        results=[]
        for r in selected:
            try:
                ent=next(e for e in context['discovery']['entries'] if e.get('ok') and e['topology_id']==r['topology_id'] and e['carrier'].get('carrier_id')==r['carrier_id'])
                n=max(config['resolutions']);Ls=[np.linalg.norm(np.roll(np.asarray(c),-1,axis=0)-np.asarray(c),axis=1).sum() for c in ent['components']];Lt=sum(Ls);comps=[resample_closed(c,max(24,int(round(n*L/Lt)))) for c,L in zip(ent['components'],Ls)];norm,_,_=normalize_by_reach(comps)
                U,B,offs=potential_factory(norm,1.0,int(config['basis_modes']));d=len(B);eps=float(config['perturb_eps']);u0,g,K=gradient_hessian(U,d,eps);M=mass_matrix(d,max(sum(r['geometry'].get('ropelength_proxy',1) for _ in [0])/max(d,1),1e-6));J,lam,freq=spectrum(M,K)
                # direct linear integration along first eigenvector of symmetrized generalized stiffness when possible
                w,V=np.linalg.eigh(np.linalg.solve(M,K));pos=np.where(w>1e-9)[0];ring=None
                if len(pos):
                    idx=pos[0];q0=V[:,idx]*0.01;expected=float(np.sqrt(w[idx]));period=2*np.pi/max(expected,1e-12);dt=min(float(config['trajectory_dt']),period/80.0);steps=max(int(config['trajectory_steps']),min(2048,int(math.ceil(10.0*period/dt))));traj=linear_trajectory(M,K,q0,dt,steps);ring=fft_peak(traj@V[:,idx],dt)
                ratio=freq[1]/freq[0] if len(freq)>=2 and freq[0]>0 else None
                results.append({"topology_id":r['topology_id'],"carrier_id":r['carrier_id'],"d":d,"U0":u0,"gradient_norm":float(np.linalg.norm(g)),"hessian_symmetry_rel":float(np.linalg.norm(K-K.T)/max(np.linalg.norm(K),1e-30)),"hessian_eigenvalues":np.linalg.eigvalsh(.5*(K+K.T)).tolist(),"jacobian_eigenvalues":[[float(z.real),float(z.imag)] for z in lam],"frequencies":freq,"ratio21":ratio,"ringdown_peak":ring,"ringdown_expected":float(np.sqrt(w[pos[0]])) if len(pos) else None})
            except Exception as ex:results.append({"topology_id":r['topology_id'],"carrier_id":r['carrier_id'],"error":f'{type(ex).__name__}: {ex}'})
        context['dynamic']=results;p=out/'A057_DYNAMIC_RESULTS.jsonl';p.unlink(missing_ok=True)
        for x in results:append_jsonl(p,x)
        return results
    dyn_cache={}
    def dyn():
        if 'x' not in dyn_cache:dyn_cache['x']=dynamic_all()
        return dyn_cache['x']

    def g10():
        rr=[x for x in dyn() if 'error' not in x];
        if not rr:return 'UNRESOLVED',{},'No dynamic carrier completed.',{}
        vals=[]
        # stationarity proxy is gradient/U scale; full trajectory EL tested on 1-D projection in G11
        for x in rr:vals.append(x['gradient_norm']/max(abs(x['U0']),1e-12))
        med=float(np.median(vals));st='PASS' if med<=0.5 else 'FAIL';return st,{"median_stationarity_gradient_over_energy":med,"threshold":0.5,"dynamic_carriers":len(rr)},'A FAIL marks the base carriers as nonstationary under this reduced energy; Hessian/Jacobian diagnostics still run with a caveat.',{}
    _run_gate(ledger,'G10',g10)

    def g11():
        if not context['nominal'] or not context['discovery']:return 'UNRESOLVED',{},'No geometry available.',{}
        # one-dimensional actual nonlinear potential on first dynamic carrier
        r=context['nominal'][0];ent=next(e for e in context['discovery']['entries'] if e.get('ok') and e['topology_id']==r['topology_id'] and e['carrier'].get('carrier_id')==r['carrier_id']);n=min(max(config['resolutions']),128);Ls=[np.linalg.norm(np.roll(np.asarray(c),-1,axis=0)-np.asarray(c),axis=1).sum() for c in ent['components']];Lt=sum(Ls);comps=[resample_closed(c,max(24,int(round(n*L/Lt)))) for c,L in zip(ent['components'],Ls)];norm,_,_=normalize_by_reach(comps);U,B,offs=potential_factory(norm,1.0,1)
        # project first basis only
        def U1(q):
            qq=np.zeros(len(B));qq[0]=float(np.asarray(q).ravel()[0]);return U(qq)
        tr=nonlinear_1d_trajectory(U1,1.0,1e-4,0.01,float(config['trajectory_dt']),int(config['trajectory_steps']));H=tr[:,2];drift=float((H.max()-H.min())/max(abs(H.mean()),1e-30));# EL residual qdd + grad estimated from stored acceleration+grad
        el=float(np.sqrt(np.mean((tr[:,3]+tr[:,4])**2))/max(np.sqrt(np.mean(tr[:,4]**2)),1e-30));st='PASS' if drift<=0.03 and el<=1e-8 else 'FAIL'
        return st,{"hamiltonian_peak_to_peak_relative_drift":drift,"euler_lagrange_relative_residual":el,"drift_threshold":0.03,"el_threshold":1e-8},'The actual nonlinear reduced one-mode potential is used, not a target-fitted oscillator.',{}
    _run_gate(ledger,'G11',g11)

    def g12():
        rr=[x for x in dyn() if 'error' not in x]
        if not rr:return 'UNRESOLVED',{},'No Hessian completed.',{}
        sym=max(x['hessian_symmetry_rel'] for x in rr);stationary=sum((x['gradient_norm']/max(abs(x['U0']),1e-12))<=0.5 for x in rr)/len(rr);st='PASS' if sym<=1e-10 and stationary>=0.5 else 'FAIL'
        return st,{"max_hessian_symmetry_relative":sym,"stationary_fraction":stationary,"dynamic_carriers":len(rr)},'Spectra from nonstationary carriers remain diagnostic only.',{}
    _run_gate(ledger,'G12',g12)

    def g13():
        rr=[x for x in dyn() if 'error' not in x and x.get('ringdown_peak') and x.get('ringdown_expected')]
        if not rr:return 'UNRESOLVED',{},'No positive oscillatory mode resolved for direct comparison.',{}
        errs=[relerr(x['ringdown_peak'],x['ringdown_expected']) for x in rr];med=float(np.median(errs));st='PASS' if med<=0.25 else 'FAIL';return st,{"comparisons":len(errs),"median_ringdown_frequency_relative_error":med,"threshold":0.25},'Finite-duration FFT resolution is included in the intentionally loose preregistered diagnostic threshold.',{}
    _run_gate(ledger,'G13',g13)

    def g14():
        rr=[x for x in dyn() if x.get('ratio21') is not None];by={}
        for x in rr:by.setdefault(x['topology_id'],[]).append(x['ratio21'])
        cvs=[]
        for v in by.values():
            if len(v)>1 and abs(np.mean(v))>0:cvs.append(float(np.std(v,ddof=1)/abs(np.mean(v))))
        if not cvs:return 'UNRESOLVED',{"ratio_topologies":len(by)},'Insufficient repeated dynamic carriers per topology for ratio-stability test.',{}
        med=float(np.median(cvs));st='PASS' if med<=0.15 else 'FAIL';return st,{"ratio_topologies":len(by),"median_within_topology_ratio_cv":med,"threshold":0.15,"protected_target_used":False},'No protected historical ratio is available to this calculation.',{}
    _run_gate(ledger,'G14',g14)

    def g15():
        mc=model_competition(context['summary']);write_json(out/'A057_MODEL_COMPETITION.json',mc);valid=[(k,v) for k,v in mc.items() if v.get('holdout_log_rmse') is not None]
        if not valid:return 'UNRESOLVED',{"models":list(mc)},'Insufficient topology holdout for model comparison.',{}
        best=min(valid,key=lambda kv:kv[1]['holdout_log_rmse']);return 'PASS',{"best_model":best[0],"best_holdout_log_rmse":best[1]['holdout_log_rmse'],"models":{k:v.get('holdout_log_rmse') for k,v in valid}},'PASS means the target-free surrogate competition was evaluable; it is not a mass-closure PASS.',{}
    _run_gate(ledger,'G15',g15)

    def g16():
        mc=json.loads((out/'A057_MODEL_COMPETITION.json').read_text()) if (out/'A057_MODEL_COMPETITION.json').is_file() else model_competition(context['summary']);b=mc.get('length_only',{}).get('holdout_log_rmse');g=mc.get('geometry3',{}).get('holdout_log_rmse')
        # spectral enhancement evaluated only for topologies with dynamic results, using a simple rank correlation diagnostic
        dmean={}
        for x in dyn():
            if x.get('ratio21') is not None:dmean.setdefault(x['topology_id'],[]).append(x['ratio21'])
        pairs=[]
        for t,v in dmean.items():
            if t in context['summary'] and context['summary'][t].get('mean') and v:pairs.append((math.log(context['summary'][t]['mean']),float(np.mean(v))))
        corr=float(np.corrcoef(np.array(pairs).T)[0,1]) if len(pairs)>=3 else None
        if b is None or g is None:return 'UNRESOLVED',{"spectral_pairs":len(pairs)},'Energy surrogate comparison incomplete.',{}
        improvement=(b-g)/max(b,1e-30);st='PASS' if improvement>=0.05 or (corr is not None and abs(corr)>=0.4) else 'FAIL';return st,{"geometry_improvement_fraction":improvement,"required_improvement":0.05,"energy_vs_ratio_correlation":corr,"spectral_pairs":len(pairs)},'Complexity is justified only by protected-holdout improvement or a preregistered strong target-free association.',{}
    _run_gate(ledger,'G16',g16)

    def g17():
        summ=context['summary'];pred={"schema":"A057-PREDICTIONS-FROZEN-1","blind":True,"target_values_used":False,"topologies":{},"anonymous_composites":{}}
        for t,v in summ.items():
            if v.get('mean') is not None:pred['topologies'][t]={"lambda_energy":v['mean'],"within_cv":v.get('cv'),"split":split_label(t),"si_mass_background_kg":SST.line_mass_scale(SST.rho_f)*v['mean'],"si_mass_core_kg":SST.line_mass_scale(SST.rho_core)*v['mean'],"si_mass_background_clock_kg":SST.line_mass_scale(SST.rho_f)*v['mean']*SST.clock_impedance,"si_mass_core_clock_kg":SST.line_mass_scale(SST.rho_core)*v['mean']*SST.clock_impedance}
        for name,weights in {"assembly_A":{"5_2":2,"6_1":1},"assembly_B":{"5_2":1,"6_1":2}}.items():
            if all(k in pred['topologies'] for k in weights):
                lam=sum(w*pred['topologies'][k]['lambda_energy'] for k,w in weights.items());pred['anonymous_composites'][name]={"weights":weights,"additive_lambda":lam,"si_mass_background_kg":SST.line_mass_scale(SST.rho_f)*lam,"si_mass_core_kg":SST.line_mass_scale(SST.rho_core)*lam,"si_mass_background_clock_kg":SST.line_mass_scale(SST.rho_f)*lam*SST.clock_impedance,"si_mass_core_clock_kg":SST.line_mass_scale(SST.rho_core)*lam*SST.clock_impedance}
        write_json(out/'PREDICTIONS_FROZEN.json',pred);st='PASS' if len(pred['topologies'])>=3 else 'FAIL';return st,{"frozen_topologies":len(pred['topologies']),"anonymous_composites":len(pred['anonymous_composites']),"target_values_used":False},'The table is complete before protected comparison; reveal may only consume entries already present here.',{}
    _run_gate(ledger,'G17',g17)

    def g18():
        mc=json.loads((out/'A057_MODEL_COMPETITION.json').read_text()) if (out/'A057_MODEL_COMPETITION.json').is_file() else {};vals=[v.get('holdout_log_rmse') for v in mc.values() if v.get('holdout_log_rmse') is not None]
        if not vals:return 'UNRESOLVED',{},'No protected topology holdout predictions.',{}
        best=min(vals);st='PASS' if best<=0.5 else 'FAIL';return st,{"best_holdout_log_rmse":best,"threshold":0.5},'This is an internal finite-core-energy holdout, not an observed-mass holdout.',{}
    _run_gate(ledger,'G18',g18)

    def g19():
        p=out/'PREDICTIONS_FROZEN.json'
        if not p.is_file():return 'UNRESOLVED',{},'No frozen prediction table.',{}
        d=json.loads(p.read_text());vals=[v['si_mass_core_kg'] for v in d['topologies'].values()];ok=bool(vals) and all(np.isfinite(vals)) and all(v>0 for v in vals);return ('PASS' if ok else 'FAIL'),{"absolute_predictions":len(vals),"background_mass_scale_kg":SST.line_mass_scale(SST.rho_f),"core_mass_scale_kg":SST.line_mass_scale(SST.rho_core),"background_tube_mass_scale_kg":SST.tube_mass_scale(SST.rho_f),"core_tube_mass_scale_kg":SST.tube_mass_scale(SST.rho_core),"clock_impedance":SST.clock_impedance},'PASS means target-free SI restoration is numerically defined; agreement with protected targets is post-reveal only.',{}
    _run_gate(ledger,'G19',g19)

    def g20():
        rows=context['rows'];by={}
        n=max(config['resolutions'])
        for r in rows:
            if r['resolution']==n:by.setdefault((r['topology_id'],r['carrier_id']),[]).append(r['energy_kernel'])
        sens=[]
        for v in by.values():
            if len(v)>1:sens.append((max(v)-min(v))/max(abs(np.mean(v)),1e-30))
        if not sens:return 'UNRESOLVED',{},'No core-scale sweep available.',{}
        med=float(np.median(sens));st='PASS' if med<=0.5 else 'FAIL';return st,{"median_core_sweep_relative_range":med,"threshold":0.5,"cases":len(sens)},'Robustness threshold is intentionally broad in v0.1.0 because the core law itself is under test.',{}
    _run_gate(ledger,'G20',g20)

    def g21():
        nom=context['nominal'];by={}
        for r in nom:by.setdefault(r['topology_id'],[]).append(r)
        rel=[]
        for t,rs in by.items():
            groups={str(r.get('independence_group')) for r in rs if r.get('independence_group')}
            if len(groups)>=2:
                vals=np.array([r['energy_kernel'] for r in rs]);mu=vals.mean();jack=[]
                for i in range(len(vals)):
                    if len(vals)>1:jack.append(np.delete(vals,i).mean())
                if jack:rel.append(max(abs(np.array(jack)-mu))/max(abs(mu),1e-30))
        if not rel:return 'UNRESOLVED',{},'No multi-group jackknife population.',{}
        mx=float(np.median(rel));st='PASS' if mx<=0.15 else 'FAIL';return st,{"median_max_leave_one_carrier_relative_shift":mx,"threshold":0.15,"topologies":len(rel)},'Provider/lineage labels are provenance strata, not manufactured replicate counts.',{}
    _run_gate(ledger,'G21',g21)

    def g22():
        essential=['G3','G7','G17'];support=['G8','G10','G11','G12','G13','G15','G16','G18','G19','G20','G21'];statuses={g:ledger.status(g) for g in essential+support};ep=sum(statuses[g]=='PASS' for g in essential);sp=sum(statuses[g]=='PASS' for g in support);un=sum(statuses[g]=='UNRESOLVED' for g in statuses)
        if ep==len(essential) and sp>=4:st='PASS';label='DYNAMIC_MASS_KERNEL_CANDIDATE_SUPPORTED_BLIND'
        elif un>len(statuses)//2:st='UNRESOLVED';label='INSUFFICIENT_QUALIFIED_EVIDENCE'
        else:st='FAIL';label='MASTER_MASS_RECONSTRUCTION_NOT_SUPPORTED_AT_REGISTERED_LEVEL'
        return st,{"classification":label,"gate_statuses":statuses,"essential_pass_count":ep,"support_pass_count":sp},'Classification is blind and lane-aware; individual diagnostics remain valid only at their recorded authority/caveat level.',{}
    _run_gate(ledger,'G22',g22)

    write_json(out/'DEPENDENCY_CAVEATS.json',{"schema":"A057-SOFT-DEPENDENCY-CAVEATS-1","rule":"Scientific failures do not block execution. These links constrain interpretation only.","rows":_soft_caveats(ledger)})
    return {"schema":"SST-BACKEND-MANIFEST-2","python_reference":{"actual_backend":"python-numpy-fp64","precision":"float64","authority":"REFERENCE"},"cpp_certification":{"gate_status":ledger.status('G5'),"authority":"CERTIFICATION"},"gpu_screening":{"gate_status":ledger.status('G6'),"authority":"SCREENING_ONLY"},"diagnostic_continuation":True,"scientific_gate_dependencies":"soft; see DEPENDENCY_CAVEATS.json"}
