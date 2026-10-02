from pathlib import Path
import hashlib,hmac,secrets
import numpy as np
from .geometry import resample_closed,normalize_length,normal_frame,min_nonlocal_vertex_distance,segment_lengths,align_cyclic
from .io import discover_sources,geom_sha,dump_json,load_json
from .blind import make_blind_ids,sealed_private_dir
from .evidence import archive_evidence,object_sha256


def analytic_trefoil(n=256):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.c_[(2+np.cos(3*t))*np.cos(2*t),(2+np.cos(3*t))*np.sin(2*t),np.sin(3*t)]


def _variant_parameters(rng,cfg,base=False):
    if base:
        return {'xy_scale':1.0,'z_scale':1.0,'mode':0,'normal_amp':0.0,'binormal_amp':0.0,'phase':0.0}
    return {
        'xy_scale':float(rng.uniform(*cfg.get('xy_scale_range',[.92,1.08]))),
        'z_scale':float(rng.uniform(*cfg.get('z_scale_range',[.82,1.18]))),
        'mode':int(rng.integers(1,int(cfg.get('max_deform_mode',6))+1)),
        'normal_amp':float(rng.uniform(*cfg.get('normal_amp_range',[-.06,.06]))),
        'binormal_amp':float(rng.uniform(*cfg.get('binormal_amp_range',[-.05,.05]))),
        'phase':float(rng.uniform(0,2*np.pi)),
    }


def _apply_variant(base,pa,cfg):
    x=np.asarray(base,float).copy(); x[:,:2]*=pa['xy_scale']; x[:,2]*=pa['z_scale']
    x=normalize_length(x,cfg.get('target_length',2*np.pi))
    if pa['mode']:
        _,n,b=normal_frame(x); s=np.arange(len(x))/len(x); f=np.cos(2*np.pi*pa['mode']*s+pa['phase'])[:,None]
        x=x+pa['normal_amp']*f*n+pa['binormal_amp']*f*b
        x=normalize_length(resample_closed(x,len(x)),cfg.get('target_length',2*np.pi))
    return x


def _source_provenance(dataset,sources,cfg):
    root=Path(dataset).resolve(); manifest_path=root/str(cfg.get('source_family_manifest','source_families.json'))
    if not manifest_path.resolve().is_relative_to(root): raise ValueError('SOURCE_MANIFEST_MUST_BE_INSIDE_DATASET')
    entries={}
    if manifest_path.exists():
        manifest=load_json(manifest_path)
        for entry in manifest.get('sources',[]):
            name=str(entry['path']).replace('\\','/')
            if name in entries: raise ValueError('DUPLICATE_SOURCE_PROVENANCE_PATH')
            entries[name]=entry
    records={}
    for p,_ in sources:
        name=p.resolve().relative_to(root).as_posix(); entry=entries.get(name,{})
        topology=str(entry.get('topology','')).lower(); family=str(entry.get('family_id','')).strip()
        verified=bool(family and str(entry.get('provenance','')).strip() and topology in ('trefoil','3_1','3.1') and entry.get('components')==1 and entry.get('held_out') is True)
        if bool(cfg.get('require_knot_library_records',False)):
            from .knot_library import verify_source_record
            if not verified: raise ValueError(f'SCIENTIFIC_SOURCE_DECLARATION_INCOMPLETE: {name}')
            _points,_record,_hash=verify_source_record(p,entry,dataset_root=root,n=int(cfg.get('candidate_n',128)))
            if entry.get('topology_witness_status')!='SUPPORTED_TREFOIL_DIAGRAM':
                raise ValueError(f'TREFOIL_NUMERICAL_WITNESS_REQUIRED: {name}')
            if entry.get('topology_status')!='SUPPORTED_NUMERICAL_DIAGRAM_NOT_EXTERNAL_PROVIDER_CERTIFIED':
                raise ValueError(f'TOPOLOGY_SUPPORT_STATUS_REJECTED: {name}')
        records[str(p)]={'family_key':f'declared:{family}' if verified else f'unverified:{name}','provenance_declared':verified,'declaration':entry}
    return records


def generate(dataset,out,cfg,config_path=None,repo=None):
    """Generate a source-stratified blind trefoil shape atlas.

    v0.2.1 uses *round-robin* source scheduling: all geometry-qualified
    source families receive their base/early variants before any one source may consume
    the complete candidate budget. Source names remain private; only opaque group IDs
    are public so downstream promotion can preserve family coverage without identity read.
    """
    out=Path(out); private=sealed_private_dir(out)
    if bool(cfg.get('require_knot_library_records',False)):
        if repo is None: raise ValueError('KNOT_LIBRARY_SCIENTIFIC_RUN_REQUIRES_REPO_ROOT')
        from .knot_library import activate
        activate(repo,cfg)
    if (out.exists() and any(out.iterdir())) or (private.exists() and any(private.iterdir())):
        raise FileExistsError('REFUSING_TO_OVERWRITE_EXISTING_EVIDENCE')
    run_kind=str(cfg.get('run_kind','blind_scientific'))
    if run_kind=='blind_scientific' and not 0<float(cfg.get('mesh_gauge_max_final_shape_distance',.035))<=.035:
        raise ValueError('FROZEN_S37_THRESHOLD_MUST_NOT_EXCEED_0.035')
    (out/'geometries').mkdir(parents=True,exist_ok=True); private.mkdir(parents=True,exist_ok=True)
    archive_evidence(Path(__file__).resolve().parents[2],dataset,config_path,cfg,out,private)
    src=discover_sources(
        dataset,cfg['source_regex'],cfg.get('extensions',['.txt','.xyz','.dat']),
        match_mode=cfg.get('source_name_match_mode','fullmatch'),
        reject_name_prefixes=tuple(cfg.get('source_reject_name_prefixes',['link_'])),
        require_closed=bool(cfg.get('require_closed_single_curve',True)),
        closure_gap_ratio_max=float(cfg.get('source_closure_gap_ratio_max',3.0)),
        component_gap_ratio_max=float(cfg.get('source_component_gap_ratio_max',5.0)),
    )
    if not src:
        if not cfg.get('allow_analytic_fallback',False):
            raise RuntimeError(f'No trefoil sources matched under {dataset}; refusing silent analytic fallback')
        src=[(Path('ANALYTIC_TORUS_TREFOIL'),analytic_trefoil(max(256,int(cfg['candidate_n']))))]
    provenance=_source_provenance(dataset,src,cfg) if all(p.exists() for p,_ in src) else {}

    # Deduplicate source shapes after common resample/normalization *and* cyclic/rigid
    # alignment. This imports the pseudoreplication lesson from the earlier phase-delay
    # campaign: differently oriented or re-indexed copies must not count as new sources.
    uniq=[]; raw_unique=[]; source_aliases=[]; dedup_tol=float(cfg.get('source_dedup_rms_tol',1e-7))
    for p,x in src:
        raw=normalize_length(x,cfg.get('target_length',2*np.pi)); y=normalize_length(resample_closed(x,int(cfg['candidate_n'])),cfg.get('target_length',2*np.pi)); h=geom_sha(y,10); duplicate_of=None; dd=None
        for ui,(_up,uy,_uh) in enumerate(uniq):
            _,d,_,_,_=align_cyclic(y,uy,int(cfg.get('cyclic_stride',4)))
            if len(raw)==len(raw_unique[ui]):
                d=min(d,align_cyclic(raw,raw_unique[ui],1)[1],align_cyclic(raw[::-1],raw_unique[ui],1)[1])
            if d<=dedup_tol: duplicate_of=ui; dd=float(d); break
        if duplicate_of is None: uniq.append((p,y,h)); raw_unique.append(raw)
        else: source_aliases.append({'source':str(p),'duplicate_of_unique_index':duplicate_of,'aligned_rms':dd})
    uniq=uniq[:int(cfg.get('max_sources',12))]
    if not uniq: raise RuntimeError('No unique trefoil source geometries')

    group_key=secrets.token_bytes(32); (private/'source_group_key.bin').write_bytes(group_key)
    source_rows=[]
    for si,(p,base,h) in enumerate(uniq):
        source_provenance=provenance.get(str(p),{'family_key':f'unverified:{si}','provenance_declared':False,'declaration':{}})
        gid='G'+hmac.new(group_key,source_provenance['family_key'].encode(),hashlib.sha256).hexdigest()[:12].upper()
        gap=min_nonlocal_vertex_distance(base,int(cfg.get('contact_skip',3)))/max(float(np.mean(segment_lengths(base))),1e-15)
        source_rows.append({'source_index':si,'source':str(p),'source_group_id':gid,'source_geom_sha':h,'base_gap_over_ds':gap,'accepted_candidates':0,**source_provenance})
    dump_json(private/'source_group_map.json',{'groups':source_rows})

    rng=np.random.default_rng(int(cfg.get('candidate_seed',1729))); per=int(cfg.get('variants_per_source',12)); maxc=int(cfg.get('max_candidates',128))
    # Pre-draw each source's own variant sequence. j=0 is always exact normalized base.
    param_grid=[]
    for _ in source_rows:
        pars=[_variant_parameters(rng,cfg,base=True)]
        pars += [_variant_parameters(rng,cfg,base=False) for _j in range(max(0,per-1))]
        param_grid.append(pars)

    rec=[]; rejections=[]
    # Round-robin variant index first, source second. This is the critical v0.2.0 change.
    for j in range(per):
        for si,(p,base,h) in enumerate(uniq):
            if len(rec)>=maxc: break
            pa=param_grid[si][j]; x=_apply_variant(base,pa,cfg)
            gap=min_nonlocal_vertex_distance(x,int(cfg.get('contact_skip',3)))/max(float(np.mean(segment_lengths(x))),1e-15)
            gid=source_rows[si]['source_group_id']
            if gap<float(cfg.get('min_initial_gap_over_ds',1.35)):
                rejections.append({'source_group_id':gid,'source_index':si,'variant_index':j,'reason':'INITIAL_GAP_GATE','initial_gap_over_ds':gap})
                continue
            rec.append({'source':str(p),'source_index':si,'source_group_id':gid,'variant_index':j,'parameters':pa,'initial_gap_over_ds':gap,'geom_sha':geom_sha(x),'x':x})
            source_rows[si]['accepted_candidates']+=1
        if len(rec)>=maxc: break

    if len(rec)<2: raise RuntimeError('Too few geometry-qualified trefoil candidates')
    pub,mapping=make_blind_ids([{k:v for k,v in r.items() if k!='x'} for r in rec],out,private)
    for r,pubrow in zip(rec,pub):
        pubrow['source_group_id']=r['source_group_id']; np.save(out/'geometries'/f"{pubrow['candidate_id']}.npy",r['x'])
    run_kind=str(cfg.get('run_kind','blind_scientific')); manifest=load_json(out/'public_manifest.json'); manifest['format']='SST-TREFOIL-SEED-BLIND-3'; manifest['candidates']=pub; manifest['run_kind']=run_kind
    manifest['source_group_ids']=sorted({r['source_group_id'] for r in rec}); manifest['n_source_groups_with_candidates']=len(manifest['source_group_ids']); dump_json(out/'public_manifest.json',manifest)
    group_counts={}
    for row in source_rows: group_counts[row['source_group_id']]=group_counts.get(row['source_group_id'],0)+row['accepted_candidates']
    dump_json(out/'public_source_coverage.json',{
        'source_groups':[{'source_group_id':gid,'accepted_candidates':count} for gid,count in group_counts.items()],
        'n_unique_source_groups':len(group_counts),'n_groups_with_candidates':sum(count>0 for count in group_counts.values()),
        'n_geometry_rejections':len(rejections),'source_identities_hidden':True,
    })
    dump_json(private/'source_generation_audit.json',{'sources':source_rows,'source_aliases':source_aliases,'rejections':rejections})
    manifest['source_audit_commitment_sha256']=object_sha256(load_json(private/'source_generation_audit.json')); dump_json(out/'public_manifest.json',manifest)
    min_groups=max(3,int(cfg.get('min_scientific_source_groups',3))); n_groups=int(manifest['n_source_groups_with_candidates'])
    provenance_ok=all(r['provenance_declared'] for r in source_rows if r['accepted_candidates']>0)
    diversity_ok=run_kind!='blind_scientific' or (n_groups>=min_groups and provenance_ok)
    source_diversity_status='PASS_SOURCE_DIVERSITY' if diversity_ok else ('INDETERMINATE_INSUFFICIENT_SOURCE_DIVERSITY' if n_groups<min_groups else 'INDETERMINATE_SOURCE_PROVENANCE_UNVERIFIED')
    prepare={
        'format':'SST-TREFOIL-DYNAMIC-SEED-PREPARE-3','run_kind':run_kind,'n_source_files':len(src),'n_unique_sources':len(uniq),'n_source_groups_with_candidates':n_groups,
        'n_candidates':len(rec),'source_identities_hidden':True,'parameter_identities_hidden':True,
        'generation_policy':'source_stratified_round_robin','source_dedup_policy':'cyclic_rigid_aligned_rms','source_dedup_rms_tol':dedup_tol,'n_source_alias_duplicates':len(source_aliases),'all_geometry_qualified_sources_scheduled_before_source_budget_reuse':True,
        'minimum_scientific_source_groups':min_groups,'source_diversity_status':source_diversity_status,
        'source_provenance_declared':provenance_ok,'independence_basis':'declared_provenance_plus_geometry_deduplication' if provenance_ok else 'geometry_only_not_independence_evidence',
        'numerics_verdict':'PASS_PREPARE' if len(rec)>=2 else 'FAIL_PREPARE',
        'physics_verdict':'NOT_APPLICABLE_WORKFLOW_VALIDATION' if run_kind=='workflow_smoke' else ('UNTESTED' if diversity_ok else 'INDETERMINATE'),
        'verdict':'PASS_SOURCE_STRATIFIED_PREPARE' if diversity_ok else source_diversity_status,
    }
    dump_json(out/'prepare_summary.json',prepare)
    if not diversity_ok:
        raise RuntimeError(f'{source_diversity_status}: accepted_groups={n_groups}, required={min_groups}')
    return len(rec)
