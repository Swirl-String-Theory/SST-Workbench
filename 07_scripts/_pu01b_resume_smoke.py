"""PU01b mid-chain resume smoke (A038-shaped stages)."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))
from paper_upgrade_runtime import finish_run, init_run, run_stage  # noqa: E402

out = WB / "01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/A038-v0.4.0/_pu01b_smoke_out"
if out.exists():
    shutil.rmtree(out)
os.environ["SST_HEARTBEAT_SEC"] = "0.2"
os.environ.pop("SST_RESUME", None)

init_run(family="A038", tier="basic", out=out, resume=False)
assert run_stage(
    family="A038",
    tier="basic",
    out=out,
    stage_id="10_prepare",
    argv=[sys.executable, "-c", "print(10)"],
    heartbeat_sec=0.2,
) == 0
assert run_stage(
    family="A038",
    tier="basic",
    out=out,
    stage_id="20_early",
    argv=[sys.executable, "-c", "print(20)"],
    heartbeat_sec=0.2,
) == 0
assert (out / "stages" / "10_prepare.done").is_file()
assert (out / "stages" / "20_early.done").is_file()

os.environ["SST_RESUME"] = "1"
init_run(family="A038", tier="basic", out=out, resume=True)
assert (
    run_stage(
        family="A038",
        tier="basic",
        out=out,
        stage_id="10_prepare",
        argv=[sys.executable, "-c", "raise SystemExit('no')"],
        resume=True,
    )
    == 0
)
assert (
    run_stage(
        family="A038",
        tier="basic",
        out=out,
        stage_id="20_early",
        argv=[sys.executable, "-c", "raise SystemExit('no')"],
        resume=True,
    )
    == 0
)
assert (
    run_stage(
        family="A038",
        tier="basic",
        out=out,
        stage_id="40_long",
        argv=[sys.executable, "-c", "print(40)"],
        resume=True,
        heartbeat_sec=0.2,
    )
    == 0
)
finish_run(family="A038", tier="basic", out=out, status="DONE")
hb = (out / "heartbeat.log").read_text(encoding="utf-8")
assert hb.count("event=SKIP") >= 2
assert "stage=40_long" in hb and "event=DONE" in hb
print("SMOKE_OK")
print(hb)
