from __future__ import annotations
from pathlib import Path
import csv, json, subprocess
from .io_xyz import parse_xyz,parse_vect
from .gilbert import uniform_resample_closed
from .geometry import analyze_components
from .util import sha256_file,write_json,json_safe

def sidecar(path):
    out={}
    for suffix in ['.knotplot.json','.metrics.json']:
        p=path.with_suffix('').with_name(path.stem+suffix)
        if p.exists():
            try: out[p.name]=json.loads(p.read_text(encoding='utf-8'))
            except Exception as e: out[p.name]={'parse_error':str(e)}
    return out

def _find_key(obj, names):
    names={n.lower() for n in names}
    if isinstance(obj,dict):
        for k,v in obj.items():
            if str(k).lower() in names: return v
        for v in obj.values():
            z=_find_key(v,names)
            if z is not None: return z
    elif isinstance(obj,list):
        for v in obj:
            z=_find_key(v,names)
            if z is not None: return z
    return None

def _sidecar_fields(sc):
    merged=list(sc.values())
    def first(names):
        for obj in merged:
            v=_find_key(obj,names)
            if v is not None: return v
        return None
    linking=first({'linking_matrix','linkingMatrix','linking_matrix_reported'})
    return {
      'knotplot_safe':first({'safe','knotplot_safe'}),
      'sidecar_component_count':first({'component_count','componentCount','component_count_expected'}),
      'sidecar_vertices_per_component_json':json.dumps(first({'vertices_per_component','verticesPerComponent'}),separators=(',',':')) if first({'vertices_per_component','verticesPerComponent'}) is not None else None,
      'sidecar_linking_matrix_json':json.dumps(linking,separators=(',',':')) if linking is not None else None,
      'ridgerunner_residual':first({'residual','projected_residual','residual_norm'}),
      'ridgerunner_ropelength':first({'ropelength','Rop','sampled_ropelength'}),
      'ridgerunner_thickness':first({'thickness','Thi'}),
      'candidate_status':first({'candidate_status','candidateStatus'}),
      'source_role':first({'source_role','sourceRole'}),
    }

def analyze_folder(root,pattern,out,samples=300):
    root=Path(root); out=Path(out); out.mkdir(parents=True,exist_ok=True); rows=[]
    paths=sorted(root.glob(pattern))
    for p in paths:
        try: comps=parse_vect(p) if p.suffix.lower()=='.vect' else parse_xyz(p)
        except Exception as e:
            rows.append({'file':str(p),'status':'PARSE_FAIL','error':str(e)}); continue
        audit=[c.copy() for c in comps]; uniform=[uniform_resample_closed(c,samples) for c in comps]
        g=analyze_components(uniform,auto_build_native=True); sc=sidecar(p)
        row={'file':str(p),'file_sha256':sha256_file(p),'status':'OK','component_count':len(comps),'raw_vertices_json':json.dumps([len(c) for c in audit]),
             'analysis_samples_per_component':samples,'sampled_total_length':g['total_length'],'sampled_reach_proxy':g['global_sampled_reach_proxy'],
             'length_over_diameter_proxy':g['global_length_over_diameter_proxy'],'edge_cv_max':max(c['edge_cv'] for c in g['components']),
             'writhe_sum_midpoint_proxy':sum(c['writhe_midpoint_proxy'] for c in g['components']),'sidecar_present':bool(sc),**_sidecar_fields(sc)}
        rows.append(row); write_json(out/'geometry'/(p.stem+'.json'),{'source':str(p),'sidecars':sc,'geometry':g})
    if rows:
        keys=[]
        for r in rows:
            for k in r:
                if k not in keys: keys.append(k)
        with (out/'ridgerunner_master.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)
    write_json(out/'ridgerunner_master.json',{'schema':'sst21d.ridgerunner.v0.1','rows':rows}); return {'files':len(rows)}

def make_bridge(pipeline_cmd,out):
    content=f"""@echo off\nsetlocal\nif "%~1"=="" (\n  echo Usage: %~nx0 input_seed.txt [analysis_output]\n  exit /b 2\n)\nset "SEED=%~f1"\nset "OUT=%~2"\nif "%OUT%"=="" set "OUT=%~dp1sst21d_analysis"\ncall "{pipeline_cmd}" "%SEED%"\nif errorlevel 1 exit /b %errorlevel%\npy -3 -m sst21d analyze-xyz --input "%~dp1" --glob "*_polish.txt" --samples 300 --out "%OUT%"\n"""
    Path(out).write_text(content,encoding='utf-8'); return out
