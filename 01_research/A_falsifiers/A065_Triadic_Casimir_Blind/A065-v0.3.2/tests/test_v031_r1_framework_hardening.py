"""A065 v0.3.1-r1: reproduce Windows WinError183 and verify fail-closed orchestration."""
from pathlib import Path
from unittest.mock import patch
import json, hashlib, os, shutil, subprocess, sys, tempfile, unittest
from framework_bridge.install import _merge_additive, _configure
from triadic import launch

ROOT=Path(__file__).resolve().parents[1]

class R1FrameworkHardening(unittest.TestCase):
    def test_merge_of_existing_native_and_preregistration_is_additive(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)
            (d/'native'/'cpp').mkdir(parents=True)
            (d/'native'/'cpp'/'native.cpp').write_bytes(b'CANONICAL_SCAFFOLD')
            (d/'preregistration').mkdir()
            (d/'preregistration'/'existing.json').write_bytes(b'GENERATOR_MATERIAL')
            root=Path(td)/'source'
            (root/'native').mkdir(parents=True)
            (root/'native'/'response.cpp').write_bytes(b'INSTANCE_RESPONSE')
            (root/'preregistration').mkdir()
            (root/'preregistration'/'QUALIFICATION_V031.json').write_bytes(b'SEALED_CONFIG')
            for key in ('native','preregistration'):
                stats=_merge_additive(root/key,d/key)
                self.assertEqual(stats['created'],1)
            self.assertEqual((d/'native'/'cpp'/'native.cpp').read_bytes(),b'CANONICAL_SCAFFOLD')
            self.assertEqual((d/'preregistration'/'existing.json').read_bytes(),b'GENERATOR_MATERIAL')
            self.assertEqual((d/'native'/'response.cpp').read_bytes(),b'INSTANCE_RESPONSE')
            self.assertEqual((d/'preregistration'/'QUALIFICATION_V031.json').read_bytes(),b'SEALED_CONFIG')
            self.assertEqual(_merge_additive(root/'native',d/'native')['identical'],1)
    def test_complete_instance_configuration_preserves_generator_scaffold(self):
        # Regression of exactly the old copytree(native) WinError183 site.
        with tempfile.TemporaryDirectory() as td:
            parent=Path(td);root=parent/'source';inst=parent/'inst'
            root.mkdir(); inst.mkdir()
            for name in ('data','seals','triadic','native','preregistration','framework_bridge'):
                shutil.copytree(ROOT/name,root/name,ignore=shutil.ignore_patterns('__pycache__'))
            from triadic.provider_manifest import write_new
            write_new(root)
            for name in ('native/cpp','preregistration','experiment','private','report'):
                (inst/name).mkdir(parents=True, exist_ok=True)
            existing_cpp=inst/'native/cpp/native.cpp'
            existing_cpp.write_text('generator-canonical-stub',encoding='utf-8')
            existing_reg=inst/'preregistration/BLIND_TERMS_COMMITMENT.json'
            existing_reg.write_text('GENERATOR_CREATED_COMMITMENT',encoding='utf-8')
            (inst/'run_instance.py').write_text('ROOT = Path(__file__).resolve().parent\n')
            (inst/'falsifier.toml').write_text('pdf_required = false\n')
            (inst/'gate_plan.json').write_text(json.dumps({'gates':[
                {'gate_id':f'G{i}','question':f'question {i}','requires':[]} for i in range(10)]}))
            (inst/'blind_policy.json').write_text('{}')
            _configure(root,inst)
            self.assertEqual(existing_cpp.read_text(),'generator-canonical-stub')
            self.assertEqual(existing_reg.read_text(),'GENERATOR_CREATED_COMMITMENT')
            self.assertTrue((inst/'native'/'filament_velocity.cpp').is_file())
            self.assertTrue((inst/'experiment/pipeline.py').is_file())
            self.assertTrue((inst/'preregistration/QUALIFICATION_V031.json').is_file())
            self.assertTrue((inst/'outputs/PROVIDER_MANIFEST.json').is_file())
            self.assertIn('pdf_required = true',(inst/'falsifier.toml').read_text())
            plan=json.loads((inst/'gate_plan.json').read_text())
            self.assertEqual(next(g for g in plan['gates'] if g['gate_id']=='G5')['requires'],['G1'])
    def test_merge_refuses_conflicting_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);src=d/'source';dst=d/'dest'
            src.mkdir();dst.mkdir()
            (src/'native.cpp').write_bytes(b'new bytes')
            (dst/'native.cpp').write_bytes(b'original bytes')
            before=hashlib.sha256((dst/'native.cpp').read_bytes()).hexdigest()
            with self.assertRaisesRegex(RuntimeError,'INSTANCE_MERGE_REFUSES_OVERWRITE'):
                _merge_additive(src,dst)
            self.assertEqual(hashlib.sha256((dst/'native.cpp').read_bytes()).hexdigest(),before)
    def test_standalone_dynamics_exports_json(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'case';d.mkdir()
            for dir in ('data','seals','preregistration','triadic','tests','framework_bridge','native'):
                shutil.copytree(ROOT/dir,d/dir,ignore=shutil.ignore_patterns('__pycache__'))
            for fil in ('README.md','requirements.txt'):
                shutil.copy2(ROOT/fil,d/fil)
            from triadic.provider_manifest import write_new
            write_new(d)
            env=os.environ.copy();env['SST_A065_ISOLATED_RUN']='1';env['PYTHONDONTWRITEBYTECODE']='1'
            # v0.3.1-r1 regression checks only the historical DYNAMICS JSON output.
            # The new 600-point v0.3.2 expensive scan is independently tested by
            # the real unique-run QUALIFY smoke campaign and dedicated v032 tests.
            command=("from triadic import entrypoint, qualification_v032; "
                     "qualification_v032.run=lambda root:{'qualification':{'historical_fail_retained':'FAIL'}}; "
                     "entrypoint.command(['DYNAMICS'])")
            p=subprocess.run([sys.executable,'-c',command],cwd=d,env=env,
                             capture_output=True,text=True,timeout=240)
            self.assertEqual(p.returncode,0,msg=p.stderr)
            result=d/'outputs'/'DYNAMICS_RESULT.json'
            self.assertTrue(result.is_file())
            body=json.loads(result.read_text())
            self.assertEqual(body['result']['spatial_pairs']['75_vs_150']['gate'],'FAIL')
            self.assertEqual(body['result']['spatial_pairs']['150_vs_300']['gate'],'PASS')
            self.assertEqual(body['scientific_status'],'FILAMENT_ODE_SIMULATION_ONLY')
    def test_all_framework_failure_is_nonzero_but_pdf_generated(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'case';d.mkdir()
            for folder in ('data','seals','triadic','native','preregistration','framework_bridge'):
                shutil.copytree(ROOT/folder,d/folder,ignore=shutil.ignore_patterns('__pycache__'))
            from triadic.provider_manifest import write_new
            write_new(d)
            env=os.environ.copy();env['SST_A065_ISOLATED_RUN']='1'
            env['SST_A065_RUN_ID']='A065-v0.3.1__test_failclosed'
            env['SST_A065_EXPORT_DIR']=str(d/'exports');(d/'exports').mkdir()
            env['SST_FALSIFIER_FRAMEWORK_ROOT']=str(d/'missing_framework')
            # The full SELFTEST suite is tested independently in this test run.
            # This sub-process isolates only fail propagation and report emission.
            command=("from triadic import runner, entrypoint; "
                     "runner.main=lambda: None; from triadic import qualification_v032; qualification_v032.run=lambda root: None; entrypoint.command(['ALL'])")
            p=subprocess.run([sys.executable,'-c',command],cwd=d,env=env,
                             capture_output=True,text=True,timeout=240)
            self.assertEqual(p.returncode,3,msg=p.stderr)
            s=json.loads((d/'FRAMEWORK_STATUS.json').read_text())
            self.assertEqual(s['state'],'FRAMEWORK_NOT_FOUND')
            self.assertTrue((d/'reports'/'A065-v0.3.1__test_failclosed_FALSIFIER_REPORT.pdf').exists())
    def test_unique_dynamics_export_preserves_zip_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            work=Path(td)/'work';export=Path(td)/'exp';(work/'outputs').mkdir(parents=True)
            export.mkdir()
            (work/'outputs'/'DYNAMICS_RESULT.json').write_text('{"test":1}')
            (work/'data'/'D01_EULER').mkdir(parents=True)
            (work/'data'/'D02_CLOCK_LINK').mkdir(parents=True)
            (work/'data'/'D03_TWO_SURFACE').mkdir(parents=True)
            (work/'seals').mkdir()
            for n in ('D01_EULER','D02_CLOCK_LINK','D03_TWO_SURFACE'):
                (work/'data'/n/'sample.txt').write_text(n)
                (work/'seals'/f'{n}.seal.json').write_text('{}')
            (work/'seals'/'GLOBAL_COMMITMENT.json').write_text('{}')
            launch._publish_exports('UNIQUE',work,export)
            self.assertEqual((export/'UNIQUE_DYNAMICS_RESULT.json').read_text(),'{"test":1}')
            oldhash=hashlib.sha256((export/'UNIQUE_DYNAMICS_RESULT.json').read_bytes()).hexdigest()
            with self.assertRaises(FileExistsError):launch._publish_exports('UNIQUE',work,export)
            self.assertEqual(hashlib.sha256((export/'UNIQUE_DYNAMICS_RESULT.json').read_bytes()).hexdigest(),oldhash)
if __name__=='__main__':unittest.main()
