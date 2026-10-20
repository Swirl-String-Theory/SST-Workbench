"""Always-on PDF report writer (stdlib fallback); never depends on LaTeX, ReportLab or fonts."""
from __future__ import annotations
import json, math, shutil, textwrap, time, os
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
    lines=[('h1','SST Triadic-Casimir / PKLSA Blind Falsifier v0.3.5'),('normal','Framework-aware, three-source-seal, geometry + regularized filament ODE numerical diagnostic'),('normal','Run label: '+label),('blank',''),
        ('h2','1. Overall epistemic verdict'),
        ('normal','Analytical toy controls and a sourced KnotPlot/PKLSA-lineage trefoil geometry were evaluated. The RK4 filament trajectory is numerical simulation only. Physical Euler closure, atom-link coupling, vacuum normalization, metal boundary forces, and gravity are NOT certified.'),
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
      ('normal','Sourced 3_1 trefoil: KnotPlot relaxed N=300; Fremlin second family registered via E010 but a single run-level raw source manifest distinguishes local provider availability from packaged evidence.'),
      ('small','Source Drive id: '+src['upstream_drive_file_id']),
      ('small','Raw geometry SHA-256: '+src['raw_sha256']),
      ('small',f"Points={stats['points']}; length={stats['perimeter']:.9f}; segment relative spread={stats['relative_segment_spread']:.5g}"),
      ('small',f"Regularized midpoint Biot-Savart: Gamma=1, eps={pklsa['regularization_epsilon_dimensionless']}, max 150 vs 300 refinement error={pklsa['max_refinement_error']:.7g}"),
      ('small',f"New fixed-parameter spatial ladder: 75->150={readjson(root/'outputs'/'BLIND'/'D01_EULER.json')['filament_dynamics']['spatial_75_150_relative_displacement']:.5%}; 150->300={readjson(root/'outputs'/'BLIND'/'D01_EULER.json')['filament_dynamics']['spatial_150_300_relative_displacement']:.5%}."),
      ('normal','The pressure-Poisson source at sample points is computed from numerical strain and curl of the regularized geometric velocity field, with no wall/stress certification.'),
      ('h2','4b. RK4 finite-core filament simulation'),
      ('small','RK4 75 points, fixed T=0.04 and predeclared dt halving, not full Euler and no material boundaries.'),
      ('h2','5. Model equations'),
      ('normal','Euler: div(u)=0; omega=curl(u); Laplace(p)=rho*(|omega|^2/2 - ||S||^2).'),
      ('normal','Conditional clock: N^2=1-|u_eff|^2/c_star^2. PKLSA geometry does not independently determine u_eff for a clock.'),
      ('normal','Link clock phase: Theta_AB=theta_B-theta_A-sum(path theta_e), conditional on gauge-covariant atom coupling.'),
      ('normal','One-body response: chi(i xi)=bT (K+xi^2 M)^(-1)b, presently a toy oscillator, not measured metal.'),
      ('normal','Two-body finite-T toy: F/A=(T/4pi) integral k log(1-r1*r2*exp(-2*k*a)) dk.'),
      ('small',f"RK4 RMS shift={readjson(root/'outputs'/'BLIND'/'D01_EULER.json')['filament_dynamics']['rms_displacement']:.8g}; relative dt mismatch={readjson(root/'outputs'/'BLIND'/'D01_EULER.json')['filament_dynamics']['relative_discretization_error']:.3g}"),
      ('small','Fremlin 3_1 raw upstream status: '+str(readjson(root/'outputs'/'BLIND'/'D01_EULER.json')['second_provider_readiness']['status'])),
      ('h2','6. Physical qualification blockers'),
      ('normal','Missing: second authenticated PKLSA bytes, full time-dependent Euler PDE qualification, Kelvin/Floquet modes, finite-core constitutive law, laboratory wall boundary conditions, atom-link coupling, independent reflection operator, fluctuation normalization and independent physical stress.'),
      ('normal','Never interpret fitted distance exponent or numeric toy attraction as a predicted electromagnetic Casimir force.'),
      ('h2','7. Reproduction and PDF availability'),
      ('normal','On Windows: run_all.cmd ALL; run_all.cmd FRAMEWORK; run_all.cmd PKLSA; run_all.cmd VERIFY. A current dynamic PDF is created even if LaTeX/ReportLab are absent.'),
      ('normal','A CPU framework profile is requested but native physical certification is still blocked by G3. The official canonical SST framework v1.0.7 must exist at the Workbench template location, or SST_FALSIFIER_FRAMEWORK_ROOT must point to it. Its source remains unmodified.'),
      ('normal','All three v0.3.0 dataset seals are new commitments; the comparator is stored separately for true external-blind review. The earlier v0.1.0 seal is NOT reused as if it still covered the same data.'),
      ('h2','8. Provenance'),
      ('small','Canon v0.8.36: sections 3.5, 3.10, 7.1, 11.16-11.17, S.2, S.52.'),
      ('small','A046 v0.3.0 and v0.3.0: Euler / Poisson controls; geometry is not gravity.'),
      ('small','Original KnotPlot Drive id and full source sha256 are included in D01. All fields are dimensionless; no prescribed SST rho_f or Casimir amplitude.')])
    historical=root/'outputs/HISTORICAL_V034_RESULT.json'
    if historical.is_file():
        hh=readjson(historical)
        lines.extend([('h2','v0.3.5: historical Fourier and torus geometry diagnostics'),('normal','Geometry-only seeds; no physical Euler, Casimir, or gravity validation.'),('small','C++ qualification: '+hh['native_qualification']['status'])])
        if hh['native_qualification']['status']=='EXECUTED':
            for name,record in hh['native_qualification']['seeds'].items():
                lines.append(('small',name+': '+str({k:round(v['relative_to_coarse_displacement'],6) for k,v in record['spatial'].items()})))
    hipath=root/'outputs/HIGHRES_V035_RESULT.json'
    if hipath.is_file():
        hi=readjson(hipath);native=hi['native']
        lines.extend([('h2','v0.3.5 High-resolution direct-analytic trefoils (up to N4800)'),
            ('small','Preregistration SHA-256: '+hi['prereg_sha256']),
            ('normal','N=600, 1200, 2400, 4800; gamma=1, T=0.04; eps=0.06, 0.12, 0.24; all geometry dimensionless.'),
            ('normal','All original coarse failures retained. Reduced filament ODE only, NOT Euler PDE, calibrated SST, Casimir or gravity.'),
            ('small','Native backend status: '+native['status'])])
        if native['status']=='EXECUTED':
            for seed,z in native['seeds'].items():
                lines.append(('h2',seed))
                lines.append(('small','Baseline 1 percent spatial status: '+z['baseline_spatial_1pct']+'; temporal='+z['temporal_status']+'; Python/C++ spot parity='+z['parity_status']))
                for eps,series in z['epsilon_ladders'].items():
                    for pair,v in series['pairs'].items():
                        frac=v['relative_error']; frac_txt='UNDEFINED' if frac is None else f'{100*frac:.6f}%'
                        lines.append(('small',f'epsilon={eps}; N={pair}; relative error={frac_txt}; 1pct={v["status_1pct"]}; 0.1pct target={v["status_0p1pct"]}'))
                for n,obs in z['temporal_controls'].items():
                    lines.append(('small',f'N={n}: dt(4 vs 8)={obs["4_vs_8"]["relative_error"]}; dt(8 vs 16)={obs["8_vs_16"]["relative_error"]}; status={obs["status"]}'))
    if revealed.exists():
        lines.extend([('h2','9. Post-seal comparator'),('normal','Revealed toy comparator available. Comparison does not use measured Casimir datasets or demonstrate an absolute physical force.')])
    # A fresh immutable workspace is created by triadic.launch for every run.
    # Publication is create-only: a colliding name is an error, not an overwrite.
    run_id=os.environ.get('SST_A065_RUN_ID')
    if not run_id:
        raise RuntimeError('Unique-run environment missing. Use run_all.cmd / run_all.sh; direct entrypoint is not an export path.')
    from .report_tex import write_tex,compile_tex
    dest=Path(destination) if destination else root/'reports'/f'{run_id}_FALSIFIER_REPORT.pdf'
    tex=root/'reports'/f'{run_id}_FALSIFIER_REPORT.tex'
    write_tex(root,tex,run_id=run_id,label=label,frame_state=fs.get('state','NOT_RUN'))
    compiled=compile_tex(tex,dest)
    if compiled.get('success'):
        pages=0  # determined by the PDF renderer; no misleading fixed page count
        generator='SELF_CONTAINED_PDFLATEX'
    else:
        if dest.exists():
            raise FileExistsError('Refusing to replace pre-existing report: '+str(dest))
        pages=_pdf_text(dest,lines)
        generator='STANDARD_LIBRARY_PDF_FALLBACK'
    export_dir=Path(os.environ['SST_A065_EXPORT_DIR'])
    # The launcher publishes both the PDF and its corresponding TeX file to
    # the unique export directory using exclusive 'xb' file creation.
    audit={'schema':'TC-REPORT-3','generator':generator,'success':True,
           'path':str(dest),'published_to':str(export_dir/dest.name),'tex':str(tex),
           'pages_reported_by_fallback':pages,'sha256':sha(dest.read_bytes()),
           'latex_status':compiled,'frame_state':fs.get('state')}
    (root/'reports'/'REPORT_RENDER.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    return audit
