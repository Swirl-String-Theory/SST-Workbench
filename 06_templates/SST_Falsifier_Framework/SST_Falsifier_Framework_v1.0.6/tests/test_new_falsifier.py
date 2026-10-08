from pathlib import Path
import os, subprocess, sys


def _generate(root: Path, dst: Path, name="demo"):
    return subprocess.run(
        [sys.executable,str(root/"tools"/"new_falsifier.py"),"A999",name,str(dst),"--profile","minimal"],
        text=True,capture_output=True,
    )


def test_new_instance_unvalidated_and_private(tmp_path):
    root=Path(__file__).resolve().parents[1];dst=tmp_path/"A999-v0.1.0"
    cp=subprocess.run([sys.executable,str(root/"tools"/"new_falsifier.py"),"A999","demo",str(dst),"--profile","cpu"],text=True,capture_output=True)
    assert cp.returncode==0,cp.stderr
    assert "UNVALIDATED" in (dst/"VALIDATION.md").read_text()
    assert (dst/"private"/"OPAQUE_ID_KEY.bin").stat().st_size==32
    assert "profile = \"cpu\"" in (dst/"falsifier.toml").read_text()


def test_tex_profile_is_escaped(tmp_path):
    root=Path(__file__).resolve().parents[1];dst=tmp_path/"t"
    cp=subprocess.run([sys.executable,str(root/"tools"/"new_falsifier.py"),"A1","demo_name",str(dst),"--profile","multilibrary_gpu"],text=True,capture_output=True)
    assert cp.returncode==0
    tex=(dst/"report"/"FALSIFIER_REPORT.tex").read_text()
    assert "multilibrary\\_gpu" in tex and "demo\\_name" in tex


def test_generator_writes_relative_framework_locator(tmp_path):
    root=Path(__file__).resolve().parents[1]
    dst=tmp_path/"nested"/"A999-v0.1.0"
    cp=_generate(root,dst)
    assert cp.returncode==0,cp.stderr
    locator=(dst/".sst_framework_root").read_text(encoding="utf-8").strip()
    assert locator
    assert not Path(locator).is_absolute()
    assert (dst/locator).resolve()==root.resolve()


def test_run_all_has_no_hardcoded_legacy_framework_path():
    root=Path(__file__).resolve().parents[1]
    cmd=(root/"instance_template"/"run_all.cmd").read_text(encoding="utf-8")
    assert "04_tools\\D_proof" not in cmd
    assert "SST_FALSIFIER_FRAMEWORK_ROOT=%~dp0" not in cmd


def test_bootstrap_uses_only_nested_canonical_template_layout():
    root=Path(__file__).resolve().parents[1]
    src=(root/"instance_template"/"framework_bootstrap.py").read_text(encoding="utf-8")
    assert '"06_templates" / "SST_Falsifier_Framework"' in src
    assert 'family.glob("SST_Falsifier_Framework_v*")' in src
    assert "04_tools" not in src and "D_proof" not in src
    assert "templates.glob" not in src  # no old flat 06_templates fallback


def test_generated_instance_has_package_safe_python_wrapper(tmp_path):
    root=Path(__file__).resolve().parents[1];dst=tmp_path/"A998-v0.1.0"
    cp=_generate(root,dst)
    assert cp.returncode==0,cp.stderr
    wrapper=(dst/"run_python.cmd").read_text(encoding="utf-8")
    assert 'cd /d "%~dp0"' in wrapper
    assert 'PYTHONPATH=%CD%;%PYTHONPATH%' in wrapper
    assert 'run_python.py %*' in wrapper


def test_default_run_all_exports_instance_root_on_pythonpath():
    root=Path(__file__).resolve().parents[1]
    cmd=(root/"instance_template"/"run_all.cmd").read_text(encoding="utf-8")
    assert 'PYTHONPATH=%CD%;%PYTHONPATH%' in cmd


def test_generated_instance_has_pytest_framework_bootstrap(tmp_path):
    root=Path(__file__).resolve().parents[1]; dst=tmp_path/'nested'/'A998-v0.1.0'
    cp=_generate(root,dst,'pytest_bootstrap')
    assert cp.returncode==0,cp.stderr
    assert (dst/'conftest.py').is_file()
    bootstrap=(dst/'framework_bootstrap.py').read_text(encoding='utf-8')
    assert '.sst_framework_root' in bootstrap
    assert 'SST_FALSIFIER_FRAMEWORK_ROOT' in bootstrap
    assert '06_templates' in bootstrap


def test_generated_instance_pytest_can_import_pinned_framework_without_env(tmp_path):
    root=Path(__file__).resolve().parents[1]; dst=tmp_path/'nested'/'A997-v0.1.0'
    cp=_generate(root,dst,'pytest_import')
    assert cp.returncode==0,cp.stderr
    tests=dst/'tests'; tests.mkdir()
    (tests/'test_framework_import.py').write_text(
        'import sst_falsifier\n\ndef test_framework_import():\n    assert sst_falsifier.__version__ == "1.0.6"\n',encoding='utf-8')
    env=os.environ.copy(); env.pop('SST_FALSIFIER_FRAMEWORK_ROOT',None); env['PYTHONPATH']=''
    cp=subprocess.run([sys.executable,'-m','pytest','tests/test_framework_import.py','-q'],cwd=dst,env=env,text=True,capture_output=True)
    assert cp.returncode==0,cp.stdout+'\n'+cp.stderr


def test_locator_overrides_preloaded_stale_framework(tmp_path):
    root=Path(__file__).resolve().parents[1]; dst=tmp_path/'A996-v0.1.0'
    cp=_generate(root,dst,'strict_pin')
    assert cp.returncode==0,cp.stderr
    fake=tmp_path/'fake'; pkg=fake/'sst_falsifier'; pkg.mkdir(parents=True)
    (pkg/'__init__.py').write_text('__version__="0.9.9"\n',encoding='utf-8')
    code=(
        'import sst_falsifier; assert sst_falsifier.__version__=="0.9.9"; '
        'from framework_bootstrap import load_framework; load_framework(); '
        'import sst_falsifier; assert sst_falsifier.__version__=="1.0.6"; print(sst_falsifier.__version__)'
    )
    env=os.environ.copy(); env.pop('SST_FALSIFIER_FRAMEWORK_ROOT',None); env['PYTHONPATH']=str(fake)
    cp=subprocess.run([sys.executable,'-c',code],cwd=dst,env=env,text=True,capture_output=True)
    assert cp.returncode==0,cp.stdout+'\n'+cp.stderr
    assert cp.stdout.strip().endswith('1.0.6')


def test_invalid_locator_fails_closed_instead_of_autodiscovery(tmp_path):
    root=Path(__file__).resolve().parents[1]; dst=tmp_path/'A995-v0.1.0'
    cp=_generate(root,dst,'bad_locator')
    assert cp.returncode==0,cp.stderr
    (dst/'.sst_framework_root').write_text('../does-not-exist\n',encoding='utf-8')
    env=os.environ.copy(); env.pop('SST_FALSIFIER_FRAMEWORK_ROOT',None)
    cp=subprocess.run([sys.executable,'-c','from framework_bootstrap import load_framework; load_framework()'],cwd=dst,env=env,text=True,capture_output=True)
    assert cp.returncode!=0
    assert '.sst_framework_root points to an invalid' in (cp.stdout+cp.stderr)


def test_invalid_env_override_fails_closed_before_valid_locator(tmp_path):
    root=Path(__file__).resolve().parents[1]; dst=tmp_path/'A994-v0.1.0'
    cp=_generate(root,dst,'bad_env')
    assert cp.returncode==0,cp.stderr
    env=os.environ.copy(); env['SST_FALSIFIER_FRAMEWORK_ROOT']=str(tmp_path/'wrong')
    cp=subprocess.run([sys.executable,'-c','from framework_bootstrap import load_framework; load_framework()'],cwd=dst,env=env,text=True,capture_output=True)
    assert cp.returncode!=0
    assert 'SST_FALSIFIER_FRAMEWORK_ROOT points to an invalid' in (cp.stdout+cp.stderr)


def test_run_python_module_uses_instance_package_and_pinned_framework(tmp_path):
    root=Path(__file__).resolve().parents[1]; dst=tmp_path/'A993-v0.1.0'
    cp=_generate(root,dst,'module_launcher')
    assert cp.returncode==0,cp.stderr
    pkg=dst/'my_pkg'; pkg.mkdir(); (pkg/'__init__.py').write_text('',encoding='utf-8')
    (pkg/'tool.py').write_text('import sst_falsifier\nprint("OK:"+sst_falsifier.__version__)\n',encoding='utf-8')
    fake=tmp_path/'fake2'; fp=fake/'sst_falsifier'; fp.mkdir(parents=True); (fp/'__init__.py').write_text('__version__="0.8.0"\n',encoding='utf-8')
    env=os.environ.copy(); env.pop('SST_FALSIFIER_FRAMEWORK_ROOT',None); env['PYTHONPATH']=str(fake)
    cp=subprocess.run([sys.executable,'run_python.py','-m','my_pkg.tool'],cwd=dst,env=env,text=True,capture_output=True)
    assert cp.returncode==0,cp.stdout+'\n'+cp.stderr
    assert cp.stdout.strip()=='OK:1.0.6'
