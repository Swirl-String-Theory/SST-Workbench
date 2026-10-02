from pathlib import Path
import re

def test_no_global_ssize_t_for_msvc():
    s=Path('cpp/native.cpp').read_text(encoding='utf-8')
    stripped=re.sub(r'py::ssize_t','',s)
    assert not re.search(r'(?<![\w:])ssize_t\b',stripped), 'Use py::ssize_t; global ssize_t breaks MSVC.'
