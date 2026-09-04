from pathlib import Path
import tempfile
from katlas_source.rdf_parser import parse_dataset, extract_presentations

SAMPLE = r'''<knot:3_1> <invariant:PD_Presentation> "<math>PD[X[1,4,2,5]]</math>" .
<knot:3_1> <invariant:Gauss_Code> "-1, 3, -2, 1, -3, 2" .
<knot:3_1> <invariant:DT_Code> "4 6 2" .
<knot:3_1> <invariant:Conway_Notation> "[3]" .
<link:L6a4> <invariant:PD_Presentation> "PD[X[...]]" .
'''

def main():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"sample.rdf"; p.write_text(SAMPLE,encoding="utf-8")
        objects,rejected=parse_dataset(p); assert not rejected
        inv=objects[("knot","3_1")].invariants
        pres=extract_presentations(inv)
        assert pres["dt"] == ["4 6 2"]
        assert pres["conway"] == ["[3]"]
    print("PASS parser tests")

if __name__ == "__main__": main()
