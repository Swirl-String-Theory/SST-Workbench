GPE GPU v0.1.0 - Windows batch hotfix v0.1.1

Root cause: an unescaped close parenthesis inside a parenthesized IF block
causes cmd.exe to print `. was unexpected at this time.`

Install:
  1. Back up the instance run_all.cmd.
  2. Overwrite ONLY the following instance file with this run_all.cmd:
     C:\workspace\projects\SST-Workbench\01_research\F_exploratory\GPE_EXT_001_GPE_GPU_Benchmark_v0.1.0\run_all.cmd
  3. In that directory, execute: run_all.cmd BASIC
  4. Later run: run_all.cmd FULL

DO NOT overwrite the framework's own run_all.cmd in 06_templates.
DO NOT modify a frozen protocol in place. If preregistration\FROZEN_PROTOCOL.json
already exists, first create a versioned new instance and refreeze it instead.

Scope of change: only ONE echo line changed, no solver or science contracts altered.
Windows execution still needs to be validated on your Intel Arc machine.
