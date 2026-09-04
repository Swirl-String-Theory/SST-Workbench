"""
SST / Intel Arc Whisper ASR pipeline
-----------------------------------
Purpose:
  Transcribe long Dutch/English audio files on Intel Arc GPUs through OpenVINO GenAI.

Expected local environment:
  - Intel Arc driver + Level Zero runtime
  - oneAPI runtime initialized by run_transcribe_arc.bat
  - Python packages from requirements_arc_asr.txt
  - ffmpeg available on PATH

Example:
  python transcribe_arc_openvino.py "De_logische_fundamenten_van_Swirl-String_Theory.m4a" --language nl --model openai/whisper-medium

Outputs:
  transcript.txt
  transcript.srt
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


def _run(cmd: List[str]) -> None:
    print("[cmd] " + " ".join(cmd))
    completed = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {completed.returncode}: {' '.join(cmd)}")


def require_executable(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise FileNotFoundError(
            f"'{name}' staat niet op PATH. Installeer het of open een terminal waarin het beschikbaar is."
        )
    return path


def convert_to_16k_mono_wav(input_audio: Path, output_wav: Path, force: bool = False) -> Path:
    """Whisper/OpenVINO verwacht effectief 16 kHz genormaliseerde audio.

    ffmpeg is robuuster dan torchaudio/librosa voor .m4a/.aac op Windows.
    """
    if output_wav.exists() and not force:
        print(f"[I/O] Bestaande 16 kHz WAV gevonden: {output_wav}")
        return output_wav

    require_executable("ffmpeg")
    print(f"[Audio] Converteren naar mono 16 kHz PCM WAV: {output_wav}")
    _run([
        "ffmpeg",
        "-y",
        "-i", str(input_audio),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(output_wav),
    ])
    return output_wav


def model_dir_name(model_id: str, quant: str = "") -> str:
    safe = model_id.replace("/", "__").replace(":", "_")
    if quant:
        safe += f"__{quant}"
    return safe


def ensure_openvino_model(model_id: str, output_dir: Path, force_export: bool = False) -> Path:
    """Export HuggingFace Whisper checkpoint to OpenVINO IR if needed."""
    if output_dir.exists() and any(output_dir.iterdir()) and not force_export:
        print(f"[Model] OpenVINO model-map bestaat al: {output_dir}")
        return output_dir

    require_executable("optimum-cli")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[Model] Exporteren naar OpenVINO IR: {model_id} -> {output_dir}")
    _run([
        "optimum-cli", "export", "openvino",
        "--trust-remote-code",
        "--model", model_id,
        str(output_dir),
    ])
    return output_dir


def read_wav_16k_as_float_list(wav_path: Path) -> List[float]:
    import librosa

    print(f"[Audio] Laden als float32 / 16 kHz: {wav_path}")
    raw_speech, samplerate = librosa.load(str(wav_path), sr=16000, mono=True)
    if samplerate != 16000:
        raise RuntimeError(f"Onverwachte sample rate na librosa.load: {samplerate}")
    return raw_speech.astype("float32").tolist()


def srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    millis = int(round(seconds * 1000.0))
    h = millis // 3_600_000
    millis %= 3_600_000
    m = millis // 60_000
    millis %= 60_000
    s = millis // 1000
    ms = millis % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


@dataclass
class Chunk:
    start_ts: float
    end_ts: float
    text: str


def normalize_chunks(result) -> List[Chunk]:
    chunks = []
    if hasattr(result, "chunks") and result.chunks:
        for c in result.chunks:
            text = getattr(c, "text", "").strip()
            if not text:
                continue
            chunks.append(Chunk(float(c.start_ts), float(c.end_ts), text))
    else:
        text = str(result).strip()
        if text:
            chunks.append(Chunk(0.0, 0.0, text))
    return chunks


def write_txt(chunks: Iterable[Chunk], output_txt: Path) -> None:
    with output_txt.open("w", encoding="utf-8") as f:
        for c in chunks:
            if c.end_ts > c.start_ts:
                f.write(f"[{c.start_ts:8.2f} - {c.end_ts:8.2f}] {c.text}\n")
            else:
                f.write(c.text + "\n")
    print(f"[I/O] Transcript TXT: {output_txt}")


def write_srt(chunks: Iterable[Chunk], output_srt: Path) -> None:
    with output_srt.open("w", encoding="utf-8") as f:
        for i, c in enumerate(chunks, start=1):
            start = srt_timestamp(c.start_ts)
            end = srt_timestamp(c.end_ts if c.end_ts > c.start_ts else c.start_ts + 2.0)
            f.write(f"{i}\n{start} --> {end}\n{c.text}\n\n")
    print(f"[I/O] Transcript SRT: {output_srt}")


def transcribe(
    input_audio: Path,
    language: Optional[str],
    task: str,
    model_id: str,
    device: str,
    out_prefix: Path,
    initial_prompt: str,
    force_preprocess: bool,
    force_export: bool,
) -> None:
    import openvino_genai

    input_audio = input_audio.resolve()
    if not input_audio.exists():
        raise FileNotFoundError(f"Audio niet gevonden: {input_audio}")

    work_dir = out_prefix.parent.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    wav_path = work_dir / (input_audio.stem + "__16k_mono.wav")
    convert_to_16k_mono_wav(input_audio, wav_path, force=force_preprocess)

    ov_dir = work_dir / "openvino_models" / model_dir_name(model_id)
    ensure_openvino_model(model_id, ov_dir, force_export=force_export)

    raw_speech = read_wav_16k_as_float_list(wav_path)

    print(f"[OpenVINO] WhisperPipeline laden op device='{device}'")
    pipe = openvino_genai.WhisperPipeline(str(ov_dir), device)

    generate_kwargs = {
        "task": task,
        "return_timestamps": True,
    }
    if language:
        # OpenVINO Whisper verwacht Whisper language tokens, bv. <|nl|>, <|en|>.
        generate_kwargs["language"] = f"<|{language}|>"
    if initial_prompt:
        generate_kwargs["initial_prompt"] = initial_prompt

    print(f"[ASR] Start transcriptie: language={language or 'auto'}, task={task}, model={model_id}")
    result = pipe.generate(raw_speech, **generate_kwargs)
    chunks = normalize_chunks(result)

    if not chunks:
        raise RuntimeError("Geen transcriptie ontvangen. Controleer audio, taal, model en 16 kHz conversie.")

    write_txt(chunks, out_prefix.with_suffix(".txt"))
    write_srt(chunks, out_prefix.with_suffix(".srt"))
    print("[Status] Transcriptie voltooid.")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Intel Arc/OpenVINO Whisper transcriptie voor lange audio.")
    p.add_argument("audio", type=Path, help="Invoerbestand: .m4a, .mp3, .wav, ...")
    p.add_argument("--language", default="nl", help="Whisper taalcode, bv. nl, en, de. Gebruik leeg/auto voor autodetectie.")
    p.add_argument("--task", default="transcribe", choices=["transcribe", "translate"])
    p.add_argument("--model", default="openai/whisper-medium", help="HuggingFace model-id")
    p.add_argument("--device", default="GPU", help="OpenVINO device: GPU, CPU, AUTO, MULTI:GPU,CPU")
    p.add_argument("--out", type=Path, default=Path("transcript"), help="Outputprefix zonder extensie")
    p.add_argument(
        "--initial-prompt",
        default=(
            "Swirl-String Theory, SST, swirl density, vorticity, incompressible inviscid fluid, "
            "rho_f, rho_core, vortex knots, Kelvin, Helmholtz, canonical constants."
        ),
        help="Contextprompt/hotwords voor technische termen.",
    )
    p.add_argument("--force-preprocess", action="store_true")
    p.add_argument("--force-export", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    lang = args.language.strip() if args.language and args.language.lower() != "auto" else None
    transcribe(
        input_audio=args.audio,
        language=lang,
        task=args.task,
        model_id=args.model,
        device=args.device,
        out_prefix=args.out,
        initial_prompt=args.initial_prompt,
        force_preprocess=args.force_preprocess,
        force_export=args.force_export,
    )
