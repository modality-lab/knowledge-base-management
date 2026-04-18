#!/usr/bin/env python3
"""
instagram_extractor.py — Extract Instagram post content and media.

Usage:
    instagram_extractor.py <url>

Downloads media to /tmp/instagram_extract_<hash>/, outputs JSON to stdout.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


YTDLP = str(Path(sys.executable).parent / "yt-dlp")


def url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:8]


def run_ytdlp(url: str, output_dir: str, extra_args: list[str] | None = None) -> dict | None:
    """Run yt-dlp --dump-json and return parsed JSON, or None on failure."""
    cmd = [YTDLP, "--dump-json", "--skip-download", "--no-warnings"]
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            return None
        first_line = result.stdout.strip().split("\n")[0]
        return json.loads(first_line)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, IndexError):
        return None


def reencode_to_h264(path: str) -> str:
    """Re-encode a video file to H.264/AAC for macOS/QuickTime compatibility."""
    if not shutil.which("ffmpeg"):
        return path
    tmp = path.rsplit(".", 1)[0] + "_h264.mp4"
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", path, "-c:v", "libx264", "-c:a", "aac",
             "-movflags", "+faststart", "-y", tmp],
            capture_output=True, timeout=300,
        )
        if result.returncode == 0:
            os.replace(tmp, path)
    except (subprocess.TimeoutExpired, OSError):
        if os.path.exists(tmp):
            os.remove(tmp)
    return path


def download_media_ytdlp(url: str, output_dir: str) -> list[dict]:
    """Download media files via yt-dlp and return list of media dicts."""
    media = []
    output_template = os.path.join(output_dir, "%(title).50s_%(id)s.%(ext)s")

    cmd = [YTDLP, "--no-warnings", "-o", output_template, url]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        pass

    for f in sorted(Path(output_dir).iterdir()):
        if f.name.startswith("."):
            continue
        ext = f.suffix.lower()
        if ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
            media.append({"type": "image", "path": str(f), "alt": f.stem})
        elif ext in (".mp4", ".webm", ".mkv", ".mov"):
            reencode_to_h264(str(f))
            media.append({"type": "video", "path": str(f)})
        elif ext in (".mp3", ".m4a", ".opus", ".ogg", ".wav"):
            media.append({"type": "audio", "path": str(f)})

    return media


def extract_instagram(url: str, output_dir: str) -> dict:
    info = run_ytdlp(url, output_dir)

    result = {
        "url": url,
        "platform": "instagram",
        "title": "",
        "author": "",
        "date": "",
        "text": "",
        "media": [],
        "metadata": {},
    }

    if info:
        result["title"] = info.get("title", "") or ""
        result["text"] = info.get("description", "") or ""
        result["author"] = info.get("uploader", "") or info.get("uploader_id", "") or ""
        upload_date = info.get("upload_date", "")
        if upload_date:
            result["date"] = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
        result["metadata"] = {
            k: info.get(k)
            for k in ("like_count", "comment_count", "view_count")
            if info.get(k) is not None
        }
        result["media"] = download_media_ytdlp(url, output_dir)
    else:
        result["text"] = f"[Could not extract content from {url}]"

    return result


def main():
    parser = argparse.ArgumentParser(description="Extract Instagram post content and media")
    parser.add_argument("url", help="Instagram URL")
    args = parser.parse_args()

    output_dir = f"/tmp/instagram_extract_{url_hash(args.url)}"
    os.makedirs(output_dir, exist_ok=True)

    try:
        result = extract_instagram(args.url, output_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"url": args.url, "platform": "instagram", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
