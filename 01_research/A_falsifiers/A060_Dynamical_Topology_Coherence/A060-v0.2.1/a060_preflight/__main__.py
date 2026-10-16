"""Run non-authoritative M00--M04 reference checks and write a development ledger."""
import argparse, hashlib, json, os, pathlib, sys
import numpy as np
from .mechanics import (diagnostics,rank_one,rank_two,balanced,rank_one_gate,
    landreman_field, finite_jacobian, direct_spherical_flux, gradient_flux_prediction)
from .projection import projection_demo


def record(k, ok, details):
    return {"module":k,"precheck_status":"REFERENCE_PASS" if ok else "REFERENCE_FAIL",
            "evidence_class":"analytic_control_or_numerical_reference", "details":details,
            "certification":"NOT_CERTIFIED"}


def run(source_dir, manifest_path):
    results={}
    with open(manifest_path, encoding='utf8') as f: sources=json.load(f)
    present=[]; absent=[]; mismatched=[]
    for src in sources['papers']:
        p=pathlib.Path(source_dir)/src['filename']
        if not p.exists(): absent.append(src['source_id']);continue
        actual=hashlib.sha256(p.read_bytes()).hexdigest()
        (present if actual==src['sha256'] else mismatched).append(src['source_id'])
    if mismatched: status='SOURCE_HASH_MISMATCH'
    elif absent:status='UNRESOLVED_MISSING_SOURCE'
    else:status='REFERENCE_PASS'
    results['M00']={"module":"M00","precheck_status":status,"verified":present,"missing":absent,
                    "hash_mismatch":mismatched,"registry_reconciliation":"UNRESOLVED_A045_NAME_CONFLICT",
                    "framework_target":"1.0.7-CANONICAL_FROZEN", "certification":"NOT_CERTIFIED"}
    residual=[]
    for eps in (0.0,.2,.5):
        x=np.array([1.04,.16,.04]);f=lambda v:landreman_field(v,eps)
        u=f(x);A=finite_jacobian(f,x,1e-5)
        residual.append({"epsilon":eps,"divergence":float(abs(np.trace(A))),
                         "momentum_residual":float(np.max(np.abs(A@u+x*np.array([1,1,4])))),
                         "pressure_poisson_residual":float(abs(diagnostics(A)['poisson_source']-6))})
    results['M01']=record('M01',all(o['divergence']<3e-7 and o['momentum_residual']<2e-7 and o['pressure_poisson_residual']<3e-6 for o in residual),residual)
    suite={name:diagnostics(A) for name,A in [('shear',rank_one()),('balanced',balanced()),('rank2',rank_two()),('positive_gate',rank_one_gate()),('negative_gate',rank_one_gate(sign=-1))]}
    rng=np.random.default_rng(20261013);errors=[]
    for i in range(2500):
        A=rng.normal(size=(3,3));A-=np.trace(A)/3*np.eye(3)
        d=diagnostics(A);errors.append(max(d['m']-(1-d['f']),(1-d['f'])-3*d['m'],0))
    cases={name:{k:float(v) for k,v in d.items() if np.isscalar(v)} for name,d in suite.items()}
    results['M02']=record('M02',max(errors)<1e-10 and abs(suite['balanced']['poisson_source'])<1e-12,
                          {'max_wedge_violation':float(max(errors)), 'random_tensors':len(errors), 'cases':cases})
    proj=projection_demo(25)
    results['M03']=record('M03',proj['projection_curl_error']<1e-8 and proj['divergence_projected_va']<1e-8
                          and abs(proj['mean_omega_gradphi'])<1e-9 and proj['non_solenoidal_va_max']>.01,proj)
    ff=[];rng=np.random.default_rng(7189)
    for A in [rank_one(),balanced(),rank_two(eps=.02)]+[rng.normal(size=(3,3)) for _ in range(15)]:
        A=A-np.trace(A)/3*np.eye(3)
        lhs=direct_spherical_flux(A,.7);rhs=gradient_flux_prediction(A,.7)
        ff.append(abs(lhs-rhs)/(1+abs(rhs)))
    results['M04']=record('M04',max(ff)<1e-12 and abs(suite['balanced']['fluxfactor'])<1e-12,
                          {'n_tensor_cases':len(ff),'max_relative_flux_quadrature_error':float(max(ff)),
                           'balanced_gradient_fluxfactor':float(suite['balanced']['fluxfactor']),
                           'scope':'linear velocity fields only; not a general turbulence DNS'})
    return {'schema':'A060-PREFLIGHT-LEDGER-DEV-1','version':'v0.2.0-dev',
            'not_an_official_framework_ledger':True,'run_level':'LOCAL_REFERENCE_PRECHECK',
            'frozen_protocol':False,'native_cpu_fp64_certification':False,
            'physical_SST_claims':False,'results':results}


def main():
    root=pathlib.Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser()
    p.add_argument('--source-dir',default=str(root/'sources'))
    p.add_argument('--out',default=str(root/'preflight_outputs'))
    args=p.parse_args()
    output=run(args.source_dir, root/'sources'/'REFERENCE_HASHES.json')
    path=pathlib.Path(args.out);path.mkdir(parents=True,exist_ok=True)
    (path/'PRECHECK_RESULTS.json').write_text(json.dumps(output,indent=2,sort_keys=True,allow_nan=False),encoding='utf8')
    for k,v in output['results'].items():print(k,v['precheck_status'])
    print('Uncertified analytic precheck - NOT a framework v1.0.7 certification')
    if any(v['precheck_status'] in ('REFERENCE_FAIL','SOURCE_HASH_MISMATCH') for v in output['results'].values()):sys.exit(2)

if __name__=='__main__':main()
