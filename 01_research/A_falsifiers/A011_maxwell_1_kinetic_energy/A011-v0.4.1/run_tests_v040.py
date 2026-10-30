from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from maxwell_sst_falsifier.framework_v110 import qualified_framework, select_native
qualified_framework()
select_native()
import pytest

if __name__ == '__main__':
    raise SystemExit(pytest.main(['-p', 'no:cacheprovider', '-q', '-rA', str(ROOT / 'tests')]))
