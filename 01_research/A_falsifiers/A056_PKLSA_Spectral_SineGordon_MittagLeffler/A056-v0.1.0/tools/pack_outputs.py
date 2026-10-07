from pathlib import Path
import argparse,zipfile,hashlib
p=argparse.ArgumentParser(); p.add_argument('output_dir'); p.add_argument('--prefix',required=True); a=p.parse_args(); root=Path(a.output_dir)
def pack(dst,sub=None):
    with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as z:
        base=root/sub if sub else root
        for f in sorted(base.rglob('*')):
            if f.is_file(): z.write(f,f.relative_to(root.parent))
    h=hashlib.sha256(Path(dst).read_bytes()).hexdigest(); Path(str(dst)+'.sha256').write_text(h+'  '+Path(dst).name+'\n')
pack(Path('..')/(a.prefix+'-outputs_BLIND.zip'),'BLIND')
if (root/'REVEALED').exists(): pack(Path('..')/(a.prefix+'-outputs_REVEALED.zip'),'REVEALED')
pack(Path('..')/(a.prefix+'-outputs.zip'),None)
