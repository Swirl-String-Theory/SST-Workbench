from pathlib import Path
import unittest

class NoPlanckTargetLeakTests(unittest.TestCase):
    def test_blind_runtime_has_no_si_target_symbols(self):
        root=Path(__file__).resolve().parents[1]
        forbidden=("H"+"_"+"SI","H"+"BAR"+"_"+"SI","scipy.constants."+"h","physical_"+"constants")
        hits=[]
        for p in (root/"sst_qgi").rglob("*.py"):
            if p.name=="reveal.py":
                continue
            text=p.read_text(encoding="utf-8",errors="ignore")
            for tok in forbidden:
                if tok in text:
                    hits.append((str(p.relative_to(root)),tok))
        self.assertEqual(hits,[])

if __name__=="__main__":
    unittest.main()
