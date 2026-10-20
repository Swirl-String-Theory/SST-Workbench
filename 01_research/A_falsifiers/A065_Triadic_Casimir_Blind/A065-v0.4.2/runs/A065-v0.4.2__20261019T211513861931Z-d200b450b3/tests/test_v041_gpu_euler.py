"""V041 regression: all GPU claims are fail-closed absent the real Arc."""
from __future__ import annotations
import copy, hashlib, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from triadic import gpu_euler_v041 as gpu
from triadic.euler3d_v040 import integrate,taylor_green
from framework_bridge.install import patch_arc_gpu_gate_plan,patch_cpu_gate_plan

ROOT=Path(__file__).resolve().parents[1]

class V041Tests(unittest.TestCase):
    def test_prereg_frozen_against_v040(self):
        a,b,h=gpu.preflight(ROOT)
        self.assertEqual(a['grids'],[48,64,96]);self.assertEqual(a['assumed_gaussian_a'],0.55)
        self.assertEqual(a['v040_prereg_sha256'],hashlib.sha256((ROOT/'preregistration/VOLUME_EULER_V040.json').read_bytes()).hexdigest())
        self.assertTrue(a['no_automatic_cpu_fallback'])
    def test_corrupted_v041_contract_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'preregistration';p.mkdir()
            a=(ROOT/'preregistration/ARC_GPU_V041.json').read_bytes()
            (p/'ARC_GPU_V041.json').write_bytes(a.replace(b'0.55',b'0.56'))
            (p/'ARC_GPU_V041.sha256').write_bytes((ROOT/'preregistration/ARC_GPU_V041.sha256').read_bytes())
            with self.assertRaises(ValueError):gpu.preflight(t)
    def test_existing_euler_fp64_parity(self):
        u=taylor_green(16)
        a=gpu.cpu_generic(u,2*np.pi,.02,4)
        b=integrate(u,2*np.pi,.02,4)
        for k,v in gpu.parity(a,b).items():self.assertLess(v,1e-12,k)
        self.assertLess(a['div_u_rms'],1e-11)
    def test_numpy_operator_time_refinement(self):
        u=taylor_green(16)
        a=gpu.cpu_generic(u,2*np.pi,.02,2)
        b=gpu.cpu_generic(u,2*np.pi,.02,4)
        self.assertLess(gpu.parity(a,b)['u'],1e-6)
    def test_missing_gpu_is_not_a_pass(self):
        with patch.object(gpu,'require_arc',side_effect=gpu.GPUUnavailable('deliberately absent')):
            result=gpu.run(ROOT,persist=False)
        for g in ('G43','G44','G45','G46','G47'):
            self.assertEqual(result['gates'][g]['status'],'NOT_RUN_PREREQUISITE')
        self.assertEqual(result['gates']['G48']['status'],'UNRESOLVED')
        self.assertFalse(result['physical_pklsa_qualified'])
    def test_prevent_forged_cpu_result_as_gpu(self):
        with patch.object(gpu,'require_arc',side_effect=gpu.GPUUnavailable('spoof blocked')):
            with self.assertRaises(gpu.GPUUnavailable):gpu.gpu_euler(taylor_green(16),2*np.pi,.02,4)
    def test_old_gate_plan_preserved_new_additive(self):
        orig={'gates':[{'gate_id':f'G{i}','question':f'old {i}','requires':[],'enabled':True} for i in range(10)]}
        legacy=patch_cpu_gate_plan(copy.deepcopy(orig))
        new=patch_arc_gpu_gate_plan(copy.deepcopy(legacy))
        self.assertEqual(len(legacy['gates']),43)
        self.assertEqual(len(new['gates']),49)
        self.assertEqual(new['gates'][:43],legacy['gates'])
        self.assertEqual(next(x for x in new['gates'] if x['gate_id']=='G48')['requires'],['G1'])
    def test_no_dd32_fft_claim(self):
        c,_,_=gpu.preflight(ROOT)
        self.assertEqual(c['gpu_precision'],'FP32_ONLY_DPNP_FFT_SCREENING')
        self.assertTrue(c['no_dd32_fft_certification'])
    def test_pressure_holdout_not_physical(self):
        c,_,_=gpu.preflight(ROOT)
        self.assertFalse(c['independent_physical_pressure_holdout'])
        self.assertEqual(c['pklsa_native_physical_closure'],'UNRESOLVED')

if __name__=='__main__': unittest.main()
