"""Version 0.2.4: opt-in boundary diagnostics, unchanged normal Euler path."""
from pathlib import Path
import hashlib
import pytest
from runtime_options import parse
from experiment.science import _resolve,profile_plan
from experiment.domain import parse_domains,run_domain_study
from tools.gpu_probe import stage_template_worker


def test_default_basic_has_no_domain_study():
    a,o,plan=parse(['BASIC','--grid','80','--threads','12'])
    assert a.mode == 'BASIC'
    assert not o['domain_study'] and not o['domain_study_only']
    assert plan['domain_boxes'] == []
    assert plan['domain_budget'] is None
    assert plan['box'] == 10.0 and plan['coarse_grid'] == 80
    assert plan['refined_grid'] == 112


def test_domain_opt_in_keeps_dx_and_checks_cost():
    a,o,plan=parse(['BASIC','--grid','80','--domain-study-only',
                    '--domains','10:80,15:120,20:160','--knots','0_1','--threads','12'])
    assert o['domain_study'] and o['domain_study_only']
    assert [x['grid'] for x in plan['domain_boxes']] == [80,120,160]
    assert all(x['dx'] == pytest.approx(0.125) for x in plan['domain_boxes'])
    assert not plan['domain_budget']['approved']  # heavy test requires explicit opt-in


def test_domains_cannot_be_silently_ignored():
    with pytest.raises(SystemExit):
        parse(['BASIC','--domains','10:80,15:120,20:160'])
    with pytest.raises(ValueError,match='DOMAIN_FIXED_DX_VIOLATION'):
        parse_domains('10:80,15:128,20:160',80)


def test_free_space_is_not_mislabeled_periodic():
    with pytest.raises(SystemExit):parse(['BASIC','--boundary','free-space'])


def test_source_staging_and_conflict_preserves_existing_file(tmp_path):
    framework=tmp_path/'framework'
    original=framework/'instance_template/native/cpp/sycl_worker.cpp'
    original.parent.mkdir(parents=True)
    original.write_bytes(b'// mock upstream worker for unit test\n')
    instance=tmp_path/'instance'
    first=stage_template_worker(framework,instance)
    assert first['success'] and first['stage_status']=='COPIED_AND_VERIFIED'
    assert first['sha256']==hashlib.sha256(original.read_bytes()).hexdigest()
    second=stage_template_worker(framework,instance)
    assert second['success'] and second['stage_status']=='VERIFIED_EXISTING'
    local=instance/'native/cpp/sycl_worker.cpp'
    local.write_bytes(b'// intentional custom native code\n')
    third=stage_template_worker(framework,instance)
    assert not third['success'] and third['reason'].startswith('LOCAL_SYCL_SOURCE_DIFFERS')
    assert local.read_bytes()==b'// intentional custom native code\n'
    assert original.read_bytes()==b'// mock upstream worker for unit test\n'


def test_small_domain_study_is_diagnostic_not_open_boundary(tmp_path):
    root=Path(__file__).resolve().parents[1]
    p=_resolve('BASIC',{'grid':16,'grid_up':32,'domains':'8:16,12:24,16:32',
                        't_end':0.02,'knots':['0_1'],'domain_study':True,
                        'domain_study_only':True,'dt':0.01,'threads':1})
    out=run_domain_study(root,'BASIC',tmp_path/'domain',p)
    assert out['executed']
    assert out['physical_answer']=='UNRESOLVED'
    assert out['physical_free_space_pass'] is False
    assert out['boundary_model']=='PERIODIC_IMAGES_PRESENT_AT_ALL_BOX_SIZES'
    assert len(out['knots']['0_1']['completed_levels'])==3
    assert (tmp_path/'domain/DOMAIN_MATRIX.json').is_file()
