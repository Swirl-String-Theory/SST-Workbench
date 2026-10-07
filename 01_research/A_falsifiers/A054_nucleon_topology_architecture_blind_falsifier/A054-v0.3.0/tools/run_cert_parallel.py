from __future__ import annotations
from pathlib import Path
import argparse, concurrent.futures, json, shutil

def _worker(args):
    campaign,config,rows,idx=args
    import sys
    camp=Path(campaign); sub=camp/'_cert_parallel'/f'w{idx:02d}'
    if sub.exists(): shutil.rmtree(sub)
    (sub/'blind_inputs').mkdir(parents=True)
    manifest=json.loads((camp/'BLIND_MANIFEST.json').read_text()); sm=dict(manifest); sm['candidates']=rows; sm['candidate_count']=len(rows)
    (sub/'BLIND_MANIFEST.json').write_text(json.dumps(sm,indent=2)+'\n')
    for r in rows: shutil.copy2(camp/'blind_inputs'/r['file'],sub/'blind_inputs'/r['file'])
    sys.path.insert(0,str(camp/'blind_runner'))
    from a054_blind.certify_v020 import run_certification
    run_certification(sub,Path(config))
    return str(sub/'CERT_RESULTS_BLIND.json')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--campaign',required=True); ap.add_argument('--config',required=True); ap.add_argument('--workers',type=int,default=5); a=ap.parse_args()
    camp=Path(a.campaign); manifest=json.loads((camp/'BLIND_MANIFEST.json').read_text()); rows=manifest['candidates']; n=max(1,min(a.workers,len(rows))); parts=[rows[i::n] for i in range(n)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=n) as ex: paths=list(ex.map(_worker,[(camp,a.config,parts[i],i) for i in range(n)]))
    results=[]
    for p in paths: results += json.loads(Path(p).read_text())['results']
    # stable order; SUMMARY after numeric N
    def k(r):
        nn=r.get('N'); nv=10**9 if nn=='SUMMARY' else int(nn)
        return (r['anonymous_id'],r['sector'],nv)
    results.sort(key=k)
    import sys; sys.path.insert(0,str(camp/'blind_runner'))
    from a054_blind.certify_v020 import analyze_certification,render_cert_report
    from a054_blind.physics import qualify_backend
    from a054_blind.seal import sha256_file
    cfg=json.loads(Path(a.config).read_text()); bq=qualify_backend(cfg.get('backend_policy','prefer_native')); (camp/'BACKEND_QUALIFICATION_CERT.json').write_text(json.dumps(bq,indent=2)+'\n')
    frozen=camp/'CERT_CONFIG.json'; frozen.write_text(json.dumps(cfg,indent=2,sort_keys=True)+'\n')
    out={'schema':'A054-CERT-BLIND-RESULTS-3.0','backend':bq['backend'],'parallel_workers':n,'results':results}
    rp=camp/'CERT_RESULTS_BLIND.json'; rp.write_text(json.dumps(out,indent=2)+'\n'); ana=analyze_certification(out,cfg); apath=camp/'CERT_ANALYSIS_BLIND.json'; apath.write_text(json.dumps(ana,indent=2)+'\n'); report=camp/'CERT_REPORT_BLIND.md'; report.write_text(render_cert_report(ana))
    seal={'schema':'A054-CERT-BLIND-SEAL-3.0','manifest_sha256':sha256_file(camp/'BLIND_MANIFEST.json'),'results_sha256':sha256_file(rp),'analysis_sha256':sha256_file(apath),'report_sha256':sha256_file(report),'config_sha256':sha256_file(frozen),'backend_qualification_sha256':sha256_file(camp/'BACKEND_QUALIFICATION_CERT.json'),'private_mapping_commitment':manifest['private_mapping_sha256'],'parallel_workers':n}
    (camp/'CERT_BLIND_SEAL.json').write_text(json.dumps(seal,indent=2)+'\n'); shutil.rmtree(camp/'_cert_parallel',ignore_errors=True)
    print(json.dumps({'candidates':len(rows),'records':len(results),'workers':n,'backend':bq['backend']},indent=2))
if __name__=='__main__': main()
