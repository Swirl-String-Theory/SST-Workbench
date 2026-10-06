from pathlib import Path
import argparse,zipfile
p=argparse.ArgumentParser(); p.add_argument('--output-dir',required=True); p.add_argument('--dest-prefix',required=True); a=p.parse_args()
out=Path(a.output_dir); dest=Path(a.dest_prefix)
for suffix,include_reveal in [('_BLIND.zip',False),('_REVEALED.zip',True),('.zip',True)]:
    zpath=Path(str(dest)+suffix); zpath.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.rglob('*')):
            if not f.is_file(): continue
            rel=f.relative_to(out)
            if not include_reveal and ('reveal' in rel.parts or rel.name.startswith('REVEAL')): continue
            z.write(f,rel.as_posix())
    print(zpath)
