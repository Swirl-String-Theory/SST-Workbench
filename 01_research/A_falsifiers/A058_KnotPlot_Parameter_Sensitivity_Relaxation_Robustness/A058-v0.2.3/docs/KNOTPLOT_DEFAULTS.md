# Runtime defaults

A058 v0.2.3 never hardcodes scientific slider defaults. `run_install.cmd` first records a bare reset-all dump for provenance, then enables each GUI sector separately and records a sector-context `parameters` dump. Slider defaults are taken from the context in which the slider is actually exposed. Campaign generation requires this successful runtime record.
