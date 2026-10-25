"""Create-only installer regression: v0.2 wrapper must point to v0.2."""
import tempfile,unittest
from pathlib import Path
from install_sidecar import install,WRAPPER

class InstallSidecarTests(unittest.TestCase):
    def test_create_only_uses_v020_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);(base/'run_all.cmd').write_text('REM original');(base/'knotplotrc.kps').write_text('# original')
            install(base,False)
            self.assertFalse((base/'run_vccr_v020.cmd').exists())
            install(base,True)
            launcher=(base/'run_vccr_v020.cmd').read_text()
            self.assertIn('tools\\VCCR_v0.2.0',launcher)
            self.assertNotIn('VCCR_v0.1.0',launcher)
            self.assertTrue((base/'tools/VCCR_v0.2.0/vccr/dispatch.py').exists())
            self.assertTrue((base/'tools/VCCR_v0.2.0/FORMULAE_EULER.md').exists())
            self.assertEqual((base/'run_all.cmd').read_text(),'REM original')
            install(base,True)
            self.assertEqual((base/'run_vccr_v020.cmd').read_text(),launcher)

    def test_refuses_conflicting_wrapper(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);(base/'run_all.cmd').write_text('REM original');(base/'knotplotrc.kps').write_text('# original')
            (base/'run_vccr_v020.cmd').write_text('WRONG')
            with self.assertRaises(RuntimeError):install(base,True)
