from __future__ import annotations
import sys,unittest
from pathlib import Path
# Valid both as bundled unittest and when copied into generated framework instance.
ROOT=Path(__file__).resolve().parents[1]
if (ROOT/'payload'/'gpe_engine.py').exists():sys.path.insert(0,str(ROOT/'payload'))
else:sys.path.insert(0,str(ROOT/'experiment'))
from gpe_engine import plane_wave_test,reversibility_test,convergence_test

class TestGPE(unittest.TestCase):
    def test_exact_periodic_plane_wave(self):
        m=plane_wave_test()
        self.assertLess(m['plane_wave_relative_l2'],1e-10)
        self.assertLess(m['norm_relative_drift'],1e-10)
    def test_reverse_time(self):
        m=reversibility_test()
        self.assertLess(m['roundtrip_relative_l2'],1e-10)
    def test_second_order_convergence(self):
        m=convergence_test()
        self.assertGreater(m['min_order'],1.75)
    def test_changed_grid_resolution(self):
        m=plane_wave_test(n=64,steps=8)
        self.assertLess(m['plane_wave_relative_l2'],1e-10)

if __name__=='__main__':unittest.main()
