from __future__ import annotations
from pathlib import Path
import argparse, concurrent.futures, json, shutil, tempfile


def _worker(args):
    pkgroot,campaign,config,rows,idx=args
    import sys
    sys.path.insert(0,str(Path(pkgroot)/'blind_runner'))
    from a054_blind.blind import run_blind
    sub=Path(campaign)/'_parallel'/f'w{idx:02d}'
    if sub.exists(): shutil.rmtree(sub)
    (sub/'blind_inputs').mkdir(parents=True)
    parent=Path(campaign)
    manifest=json.loads((parent/'BLIND_MANIFEST.json').read_text())
    submanifest=dict(manifest); submanifest['candidates']=rows; submanifest['candidate_count']=len(rows)
    (sub/'BLIND_MANIFEST.json').write_text(json.dumps(submanifest,indent=2)+'\n')
    for r in rows: shutil.copy2(parent/'blind_inputs'/r['file'], sub/'blind_inputs'/r['file'])
    run_blind(sub,Path(config))
    return str(sub/'BLIND_RESULTS.json')


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--campaign',required=True); ap.add_argument('--config',required=True); ap.add_argument('--workers',type=int,default=5); a=ap.parse_args()
    campaign=Path(a.campaign); config=Path(a.config)
    manifest=json.loads((campaign/'BLIND_MANIFEST.json').read_text())
    rows=manifest['candidates']; n=max(1,min(a.workers,len(rows)))
    parts=[rows[i::n] for i in range(n)]
    args=[(campaign/'blind_runner',campaign,config,parts[i],i) for i in range(n)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=n) as ex:
        result_paths=list(ex.map(_worker,args))
    results=[]
    for p in result_paths: results += json.loads(Path(p).read_text())['results']
    # deterministic merged order
    results.sort(key=lambda r:(r['anonymous_id'],int(r['N']),float(r['core_ratio']),r['sector']))
    import sys; sys.path.insert(0,str(campaign/'blind_runner'))
    from a054_blind.blind import analyze,render_report
    from a054_blind.physics import qualify_backend
    from a054_blind.seal import sha256_file
    cfg=json.loads(config.read_text()); bq=qualify_backend(cfg.get('backend_policy','prefer_native'),float(cfg.get('native_reference_abs_tol',1e-11)))
    (campaign/'BACKEND_QUALIFICATION.json').write_text(json.dumps(bq,indent=2)+'\n')
    frozen=campaign/'BLIND_CONFIG.json'; frozen.write_bytes(config.read_bytes())
    rp=campaign/'BLIND_RESULTS.json'; rp.write_text(json.dumps({'schema':'A054-BLIND-RESULTS-3.0','parallel_workers':n,'results':results},indent=2)+'\n')
    ana=analyze(results,cfg,manifest,bq); apath=campaign/'ANALYSIS_BLIND.json'; apath.write_text(json.dumps(ana,indent=2)+'\n')
    report=campaign/'REPORT_BLIND.md'; report.write_text(render_report(ana,manifest))
    seal={'schema':'A054-BLIND-SEAL-3.0','manifest_sha256':sha256_file(campaign/'BLIND_MANIFEST.json'),'results_sha256':sha256_file(rp),'analysis_sha256':sha256_file(apath),'report_sha256':sha256_file(report),'backend_qualification_sha256':sha256_file(campaign/'BACKEND_QUALIFICATION.json'),'config_sha256':sha256_file(frozen),'private_mapping_commitment':manifest['private_mapping_sha256'],'parallel_workers':n}
    (campaign/'BLIND_SEAL.json').write_text(json.dumps(seal,indent=2)+'\n')
    shutil.rmtree(campaign/'_parallel',ignore_errors=True)
    print(json.dumps({'candidate_count':len(manifest['candidates']),'record_count':len(results),'workers':n,'backend':bq['backend']},indent=2))
if __name__=='__main__': main()
