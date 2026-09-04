from sst_seed_falsifier import __version__
from sst_seed_falsifier.release import release_identity

def test_release_identity_matches_runtime():
    r=release_identity(); assert r['match']; assert r['declared_version']==__version__=='0.3.0'
