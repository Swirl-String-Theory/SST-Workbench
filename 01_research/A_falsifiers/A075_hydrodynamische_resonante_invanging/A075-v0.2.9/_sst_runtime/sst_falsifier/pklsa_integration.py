"""Read-only integration with PKLSA Universal Atlas Adapter v0.1.0 and E010-v0.4.0.
No implicit source admission or independent-provider claims.
"""
from __future__ import annotations
import importlib.util, json, os, sys
from pathlib import Path

ATLAS_ZIP='SST_Parametric_Knot_Link_Seed_Atlas_v0.4.0_outputs.zip'
FAMILY='E010_pklsa_parametric_knot_link_seed_atlas'

def find_workbench(instance_root, explicit=None):
    if explicit:return Path(explicit).expanduser().resolve()
    env=os.getenv('SST_WORKBENCH_ROOT')
    if env:return Path(env).expanduser().resolve()
    p=Path(instance_root).resolve()
    for candidate in [p,*p.parents]:
        if (candidate/'01_research'/'E_pipelines').is_dir() and (candidate/'04_tools'/'A_geometry').is_dir():
            return candidate
    raise FileNotFoundError('Set SST_WORKBENCH_ROOT to the actual SST-Workbench root; no geometry fallback')

def resolve_paths(instance_root, cfg=None, workbench=None):
    cfg=cfg or {}; wb=find_workbench(instance_root,workbench)
    geom=wb/'04_tools'/'A_geometry'
    bridge_dir=None
    for candidate in [geom/'PKLSA_Universal_Atlas_Adapter'/'PKLSA_Universal_Atlas_Adapter_v0.1.0',
                      geom/'PKLSA_Universal_Atlas_Adapter_v0.1.0',
                      geom/'PKLSA_Universal_Atlas_Adapter']:
        if (candidate/'pklsa_bridge'/'__init__.py').is_file():bridge_dir=candidate;break
    if bridge_dir is None:
        for candidate in sorted(geom.glob('**/PKLSA_Universal_Atlas_Adapter_v0.1.0')):
            if (candidate/'pklsa_bridge'/'__init__.py').is_file():bridge_dir=candidate;break
    if bridge_dir is None:raise FileNotFoundError('Pinned PKLSA_Universal_Atlas_Adapter_v0.1.0/pklsa_bridge not found')
    path=os.environ.get('E010_ATLAS') or cfg.get('atlas',{}).get('path')
    parent=wb/'01_research'/'E_pipelines'/FAMILY/'E010-v0.4.0'
    candidates=[Path(path).expanduser()] if path else [parent/ATLAS_ZIP,parent/'SST_Parametric_Knot_Link_Seed_Atlas_v0.4.0_outputs',parent]
    atlas=next((p.resolve() for p in candidates if (p.is_file() and p.suffix.lower()=='.zip') or (p.is_dir() and (p/'COMBINED_INDEX.json').is_file())),None)
    if atlas is None:raise FileNotFoundError('Pinned E010-v0.4.0 ZIP/index not found. Set E010_ATLAS to the published ZIP or extracted payload root')
    return {'workbench':wb,'adapter':bridge_dir,'atlas':atlas}

def _load_bridge(adapter_root):
    # Prefer the exact project-local source; never import an unrelated global pklsa_bridge.
    if str(adapter_root) not in sys.path:sys.path.insert(0,str(adapter_root))
    import pklsa_bridge
    module_path=Path(pklsa_bridge.__file__).resolve()
    if not module_path.is_relative_to(adapter_root.resolve()):raise RuntimeError('PKLSA bridge import path mismatch')
    if getattr(pklsa_bridge,'__version__',None)!='0.1.0':raise RuntimeError('Unsupported PKLSA bridge version')
    return pklsa_bridge

def with_bridge(instance_root, cfg, callback, *, workbench=None):
    paths=resolve_paths(instance_root,cfg,workbench)
    mod=_load_bridge(paths['adapter'])
    with mod.AtlasBridge(paths['atlas']) as reader:return callback(reader, paths)

def check_atlas(instance_root,cfg,*,workbench=None):
    try:
        def run(reader,paths):
            ids=reader.query(topology='3_1',collection='historical_v031',limit=3)
            return {'schema':'SST-PKLSA-PREFLIGHT-1','status':'AVAILABLE',
                    'atlas_version':'E010-v0.4.0','adapter_version':'v0.1.0','workbench':str(paths['workbench']),
                    'atlas_path':str(paths['atlas']),'atlas_index_sha256':reader.index_sha,
                    'trefoil_preview_ids':ids,'research_only_admitted':False,
                    'scientific_status':'INTAKE_ONLY_NOT_DYNAMICS_QUALIFIED'}
        return with_bridge(instance_root,cfg,run,workbench=workbench)
    except Exception as e:return {'schema':'SST-PKLSA-PREFLIGHT-1','status':'BLOCKED','reason':f'{type(e).__name__}: {e}',
                              'no_silent_fallback':True,'scientific_status':'NOT_EVALUATED'}

def select_ids(instance_root,cfg,*,topology=None,embedding=None,collection=None,limit=10,allow_research=False):
    return with_bridge(instance_root,cfg,lambda b,p:b.query(topology=topology,embedding=embedding,
        collection=collection,limit=limit,allow_research=allow_research))

def export_dataset(instance_root,cfg,ids,destination,*,allow_research=False):
    if Path(destination).exists():raise FileExistsError('Refuse to overwrite existing atlas export')
    return with_bridge(instance_root,cfg,lambda b,p:b.export_dataset(ids,destination,allow_research=allow_research))
