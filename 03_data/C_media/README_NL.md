# SST Arc Whisper ASR patch

Deze patch hergebruikt jouw bestaande Arc/XPU aanpak, maar vervangt de XTTS-spraaksynthese door Whisper transcriptie via OpenVINO GenAI.

## Bestanden

- `transcribe_arc_openvino.py` — hoofdscript voor transcriptie.
- `run_transcribe_arc.bat` — Windows launcher in dezelfde stijl als je `run_xpu.bat`.
- `requirements_arc_asr.txt` — Python packages.

## Installatie

Open Anaconda Prompt:

```bat
call C:\Users\mr\anaconda3\Scripts\activate.bat SSTcore_TTS
pip install --upgrade-strategy eager -r requirements_arc_asr.txt
winget install Gyan.FFmpeg
```

## Run

Plaats `De_logische_fundamenten_van_Swirl-String_Theory.m4a` naast deze scripts en start:

```bat
run_transcribe_arc.bat
```

Of handmatig:

```bat
python transcribe_arc_openvino.py "Rigorous_derivations_for_Swirl_String_Theory.m4a" --language nl --model openai/whisper-medium --device GPU --out transcript_sst
```

## Output

- `transcript_sst.txt`
- `transcript_sst.srt`
- tijdelijke geconverteerde WAV: `De_logische_fundamenten_van_Swirl-String_Theory__16k_mono.wav`
- OpenVINO modelmap onder `openvino_models/`

## Modelkeuze

Start met `openai/whisper-medium`.
Voor hogere kwaliteit kun je later proberen:

```bat
python transcribe_arc_openvino.py audio.m4a --language nl --model openai/whisper-large-v3-turbo --device GPU --out transcript_large
```