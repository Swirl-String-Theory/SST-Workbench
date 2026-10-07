import json
from pathlib import Path
import numpy as np
import pytest

import a054_ntaf.certify_v020 as c


def _cfg():
    return {
        'backend_policy':'prefer_native',
        'core_ratio':0.04,
        'circulation_sectors':['Q0'],
        'n_ref':3,
        'n_ladder':[2,3],
        'kelvin_harmonics':[1],
        'jacobian_eps_values':[0.01,0.02],
        'jacobian_convergence_max':1.0,
        'hessian_eps':0.01,
        'normalized_growth_max':1.0,
        'kelvin_restricted_normalized_growth_max':1.0,
        'restoring_amp':0.01,
        'restoring_dt_ref':0.01,
        'restoring_T_final':0.01,
        'restoring_return_ratio_max':10.0,
        'ringdown_amp':0.01,
        'ringdown_dt_ref':0.01,
        'ringdown_T_final':0.01,
        'ringdown_stride':1,
        'ringdown_max_over_initial':10.0,
        'max_linking_drift':10.0,
        'min_clearance_ratio_min':0.0,
        'rpo_amp':0.01,
        'rpo_phase_count':1,
        'rpo_dt_ref':0.01,
        'rpo_T_final':0.01,
        'rpo_stride':1,
        'rpo_min_step_fraction':0.0,
        'rpo_excursion_min':0.0,
        'rpo_recurrence_max':10.0,
        'rpo_return_ratio_max':10.0,
        'floquet_modes_max':1,
        'floquet_eps':0.01,
        'floquet_spectral_radius_max':10.0,
        'spatial_normalized_growth_abs_max':10.0,
        'spatial_kelvin_growth_abs_max':10.0,
        'spatial_rel_eq_abs_max':10.0,
        'spatial_restoring_ratio_abs_max':10.0,
        'relative_equilibrium_residual_diagnostic_max':10.0,
        'floquet_base_recurrence_max':10.0,
    }


def _record():
    return {
        'status':'LOCAL_NUMERICALLY_QUALIFIED',
        'spectrum':{'normalized_max_real':0.0,'kelvin_restricted':{'normalized_max_real':0.0}},
        'relative_equilibrium_residual':0.0,
        'restoring':[{'return_ratio_median':1.0}],
        'gates':{},
    }


def _campaign(tmp_path: Path):
    camp=tmp_path/'camp'; (camp/'blind_inputs').mkdir(parents=True)
    (camp/'blind_inputs'/'CAND_x.npz').write_bytes(b'x')
    (camp/'BLIND_MANIFEST.json').write_text(json.dumps({
        'schema':'test','private_mapping_sha256':'abc','candidates':[{'anonymous_id':'CAND_x','file':'CAND_x.npz'}]
    }))
    cfg=tmp_path/'cfg.json'; cfg.write_text(json.dumps(_cfg()))
    return camp,cfg


def test_checkpoint_resume_skips_completed_unit(tmp_path, monkeypatch):
    camp,cfg=_campaign(tmp_path)
    monkeypatch.setattr(c,'qualify_backend',lambda policy:{'qualified':True,'backend':'test_backend'})
    base=[np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]) for _ in range(3)]
    monkeypatch.setattr(c,'load_components_npz',lambda p:base)
    monkeypatch.setattr(c,'resample_closed_curve',lambda x,n:x)
    calls={'n':0}
    def crash_second(*args, **kwargs):
        calls['n']+=1
        if calls['n']==2:
            raise KeyboardInterrupt()
        return _record()
    monkeypatch.setattr(c,'certify_case',crash_second)
    with pytest.raises(KeyboardInterrupt):
        c.run_certification(camp,cfg)
    cps=list((camp/'cert_checkpoints').glob('*.json'))
    assert len(cps)==1
    assert json.loads((camp/'PROGRESS.json').read_text())['status']=='INTERRUPTED'

    calls2={'n':0}
    def succeed(*args, **kwargs):
        calls2['n']+=1
        return _record()
    monkeypatch.setattr(c,'certify_case',succeed)
    c.run_certification(camp,cfg,resume=True)
    assert calls2['n']==1, 'resume must skip the already checkpointed first resolution'
    out=json.loads((camp/'CERT_RESULTS_BLIND.json').read_text())
    assert len(out['results'])==3  # N=2, N=3, SUMMARY
    prog=json.loads((camp/'PROGRESS.json').read_text())
    assert prog['status']=='COMPLETE'
    assert prog['completed_units']==2
    assert (camp/'CERT_BLIND_SEAL.json').exists()


def test_checkpoint_provenance_mismatch_fails(tmp_path, monkeypatch):
    camp,cfg=_campaign(tmp_path)
    monkeypatch.setattr(c,'qualify_backend',lambda policy:{'qualified':True,'backend':'test_backend'})
    base=[np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]) for _ in range(3)]
    monkeypatch.setattr(c,'load_components_npz',lambda p:base)
    monkeypatch.setattr(c,'resample_closed_curve',lambda x,n:x)
    monkeypatch.setattr(c,'certify_case',lambda *a,**k:_record())
    c.run_certification(camp,cfg)
    # Finished campaign cannot be resumed under a changed config.
    data=_cfg(); data['core_ratio']=0.05; cfg2=tmp_path/'cfg2.json'; cfg2.write_text(json.dumps(data))
    (camp/'CERT_BLIND_SEAL.json').unlink()
    with pytest.raises(RuntimeError, match='CERT_CONFIG'):
        c.run_certification(camp,cfg2,resume=True)
