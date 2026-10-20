# Installation and framework pin

This is NOT the framework archive; user must install exact `SST_Falsifier_Framework_v1.0.7` separately and keep it frozen under `SST-Workbench/06_templates/SST_Falsifier_Framework/`. The `.sst_framework_root` file pins that exact folder relative to instance path.

Before placing under Workbench, check the active authoritative catalog and assign A069 only if unoccupied.

For standalone analytic tests without framework: `python -m pip install -r requirements.txt`, `python -m unittest discover -s tests -v`, `python -m experiment.standalone`.

Official framework (only from the canonical Workbench instance folder and after source/contract review): `run_all.cmd FREEZE`, `run_all.cmd BASIC`, `run_all.cmd FULL`, `run_all.cmd CERTIFY`, `run_all.cmd REVEAL_IF_ALLOWED`. D2/D3 physical gates are unresolved and reveal must be withheld. `pdf_required = true` mandates a working pdflatex/latexmk installation for official report generation.

D1 is an exact affine 3D Euler *control*, not a localized vortex/particle. The analytic report PDF was independently generated during development, not by official framework v1.0.7.
