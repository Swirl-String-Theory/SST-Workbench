
from pathlib import Path
import pandas as pd

from sst_link_suite.qm_report import dataframe_to_markdown_safe


def test_markdown_fallback_without_tabulate(monkeypatch):
    frame = pd.DataFrame({"a": [1, 2], "b": ["x|y", "z"]})

    def fail(*args, **kwargs):
        raise ImportError("simulated missing tabulate")

    monkeypatch.setattr(pd.DataFrame, "to_markdown", fail)
    text = dataframe_to_markdown_safe(frame, index=False)

    assert "| a | b |" in text
    assert "x\\|y" in text
    assert "| 2 | z |" in text
