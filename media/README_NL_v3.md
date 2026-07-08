# SST Arc Whisper ASR patch v3

Deze versie maakt automatisch de outputnaam uit de invoerfile.

## Gebruik

```bat
call C:\Users\oscar\anaconda3\Scripts\activate.bat SSTcore_TTS
cd C:\workspace\projects\SST-Workbench\media
run_transcribe_arc_v3.bat "De_logische_fundamenten_van_Swirl-String_Theory.m4a"
```

Dan ontstaan automatisch:

```text
De_logische_fundamenten_van_Swirl-String_Theory_transcript.txt
De_logische_fundamenten_van_Swirl-String_Theory_transcript.srt
```

Je kunt ook een bestand naar de `.bat` slepen in Verkenner.

## Handmatig, zonder batch

```bat
python transcribe_arc_openvino_v3.py "Rigorous_derivations_for_Swirl_String_Theory.m4a" --language nl --device AUTO
```

Zonder `--out` schrijft de Python-code automatisch naast de audio:

```text
mijn_audio_transcript.txt
mijn_audio_transcript.srt
```

## Device-test

```bat
python transcribe_arc_openvino_v3.py --probe-devices
```

## Modelkeuze

Default is `openai/whisper-medium`. Voor sneller testen kun je tijdelijk `openai/whisper-small` gebruiken. Voor hogere kwaliteit kun je later `openai/whisper-large-v3-turbo` proberen.