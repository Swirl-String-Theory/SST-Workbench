from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import importlib.util
import numpy as np

def _write(obj, path):
    text=json.dumps(obj, indent=2, sort_keys=True)
    if path: Path(path).write_text(text+"\n", encoding="utf-8")
    else: print(text)

def _arr(x): return np.asarray(x, dtype=float)

def _cert_mod():
    for parent in Path(__file__).resolve().parents:
        cand = parent / "07_scripts" / "paper_upgrade_certificate.py"
        if cand.is_file():
            name = "paper_upgrade_certificate"
            if name in sys.modules:
                return sys.modules[name]
            spec = importlib.util.spec_from_file_location(name, cand)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("paper_upgrade_certificate not found")

def consume_a034(cert):
    puc = _cert_mod()
    required=('family','status','provenance_sha256','classification')
    missing=[k for k in required if k not in cert]
    ok_prom, why = puc.require_promotable(cert)
    payload_ok = (cert.get('payload_schema') == 'SST-ADMISSIBILITY-1.0') or (
        # transitional: family field present
        cert.get('family') == 'A034'
    )
    ok = (
        not missing
        and cert.get('family') == 'A034'
        and payload_ok
        and ok_prom
        and cert.get('classification') not in ('NONSTATIONARY','ENERGETIC_SADDLE')
    )
    reason = 'ok' if ok else (why if not ok_prom else 'A034 CAMPAIGN admissibility certificate with promotion_allowed required')
    return {
        "accepted": bool(ok),
        "missing": missing,
        "reason": reason,
        "promotion_allowed": bool(cert.get('promotion_allowed')),
        "promotable": bool(ok_prom),
    }

def selftest():
    puc = _cert_mod()
    c = puc.apply_certificate_envelope(
        {
            'family': 'A034',
            'classification': 'ENERGETICALLY_ADMISSIBLE',
            'provenance_sha256': 'a' * 64,
        },
        certificate_kind='CAMPAIGN',
        producer='A034',
        gate='constrained_admissibility',
        payload_schema='SST-ADMISSIBILITY-1.0',
        gate_status='PASS',
        source_run_id='selftest',
        source_output_sha256='c' * 64,
        gate_input_sha256='d' * 64,
        numerical_qualification={'temporal': 'PASS', 'spatial': 'PASS', 'mesh': 'PASS'},
        synthetic_inputs=False,
    )
    # provenance for consume required field
    c['provenance_sha256'] = 'a' * 64
    assert consume_a034(c)['accepted']
    c2 = dict(c); c2['classification'] = 'ENERGETIC_SADDLE'
    assert not consume_a034(c2)['accepted']
    synth = puc.apply_certificate_envelope(
        {'family': 'A034', 'classification': 'ENERGETICALLY_ADMISSIBLE', 'provenance_sha256': 'a' * 64},
        certificate_kind='SELFTEST',
        producer='A034',
        gate='constrained_admissibility',
        payload_schema='SST-ADMISSIBILITY-1.0',
    )
    synth['provenance_sha256'] = 'a' * 64
    assert not consume_a034(synth)['accepted']
    no_nq = dict(c)
    no_nq['numerical_qualification'] = {'temporal': 'NOT_RUN', 'spatial': 'PASS', 'mesh': 'PASS'}
    no_nq = puc.stamp_promotion_allowed(no_nq)
    assert not consume_a034(no_nq)['accepted']
    return {"status": "PASS"}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--selftest',action='store_true'); ap.add_argument('--input'); ap.add_argument('--output')
    ns=ap.parse_args()
    if ns.selftest: return _write(selftest(),ns.output)
    if not ns.input: ap.error('--input required unless --selftest')
    data=json.loads(Path(ns.input).read_text(encoding='utf-8'))
    op=data.pop('operation',None)
    if not op or op not in globals() or not callable(globals()[op]): raise SystemExit(f'unknown operation: {op}')
    _write(globals()[op](**data),ns.output)
if __name__=='__main__': main()
