# KnotPlot reset-all defaults used by A058-v0.2.0

A058 deliberately does not override non-strength relaxation controls. Official KnotPlot documentation states that reset/default relaxation includes `bendforce=off`, `elecforce=on`, `mechforce=on`, `bencon=1.0`, `close=0.12`, and `max-dr=0.1`. The official control-panel handout shows the strength defaults Hooke=1.00 and Charge=15.0.

The private strength map therefore preregisters the three magnitude defaults as 1.0, 15.0, and 1.0. Every generated script prints `parameters` before applying its one strength override, so the exact runtime state is retained in the private KnotPlot log for build-level provenance.

References:
- https://knotplot.com/doc/KnotPlot-Manual.pdf
- https://knotplot.com/doc/handout.pdf
- https://knotplot.com/manual/commands.html
