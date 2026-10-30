import csv,json,struct,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_native_census import parse_native,component_stats

def field(name,data=b''):
    assert len(name)==4
    return name.encode()+(struct.pack('>I',len(data))+data if name[:2].isupper() else data)

def make_native():
    pts1=[(0,0,0),(1,0,0),(0,1,0)]
    pts2=[(0,0,2),(2,0,2),(0,2,2),(1,1,2)]
    head=b'KnotPlot 1.0 native fixture\x0c\n'
    payload=head+b'comp'+field('LOCF',b''.join(struct.pack('>fff',*p) for p in pts1))+b'comp'+field('LOCD',b''.join(struct.pack('>ddd',*p) for p in pts2))+b'endf'
    return payload

def test_parser():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'two_components.kpf';p.write_bytes(make_native());cc, fields=parse_native(p)
        assert len(cc)==2 and len(cc[0]['points'])==3 and len(cc[1]['points'])==4
        assert abs(component_stats(cc[0])['L_polygon_units']-(2+2**0.5))<1e-12
        assert abs(component_stats(cc[1])['L_polygon_units']-(2+(8)**0.5+2**0.5+2**0.5))<1e-12

def test_reject_quantized():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'bad.kpf';p.write_bytes(b'KnotPlot 1.0\x0c\ncomp'+field('LOCS',b'\0\0\0\0')+b'endf')
        try:parse_native(p)
        except ValueError as e:assert 'not supported' in str(e)
        else:raise AssertionError('LOCS not rejected')
if __name__=='__main__':
 test_parser();test_reject_quantized();print('PASS: 2 independent KnotPlot 1.0 parser regression fixtures')
