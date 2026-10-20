from __future__ import annotations
import importlib.util,json,sys,tempfile,unittest,zipfile
from pathlib import Path
import numpy as np

MODULE=Path(__file__).resolve().parents[1]/'data'/'f005_data_pilot_v0.2.0.py'
spec=importlib.util.spec_from_file_location('f005',MODULE)
f005=importlib.util.module_from_spec(spec);spec.loader.exec_module(f005)

class TestDataPilot(unittest.TestCase):
    def test_time_explicit_units(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'time_vector.csv';p.write_text('sample_index,time_s\n0,0.000\n1,0.004\n2,0.008\n')
            tt,d=f005.read_time(p,3)
            self.assertEqual(d['status'],'PASS')
            self.assertAlmostEqual(d['dt_seconds'],0.004)
    def test_time_no_label_is_unresolved(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'time_vector.csv';p.write_text('foo,bar\n0,0.000\n1,0.004\n2,0.008\n')
            tt,d=f005.read_time(p,3)
            self.assertIsNone(tt);self.assertEqual(d['status'],'UNRESOLVED')
    def test_nobody_only_one_zip_member(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'sources').mkdir()
            with zipfile.ZipFile(root/'sources'/'DATASET.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr(f005.DEFAULT_MEMBER,'time,pressure\n0,0.1\n1,0.2\n')
                z.writestr('DATASET/FloatingBody/a.csv','not allowed')
            d=f005.large_single_member(root,root/'out',None,f005.DEFAULT_MEMBER)
            self.assertEqual(d['status'],'ONE_CSV_CRC_VERIFIED')
            self.assertTrue((root/'out'/'NoBody_single_pressure_preview.txt').exists())
            with self.assertRaises(ValueError): f005.large_single_member(root,root/'out',None,'DATASET/FloatingBody/a.csv')
    def test_robot_synthetic_exposes_uncertified_shape(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);folder=root/'outputs'/'data_preflight_v0.1.0'/'data'/'robot_sloshing'/'raw_extracted';folder.mkdir(parents=True)
            t=np.arange(120)*0.004
            a=np.zeros((12,120)); a[:,20:35]=0.3
            y=np.array([0.1*np.sin(2*np.pi*2*t)*np.exp(-t) for _ in range(12)])
            np.save(folder/'INPUT_TRAIN.npy',a)
            np.save(folder/'OUTPUT_TRAIN.npy',y)
            (folder/'time_vector.csv').write_text('sample_index,time_s\n'+''.join(f'{i},{v:.6f}\n' for i,v in enumerate(t)))
            (folder/'trajectory_metadata.csv').write_text('id,subset\n'+''.join(f'{i},standard\n' for i in range(12)))
            r=f005.robot_pilot(root,root/'pilot',8,20261019)
            self.assertEqual(r['status'],'ROBOT_INGESTED_DESCRIPTIVE_ONLY')
            self.assertEqual(r['time']['status'],'PASS')
            self.assertFalse(r['arrays']['published_dimensions_match'])
            self.assertEqual(r['split']['status'],'BLOCKED_SHAPE_OR_METADATA')
            self.assertTrue((root/'pilot'/'F005_robot_pilot_report_DEVELOPMENT.pdf').is_file())
    def test_md5_known_string(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.txt';p.write_bytes(b'abc')
            self.assertEqual(f005.md5_file(p),'900150983cd24fb0d6963f7d28e17f72')
    def test_fft_diagnostic_returns_resolution(self):
        t=np.arange(500)*0.004;signal=np.sin(2*np.pi*2*t)
        d=f005.diagnostic_frequency(signal,.004)
        self.assertAlmostEqual(d['peak_hz'],2.0)
        self.assertAlmostEqual(d['resolution_hz'],.5)

if __name__=='__main__':unittest.main()
