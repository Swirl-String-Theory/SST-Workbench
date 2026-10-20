from __future__ import annotations
import sys,unittest,json,tempfile,hashlib,os,zipfile
from unittest.mock import patch
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from triadic.export_audit_v043 import load_protocol,rederive,inspect_array_bytes,EvidenceError
from triadic.gpu_trace_v043 import solve_trace,registered_framework_gates,operators_fingerprint
from triadic.euler3d_v040 import taylor_green,integrate
from triadic.gpu_euler_v041 import cpu_generic

class PostExportTests(unittest.TestCase):
    def test_protocol_pinned(self):
        cfg,pin=load_protocol(ROOT)
        self.assertEqual(cfg['grids'],[48,64,96]);self.assertEqual(cfg['T'],.08)
        self.assertEqual(cfg['coarse_steps'],16);self.assertEqual(cfg['refined_steps'],32)
    def test_append_only_gates(self):
        from framework_bridge.install import patch_postexport_gate_plan,patch_arc_gpu_gate_plan,patch_cpu_gate_plan
        original=patch_arc_gpu_gate_plan(patch_cpu_gate_plan({'gates':[{'gate_id':'G1'},{'gate_id':'G3'},{'gate_id':'G5'},{'gate_id':'G8'}]}))
        before=[dict(x) for x in original['gates']]
        patched=patch_postexport_gate_plan(original)
        self.assertEqual(patched['gates'][:len(before)],before)
        self.assertEqual([x['gate_id'] for x in patched['gates'][-6:]],[f'G{i}' for i in range(49,55)])
    def test_missing_extended_stays_unexecuted(self):
        r=registered_framework_gates(ROOT)
        self.assertEqual(r['gates']['G50']['status'],'NOT_RUN_PREREQUISITE')
        self.assertEqual(r['gates']['G54']['status'],'UNRESOLVED')
    def test_external_framework_evidence_explicit_and_fail_closed(self):
        from triadic.gpu_trace_v043 import registered_framework_gates
        with patch.dict(os.environ,{'SST_A065_V043_EVIDENCE_ZIP':str(ROOT/'DOES_NOT_EXIST.zip')}):
            with self.assertRaises(EvidenceError):registered_framework_gates(ROOT)
        with tempfile.TemporaryDirectory() as td:
            archive=Path(td)/'BLIND_RESULTS.zip'
            with zipfile.ZipFile(archive,'w') as z:z.writestr('README.txt','no arrays')
            with patch.dict(os.environ,{'SST_A065_V043_EVIDENCE_ZIP':str(archive)}):
                r=registered_framework_gates(ROOT)
                self.assertEqual(r['gates']['G50']['status'],'NOT_RUN_PREREQUISITE')
                self.assertEqual(r['gates']['G49']['status'],'NOT_RUN_PREREQUISITE')
    def test_independent_taylor_green(self):
        n=16;L=2*np.pi;u0=taylor_green(n)
        a=solve_trace(np,u0,L,.08,16,trace_indices=(0,4,8,12,16),snapshot_indices=(0,8,16))
        b=integrate(u0,L,.08,16)
        q=a['snapshots'][16]
        for field in ('u','omega','p'):
            self.assertLess(np.linalg.norm(q[field]-b[field])/max(np.linalg.norm(b[field]),1e-30),1e-12)
        self.assertEqual(len(a['trace']),5);self.assertEqual(len(a['snapshots']),3)
        checks=rederive(q['u'],q['omega'],q['p'],L)
        self.assertLess(checks['divergence_rms'],1e-10)
        self.assertLess(checks['curl_l2'],1e-10)
        self.assertLess(checks['pressure_poisson_l2'],1e-10)
    def test_generated_cpu_npz_passes(self):
        cfg,_=load_protocol(ROOT)
        u0=taylor_green(16)
        run=solve_trace(np,u0,2*np.pi,.08,16,trace_indices=(0,4,8,12,16),snapshot_indices=(0,8,16))
        a=run['snapshots'];import io
        b=io.BytesIO()
        np.savez_compressed(b,**a[16],**{k+'0':a[0][k] for k in ('u','omega','p')},L=2*np.pi)
        # fixed A003 L=12 check is intentional fail; synthetic test uses explicit temporary cfg.
        c=dict(cfg,L=2*np.pi)
        out=inspect_array_bytes(b.getvalue(),'cpu',c)
        self.assertEqual(out['status'],'PASS')
    def test_corrupted_pressure_is_rejected(self):
        cfg,_=load_protocol(ROOT);u0=taylor_green(16)
        run=solve_trace(np,u0,2*np.pi,.08,16,trace_indices=(16,),snapshot_indices=(0,16))
        a=run['snapshots'];bad=dict(a[16]);bad['p']=bad['p'].copy()
        x=np.arange(16)*2*np.pi/16
        bad['p']+=.01*np.sin(3*x)[:,None,None]
        import io
        b=io.BytesIO();np.savez_compressed(b,**bad,**{k+'0':a[0][k] for k in ('u','omega','p')},L=2*np.pi)
        out=inspect_array_bytes(b.getvalue(),'cpu',dict(cfg,L=2*np.pi))
        self.assertEqual(out['status'],'FAIL');self.assertFalse(out['checks']['pressure_poisson'])
    def test_fp32_rounding_must_not_be_assumed_fp64(self):
        cfg,_=load_protocol(ROOT);u0=taylor_green(16)
        run=solve_trace(np,u0,2*np.pi,.08,16,trace_indices=(16,),snapshot_indices=(0,16))
        a=run['snapshots'];import io
        b=io.BytesIO();np.savez_compressed(b,**{k:np.float32(v) for k,v in a[16].items()},
            **{k+'0':np.float32(a[0][k]) for k in ('u','omega','p')},L=2*np.pi)
        with self.assertRaises(EvidenceError):inspect_array_bytes(b.getvalue(),'cpu',dict(cfg,L=2*np.pi))
    def test_fingerprint_has_real_source_hash(self):
        fp=operators_fingerprint(ROOT)
        self.assertEqual(len(fp['operator_source_sha256']),3)
        self.assertFalse(fp['complete_driver_and_onemkl_provenance'])
if __name__=='__main__':unittest.main()
