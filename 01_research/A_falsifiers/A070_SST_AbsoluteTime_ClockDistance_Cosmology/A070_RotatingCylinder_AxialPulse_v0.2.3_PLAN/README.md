# A070 — Rotating Cylinder Axial Pulse, v0.2.3 PLAN

Status **DEVELOPMENT / OBSERVATIONAL AUDIT / NOT BLIND-CERTIFIED / NOT PHYSICAL SST VALIDATION**.

This is a non-destructive follow-up to frozen `A070 v0.2.2` and an analysis of the user's 240-fps water video. The existing blinded dataset and lock files are **not** changed, nor are they copied and re-labeled.

Input video (not bundled because 164 MB): `20260625_020642_1.mp4`, SHA-256 recorded in `results/video_audit.json`. Real recording time is computed from *240 raw captured frames per second* **assuming** 1:1 video frame retention. Stored video playback fps near 29.97. Video at 12 s playback means ~1.5 s recorded; the timestamp relative to rotor actuation is unknown.

## Re-run

```bash
pip install -r requirements.txt
python src/video_audit.py --video ../20260625_020642_1.mp4 --output results
python -m unittest discover -s tests -v
```

If the file sits elsewhere, supply its actual path. The program does not automatically output wave speed: the video lacks an independently established wavefront, temporal actuation reference, and depth calibration. The brightness kymograph measures image contrast, not speed, pressure or vorticity.

## Source identity and scope

- Cylinder D=0.15 m, physical cylinder H=0.30 m, **water depth not measured**.
- Approximately 14 s slowed playback per cylinder revolution, motor around <=33 rpm. Mean background rate is not independently measured.
- The water experiment is viscous; SST source fluid is incompressible and inviscid. This film cannot establish an inviscid torsional photon mode.
- Never reuse this known clip as a truly blinded held-out physical validation set.

See `REPORT.pdf` and `preregistration/SCIENCE_CONTRACT.json` for the preregistered *proposed* next physical falsifier design.
