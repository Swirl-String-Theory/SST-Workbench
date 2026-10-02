import numpy as np
import pytest
from sst_torsion.fitting import classify_dispersion


@pytest.mark.parametrize('exponent',[.5,3.])
def test_out_of_model_data_is_ambiguous(exponent):
    k=np.arange(1.,11.)
    report=classify_dispersion(k,k**exponent)
    assert report['classification']=='AMBIGUOUS'
    assert report['decision_reason']=='inadequate_fit_or_insufficient_model_separation'


@pytest.mark.parametrize('bad',[[1,2,3,np.nan],[1,1,1,1],[0,1,2,3]])
def test_invalid_frequency_pairs_rejected(bad):
    with pytest.raises(ValueError):
        classify_dispersion(bad,np.ones(4))
