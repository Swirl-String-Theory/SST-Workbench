from convert_catalog_kpc import checkpoint_name, transform_kpc

def test_checkpoint_mapping():
    assert checkpoint_name('analytic_D1')=='i00000'; assert checkpoint_name('trial_015k')=='i15000'

def test_refine_nbeads_is_target_runtime_form():
    src='nbeads 300\necho CHECKPOINT analytic_D1\nsave knots/knot_0.1/knot_0.1_analytic_D1.txt\n'
    out=transform_kpc(src,'knot_0.1')
    assert 'refine nbeads 300' in out
    assert '\nnbeads 300\n' not in out

def test_recipe_injection():
    recipe={'recipe_id':'R','approved_for_catalog':True,'parameters':{'collision':'fast','close':1,'max_dr':.01,'mechforce':True,'elecforce':True,'bendforce':False,'charge':30,'hooke':2,'power':7,'timeincr':15,'bencon':1,'stusplit':0,'dstep':1,'bradius':.1,'cradius':.05,'energy_model':'MD'}}
    src='reset all\nload 3.1\nrefine nbeads 300\ncentre\nfitto mindist 1.05\ncharge 15\nhooke 1\npower 6\ntimeincr 15\necho CHECKPOINT analytic_D1\nsave knots/knot_3.1/knot_3.1_analytic_D1.txt\n'
    out=transform_kpc(src,'knot_3.1',recipe)
    assert 'charge 30' in out and 'hooke 2' in out and 'power 7' in out
    assert '% RECIPE_SHA256 ' in out
