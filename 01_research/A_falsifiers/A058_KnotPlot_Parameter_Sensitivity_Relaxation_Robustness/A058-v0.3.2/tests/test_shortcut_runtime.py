"""Offline launcher regression (mock KnotPlot only; native Windows still required)."""
from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.shortcut_runtime import resolve_launcher, native_probe_script
from tools.distribution_audit import run_safe_probes, safe_probe_script, sha

class ShortcutTest(unittest.TestCase):
 def test_direct_exe_uses_own_folder(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'KnotPlot.exe';p.write_bytes(b'fake exe')
   launch=resolve_launcher(p)
   self.assertEqual(launch.workdir,p.parent)
   self.assertEqual(launch.command(),[str(p),'-stdin','-nographics'])

 def test_mock_windows_link_retains_start_in(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); link=root/'KnotPlot.lnk';link.write_bytes(b'lnk')
   exe=root/'Bin'/'KnotPlot.exe';exe.parent.mkdir();exe.write_bytes(b'exe')
   work=root/'data';work.mkdir()
   resp=subprocess.CompletedProcess([],0,json.dumps({'target':str(exe),'workdir':str(work),'arguments':'-testflag'}),'')
   with patch('tools.shortcut_runtime.subprocess.run',return_value=resp) as spy:
    launch=resolve_launcher(link,platform='win32')
   self.assertEqual(launch.executable,exe)
   self.assertEqual(launch.workdir,work)
   self.assertEqual(launch.workdir_source,'shortcut_start_in_absolute')
   self.assertIn('-testflag',launch.command())
   self.assertEqual(spy.call_args.kwargs['env']['A058_SHORTCUT_PATH'],str(link))

 def test_mock_windows_empty_start_in_fallback_explicit(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);link=root/'k.lnk';link.write_bytes(b'lnk')
   exe=root/'bin'/'KnotPlot.exe';exe.parent.mkdir();exe.write_bytes(b'exe')
   resp=subprocess.CompletedProcess([],0,json.dumps({'target':str(exe),'workdir':'','arguments':''}),'')
   with patch('tools.shortcut_runtime.subprocess.run',return_value=resp):
    launch=resolve_launcher(link,platform='win32')
   self.assertEqual(launch.workdir,exe.parent)
   self.assertIn('fallback',launch.workdir_source)

 def _mock_link(self, root, *, raw, folder='exe_bin', args=''):
  link=root/'KnotPlot.lnk';link.write_bytes(b'lnk')
  exe=root/folder/'KnotPlot.exe';exe.parent.mkdir(parents=True,exist_ok=True);exe.write_bytes(b'fake')
  response=subprocess.CompletedProcess([],0,json.dumps({'target':str(exe),'workdir':raw,'arguments':args}),'')
  return link,exe,response

 def test_relative_dot_uses_exe_parent_not_shortcut_parent(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);link,exe,response=self._mock_link(root,raw='.')
   with patch('tools.shortcut_runtime.subprocess.run',return_value=response):
    launch=resolve_launcher(link,platform='win32')
   self.assertEqual(launch.workdir,exe.parent)
   self.assertEqual(launch.workdir_source,'relative_dot_executable_parent')

 def test_relative_child_only_under_exe_folder(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);link,exe,response=self._mock_link(root,raw='data')
   (exe.parent/'data').mkdir()
   with patch('tools.shortcut_runtime.subprocess.run',return_value=response):
    launch=resolve_launcher(link,platform='win32')
   self.assertEqual(launch.workdir,exe.parent/'data')
   self.assertEqual(launch.workdir_source,'relative_start_in_executable_parent')

 def test_relative_child_only_under_shortcut_folder(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);link,exe,response=self._mock_link(root,raw='data')
   (link.parent/'data').mkdir()
   with patch('tools.shortcut_runtime.subprocess.run',return_value=response):
    launch=resolve_launcher(link,platform='win32')
   self.assertEqual(launch.workdir,link.parent/'data')
   self.assertEqual(launch.workdir_source,'relative_start_in_shortcut_parent')

 def test_ambiguous_relative_child_fails_closed_without_override(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);link,exe,response=self._mock_link(root,raw='data')
   (exe.parent/'data').mkdir();(link.parent/'data').mkdir()
   with patch('tools.shortcut_runtime.subprocess.run',return_value=response):
    with self.assertRaisesRegex(RuntimeError,'Ambiguous relative Start-in'):
     resolve_launcher(link,platform='win32')

 def test_missing_relative_child_fails_closed_without_override(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);link,exe,response=self._mock_link(root,raw='missing')
   with patch('tools.shortcut_runtime.subprocess.run',return_value=response):
    with self.assertRaisesRegex(FileNotFoundError,'--workdir'):
     resolve_launcher(link,platform='win32')

 def test_explicit_override_resolves_ambiguous_relative(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);link,exe,response=self._mock_link(root,raw='data')
   a=exe.parent/'data';a.mkdir();b=link.parent/'data';b.mkdir()
   with patch('tools.shortcut_runtime.subprocess.run',return_value=response):
    launch=resolve_launcher(link,platform='win32',workdir_override=a)
   self.assertEqual(launch.workdir,a)
   self.assertEqual(launch.workdir_source,'explicit_cli_override')

 def test_explicit_override_must_be_absolute_and_existing(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);exe=root/'KnotPlot.exe';exe.write_bytes(b'exe')
   with self.assertRaisesRegex(ValueError,'absolute'):
    resolve_launcher(exe,workdir_override='relative')
   with self.assertRaises(FileNotFoundError):
    resolve_launcher(exe,workdir_override=root/'missing')

 def test_relative_dot_wrapped_by_windows_dot_slash(self):
  # The mock runs on POSIX; Windows Path normalization of '.\' is exercised
  # by the real Windows launcher using the same Path conversion.
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);link,exe,response=self._mock_link(root,raw='./')
   with patch('tools.shortcut_runtime.subprocess.run',return_value=response):
    launch=resolve_launcher(link,platform='win32')
   self.assertEqual(launch.workdir,exe.parent)

 def test_mock_windows_bad_start_in_fail_closed(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);link=root/'k.lnk';link.write_bytes(b'lnk')
   exe=root/'KnotPlot.exe';exe.write_bytes(b'exe')
   resp=subprocess.CompletedProcess([],0,json.dumps({'target':str(exe),'workdir':str(root/'MISSING'),'arguments':''}),'')
   with patch('tools.shortcut_runtime.subprocess.run',return_value=resp):
    with self.assertRaises(FileNotFoundError):resolve_launcher(link,platform='win32')

 def test_shortcut_check_cli_reports_without_exec(self):
  with tempfile.TemporaryDirectory() as td:
   import contextlib,io
   from tools import shortcut_check
   exe=Path(td)/'KnotPlot.exe';exe.write_bytes(b'fake')
   with patch.object(sys,'argv',['shortcut_check.py','CHECK_SHORTCUT','--exe',str(exe)]):
    out=io.StringIO()
    with contextlib.redirect_stdout(out):
     rc=shortcut_check.main()
   self.assertEqual(rc,0)
   result=json.loads(out.getvalue())
   self.assertEqual(result['workdir'],str(exe.parent))
   self.assertFalse(result['native_KnotPlot_executed'])

 def test_native_script_keeps_generator_immutable(self):
  with tempfile.TemporaryDirectory() as td:
   wd=Path(td)/'output';wd.mkdir()
   src=safe_probe_script(4)
   native=native_probe_script(src,wd)
   self.assertIn('load '+(wd/'A058_seed.kpf').as_posix(),native)
   self.assertIn('data open '+(wd/'A058_native_metrics.csv').as_posix(),native)
   self.assertIn('save '+(wd/'A058_final.txt').as_posix()+' ascii',native)
   self.assertIn('collision fast',native)
   self.assertIn('dstep = 4',native)
   self.assertIn('load A058_seed.kpf',src)

 def test_missing_output_rebinding_fails_closed(self):
  with tempfile.TemporaryDirectory() as td:
   src=safe_probe_script(1).replace('save A058_final.txt ascii','save hacked.txt ascii')
   with self.assertRaises(ValueError):native_probe_script(src,Path(td))

 def test_mock_native_process_uses_executable_folder_with_absolute_io(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); exe=root/'KnotPlot.exe';exe.write_bytes(b'executable')
   out=root/'A058_probes';out.mkdir()
   seed=b'KnotPlot binary specimen (mock)';seed_sha=sha(seed)
   for val in [1,4]:
    wd=out/f'dstep_{val}';wd.mkdir()
    (wd/'A058_seed.kpf').write_bytes(seed)
    (wd/'probe.kpc').write_text(safe_probe_script(val))
   (out/'PROBES.json').write_text(json.dumps({'dstep_values':[1,4],'seed_sha256':seed_sha}))
   seen=[]
   def fake_run(cmd,**kw):
    seen.append((cmd,kw['cwd']))
    raw=kw['stdin'].read().decode('utf-8')
    val=4 if 'dstep = 4' in raw else 1
    wd=out/f'dstep_{val}'
    self.assertIn(str((wd/'A058_final.txt').resolve().as_posix()),raw)
    self.assertEqual(kw['cwd'],exe.parent)
    kw['stdout'].write(b'A058_SAFE_START\nCurrent position is safe.\nA058_SAFE_FINAL\nCurrent position is safe.\n')
    (wd/'A058_final.txt').write_text('0 0 0\n1 0 0\n0 1 0\n')
    (wd/'A058_native_metrics.csv').write_text('Nbeads,length\n3,3.414\n')
    return subprocess.CompletedProcess(cmd,0)
   with patch('tools.distribution_audit.subprocess.run',side_effect=fake_run):
    result=run_safe_probes(exe,out,120)
   self.assertEqual(len(seen),2)
   self.assertEqual(result['dstep_negative_control']['status'],'WITHIN_DISPLAY_CONTROL_TOLERANCE')
   self.assertFalse(result['shortcut_used'])
   self.assertEqual((out/'dstep_1/probe.kpc').read_text(),safe_probe_script(1))
   self.assertTrue((out/'NATIVE_LAUNCH_PRIVATE.json').exists())
   self.assertEqual(json.loads((out/'NATIVE_LAUNCH_PRIVATE.json').read_text())['startup_workdir'],str(root))

if __name__=='__main__':unittest.main()
