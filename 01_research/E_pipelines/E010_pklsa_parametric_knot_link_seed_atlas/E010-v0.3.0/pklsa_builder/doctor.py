from __future__ import annotations
from pathlib import Path
import importlib, json, platform, sys

def doctor(workbench_root=None, base=None):
    root=Path(__file__).resolve().parents[1]
    packages={}
    for name in ('numpy','scipy','xlrd','pybind11'):
        try:
            m=importlib.import_module(name); packages[name]={'available':True,'version':getattr(m,'__version__',None)}
        except Exception as e:
            packages[name]={'available':False,'error':str(e)}
    try:
        from . import _native
        native={'available':True,'openmp_enabled':bool(getattr(_native,'openmp_enabled',False))}
    except Exception as e:
        native={'available':False,'error':str(e),'fallback':'pure Python O(N^2) kernels remain available'}
    wb=Path(workbench_root).resolve() if workbench_root else None
    bp=Path(base).resolve() if base else None
    required={
        'bundled_linkinfo_xls': root/'data'/'topology_sources'/'linkinfo_data_complete.xls',
        'bundled_knotinfo_xls_zip': root/'data'/'topology_sources'/'knotinfo_data_complete.xls.zip',
        'fremlin_fixture': root/'data'/'fixtures'/'knot.3_1.fseries',
        'gilbert_fixture': root/'data'/'fixtures'/'Ideal.txt.gz',
        'katlas_braid_fixture': root/'data'/'fixtures'/'3_1_katlas_braid.xyz',
        'workbench_source_catalog': root/'data'/'SST_WORKBENCH_KNOT_SOURCES_LOCATIONS_0.1.json',
    }
    source_probes={}
    if wb:
        probes={
            'a001_knotplot_relaxed':wb/'KnotPlot'/'knots',
            'a002_knotplot_fourier':wb/'KnotPlot'/'Knots_FourierSeries',
            'a003_qhp':wb/'KnotPlot'/'qhp',
            'a004_gilbert':wb/'Ideal_Sources',
            'a005_katlas':wb/'Katlas_Sources_v0.2.2_Outputs',
            'a006_fremlin':wb/'Fremlin_FourierSeries',
            'a007_knot_library':wb/'Knot_Library',
            'a008_ptsa':wb/'PTSA_Parametric_Trefoil_Seed_Atlas_v1.0.0',
        }
        source_probes={k:{'path':str(v),'exists':v.exists()} for k,v in probes.items()}
    return {
        'schema':'PKLSA-BUILDER-DOCTOR-2',
        'python':sys.version,
        'platform':platform.platform(),
        'packages':packages,
        'native_backend':native,
        'bundled_inputs':{k:{'path':str(v),'exists':v.exists(),'bytes':v.stat().st_size if v.exists() else None} for k,v in required.items()},
        'workbench_root':str(wb) if wb else None,
        'workbench_source_probes':source_probes,
        'base':str(bp) if bp else None,
    }
