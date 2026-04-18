#!/usr/bin/env python3
"""
tweet_extractor.py — Extract tweet content, media, and metadata.

Usage:
    tweet_extractor.py <url>

Downloads media to /tmp/tweet_extract_<hash>/, outputs JSON to stdout.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

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


def _extract_tweet_id(url: str) -> str | None:
    """Extract tweet ID from a Twitter/X URL."""
    match = re.search(r"/status/(\d+)", url)
    return match.group(1) if match else None


def _fetch_tweet_vxtwitter(tweet_id: str) -> dict | None:
    """Fetch tweet data from vxtwitter API (works for all public tweets)."""
    try:
        resp = requests.get(
            f"https://api.vxtwitter.com/status/{tweet_id}",
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def _fetch_tweet_oembed(url: str) -> dict | None:
    """Fetch tweet data via Twitter's oEmbed API (no auth needed)."""
    try:
        resp = requests.get(
            "https://publish.twitter.com/oembed",
            params={"url": url},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            html = data.get("html", "")
            text_match = re.search(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
            text = ""
            if text_match:
                text = re.sub(r'<[^>]+>', '', text_match.group(1))
                text = text.replace("&mdash;", "—").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            return {
                "text": text.strip(),
                "author_name": data.get("author_name", ""),
                "author_url": data.get("author_url", ""),
            }
    except Exception:
        pass
    return None


def extract_twitter(url: str, output_dir: str) -> dict:
    result = {
        "url": url,
        "platform": "twitter",
        "title": "",
        "author": "",
        "date": "",
        "text": "",
        "media": [],
        "metadata": {},
    }

    tweet_id = _extract_tweet_id(url)
    vx_data = _fetch_tweet_vxtwitter(tweet_id) if tweet_id else None

    if vx_data:
        result["text"] = vx_data.get("text", "")
        result["title"] = result["text"][:80]
        result["author"] = "@" + vx_data.get("user_screen_name", "")
        date_epoch = vx_data.get("date_epoch")
        if date_epoch:
            result["date"] = datetime.fromtimestamp(date_epoch, tz=timezone.utc).strftime("%Y-%m-%d")
        result["metadata"] = {
            k: v for k, v in {
                "likes": vx_data.get("likes"),
                "retweets": vx_data.get("retweets"),
                "replies": vx_data.get("replies"),
            }.items() if v is not None
        }

        for i, media_url in enumerate(vx_data.get("mediaURLs", [])):
            media_ext = vx_data.get("media_extended", [])
            media_type = media_ext[i].get("type", "image") if i < len(media_ext) else "image"
            try:
                resp = requests.get(media_url, timeout=30)
                resp.raise_for_status()
                ext = Path(urlparse(media_url).path).suffix or ".jpg"
                fname = f"tweet_media_{i:03d}{ext}"
                fpath = os.path.join(output_dir, fname)
                with open(fpath, "wb") as f:
                    f.write(resp.content)
                result["media"].append({
                    "type": media_type,
                    "path": fpath,
                    "alt": f"Tweet media {i+1}",
                })
            except Exception:
                continue
    else:
        info = run_ytdlp(url, output_dir)
        if info:
            result["title"] = info.get("title", "") or info.get("fulltitle", "")
            result["text"] = info.get("description", "") or ""
            uploader = info.get("uploader", "") or ""
            uploader_id = info.get("uploader_id", "") or ""
            result["author"] = f"@{uploader_id}" if uploader_id else uploader
            upload_date = info.get("upload_date", "")
            if upload_date:
                result["date"] = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
            result["metadata"] = {
                k: info.get(k)
                for k in ("like_count", "repost_count", "view_count", "comment_count")
                if info.get(k) is not None
            }
            result["media"] = download_media_ytdlp(url, output_dir)
        else:
            fallback = _fetch_tweet_oembed(url)
            if fallback and fallback.get("text"):
                result["title"] = fallback["text"][:80]
                result["text"] = fallback["text"]
                author_url = fallback.get("author_url", "")
                author_handle = author_url.rstrip("/").split("/")[-1] if author_url else ""
                result["author"] = f"@{author_handle}" if author_handle else fallback.get("author_name", "")

    if not result["text"]:
        result["text"] = f"[Could not extract content from {url}]"

    return result


def main():
    parser = argparse.ArgumentParser(description="Extract tweet content and media")
    parser.add_argument("url", help="Twitter/X URL")
    args = parser.parse_args()

    output_dir = f"/tmp/tweet_extract_{url_hash(args.url)}"
    os.makedirs(output_dir, exist_ok=True)

    try:
        result = extract_twitter(args.url, output_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"url": args.url, "platform": "twitter", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
