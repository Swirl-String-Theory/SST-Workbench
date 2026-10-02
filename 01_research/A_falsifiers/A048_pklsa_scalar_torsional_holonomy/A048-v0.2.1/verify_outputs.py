"""Verify a safely extracted run or scope-specific ZIP directory."""
import argparse,json
from pathlib import Path
from sst_torsion.run_contract import verify_seal,verify_reveal


def main():
    p=argparse.ArgumentParser()
    p.add_argument('directory',type=Path)
    p.add_argument('--scope',choices=['full','blind','revealed'],default='full')
    a=p.parse_args()
    if a.scope in ('full','blind'):
        verify_seal(a.directory,require_private_key=a.scope=='full')
    if a.scope in ('full','revealed'):
        verify_reveal(a.directory)
    print(json.dumps({'scope':a.scope,'status':'PASS',
        'meaning':'Inventory and retained hash commitments verified; not an external signature or a physics certificate.',
        'private_label_key_checked':a.scope=='full'}))


if __name__=='__main__':
    main()
