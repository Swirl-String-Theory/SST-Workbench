from pathlib import Path
import pytest

from a055_science.upstream import import_a054_runner


def test_import_a054_runner_symbol_present_and_missing_runner_fails_closed(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="isolated blind runner absent"):
        import_a054_runner(tmp_path)
