from pathlib import Path
import hashlib, json, statistics
from sst_torsion.reveal_constants import derived_scales
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.1.0-outputs'
BLIND=OUT/'BLIND'; REV=OUT/'REVEALED'; PRIVATE=ROOT/'.a048_private_reveal.json'
CFG=json.loads((ROOT/'configs'/'default.json').read_text(encoding='utf-8'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    for line in (BLIND/'BLIND_SEAL_SHA256.txt').read_text(encoding='utf-8').splitlines():
        h,rel=line.split('  ',1); p=BLIND/rel
        if not p.exists() or digest(p)!=h: raise RuntimeError(f'blind seal verification failed: {rel}')
def evaluate(folder,key):
    rows=json.loads((folder/'case_metrics.json').read_text(encoding='utf-8'))
    correct=0; errs=[]; amb=0
    for r in rows:
        truth=key['cases'][r['anonymous_case_id']]
        correct += (r['classification']==truth['label'])
        amb += (r['classification']=='AMBIGUOUS')
        errs.append(abs(r['power_exponent_p']-truth['target_exponent']))
    return {'count':len(rows),'accuracy':correct/len(rows),'ambiguous':amb,'median_abs_exponent_error':statistics.median(errs)}
if __name__=='__main__':
    verify(); key=json.loads(PRIVATE.read_text(encoding='utf-8'))
    py=evaluate(BLIND/'python_backend',key)
    py_summary=json.loads((BLIND/'python_backend'/'blind_summary.json').read_text(encoding='utf-8'))
    controls=py_summary['controls']
    gates={
      'classification_accuracy':py['accuracy']>=CFG['classification_accuracy_gate'],
      'median_exponent_error':py['median_abs_exponent_error']<=CFG['median_exponent_error_gate'],
      'circle_curvature':controls['circle_curvature_mean_abs_error']<=CFG['circle_curvature_error_gate'],
      'circle_torsion':controls['circle_torsion_max_abs']<=CFG['circle_torsion_gate'],
      'winding_gauge':controls['winding_gauge_error']<=CFG['winding_gauge_error_gate'],
    }
    native=None
    if (BLIND/'native_backend'/'case_metrics.json').exists():
        native=evaluate(BLIND/'native_backend',key)
        gates['native_classification_accuracy']=native['accuracy']>=CFG['classification_accuracy_gate']
    parity_file=BLIND/'backend_parity_summary.json'
    if parity_file.exists():
        parity=json.loads(parity_file.read_text(encoding='utf-8'))
        gates['native_backend_parity']=bool(parity.get('passed',False))
    status='SYNTHETIC_DISCRIMINATOR_QUALIFIED' if all(gates.values()) else 'SYNTHETIC_DISCRIMINATOR_FAILED'
    report={'status':status,'physics_status':'NOT_YET_TESTED_ON_INDEPENDENT_DYNAMICAL_PKLSA_OBSERVATIONS','python':py,'native':native,'gates':gates,'sst_scale_mapping':derived_scales()}
    REV.mkdir(exist_ok=True)
    (REV/'reveal_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    lines=[f'# A048 v0.1.0 reveal report','',f'**Status:** `{status}`','',f'**Physics status:** `{report["physics_status"]}`','',
           f'- Python classification accuracy: {py["accuracy"]:.6f}',f'- Median |p-p_true|: {py["median_abs_exponent_error"]:.6g}',f'- Ambiguous cases: {py["ambiguous"]}', '', '## Gates']
    lines += [f'- {k}: {"PASS" if v else "FAIL"}' for k,v in gates.items()]
    sc=report['sst_scale_mapping']; lines += ['', '## Post-seal SST scale mapping',f'- Gamma_c = {sc["Gamma_c_m2_s"]:.12e} m^2 s^-1',f'- beta_c = {sc["beta_c_m2_s"]:.12e} m^2 s^-1',f'- t_c = {sc["t_c_s"]:.12e} s',f'- omega_c = {sc["omega_c_s-1"]:.12e} s^-1','', '> These scales are reveal-only and do not enter the blind classifier.']
    (REV/'reveal_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
