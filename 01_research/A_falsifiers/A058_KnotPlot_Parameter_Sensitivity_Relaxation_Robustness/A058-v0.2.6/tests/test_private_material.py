from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_private_material():
    assert (ROOT/'private/OPAQUE_ID_KEY.bin').stat().st_size==32;assert (ROOT/'private/REVEAL_NONCE.bin').stat().st_size==32
