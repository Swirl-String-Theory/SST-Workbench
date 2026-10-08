from __future__ import annotations

"""Package-safe Python launcher for a generated falsifier instance.

Supports the intended helper forms ``-m module``, ``-c code`` and direct script paths.
The instance root and the authoritative shared-framework pin are established before the
requested code executes.
"""

from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from framework_bootstrap import load_framework

FRAMEWORK_ROOT = load_framework()
# Instance-local packages take precedence over unrelated site-packages; the framework
# itself remains pinned because load_framework has already imported it from FRAMEWORK_ROOT.
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))


def main(argv: list[str]) -> int:
    if not argv:
        print("Usage: run_python.cmd -m package.module [args] | run_python.cmd script.py [args] | run_python.cmd -c code [args]", file=sys.stderr)
        return 2
    head=argv[0]
    if head=="-m":
        if len(argv)<2:
            print("run_python: -m requires a module name", file=sys.stderr); return 2
        module=argv[1]; sys.argv=[module,*argv[2:]]
        runpy.run_module(module,run_name="__main__",alter_sys=True); return 0
    if head=="-c":
        if len(argv)<2:
            print("run_python: -c requires code", file=sys.stderr); return 2
        sys.argv=["-c",*argv[2:]]
        ns={"__name__":"__main__","__file__":"<run_python -c>","__package__":None}
        exec(compile(argv[1],"<run_python -c>","exec"),ns,ns); return 0
    if head.startswith("-"):
        print(f"run_python: unsupported interpreter option {head!r}; use -m, -c, or a script path", file=sys.stderr)
        return 2
    script=Path(head)
    if not script.is_absolute(): script=ROOT/script
    if not script.is_file():
        print(f"run_python: script not found: {script}", file=sys.stderr); return 2
    sys.argv=[str(script),*argv[1:]]
    runpy.run_path(str(script),run_name="__main__"); return 0


if __name__=="__main__":
    raise SystemExit(main(sys.argv[1:]))
