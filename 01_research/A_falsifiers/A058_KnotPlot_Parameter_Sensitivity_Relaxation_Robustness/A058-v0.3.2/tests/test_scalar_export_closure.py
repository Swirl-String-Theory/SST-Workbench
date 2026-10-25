"""v0.3.8 closure contract tests, no actual KnotPlot solver emulated as science."""
from __future__ import annotations
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'tools'))
from scalar_export_closure import (audit_v037,generate,_plan,_runtime_script,_script,
                                  qualify_native,run_native,SCHEMA,ITERATIONS,CASES,
                                  STATUS_PASS,_state_param)
from native_measurement import geom_metrics

PTS = b'0 0 0\n1 0 0\n0 1 0\n'
GEOM = geom_metrics([(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)])


def state_log(d=1,n=32,*,safe=True,drift=False):
    forces='velforce = off\ntanforce = off\ngravity = off\nthermalforce = off\n'
    return ('A058_V038_INITIAL_STATE_BEGIN\n'
            f'dstep = {d}\niteration = 0\n{forces}'
            'A058_V038_INITIAL_STATE_END\n'
            'A058_SAFE_START\nCurrent position is safe.\nA058_SAFE_START_END\n'
            'A058_V038_FINAL_STATE_BEGIN\n'
            f'dstep = {4 if drift else d}\niteration = {n}\n{forces}'
            'A058_V038_FINAL_STATE_END\n'
            f'A058_SAFE_FINAL\nCurrent position is {"safe" if safe else "not safe"}.\nA058_SAFE_FINAL_END\n').encode()


def sample_csv(n=32,*,length=None,rg=None,nb=3):
    return (f'Nbeads,Length,RoG,iteration\n{nb},'
            f'{GEOM["length"] if length is None else length},'
            f'{GEOM["rg"] if rg is None else rg},{n}\n').encode()


def native_case(*,d=1,n=32,csvdata=None,log=None,script=None,rc=0,timeout=False):
    source=_script(d,n)
    with tempfile.TemporaryDirectory() as td:
        scr=_runtime_script(source,Path(td)) if script is None else script
        return qualify_native(state_log(d,n) if log is None else log,
                              PTS,sample_csv(n) if csvdata is None else csvdata,
                              dstep=d,iterations=n,native_script=scr.encode(),
                              returncode=rc,timedout=timeout)


class ScalarExportClosureTest(unittest.TestCase):
    def test_six_explicit_registered_cases(self):
        self.assertEqual(len(CASES),6)
        self.assertEqual(CASES,((1,32),(1,128),(1,512),(4,32),(4,128),(4,512)))
        for d,n in CASES:
            s=_script(d,n)
            self.assertIn(f'go {n}',s)
            self.assertLess(s.index('data open'),s.index('length\n'))
            self.assertLess(s.index('length\n'),s.index('rog\n'))
            self.assertLess(s.index('rog\n'),s.index('\ndata\n'))
            self.assertEqual(s.count('data open'),1)
            self.assertIn('collision fast',s)
            self.assertIn('velforce = off',s)
            self.assertNotIn('collision allow',s)
            self.assertNotIn('alex -1',s)

    def test_positive_all_six_can_qualify_numerics_only(self):
        for d,n in CASES:
            with self.subTest(dstep=d,iterations=n):
                r=native_case(d=d,n=n)
                self.assertEqual(r['status'],STATUS_PASS)
                self.assertTrue(r['parameter_gate'])
                self.assertTrue(r['csv_gate'])
                self.assertEqual(r['physical_convergence'],'UNRESOLVED')
                self.assertEqual(r['continuous_collision_avoidance'],'NOT_CERTIFIED')

    def test_zero_csv_failure(self):
        self.assertEqual(native_case(csvdata=sample_csv(length=0,rg=0))['status'],
                         'FAIL_SCALAR_EXPORT_CONTRACT')

    def test_csv_wrong_iteration_and_wrong_bead_count_fail(self):
        self.assertFalse(native_case(csvdata=sample_csv(128))['csv_gate'])
        self.assertFalse(native_case(csvdata=sample_csv(nb=47))['csv_gate'])

    def test_csv_malformed_nonfinite_and_extra_row_fail(self):
        self.assertFalse(native_case(csvdata=sample_csv(length='NaN'))['csv_gate'])
        self.assertFalse(native_case(csvdata=sample_csv()+sample_csv())['csv_gate'])
        self.assertFalse(native_case(csvdata=b'not a csv')['csv_gate'])

    def test_bad_readback_dstep_or_iteration_fails(self):
        self.assertFalse(native_case(log=state_log(drift=True))['parameter_gate'])
        self.assertFalse(native_case(log=state_log(n=128))['parameter_gate'])

    def test_unsafe_markers_are_fatal_even_if_process_success(self):
        r=native_case(log=state_log(safe=False))
        self.assertFalse(r['final_safe']);self.assertEqual(r['status'],'FAIL_SCALAR_EXPORT_CONTRACT')

    def test_force_readback_missing_or_on_is_failure(self):
        log=state_log().replace(b'velforce = off',b'velforce = on')
        r=native_case(log=log)
        self.assertFalse(r['parameter_gate'])

    def test_process_exit_timeout_and_fatal_log_fail(self):
        self.assertFalse(native_case(rc=2)['process_gate'])
        self.assertFalse(native_case(timeout=True)['process_gate'])
        self.assertFalse(native_case(log=state_log()+b'unknown command\n')['process_gate'])

    def test_strict_command_order_and_no_redundant_data(self):
        with tempfile.TemporaryDirectory() as td:
            script=_runtime_script(_script(1,32),Path(td))
            broken=script.replace('length\nrog\ndata\n','data\nlength\nrog\n')
            self.assertFalse(native_case(script=broken)['script_order_gate'])
            doubled=script.replace('\ndata\ndata close','\ndata\ndata\ndata close')
            self.assertFalse(native_case(script=doubled)['script_order_gate'])

    def test_missing_evidence_is_failure_not_fiction(self):
        r=qualify_native(None,PTS,sample_csv(),dstep=1,iterations=32,native_script=b'foo',returncode=0,timedout=False)
        self.assertEqual(r['status'],'FAIL_MISSING_NATIVE_EVIDENCE')

    def test_real_distribution_generation_and_immutability(self):
        dist=next((p for p in (BASE/'kpdist-23mar2025.zip',Path('/mnt/data/kpdist-23mar2025.zip')) if p.is_file()), BASE/'kpdist-23mar2025.zip')
        if not dist.is_file(): self.skipTest('Original optional distribution not installed with release')
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'new'
            record=generate(dist,out)
            self.assertEqual(len(record['cases']),6)
            self.assertEqual(len(_plan(out)),6)
            with self.assertRaises(FileExistsError):generate(dist,out)
            (out/'dstep_1_go_32/probe.kpc').write_text('tampered')
            with self.assertRaises(ValueError):_plan(out)

    def test_generated_inputs_mock_dist_and_absolute_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);dist=root/'dist.zip';out=root/'run'
            with zipfile.ZipFile(dist,'w') as z:
                z.writestr('mock/demos/Dyna_help.txt','sample')
                z.writestr('mock/basic/3.1',b'KnotPlot 1.0'+b'A'*200)
            generate(dist,out)
            plan=_plan(out)
            for row in plan:
                self.assertIn((row['folder']/'A058_seed.kpf').as_posix(),row['runtime'])
                self.assertIn((row['folder']/'A058_final.txt').as_posix(),row['runtime'])
            (out/'dstep_4_go_512/NATIVE_STDOUT_PRIVATE.log').write_bytes(b'previous')
            with self.assertRaises(FileExistsError):_plan(out)

    def test_mock_native_end_to_end_positive_reconciles_six(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);exe=root/'KnotPlot.exe';exe.write_bytes(b'mock exe')
            dist=root/'dist.zip';out=root/'new'
            with zipfile.ZipFile(dist,'w') as z:
                z.writestr('mock/demos/Dyna_help.txt','sample')
                z.writestr('mock/basic/3.1',b'KnotPlot 1.0'+b'A'*200)
            def simulate(cmd,**kw):
                data=kw['stdin'].read().decode()
                d=int(__import__('re').search(r'(?m)^dstep = (\d+)',data).group(1))
                n=int(__import__('re').search(r'(?m)^go (\d+)',data).group(1))
                path=recover(data,'data open ');save=recover(data,'save ').rsplit(' ascii',1)[0]
                Path(path).write_bytes(sample_csv(n))
                Path(save).write_bytes(PTS)
                kw['stdout'].write(state_log(d,n))
                class CP: returncode=0
                self.assertEqual(kw['cwd'],exe.parent)
                return CP()
            def recover(body,prefix):
                return next(s[len(prefix):].strip() for s in body.splitlines() if s.startswith(prefix))
            with patch('scalar_export_closure.subprocess.run',side_effect=simulate):
                doc=run_native(exe,out,60,dist=dist)
            self.assertEqual(doc['native_scalar_closure'],'PASS')
            self.assertEqual(doc['qualified_conditions'],6)
            self.assertEqual(len(doc['conditions']),6)
            self.assertTrue((out/'qualification/CLOSURE_MATRIX.csv').is_file())
            with self.assertRaises(FileExistsError):run_native(exe,out,60,dist=dist)

    def test_prior_v037_four_branch_real_receipt(self):
        source=next((p for p in (BASE/'A058_measurement_v037.zip',Path('/mnt/data/A058_measurement_v037.zip')) if p.is_file()),BASE/'A058_measurement_v037.zip')
        if not source.is_file():self.skipTest('User native v0.3.7 ZIP not bundled with source release')
        before=hashlib.sha256(source.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            report=audit_v037(source,Path(td)/'result')
            self.assertEqual(report['historical_method_closure'],'PASS')
            self.assertEqual(report['positive_controls_pass'],2)
            self.assertEqual(report['negative_controls_reproduce'],2)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before)
            self.assertEqual(report['full_internal_cause'],'NOT_ISOLATED')

    def test_invalid_historical_native_receipt_fails_closed(self):
        source=next((p for p in (BASE/'A058_measurement_v037.zip',Path('/mnt/data/A058_measurement_v037.zip')) if p.is_file()),BASE/'A058_measurement_v037.zip')
        if not source.is_file():self.skipTest('User native v0.3.7 ZIP not bundled with source release')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'tampered.zip'
            with zipfile.ZipFile(source) as a,zipfile.ZipFile(path,'w') as b:
                for entry in a.infolist():
                    content=a.read(entry.filename)
                    if entry.filename.endswith('dstep_1_before/A058_native_metrics.csv'):
                        content=content.replace(b'56.757945',b'99.757945')
                    b.writestr(entry.filename,content)
            doc=audit_v037(path,Path(td)/'audit')
            self.assertNotEqual(doc['historical_method_closure'],'PASS')

    def test_launcher_routes_all_closure_modes_and_preserves_old(self):
        cmd=(BASE/'run_all.cmd').read_text(encoding='utf-8')
        for keyword in ('AUDIT_SCALAR_CLOSURE','GENERATE_SCALAR_CLOSURE','RUN_SCALAR_CLOSURE','QUALIFY_EXISTING'):
            self.assertIn(keyword,cmd)
        self.assertIn('tools\\scalar_export_closure.py',cmd)
        self.assertIn('tools\\native_measurement.py',cmd)


if __name__=='__main__':unittest.main()
