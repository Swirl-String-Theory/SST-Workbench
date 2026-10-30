"""Integrity-locked Framework v1.1.0 reference template preflight.
This is NOT an official falsifier FREEZE or scientific CERTIFY.
"""
import hashlib,json,sys
from pathlib import Path
from framework_bootstrap import load_framework,resolve_framework_root

def main():
    root=load_framework();info=json.loads((root/'RUNTIME_SNAPSHOT_MANIFEST.json').read_text())
    n=len(info['files']);assert n==142 and info['file_count']==142
    from sst_falsifier.dd32_reference import DS, add, mul
    a=DS.from_double(.1234567890123);b=DS.from_double(.987654321987)
    err_add=abs(add(a,b).value()-(.1234567890123+.987654321987))
    err_mul=abs(mul(a,b).value()-(.1234567890123*.987654321987))
    print(json.dumps({'schema':'SST-EULER-FRAMEWORK-INTEGRITY-1','runtime_version':info['version'],
          'verified_source_files':n,'integrity_status':'PASS','template_root':str(root/'instance_template'),
          'dd32_scalar_reference_regression_errors':{'addition':err_add,'multiplication':err_mul},
          'framework_falsifier_CERTIFY':'NOT_EXECUTED','GPU_Euler_DD32_qualification':'NOT_IMPLEMENTED'},indent=2))
if __name__=='__main__':main()
