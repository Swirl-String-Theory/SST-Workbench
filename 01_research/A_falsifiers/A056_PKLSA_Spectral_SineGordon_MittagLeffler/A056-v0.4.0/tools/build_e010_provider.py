from __future__ import annotations

from pathlib import Path
import sys

# When Python executes ``tools\build_e010_provider.py`` directly, sys.path[0]
# is the tools directory rather than the falsifier root.  Bootstrap the instance
# root explicitly before importing instance-local packages.  This keeps the tool
# usable both as a script and through ``python -m a056_provider.campaign``.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from a056_provider.campaign import main  # noqa: E402


if __name__ == "__main__":
    main()
