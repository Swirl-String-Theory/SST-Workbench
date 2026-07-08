Sound to text

```bash
pip install -U openai-whisper
whisper "De_logische_fundamenten_van_Swirl-String_Theory.m4a" --language Dutch --task transcribe --model medium --output_format txt
```