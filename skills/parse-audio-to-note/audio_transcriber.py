#!/usr/bin/env python3
"""
audio_transcriber.py — Transcribe audio or video files using local Whisper.

Usage:
    audio_transcriber.py <file_path>

If the input is a video file (mp4, mkv, mov, webm), audio is extracted via ffmpeg first.
Outputs JSON to stdout with transcription segments.

Environment variables:
  WHISPER_MODEL   faster-whisper model size: tiny, base, small, medium, large-v2, large-v3 (default: base)
  HF_TOKEN        HuggingFace token — required for speaker diarization via pyannote.audio (optional)
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


FFMPEG = "ffmpeg"
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".webm"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".opus", ".flac", ".aac", ".wma"}


def file_hash(path: str) -> str:
    return hashlib.md5(path.encode()).hexdigest()[:12]


def output_dir_for(path: str) -> Path:
    d = Path(tempfile.gettempdir()) / f"transcribe_{file_hash(path)}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def format_timestamp(seconds: float) -> str:
    s = int(seconds)
    h, m, s = s // 3600, (s % 3600) // 60, s % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def extract_audio(video_path: Path, out_dir: Path) -> Path:
    """Extract audio from a video file using ffmpeg."""
    audio_path = out_dir / "audio.mp3"
    subprocess.run(
        [FFMPEG, "-y", "-i", str(video_path), "-vn",
         "-ar", "16000", "-ac", "1", "-b:a", "64k", str(audio_path)],
        capture_output=True, check=True
    )
    return audio_path


def transcribe_audio(audio_path: Path, model_size: str = "base") -> tuple[list[dict], str]:
    """Transcribe using faster-whisper locally. Returns (segments, detected_language)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError(
            "faster-whisper not installed. Run: pip install faster-whisper"
        )

    print(f"[whisper] Loading model '{model_size}'...", file=sys.stderr)
    model = WhisperModel(model_size, device="auto", compute_type="auto")

    print("[whisper] Transcribing...", file=sys.stderr)
    segments_iter, info = model.transcribe(
        str(audio_path),
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )

    segments = []
    for seg in segments_iter:
        segments.append({
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
        })

    print(f"[whisper] Done. Language: {info.language}, {len(segments)} segments", file=sys.stderr)
    return segments, info.language


def diarize_audio(audio_path: Path, hf_token: str) -> list[dict]:
    """
    Run speaker diarization via pyannote.audio.
    Returns list of {start, end, speaker}.
    Requires HF_TOKEN and acceptance of pyannote model license on HuggingFace.
    """
    try:
        from pyannote.audio import Pipeline
        import torch
    except ImportError:
        raise RuntimeError(
            "pyannote.audio not installed. Run: pip install pyannote.audio"
        )

    print("[pyannote] Loading diarization pipeline...", file=sys.stderr)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token,
    )
    pipeline.to(torch.device(device))

    print("[pyannote] Running diarization...", file=sys.stderr)
    diarization = pipeline(str(audio_path))

    turns = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        turns.append({
            "start": round(turn.start, 3),
            "end": round(turn.end, 3),
            "speaker": speaker,
        })

    speakers = set(t["speaker"] for t in turns)
    print(f"[pyannote] Done. {len(speakers)} speakers detected", file=sys.stderr)
    return turns


def assign_speakers(segments: list[dict], speaker_turns: list[dict]) -> list[dict]:
    """Label each transcript segment with the speaker active at its midpoint."""
    for seg in segments:
        mid = (seg["start"] + seg["end"]) / 2
        seg["speaker"] = None
        for turn in speaker_turns:
            if turn["start"] <= mid <= turn["end"]:
                seg["speaker"] = turn["speaker"]
                break
    return segments


def get_duration(file_path: Path) -> float:
    """Get duration of audio/video file via ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "json", str(file_path)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
    except Exception:
        pass
    return 0.0


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio or video files")
    parser.add_argument("file_path", help="Path to audio or video file")
    args = parser.parse_args()

    file_path = Path(args.file_path).resolve()
    if not file_path.exists():
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)

    ext = file_path.suffix.lower()
    is_video = ext in VIDEO_EXTENSIONS
    is_audio = ext in AUDIO_EXTENSIONS

    if not is_video and not is_audio:
        print(json.dumps({"error": f"Unsupported file type: {ext}"}))
        sys.exit(1)

    model_size = os.environ.get("WHISPER_MODEL", "base")
    hf_token = os.environ.get("HF_TOKEN")

    out_dir = output_dir_for(str(file_path))

    # Extract audio from video if needed
    if is_video:
        try:
            audio_path = extract_audio(file_path, out_dir)
        except subprocess.CalledProcessError as e:
            print(json.dumps({"error": f"ffmpeg audio extraction failed: {e}"}))
            sys.exit(1)
    else:
        audio_path = file_path

    # Transcribe
    try:
        segments, detected_language = transcribe_audio(audio_path, model_size)
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    # Optional diarization
    if hf_token:
        try:
            speaker_turns = diarize_audio(audio_path, hf_token)
            segments = assign_speakers(segments, speaker_turns)
        except Exception as e:
            print(f"[diarization] Skipped: {e}", file=sys.stderr)
    else:
        print("[diarization] Skipped: HF_TOKEN not set", file=sys.stderr)

    duration = get_duration(file_path)

    result = {
        "source_path": str(file_path),
        "audio_path": str(audio_path),
        "segments": segments,
        "language": detected_language,
        "duration": duration,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
