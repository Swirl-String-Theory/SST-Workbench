import pathlib
import sys
import unittest

TOOLSDIR = pathlib.Path(__file__).resolve().parents[1] / 'tools'
if str(TOOLSDIR) not in sys.path:
    sys.path.insert(0, str(TOOLSDIR))
from report_fonts import font_candidates, register_portable_fonts

class PortableFontTest(unittest.TestCase):
    def test_windows_without_system_fonts_uses_reportlab_package(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            info=register_portable_fonts(platform_name='Windows',windows_dir=tmp)
        self.assertEqual(info['provider'],'ReportLab Bitstream Vera')
    def test_reportlab_fallback_available_on_any_system(self):
        for name in ('Windows','Linux','Darwin'):
            normal,bold,provider=font_candidates(platform_name=name)[-1]
            self.assertEqual(provider,'ReportLab Bitstream Vera')
            self.assertTrue(normal.is_file() and bold.is_file())

if __name__=='__main__':
    unittest.main()
