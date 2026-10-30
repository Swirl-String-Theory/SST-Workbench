"""Persistent create-exclusive run guard for this chat's daily local control task.

The lock persists across short shell invocations. There is no automatic expiry or
PID-based reclamation: an unresolved interrupted run must be inspected explicitly.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import uuid

DEFAULT_STATE = Path(__file__).resolve().parents[2] / '10_docs/migration_v110/scheduled_control'


def acquire(state, owner='sst-workbench-dagelijkse-migratiecontrole'):
    state.mkdir(parents=True, exist_ok=True)
    path = state / 'run.lock'
    record = {'owner': owner, 'token': uuid.uuid4().hex, 'started_utc': datetime.now(timezone.utc).isoformat(),
              'policy': 'No automatic expiry; release only after this execution finishes'}
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        payload = (json.dumps(record, indent=2) + '\n').encode()
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        # A partial file remains deliberately fail-closed for manual inspection.
        raise
    return record


def release(state, token):
    path = state / 'run.lock'
    record = json.loads(path.read_text(encoding='utf-8'))
    if not token or record['token'] != token:
        raise PermissionError('Only the recorded run owner may release this lock')
    path.unlink()
    return {'released': True, 'owner': record['owner']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['acquire', 'release', 'status'])
    p.add_argument('--state', type=Path, default=DEFAULT_STATE)
    p.add_argument('--token')
    args = p.parse_args()
    if args.command == 'acquire':
        try:
            result = acquire(args.state)
        except FileExistsError:
            print(json.dumps({'status': 'SKIPPED_BUSY', 'lock': str(args.state / 'run.lock')}))
            raise SystemExit(3)
    elif args.command == 'release':
        result = release(args.state, args.token)
    else:
        result = {'locked': (args.state / 'run.lock').exists()}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
