"""Preflight protects immutable native evidence; no real KnotPlot required."""
from __future__ import annotations
import json,os,sys,tempfile,unittest,struct,zipfile,subprocess
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.distribution_audit import probe_preflight,require_probe_preflight,run_safe_probes,safe_probe_script,sha


def make_bundle(out:Path):
 out.mkdir(parents=True)
 seed=b'KnotPlot mock bytes'
 for dstep in [1,4]:
  dest=out/f'dstep_{dstep}'
  dest.mkdir()
  (dest/'A058_seed.kpf').write_bytes(seed)
  (dest/'probe.kpc').write_text(safe_probe_script(dstep),encoding='utf-8')
 (out/'PROBES.json').write_text(json.dumps({'schema':'A058-SAFE-NATIVE-PROBES-1','dstep_values':[1,4], 'seed_sha256':sha(seed), 'distribution_sha256':'f'*64}),encoding='utf-8')

class PreflightTest(unittest.TestCase):
 def test_ready(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'probe';make_bundle(out)
   doc=probe_preflight(out)
   self.assertEqual(doc['status'],'READY')
   self.assertTrue(doc['ready_for_native_execution'])

 def test_missing_seed_explicitly_identified_and_no_native_output(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'probe';make_bundle(out)
   (out/'dstep_1/A058_seed.kpf').unlink()
   self.assertIn('dstep_1/A058_seed.kpf',probe_preflight(out)['missing'])
   fake=Path(td)/'KnotPlot.exe';fake.write_bytes(b'fake')
   with self.assertRaisesRegex(RuntimeError,'PROBE_PREFLIGHT_INCOMPLETE_OR_MODIFIED') as cm:
    run_safe_probes(fake,out,30)
   self.assertIn('dstep_1/A058_seed.kpf',str(cm.exception))
   self.assertFalse((out/'NATIVE_LAUNCH_PRIVATE.json').exists())
   self.assertFalse((out/'dstep_1/NATIVE_STDOUT_PRIVATE.log').exists())

 def test_missing_bundle_never_inferred_from_old_dir(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'new';doc=probe_preflight(p)
   self.assertEqual(doc['status'],'NOT_GENERATED')
   self.assertFalse(p.exists())

 def test_existing_runtime_evidence_never_overwritten(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'probe';make_bundle(out)
   log=out/'dstep_1/NATIVE_STDOUT_PRIVATE.log'
   log.write_text('precious log evidence')
   self.assertEqual(probe_preflight(out)['status'],'PREVIOUS_NATIVE_ATTEMPT_PRESENT')
   with self.assertRaisesRegex(RuntimeError,'PREVIOUS_NATIVE_ATTEMPT_PRESENT'):
    require_probe_preflight(out)
   self.assertEqual(log.read_text(),'precious log evidence')

 def test_modified_script_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'probe';make_bundle(out)
   (out/'dstep_1/probe.kpc').write_text('reset all\n',encoding='utf-8')
   doc=probe_preflight(out)
   self.assertEqual(doc['status'],'INCOMPLETE_OR_MODIFIED')
   self.assertTrue(any('probe.kpc' in s for s in doc['mismatches']))

 def test_on_demand_generated_bundle_is_used_by_mock_native_runner(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   source=root/'kpdist_mock.zip'
   # A valid three-bead binary KnotPlot file, not actual 2026 KnotPlot physics.
   xyz=struct.pack('>9d',0,0,0,1,0,0,0,1,0)
   blob=b'KnotPlot 1.0  \\x0c\\n'
   blob=b'KnotPlot 1.0  '+bytes([12,10])+b'compLOCD'+len(xyz).to_bytes(4,'big')+xyz+b'endf\n\n\n\n'
   with zipfile.ZipFile(source,'w') as z:
    z.writestr('mock/demos/Dyna_help.txt','mock help')
    z.writestr('mock/basic/3.1',blob)
   exe=root/'KnotPlot.exe';exe.write_bytes(b'mock binary')
   out=root/'new_probe_folder'
   self.assertFalse(out.exists())
   def fake_native_run(command,**kwargs):
    script=kwargs['stdin'].read().decode('utf-8')
    i=4 if 'dstep = 4' in script else 1
    wd=out/f'dstep_{i}'
    self.assertEqual(kwargs['cwd'],root)
    self.assertIn((wd/'A058_final.txt').as_posix(),script)
    kwargs['stdout'].write(b'A058_SAFE_START\nCurrent position is safe.\nA058_SAFE_FINAL\nCurrent position is safe.\n')
    (wd/'A058_final.txt').write_text('0 0 0\n1 0 0\n0 1 0\n')
    (wd/'A058_native_metrics.csv').write_text('Nbeads,length\n3,3.414\n')
    return subprocess.CompletedProcess(command,0)
   with patch('tools.distribution_audit.subprocess.run',side_effect=fake_native_run) as mock_call:
    result=run_safe_probes(exe,out,20,dist=source)
   self.assertEqual(mock_call.call_count,2)
   self.assertTrue((out/'PROBES.json').exists())
   self.assertEqual(result['dstep_negative_control']['status'],'WITHIN_DISPLAY_CONTROL_TOLERANCE')
   self.assertEqual(probe_preflight(out,source)['status'],'PREVIOUS_NATIVE_ATTEMPT_PRESENT')

 def test_no_auto_repair_for_preexisting_partial_directory(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);out=root/'old';out.mkdir()
   exe=root/'KnotPlot.exe';exe.write_bytes(b'fake')
   dist=root/'source.zip';dist.write_bytes(b'fake archive')
   with self.assertRaisesRegex(RuntimeError,'PROBE_PREFLIGHT_NOT_GENERATED'):
    run_safe_probes(exe,out,30,dist=dist)
   self.assertEqual(list(out.iterdir()),[])

 def test_relative_out_resolved_against_caller_working_directory(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'p';make_bundle(out)
   with patch('pathlib.Path.cwd',return_value=Path(td)):
    # Path.resolve uses os.getcwd at the interpreter level on some Python versions,
    # so this test uses an absolute input path without altering global cwd.
    self.assertEqual(probe_preflight(out)['output_directory'],str(out.resolve()))

if __name__=='__main__':unittest.main()
