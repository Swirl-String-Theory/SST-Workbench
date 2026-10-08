from __future__ import annotations

"""Load the framework pin before pytest imports instance test modules."""

from framework_bootstrap import load_framework

FRAMEWORK_ROOT = load_framework()
