from pathlib import Path
import zipfile

from sst_bkm.campaign import NAME, VERSION, create_archives


def test_create_archives_accepts_relative_outbase_with_absolute_root(tmp_path, monkeypatch):
    version_root = tmp_path / "version"
    version_root.mkdir()
    monkeypatch.chdir(version_root)

    outbase = Path(f"{NAME}_{VERSION}-outputs")
    blind = outbase / "BLIND"
    revealed = outbase / "REVEALED"
    blind.mkdir(parents=True)
    revealed.mkdir(parents=True)
    (blind / "summary.json").write_text("{}\n", encoding="utf-8")
    (revealed / "provenance.json").write_text("{}\n", encoding="utf-8")

    archives = [Path(x) for x in create_archives(Path.cwd(), outbase, revealed)]
    assert all(p.is_file() for p in archives)

    expected_prefix = f"{NAME}_{VERSION}-outputs/"
    with zipfile.ZipFile(archives[0]) as z:
        assert z.testzip() is None
        assert z.namelist() == [expected_prefix + "BLIND/summary.json"]
    with zipfile.ZipFile(archives[1]) as z:
        assert z.testzip() is None
        assert expected_prefix + "BLIND/summary.json" in z.namelist()
        assert expected_prefix + "REVEALED/provenance.json" in z.namelist()
    with zipfile.ZipFile(archives[2]) as z:
        assert z.testzip() is None
        assert expected_prefix + "BLIND/summary.json" in z.namelist()
        assert expected_prefix + "REVEALED/provenance.json" in z.namelist()
