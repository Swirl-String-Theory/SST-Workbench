"""Fail-closed, read-only KnotPlot 1.0 single closed-component geometry decoder.

Reverse implementation based on the user's original 2025 distribution
resource/src/simple-reader-writer/kpf_io.cpp, NOT a copy of KnotPlot code.
The original minimal reader expressly does not support multi-component links.
No writes or geometry transformations occur in this module.
"""
from __future__ import annotations
from dataclasses import dataclass
import io
import math
import struct
from typing import BinaryIO

MAX_VERTICES = 200_000
MAX_FILE_BYTES = 80 * 1024 * 1024

class KPFUnsupported(ValueError):
    pass
class KPFMalformed(ValueError):
    pass

@dataclass(frozen=True)
class KPFGeometry:
    points: tuple[tuple[float, float, float], ...]
    encoding: str
    component_count: int
    chunks: tuple[str,...]


def _take(f: BinaryIO, n: int) -> bytes:
    if n < 0 or n > MAX_FILE_BYTES:
        raise KPFMalformed('Invalid section length')
    b = f.read(n)
    if len(b) != n:
        raise KPFMalformed('Truncated KnotPlot section')
    return b

def _be_u32(f: BinaryIO) -> int:
    return struct.unpack('>I', _take(f, 4))[0]

def _xyz_from_payload(code: str, payload: bytes) -> tuple[tuple[float,float,float],...]:
    n = len(payload)
    if code == 'LOCS':
        if n < 16 or (n - 16) % 6:
            raise KPFMalformed('LOCS payload length != 16+6*N')
        count = (n - 16)//6
        scale, ox, oy, oz = struct.unpack_from('>ffff', payload, 0)
        raw = struct.iter_unpack('>HHH', payload[16:])
        points = tuple((float(scale*x+ox),float(scale*y+oy),float(scale*z+oz)) for x,y,z in raw)
    elif code == 'LOCF':
        if n % 12:
            raise KPFMalformed('LOCF payload length != 12*N')
        count = n//12
        points = tuple(tuple(map(float,xyz)) for xyz in struct.iter_unpack('>fff',payload))
    elif code == 'LOCD':
        if n % 24:
            raise KPFMalformed('LOCD payload length != 24*N')
        count = n//24
        points = tuple(tuple(map(float,xyz)) for xyz in struct.iter_unpack('>ddd',payload))
    elif code == 'LOCC':
        # 12 bytes epsilon + 12 bytes initial point + 3 bytes per subsequent bead.
        # (S-21)/3 gives bead count; original C++ helper omits assignment vertex[0].
        if n < 24 or (n - 21) % 3:
            raise KPFMalformed('LOCC payload length != 21+3*N')
        count = (n - 21)//3
        eps = struct.unpack_from('>fff',payload,0)
        first = tuple(map(float,struct.unpack_from('>fff',payload,12)))
        pt = list(first); pts=[first]
        for diff in struct.iter_unpack('>bbb',payload[24:]):
            pt = [float(pt[i]+diff[i]*eps[i]) for i in range(3)]
            pts.append(tuple(pt))
        points=tuple(pts)
    else:
        raise KPFUnsupported('Unsupported geometry encoding '+code)
    if not 3 <= count <= MAX_VERTICES or len(points) != count:
        raise KPFMalformed('Unacceptable or inconsistent vertex count')
    if not all(math.isfinite(v) for pt in points for v in pt):
        raise KPFMalformed('Nonfinite geometry coordinate')
    return points


def decode_kpf(data: bytes) -> KPFGeometry:
    if len(data) > MAX_FILE_BYTES:
        raise KPFMalformed('KnotPlot file exceeds protective size cap')
    if not data.startswith(b'KnotPlot 1.0'):
        raise KPFUnsupported('Not a KnotPlot 1.0 binary file')
    boundary=data.find(b'\x0c',0,256)
    if boundary < 0 or boundary+1 >= len(data):
        raise KPFMalformed('Missing form-feed header separator')
    # A single byte after form feed is skipped, as in original read_KnotPlot.
    f=io.BytesIO(data[boundary+2:]); components=0; vertices=None; encoding=None; chunks=[]
    while True:
        code=_take(f,4).decode('ascii',errors='replace')
        chunks.append(code)
        if len(chunks)>10000:
            raise KPFMalformed('Excessive section count')
        if code=='endf':
            break
        if code=='comp':
            components+=1
            continue
        if code in ('LOCS','LOCF','LOCD','LOCC'):
            if components != 1 or vertices is not None:
                raise KPFUnsupported('Multiple components or vertex chunks; use a link-aware importer')
            size=_be_u32(f)
            vertices=_xyz_from_payload(code,_take(f,size))
            encoding=code
            continue
        if len(code)!=4 or not code.isascii():
            raise KPFMalformed('Invalid chunk identifier')
        if code[0].isupper() and code[1].isupper():
            # Chunk framing is documented; unknown payloads skipped with strict size cap.
            size=_be_u32(f)
            _take(f,size)
        elif code[0].isupper() and code[1].islower():
            _take(f,4)  # Attribute scalar record (e.g. Attr).
        else:
            raise KPFUnsupported('Unknown chunk framing: '+code)
    if components != 1 or vertices is None:
        raise KPFUnsupported(f'Only one closed component supported, got {components}')
    # Catalog files commonly end with 4 newlines. Reject non-whitespace trailing data.
    if f.read().strip(b'\x00\r\n\t '):
        raise KPFMalformed('Unexpected trailing bytes')
    return KPFGeometry(vertices,encoding,components,tuple(chunks))


def metrics(points) -> dict:
    pts=tuple(points); n=len(pts)
    mx=[sum(p[d] for p in pts)/n for d in range(3)]
    edges=[math.dist(pts[i],pts[(i+1)%n]) for i in range(n)]
    length=sum(edges)
    mean=length/n
    rg=math.sqrt(sum(sum((p[d]-mx[d])**2 for d in range(3)) for p in pts)/n)
    ecv=math.sqrt(sum((e-mean)**2 for e in edges)/n)/mean if mean else None
    return {'nbeads':n,'length_native_units':length,'radius_gyration_native_units':rg,
            'edge_cv':ecv,'min_edge_native_units':min(edges),'max_edge_native_units':max(edges),
            'scale_is_physical_SI':False}
