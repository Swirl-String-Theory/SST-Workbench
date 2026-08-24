# Prior VortexLab sources located in the ChatGPT Library

The following earlier-session files were found while preparing v0.2.1:

- `vortexlab-session-7-6-24b-20260716_095112796Z.txt`
- `vortexlab-session-7-6-24f-20260716_184352596Z.txt`
- `vortexlab-session-7-6-21.txt`
- `vortexlab-session-7-6-10.txt`
- `vortexlab-session-7-6-12.txt`

The recursive scanner recognizes VortexLab log lines of the form

`... tPhys=<...> type=diag detail={...}`

and exports them to `outputs_*\campaign_scan\diagnostics\` for QC. Such scalar logs remain diagnostic-only unless they also contain or are accompanied by a full spatial trajectory or an explicit k-resolved spectrum.
