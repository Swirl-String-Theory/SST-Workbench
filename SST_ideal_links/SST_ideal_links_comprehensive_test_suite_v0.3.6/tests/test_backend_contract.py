import pytest
from sst_link_suite.native_ext import BackendOptions, NativeBackendError, resolve_backend


def test_mutually_exclusive_backend_flags():
    with pytest.raises(NativeBackendError):
        resolve_backend(BackendOptions(require_native=True, force_python=True))
