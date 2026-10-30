from pathlib import Path
import subprocess,sys
if __name__=='__main__':
 raise SystemExit(subprocess.call(['cmd.exe','/d','/c',str(Path(__file__).with_name('run_all.cmd')),*sys.argv[1:]],cwd=Path(__file__).parent))
