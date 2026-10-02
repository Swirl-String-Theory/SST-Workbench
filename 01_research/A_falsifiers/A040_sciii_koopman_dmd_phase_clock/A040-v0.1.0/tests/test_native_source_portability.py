import re
from pathlib import Path
def test_no_unqualified_ssize_t():
 s=(Path(__file__).parents[1]/'cpp/native.cpp').read_text(); assert not re.findall(r'(?<![:\w])ssize_t\b',s)
def test_uses_py_ssize_t():
 s=(Path(__file__).parents[1]/'cpp/native.cpp').read_text(); assert 'py::ssize_t' in s
