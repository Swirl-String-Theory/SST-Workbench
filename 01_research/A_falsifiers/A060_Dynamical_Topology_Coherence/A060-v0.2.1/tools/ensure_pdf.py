"""Safe plain-PDF fallback for missing TeX; never mark framework render successful."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'CrossPaper_VortexMechanics_v0.2.1-outputs'
DEST=ROOT.parent/'A060-v0.2.1_FALSIFIER_REPORT.pdf'
def makepdf(lines):
    # ASCII Helvetica single-page PDF using only Python stdlib
    import textwrap
    rows=[]
    for line in lines:
        rows += textwrap.wrap(line,93) or ['']
    parts=[]
    for page_i in range(0,len(rows),56):
        page=rows[page_i:page_i+56]
        txt=['BT','/F1 9 Tf','42 790 Td','12 TL']
        for row in page:
            esc=row.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
            txt.append('('+esc+') Tj T*')
        txt.append('ET')
        parts.append('\n'.join(txt).encode('latin1','replace'))
    objs=[b'<< /Type /Catalog /Pages 2 0 R >>',None,b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    for chunk in parts:
        contents=len(objs)+2
        objs.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {contents} 0 R >>'.encode())
        objs.append(b'<< /Length '+str(len(chunk)).encode()+b' >>\nstream\n'+chunk+b'\nendstream')
    kids=' '.join(f'{i} 0 R' for i in range(4,len(objs)+1,2))
    objs[1]=f'<< /Type /Pages /Kids [{kids}] /Count {len(parts)} >>'.encode()
    result=b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n';offset=[0]
    for i,obj in enumerate(objs,1):
        offset.append(len(result));result+=f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n'
    pos=len(result);result+=f'xref\n0 {len(objs)+1}\n0000000000 65535 f \n'.encode()
    result+=b''.join(f'{x:010d} 00000 n \n'.encode() for x in offset[1:])
    result+=f'trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{pos}\n%%EOF'.encode()
    return result
if __name__=='__main__':
    if DEST.is_file() and DEST.stat().st_size>1000:
        print('Scientific LaTeX PDF already exists:',DEST);raise SystemExit(0)
    if not (OUT/'GATE_LEDGER.json').is_file():
        print('No blind ledger, no fallback PDF produced.');raise SystemExit(0)
    l=json.loads((OUT/'GATE_LEDGER.json').read_text())
    lines=['A060 v0.2.1 - Blind analytic reference results','PDF FALLBACK: NOT THE CANONICAL LATEX RENDER','Framework SST 1.0.7 protocol and TeX are packaged separately.','No physics of SST particles/gravity is certified.','',]
    lines += ['GATE '+r['gate_id']+' : '+r['status']+' :: '+r['reason'] for r in l['records']]
    lines += ['','Full numeric detail: M00_M04_REFERENCE.json and GATE_LEDGER.json','Native C++ and PDF render provenance in BACKEND_MANIFEST.json, REPORT_RENDER.json']
    DEST.write_bytes(makepdf(lines));print('Noncanonical summary PDF:',DEST)
