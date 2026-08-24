# Imported VortexLab excerpts

This folder contains a **real diagnostic excerpt** recovered from a VortexLab session shared in an earlier ChatGPT conversation:

- `vortexlab-session-7-6-24b-20260716_095112796Z.txt`
- excerpted diagnostic interval: `tPhys = 1.0 ... 8.5`
- source records contain `Wr`, `Lk`, `ACN`, `RA`, `zA`, `topologyGap`, stretch diagnostics and the SST `scaleProbe`.

Important: this is scalar diagnostic data, **not** a full `xyz(s,t)` centerline trajectory and not a `(k, omega)` spectrum. Therefore v0.2.1 keeps it as `diagnostic_only`; it cannot by itself establish a propagation speed in m/s.

The raw Library file could not be copied byte-for-byte into the build environment when this package was assembled. If you have the original `.txt` locally, simply copy it anywhere below `campaigns\`; the recursive scanner will parse the complete file automatically.
