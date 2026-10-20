"""Non-overwrite and unique-run assurance for A065 v0.3.0-r1."""
import hashlib
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
R=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R))
from triadic import launch


class UniqueExportContract(unittest.TestCase):
    def test_unique_run_allocation(self):
        with tempfile.TemporaryDirectory() as td, patch.object(launch,'ROOT',pathlib.Path(td)):
            k1,p1=launch._new_run_dir();k2,p2=launch._new_run_dir()
            self.assertNotEqual(k1,k2)
            self.assertNotEqual(p1,p2)
            self.assertTrue(p1.is_dir() and p2.is_dir())

    def test_existing_export_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)
            src=p/'src';dst=p/'dst'
            src.write_bytes(b'new payload');dst.write_bytes(b'existing payload')
            digest=hashlib.sha256(dst.read_bytes()).hexdigest()
            with self.assertRaises(FileExistsError):launch._copy_new(src,dst)
            self.assertEqual(hashlib.sha256(dst.read_bytes()).hexdigest(),digest)

    def test_zip_create_only(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td);src=p/'source.dat';src.write_bytes(b'fixed evidence')
            dst=p/'unique_run.zip';launch._zip_new(dst,[(src,'source.dat')]);digest=hashlib.sha256(dst.read_bytes()).hexdigest()
            with self.assertRaises(FileExistsError):launch._zip_new(dst,[(src,'source.dat')])
            self.assertEqual(hashlib.sha256(dst.read_bytes()).hexdigest(),digest)
            with zipfile.ZipFile(dst) as z:self.assertEqual(z.read('source.dat'),b'fixed evidence')

    def test_tex_self_contained_format(self):
        from triadic.report_tex import write_tex
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)
            # Generate fresh real synthetic results in an isolated fixture; never rely on stale outputs.
            from triadic.provider_manifest import write_new
            from triadic.runner import run_blind
            import shutil
            from unittest.mock import patch
            for directory in ('data','seals','preregistration'):
                shutil.copytree(R/directory,p/directory)
            write_new(p)
            with patch.dict('os.environ',{'SST_A065_ISOLATED_RUN':'1'}):
                run_blind(p)
            path=write_tex(p,p/'report.tex',run_id='A065-v0.3.1__test',label='SELFTEST',frame_state='NOT_RUN')
            content=path.read_text()
            self.assertIn('\\documentclass',content)
            self.assertNotIn('\\input{',content)
            self.assertNotIn('\\include{',content)
            with self.assertRaises(FileExistsError):write_tex(p,path,run_id='A065-v0.3.1__test',label='SELFTEST',frame_state='NOT_RUN')


if __name__=='__main__':unittest.main()
