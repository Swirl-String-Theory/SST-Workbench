from pathlib import Path
import zipfile
import pytest
from sst_torsion.pipeline import prepare,analyze,reveal
from sst_torsion.run_contract import seal_run,package_run,verify_seal,verify_reveal

ROOT=Path(__file__).resolve().parents[1]


def test_all_three_package_scopes_verify_after_extraction(tmp_path):
    run=prepare(ROOT,'portable-regression',tmp_path/'runs')
    analyze(run,'python');seal_run(run);reveal(run)
    archives=package_run(run)
    for path in archives:
        path=Path(path)
        target=tmp_path/path.stem
        with zipfile.ZipFile(path) as z:
            assert not any('/PRIVATE/' in name for name in z.namelist())
            assert z.testzip() is None
            z.extractall(target)
        if path.name.endswith('_BLIND.zip'):
            verify_seal(target,require_private_key=False)
            assert not (target/'REVEALED').exists()
        elif path.name.endswith('_REVEALED.zip'):
            verify_reveal(target)
            assert not (target/'BLIND').exists()
        else:
            restored=target/run.name
            verify_seal(restored);verify_reveal(restored)
            (restored/'REVEALED'/'reveal_key.json').write_text('{}')
            with pytest.raises(RuntimeError):
                verify_seal(restored)


def test_packaging_will_not_overwrite_an_existing_archive(tmp_path):
    run=prepare(ROOT,'no-overwrite',tmp_path)
    analyze(run,'python');seal_run(run);reveal(run)
    paths=package_run(run)
    before=[Path(p).read_bytes() for p in paths]
    with pytest.raises(FileExistsError):
        package_run(run)
    assert before==[Path(p).read_bytes() for p in paths]
