# Optional topology providers

The core library deliberately does not install these packages during `run_all.cmd`.

## pyknotid

Primary optional provider for identifying a 3D polygonal space curve.

```bat
.venv\Scripts\python.exe -m pip install pyknotid
.venv\Scripts\python.exe -m sst_knotlib providers
```

If installation fails on a very new Python version, do not weaken the falsifier gate or silently substitute a filename. Use a compatible isolated Python environment and export the certification result, or leave the candidate `UNVERIFIED`.

## Spherogram / SnapPy

Useful as independent checks of named-knot diagram data and hyperbolic-complement quantities.

```bat
.venv\Scripts\python.exe -m pip install spherogram
.venv\Scripts\python.exe -m pip install snappy
```

They are not required to load `ideal.txt`, `fseries`, VECT, KnotPlot, or Ridgerunner geometries.

## External KnotPlot / Ridgerunner

The library does not execute or redistribute them by default. Their files are inputs with source hashes and source-family provenance.

Run:

```bat
python -m sst_knotlib providers
```

to see whether executables are discoverable on `PATH`.
