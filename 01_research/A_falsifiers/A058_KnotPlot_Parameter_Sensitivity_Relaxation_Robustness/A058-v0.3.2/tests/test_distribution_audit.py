"""Offline A058-v0.3.2 regression suite; authentic distribution tests optional via env.

A058_KPDIST_ZIP=<path> enables actual uploaded/source ZIP audit.
"""
from __future__ import annotations
import io,json,os,struct,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.kpf_readonly import decode_kpf,metrics,KPFMalformed,KPFUnsupported
from tools.distribution_audit import (distribution_report,kpf_report,do_audit,generate_probes,safe_probe_script)


def made_kpf(code:bytes,payload:bytes,components=1)->bytes:
 header=b'KnotPlot 1.0  \x0c\n'
 chunks=b''.join(b'comp'+(code+struct.pack('>I',len(payload))+payload if i==0 else b'') for i in range(components))
 return header+chunks+b'endf\n\n\n\n'

class KPFDecoderTest(unittest.TestCase):
 def test_float64(self):
  b=made_kpf(b'LOCD',struct.pack('>9d',0,0,0,1,0,0,0,1,0))
  a=decode_kpf(b);self.assertEqual(a.encoding,'LOCD');self.assertEqual(len(a.points),3)
  self.assertAlmostEqual(metrics(a.points)['length_native_units'],2+2**.5)
 def test_float32(self):
  b=made_kpf(b'LOCF',struct.pack('>9f',0,0,0,1,0,0,0,1,0))
  self.assertEqual(len(decode_kpf(b).points),3)
 def test_locs(self):
  p=struct.pack('>ffff',.5,1,2,3)+struct.pack('>9H',0,0,0,2,0,0,0,2,0)
  a=decode_kpf(made_kpf(b'LOCS',p));self.assertEqual(a.points[1],(2.,2.,3.))
 def test_locc_first_point_not_lost(self):
  eps=struct.pack('>fff',.5,.5,.5)
  first=struct.pack('>fff',10,20,30)
  deltas=struct.pack('>6b',1,0,0,0,2,0)
  a=decode_kpf(made_kpf(b'LOCC',eps+first+deltas))
  self.assertEqual(a.points[0],(10.,20.,30.))
  self.assertEqual(a.points[1],(10.5,20.,30.))
  self.assertEqual(a.points[2],(10.5,21.,30.))
 def test_link_rejected(self):
  b=made_kpf(b'LOCD',struct.pack('>9d',*([0.,0.,0.]*3)),components=2)
  with self.assertRaises(KPFUnsupported):decode_kpf(b)
 def test_missing_end_rejected(self):
  b=made_kpf(b'LOCD',struct.pack('>9d',*([0.,0.,0.]*3)))[:-8]
  with self.assertRaises(KPFMalformed):decode_kpf(b)
 def test_nonfinite_rejected(self):
  b=made_kpf(b'LOCD',struct.pack('>9d',float('nan'),0,0,1,0,0,0,1,0))
  with self.assertRaises(KPFMalformed):decode_kpf(b)
 def test_unknown_chunk_rejected(self):
  b=b'KnotPlot 1.0  \x0c\ncompzzzzendf'
  with self.assertRaises(KPFUnsupported):decode_kpf(b)

class DistributionAuditTest(unittest.TestCase):
 def test_control_never_enables_velocity_buggy_or_collision_allow(self):
  for i in (1,4):
   s=safe_probe_script(i).lower()
   self.assertIn('collision fast',s)
   self.assertIn('velforce = off',s)
   self.assertIn('tanf = off',s)
   self.assertNotIn('collision allow',s)
   self.assertIn('go 32',s)
   self.assertIn('safe',s)
   self.assertIn('data format',s)
 def test_probes_match_except_dstep(self):
  a=safe_probe_script(1);b=safe_probe_script(4)
  self.assertEqual(a.replace('dstep = 1','dstep = 4'),b)
 def test_archive_optional(self):
  path=os.environ.get('A058_KPDIST_ZIP','')
  if not path:self.skipTest('A058_KPDIST_ZIP not set; basic offline tests still cover format')
  p=Path(path);self.assertTrue(p.is_file())
  d=distribution_report(p);self.assertTrue(d['static_tests_pass'],d['static_tests'])
  k=kpf_report(p)
  got={r['catalog']:r for r in k['catalog_samples']}
  self.assertEqual(got['basic/3.1']['nbeads'],47)
  self.assertEqual(got['basic/8.19']['nbeads'],86)
  self.assertEqual(got['basic/6.3.3']['status'],'UNSUPPORTED_LINK_OR_ENCODING')
  with tempfile.TemporaryDirectory() as td:
   dest=Path(td)/'audit';do_audit(p,dest,'AUDIT_ALL')
   self.assertTrue((dest/'KPF_AUDIT.csv').is_file())
   with self.assertRaises(FileExistsError):do_audit(p,dest,'AUDIT_ALL')
   probes=Path(td)/'probes';generate_probes(p,probes)
   self.assertEqual((probes/'dstep_1/A058_seed.kpf').read_bytes(),(probes/'dstep_4/A058_seed.kpf').read_bytes())
   self.assertEqual(json.loads((probes/'PROBES.json').read_text())['native_execution'],'NOT_RUN')
 def test_tamper_synthetic_archive_stops_without_outputs(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'wrong.zip'
   with zipfile.ZipFile(p,'w') as z:z.writestr('wrong/file','x')
   with self.assertRaises(ValueError):distribution_report(p)

if __name__=='__main__':unittest.main()
