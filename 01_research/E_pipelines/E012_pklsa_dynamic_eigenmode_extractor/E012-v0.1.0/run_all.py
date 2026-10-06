from __future__ import annotations
import argparse
from pathlib import Path
from e012_dynamic.pipeline import run

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--workbench-root",default=None)
    p.add_argument("--preset",choices=["quick","full"],default="quick")
    p.add_argument("--force-python",action="store_true")
    p.add_argument("--physical-scale",default=None)
    a=p.parse_args()
    result=run(Path(__file__).resolve().parent,
               workbench_root=a.workbench_root,
               preset=a.preset,
               force_python=a.force_python,
               physical_scale_path=Path(a.physical_scale) if a.physical_scale else None)
    print(result)

if __name__=="__main__":
    main()
