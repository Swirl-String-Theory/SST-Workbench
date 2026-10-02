from pathlib import Path

from sst_thpcf.campaign import allocate_archive_path, allocate_output_dir


def test_existing_output_is_preserved(tmp_path: Path):
    first, mode1 = allocate_output_dir(tmp_path, "TEST1")
    assert mode1 == "canonical_fresh"
    first.mkdir()
    sentinel = first / "sentinel.txt"
    sentinel.write_text("keep")

    second, mode2 = allocate_output_dir(tmp_path, "TEST2")
    assert mode2 == "preserved_existing_fallback"
    assert second != first
    assert "_RUN_TEST2" in second.name
    assert sentinel.read_text() == "keep"
    assert first.exists()


def test_existing_zip_is_never_overwritten(tmp_path: Path):
    first = allocate_archive_path(tmp_path, "BLIND", "TEST1")
    first.write_bytes(b"old")
    second = allocate_archive_path(tmp_path, "BLIND", "TEST2")
    assert second != first
    assert "_RUN_TEST2" in second.name
    assert first.read_bytes() == b"old"
