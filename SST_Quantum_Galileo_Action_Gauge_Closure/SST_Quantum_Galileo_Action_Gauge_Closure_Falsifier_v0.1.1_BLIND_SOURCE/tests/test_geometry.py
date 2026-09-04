import unittest, numpy as np
from sst_qgi.geometry import track_trefoil, resample_closed, segment_cv, geometry_sha256, descriptors

class GeometryTests(unittest.TestCase):
    def test_shader_family_geometry(self):
        p=track_trefoil(512,4.08248290463863,2.2,3.0)
        q=resample_closed(p,512)
        self.assertEqual(q.shape,(512,3))
        self.assertLess(segment_cv(q),5e-3)
        self.assertEqual(len(geometry_sha256(q)),64)
        d=descriptors(q)
        self.assertGreater(d["length"],0)
        self.assertGreater(d["min_nonlocal_distance_proxy"],0)

if __name__=="__main__":
    unittest.main()
