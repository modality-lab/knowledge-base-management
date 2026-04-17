#!/usr/bin/env python3
"""
youtube_downloader.py — Download audio and metadata from YouTube videos.

Usage:
    youtube_downloader.py <url>

Downloads audio as mp3 and thumbnail, outputs JSON with metadata to stdout.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


YTDLP = str(Path(__file__).parent / ".venv" / "bin" / "yt-dlp")


def url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def output_dir_for(url: str) -> Path:
    d = Path(tempfile.gettempdir()) / f"yt_download_{url_hash(url)}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def format_timestamp(seconds: float) -> str:
    s = int(seconds)
    h, m, s = s // 3600, (s % 3600) // 60, s % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def get_metadata(url: str) -> dict:
    result = subprocess.run(
        [YTDLP, "--dump-json", "--no-playlist", url],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr.strip()}")
    data = json.loads(result.stdout)

    duration = data.get("duration", 0)
    return {
        "title": data.get("title", ""),
        "channel": data.get("uploader") or data.get("channel", ""),
        "date": data.get("upload_date", ""),
        "duration": duration,
        "duration_formatted": format_timestamp(duration),
        "video_id": data.get("id", ""),
        "view_count": data.get("view_count"),
        "description": (data.get("description") or "")[:2000],
    }


def download_audio(url: str, out_dir: Path) -> Path:
    """Download audio as mp3 at 64k for transcription."""
    result = subprocess.run(
        [
            YTDLP,
            "-x", "--audio-format", "mp3", "--audio-quality", "64K",
            "--no-playlist",
            "-o", str(out_dir / "audio.%(ext)s"),
            url,
        ],
        capture_output=True, text=True, timeout=600
    )
    if result.returncode != 0:
        raise RuntimeError(f"Audio download failed: {result.stderr.strip()}")
    audio = out_dir / "audio.mp3"
    if not audio.exists():
        matches = list(out_dir.glob("audio.*"))
        if not matches:
            raise RuntimeError("Audio file not found after download")
        audio = matches[0]
    return audio


def download_thumbnail(url: str, out_dir: Path) -> Path | None:
    """Download thumbnail image."""
    result = subprocess.run(
        [
            YTDLP,
            "--write-thumbnail", "--skip-download",
            "--convert-thumbnails", "jpg",
            "--no-playlist",
            "-o", str(out_dir / "thumbnail.%(ext)s"),
            url,
        ],
        capture_output=True, text=True, timeout=60
    )
    for ext in ("jpg", "jpeg", "webp", "png"):
        p = out_dir / f"thumbnail.{ext}"
        if p.exists():
            return p
    return None


def main():
    parser = argparse.ArgumentParser(description="Download YouTube audio and metadata")
    parser.add_argument("url", help="YouTube video URL")
    args = parser.parse_args()

    url = args.url
    out_dir = output_dir_for(url)

    try:
        meta = get_metadata(url)
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    thumbnail_path = download_thumbnail(url, out_dir)

    try:
        audio_path = download_audio(url, out_dir)
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    result = {
        "audio_path": str(audio_path),
        "thumbnail_path": str(thumbnail_path) if thumbnail_path else None,
        **meta,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
