from pathlib import Path
from kpc_audit import script_issues, log_issues

def test_legacy_relax_syntax_rejected(tmp_path):
    p=tmp_path/'x.kpc'; p.write_text('charge = 15\n'); assert any('charge' in x for x in script_issues(p))
def test_target_obsolete_nbeads_rejected(tmp_path):
    p=tmp_path/'x.kpc'; p.write_text('nbeads 300\n'); assert any('obsolete' in x for x in script_issues(p))
def test_unknown_command_log_fails(): assert 'unknown command' in log_issues("*** unknown command: `charge'")
