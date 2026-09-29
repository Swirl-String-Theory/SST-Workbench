@echo off
if not exist .venv (py -3 -m venv .venv)
.venv\Scripts\python.exe -m pip install -q --upgrade pip setuptools wheel
.venv\Scripts\python.exe -m pip install -q -e .
