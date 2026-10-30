"""Static source-admission contract must not mistake modified bytes for science."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from e011_audit import audit, sha256


class StaticAdmissionRejectsBadInputs(unittest.TestCase):
    def test_sha256_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            z=Path(tmp)/'source.zip'
            with zipfile.ZipFile(z,'w') as archive:
                archive.writestr('E011/a.txt','source')
            side=Path(tmp)/'source.zip.sha256'
            side.write_text('0'*64+'  source.zip\n',encoding='utf-8')
            result=audit(z,side)
            self.assertEqual(result['status'],'BLOCKED_SOURCE')
            self.assertEqual(result['reason'],'SHA256_MISMATCH')

    def test_research_only_contract_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            z=Path(tmp)/'source.zip'
            root='E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs/'
            fixtures={
                'RUN_SUMMARY.json':{'schema':'E011-SKLSA-STATIC-READY-ATLAS-1','execution_gate':'PASS','operational_error_count':0,'e010_release_version':'0.3.1','provider_anchor_count':0,'primary_static_seed_count':0},
                # Deliberate false flag; never accept as STATIC_READY.
                'SEED_CONTRACT_SCHEMA.json':{'schema':'E011-STATIC-SEED-CONTRACT-1','dynamics_ready':True},
                'PARENT_RELEASE.json':{'e010_version':'0.3.1'},
                'STATIC_READY_PROVIDER_ANCHORS.jsonl':'',
                'STATIC_READY_PRIMARY_SEEDS.jsonl':'',
            }
            with zipfile.ZipFile(z,'w') as archive:
                for name,value in fixtures.items():
                    archive.writestr(root+name,json.dumps(value) if isinstance(value,dict) else value)
            side=Path(tmp)/'source.zip.sha256'
            side.write_text(sha256(z)+'  source.zip\n',encoding='utf-8')
            result=audit(z,side)
            self.assertEqual(result['status'],'BLOCKED_SOURCE')
            self.assertEqual(result['reason'],'INVALID_E011_STATIC_ADMISSION_CONTRACT')

if __name__ == '__main__':
    unittest.main()
