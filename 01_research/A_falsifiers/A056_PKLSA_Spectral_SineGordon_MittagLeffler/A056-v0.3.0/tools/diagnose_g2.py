from __future__ import annotations
import argparse, json, os
from pathlib import Path
import numpy as np
from a056_science.io import discover_cases, uniformity
from a056_science.spectral import pod_metrics


def main():
    ap=argparse.ArgumentParser(description='Read-only A056 G2 POD diagnostic for an existing provider directory.')
    ap.add_argument('--instance-root', default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument('--input-dir', default=None)
    ap.add_argument('--config', default='configs/e010_real_score.json')
    ap.add_argument('--json-out', default=None)
    a=ap.parse_args()
    root=Path(a.instance_root).resolve()
    cfgp=Path(a.config); cfgp=cfgp if cfgp.is_absolute() else root/cfgp
    cfg=json.loads(cfgp.read_text(encoding='utf-8'))
    raw=a.input_dir or os.environ.get('A056_INPUT_DIR') or 'data/runtime_e010_filament'
    inp=Path(raw); inp=inp if inp.is_absolute() else root/inp
    rows=[]
    for case in discover_cases(inp):
        meta=case['meta']; t,s,phi=case['t'],case['s'],case['phi']
        tr,dt=uniformity(t); sr,ds=uniformity(s)
        sm,_,_=pod_metrics(phi,cfg['spectral']['top_k'],cfg['phase']['discovery_fraction'])
        opass=sm['orthogonality_residual']<=cfg['spectral']['orthogonality_max']
        spass=sm['discovery_confirmation_subspace_overlap']>=cfg['spectral']['subspace_overlap_min']
        rows.append({
            'opaque_id':meta.get('opaque_id',case['path'].stem),
            'nt':len(t),'ns':len(s),'t_uniform_rel':tr,'s_uniform_rel':sr,
            'pod_top_energy_fraction':sm['top_energy_fraction'],
            'pod_orthogonality_residual':sm['orthogonality_residual'],
            'pod_split_overlap':sm['discovery_confirmation_subspace_overlap'],
            'pod_rank':sm['rank'],'pod_k':sm['k'],'pod_discovery_cut':sm['discovery_cut'],
            'orthogonality_pass':bool(opass),'split_overlap_pass':bool(spass),
            'spectral_pass':bool(opass and spass),
        })
    payload={
        'schema':'A056-G2-DIAGNOSTIC-READONLY-1',
        'input_dir':str(inp),
        'config':str(cfgp),
        'thresholds':{
            'orthogonality_max':cfg['spectral']['orthogonality_max'],
            'subspace_overlap_min':cfg['spectral']['subspace_overlap_min'],
            'top_k':cfg['spectral']['top_k'],
        },
        'cases':rows,
    }
    txt=json.dumps(payload,indent=2,allow_nan=False)
    print(txt)
    if a.json_out:
        out=Path(a.json_out); out=out if out.is_absolute() else root/out
        out.parent.mkdir(parents=True,exist_ok=True); out.write_text(txt+'\n',encoding='utf-8')

if __name__=='__main__':
    main()
