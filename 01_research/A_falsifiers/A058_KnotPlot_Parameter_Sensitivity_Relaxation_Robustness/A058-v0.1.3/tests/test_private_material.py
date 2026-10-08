from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_framework_private_material_present_and_256_bit():
    for rel in ("private/OPAQUE_ID_KEY.bin","private/REVEAL_NONCE.bin"):
        p=ROOT/rel
        assert p.is_file(), rel
        assert len(p.read_bytes())==32, rel
