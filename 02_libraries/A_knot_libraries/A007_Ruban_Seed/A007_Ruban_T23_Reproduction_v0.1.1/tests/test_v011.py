import math
from pathlib import Path
import numpy as np
from ruban_falsifier.model import torus_knot,RubanModel
from ruban_falsifier.runner import local_induction_dt_cap,simulate,main
from ruban_falsifier.plotgen import closed

def test_stability_cap_tracks_resolution_squared():
    lam=RubanModel().lambda_tilde
    low=local_induction_dt_cap(torus_knot(128,.154),lam)
    high=local_induction_dt_cap(torus_knot(256,.154),lam)
    assert 3.9<low/high<4.1
    assert 0<high<.002

def test_closed_curve_plot_without_solver_duplicate():
    x=torus_knot(64,.154);y=closed(x)
    assert len(y)==65 and np.array_equal(y[0],y[-1])
    assert np.linalg.norm(x[0]-x[-1])>0

def test_quick_timestep_cap_allows_n256():
    r=simulate(256,.154,.002,.015,.015,1e-5,1.4+.5*math.log(200),.05,20261030,diagnostic_interval=.01)
    assert r['stop_reason']=='TIME_LIMIT'
    assert r['min_stability_cap']<.002
    assert r['steps_taken']>8

def test_failure_exit_without_framework():
    assert main(['CERTIFY'])==4

def test_framework_template_section_markers():
    root=Path(__file__).resolve().parents[1]
    a=(root/'report'/'FALSIFIER_REPORT.tex').read_text()
    b=(root/'docs'/'FRAMEWORK_v1.1.0_RC2_REFERENCE.tex').read_text()
    import re
    x=re.findall(r'^% SST-REPORT-SECTION:(\w+)',a,re.M)
    y=re.findall(r'^% SST-REPORT-SECTION:(\w+)',b,re.M)
    assert x==y and len(x)==16
    assert 'AUTO_RESULTS.tex' in a and 'figures/seed_quad.png' in a
    assert not any(z in a for z in ('SSTTODO','REPLACE_BEFORE_FREEZE','TODO_SCIENCE'))
