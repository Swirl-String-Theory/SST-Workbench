"""Stage Framework v1.1.0's unchanged instance-template SYCL worker.

Framework sycl_worker._src(root) intentionally resolves root/native/cpp/sycl_worker.cpp.
This is an instance-level path; passing the FRAMEWORK root to probe_worker was wrong.
Never overwrite a differing local native source or modify framework shared files.
"""
from __future__ import annotations
import hashlib
import shutil
from pathlib import Path


def _sha256(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def stage_template_worker(framework_root, instance_root)->dict:
    framework=Path(framework_root).resolve()
    instance=Path(instance_root).resolve()
    template=framework/'instance_template'/'native'/'cpp'/'sycl_worker.cpp'
    target=instance/'native'/'cpp'/'sycl_worker.cpp'
    if not template.is_file():
        return {'success':False,'reason':f'MISSING_TEMPLATE_SYCL_SOURCE: {template}',
                'required_source':str(template),'destination':str(target)}
    original=_sha256(template)
    if target.exists() and _sha256(target)!=original:
        return {'success':False,'reason':'LOCAL_SYCL_SOURCE_DIFFERS: refusal to overwrite; inspect native/cpp/sycl_worker.cpp',
                'template_sha256':original,'local_sha256':_sha256(target)}
    existed=target.exists()
    if not existed:
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(template,target)
    if _sha256(target)!=original:
        raise RuntimeError('SOURCE_COPY_INTEGRITY_FAILURE')
    return {'success':True,'source':str(template),'instance_source':str(target),
            'sha256':original,'stage_status':'VERIFIED_EXISTING' if existed else 'COPIED_AND_VERIFIED',
            'framework_untouched':True,'builder_root':str(instance),
            'note':'SYCL worker Biot-Savart diagnostic only, not the A075 Fourier-Euler GPU implementation'}
