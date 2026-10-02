"""Shared import of paper_upgrade_certificate from family gate modules."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_certificate_module():
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "07_scripts" / "paper_upgrade_certificate.py"
        if cand.is_file():
            name = "paper_upgrade_certificate"
            if name in sys.modules:
                return sys.modules[name]
            spec = importlib.util.spec_from_file_location(name, cand)
            if spec is None or spec.loader is None:
                break
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("paper_upgrade_certificate.py not found under any 07_scripts/")
