from pathlib import Path
import shutil, subprocess, sys, json, tempfile, zipfile, hashlib
KIT=Path(__file__).resolve().parents[1]

def test_registry():
    r=json.loads((KIT/'dataset/registry.json').read_text())
    assert r['counts']['objects']==50 and r['counts']['components']==85
    assert r['counts']['beads']==4431
    assert len(r['objects'])==50
    assert sum(x['component_count'] for x in r['objects'])==85

def test_verifier():
    subprocess.run([sys.executable,str(KIT/'verify_dataset.py')],check=True,capture_output=True,text=True)

def test_install_and_idempotency():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        pk=root/'01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.3.1'
        (pk/'sst_pklsa').mkdir(parents=True)
        (pk/'configs').mkdir()
        (pk/'sst_pklsa/core.py').write_text('class Workbench: pass\n')
        contract={'schema':'x','sources':[{'source_id':'old_provider','admit_geometry':True}]}
        for nm in ('source_contract_v1.json','source_contract_production_v2.json'):
            (pk/'configs'/nm).write_text(json.dumps(contract))
        cmd=[sys.executable,str(KIT/'install_additive.py'),'--workbench',str(root)]
        for _ in range(2):subprocess.run(cmd,check=True,capture_output=True,text=True)
        assert (pk/'sst_pklsa/core.py').read_text()=='class Workbench: pass\n'
        for nm in ('source_contract_v1.json','source_contract_production_v2.json'):
            x=json.loads((pk/'configs'/nm).read_text()); assert len(x['sources'])==2
            assert x['sources'][0]==contract['sources'][0]
            assert x['sources'][1]['admit_geometry'] is False
        assert (root/'03_data/A_knots/04_knotplot/PKLSA_KnotPlot_Native_Census_v0.1.2/raw_native/knot_3.1.txt').is_file()

def test_real_e010_facade_and_geometry_loader():
    """Exercise actual E010-v0.3.1 core.py + io_geometry.py from user's Drive snapshot."""
    from importlib import import_module
    import contextlib
    import os
    import numpy as np
    with tempfile.TemporaryDirectory() as tmp:
        r=Path(tmp); repo=Path('/mnt/data')
        pk=r/'01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.3.1'
        (pk/'sst_pklsa').mkdir(parents=True)
        (pk/'pklsa_builder').mkdir(parents=True)
        (pk/'configs').mkdir()
        shutil.copy2(repo/'core.py',pk/'sst_pklsa/core.py')
        shutil.copy2(repo/'io_geometry.py',pk/'pklsa_builder/io_geometry.py')
        (pk/'sst_pklsa/__init__.py').write_text('from .core import Workbench\n')
        (pk/'pklsa_builder/__init__.py').write_text('')
        (pk/'pklsa_builder/fseries.py').write_text('def sample_fremlin_fseries(*args,**kwargs): raise NotImplementedError\n')
        shutil.copy2(repo/'source_contract_v1.json',pk/'configs/source_contract_v1.json')
        shutil.copy2(repo/'source_contract_production_v2.json',pk/'configs/source_contract_production_v2.json')
        old=json.loads((pk/'configs/source_contract_v1.json').read_text())['sources']
        subprocess.run([sys.executable,str(KIT/'install_additive.py'),'--workbench',str(r)],check=True,capture_output=True)
        add=json.loads((pk/'configs/source_contract_v1.json').read_text())['sources']
        assert add[:-1]==old
        # Use subprocess to isolate package imports from user's environment
        code=(
            'from sst_pklsa import Workbench\n'
            'from sst_pklsa.knotplot_census import KnotPlotNativeCensus\n'
            'wb=Workbench.open('+repr(str(r))+')\n'
            'assert any(s.source_id=="knotplot.native_census.v0.1.2" and s.status=="RESOLVED" and not s.admit_geometry for s in wb.resolve_sources())\n'
            'ds=KnotPlotNativeCensus.open(wb)\n'
            'assert len(ds.list_ids())==50\n'
            'assert [len(x) for x in ds.load("knot_3.1")]==[47]\n'
            'assert [len(x) for x in ds.load("torus_6.21")]==[26,26,26]\n'
            'assert len(ds.load("link_6.3.3"))==3\n'
            'assert ds.provenance("knot_3.1")["independent_from_existing_knotplot_provider"] is False\n'
            'print("REAL_E010_INTEGRATION_PASS")\n'
        )
        env=dict(os.environ,PYTHONPATH=str(pk))
        subprocess.run([sys.executable,'-c',code],env=env,check=True,capture_output=True,text=True)
