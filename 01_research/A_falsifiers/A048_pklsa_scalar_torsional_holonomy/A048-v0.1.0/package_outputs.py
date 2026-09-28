from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parent
NAME='A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.1.0-outputs'
OUT=ROOT.parent/NAME

def zip_tree(path,dst,arcroot=None):
    with zipfile.ZipFile(dst,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(path.rglob('*')):
            if p.is_file():
                arc=(Path(arcroot)/p.relative_to(path)) if arcroot else p.relative_to(path)
                z.write(p,arc.as_posix())
if __name__=='__main__':
    zip_tree(OUT/'BLIND',ROOT.parent/f'{NAME}_BLIND.zip','BLIND')
    zip_tree(OUT/'REVEALED',ROOT.parent/f'{NAME}_REVEALED.zip','REVEALED')
    zip_tree(OUT,ROOT.parent/f'{NAME}.zip',NAME)
    print('packaged outputs')
