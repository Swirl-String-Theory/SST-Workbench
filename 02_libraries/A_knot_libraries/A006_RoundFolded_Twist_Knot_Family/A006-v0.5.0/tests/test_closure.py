import unittest,math,tempfile
from pathlib import Path
import numpy as np
from vccr.core import reference_trefoil, state_from_length, stretch_table, knot_type_bounds, state_from_ropelength_saturated,dimension_checks
from vccr.geometry import read_xyz,measurements,material_pair

class ClosureTests(unittest.TestCase):
    def setUp(self): self.ref=reference_trefoil()
    def test_reference_constants(self):
        s=self.ref
        self.assertAlmostEqual(s.L_m/4.6133817956357553e-14,1,places=12)
        self.assertAlmostEqual(s.volume_m3/2.877218654223102e-43,1,places=12)
        self.assertAlmostEqual(s.circulation_m2_s/9.683619203488876e-9,1,places=12)
        self.assertTrue(all(dimension_checks(s).values()))
    def test_scaling(self):
        s=self.ref; t=state_from_length(2*s.L_m,s.volume_m3,s.circulation_m2_s)
        self.assertAlmostEqual(t.a_m/s.a_m,1/math.sqrt(2),places=12)
        self.assertAlmostEqual(t.mean_omega_s1/s.mean_omega_s1,2,places=12)
        self.assertAlmostEqual(t.swirl_edge_speed_m_s/s.swirl_edge_speed_m_s,math.sqrt(2),places=12)
        self.assertAlmostEqual(t.ropelength_diameter/s.ropelength_diameter,2**1.5,places=12)
    def test_ropelength_saturated(self):
        s=state_from_ropelength_saturated(self.ref.ropelength_diameter,self.ref.volume_m3,self.ref.circulation_m2_s)
        self.assertAlmostEqual(s.L_m/self.ref.L_m,1,places=12)
        self.assertAlmostEqual(s.a_m/self.ref.a_m,1,places=12)
    def test_bounds(self):
        d=knot_type_bounds(self.ref.volume_m3,self.ref.ropelength_diameter)
        self.assertAlmostEqual(d['radius_max_m']/self.ref.a_m,1,places=12)
        self.assertAlmostEqual(d['L_min_m']/self.ref.L_m,1,places=12)
    def test_invalid(self):
        for x in [0,-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):state_from_length(x,1,1)
    def test_geometry_parser_link_and_material(self):
        with tempfile.TemporaryDirectory() as td:
            x=Path(td)/'before.xyz';y=Path(td)/'after.xyz'
            def circle(r):return [[r*math.cos(i*math.pi/4),r*math.sin(i*math.pi/4),0] for i in range(8)]
            c0=circle(3);c1=[[xx+20,yy,zz] for xx,yy,zz in circle(2)]
            def write(p,r):p.write_text('\n'.join(' '.join(map(str,pt)) for pt in c0)+'\n\n'+
                                          '\n'.join(' '.join(map(str,pt)) for pt in c1 if r==1 or r==2)+'\n' if r==1 else
                                          '\n'.join(' '.join(map(str,pt)) for pt in circle(6))+'\n\n'+
                                          '\n'.join(' '.join(map(str,pt)) for pt in [[20+2*(pt[0]-20),2*pt[1],pt[2]] for pt in c1])+'\n')
            write(x,1);write(y,2)
            self.assertEqual([len(c) for c in read_xyz(x)],[8,8]);self.assertEqual(measurements(x)['n_components'],2)
            s=material_pair(x,y,2,3,1.0)
            self.assertEqual(s['gates']['material_volume_bookkeeping'],'PASS')
            for c in s['components']:
                self.assertAlmostEqual(c['volume_relative_residual'],0,places=12)
    def test_reference_examples_present(self):
        root=Path(__file__).resolve().parents[1]
        sample=root/'examples/LINK_5_5_6_BALANCED_N0512_ORIG_CPFIXED61.xyz'
        self.assertEqual(measurements(sample)['n_components'],3)
        self.assertEqual(measurements(root/'examples/KNOT_5_2_N0512_ORIG.xyz')['n_components'],1)

if __name__=='__main__':unittest.main()
