from pathlib import Path
from sst_falsifier.native_build import _compiler_from_build_log,_compiler_family,_toolset_from_path,_python_abi


def test_msvc_actual_compiler_wins_over_path_cxx():
    log='"C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Tools\\MSVC\\14.44.35207\\bin\\HostX86\\x64\\cl.exe" /c /nologo /O2 /W3 source.cpp\n'
    got=_compiler_from_build_log(log)
    # On non-Windows test hosts the path need not exist; parser must still retain it.
    assert got and got.lower().endswith('cl.exe')
    assert _compiler_family(got)=='msvc'
    assert _toolset_from_path(got)=='14.44.35207'


def test_python_abi_nonempty():
    assert '-' in _python_abi()
