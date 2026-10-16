# Runtime campaign directory

This source release intentionally contains no pre-generated machine-bound KnotPlot campaign scripts.

Run `run_10_prepare_campaign.cmd smoke|pilot|full` on the target Windows workstation **before FREEZE**. Generated `.kpc` scripts contain absolute result paths for that frozen instance. KnotPlot execution then writes `results/`, `logs/`, `runtime_<tier>.json`, and `runlog_<tier>.json` here after freeze.
