from __future__ import annotations
from pathlib import Path
import re, numpy as np

_HEADER=re.compile(r'^\s*%|^\s*#')


def parse_fremlin_fseries(path):
    """Decode Fremlin Fourier coefficient records.

    Two source-native layouts are admitted:

    1. Six-column harmonic rows only::

         a_x(j) b_x(j) a_y(j) b_y(j) a_z(j) b_z(j)

       with j = 1..M.

    2. An optional *first* three-column constant term followed by the same
       six-column harmonic rows::

         a_x(0) a_y(0) a_z(0)
         a_x(1) b_x(1) a_y(1) b_y(1) a_z(1) b_z(1)
         ...

       This layout is present in archived Fremlin SST mirrors such as the
       ``knot.*d.fseries`` family.  For j=0 the sine coefficient vanishes, so
       only the three cosine/constant coefficients are stored.

    A three-column row anywhere other than the first numeric row remains an
    error.  This keeps the parser fail-closed for malformed files.
    """
    rows=[]
    header=[]
    offset=None
    numeric_row_index=0
    for raw in Path(path).read_text(encoding='utf-8',errors='replace').splitlines():
        s=raw.strip()
        if not s:
            continue
        if _HEADER.match(s):
            header.append(s)
            continue
        parts=s.replace(',',' ').split()
        try:
            vals=[float(x) for x in parts]
        except ValueError as e:
            raise ValueError(f"non-numeric fseries row: {s[:100]}") from e

        if len(vals)==3 and numeric_row_index==0 and offset is None:
            offset=np.asarray(vals,float)
        elif len(vals)==6:
            rows.append(vals)
        else:
            raise ValueError(
                "Fremlin fseries rows must be either one initial three-coefficient "
                f"constant term or six harmonic coefficients: {s[:100]}"
            )
        numeric_row_index += 1

    if not rows:
        raise ValueError('no Fourier harmonic coefficient rows')
    c=np.asarray(rows,float)
    if not np.isfinite(c).all():
        raise ValueError('non-finite Fourier coefficients')
    if offset is None:
        offset=np.zeros(3,float)
    if not np.isfinite(offset).all():
        raise ValueError('non-finite Fourier constant term')
    return {
        'coefficients': c,
        'offset': np.asarray(offset,float),
        'header': header,
        'format': 'fremlin_six_column_optional_a0',
    }


def sample_fremlin_fseries(path_or_coeffs, n=1024, phase=0.0):
    if isinstance(path_or_coeffs,(str,Path)):
        parsed=parse_fremlin_fseries(path_or_coeffs)
        coeff=np.asarray(parsed['coefficients'],float)
        offset=np.asarray(parsed.get('offset',(0.0,0.0,0.0)),float)
    elif isinstance(path_or_coeffs,dict):
        coeff=np.asarray(path_or_coeffs['coefficients'],float)
        offset=np.asarray(path_or_coeffs.get('offset',(0.0,0.0,0.0)),float)
    else:
        coeff=np.asarray(path_or_coeffs,float)
        offset=np.zeros(3,float)

    if offset.shape != (3,):
        raise ValueError('Fourier constant term must contain exactly three coefficients')
    t=np.linspace(0,2*np.pi,int(n),endpoint=False)+float(phase)
    k=np.arange(1,len(coeff)+1,dtype=float)[:,None]
    ct=np.cos(k*t[None,:]); st=np.sin(k*t[None,:])
    out=np.empty((int(n),3),float)
    out[:,0]=offset[0] + (coeff[:,0,None]*ct + coeff[:,1,None]*st).sum(axis=0)
    out[:,1]=offset[1] + (coeff[:,2,None]*ct + coeff[:,3,None]*st).sum(axis=0)
    out[:,2]=offset[2] + (coeff[:,4,None]*ct + coeff[:,5,None]*st).sum(axis=0)
    return out
