import unittest
import numpy as np
from sst_einstein.geometry import ring, kelvin_ring, resample_closed
from sst_einstein import reference

class ReferenceTests(unittest.TestCase):
    def test_translation_invariance_energy_impulse(self):
        p=kelvin_ring(32,1.0,0.04,2,0.1,True)
        q=p+np.array([0.3,-0.2,0.1])
        self.assertAlmostEqual(reference.filament_energy(p,0.08),reference.filament_energy(q,0.08),places=12)
        np.testing.assert_allclose(reference.impulse(p),reference.impulse(q),rtol=1e-12,atol=1e-12)
    def test_uniform_velocity_adds_exactly(self):
        p=ring(24); u=np.array([0.1,-0.2,0.03])
        a=reference.biot_savart_velocity(p,0.08,1.0,(0,0,0)); b=reference.biot_savart_velocity(p,0.08,1.0,u)
        np.testing.assert_allclose(b-a,np.broadcast_to(u,a.shape),rtol=1e-13,atol=1e-13)
    def test_resample_count(self):
        self.assertEqual(resample_closed(ring(17),40).shape,(40,3))

if __name__=='__main__': unittest.main()
