from pathlib import Path
import json,sys,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from mega.common import verify_source_archive,implementation_verify,EXPECTED_FRAMEWORK_ARCHIVE_SHA256,sha256_file
from framework_bootstrap import load_framework

def main():
    src=verify_source_archive(ROOT);impl=implementation_verify(ROOT)
    fwzip=ROOT/'inputs'/'SST_Falsifier_Framework_v1.0.6-CANONICAL_FROZEN.zip'
    fw_archive_ok=fwzip.is_file() and sha256_file(fwzip)==EXPECTED_FRAMEWORK_ARCHIVE_SHA256
    fw=load_framework()
    ok=src['pass'] and impl['pass'] and fw_archive_ok and fw.name=='SST_Falsifier_Framework_v1.0.6'
    print(json.dumps({'overall_pass':ok,'source':src,'implementation':impl,'framework_root':str(fw),'framework_reference_archive_ok':fw_archive_ok},indent=2))
    return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
