#!/usr/bin/env python3
"""Small self-contained installer regression: file safety, upgrade, repeat, rollback."""
from __future__ import annotations
import hashlib, json, tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from install_patch import validate, apply, rollback


def checksum(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def make_root(root, *, beadlimit):
    (root/'src').mkdir(); (root/'tools').mkdir(); (root/'extensions/borromean/whole').mkdir(parents=True)
    (root/'src/build_v040.py').write_text('')
    (root/'extensions/borromean/whole/build_whole.py').write_text('')
    (root/'SEED_MANIFEST.json').write_text(json.dumps({'version':'0.4.0','knots':[{}]*13}))
    (root/'tools/selection_v043.py').write_text('go beadlimit 4000\n' if beadlimit else 'legacy selection\n')
    (root/'tools/analysis_v043.py').write_text('legacy analysis\n')
    (root/'run_all.cmd').write_bytes((
      '@echo off\r\nrem A006_SELECT_DISPATCH_v043 BEGIN\r\n'
      'goto A006_SELECT_DISPATCH_v043\r\n'
      ':A006_SELECT_DISPATCH_v043\r\n'
      'py -3 "%~dp0tools\\selection_v043.py" %*\r\n'
      'exit /b %errorlevel%\r\n').encode('ascii'))


def test_variant(beadlimit):
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);make_root(root,beadlimit=beadlimit)
        originals={r:checksum(root/r) for r in ['tools/selection_v043.py','tools/analysis_v043.py']}
        before=(root/'run_all.cmd').read_bytes()
        assert validate(root)['existing_selector_has_beadlimit']==beadlimit
        receipt=apply(root);assert receipt['status']=='INSTALLED'
        cmd=(root/'run_all.cmd').read_bytes()
        assert cmd.replace(b'selection_v043b.py',b'selection_v043.py')==before
        assert all(checksum(root/r)==digest for r,digest in originals.items())
        assert all((root/r).exists() for r in ('tools/selection_v043b.py','tools/orientation_v043b.py','tools/analysis_v043b.py'))
        try:apply(root)
        except RuntimeError:pass
        else:raise AssertionError('Repeat install accepted')
        result=rollback(root);assert result['status']=='ROLLED_BACK'
        assert (root/'run_all.cmd').read_bytes()==before
        assert all(checksum(root/r)==digest for r,digest in originals.items())

if __name__=='__main__':
    test_variant(False);test_variant(True)
    print('PASS: v0.4.3 and v0.4.3a upgrade, no overwrite, duplicate refusal and rollback')
