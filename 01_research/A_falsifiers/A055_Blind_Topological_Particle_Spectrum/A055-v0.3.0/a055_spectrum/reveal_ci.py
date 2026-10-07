from pathlib import Path
from .reveal import run_reveal
from .util import load_json
def main():
    root=Path(__file__).resolve().parents[1]
    cfg=load_json(root/"configs"/"ci.json")
    run_reveal(root,root/cfg["output_dir"])
if __name__=="__main__": main()
