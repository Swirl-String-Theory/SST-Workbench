from __future__ import annotations
import json, math, os, tempfile, unittest
from pathlib import Path
import numpy as np

from pklsa_builder.fseries import parse_fremlin_fseries, sample_fremlin_fseries
from pklsa_builder.gilbert import find_gilbert_record, sample_gilbert_record
from pklsa_builder.io_geometry import load_xyz
from pklsa_builder.geometry import polygon_length, sample_spline, local_metrics
from pklsa_builder.qualification import qualify_components
from pklsa_builder.models import QualificationConfig
from pklsa_builder.convergence import classify
from pklsa_builder.topology_db import canonicalize_knot_label
from pklsa_builder.independence import build_independence_ledger
from pklsa_builder.hashing import geometry_sha256

ROOT=Path(__file__).resolve().parents[1]

class BuilderTests(unittest.TestCase):
    def test_fremlin_fixture(self):
        p=ROOT/'data'/'fixtures'/'knot.3_1.fseries'
        r=parse_fremlin_fseries(p)
        self.assertGreaterEqual(len(r['coefficients']),3)
        x=sample_fremlin_fseries(p,512)
        self.assertEqual(x.shape,(512,3)); self.assertTrue(np.isfinite(x).all())
        self.assertGreater(polygon_length(x),0)

    def test_gilbert_fixture(self):
        p=ROOT/'data'/'fixtures'/'Ideal.txt.gz'
        r=find_gilbert_record(p,'3_1')
        self.assertEqual(r['attrs']['Id'],'3:1:1')
        self.assertAlmostEqual(float(r['attrs']['L']),16.371637,places=6)
        x=sample_gilbert_record(r,512)
        self.assertEqual(x.shape,(512,3)); self.assertTrue(np.isfinite(x).all())

    def test_geometry_local_ladder(self):
        p=ROOT/'data'/'fixtures'/'3_1_katlas_braid.xyz'
        c=load_xyz(p)[0]
        cfg=QualificationConfig(resolution_ladder=[64,128,256],min_levels_for_resolution=3,expensive_metrics=False)
        q=qualify_components([c],cfg)
        self.assertEqual(len(q['levels']),3)
        for lev in q['levels']:
            for key in ('L','kappa_max','kappa_rms','kappa_std','tau_rms'):
                self.assertTrue(math.isfinite(float(lev['metrics'][key])))
        self.assertIn(q['convergence']['L']['status'],('COARSE','CONVERGING','RESOLVED','UNRESOLVED'))

    def test_convergence_classifier(self):
        r=classify({'128':1.0,'256':1.001,'512':1.0012},resolved_tol=.005,converging_tol=.05,min_levels=3)
        self.assertEqual(r['status'],'RESOLVED')
        r2=classify({'128':1.0},min_levels=3)
        self.assertEqual(r2['status'],'UNRESOLVED')

    def test_label_normalization(self):
        self.assertEqual(canonicalize_knot_label('3.1'),'3_1')
        self.assertEqual(canonicalize_knot_label('K12a1202'),'12a_1202')
        self.assertEqual(canonicalize_knot_label('12n_34'),'12n_34')

    def test_independence_guard(self):
        pts=np.column_stack([np.cos(np.linspace(0,2*np.pi,64,endpoint=False)),np.sin(np.linspace(0,2*np.pi,64,endpoint=False)),np.zeros(64)])
        gh=geometry_sha256([pts])
        rows=[]
        for cid,sf,grp,parent,role in [
            ('A','fremlin_fourier','fremlin:3_1',None,'independent_reference_geometry'),
            ('B','fremlin_fourier_mirror','fremlin:3_1','fremlin_fourier','mirror_reference_geometry'),
            ('C','ridgerunner','rr:3_1','knotplot','derived_relaxed_geometry'),
            ('D','ptsa','ptsa:v1', 'sst_generated','generated_experimental_family')]:
            rows.append({'carrier':{'carrier_id':cid,'source_family':sf,'topology_id':'3_1','independence_group':grp,'parent_source_family':parent,'source_role':role,'raw_sha256':cid},'geometry_sha256':gh})
        led=build_independence_ledger(rows)
        by={x['carrier_id']:x for x in led['entries']}
        self.assertEqual(by['B']['evidence_independence_class'],'MIRROR_NOT_INDEPENDENT')
        self.assertEqual(by['C']['evidence_independence_class'],'DERIVED_CROSS_METHOD')
        self.assertEqual(by['D']['evidence_independence_class'],'GENERATED_FAMILY')
        self.assertEqual(led['strict_upstream_independent_group_count'],1)


    def test_topology_path_does_not_take_version_number(self):
        from pklsa_builder.source_discovery import topology_from_path
        self.assertEqual(topology_from_path(r'C:\\repo\\pack_v0.2.3\\KnotPlot\\knots\\final\\knot_3.1_final.txt'),'3_1')
        self.assertEqual(topology_from_path(r'C:\\repo\\pack_v0.2.3\\3.1\\ideal.txt'),'3_1')

    def test_source_discovery_synthetic_workbench(self):
        import shutil
        from pklsa_builder.source_discovery import discover_workbench
        with tempfile.TemporaryDirectory() as td:
            wb=Path(td)
            fdir=wb/'Ideal_Fremlin_Fseries'/'fremlin'/'3_1'; fdir.mkdir(parents=True)
            shutil.copy2(ROOT/'data'/'fixtures'/'knot.3_1.fseries',fdir/'knot.3_1.fseries')
            idir=wb/'Ideal_Sources'; idir.mkdir()
            shutil.copy2(ROOT/'data'/'fixtures'/'Ideal.txt.gz',idir/'Ideal.txt.gz')
            kdir=wb/'Knot_Library'/'outputs'; kdir.mkdir(parents=True)
            shutil.copy2(ROOT/'data'/'fixtures'/'3_1_katlas_braid.xyz',kdir/'katlas_braid_3_1.xyz')
            cs=discover_workbench(wb,'3_1')
            fam={c.source_family for c in cs}
            self.assertIn('fremlin_fourier',fam)
            self.assertIn('gilbert_ideal',fam)
            self.assertIn('katlas_braid_derived',fam)
            g=[c for c in cs if c.source_family=='gilbert_ideal'][0]
            self.assertAlmostEqual(g.metadata['reference_ropelength'],16.371637,places=6)

    def test_bundled_raw_sources_exist(self):
        self.assertTrue((ROOT/'data'/'topology_sources'/'linkinfo_data_complete.xls').exists())
        self.assertTrue((ROOT/'data'/'topology_sources'/'knotinfo_data_complete.xls.zip').exists())

class RepoFinderV020Tests(unittest.TestCase):
    def _make_full_catalog_tree(self, root: Path):
        import shutil
        # A001
        p=root/'KnotPlot'/'knots'/'3.1'/'final'; p.mkdir(parents=True)
        (p/'knot_3.1_final.txt').write_text('0 0 0\n1 0 0\n1 1 0\n0 1 0\n',encoding='utf-8')
        # A002
        p=root/'KnotPlot'/'Knots_FourierSeries'/'3_1'; p.mkdir(parents=True)
        shutil.copy2(ROOT/'data'/'fixtures'/'knot.3_1.fseries',p/'knot.3_1.fseries')
        # A004
        p=root/'Ideal_Sources'; p.mkdir()
        shutil.copy2(ROOT/'data'/'fixtures'/'Ideal.txt.gz',p/'Ideal.txt.gz')
        (root/'knots_ideal_favorites.txt').write_text('3_1\n',encoding='utf-8')
        (root/'rhof_triage.csv').write_text('knot,rhof\n3_1,1\n',encoding='utf-8')
        # A006
        p=root/'Fremlin_FourierSeries'/'3_1'; p.mkdir(parents=True)
        shutil.copy2(ROOT/'data'/'fixtures'/'knot.3_1.fseries',p/'knot.3_1.fseries')
        # A007 all four declared subroots
        for sub in ('Sources','Derived','Registry','Quarantine'):
            (root/'Knot_Library'/sub).mkdir(parents=True)
        p=root/'Knot_Library'/'Sources'/'FourierSeries_Fremlin'/'3_1'; p.mkdir(parents=True)
        shutil.copy2(ROOT/'data'/'fixtures'/'knot.3_1.fseries',p/'knot.3_1.fseries')
        (root/'Knot_Library'/'Registry'/'registry.json').write_text('{"schema":"test"}',encoding='utf-8')
        (root/'Knot_Library'/'Quarantine'/'bad.xyz').write_text('not geometry\n',encoding='utf-8')
        # A008 source-native PTSA
        p=root/'PTSA_Parametric_Trefoil_Seed_Atlas_v1.0.0'/'candidates'; p.mkdir(parents=True)
        (p/'PTSA_deadbeef0001.xyz').write_text('0 0 0\n1 0 0\n1 1 0\n0 1 0\n',encoding='utf-8')
        (root/'PTSA_Parametric_Trefoil_Seed_Atlas_v1.0.0'/'controls').mkdir()
        (root/'PTSA_Parametric_Trefoil_Seed_Atlas_v1.0.0'/'reveal_only').mkdir()

    def test_repo_scan_a001_a008_coverage(self):
        from pklsa_builder.repo_finder import scan_repository
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self._make_full_catalog_tree(root)
            scan=scan_repository(root,ROOT/'data'/'SST_WORKBENCH_KNOT_SOURCES_LOCATIONS_0.1.json',find_unregistered=False)
            self.assertTrue(scan['coverage_gate']['pass'],scan['coverage_gate'])
            by={x['catalog_id']:x for x in scan['source_results']}
            self.assertEqual(by['A001']['status'],'INGESTED')
            self.assertEqual(by['A003']['status'],'SOURCE_UNAVAILABLE_WITH_PROVENANCE')
            self.assertEqual(by['A005']['status'],'SOURCE_UNAVAILABLE_WITH_PROVENANCE')
            self.assertEqual(by['A008']['role_counts'].get('generated_geometry'),1)
            q=by['A007']['role_counts'].get('quarantine',0)
            self.assertEqual(q,1)

    def test_repo_scan_blocks_missing_declared_a007_subsource(self):
        from pklsa_builder.repo_finder import scan_repository
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self._make_full_catalog_tree(root)
            # A007 Derived is catalogued as present; its disappearance must be visible.
            import shutil
            shutil.rmtree(root/'Knot_Library'/'Derived')
            scan=scan_repository(root,ROOT/'data'/'SST_WORKBENCH_KNOT_SOURCES_LOCATIONS_0.1.json',find_unregistered=False)
            by={x['catalog_id']:x for x in scan['source_results']}
            self.assertEqual(by['A007']['status'],'DECLARED_SUBSOURCE_MISSING')
            self.assertFalse(scan['coverage_gate']['pass'])

    def test_repo_native_ptsa_and_mirror_reconciliation(self):
        from pklsa_builder.repo_finder import scan_repository
        from pklsa_builder.source_discovery import discover_from_repo_scan,dedupe_carriers
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self._make_full_catalog_tree(root)
            scan=scan_repository(root,ROOT/'data'/'SST_WORKBENCH_KNOT_SOURCES_LOCATIONS_0.1.json',find_unregistered=False)
            cs=dedupe_carriers(discover_from_repo_scan(scan,'3_1'))
            self.assertTrue(any(c.source_family=='ptsa' and c.catalog_id=='A008' for c in cs))
            fremlin=[c for c in cs if c.source_family=='fremlin_fourier'][0]
            kp=[c for c in cs if c.source_family=='knotplot_fourier_series'][0]
            self.assertEqual(kp.metadata.get('byte_identical_mirror_of'),fremlin.carrier_id)
            self.assertEqual(kp.independence_group,fremlin.independence_group)

    def test_missing_a004_extra_file_blocks(self):
        from pklsa_builder.repo_finder import scan_repository
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self._make_full_catalog_tree(root)
            (root/'rhof_triage.csv').unlink()
            scan=scan_repository(root,ROOT/'data'/'SST_WORKBENCH_KNOT_SOURCES_LOCATIONS_0.1.json',find_unregistered=False)
            by={x['catalog_id']:x for x in scan['source_results']}
            self.assertEqual(by['A004']['status'],'DECLARED_SUBSOURCE_MISSING')
            self.assertFalse(scan['coverage_gate']['pass'])

    def test_restructured_destination_is_accepted(self):
        from pklsa_builder.repo_finder import scan_repository
        import shutil, json
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            catalog=json.loads((ROOT/'data'/'SST_WORKBENCH_KNOT_SOURCES_LOCATIONS_0.1.json').read_text())
            # Create every post-restructure destination. A004 also needs its two explicitly
            # catalogued extra files inside the destination.
            for src in catalog['sources']:
                d=root/src['destination']; d.mkdir(parents=True,exist_ok=True)
                cid=src['catalog_id']
                if cid=='A001': (d/'3.1').mkdir(); (d/'3.1/knot_3.1_final.txt').write_text('0 0 0\n1 0 0\n1 1 0\n0 1 0\n')
                elif cid=='A002': shutil.copy2(ROOT/'data/fixtures/knot.3_1.fseries',d/'knot.3_1.fseries')
                elif cid=='A003': (d/'QHP_3_1.xyz').write_text('0 0 0\n1 0 0\n1 1 0\n0 1 0\n')
                elif cid=='A004':
                    shutil.copy2(ROOT/'data/fixtures/Ideal.txt.gz',d/'Ideal.txt.gz')
                    (d/'knots_ideal_favorites.txt').write_text('3_1\n'); (d/'rhof_triage.csv').write_text('knot,rhof\n3_1,1\n')
                elif cid=='A005': (d/'katlas.json').write_text('{"3_1":{}}')
                elif cid=='A006': shutil.copy2(ROOT/'data/fixtures/knot.3_1.fseries',d/'knot.3_1.fseries')
                elif cid=='A007':
                    for sub in ('Sources','Derived','Registry','Quarantine'): (d/sub).mkdir()
                    (d/'Registry/registry.json').write_text('{}')
                elif cid=='A008': (d/'candidates').mkdir(); (d/'candidates/PTSA_x.xyz').write_text('0 0 0\n1 0 0\n1 1 0\n0 1 0\n')
            scan=scan_repository(root,ROOT/'data'/'SST_WORKBENCH_KNOT_SOURCES_LOCATIONS_0.1.json',find_unregistered=False)
            self.assertTrue(scan['coverage_gate']['pass'],scan['coverage_gate'])
            self.assertTrue(all(x['resolved_roots'] for x in scan['source_results']))

    def test_unregistered_candidate_finder(self):
        from pklsa_builder.repo_finder import scan_repository
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self._make_full_catalog_tree(root)
            x=root/'External_KnotInfo_Download'; x.mkdir()
            (x/'knotinfo_data_complete.xls').write_bytes(b'test')
            scan=scan_repository(root,ROOT/'data'/'SST_WORKBENCH_KNOT_SOURCES_LOCATIONS_0.1.json',find_unregistered=True)
            self.assertTrue(any('KNOTINFO' in r['candidate_classes'] for r in scan['unregistered_source_candidates']))


if __name__=='__main__': unittest.main()
