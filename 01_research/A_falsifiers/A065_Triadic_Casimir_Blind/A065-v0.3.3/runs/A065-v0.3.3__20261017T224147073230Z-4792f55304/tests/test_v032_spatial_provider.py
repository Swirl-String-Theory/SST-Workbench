"""Tranche v0.3.2: do not promote interpolated grids or unrelated data to providers."""
from __future__ import annotations
import hashlib,json,math,shutil,subprocess,tempfile,unittest
from pathlib import Path
from triadic.spatial_v032 import interpolate_600,compare
from triadic.independent_fremlin_v032 import run_native
from triadic.pklsa import load_geometry
from triadic.dynamics import evolve,rms_difference
from framework_bridge.install import patch_cpu_gate_plan
from triadic.security import readjson,verify_all

ROOT=Path(__file__).resolve().parents[1]

class V032Tests(unittest.TestCase):
 def test_interpolant_anchor_invariance(self):
  p=load_geometry(ROOT/'data/D01_EULER/pklsa/trefoil_KnotPlot_relaxed_N300.txt')
  out=interpolate_600(p)
  self.assertEqual(len(out),600)
  self.assertEqual(out[::2],p)
 def test_precommit_and_seals(self):
  x=readjson(ROOT/'preregistration/QUALIFICATION_V032.json')
  self.assertEqual(x['T'],0.04)
  self.assertEqual(x['epsilon'],.12)
  self.assertEqual(x['threshold'],.05)
  self.assertEqual(len(verify_all(ROOT)),3)
 def test_cpp_native_trajectory_knotplot_is_control_not_provider(self):
  compiler='g++'
  if not shutil.which(compiler): self.skipTest('g++ unavailable')
  pts=load_geometry(ROOT/'data/D01_EULER/pklsa/trefoil_KnotPlot_relaxed_N300.txt')[::4]
  with tempfile.TemporaryDirectory() as d:
   exe=Path(d)/'native'
   cp=subprocess.run([compiler,'-O2','-std=c++17',str(ROOT/'native/fremlin_propagator.cpp'),'-o',str(exe)],capture_output=True,text=True)
   self.assertEqual(cp.returncode,0,cp.stderr)
   sim=run_native(exe,pts,8,.12,.04,1.)
  expected=evolve(pts,.12,1.,.04,8)
  self.assertLess(rms_difference(sim,expected),1e-12)
 def test_framework_gates_independent_from_historical_g2(self):
  plan={'schema':'SST-GATE-PLAN-2','gates':[{'gate_id':k,'question':k,'requires':[],'enabled':True} for k in ['G0','G1','G2','G3','G4','G5','G6','G7','G8','G9']]}
  patched=patch_cpu_gate_plan(plan)
  by={k['gate_id']:k for k in patched['gates']}
  self.assertEqual(by['G10']['requires'],['G1'])
  self.assertEqual(by['G11']['requires'],['G1'])
  self.assertNotIn('G2',by['G10']['requires'])
  self.assertNotIn('G7',by['G8']['requires'])
 def test_fremlin_source_unavailable_does_not_promote(self):
  contract=readjson(ROOT/'data/D01_EULER/pklsa/fremlin_provider_contract.json')
  self.assertEqual(contract['carrier_id'],'CAR_d8a316361e0941af')
  self.assertFalse(contract['raw_file_in_bundle'])
  self.assertNotEqual(contract['expected_raw_sha256'],readjson(ROOT/'data/D01_EULER/pklsa/source.json')['raw_sha256'])

if __name__=='__main__':unittest.main()
