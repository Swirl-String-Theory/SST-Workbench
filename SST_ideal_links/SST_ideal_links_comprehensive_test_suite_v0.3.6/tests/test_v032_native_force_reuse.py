import sys
from sst_link_suite.native_ext import core

class Dummy:
    @staticmethod
    def build_info(): return {"dummy": True}

def test_loaded_native_module_is_reused_without_rebuild(monkeypatch):
    name=f"{core._config.PACKAGE_NAME}.{core._config.EXT_BASENAME}"
    dummy=Dummy()
    monkeypatch.setitem(sys.modules,name,dummy)
    monkeypatch.setattr(core,"build_if_needed",lambda **kwargs: (_ for _ in ()).throw(AssertionError("must not rebuild")))
    assert core._import_native(True,False,False) is dummy
