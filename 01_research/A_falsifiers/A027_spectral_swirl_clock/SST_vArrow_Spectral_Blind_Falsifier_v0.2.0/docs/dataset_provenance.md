# Dataset provenance note — v0.2.0

During assembly, earlier ChatGPT Library searches located multiple VortexLab session logs, including:

- `vortexlab-session-7-6-24b-20260716_095112796Z.txt`
- `vortexlab-session-7-6-24f-20260716_184352596Z.txt`
- `vortexlab-session-7-6-21.txt`
- `vortexlab-session-7-6-10.txt`
- `vortexlab-session-7-6-12.txt`

The 24b log contains scalar `type=diag` time records and a proxy-decomposition plan with resolution-ladder and holdout scenarios. The 24f log contains a much longer physical-time run.

Raw-byte materialization of those prior Library files was not authorized in the package-build environment. Therefore this archive does **not** pretend to contain complete originals. It contains:

1. an exact scalar diagnostic excerpt transcribed from the accessible 24b parsed source;
2. a recursive parser that will ingest the full original `.txt` files when you place them anywhere under `campaigns/` locally;
3. strict quarantine of scalar-only logs from the primary speed estimator.

This preserves the blind test: missing spatial information is reported as missing rather than synthesized.
