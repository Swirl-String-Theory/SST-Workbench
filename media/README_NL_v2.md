# SST Arc Whisper ASR patch v2

Deze patch corrigeert de twee problemen uit de getoonde terminal-log:

1. `run_transcribe_arc.bat` had een hardcoded Conda-pad naar `C:\Users\mr\...`; v2 gebruikt de reeds actieve Python/Conda-omgeving.
2. v1 forceerde `ONEAPI_DEVICE_SELECTOR=level_zero:0`. OpenVINO/oneDNN routeert GPU-inferentie op Windows vaak via OpenCL, waardoor die selector verwarrende `CL_INVALID_OPERATION`-logs kan geven. v2 laat OpenVINO zelf devices detecteren en gebruikt standaard `--device AUTO`.

Gebruik:

```bat
call C:\Users\oscar\anaconda3\Scripts\activate.bat SSTcore_TTS
cd C:\workspace\projects\SST-Workbench\media
run_transcribe_arc_v2.bat
```

Handmatig GPU forceren:

```bat
python transcribe_arc_openvino_v2.py "De_logische_fundamenten_van_Swirl-String_Theory.m4a" --language nl --device GPU --out transcript_sst_gpu
```

CPU fallback:

```bat
python transcribe_arc_openvino_v2.py "De_logische_fundamenten_van_Swirl-String_Theory.m4a" --language nl --device CPU --out transcript_sst_cpu
```

Device probe:

```bat
python transcribe_arc_openvino_v2.py --probe-devices
```

Output:

- `transcript_sst.txt`
- `transcript_sst.srt`
