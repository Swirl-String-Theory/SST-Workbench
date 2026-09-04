@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
"%PY%" -c "from pathlib import Path; import zipfile; r=Path('.').resolve(); z=r.parent/(r.name+'.zip'); f=[p for p in r.rglob('*') if p.is_file() and not any(q in p.parts for q in ('.venv','build','__pycache__','.pytest_cache')) and not p.name.endswith('.pyd')]; w=zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED); [w.write(p,(Path(r.name)/p.relative_to(r)).as_posix()) for p in f]; w.close(); print(z)"
