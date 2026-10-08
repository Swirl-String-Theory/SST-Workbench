from pathlib import Path
from a054_state.commitment import compute_implementation_bundle,expected_commitment
ROOT=Path(__file__).resolve().parents[1]
def test_commitment():
 actual,_=compute_implementation_bundle(ROOT);assert actual==expected_commitment(ROOT)
