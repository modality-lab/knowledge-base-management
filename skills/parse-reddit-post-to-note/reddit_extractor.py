#!/usr/bin/env python3
"""
reddit_extractor.py — Extract Reddit post content, top comments, and media.

Usage:
    reddit_extractor.py <url>

Downloads media to /tmp/reddit_extract_<hash>/, outputs JSON to stdout.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
import trafilatura

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


def extract_reddit(url: str, output_dir: str) -> dict:
    result = {
        "url": url,
        "platform": "reddit",
        "title": "",
        "author": "",
        "date": "",
        "text": "",
        "media": [],
        "metadata": {},
    }

    json_url = url.rstrip("/") + ".json"
    headers = {"User-Agent": "Mozilla/5.0 (link-extractor/1.0)"}

    try:
        resp = requests.get(json_url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, list) and len(data) > 0:
            post_data = data[0]["data"]["children"][0]["data"]
            result["title"] = post_data.get("title", "")
            result["author"] = "u/" + post_data.get("author", "")
            result["text"] = post_data.get("selftext", "") or post_data.get("title", "")

            created_utc = post_data.get("created_utc")
            if created_utc:
                result["date"] = datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime("%Y-%m-%d")

            result["metadata"] = {
                "score": post_data.get("score"),
                "upvote_ratio": post_data.get("upvote_ratio"),
                "num_comments": post_data.get("num_comments"),
                "subreddit": post_data.get("subreddit"),
            }

            # Collect top comments
            if len(data) > 1:
                comments = []
                for child in data[1]["data"]["children"][:5]:
                    if child["kind"] == "t1":
                        body = child["data"].get("body", "")
                        author = child["data"].get("author", "")
                        score = child["data"].get("score", 0)
                        if body:
                            comments.append(f"**u/{author}** ({score} pts):\n{body}")
                if comments:
                    result["text"] += "\n\n--- Top Comments ---\n\n" + "\n\n".join(comments)

            # Download linked media if present
            media_url = post_data.get("url", "")
            if media_url and any(media_url.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp")):
                try:
                    img_resp = requests.get(media_url, timeout=30)
                    img_resp.raise_for_status()
                    ext = Path(urlparse(media_url).path).suffix
                    img_path = os.path.join(output_dir, f"reddit_image{ext}")
                    with open(img_path, "wb") as f:
                        f.write(img_resp.content)
                    result["media"].append({"type": "image", "path": img_path, "alt": result["title"]})
                except Exception:
                    pass
            elif media_url:
                result["media"] = download_media_ytdlp(media_url, output_dir)

    except Exception:
        pass

    # Fallback: use trafilatura if JSON API failed
    if not result["text"]:
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text = trafilatura.extract(downloaded, include_comments=True, output_format="txt")
                meta = trafilatura.metadata.extract_metadata(downloaded)
                if text:
                    result["text"] = text
                if meta:
                    result["title"] = meta.title or ""
                    result["author"] = meta.author or ""
                    result["date"] = meta.date or ""
        except Exception:
            pass

    if not result["text"]:
        result["text"] = f"[Could not extract content from {url}]"

    return result


def main():
    parser = argparse.ArgumentParser(description="Extract Reddit post content and media")
    parser.add_argument("url", help="Reddit URL")
    args = parser.parse_args()

    output_dir = f"/tmp/reddit_extract_{url_hash(args.url)}"
    os.makedirs(output_dir, exist_ok=True)

    try:
        result = extract_reddit(args.url, output_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"url": args.url, "platform": "reddit", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
