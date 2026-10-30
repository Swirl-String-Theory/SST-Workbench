"""Independent, fail-closed consumer interface to the E010 v0.4.0 atlas.

Scientific status is not promoted by this package.
"""
from .adapter import AtlasBridge, AdmissionError, AtlasContractError, resample_closed_arclength
from .consumer import ConsumerDataset
__version__ = '0.1.0'
__all__ = ['AtlasBridge','AdmissionError','AtlasContractError','resample_closed_arclength','ConsumerDataset']
