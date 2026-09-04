"""
SST / Intel Arc Whisper ASR pipeline v2
--------------------------------------
Wijzigingen t.o.v. v1:
  - Geen hardcoded Conda-pad; launcher gebruikt de actieve Python.
  - OpenVINO device-probe via Core.available_devices.
  - Default device is AUTO in plaats van hard GPU.
  - Als GPU niet beschikbaar is, valt de code expliciet terug naar AUTO/CPU.
  - Houdt TXT + SRT output gelijk aan v1.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


def _run(cmd: Sequence[str]) -> None:
    printable = " ".join(str(c) for c in cmd)
    print(f"[cmd] {printable}")
    completed = subprocess.run(list(cmd), stdout=sys.stdout, stderr=sys.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {completed.returncode}: {printable}")


def require_executable(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise FileNotFoundError(
            f"'{name}' staat niet op PATH. Installeer het of open een terminal waarin het beschikbaar is."
        )
    return path


def probe_openvino_devices() -> list[str]:
    try:
        import openvino as ov
        core = ov.Core()
        devices = list(core.available_devices)
        print("[OpenVINO] Beschikbare devices: " + (", ".join(devices) if devices else "<geen>"))
        return devices
    except Exception as exc:
        print(f"[OpenVINO] Device probe faalde: {exc}")
        return []


def choose_device(requested: str, available: list[str]) -> str:
    req = (requested or "AUTO").strip().upper()
    if req in {"CPU", "AUTO"}:
        return req

    if req == "GPU":
        if any(d == "GPU" or d.startswith("GPU.") for d in available):
            return "GPU"
        print("[Waarschuwing] GPU gevraagd, maar OpenVINO toont geen GPU-device. Fallback naar AUTO.")
        return "AUTO"

    if req.startswith("GPU."):
        if req in available:
            return req
        print(f"[Waarschuwing] {req} gevraagd, maar niet gevonden. Fallback naar AUTO.")
        return "AUTO"

    # MULTI:GPU,CPU of AUTO:GPU,CPU mag de gebruiker zelf forceren.
    return requested


def convert_to_16k_mono_wav(input_audio: Path, output_wav: Path, force: bool = False) -> Path:
    if output_wav.exists() and not force:
        print(f"[I/O] Bestaande 16 kHz WAV gevonden: {output_wav}")
        return output_wav

    require_executable("ffmpeg")
    print(f"[Audio] Converteren naar mono 16 kHz PCM WAV: {output_wav}")
    _run([
        "ffmpeg", "-y",
        "-i", str(input_audio),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(output_wav),
    ])
    return output_wav


def model_dir_name(model_id: str) -> str:
    return model_id.replace("/", "__").replace(":", "_")


def ensure_openvino_model(model_id: str, output_dir: Path, force_export: bool = False) -> Path:
    marker_files = ["openvino_encoder_model.xml", "openvino_decoder_model.xml", "config.json"]
    has_useful_files = output_dir.exists() and any((output_dir / m).exists() for m in marker_files)
    if output_dir.exists() and any(output_dir.iterdir()) and not force_export:
        if has_useful_files:
            print(f"[Model] OpenVINO model-map bestaat al: {output_dir}")
            return output_dir
        print(f"[Waarschuwing] Model-map bestaat maar lijkt incompleet: {output_dir}. Gebruik --force-export bij problemen.")
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
    seconds = max(0.0, float(seconds))
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
    chunks: list[Chunk] = []
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


def transcribe(args: argparse.Namespace) -> None:
    import openvino_genai

    input_audio = args.audio.resolve()
    if not input_audio.exists():
        raise FileNotFoundError(f"Audio niet gevonden: {input_audio}")

    available = probe_openvino_devices()
    device = choose_device(args.device, available)
    print(f"[OpenVINO] Geselecteerd device: {device}")

    work_dir = args.out.parent.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    wav_path = work_dir / (input_audio.stem + "__16k_mono.wav")
    convert_to_16k_mono_wav(input_audio, wav_path, force=args.force_preprocess)

    ov_dir = work_dir / "openvino_models" / model_dir_name(args.model)
    ensure_openvino_model(args.model, ov_dir, force_export=args.force_export)

    raw_speech = read_wav_16k_as_float_list(wav_path)

    print(f"[OpenVINO] WhisperPipeline laden op device='{device}'")
    pipe = openvino_genai.WhisperPipeline(str(ov_dir), device)

    generate_kwargs = {"task": args.task, "return_timestamps": True}
    language = args.language.strip() if args.language and args.language.lower() != "auto" else None
    if language:
        generate_kwargs["language"] = f"<|{language}|>"
    if args.initial_prompt:
        generate_kwargs["initial_prompt"] = args.initial_prompt

    print(f"[ASR] Start transcriptie: language={language or 'auto'}, task={args.task}, model={args.model}")
    result = pipe.generate(raw_speech, **generate_kwargs)
    chunks = normalize_chunks(result)
    if not chunks:
        raise RuntimeError("Geen transcriptie ontvangen. Controleer audio, taal, model en 16 kHz conversie.")

    write_txt(chunks, args.out.with_suffix(".txt"))
    write_srt(chunks, args.out.with_suffix(".srt"))
    print("[Status] Transcriptie voltooid.")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Intel Arc/OpenVINO Whisper transcriptie voor lange audio.")
    p.add_argument("audio", type=Path, nargs="?", help="Invoerbestand: .m4a, .mp3, .wav, ...")
    p.add_argument("--probe-devices", action="store_true", help="Toon OpenVINO devices en stop.")
    p.add_argument("--language", default="nl", help="Whisper taalcode: nl, en, de, of auto.")
    p.add_argument("--task", default="transcribe", choices=["transcribe", "translate"])
    p.add_argument("--model", default="openai/whisper-medium", help="HuggingFace model-id")
    p.add_argument("--device", default="AUTO", help="OpenVINO device: AUTO, GPU, GPU.0, CPU, MULTI:GPU,CPU")
    p.add_argument("--out", type=Path, default=Path("transcript"), help="Outputprefix zonder extensie")
    p.add_argument("--initial-prompt", default=(
        "Swirl-String Theory, SST, swirl density, vorticity, incompressible inviscid fluid, "
        "rho_f, rho_core, vortex knots, Kelvin, Helmholtz, canonical constants."
    ))
    p.add_argument("--force-preprocess", action="store_true")
    p.add_argument("--force-export", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    ns = parse_args()
    if ns.probe_devices:
        probe_openvino_devices()
        raise SystemExit(0)
    if ns.audio is None:
        raise SystemExit("Geef een audiofile op, of gebruik --probe-devices.")
    transcribe(ns)
