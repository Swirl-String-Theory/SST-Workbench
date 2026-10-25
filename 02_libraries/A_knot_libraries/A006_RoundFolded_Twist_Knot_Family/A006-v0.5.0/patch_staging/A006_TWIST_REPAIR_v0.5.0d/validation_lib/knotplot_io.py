"""KPT 1.0 LOCD writer plus strict byte-for-byte roundtrip decoder.
Based on the validated internal data layout used by the previous v0.1.x seeds.
"""
from pathlib import Path
import numpy as np
import struct
HEADER=b'KnotPlot 1.0\n\x0c\n'
def encode(components):
    parts=[HEADER]
    for p in components:
        q=np.asarray(p,dtype='>f8')
        b=q.tobytes()
        parts += [b'comp',b'Attr',struct.pack('>I',1),b'LOCD',struct.pack('>I',len(b)),b]
    parts += [b'endf']
    return b''.join(parts)
def decode(b):
    assert b.startswith(HEADER)
    pos=len(HEADER);items=[]
    while b[pos:pos+4]!=b'endf':
        assert b[pos:pos+4]==b'comp';pos+=4
        assert b[pos:pos+4]==b'Attr';pos+=4
        assert struct.unpack('>I',b[pos:pos+4])[0]==1;pos+=4
        assert b[pos:pos+4]==b'LOCD';pos+=4
        n=struct.unpack('>I',b[pos:pos+4])[0];pos+=4
        assert n%24==0
        items.append(np.frombuffer(b[pos:pos+n],dtype='>f8').reshape(-1,3).astype(np.float64));pos+=n
    assert pos+4==len(b)
    return items
