"""Pinned E013/E011 admission. Integrity errors abort before geometry loading."""
from __future__ import annotations
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys


class AdmissionError(RuntimeError):
    pass


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def require(condition, reason):
    if not condition:raise AdmissionError(reason)


def workspace_path(workbench, relative):
    root = Path(workbench).resolve()
    p = (root/relative).resolve()
    require(p.is_relative_to(root), 'source path escapes workbench')
    return p


def verify_file(path, expected, label):
    require(Path(path).is_file(),label+' missing')
    require(digest(path)==expected,label+' hash mismatch')


def verify_loader(workbench, pins):
    loader = workspace_path(workbench,pins['e010_root'])
    require(loader.name=='E010-v0.3.1','E010 loader version mismatch')
    files = pins['e010_loader_files']
    require(bool(files),'E010 loader pins missing')
    actual = {p.relative_to(loader).as_posix() for p in (loader/'pklsa_builder').glob('*.py')}
    require(actual=={Path(p).as_posix() for p in files},'E010 loader file set mismatch')
    for relative, expected in files.items():
        p = workspace_path(loader,relative)
        verify_file(p,expected,'E010 loader '+relative)
    release=pins['e010_release']
    verify_file(workspace_path(workbench,release['path']),release['sha256'],'E010 production release')
    for name, module in list(sys.modules.items()):
        if name=='pklsa_builder' or name.startswith('pklsa_builder.'):
            filename = getattr(module,'__file__',None)
            require(filename is not None and Path(filename).resolve().is_relative_to(loader), 'E010 imported loader origin mismatch')
    return loader


def validate_manifest(path, workbench, pins):
    verify_file(path,pins['expected_manifest_sha256'],'E013 external binding')
    data = read(path)
    core = {k:v for k,v in data.items() if k!='content_sha256_without_self_field'}
    self_hash = hashlib.sha256(json.dumps(core,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    require(self_hash==data.get('content_sha256_without_self_field'),'E013 self hash mismatch')
    require(data.get('schema')=='E013-COMMON-CARRIER-MANIFEST-1','E013 schema mismatch')
    require(data.get('sklsa_release_id')=='E011-v0.3.0','E011 release mismatch')
    require(data.get('legacy_falsifier_outputs_used_as_evidence') is False,'legacy evidence forbidden')
    carriers = data.get('carriers')
    require(isinstance(carriers,list) and bool(carriers),'empty carrier selection')
    count = data.get('selected_carrier_count')
    require(type(count) is int and count==len(carriers),'selected carrier count mismatch')
    for key, field in [('e011_index','sklsa_static_index_sha256'),('e011_anchors','sklsa_provider_anchors_sha256')]:
        spec = pins[key]
        verify_file(workspace_path(workbench,spec['path']),spec['sha256'],key)
        require(data.get(field)==spec['sha256'],key+' manifest binding mismatch')
    index_rows = read(workspace_path(workbench,pins['e011_index']['path']))
    require(isinstance(index_rows,list),'E011 index is not a list')
    index = {r['topology_id']:r for r in index_rows}
    require(len(index)==len(index_rows),'duplicate E011 topology')
    anchors = [json.loads(line) for line in workspace_path(workbench,pins['e011_anchors']['path']).read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    def join(row):return tuple(row.get(k) for k in ['topology_id','static_seed_id','carrier_id','provider_group'])
    anchor_by_key = {join(r):r for r in anchors}
    require(len(anchor_by_key)==len(anchors),'duplicate E011 anchor')
    seen, seeds, groups, paths = set(), set(), defaultdict(set), []
    for row in carriers:
        key = join(row)
        require(all(isinstance(x,str) and x for x in key),'incomplete carrier join key')
        require(key not in seen and row['static_seed_id'] not in seeds,'duplicate selected seed')
        seen.add(key);seeds.add(row['static_seed_id'])
        anchor = anchor_by_key.get(key)
        require(anchor is not None,'E011 anchor join mismatch')
        require(anchor.get('static_ready') is True and anchor.get('provider_anchor') is True,'E011 anchor not STATIC_READY')
        top = index.get(row['topology_id'],{})
        require(top.get('static_ready') is True and row['static_seed_id'] in top.get('provider_anchor_seed_ids',[]),'E011 index seed join mismatch')
        require(row.get('e011_static_status')==top.get('static_status'),'E011 status join mismatch')
        loc = row.get('source_locator')
        require(isinstance(loc,dict) and loc==anchor.get('source_locator'),'source locator join mismatch')
        for field in ['raw_sha256','geometry_sha256']:
            require(isinstance(row.get(field),str) and len(row[field])==64 and row[field]==loc.get(field),field+' binding mismatch')
        source = workspace_path(workbench,loc['source_path'])
        require(source.is_relative_to(Path(workbench).resolve()/'03_data/A_knots'),'geometry source outside admitted data root')
        verify_file(source,row['raw_sha256'],'raw geometry')
        groups[row['topology_id']].add(row['provider_group'])
        paths.append(source)
    loader = verify_loader(workbench,pins)
    return {'manifest':data,'source_paths':paths,'loader':loader,
            'provider_counts':{k:len(v) for k,v in groups.items()},
            'cross_provider_science_ready':all(len(v)>=pins['scientific_provider_minimum'] for v in groups.values())}
