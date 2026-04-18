---
name: note-youtube-video
description: Download a YouTube video, transcribe it with Whisper via note-audio, and save as an Obsidian note with timecodes and screenshots
---

Download and transcribe the YouTube video from the user's message, then save it as an Obsidian note in this vault.

- `NOTE_LANGUAGE` env var sets the note language: `auto` (default, matches transcript language), or a language code like `en`, `ru`.

## Instructions

### Step 1 — Check system dependencies

```bash
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required but not found on PATH"; exit 1; }
command -v ffmpeg >/dev/null 2>&1 || { echo "ERROR: ffmpeg is required but not found on PATH. Install via: brew install ffmpeg"; exit 1; }
```

### Step 2 — Set up environment

If `.venv` does not exist in this skill's directory, create it and install dependencies:

```bash
python3 -m venv <this-skill-dir>/.venv
<this-skill-dir>/.venv/bin/pip install -r <this-skill-dir>/requirements.txt
```

### Step 3 — Download audio and metadata

```bash
<this-skill-dir>/.venv/bin/python3 <this-skill-dir>/youtube_downloader.py "<url>" 2>/dev/null
```

Returns JSON:
```json
{
  "audio_path": "/tmp/yt_download_<hash>/audio.mp3",
  "thumbnail_path": "/tmp/yt_download_<hash>/thumbnail.jpg",
  "title": "Video Title",
  "channel": "Channel Name",
  "date": "20250115",
  "duration": 3621,
  "duration_formatted": "01:00:21",
  "video_id": "dQw4w9WgXcQ",
  "view_count": 12345,
  "description": "..."
}
```

### Step 4 — Transcribe via note-audio

Use the `note-audio` skill to transcribe the downloaded audio file at `audio_path`. Pass any user-provided screenshots along.

**Important:** The `note-audio` skill will handle transcription and analysis. Override the note format with YouTube-specific metadata (see Step 5).

### Step 5 — Create the note

After transcription, create the note with YouTube-specific frontmatter and timecoded outline:

```markdown
---
source: "https://www.youtube.com/watch?v=VIDEO_ID"
platform: youtube
author: "<channel>"
date_published: <date formatted as YYYY-MM-DD>
date_saved: <today>
tags:
  - source/youtube
  - topic/<topic>
---

# Timecodes
- [00:00](https://www.youtube.com/watch?v=VIDEO_ID) - Introduction
- [02:30](https://www.youtube.com/watch?v=VIDEO_ID&t=150s) - Topic name

# Key points
1. First major point
   - Sub-point with detail

![[attachments/safe-title_05m45s.jpg|700]]

2. Second major point (visual reference above)

# To try
- [ ] Action item

# References
```

**Rules:**
- Language: use `NOTE_LANGUAGE` env var — `auto` (default) = transcript language, otherwise the specified language
- Place `![[...]]` screenshot embeds inline within Key points where they are most relevant
- Use `|700` width on all image embeds
- Include timecode entries for each major section (aim for one entry per 2-5 minutes of content)
- Timecode links point to YouTube with `&t=Xs` parameter
- Leave `# References` section empty
- Copy thumbnail to `<target-folder>/attachments/<safe-title>_thumb.jpg`
- Save transcript JSON as `<target-folder>/<Title>_transcript.json`
