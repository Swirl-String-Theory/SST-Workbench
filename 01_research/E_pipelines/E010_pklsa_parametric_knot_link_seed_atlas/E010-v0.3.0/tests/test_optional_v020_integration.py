from __future__ import annotations
import os, unittest
from pathlib import Path
from pklsa_builder.source_discovery import discover_from_v020
from pklsa_builder.base_adapter import load_v020_carrier

class OptionalV020Integration(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('PKLSA_V020_ROOT'),'Set PKLSA_V020_ROOT to run integration test')
    def test_trefoil_reference_and_generated(self):
        root=Path(os.environ['PKLSA_V020_ROOT'])
        cs=discover_from_v020(root,'3_1')
        self.assertTrue(any(c.source_family=='knotinfo_3d' for c in cs))
        self.assertTrue(any(c.source_family=='ptsa' for c in cs))
        for c in cs[:3]:
            x=load_v020_carrier(root,c)
            self.assertGreater(len(x[0]),3)

if __name__=='__main__': unittest.main()
