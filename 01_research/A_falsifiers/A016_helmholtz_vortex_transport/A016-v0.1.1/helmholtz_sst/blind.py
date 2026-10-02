from __future__ import annotations
import hashlib

def blind_id(file_sha256,salt):return hashlib.sha256((salt+':'+file_sha256).encode()).hexdigest()[:16]

def gate(name,passed,metrics=None,note=''):
    return {'gate':name,'status':'PASS' if passed else 'FAIL','metrics':metrics or {},'note':note}
