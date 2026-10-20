import tempfile
import unittest
from pathlib import Path
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"data"))
from f005_sloshing_preflight import inspect_zip, safe_member, extract_robot, main

class PreflightTests(unittest.TestCase):
    def test_unsafe_path(self):
        i = zipfile.ZipInfo('../evil.txt')
        self.assertFalse(safe_member(i))
    def test_unsafe_absolute(self):
        i = zipfile.ZipInfo('/root/evil.txt')
        self.assertFalse(safe_member(i))
    def test_robot_inventory_and_extraction(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'sources').mkdir()
            f=root/'sources'/'renamed.zip'
            with zipfile.ZipFile(f,'w') as z:
                for n in ['dir/INPUT_TRAIN.npy','dir/OUTPUT_TRAIN.npy','dir/time_vector.csv','dir/trajectory_metadata.csv','dir/load_dataset.py']:
                    z.writestr(n,b'abcd')
            result=inspect_zip(f,root)
            self.assertEqual(result['dataset_class'],'ROBOT_SLOSHING')
            self.assertEqual(result['status'],'ZIP_CENTRAL_DIRECTORY_OK')
            self.assertEqual(main(['--root',str(root),'--extract-robot']),0)
            self.assertTrue((root/'outputs'/'data_preflight_v0.1.0'/'data'/'robot_sloshing'/'raw_extracted'/'INPUT_TRAIN.npy').exists())
    def test_large_metadata_only(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'sources').mkdir()
            f=root/'sources'/'DATASET.zip'
            with zipfile.ZipFile(f,'w') as z:
                z.writestr('DATASET/NoBody/2deg_105_0.4375Hz/measurement.csv','1,2,3')
                z.writestr('DATASET/FloatingBody/2deg_105_0.4375Hz/measurement.csv','1,2,3')
            result=inspect_zip(f,root)
            self.assertEqual(result['dataset_class'],'ROLL_TANK_SLOSHING')
            self.assertEqual(result['NoBody_candidates'],1)
            self.assertEqual(result['FloatingBody_candidates'],1)
            self.assertEqual(main(['--root',str(root)]),0)
            self.assertFalse((root/'outputs'/'data_preflight_v0.1.0'/'data').exists())

if __name__=='__main__':unittest.main()
