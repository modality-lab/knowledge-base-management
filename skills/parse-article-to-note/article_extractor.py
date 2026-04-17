#!/usr/bin/env python3
"""
article_extractor.py — Extract article content, metadata, and images from any URL.

Usage:
    article_extractor.py <url>

Downloads images to /tmp/article_extract_<hash>/, outputs JSON to stdout.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
import trafilatura


def url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:8]


def _download_article_images(html: str, base_url: str, output_dir: str, result: dict):
    """Download main images from article HTML."""
    og_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html)
    img_urls = []

    if og_match:
        img_urls.append(og_match.group(1))

    img_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)', html)
    for img_url in img_matches[:3]:
        if img_url not in img_urls and not img_url.endswith(".svg"):
            img_urls.append(img_url)

    for i, img_url in enumerate(img_urls[:5]):
        try:
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                parsed = urlparse(base_url)
                img_url = f"{parsed.scheme}://{parsed.hostname}{img_url}"

            resp = requests.get(img_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            ext = ".jpg"
            if "png" in content_type:
                ext = ".png"
            elif "webp" in content_type:
                ext = ".webp"
            elif "gif" in content_type:
                ext = ".gif"

            img_path = os.path.join(output_dir, f"article_image_{i:03d}{ext}")
            with open(img_path, "wb") as f:
                f.write(resp.content)

            result["media"].append({"type": "image", "path": img_path, "alt": ""})
        except Exception:
            continue


def extract_article(url: str, output_dir: str) -> dict:
    result = {
        "url": url,
        "platform": "article",
        "title": "",
        "author": "",
        "date": "",
        "text": "",
        "media": [],
        "metadata": {},
    }

    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            result["text"] = f"[Could not fetch {url}]"
            return result

        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            include_links=True,
            output_format="txt",
        )

        result["text"] = text or ""

        meta = trafilatura.metadata.extract_metadata(downloaded)
        if meta:
            result["title"] = meta.title or ""
            result["author"] = meta.author or ""
            result["date"] = meta.date or ""
            result["metadata"]["sitename"] = meta.sitename or ""
            result["metadata"]["categories"] = meta.categories or []
            result["metadata"]["tags"] = meta.tags or []

        if downloaded:
            _download_article_images(downloaded, url, output_dir, result)

    except Exception as e:
        result["text"] = f"[Error extracting article: {e}]"

    return result


def main():
    parser = argparse.ArgumentParser(description="Extract article content from a URL")
    parser.add_argument("url", help="Article URL")
    args = parser.parse_args()

    output_dir = f"/tmp/article_extract_{url_hash(args.url)}"
    os.makedirs(output_dir, exist_ok=True)

    try:
        result = extract_article(args.url, output_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"url": args.url, "platform": "article", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
