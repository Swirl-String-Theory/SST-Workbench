from pathlib import Path


def test_msvc_pi_portability():
    src = (Path(__file__).resolve().parents[1] / "cpp" / "vortex_shear_native.cpp").read_text(encoding="utf-8")
    assert "M_PI" not in src
    assert "constexpr double kPi" in src
