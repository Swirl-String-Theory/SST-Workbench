from pathlib import Path

from sst_thpcf.provenance import source_leakage_audit


def _minimal_surface(root: Path) -> None:
    (root / "configs").mkdir(parents=True)
    (root / "configs" / "basic.json").write_text('{"drive":"two_colour"}\n', encoding="utf-8")
    (root / "cpp").mkdir()
    (root / "cpp" / "native.cpp").write_text("double finite_core = 1.0;\n", encoding="utf-8")
    (root / "sst_thpcf").mkdir()
    (root / "sst_thpcf" / "model.py").write_text("MODEL = 'blind'\n", encoding="utf-8")
    # The audit implementation necessarily contains every denylist token and is
    # deliberately outside the audited scientific surface.
    (root / "sst_thpcf" / "provenance.py").write_text(
        "alpha v_circlearrow gamma circulation rho_core rho_f r_c\n", encoding="utf-8"
    )
    (root / "data" / "provenance").mkdir(parents=True)
    (root / "data" / "FROZEN_INPUTS.json").write_text('{"seeds":[]}\n', encoding="utf-8")
    (root / "data" / "provenance" / "upstream.json").write_text('{"topology":"3_1"}\n', encoding="utf-8")


def test_runtime_outputs_and_binary_build_products_cannot_contaminate_g0(tmp_path: Path):
    _minimal_surface(tmp_path)

    # Reproduce the exact v0.2.1 false-positive classes.
    obj = tmp_path / "build" / "temp.win-amd64-cpython-313" / "Release" / "cpp" / "native.obj"
    obj.parent.mkdir(parents=True)
    obj.write_bytes(b"binary-ish\\x00alpha\\x00gamma")

    cert = tmp_path / "SST_Two_Harmonic_Phase_Chirality_Floquet_Blind_Falsifier_v0.2.2-outputs" / "certification"
    cert.mkdir(parents=True)
    (cert / "leakage_audit.json").write_text(
        '{"denylist":["alpha","v_circlearrow","gamma","circulation","rho_core","rho_f","r_c"]}\n',
        encoding="utf-8",
    )
    reveal = tmp_path / "private_reveal"
    reveal.mkdir()
    (reveal / "map.json").write_text('{"secret":"alpha gamma"}\n', encoding="utf-8")

    audit = source_leakage_audit(tmp_path)
    assert audit["pass"] is True
    assert audit["hits"] == []
    assert audit["read_errors"] == []
    assert all(not p.startswith("build/") for p in audit["scanned_files"])
    assert all("-outputs/" not in p for p in audit["scanned_files"])
    assert all(not p.startswith("private_reveal/") for p in audit["scanned_files"])
    assert "sst_thpcf/provenance.py" not in audit["scanned_files"]


def test_forbidden_token_in_allowlisted_blind_source_fails(tmp_path: Path):
    _minimal_surface(tmp_path)
    (tmp_path / "configs" / "bad.json").write_text('{"forbidden":"alpha"}\n', encoding="utf-8")
    audit = source_leakage_audit(tmp_path)
    assert audit["pass"] is False
    assert {"file": "configs/bad.json", "token": "alpha"} in audit["hits"]


def test_empty_audit_surface_fails_closed(tmp_path: Path):
    audit = source_leakage_audit(tmp_path)
    assert audit["pass"] is False
    assert audit["surface_nonempty"] is False
    assert audit["n_scanned"] == 0
