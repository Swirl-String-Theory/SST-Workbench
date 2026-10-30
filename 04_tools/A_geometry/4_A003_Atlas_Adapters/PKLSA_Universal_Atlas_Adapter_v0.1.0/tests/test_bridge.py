import json
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np

from pklsa_bridge import AtlasBridge, ConsumerDataset, AdmissionError, AtlasContractError, resample_closed_arclength
from pklsa_bridge.adapter import EXPECTED_INDEX_SHA256, verify_export, geometry_summary


ATLAS=os.environ.get('PKLSA_TEST_ATLAS')


class PureTests(unittest.TestCase):
    def test_periodic_interpolation(self):
        square=np.array([[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.]])
        out=resample_closed_arclength(square,8)
        self.assertEqual(out.shape,(8,3))
        np.testing.assert_allclose(out[::2],square)
        self.assertEqual(geometry_summary([out])['component_count'],1)

    def test_bad_count(self):
        with self.assertRaises(AtlasContractError):
            resample_closed_arclength(np.zeros((4,3)),10)

    def test_reject_duplicate_endpoint(self):
        sample=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[0.,0.,0.]])
        with self.assertRaises(AtlasContractError):
            resample_closed_arclength(sample,16)

    def test_nonfinite_and_bad_count(self):
        with self.assertRaises(AtlasContractError):
            resample_closed_arclength(np.ones((3,3))*np.nan,16)
        with self.assertRaises(AtlasContractError):
            resample_closed_arclength(np.eye(3),2)


@unittest.skipUnless(ATLAS and Path(ATLAS).is_file() or ATLAS and Path(ATLAS).is_dir(),
                     'Provide --atlas to selftest for full integration checks')
class RealAtlasIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge=AtlasBridge(ATLAS)

    @classmethod
    def tearDownClass(cls):
        cls.bridge.close()
        # Original E010 reader modules must not persist from a deleted ZIP cache.
        with AtlasBridge(ATLAS) as fresh:
            assert len(fresh.records)==11757

    def test_count_and_pin(self):
        self.assertEqual(len(self.bridge.records),11757)
        self.assertEqual(self.bridge.index_sha,EXPECTED_INDEX_SHA256)

    def test_default_research_exclusion(self):
        self.assertEqual(len(self.bridge.query(collection='ruban_v036')),0)
        self.assertEqual(len(self.bridge.query(collection='historical_v031')),4497)

    def test_explicit_research_optin(self):
        records=self.bridge.query(embedding='T_2_3',variant='nominal',allow_research=True,limit=3)
        self.assertEqual(len(records),3)
        self.assertTrue(all(self.bridge.records[r]['research_only'] for r in records))

    def test_reject_research_metadata_without_optin(self):
        ident=self.bridge.query(embedding='T_2_3',variant='nominal',allow_research=True,limit=1)[0]
        with self.assertRaises(AdmissionError):self.bridge.describe(ident)
        with self.assertRaises(AdmissionError):self.bridge.load(ident)
        with self.assertRaises(AdmissionError):self.bridge.query(ids=[ident])

    def test_ruban_load_original_reader_multi_component(self):
        ids=self.bridge.query(embedding='T_3_6',variant='nominal',allow_research=True,limit=1)
        self.assertEqual(len(ids),1)
        parts=self.bridge.load(ids[0],allow_research=True)
        self.assertEqual([p.shape for p in parts],[(1024,3)]*3)
        self.assertTrue(np.isfinite(np.concatenate(parts)).all())

    def test_historical_load_original_reader(self):
        ids=self.bridge.query(topology='3_1',collection='historical_v031',limit=20)
        self.assertGreater(len(ids),0)
        parts=self.bridge.load(ids[0])
        self.assertTrue(len(parts)>=1)
        self.assertTrue(np.isfinite(np.concatenate(parts)).all())

    def test_filter_topology_distinct_from_embedding(self):
        x=self.bridge.query(topology='5_2',collection='historical_v031',limit=3)
        self.assertEqual(len(x),3)
        y=self.bridge.query(embedding='T_2_5',collection='ruban_v036',allow_research=True,limit=3)
        self.assertEqual(len(y),3)
        self.assertTrue(all(self.bridge.records[r]['topology_id']!='5_2' for r in y))

    def test_out_of_index_b0_cannot_be_fabricated(self):
        ids=self.bridge.query(embedding='T_2_3',variant='nominal',
                              b0_min=.36,b0_max=.40,allow_research=True)
        self.assertEqual(ids,[])

    def test_query_b0_and_source_independence(self):
        ids=self.bridge.query(embedding='T_2_3',variant='nominal',b0_min=.28,b0_max=.30,
                              allow_research=True,limit=100)
        self.assertTrue(ids)
        self.assertTrue(all(.28-1e-12<=self.bridge.records[r]['B0']<=.30+1e-12 for r in ids))
        self.assertEqual(len({self.bridge.records[r]['source_independence_group'] for r in ids}),1)

    def test_exact_duplicate_detection(self):
        ids=self.bridge.query(collection='ruban_v036',allow_research=True,unique_geometry=True,limit=20)
        self.assertEqual(len(ids),len({self.bridge.records[r]['geometry_sha256'] for r in ids}))

    def test_export_immutable_manifest_and_verify(self):
        ids=self.bridge.query(embedding='T_3_6',variant='nominal',allow_research=True,limit=1)
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'B007_demo_dataset'
            self.bridge.export_dataset(ids,target,allow_research=True,resample_points=256,
                                      consumer='B007-v0.2.3-intake-pilot')
            report=verify_export(target)
            self.assertEqual(report['records'],1)
            self.assertEqual(report['files'],3)
            downstream=ConsumerDataset(target)
            self.assertEqual(downstream.list_ids(),ids)
            self.assertEqual([p.shape for p in downstream.load(ids[0])],[(256,3)]*3)
            self.assertEqual(downstream.metadata(ids[0])['collection'],'ruban_v036')
            manifest=json.loads((target/'DATASET_MANIFEST.json').read_text())
            self.assertEqual(manifest['qualification']['scientific_admission'],'NOT_GRANTED')
            self.assertFalse(manifest['coordinate_policy']['automatic_SI_conversion'])
            self.assertTrue(manifest['records'][0]['transforms']['arclength_interpolation'])
            with self.assertRaises(AtlasContractError):
                self.bridge.export_dataset(ids,target,allow_research=True)
            component=target/'seeds'/ids[0]/'component_001.xyz'
            with component.open('a') as file:file.write('1 2 3\n')
            with self.assertRaises(AtlasContractError):verify_export(target)

    def test_no_export_inside_atlas(self):
        ident=self.bridge.query(embedding='T_2_3',variant='nominal',allow_research=True,limit=1)
        target=self.bridge.root/'BAD_OUTPUT'
        with self.assertRaises(AtlasContractError):
            self.bridge.export_dataset(ident,target,allow_research=True)

    def test_no_duplicate_records(self):
        ident=self.bridge.query(embedding='T_2_3',variant='nominal',allow_research=True,limit=1)[0]
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(AtlasContractError):
                self.bridge.export_dataset([ident,ident],Path(t)/'bad',allow_research=True)
            self.assertFalse((Path(t)/'bad').exists())

    def test_unqualified_not_new_physics(self):
        rec=self.bridge.source_summary(self.bridge.query(embedding='T_2_3',allow_research=True,limit=1)[0],
                                       allow_research=True)
        self.assertTrue(rec['research_only'])
        self.assertFalse(rec['production_admission'])
        self.assertEqual(rec['gates']['scientific'],'NOT_RUN')


if __name__=='__main__':unittest.main()
