from pathlib import Path
import os, json
import numpy as np
import pytest

from sst_seed_falsifier.io import load_json
from sst_seed_falsifier import knot_library as kl


def _cfg():
    return {
        'require_knot_library_records':True,
        'knot_library':{
            'required':True,'required_version':'0.2.5',
            'relative_path':'unused-when-env-set','env_var':'SST_KNOT_LIBRARY_HOME'
        }
    }


def test_pinned_knot_library_and_fremlin_provenance(tmp_path,monkeypatch):
    home=os.environ.get('SST_KNOT_LIBRARY_HOME')
    if not home: pytest.skip('set SST_KNOT_LIBRARY_HOME to run external dependency integration test')
    # Reset module globals in case another test activated it.
    kl._ACTIVE=None; kl._ACTIVE_MODULE=None
    monkeypatch.setenv('SST_KNOT_LIBRARY_HOME',home)
    att=kl.activate(tmp_path,_cfg())
    assert att['runtime_version']=='0.2.5'
    sk=kl.module()
    d=tmp_path/'Fremlin_FourierSeries'/'fremlin'/'3_1'; d.mkdir(parents=True)
    p=d/'knot.3_1.short'; np.savetxt(p,sk.classic_trefoil(64))
    _,rec,h=kl.make_source_record(p,n=64,relative_path='Fremlin_FourierSeries/fremlin/3_1/knot.3_1.short')
    assert len(h)==64
    assert rec['geometry']['source_family']=='fremlin_short_coordinate'
    assert rec['geometry']['source_provider']['provider_id']=='fremlin_local_fourier'
    assert rec['topology_expected']=='3_1'
    assert rec['topology_certification']['status']=='UNVERIFIED'
