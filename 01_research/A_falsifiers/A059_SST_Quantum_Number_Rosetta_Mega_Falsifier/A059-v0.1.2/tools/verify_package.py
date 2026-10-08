from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from mega.common import verify_source_archive,implementation_verify
from framework_bootstrap import verify_bundled_framework

def main():
    result={'framework':verify_bundled_framework(),'source':verify_source_archive(ROOT),'implementation':implementation_verify(ROOT)}
    ok=all(x.get('pass') for x in result.values())
    print(json.dumps({'overall_pass':ok,**result},indent=2))
    return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
