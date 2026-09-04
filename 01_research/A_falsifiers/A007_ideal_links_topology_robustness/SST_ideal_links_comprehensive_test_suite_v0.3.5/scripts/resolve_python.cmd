@echo off
rem Resolve the project/Workbench virtualenv without invoking PowerShell.
rem Search the suite directory first, then parent directories.
set "PYTHON="
if exist ".venv\Scripts\python.exe" set "PYTHON=%CD%\.venv\Scripts\python.exe"
if not defined PYTHON if exist "..\.venv\Scripts\python.exe" set "PYTHON=%CD%\..\.venv\Scripts\python.exe"
if not defined PYTHON if exist "..\..\.venv\Scripts\python.exe" set "PYTHON=%CD%\..\..\.venv\Scripts\python.exe"
if not defined PYTHON if exist "..\..\..\.venv\Scripts\python.exe" set "PYTHON=%CD%\..\..\..\.venv\Scripts\python.exe"
if not defined PYTHON if exist "..\..\..\..\.venv\Scripts\python.exe" set "PYTHON=%CD%\..\..\..\..\.venv\Scripts\python.exe"
if not defined PYTHON set "PYTHON=python"
