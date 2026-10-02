from pathlib import Path
from run_matrix_batch import resolve_shortcut, DEFAULT_SHORTCUT
from knotplot_runtime import runtime_info, find_basic_dirs, find_catalogue_file, candidate_load_strategies

root=Path(__file__).resolve().parent
exe,wd=resolve_shortcut(DEFAULT_SHORTCUT.resolve())
rc,text=runtime_info(exe,wd,root/"preflight")
basics=find_basic_dirs(exe,wd,text)
print("KnotPlot runtime diagnostic")
print("="*72)
print("Executable :",exe)
print("Shortcut CWD:",wd)
print("runtime-info exit:",rc)
print("basic dirs:")
for p in basics: print("  ",p)
seed=find_catalogue_file("3.1",basics)
print("3.1 seed:",seed if seed else "NOT FOUND")
if seed:
    print("candidate load strategies:")
    for s in candidate_load_strategies(wd,seed.parent):
        print(f"  {s.name:22s} cwd={s.process_cwd} prefix={s.prefix.strip()!r} load={s.load_line('3.1')}")
print("runtime log:",root/"preflight"/"00_runtime_info.log")
raise SystemExit(0 if seed else 2)
