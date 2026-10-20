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
        # Missing A003 sources must never become synthetic impostors, irrespective
        # of whether the actual atlas is installed on the test machine.
        from unittest.mock import patch
        c,_=campaign.preflight(ROOT)
        with patch.object(campaign,'adapter_root',return_value=None):
            sources,reason=campaign.selected_sources(ROOT,c)
        self.assertIsNone(sources)
        self.assertEqual(reason,'A003_ADAPTER_MISSING')
        self.assertEqual(c['independent_physical_provider_count'],0)

    def test_a003_selected_sources_passes_mapping_not_integer(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        c,_=campaign.preflight(ROOT)
        registry={'atlas_manifest_sha256':c['atlas_manifest_sha256'],
                  'records':[{'id':sid,'sampling':c['sampling'],
                              'points':c['source_resolution'],'file':sid+'.xyz'} for sid in c['seeds']]}
        adapter=SimpleNamespace(validate_atlas=lambda *args,**kw:(
            registry,{'status':'GEOMETRIC_IMPORT_QUALIFIED','source_records':384}))
        seen=[]
        def screen(adapter_obj,ar,reg,record,pre):
            self.assertIsInstance(pre,dict)
            self.assertEqual(pre['source_resolution'],c['source_resolution'])
            seen.append(record['id'])
            xyz=np.array([[1.,0,0],[0,1,0],[-1.,0,0],[0,-1,0]],dtype=np.float64)
            return {'xyz':xyz,'source_sha256':'unit-test-hash',
                    'source_file':record['file'],'polyline_length':4.0}
        with patch.object(campaign,'adapter_root',return_value=Path('/synthetic/path')),\
             patch.object(campaign,'_load_original_adapter',return_value=adapter),\
             patch.object(campaign,'atlas_root',return_value=Path('/synthetic/atlas')),\
             patch.object(campaign,'_screen_geometry',side_effect=screen):
            sources,missing=campaign.selected_sources(ROOT,c)
        self.assertIsNone(missing)
        self.assertEqual(sorted(seen),sorted(c['seeds']))
        self.assertEqual(set(sources),set(c['seeds']))
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
