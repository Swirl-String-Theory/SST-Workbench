from __future__ import annotations
import hashlib,importlib.util,io,json,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'payload'/'fetch_data.py'
if not SOURCE.is_file(): SOURCE=ROOT/'experiment'/'fetch_data.py'
spec=importlib.util.spec_from_file_location('_gpe_fetch_for_test',SOURCE)
fetch=importlib.util.module_from_spec(spec);spec.loader.exec_module(fetch)

class TestDownloader(unittest.TestCase):
    def test_offline_missing_does_not_fabricate_data(self):
        with tempfile.TemporaryDirectory() as td:
            info=fetch.run(Path(td),offline=True)
            self.assertFalse(info['exists']);self.assertFalse(info['verified'])
    def test_archive_integrity_and_corruption(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);p=d/fetch.RECORD['name']
            with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_DEFLATED) as f:
                f.writestr('example.csv','x,y\n1,2\n')
            original=fetch.RECORD['md5']
            try:
                fetch.RECORD['md5']=fetch.digest(p,'md5')
                info=fetch.run(d,offline=True)
                self.assertTrue(info['verified']);self.assertEqual(info['file_count'],1)
                p.write_bytes(p.read_bytes()+b'garbage')
                newer=fetch.run(d,offline=True)
                # checksum and SHA fingerprint must fail for modified bytes
                self.assertFalse(newer['verified'])
            finally:
                fetch.RECORD['md5']=original

if __name__=='__main__':unittest.main()
