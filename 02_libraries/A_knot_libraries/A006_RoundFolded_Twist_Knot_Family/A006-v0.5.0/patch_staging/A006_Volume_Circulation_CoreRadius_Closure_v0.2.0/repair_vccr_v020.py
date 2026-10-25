r"""Safe recovery installer for A006 VCCR v0.2.0.

Archives existing v0.2.0 sidecar and wrapper with unique suffix, leaving
A006-v0.5.0 and any older VCCR versions untouched. Does not delete files.
Run from the extracted v0.2.0 package:
  py -3 repair_vccr_v020.py --base "C:\...\A006-v0.5.0" --check
  py -3 repair_vccr_v020.py --base "C:\...\A006-v0.5.0" --apply
"""
import argparse
from datetime import datetime
from pathlib import Path
import sys
from install_sidecar import install


def backup_target(original: Path, suffix: str):
    stem = original.name if original.is_dir() else original.stem
    extension = "" if original.is_dir() else original.suffix
    for ix in range(1000):
        proposed = original.with_name(f'{stem}_{suffix}' + (f'_{ix}' if ix else '') + extension)
        if not proposed.exists():
            return proposed
    raise RuntimeError('No available backup name: ' + str(original))


def execute(base: Path, apply: bool):
    base = base.resolve()
    if not (base/'run_all.cmd').is_file() or not (base/'knotplotrc.kps').is_file():
        raise RuntimeError('Not the A006-v0.5.0 root (missing run_all.cmd / knotplotrc.kps): ' + str(base))
    sidecar = base/'tools'/'VCCR_v0.2.0'
    wrapper = base/'run_vccr_v020.cmd'
    if (sidecar.exists() and (not sidecar.is_dir() or sidecar.is_symlink())) or (wrapper.exists() and (not wrapper.is_file() or wrapper.is_symlink())):
        raise RuntimeError('Unexpected symlink/file type in installation path; manual review required')
    try:
        install(base, False)
    except RuntimeError as exc:
        msg = str(exc)
        if ('EXISTING MODIFIED FILE' not in msg and 'Existing run_vccr_v020.cmd differs' not in msg):
            raise
    else:
        print('No conflicting VCCR files; use ordinary create-only installation.')
        if apply:
            install(base,True)
        return

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_sidecar = backup_target(sidecar, f'backup_{stamp}') if sidecar.exists() else None
    backup_wrapper = backup_target(wrapper, f'backup_{stamp}') if wrapper.exists() else None
    print('CONFLICT DETECTED: preserving the entire existing VCCR v0.2.0 install.')
    if backup_sidecar: print('  Sidecar: ' + str(sidecar) + '\n    -> ' + str(backup_sidecar))
    if backup_wrapper: print('  Launcher: ' + str(wrapper) + '\n    -> ' + str(backup_wrapper))
    if not apply:
        print('REPAIR CHECK PASS: no filesystem changes made. Run again with --apply.')
        return
    moved=[]
    try:
        for old,new in [(sidecar,backup_sidecar),(wrapper,backup_wrapper)]:
            if new is not None:
                old.rename(new)
                moved.append((old,new))
        install(base,False)
        install(base,True)
        print('REPAIR INSTALLED; previous sidecar/launcher safely archived.')
        print('NEXT: from the A006 base: run_vccr_v020.cmd TEST')
    except Exception:
        # Preserve any new files rather than deleting them; restore originals.
        failed_stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        for newly_created in [wrapper,sidecar]:
            if newly_created.exists():
                failed = backup_target(newly_created,f'failed_repair_{failed_stamp}')
                newly_created.rename(failed)
                print('Retained incomplete repair at: ' + str(failed),file=sys.stderr)
        for old,backup in reversed(moved):
            backup.rename(old)
        print('Original installed files restored; repair failed.',file=sys.stderr)
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check',action='store_true')
    mode.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    try:execute(Path(args.base),args.apply)
    except Exception as exc:
        print('REPAIR REFUSED: ' + str(exc),file=sys.stderr)
        sys.exit(2)
