"""Source-derived geometry self-test; does NOT unseal user validation or test outputs."""
from pathlib import Path
import json,math,unittest
ROOT=Path(__file__).resolve().parents[1]
G=json.loads((ROOT/'config/EULER_GEOMETRY_REQUIRED.json').read_text(encoding='utf8'))
class Geometry(unittest.TestCase):
    def test_rectangular_dimensions(self):
        self.assertEqual((G['tank_length_internal_m'],G['tank_width_internal_m'],G['fill_depth_m']),(.08,.031,.043))
    def test_right_wall_elevation(self):
        self.assertAlmostEqual(G['sensor_x_from_center_m'],G['tank_length_internal_m']/2)
    def test_source_assumptions_explicit(self):
        self.assertEqual(G['surface_tension_N_m'],0.)
        self.assertEqual(G['n_modes'],4)
        self.assertEqual(G['liquid_density_kg_m3'],998.)
    def test_source_modal_frequencies(self):
        expected=[18.9684,33.9944,43.8884,51.9294]
        for n,w in enumerate(expected):
            k=(2*n+1)*math.pi/G['tank_length_internal_m']
            calc=math.sqrt(G['gravity_m_s2']*k*math.tanh(k*G['fill_depth_m']))
            self.assertAlmostEqual(calc,w,places=3)
    def test_fail_closed_unverified_signal_mapping(self):
        self.assertIsNone(G['measurement_height_sign'])
        self.assertIsNone(G['acceleration_axis_sign'])
        self.assertIs(G['initial_equilibrium_confirmed'],False)
        self.assertIs(G['provenance_confirmed'],False)
if __name__=='__main__':unittest.main(verbosity=2)
