"""Always-on PDF report writer (stdlib fallback); never depends on LaTeX, ReportLab or fonts."""
from __future__ import annotations
import json, math, shutil, textwrap, time
from pathlib import Path
from .security import readjson,sha


def _pdf_text(path, lines):
    # PDF 1.4, Type1 Helvetica, WinAnsiEncoding, no optional dependencies.
    # Preserve only Windows-1252 glyphs, replacing unsupported characters.
    WIDTH,HEIGHT=595,842
    chunks=[];page=[];y=790
    def flush():
        nonlocal page,y
        if page:chunks.append('\n'.join(page));page=[];y=790
    for kind,content in lines:
        if kind=='blank':y-=14;continue
        size={'h1':16,'h2':12,'normal':9,'small':8}.get(kind,9)
        if kind=='h2': y-=6
        indent=36 if kind.startswith('h') else 42
        wrap=66 if kind=='h1' else 99 if kind=='small' else 89
        for item in textwrap.wrap(content.replace('\t','    '),width=wrap,break_long_words=False,break_on_hyphens=False) or ['']:
            if y<65:flush()
            s=item.encode('cp1252','replace').decode('cp1252')
            safe=s.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
            page.append(f'BT /F1 {size} Tf 1 0 0 1 {indent} {y:.1f} Tm ({safe}) Tj ET')
            y-=size+6
    flush()
    objects=[b'']
    def add(o):objects.append(o if isinstance(o,bytes) else o.encode('latin1'));return len(objects)-1
    pages_id=add(b'')
    font_id=add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
    page_ids=[]
    for content in chunks:
        raw=content.encode('cp1252','replace')
        stream_id=add(f'<< /Length {len(raw)} >>\nstream\n'.encode('ascii')+raw+b'\nendstream')
        page_ids.append(add(f'<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {WIDTH} {HEIGHT}] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {stream_id} 0 R >>'))
    objects[pages_id]=f'<< /Type /Pages /Count {len(page_ids)} /Kids [ '+ ' '.join(f'{k} 0 R' for k in page_ids)+' ] >>'
    if isinstance(objects[pages_id],str):objects[pages_id]=objects[pages_id].encode('ascii')
    catalog_id=add(f'<< /Type /Catalog /Pages {pages_id} 0 R >>')
    b=bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'); offsets=[0]
    for i,o in enumerate(objects[1:],1):
        offsets.append(len(b));b.extend(f'{i} 0 obj\n'.encode());b.extend(o);b.extend(b'\nendobj\n')
    xref=len(b);b.extend(f'xref\n0 {len(objects)}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:b.extend(f'{offset:010d} 00000 n \n'.encode())
    b.extend(f'trailer\n<< /Size {len(objects)} /Root {catalog_id} 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
    if not (path.stat().st_size>200 and b'/Type /Page' in b):raise RuntimeError('PDF validation failure')
    return len(page_ids)


def create_report(root, *, label='PILOT', framework_status=None, destination=None):
    root=Path(root).resolve()
    blindp=root/'outputs'/'BLIND'/'RUN_SUMMARY.json'
    if not blindp.exists():raise FileNotFoundError('BLIND required before dynamic PDF report')
    summary=readjson(blindp)
    pklsa=readjson(root/'outputs'/'BLIND'/'D01_EULER.json')['pklsa']
    revealed=root/'outputs'/'REVEALED'/'COMPARISON.json'
    seals=readjson(root/'seals'/'GLOBAL_COMMITMENT.json')
    fs=framework_status or (readjson(root/'FRAMEWORK_STATUS.json') if (root/'FRAMEWORK_STATUS.json').exists() else {'state':'NOT_RUN'})
    lines=[('h1','SST Triadic-Casimir / PKLSA Blind Falsifier v0.2.0'),('normal','Framework-aware, three-source-seal, geometry-only scientific diagnostic'),('normal','Run label: '+label),('blank',''),
        ('h2','1. Overall epistemic verdict'),
        ('normal','Analytical toy controls and a sourced KnotPlot/PKLSA-lineage trefoil geometry were evaluated. A physical Casimir force, atom-link coupling, quantum vacuum amplitude, and gravity are NOT certified.'),
        ('normal','Official frozen-framework invocation: '+str(fs.get('state','NOT_RUN'))),
        ('normal','Framework detail: '+str(fs.get('detail','No native framework validation claim.'))[:190]),
        ('h2','2. Three independently sealed datasets')]
    for key,digest in seals['seals'].items():lines.append(('small',key+' SHA-256 seal: '+digest))
    lines += [('h2','3. Numeric control gates')]
    gates=summary.get('gates',[])
    for g in gates:lines.append(('small',f"{g['gate']}: {g['status']} | observed={str(g['metric'])[:55]} | criterion={g['limit']}"))
    lines += [('normal',f"Pilot synthetic/numerical checks: {sum(g['status']=='PASS' for g in gates)}/{len(gates)} PASS"),
              ('h2','4. PKLSA geometry and numerical bridge')]
    src=pklsa['source'];stats=pklsa['stats'];lines.extend([
      ('normal','Sourced 3_1 trefoil: KnotPlot relaxation sequence, N=300, one upstream family (NOT two independent providers).'),
      ('small','Source Drive id: '+src['upstream_drive_file_id']),
      ('small','Raw geometry SHA-256: '+src['raw_sha256']),
      ('small',f"Points={stats['points']}; length={stats['perimeter']:.9f}; segment relative spread={stats['relative_segment_spread']:.5g}"),
      ('small',f"Regularized midpoint Biot-Savart: Gamma=1, eps={pklsa['regularization_epsilon_dimensionless']}, max 150 vs 300 refinement error={pklsa['max_refinement_error']:.7g}"),
      ('normal','The pressure-Poisson source at sample points is computed from numerical strain and curl of the regularized geometric velocity field, with no wall/stress certification.'),
      ('h2','5. Model equations'),
      ('normal','Euler: div(u)=0; omega=curl(u); Laplace(p)=rho*(|omega|^2/2 - ||S||^2).'),
      ('normal','Conditional clock: N^2=1-|u_eff|^2/c_star^2. PKLSA geometry does not independently determine u_eff for a clock.'),
      ('normal','Link clock phase: Theta_AB=theta_B-theta_A-sum(path theta_e), conditional on gauge-covariant atom coupling.'),
      ('normal','One-body response: chi(i xi)=bT (K+xi^2 M)^(-1)b, presently a toy oscillator, not measured metal.'),
      ('normal','Two-body finite-T toy: F/A=(T/4pi) integral k log(1-r1*r2*exp(-2*k*a)) dk.'),
      ('h2','6. Physical qualification blockers'),
      ('normal','Missing: independent second PKLSA provider, time-dependent Euler evolution, finite-core constitutive law, laboratory wall boundary conditions, atom-link coupling, independent reflection operator, fluctuation normalization and independent physical stress.'),
      ('normal','Never interpret fitted distance exponent or numeric toy attraction as a predicted electromagnetic Casimir force.'),
      ('h2','7. Reproduction and PDF availability'),
      ('normal','On Windows: run_all.cmd ALL; run_all.cmd FRAMEWORK; run_all.cmd PKLSA; run_all.cmd VERIFY. A current dynamic PDF is created even if LaTeX/ReportLab are absent.'),
      ('normal','The official canonical SST framework v1.0.7 must exist at the Workbench template location, or SST_FALSIFIER_FRAMEWORK_ROOT must point to it. Its source remains unmodified.'),
      ('normal','All three v0.2.0 dataset seals were reissued after adding PKLSA bytes to D01. The earlier v0.1.0 seal is NOT reused as if it still covered the same data.'),
      ('h2','8. Provenance'),
      ('small','Canon v0.8.36: sections 3.5, 3.10, 7.1, 11.16-11.17, S.2, S.52.'),
      ('small','A046 v0.2.0 and v0.3.0: Euler / Poisson controls; geometry is not gravity.'),
      ('small','Original KnotPlot Drive id and full source sha256 are included in D01. All fields are dimensionless; no prescribed SST rho_f or Casimir amplitude.')])
    if revealed.exists():
        lines.extend([('h2','9. Post-seal comparator'),('normal','Revealed toy comparator available. Comparison does not use measured Casimir datasets or demonstrate an absolute physical force.')])
    dest=Path(destination) if destination else root/'reports'/'TRIADIC_CASIMIR_v0.2.0_FALSIFIER_REPORT.pdf'
    pages=_pdf_text(dest,lines)
    # Exact parent naming contract used by SST Workbench versions.
    public=root.parent/(root.name+'_FALSIFIER_REPORT.pdf')
    shutil.copy2(dest,public)
    audit={'schema':'TC-REPORT-2','generator':'STANDARD_LIBRARY_PDF_NO_LATEX_REQUIRED','success':True,'path':str(dest),'published_to':str(public),'pages':pages,'sha256':sha(dest.read_bytes()),'frame_state':fs.get('state')}
    (root/'reports'/'REPORT_RENDER.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    return audit
