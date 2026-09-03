from pathlib import Path
import numpy as np

from sst_seed_falsifier.archive import archive
from sst_seed_falsifier.blind import sealed_private_dir
from sst_seed_falsifier.candidates import analytic_trefoil
from sst_seed_falsifier.dynamics import tangential_redistribution
from sst_seed_falsifier.geometry import normalize_length,resample_closed,tangents
from sst_seed_falsifier.io import dump_json,load_json
from sst_seed_falsifier.mesh_closure import (
    displacement_decomposition,run_resolution,classify_resolution_ladder,build_arms,
)
from sst_seed_falsifier.workflow import stage_mesh_closure


def _cfg():
    return {
        'run_kind':'workflow_validation','gamma':1.0,'core_fraction':.08,'require_native':False,
        'dt_factor':.02,'max_steps':20000,'contact_skip':3,'min_gap_over_ds':.1,
        'max_ds_cv':2.0,'cyclic_stride':2,'store_samples':12,
        'mesh_rate':4.0,'mesh_redistribution_method':'segment_feedback','mesh_max_relative_rms':2.0,
        'mesh_closure_methods':['segment_feedback','target_projection'],'mesh_closure_rates':[2.4,4.0],
        'mesh_closure_mesh_max_relative_rms':2.0,'mesh_closure_samples':10,'mesh_closure_compare_samples':6,
        'mesh_closure_hard_ds_cv':2.0,'mesh_closure_shape_tol':.2,'mesh_closure_min_convergence_order':-.5,
        'mesh_closure_error_floor':1e-12,'mesh_gauge_max_final_shape_distance':.2,
        'score_shape_scale':.13,'score_highk_scale':.1,'high_k_cut_fraction':.33,'pod_modes':3,
        'score_weights':{'rolling':.4,'shape':.3,'highk':.15,'pod':0.,'contact':.1,'mesh':.05},
    }


def test_both_mesh_controllers_are_purely_tangential():
    x=normalize_length(resample_closed(analytic_trefoil(256),48),2*np.pi); t=tangents(x)
    for method in ('segment_feedback','target_projection'):
        u=tangential_redistribution(x,4.0,method)
        normal=u-np.sum(u*t,axis=1)[:,None]*t
        assert np.max(np.linalg.norm(normal,axis=1))<1e-12
    assert np.max(np.abs(tangential_redistribution(x,4.0,'none')))==0.0


def test_displacement_decomposition_separates_tangent_drift():
    # Same geometric circle with a smooth nonuniform parameterization.  To first order
    # the label displacement is tangential while the embedded curve is unchanged.
    t=np.linspace(0,2*np.pi,128,endpoint=False); eps=2e-3
    x=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]
    q=t+eps*np.sin(t)
    y=np.c_[np.cos(q),np.sin(q),np.zeros_like(q)]
    d=displacement_decomposition(x,y,2)
    assert d['shape_rms']<d['raw_label_rms']
    assert d['shape_rms']<5e-4
    assert np.isfinite(d['tangential_rms']) and np.isfinite(d['normal_rms'])


def test_run_resolution_freezes_same_plan_across_arms():
    cfg=_cfg(); cfg['mesh_closure_methods']=['segment_feedback','target_projection']; cfg['mesh_closure_rates']=[2.4]
    x=analytic_trefoil(96)
    r=run_resolution(x,cfg,24,.03)
    plans={(v['integration_steps'],v['dt'],v['guard_stride']) for v in r['arms'].values()}
    assert len(plans)==1
    assert set(r['arms'])=={'mesh_off','segment_feedback_r2p4','target_projection_r2p4'}
    assert r['arms']['mesh_off']['max_mesh_ratio']==0.0


def test_closure_classification_never_promotes_to_s40():
    cfg=_cfg();
    rows=[
        {'resolution':64,'all_arms_completed':True,'max_shape_vs_off':.06,'max_normal_vs_off':.05,'max_tangential_vs_off':.1,'max_rate_sensitivity_shape':.01,'max_controller_sensitivity_shape':.02,'versus_mesh_off':{'a':{'final':{'shape_rms':.06}}}},
        {'resolution':128,'all_arms_completed':True,'max_shape_vs_off':.05,'max_normal_vs_off':.04,'max_tangential_vs_off':.1,'max_rate_sensitivity_shape':.01,'max_controller_sensitivity_shape':.02,'versus_mesh_off':{'a':{'final':{'shape_rms':.05}}}},
    ]
    c=classify_resolution_ladder(rows,{**cfg,'mesh_closure_shape_tol':.035})
    assert c['status']=='GEOMETRIC_CENTERLINE_COUPLED_TO_MESH_GAUGE'
    assert c['promotion_to_s40_allowed'] is False and c['diagnostic_only'] is True


def test_stage_mesh_closure_reads_s35_not_s37(tmp_path):
    cfg={**_cfg(),'mesh_closure_top_k':1,'mesh_closure_min_per_source':1,'mesh_closure_resolution_ladder':[24],
         'mesh_closure_t_final':.02,'long_top_k':1}
    (tmp_path/'geometries').mkdir(); np.save(tmp_path/'geometries'/'C1.npy',analytic_trefoil(64))
    dump_json(tmp_path/'public_manifest.json',{'candidates':[{'candidate_id':'C1','source_group_id':'G1'}]})
    dump_json(tmp_path/'stage35_core_robustness'/'results.json',[{'candidate_id':'C1','qualified':True}])
    # Explicitly show that S37A has zero qualifiers. S37B must still diagnose C1.
    dump_json(tmp_path/'stage37_mesh_gauge'/'results.json',[{'candidate_id':'C1','qualified':False}])
    rows=stage_mesh_closure(tmp_path,cfg)
    assert len(rows)==1 and rows[0]['candidate_id']=='C1'
    s=load_json(tmp_path/'stage37b_mesh_closure'/'summary.json')
    assert s['diagnostic_only'] is True and s['promotion_to_s40_allowed'] is False


def test_blind_archive_excludes_sealed_private(tmp_path):
    project=tmp_path/'project'; root=project/'SST_Test_v0.0.1-outputs'; root.mkdir(parents=True)
    (root/'public.json').write_text('{}',encoding='utf-8')
    private=sealed_private_dir(root/'campaign'); private.mkdir(parents=True); (private/'blind_key.bin').write_bytes(b'secret')
    # private is a sibling under root because campaign is under root
    assert private.parent==root
    z=archive(root,'blind')
    import zipfile
    with zipfile.ZipFile(z) as f:
        names=f.namelist()
    assert any(n.endswith('/public.json') for n in names)
    assert not any('sealed_private' in n or n.endswith('blind_key.bin') for n in names)


def test_revealed_archive_includes_sealed_private(tmp_path):
    project=tmp_path/'project'; root=project/'SST_Test_v0.0.1-outputs'; root.mkdir(parents=True)
    (root/'public.json').write_text('{}',encoding='utf-8')
    private=sealed_private_dir(root/'campaign'); private.mkdir(parents=True); (private/'blind_key.bin').write_bytes(b'secret')
    z=archive(root,'revealed')
    import zipfile
    with zipfile.ZipFile(z) as f: names=f.namelist()
    assert any('campaign_sealed_private/blind_key.bin' in n for n in names)
