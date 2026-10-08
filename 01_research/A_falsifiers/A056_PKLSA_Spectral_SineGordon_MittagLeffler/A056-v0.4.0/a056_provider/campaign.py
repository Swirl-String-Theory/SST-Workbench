from __future__ import annotations
from pathlib import Path
import argparse,hashlib,json,secrets,shutil,os,stat,time
import numpy as np
from .pklsa import resolve_workbench_root,locate_e010,validate_e010_release,strict_provider_representatives,load_carrier_centerline
from .geometry import canonicalize
from .evolution import paired_observables

def _canon(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def _token(key,*parts,n=16): return hashlib.sha256(key+b'|'+b'|'.join(str(x).encode() for x in parts)).hexdigest()[:n].upper()
def _sha_file(p):
    h=hashlib.sha256();
    with open(p,'rb') as f:
      for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def _make_writable(path: Path):
    """Best-effort clear Windows read-only attributes before deletion."""
    try:
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
    except OSError:
        pass


def _remove_entry_with_retry(path: Path, attempts: int = 10):
    """Remove one child entry, retrying transient Windows sharing/AV races."""
    path = Path(path)
    last = None
    for attempt in range(attempts):
        try:
            if path.is_dir() and not path.is_symlink():
                # Clear read-only bits throughout the child tree first.  Crucially,
                # callers never ask us to delete the runtime directory itself.
                for root, dirs, files in os.walk(path, topdown=False):
                    for name in files:
                        _make_writable(Path(root) / name)
                    for name in dirs:
                        _make_writable(Path(root) / name)
                _make_writable(path)
                shutil.rmtree(path)
            else:
                _make_writable(path)
                path.unlink(missing_ok=True)
            return
        except (PermissionError, OSError) as exc:
            last = exc
            if attempt + 1 >= attempts:
                break
            time.sleep(0.05 * (attempt + 1))
    raise RuntimeError(
        f"cannot clear stale runtime entry after {attempts} attempts: {path}; "
        f"last error: {last}"
    ) from last


def _reset_runtime_directory(path: Path):
    """Empty a runtime directory without deleting its root.

    On Windows an antivirus/indexer/Explorer handle can allow all children to be
    removed but still make the final os.rmdir(root) fail with WinError 5.  The
    provider only needs an empty directory, so deleting the root is unnecessary.
    Keeping it also avoids turning a benign open-directory handle into a failed
    scientific run.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    _make_writable(path)
    for child in list(path.iterdir()):
        _remove_entry_with_retry(child)
    return path

def build_provider(instance_root,config_path,workbench_root=None,out_dir=None):
    root=Path(instance_root); config_path=Path(config_path); cfg=json.loads(config_path.read_text()); sc=json.loads((root/'science_contract.json').read_text()); expected=sc.get('provider_preregistration',{}).get('provider_config_sha256',{}).get(config_path.name); actual=_sha_file(config_path);
    if expected!=actual: raise RuntimeError(f'provider config is not the frozen preregistered version: {config_path.name} {actual} != {expected}')
    wb=resolve_workbench_root(workbench_root); eroot,eout=locate_e010(wb); release=validate_e010_release(eout); carriers,audit,summary=strict_provider_representatives(eout)
    maxc=int(cfg.get('selection',{}).get('max_carriers',0) or 0); carriers=carriers[:maxc] if maxc else carriers
    out=Path(out_dir) if out_dir else root/cfg.get('output_dir','data/runtime_e010');
    _reset_runtime_directory(out)
    priv=out.parent/'private'/(out.name+'_reveal')
    _reset_runtime_directory(priv)
    key=secrets.token_bytes(32); nonce=secrets.token_bytes(32); (priv/'OPAQUE_KEY.bin').write_bytes(key); (priv/'NONCE.bin').write_bytes(nonce)
    reveal={"schema":"A056-PROVIDER-REVEAL-1","provider_config":str(config_path),"cases":[]}; generated=[]
    for car in carriers:
        raw,prov=load_carrier_centerline(car,wb,eroot,True,True)
        default_M=int(cfg['geometry']['marker_points'])
        family=_token(key,'family',car.carrier_id,cfg['solver']['kind'],cfg['perturbation']['mode'])
        for level in cfg['resolution_levels']:
            solver={**cfg['solver'],**level}
            M=int(solver.get('marker_points',default_M)) if solver['kind']=='filament_bs' else default_M
            base,canon=canonicalize(raw,M,cfg['geometry'].get('target_rms_radius',1.0))
            resval=int(solver.get('N',M))
            obs=paired_observables(base,solver,cfg['perturbation']); oid=_token(key,'case',car.carrier_id,solver['kind'],resval)
            sg=_token(key,'source',car.provider_group or car.independence_group or car.source_family); indep=_token(key,'ind',car.carrier_id); pf=_token(key,'prov',car.provider_group or car.source_family)
            npz=out/f'{oid}.npz'; np.savez_compressed(npz,t=obs['t'],s=obs['s'],phi=obs['phi'],ringdown_t=obs['ringdown_t'],ringdown=obs['ringdown'])
            meta={"schema":"A056-DYNAMIC-PROVIDER-5","opaque_id":oid,"source_group":sg,"boundary":"periodic","phase_definition_id":"paired_kelvin_residual_phase_v1","ringdown_definition_id":"paired_kelvin_mode_envelope_v1","perturbation_id":cfg['perturbation']['id'],"solver_id":f"a056_{solver['kind']}_v1","provider_version":"A056-v0.4.0","evidence_class":"simulation","independence_unit":indep,"provenance_family":pf,"upstream_geometry_sha256":car.geometry_sha256,"carrier_sha256":prov['raw_sha256'],"provider_case_family":family,"resolution_value":resval,"resolution_unit":"grid_N" if solver['kind']=='euler_ps3d' else "marker_points","provider_numerically_valid":bool(obs['diagnostics']['provider_numerically_valid']),"provider_diagnostics":obs['diagnostics'],"t_unit":"nondimensional Euler time","s_unit":"canonical arclength","synthetic":False}
            (out/f'{oid}.json').write_text(json.dumps(meta,indent=2)+'\n')
            reveal['cases'].append({"opaque_id":oid,"carrier_id":car.carrier_id,"source_family":car.source_family,"provider_group":car.provider_group,"independence_group":car.independence_group,"catalog_id":car.catalog_id,"variant_id":car.variant_id,"resolved_source_path":prov['resolved_source_path'],"raw_sha256":prov['raw_sha256'],"geometry_sha256":prov['geometry_sha256'],"provider_case_family":family,"resolution_value":resval,"solver":solver})
            generated.append({"opaque_id":oid,"npz_sha256":_sha_file(npz),"meta_sha256":_sha_file(out/f'{oid}.json'),"valid":meta['provider_numerically_valid']})
    reveal_bytes=_canon(reveal); (priv/'provider_reveal.json').write_bytes(reveal_bytes+b'\n'); commitment=hashlib.sha256(nonce+reveal_bytes).hexdigest(); (out/'PROVIDER_REVEAL_COMMITMENT.json').write_text(json.dumps({"schema":"A056-PROVIDER-REVEAL-COMMITMENT-1","sha256":commitment},indent=2)+'\n')
    for mp in out.glob('*.json'):
        if mp.name=='PROVIDER_REVEAL_COMMITMENT.json': continue
        o=json.loads(mp.read_text()); o['provider_reveal_commitment_sha256']=commitment; mp.write_text(json.dumps(o,indent=2)+'\n')
    manifest={"schema":"A056-E010-PROVIDER-MANIFEST-1","e010_release_version":release.get('e010_version'),"e010_release_path":str(eout),"selection_audit":audit,"selected_carrier_count":len(carriers),"generated_case_count":len(generated),"provider_reveal_commitment_sha256":commitment,"cases":generated}
    (out/'PROVIDER_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n'); return out,priv,manifest

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--instance-root',default=str(Path(__file__).resolve().parents[1])); ap.add_argument('--config',required=True); ap.add_argument('--workbench-root'); ap.add_argument('--out-dir'); a=ap.parse_args(); out,priv,m=build_provider(a.instance_root,a.config,a.workbench_root,a.out_dir); print(json.dumps({"status":"PASS","blind_input":str(out),"private_reveal":str(priv),"cases":m['generated_case_count']},indent=2))
if __name__=='__main__': main()
