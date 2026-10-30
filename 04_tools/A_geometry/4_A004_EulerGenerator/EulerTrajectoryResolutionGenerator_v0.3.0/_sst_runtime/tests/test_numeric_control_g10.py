from sst_falsifier.auto_backend_matrix import assess_numeric_control

def matrix(cpp=[1.,2.],gpu=None):
    records={'py':{'scientific_execution':True,'observable':[1.,2.]}}
    if cpp is not None:records['cpp']={'scientific_execution':True,'observable':cpp}
    if gpu is not None:records['gpu']={'scientific_execution':True,'observable':gpu}
    count=sum(rec['scientific_execution'] for rec in records.values())
    return {'status':'EXECUTION_CONTRACT_PASS' if count>=2 else 'EXECUTION_CONTRACT_BLOCKED',
            'counted_backend_categories':count,'scientific':records}

def test_parity_pass():
    assert assess_numeric_control(matrix(),{})['status']=='PASS'
def test_wrong_parity_fails_not_certified():
    assert assess_numeric_control(matrix([2.,2.]),{})['status']=='FAIL'
def test_missing_second_execution_is_unresolved():
    assert assess_numeric_control(matrix(None),{})['status']=='UNRESOLVED'
def test_missing_python_reference_is_unresolved():
    m=matrix();m['scientific'].pop('py');assert assess_numeric_control(m,{})['status']=='UNRESOLVED'
def test_gpu_numeric_pass():
    assert assess_numeric_control(matrix(None,[1+1e-6,2]),{})['status']=='PASS'
def test_gpu_numeric_fail():
    assert assess_numeric_control(matrix(None,[1.01,2]),{})['status']=='FAIL'
def test_invalid_tolerance_refuses():
    assert assess_numeric_control(matrix(),{'numeric_tolerance_cpp':0})['status']=='UNRESOLVED'
