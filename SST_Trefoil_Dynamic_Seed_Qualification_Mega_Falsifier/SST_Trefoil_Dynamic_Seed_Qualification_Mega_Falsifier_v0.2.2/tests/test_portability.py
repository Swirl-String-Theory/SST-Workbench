from pathlib import Path

def test_msvc_ssize_guard():
    s=Path('cpp/native.cpp').read_text(encoding='utf-8'); assert 'py::ssize_t' in s; assert 'const ssize_t' not in s
