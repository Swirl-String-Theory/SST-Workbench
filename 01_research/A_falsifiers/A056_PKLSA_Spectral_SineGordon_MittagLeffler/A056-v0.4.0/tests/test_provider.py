from pathlib import Path
import sys,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from a056_provider.geometry import bishop_frame_closed,kelvin_perturb,phase_and_ringdown
from a056_provider.evolution import paired_observables
from a056_provider.campaign import _reset_runtime_directory
from a056_science.provider_contract import validate_dynamic_metadata,SCHEMA

def trefoil(n=96):
 u=np.linspace(0,2*np.pi,n,endpoint=False); return np.column_stack([(2+.5*np.cos(3*u))*np.cos(2*u),(2+.5*np.cos(3*u))*np.sin(2*u),.5*np.sin(3*u)])

def test_closed_bishop_frame_orthonormal():
 P=trefoil(); T,E1,E2,_=bishop_frame_closed(P); assert np.max(np.abs(np.sum(T*E1,axis=1)))<1e-10; assert np.max(np.abs(np.linalg.norm(E1,axis=1)-1))<1e-10; assert np.max(np.abs(np.linalg.norm(E2,axis=1)-1))<1e-10

def test_phase_identity_at_initial_perturbation():
 P=trefoil(); Q,_=kelvin_perturb(P,.03,4); phi,t,R,d=phase_and_ringdown([0.0],[P],[Q],P,4); assert np.max(np.abs(phi))<1e-8 and abs(R[0]-1)<1e-12 and d['phase_valid_fraction']==1.0

def test_simulation_contract_requires_provider_fields():
 m={'schema':SCHEMA,'opaque_id':'x','source_group':'g','boundary':'periodic','phase_definition_id':'paired_kelvin_residual_phase_v1','ringdown_definition_id':'paired_kelvin_mode_envelope_v1','perturbation_id':'p','solver_id':'s','provider_version':'v','evidence_class':'simulation','independence_unit':'i','provenance_family':'pf','upstream_geometry_sha256':'u','carrier_sha256':'c'}; r=validate_dynamic_metadata(m,False); assert not r['pass'] and 'provider_case_family' in r['missing']

def test_short_filament_provider_finite():
 P=trefoil(64); P=P/np.sqrt(np.mean(np.sum(P*P,axis=1))); o=paired_observables(P,{'kind':'filament_bs','dt':.01,'T':.05,'core':.08,'sample_every':1,'max_segment_ratio':8},{'id':'t','epsilon':.01,'mode':4,'min_phase_valid_fraction':.8,'amplitude_floor_fraction':.02}); assert np.isfinite(o['phi']).all() and abs(o['ringdown'][0]-1)<1e-12

def test_build_e010_provider_direct_script_import_bootstrap():
    import subprocess
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build_e010_provider.py"), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "--workbench-root" in proc.stdout



def test_runtime_reset_keeps_root_and_removes_stale_files(tmp_path, monkeypatch):
    root=tmp_path/"runtime_e010_filament"
    root.mkdir()
    stale=root/"stale.json"; stale.write_text("old")
    nested=root/"nested"; nested.mkdir(); (nested/"old.bin").write_bytes(b"old")
    import a056_provider.campaign as campaign
    real_rmtree=campaign.shutil.rmtree
    def guarded_rmtree(path,*args,**kwargs):
        assert Path(path) != root, "runtime root must never be passed to shutil.rmtree"
        return real_rmtree(path,*args,**kwargs)
    monkeypatch.setattr(campaign.shutil,"rmtree",guarded_rmtree)
    returned=_reset_runtime_directory(root)
    assert returned==root
    assert root.is_dir()
    assert list(root.iterdir())==[]


def test_runtime_reset_handles_readonly_stale_file(tmp_path):
    import os, stat
    root=tmp_path/"runtime"; root.mkdir()
    stale=root/"readonly.json"; stale.write_text("old")
    os.chmod(stale, stat.S_IREAD)
    _reset_runtime_directory(root)
    assert root.is_dir() and not any(root.iterdir())
