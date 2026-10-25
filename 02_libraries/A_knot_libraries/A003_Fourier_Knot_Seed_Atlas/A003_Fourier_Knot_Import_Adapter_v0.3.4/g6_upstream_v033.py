#!/usr/bin/env python3
"""A003 v0.3.3: provenance-separated G6P16, versioned E010 G6P8 staging,
read-only E010 v0.3.2 DYNAMICS_READY comparison for G6P9.
No source mutation and no Euler PDE promotion. Generates a *supplemental*
Framework v1.0.10 gate ledger, without rewriting inherited G6 ledgers.
"""
from __future__ import annotations
import argparse, datetime, hashlib, importlib.util, json, math, os, secrets, sys, zipfile
from pathlib import Path

VERSION='0.3.3'; SCHEMA='sst.a003.g6-upstream/1'
SHA_KPDIST='cb4e49983d18ea373fa2f1f3c63ca0900e0a8093130830c4810cc50e85b50509'
KPF_CASES=(('basic/3.1',47,'fibonacci_torus_F3'),('basic/8.19',86,'fibonacci_torus_F4'))
E011_ZIP_HASH='97cd1acbf23c102e4564f2d74fd329a2d03f32a29b8bd376ffa8b806c14246cc'

class SourceError(RuntimeError):pass

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()

def dump(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():raise SourceError('create-only output collision '+str(path))
    path.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf8')

def load_module(source,alias):
    if not Path(source).is_file():raise SourceError('native module not found: '+str(source))
    spec=importlib.util.spec_from_file_location(alias,source)
    if not spec or not spec.loader:raise SourceError('module loader unavailable')
    module=importlib.util.module_from_spec(spec);sys.modules[alias]=module
    try:spec.loader.exec_module(module)
    except Exception:sys.modules.pop(alias,None);raise
    return module

def check_a058(a058,dist=None):
    """Read-only verification against native A058 decoder and its original source audit."""
    if not a058 or not a058.is_dir():return {'status':'UNRESOLVED','reason':'A058-v0.3.2 directory unavailable','carriers':[]}
    version=a058/'VERSION_CONTRACT.json';version_info=json.loads(version.read_text('utf8')) if version.is_file() else {}
    observed_version=str(version_info.get('version','UNKNOWN'))
    version_alert=observed_version not in ('v0.3.2','0.3.2')
    parser=a058/'tools'/'kpf_readonly.py'
    audit=a058/'A058_audit'/'KPF_AUDIT.json'
    if not audit.is_file():
        return {'status':'UNRESOLVED','reason':'A058 KPF_AUDIT.json missing; source-authenticity must be demonstrated',
                'observed_version':observed_version,'source_version_mismatch':version_alert,'carriers':[]}
    j=json.loads(audit.read_text('utf8'))
    if j.get('schema')!='A058-KPF-INDEPENDENT-AUDIT-1':raise SourceError('A058 KPF audit schema not recognized')
    archive=Path(dist).resolve() if dist else a058/'kpdist-23mar2025.zip'
    if not archive.is_file():return {'status':'UNRESOLVED','reason':'Original KnotPlot distribution ZIP missing',
        'distribution_expected_sha256':j.get('distribution_sha256'),'archive_path':str(archive),
        'observed_version':observed_version,'source_version_mismatch':version_alert,'carriers':[]}
    archive_hash=digest(archive)
    if archive_hash!=SHA_KPDIST or archive_hash!=j.get('distribution_sha256'):
        raise SourceError('A058 distribution SHA mismatch: refusing substitution')
    dec=load_module(parser,'a058_native_kpf_decoder_v033')
    import numpy as np
    items={x.get('catalog'):x for x in j['catalog_samples']}
    carriers=[]
    with zipfile.ZipFile(archive) as z:
        for cat,n,seed in KPF_CASES:
            audit_rec=items.get(cat)
            if not audit_rec or audit_rec.get('status')!='PARSED_SINGLE_CLOSED_COMPONENT':
                raise SourceError('A058 KPF source not admitted by original audit '+cat)
            blob=z.read(audit_rec['archive_path'])
            if hashlib.sha256(blob).hexdigest()!=audit_rec['sha256']:
                raise SourceError('KPF raw bytes do not match frozen A058 audit '+cat)
            geo=dec.decode_kpf(blob)
            if len(geo.points)!=n or geo.component_count!=1:
                raise SourceError('KPF native topology scope/vertex-count disagreement '+cat)
            a=np.asarray(geo.points,dtype=float)
            edge=np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1)
            if np.any(edge<=0) or not np.isfinite(a).all():raise SourceError('invalid native KPF geometry')
            carriers.append({'source':'A058/native KnotPlot KPF', 'catalog':cat,'seed_label_crosswalk':seed,
                'crosswalk_note':'reference naming only: not a new mathematical proof of knot identity',
                'raw_sha256':audit_rec['sha256'],'n_native':n,'encoding':geo.encoding,
                'provider_group':'knotplot_distribution_2025','independence_group':'A058_KNOTPLOT_SOURCE_CATALOG',
                'mean_segment_length':float(np.mean(edge)), 'length_native_units':float(np.sum(edge)),
                'native_resolution_256_satisfied':n>=256, 'physical_geometry':False})
    status='PASS_READONLY_SOURCE_AUTHENTICITY_NOT_DYNAMICS'
    if version_alert:status='UNRESOLVED_SOURCE_VERSION_CONFLICT'
    return {'status':status,'observed_version':observed_version,'requested_directory_version':'v0.3.2',
        'source_version_mismatch':version_alert,'original_audit_sha256':digest(audit),
        'decoder_sha256':digest(parser),'distribution_sha256':archive_hash,
        'carriers':carriers, 'distinct_independence_groups':1,
        'note':'A058 static KPF catalog is an independent geometric SOURCE, not an independent validated time-dependent dynamics experiment.'}

def check_e010(e010):
    if not e010 or not e010.is_dir():return {'status':'UNRESOLVED','reason':'E010-v0.3.2 directory unavailable'}
    ext=e010/'DYNAMICS_EXTENSION_RELEASE.json';code=e010/'pklsa_builder'/'dynamics_ready.py'
    contract=e010/'configs'/'source_contract_production_v2.json'
    if not all(x.is_file() for x in (ext,code,contract)):
        return {'status':'UNRESOLVED','reason':'E010-v0.3.2 extension code or production contract missing',
                'found':{x.name:x.exists() for x in (ext,code,contract)}}
    release=json.loads(ext.read_text('utf8'))
    content=code.read_text('utf8')
    if 'DYN6_FULL_3D_EULER' not in (e010/'pklsa_dynamics_v032.py').read_text('utf8'):
        raise SourceError('E010 v0.3.2 Euler qualification boundary unexpectedly changed')
    if 'Rosenhead' not in content and 'rosenhead' not in content:
        raise SourceError('E010 dynamics model unexpectedly changed')
    return {'status':'PASS_SOURCE_PRESENT_DEVELOPMENT_ONLY','extension':release,
       'extension_release_sha256':digest(ext),'code_sha256':digest(code),
       'production_contract_sha256':digest(contract), 'python_package_version':'0.3.1+v0.3.2 dynamics extension',
       'full_euler_solver_present':False}

def stage_registry(out,e010,atlas,wb,carriers):
    """Versioned E010-v0.3.3 candidate; NEVER write inside E010 or Workbench."""
    if not e010 or not atlas or not wb:return {'status':'UNRESOLVED','reason':'E010, atlas, or Workbench missing'}
    source=e010/'configs'/'source_contract_production_v2.json'
    if not source.is_file() or not atlas.is_dir():return {'status':'UNRESOLVED','reason':'E010 contract or A003 atlas unavailable'}
    try:rel=atlas.resolve().relative_to(wb.resolve()).as_posix()
    except ValueError:return {'status':'UNRESOLVED','reason':'atlas outside declared Workbench root'}
    from g6_pklsa_pilot_v029 import source_check
    from g6_pklsa_temporal_v030 import carrier_rows,SOURCE_ID
    registry,_=source_check(atlas)
    rows=carrier_rows(atlas,registry)
    contract=json.loads(source.read_text('utf8'))
    matches=[s for s in contract.get('sources',[]) if s.get('source_id')==SOURCE_ID]
    if len(matches)>1:raise SourceError('E010 duplicate A003 source IDs')
    spec={'source_id':SOURCE_ID,'kind':'geometry_atlas', 'role':'generated_analytic_geometry_seed',
          'canonical_paths':[rel],'legacy_globs':[],'provider_group':'a003_analytic_seed_atlas',
          'method_group':'a003_fourier_torus','admit_geometry':True,'required':False,
          'independence_note':'Analytic F3/F4 seed families; no empirical or external provider independence'}
    if matches:
        if matches[0].get('provider_group')!=spec['provider_group'] or matches[0].get('canonical_paths')!=[rel]:
            raise SourceError('conflicting E010 A003 source registration')
    else:contract.setdefault('sources',[]).append(spec)
    staged=out/'G6P8_STAGE_E010_V033';staged.mkdir()
    c=staged/'source_contract_production_v2.json';dump(c,contract)
    idx={'schema':'sst.a003.e010-carriers-staged/2','source_id':SOURCE_ID,'carrier_count':len(rows),
         'carriers':rows,'external_source_evidence':carriers,
         'canonical_committed':False,'independent_empirical_carriers':0,
         'no_workbench_files_modified':True}
    f=staged/'a003_v0.3.3_carriers.json';dump(f,idx)
    # Native E010 readback of the staged CONTRACT before any canonical commit.
    source_module=e010/'sst_pklsa'/'__init__.py'
    native_readback={'status':'UNRESOLVED'}
    if source_module.is_file():
        alias='sst_pklsa_a003_stage_v033'
        spec_obj=importlib.util.spec_from_file_location(alias,source_module,submodule_search_locations=[str(source_module.parent)])
        if spec_obj is None or spec_obj.loader is None:raise SourceError('E010 native source resolver unavailable')
        m=importlib.util.module_from_spec(spec_obj);sys.modules[alias]=m
        spec_obj.loader.exec_module(m)
        resolved=[v for v in m.Workbench.open(wb,contract=c).resolve_sources() if v.source_id==SOURCE_ID]
        if len(resolved)!=1 or resolved[0].status!='RESOLVED' or Path(resolved[0].path).resolve()!=atlas.resolve():
            raise SourceError('Native E010 v0.3.2 resolver did not resolve staged A003 contract correctly')
        native_readback={'status':'PASS_STAGED_CONTRACT_NOT_CANONICAL','native_core_sha256':digest(e010/'sst_pklsa'/'core.py'),
            'resolved_source_id':resolved[0].source_id,'resolved_mode':resolved[0].resolution_mode}
    dump(staged/'NATIVE_RESOLVER_READBACK.json',native_readback)
    meta={'schema':'sst.a003.e010-v033-stage/1','base_e010_path':str(e010.resolve()),
        'native_staged_readback':native_readback,'native_staged_readback_sha256':digest(staged/'NATIVE_RESOLVER_READBACK.json'),
        'target_new_release':'E010-v0.3.3', 'original_contract_sha256':digest(source),
        'candidate_contract_sha256':digest(c),'candidate_carrier_index_sha256':digest(f),
        'index_source_sha256':digest(f),'status':'STAGED_NOT_CANONICAL',
        'mandatory_next':'Publish a separately frozen E010-v0.3.3 with source contract, carrier registry, source manifest; independently verify E010 native resolver and re-read SHA256.'}
    dump(staged/'STAGE_MANIFEST.json',meta)
    return {'status':'UNRESOLVED','stage_status':'PREPARED_SHA256_PINNED',
            'stage_manifest_sha256':digest(staged/'STAGE_MANIFEST.json'),
            'candidate_carrier_count':len(rows),'stage_directory':str(staged),
            'immutable_e010_base':True,'canonical_committed':False}

def p9_euler_audit(e010_info,upstream_receipt=None):
    """Independent, fail-closed PDE requirement audit, never substitutes centerline ODE."""
    source={'E010_v032':e010_info.get('status'),'E010_DYN6':'UNRESOLVED',
       'E010_model':'free-space regularized Rosenhead midpoint Biot-Savart filament RK4',
       'C005_model':'same class of regularized filament ODE (distinct numerical software)',
       'pressure_poisson_BC':'NOT_PROVIDED','momentum_PDE_residual':'NOT_PROVIDED',
       'vorticity_transport_3d':'NOT_PROVIDED','independent_3d_Euler_solver':'NOT_PROVIDED',
       'core_density_calibration':'NOT_DERIVED','Euler_GPE_equivalence':'NOT_CLAIMED'}
    if upstream_receipt:
        j=json.loads(Path(upstream_receipt).read_text('utf8'))
        source['external_receipt_sha256']=digest(upstream_receipt)
        source['external_receipt_claim']=j.get('status','UNKNOWN')
        source['external_receipt_unverified']=True
    return {'schema':'sst.a003.g6p9-euler/2','status':'UNRESOLVED',
       'independent_dynamic_baseline':'E010 v0.3.2 DYNAMICS_READY; one finite-core filament model, NOT Euler',
       'checks':source,'euler_certified':False,
       'next_required':'3D divergence-free vorticity initial data + Euler PDE solver + pressure-Poisson BC/residual + fixed-time convergence and independent field comparison'}

def run_source_native_model_diagnostics(a058,a058_info,dist,e010,e011,c005,workbench):
    """Real finite-core filament evaluations on native upstream source coordinates.

    No attempt is made to reinterpret KnotPlot relaxation as Euler. Up-sampling
    A058's 47/86 beads is explicitly prohibited for source resolution claims.
    """
    if not c005.is_dir() or not (c005/'fermat_ext'/'core.py').is_file():
        return {'status':'UNRESOLVED','reason':'C005 v0.6.1 implementation missing','rows':[]}
    if not a058_info.get('carriers'):
        return {'status':'UNRESOLVED','reason':'No authenticated KnotPlot native sources','rows':[]}
    from g6_pklsa_temporal_v030 import c005_callable,rk4,curve_length
    import numpy as np
    rhs,source=c005_callable(c005,0.017)
    rows=[];geom=[]
    archive=Path(dist).resolve() if dist else a058/'kpdist-23mar2025.zip'
    decoder=load_module(a058/'tools'/'kpf_readonly.py','a058_kpf_native_for_dynamics_v033')
    audit=json.loads((a058/'A058_audit'/'KPF_AUDIT.json').read_text('utf8'))
    known={x.get('catalog'):x for x in audit.get('catalog_samples',[])}
    with zipfile.ZipFile(archive) as z:
        for cat,n,seed in KPF_CASES:
            rec=known[cat];data=z.read(rec['archive_path'])
            if hashlib.sha256(data).hexdigest()!=rec['sha256']:raise SourceError('A058 geometry changed before C005 integration')
            pts=np.asarray(decoder.decode_kpf(data).points,dtype=float)
            # Normalize TOTAL LENGTH to 1 as in E010; no new geometric vertices.
            pts=(pts-pts.mean(axis=0))/curve_length(pts)
            geom.append((cat,seed,pts,rec['sha256'],'KNOTPLOT_ORIGINAL_STATIC'))
    e011_state='NOT_PROVIDED'
    if e011:
        # Native E010 v0.3.2 source admission relies on unmodified E011.
        if not Path(e011).is_file():e011_state='SOURCE_MISSING'
        else:
            sys.path.insert(0,str(e010.resolve()))
            from pklsa_builder.dynamics_ready import E011SeedContract,native_geometry
            evidence=E011SeedContract(str(e011),E011_ZIP_HASH)
            anchor=evidence.select('3_1','gilbert')
            gilbert,loc=native_geometry(anchor,str(workbench.resolve()),None,n_original=1024)
            # Path resolution is separately recorded, and source hash is verified by E010.
            import numpy as np
            pts=np.asarray(gilbert,dtype=float)
            geom.append(('E011/Gilbert 3_1','fibonacci_torus_F3',pts,loc['raw_sha256'],'E011_GILBERT_UPSTREAM'))
            e011_state='NATIVE_E010_ADMITTED'
    for cat,seed,x,rawhash,origin in geom:
        y4,_=rk4(rhs,x,0.004,4);y8,_=rk4(rhs,x,0.004,8)
        rms=float(np.sqrt(np.mean(np.sum((y8-y4)**2,axis=1))))
        displacement=float(np.sqrt(np.mean(np.sum((y8-x)**2,axis=1))))
        if not np.isfinite(y8).all():raise SourceError('nonfinite finite-core trajectory '+cat)
        rows.append({'carrier':cat,'seed_label':seed,'source_group':origin,'native_n':len(x),
            'source_sha256':rawhash,'model':'C005 Rosenhead filament ODE, not KnotPlot native dynamics or 3D Euler',
            'T_normalized_model':0.004,'epsilon_normalized':0.017,
            'rms_RK4_4_8':rms,'rms_displacement_T':displacement,
            'length_relative_change':float((curve_length(y8)-curve_length(x))/curve_length(x)),
            'status':'PASS_FINITE_FILAMENT_MODEL_DIAGNOSTIC_ONLY','source_resolution_256':len(x)>=256})
    return {'status':'PASS_MODEL_DIAGNOSTIC_ONLY','rows':rows,
        'e011_state':e011_state,'all_sources_share_one_C005_rhs':True,
        'cannot_demonstrate_independent_native_relaxation_dynamics':True}


def pressure_poisson_source_proxy(c005,atlas):
    """Independent local Euler source-term algebra from a C005 Jacobian.
    This is NOT a pressure solution; there is no boundary condition or momentum residual.
    """
    if not (c005/'fermat_ext'/'core.py').is_file() or not (atlas/'manifest.json').is_file():
        return {'status':'UNRESOLVED','reason':'C005 or A003 atlas unavailable'}
    import numpy as np
    from g6_pklsa_pilot_v029 import source_check
    from fourier_atlas_adapter import read_xyz,safe_atlas_file
    from g6_pklsa_temporal_v030 import SEEDS
    registry,_=source_check(atlas)
    r=next(x for x in registry['records'] if x['id']==SEEDS[0] and x['points']==1200 and x['sampling']=='uniform_t')
    pts=read_xyz(safe_atlas_file(atlas,r['file']),1200)
    # Derived from the single current filament geometry, not an Euler vorticity field.
    sys.path.insert(0,str(c005))
    import fermat_ext.core as core
    v,j,_=core.backend_biot_savart_with_jacobian(pts,pts[::75],epsilon=.05,force_python=True,auto_build=False)
    J=np.asarray(j,float)
    div=np.trace(J,axis1=1,axis2=2)
    poisson=-np.einsum('nij,nji->n',J,J)
    return {'status':'PASS_SOURCE_ONLY_NOT_PRESSURE_SOLVE','model':'instantaneous regularized C005 kernel',
      'probe_count':int(len(poisson)),'max_divergence':float(np.max(np.abs(div))),
      'mean_euler_pressure_poisson_source':float(np.mean(poisson)),
      'max_abs_pressure_poisson_source':float(np.max(np.abs(poisson))),
      'units':'model units; no physical calibration',
      'pressure_boundary_conditions':'NOT_DEFINED','pressure_solution':'NOT_COMPUTED',
      'momentum_euler_residual':'NOT_COMPUTED','full_Euler_PDE':'UNRESOLVED'}

def independent_source_audit(a058_info,e010_info,e011=None,model_diagnostics=None):
    n=len(a058_info.get('carriers',[]))
    has_kpf=n==2 and not a058_info.get('source_version_mismatch')
    # E011 may be verified only by actually accessing native seed coordinates in a separately approved run.
    return {'schema':'sst.a003.g6p16-independent/2','status':'UNRESOLVED',
       'a058_native_kpf_source_verified':bool(has_kpf),
       'a058_native_kpf_carriers':n,'a058_native_beads':[x['n_native'] for x in a058_info.get('carriers',[])],
       'knotplot_native_evolution_qualified':False,
       'e011_gilbert_source_qualified':False,'e011_input_path':str(e011) if e011 else None,
       'distinct_verified_dynamic_provider_families':0,
       'actual_finite_core_computed_carriers':len((model_diagnostics or {}).get('rows',[])),
       'model_diagnostics_status':(model_diagnostics or {}).get('status','UNRESOLVED'),
       'key_obstacle':'A058 KPF catalog is static and 47/86 original beads; E010 v0.3.2 dynamics is a finite-core simulation, not an independent KnotPlot native solver run',
       'requirements':'native A058 runtime trajectories with verified getters and source hashes; independently admitted E011/Gilbert trajectories; same predeclared observable, T, core model and resolution ladder',
       'no_synthetic_interpolation_counted_as_new_independent_evidence':True}

def emit_pdf(out,summary,p16,p8,p9,a058,e010):
    """Optional report; JSON and Framework ledger remain authoritative."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
    except ImportError:return {'status':'UNRESOLVED_REPORTLAB_UNAVAILABLE'}
    path=out/'A003_v0.3.3_G6_UPSTREAM_DIAGNOSTIC_REPORT.pdf'
    c=canvas.Canvas(str(path),pagesize=A4)
    w,h=A4;y=h-48
    def line(t,bold=False):
        nonlocal y
        if y<60:c.showPage();y=h-60
        c.setFont('Helvetica-Bold' if bold else 'Helvetica',10 if not bold else 11)
        c.drawString(43,y,str(t)[:111]);y-=16
    line('A003 v0.3.3  |  G6 upstream verification',True)
    line('Model: E010 v0.3.2 + A058 KPF + C005 v0.6.1 + SST Framework v1.0.10')
    line('Run ID: '+summary['run_id'])
    line('G6P16: '+p16['status']+'  |  G6P8: '+p8['status']+'  |  G6P9: '+p9['status'],True)
    y-=12;line('P16: provenance-separated source family audit',True)
    line('A058 native KPF source audit: '+a058['status'])
    line('KnotPlot native beads: '+', '.join(str(z['n_native']) for z in a058.get('carriers',[])))
    line('Version-contract conflict: '+str(a058.get('source_version_mismatch',False)))
    line('P16 independence: no certified independent native dynamic provider comparison')
    y-=12;line('P8: E010 canonical registration',True)
    line('E010 v0.3.2 extension source: '+e010['status'])
    line('Staged A003 carrier index and native E010 resolver: '+p8.get('stage_status','not available'))
    line('Canonical E010 source tree changed: NO  |  G6P8 remains UNRESOLVED')
    y-=12;line('P9: Euler closure',True)
    line('Poisson algebraic source: '+p9.get('pressure_poisson_source_proxy',{}).get('status','UNRESOLVED'))
    line('Pressure boundary-value problem: NOT SOLVED')
    line('3D vorticity transport and Euler momentum PDE residual: NOT COMPUTED')
    line('DYN6_FULL_3D_EULER in E010-v0.3.2: UNRESOLVED')
    y-=12;line('Scientific classification: DEVELOPMENT / NOT CERTIFIED',True)
    line('A numerical filament ODE does not establish full Euler or knot stability.')
    line('No source overwrite; outputs are unique and create-only.')
    c.save()
    return {'status':'PASS','filename':path.name,'sha256':digest(path)}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workbench',type=Path,required=True);p.add_argument('--e010',type=Path,required=True)
    p.add_argument('--a058',type=Path,required=True);p.add_argument('--c005',type=Path,required=True)
    p.add_argument('--framework',type=Path,required=True);p.add_argument('--atlas',type=Path)
    p.add_argument('--kpdist',type=Path);p.add_argument('--e011',type=Path)
    p.add_argument('--euler-receipt',type=Path)
    p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent.parent/'A003_Fourier_Knot_Import_Adapter_v0.3.3-outputs')
    a=p.parse_args(argv)
    wb=a.workbench.resolve();e010=a.e010.resolve();a058=a.a058.resolve()
    atlas=a.atlas.resolve() if a.atlas else wb/'02_libraries'/'A_knot_libraries'/'A003_Fourier_Knot_Seed_Atlas'/'A003-v0.1.2'
    run=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'_'+secrets.token_hex(5)
    out=a.out.resolve()/run;out.mkdir(parents=True,exist_ok=False)
    # E010 and A058 may be incomplete locally: emit honest UNRESOLVED, never template PASS.
    a058_info=check_a058(a058,a.kpdist);e010_info=check_e010(e010)
    model_dynamics=(run_source_native_model_diagnostics(a058,a058_info,a.kpdist,e010,a.e011,a.c005.resolve(),wb)
                    if a058_info.get('carriers') and not a058_info.get('source_version_mismatch')
                    else {'status':'UNRESOLVED','reason':'A058 authentic native geometry unavailable or version conflict','rows':[]})
    p16=independent_source_audit(a058_info,e010_info,a.e011,model_dynamics)
    p8=stage_registry(out,e010,atlas,wb,a058_info.get('carriers',[]))
    p9=p9_euler_audit(e010_info,a.euler_receipt)
    p9['pressure_poisson_source_proxy']=pressure_poisson_source_proxy(a.c005.resolve(),atlas)
    for k,item in [('A058_NATIVE_KPF_AUDIT',a058_info),('E010_V032_DYNAMICS_PROVIDER',e010_info),
       ('G6P16_INDEPENDENT_PROVIDER_AUDIT',p16),('G6P16_MODEL_TRAJECTORY_DIAGNOSTICS',model_dynamics),('G6P8_CANONICAL_REGISTRY_STAGE',p8),('G6P9_EULER_PDE_REQUIREMENTS',p9)]:
        dump(out/(k+'.json'),item)
    # The real Framework is imported, source-pinned and used, not recreated.
    from a003_diagnostic_v027 import load_framework
    fw_meta=None;fw_hash=None
    try:
        _,fw_meta,mod,fw_hash=load_framework(a.framework.resolve())
        ledger=mod.GateLedger([mod.GateDefinition('G6P16','Native KnotPlot and separately qualified Gilbert dynamics'),
            mod.GateDefinition('G6P8','Versioned canonical E010 registry commit + native readback'),
            mod.GateDefinition('G6P9','Independent full 3D Euler pressure-Poisson/PDE closure')],strict_dependencies=False)
        ledger.run_evaluators({name:(lambda state=state:{'status':state['status'],'reason':state.get('key_obstacle') or state.get('next_required') or state.get('stage_status')})
            for name,state in [('G6P16',p16),('G6P8',p8),('G6P9',p9)]})
        ledger.write(out/'G6_UPSTREAM_GATE_LEDGER.json')
        fw_state=fw_meta.get('status')
    except Exception:
        # Framework version/hash problems are integrity errors, never a scientific UNRESOLVED.
        raise
    summary={'schema':SCHEMA,'version':VERSION,'run_id':run,'overall_status':'UNRESOLVED',
       'G6P16':p16['status'],'G6P8':p8['status'],'G6P9':p9['status'],
       'framework_version':'1.0.10','framework_release_status':fw_state,'framework_gates_source_sha256':fw_hash,
       'ledger_sha256':digest(out/'G6_UPSTREAM_GATE_LEDGER.json'),
       'a058_source_version_alert':a058_info.get('source_version_mismatch'),
       'permanent_e010_source_untouched':True,'C005_RHS_not_Euler':True}
    dump(out/'G6_UPSTREAM_SUMMARY.json',summary)
    dump(out/'PDF_RENDER.json',emit_pdf(out,summary,p16,p8,p9,a058_info,e010_info))
    print(json.dumps({'outputs':str(out),'gates':{k:summary[k] for k in ('G6P16','G6P8','G6P9')},
         'a058_source_version_alert':summary['a058_source_version_alert']},indent=2))
    return 3
if __name__=='__main__':
    try:raise SystemExit(main())
    except (SourceError,ValueError,KeyError,zipfile.BadZipFile) as e:
        print(f'A003 G6-UPSTREAM FAIL_CLOSED: {type(e).__name__}: {e}',file=sys.stderr)
        raise SystemExit(4)
