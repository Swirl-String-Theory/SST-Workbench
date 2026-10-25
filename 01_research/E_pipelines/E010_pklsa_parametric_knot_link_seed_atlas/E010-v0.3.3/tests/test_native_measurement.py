"""v0.3.7 regression tests: numerical evidence only, no simulated physics claims."""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import subprocess

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from native_measurement import (Evidence, qualify_case, analyze_existing, native_script,
    csv_observation, geom_metrics, generate_measurements, probe_plan,
    _runtime_script, _get_readback, _safe_pass, tolerance, CASES,run_measurements)

PTS='0 0 0\n1 0 0\n0 1 0\n'
GEO=geom_metrics([(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)])

def logfile(*, readback=True, csv_length=None, final_safe=True):
    txt='KnotPlot> A058_SAFE_START\nCurrent position is safe.\nKnotPlot> A058_SAFE_START_END\n'
    if readback: txt+='A058_READBACK_BEGIN\n dstep = 1\nA058_READBACK_END\n'
    txt+='A058_SAFE_FINAL\n'+('Current position is safe.\n' if final_safe else 'Current position is not safe.\n')+'A058_SAFE_FINAL_END\n'
    txt+=f'#0: Nb 3 tot {GEO["length"]:.6f} aspect 1\nKnotPlot> {GEO["rg"]:.6f}\n'
    return txt.encode()

def data_csv(length=None,rg=None):
    return (f'Nbeads,Length,RoG,iteration\n3,{GEO["length"] if length is None else length},'
            f'{GEO["rg"] if rg is None else rg},32\n').encode()

class MeasurementQualificationTest(unittest.TestCase):
    def test_valid_case(self):
        script=native_script(1,'before').encode()
        q=qualify_case(logfile(),PTS.encode(),data_csv(),expected_dstep=1,runtime_script=script)
        self.assertEqual(q['status'],'QUALIFIED_NUMERICAL_MEASUREMENT_ONLY')
        self.assertEqual(q['parameter_gate'],'PASS')
        self.assertEqual(q['scalar_gate'],'PASS')
        self.assertTrue(q['csv_comparison']['iteration_32'])
        self.assertTrue(q['safe_final'])

    def test_zero_csv_fails_even_when_process_log_is_positive(self):
        q=qualify_case(logfile(),PTS.encode(),data_csv(0,0),expected_dstep=1,
                       runtime_script=native_script(1,'after').encode())
        self.assertEqual(q['status'],'FAIL_MEASUREMENT_QUALIFICATION')
        self.assertEqual(q['scalar_gate'],'FAIL')
        self.assertTrue(q['console_comparison']['length_matches_xyz'])

    def test_missing_getter_is_unresolved_not_pass(self):
        q=qualify_case(logfile(readback=False),PTS.encode(),data_csv(),expected_dstep=1,
                       runtime_script=native_script(1,'before').encode())
        self.assertEqual(q['status'],'INCOMPLETE_PARAMETER_READBACK')
        self.assertEqual(q['parameter_gate'],'UNRESOLVED')

    def test_bad_getter_fails(self):
        bad=logfile().replace(b'dstep = 1',b'dstep = 4')
        q=qualify_case(bad,PTS.encode(),data_csv(),expected_dstep=1,
                       runtime_script=native_script(1,'before').encode())
        self.assertEqual(q['parameter_gate'],'FAIL')

    def test_unsafe_marker_fails(self):
        q=qualify_case(logfile(final_safe=False),PTS.encode(),data_csv(),expected_dstep=1,
                       runtime_script=native_script(1,'before').encode())
        self.assertEqual(q['safety_gate'],'FAIL')
        self.assertNotEqual(q['status'],'QUALIFIED_NUMERICAL_MEASUREMENT_ONLY')

    def test_wrong_dstep_script_fails(self):
        q=qualify_case(logfile(),PTS.encode(),data_csv(),expected_dstep=1,
                       runtime_script=native_script(4,'before').encode())
        self.assertEqual(q['script_gate'],'UNRESOLVED_OR_FAIL')
        self.assertNotEqual(q['status'],'QUALIFIED_NUMERICAL_MEASUREMENT_ONLY')

    def test_missing_script_is_not_qualified(self):
        q=qualify_case(logfile(),PTS.encode(),data_csv(),expected_dstep=1)
        self.assertNotEqual(q['status'],'QUALIFIED_NUMERICAL_MEASUREMENT_ONLY')

    def test_csv_tolerance_and_nonfinite_guard(self):
        self.assertTrue(tolerance(round(GEO['length'],6),GEO['length']))
        self.assertEqual(csv_observation(b'Nbeads,Length,RoG,iteration\n3,nan,2,32')['status'],'NONFINITE_CSV')
        self.assertEqual(csv_observation(b'Nbeads,Length\n3,7')['status'],'MISSING_COLUMN')

    def test_alex_helper_error_independent_of_scalars(self):
        q=qualify_case(logfile()+b"*** can't open file `KP-alex.exe'\n",PTS.encode(),data_csv(),
                       expected_dstep=1,runtime_script=native_script(1,'before').encode())
        self.assertEqual(q['alex_gate'],'UNAVAILABLE')
        self.assertEqual(q['scalar_gate'],'PASS')

    def test_no_physical_collision_claim(self):
        q=qualify_case(logfile(),PTS.encode(),data_csv(),expected_dstep=1,runtime_script=native_script(1,'before').encode())
        self.assertEqual(q['scientific_status'],'NO_PHYSICAL_CONCLUSION')
        self.assertEqual(q['safety_gate'],'PASS_SNAPSHOT_MARKERS_ONLY')

    def test_exact_four_sanitized_branches(self):
        self.assertEqual(len(CASES),4)
        for d,o in CASES:
            script=native_script(d,o)
            self.assertIn(f'dstep = {d}',script)
            self.assertIn('velforce = off',script)
            self.assertIn('tanf = off',script)
            self.assertIn('collision fast',script)
            self.assertNotIn('collision allow',script)
            self.assertNotIn('alex -1',script)
            self.assertEqual(script.count('go 32'),1)
            self.assertEqual(script.count('data open'),1)
            if o=='before':self.assertLess(script.index('data open'),script.index('length'))
            else:self.assertGreater(script.index('data open'),script.index('length'))

    def test_runtime_io_absolute_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            text=native_script(1,'before')
            transformed=_runtime_script(text,root)
            self.assertIn((root/'A058_seed.kpf').resolve().as_posix(),transformed)
            self.assertIn((root/'A058_native_metrics.csv').resolve().as_posix(),transformed)
            self.assertIn((root/'A058_final.txt').resolve().as_posix(),transformed)
            self.assertIn('load A058_seed.kpf',text)

    def test_non_destructive_generated_design_and_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            tmp=Path(td);dist=tmp/'dist.zip';out=tmp/'measurements'
            with zipfile.ZipFile(dist,'w') as z:
                z.writestr('mock/demos/Dyna_help.txt','help')
                z.writestr('mock/basic/3.1',b'KnotPlot 1.0  \x0c\n'+b'A'*150)
            doc=generate_measurements(dist,out)
            self.assertEqual(len(doc['conditions']),4)
            plan=probe_plan(out);self.assertEqual(len(plan),4)
            self.assertEqual((out/'dstep_1_before/A058_seed.kpf').read_bytes(),(out/'dstep_4_after/A058_seed.kpf').read_bytes())
            with self.assertRaises(FileExistsError):generate_measurements(dist,out)
            (out/'dstep_1_before/probe.kpc').write_text('tampered',encoding='utf-8')
            with self.assertRaises(ValueError):probe_plan(out)

    def test_qualification_archives_must_be_new_and_read_only(self):
        with tempfile.TemporaryDirectory() as td:
            tmp=Path(td);archive=tmp/'results.zip';out=tmp/'qual'
            payload={}
            for d in (1,4):
                folder=f'A058_probes/dstep_{d}/'
                data=logfile(readback=False).replace(b'dstep = 1',f'dstep = {d}'.encode())
                for name,value in {'NATIVE_STDOUT_PRIVATE.log':data,'A058_final.txt':PTS.encode(),
                    'A058_native_metrics.csv':data_csv(0,0),'probe.native.kpc':native_script(d,'before').encode(),
                    'probe.kpc':native_script(d,'before').encode(), 'A058_seed.kpf':b'test_seed_bytes'}.items():
                    payload[folder+name]=value
            rows=[]
            for d in (1,4):
                folder=f'A058_probes/dstep_{d}/'
                rows.append({'dstep':d,'returncode':0,'timeout':False,
                             'private_log_sha256':hashlib.sha256(payload[folder+'NATIVE_STDOUT_PRIVATE.log']).hexdigest(),
                             'coordinate_sha256':hashlib.sha256(payload[folder+'A058_final.txt']).hexdigest(),
                             'runtime_script_sha256':hashlib.sha256(payload[folder+'probe.native.kpc']).hexdigest(),
                             'source_probe_sha256':hashlib.sha256(payload[folder+'probe.kpc']).hexdigest()})
            payload['A058_probes/NATIVE_RESULTS.json']=json.dumps({'conditions':rows}).encode()
            payload['A058_probes/PROBES.json']=json.dumps({'seed_sha256':hashlib.sha256(b'test_seed_bytes').hexdigest()}).encode()
            with zipfile.ZipFile(archive,'w') as z:
                for name,value in payload.items():z.writestr(name,value)
            before=hashlib.sha256(archive.read_bytes()).hexdigest()
            doc=analyze_existing(archive,out)
            self.assertFalse(doc['all_measurements_qualified'])
            self.assertEqual(doc['conditions']['dstep_1']['original_run_record_gate'],'PASS')
            self.assertTrue((out/'MEASUREMENT_MATRIX.csv').is_file())
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),before)
            with self.assertRaises(FileExistsError): analyze_existing(archive,out)

    def test_mock_native_four_case_end_to_end_receipts_and_path_separation(self):
        # Only a fake process with controlled output; never called a science run.
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); exe=root/'KnotPlot.exe';exe.write_bytes(b'mock exe')
            z=root/'mock.zip';out=root/'new'
            with zipfile.ZipFile(z,'w') as arch:
                arch.writestr('mock/demos/Dyna_help.txt','help')
                arch.writestr('mock/basic/3.1',b'KnotPlot 1.0'+b'X'*200)
            def fake_run(command,**kw):
                native_script_body=kw['stdin'].read().decode('utf-8')
                is_four='dstep = 4' in native_script_body
                is_before=native_script_body.index('data open') < native_script_body.index('length')
                sub=out/(('dstep_4_' if is_four else 'dstep_1_')+('before' if is_before else 'after'))
                # Check all paths appear absolute and output inside A058 folder.
                self.assertIn((sub/'A058_final.txt').resolve().as_posix(),native_script_body)
                self.assertEqual(kw['cwd'],exe.parent)
                (sub/'A058_final.txt').write_text(PTS)
                (sub/'A058_native_metrics.csv').write_bytes(data_csv())
                data=logfile().replace(b'dstep = 1',b'dstep = 4' if is_four else b'dstep = 1')
                kw['stdout'].write(data)
                return subprocess.CompletedProcess(command,0)
            # Construct this closure without rewriting real run bytes.
            with patch('native_measurement.subprocess.run',side_effect=fake_run) as mock:
                doc=run_measurements(exe,out,30,dist=z)
            self.assertEqual(mock.call_count,4)
            self.assertTrue(doc['all_measurements_qualified'])
            self.assertEqual(len(doc['conditions']),4)
            self.assertTrue((out/'qualification/MEASUREMENT_MATRIX.csv').exists())
            with self.assertRaises(FileExistsError):run_measurements(exe,out,30)

    def test_fails_when_historical_receipt_hash_is_mismatched(self):
        with tempfile.TemporaryDirectory() as td:
            tmp=Path(td);d=tmp/'native';(d/'dstep_1').mkdir(parents=True);(d/'dstep_4').mkdir()
            for i in (1,4):
                p=d/f'dstep_{i}'
                (p/'NATIVE_STDOUT_PRIVATE.log').write_bytes(logfile(readback=False))
                (p/'A058_final.txt').write_text(PTS)
                (p/'A058_native_metrics.csv').write_bytes(data_csv())
                (p/'probe.native.kpc').write_text(native_script(i,'before'))
            (d/'NATIVE_RESULTS.json').write_text(json.dumps({'conditions':[]}))
            doc=analyze_existing(d,tmp/'qualification')
            self.assertEqual(doc['conditions']['dstep_1']['status'],'INVALID_HISTORICAL_RECEIPT')

if __name__=='__main__': unittest.main()
