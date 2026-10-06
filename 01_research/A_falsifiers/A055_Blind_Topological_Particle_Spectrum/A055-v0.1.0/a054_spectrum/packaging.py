from pathlib import Path
import zipfile
from .util import sha256_file

def zip_tree(base: Path, zip_path: Path, include):
    if zip_path.exists(): zip_path.unlink()
    with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(base.rglob("*")):
            if p.is_file() and include(p):
                z.write(p,p.relative_to(base))
    zip_path.with_suffix(zip_path.suffix+".sha256").write_text(sha256_file(zip_path)+"  "+zip_path.name+"\n",encoding="ascii")
    return zip_path

def package_outputs(out: Path):
    archive_dir=out.parent.parent
    blind_zip=archive_dir/(out.name+"_BLIND.zip")
    revealed_zip=archive_dir/(out.name+"_REVEALED.zip")
    combined_zip=archive_dir/(out.name+".zip")
    zip_tree(out,blind_zip,lambda p: p.parts[-2]!="PRIVATE_REVEAL_DO_NOT_INCLUDE_IN_BLIND" and "PRIVATE_REVEAL_DO_NOT_INCLUDE_IN_BLIND" not in p.parts and "REVEALED" not in p.parts)
    zip_tree(out,revealed_zip,lambda p: "PRIVATE_REVEAL_DO_NOT_INCLUDE_IN_BLIND" not in p.parts)
    zip_tree(out,combined_zip,lambda p: True)
    return blind_zip,revealed_zip,combined_zip
