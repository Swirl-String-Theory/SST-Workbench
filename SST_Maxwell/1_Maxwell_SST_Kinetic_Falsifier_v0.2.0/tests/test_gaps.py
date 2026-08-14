from maxwell_sst_falsifier.gaps import classify_amplitude_scans


def rows(offset):
    return [
        {"knot": "K", "mode_id": "m", "amplitude": str(a), "delta_energy_eV": str(offset + a*a)}
        for a in (0.001, 0.002, 0.004, 0.008)
    ]


def test_continuous_branch():
    r = classify_amplitude_scans(rows(0.0), 1e-8, 0.02)[0]
    assert r["status"] == "CONTINUOUS_TO_ZERO"


def test_finite_intercept_branch():
    r = classify_amplitude_scans(rows(0.5), 1e-8, 0.02)[0]
    assert r["status"] == "FINITE_INTERCEPT_CANDIDATE"
