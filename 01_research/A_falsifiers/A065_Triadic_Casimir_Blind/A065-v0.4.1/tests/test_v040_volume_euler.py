"""Regression checks for v0.4.0. No physical PKLSA positive assertion."""
from __future__ import annotations
import copy,json,math,tempfile,unittest
from pathlib import Path
import numpy as np
from triadic import euler3d_v040 as solver
from triadic import volume_v040 as campaign
ROOT=Path(__file__).resolve().parents[1]

class V040VolumeEulerTests(unittest.TestCase):
    def test_taylor_green_divergence_and_energy(self):
        v=solver.integrate(solver.taylor_green(16),2*np.pi,T=.02,steps=4)
        self.assertLess(v['audit']['div_u_rms'],1e-10)
        self.assertLess(v['audit']['relative_energy_drift'],1e-8)
        self.assertLess(v['audit']['curl_u_omega_relative'],1e-10)
        self.assertEqual(v['audit']['independent_physical_pressure_holdout'],False)
    def test_euler_time_halving(self):
        u=solver.taylor_green(16)
        a=solver.integrate(u,2*np.pi,T=.02,steps=2)
        b=solver.integrate(u,2*np.pi,T=.02,steps=4)
        self.assertLess(campaign.relerr(a['u'],b['u']),1e-4)
    def test_analytic_initial_velocity_divergence(self):
        n=24;L=2*np.pi;U=solver.taylor_green(n)
        K,_,inv,mask=solver.wave(n,L)
        V=solver.project(np.fft.fftn(U,axes=(1,2,3)),K,inv,mask)
        diverge=np.fft.ifftn(1j*np.einsum('ixyz,ixyz->xyz',K,V)).real
        self.assertLess(float(np.max(abs(diverge))),1e-12)
    def test_48_64_96_prereg_frozen(self):
        c,h=campaign.preflight(ROOT)
        self.assertEqual(c['grids'],[48,64,96]);self.assertEqual(c['euler_steps'],4)
        self.assertEqual(c['gaussian_a_assumed'],0.55)
        self.assertEqual(c['independent_physical_provider_count'],0)
    def test_mutated_prereg_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            tmp=Path(t)/'preregistration';tmp.mkdir()
            original=(ROOT/'preregistration'/'VOLUME_EULER_V040.json').read_bytes()
            (tmp/'VOLUME_EULER_V040.json').write_bytes(original.replace(b'0.55',b'0.56'))
            with self.assertRaises(campaign.SourceIntegrityError):campaign.preflight(t)
    def test_high_grid_interpolation_is_not_truth(self):
        a=np.ones((3,16,16,16)); b=campaign.truth_on_grid(a,32)
        self.assertEqual(b.shape,(3,32,32,32))
        self.assertLess(float(np.max(abs(b-1))),1e-10)
    def test_missing_A003_never_faked(self):
        root=ROOT
        c,_=campaign.preflight(root)
        if not (campaign.selected_sources(root,c)[1] is None):
            # The developer sandbox lacks original A003-v0.1.2; locally it may be installed.
            self.assertEqual(c['independent_physical_provider_count'],0)
        else:
            self.assertEqual(c['independent_physical_provider_count'],0)
    def test_new_gates_append_only(self):
        from framework_bridge.install import patch_cpu_gate_plan
        src=json.loads((ROOT/'preregistration'/'SOURCE_NATIVE_CORE_V038.json').read_text())
        plan={'gates':[{'gate_id':f'G{i}','question':'test','requires':[],'enabled':True} for i in range(10)]}
        modified=patch_cpu_gate_plan(copy.deepcopy(plan))
        ids=[g['gate_id'] for g in modified['gates']]
        self.assertEqual(len(ids),43)
        self.assertEqual(len(set(ids)),43)
        self.assertEqual(next(x for x in modified['gates'] if x['gate_id']=='G41')['requires'],['G1'])
    def test_pressure_not_independently_observed(self):
        a=solver.integrate(solver.taylor_green(16),2*np.pi,.02,2)
        self.assertTrue(np.isfinite(a['p']).all())
        self.assertFalse(a['audit']['independent_physical_pressure_holdout'])

if __name__=='__main__':unittest.main()
