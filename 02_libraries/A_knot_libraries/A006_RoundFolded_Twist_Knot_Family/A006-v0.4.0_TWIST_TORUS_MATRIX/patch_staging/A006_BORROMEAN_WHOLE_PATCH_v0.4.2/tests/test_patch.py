import tempfile,shutil,subprocess,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]

def check_fixture(base):
    # A valid pre-patched 0.4.0 fixture must be provided as --base.
    with tempfile.TemporaryDirectory() as temp:
        test=Path(temp)/'A006'
        for rel in ('run_all.cmd','SEED_MANIFEST.json'):
            (test/rel).parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(base/rel,test/rel)
        dest=test/'extensions/borromean'
        dest.mkdir(parents=True)
        for rel in ('build_borromean.py','run_borromean.cmd','PATCH_RECEIPT.json'):
            src=base/'extensions/borromean'/rel
            if rel=='run_borromean.cmd' and b'A006_BORROMEAN_WHOLE_V042' in src.read_bytes():
                src=base/'patch_backups/A006_BORROMEAN_v0.4.2/run_borromean.cmd.before'
            shutil.copy2(src,dest/rel)
        proc=subprocess.run([sys.executable,str(P/'install_patch.py'),'--base',str(test),'--check'],capture_output=True,text=True)
        assert proc.returncode==0,proc.stderr+proc.stdout
        orig=(test/'run_all.cmd').read_bytes()
        proc=subprocess.run([sys.executable,str(P/'install_patch.py'),'--base',str(test),'--apply'],capture_output=True,text=True)
        assert proc.returncode==0,proc.stderr+proc.stdout
        assert (test/'run_all.cmd').read_bytes()==orig
        assert (test/'extensions/borromean/whole/build_whole.py').is_file()
        proc=subprocess.run([sys.executable,str(P/'install_patch.py'),'--base',str(test),'--apply'],capture_output=True,text=True)
        assert proc.returncode!=0
        assert (test/'run_all.cmd').read_bytes()==orig
        print('PASS installer check, apply, idempotence fail-closed, run_all untouched')

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--base',required=True,type=Path);args=a.parse_args()
    check_fixture(args.base)
