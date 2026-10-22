A058 v0.3.6 input bundle hotfix for existing v0.3.5 setup.
Unzip OVER existing A058 root, keeping the original project folder and .lnk unchanged.
No existing A058_probes data is altered. For a new output directory run:
  run_all.cmd RUN_SAFE_PROBES --exe ".\KnotPlot.lnk" --dist ".\kpdist-23mar2025.zip" --out ".\A058_probes_NEW" --timeout 120
Run CHECK_PROBES --out <OLD_DIR> to inspect incomplete old evidence.
Native KnotPlot 2026 NOT RUN in release environment.
