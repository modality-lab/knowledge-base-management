---
name: parse-audio-to-note
description: Transcribe a local audio or video file with Whisper and save as an Obsidian note with transcript JSON
---

Transcribe the audio/video file from the user's message and save it as an Obsidian note in this vault.

- `ffmpeg` must be available on PATH.
- `WHISPER_MODEL` env var selects the model (default: `base`; options: tiny/base/small/medium/large-v2/large-v3).
- `HF_TOKEN` env var enables speaker diarization via pyannote (optional).
- `NOTE_LANGUAGE` env var sets the note language: `auto` (default, matches transcript language), or a language code like `en`, `ru`.

Supported input: audio files (mp3, wav, m4a, ogg, opus, flac, aac, wma) and video files (mp4, mkv, mov, webm). If a video file is provided, audio is extracted automatically via ffmpeg.

## Instructions

### Step 1 — Set up environment

If `.venv` does not exist in this skill's directory, create it and install dependencies:

```bash
python3 -m venv <this-skill-dir>/.venv
<this-skill-dir>/.venv/bin/pip install -r <this-skill-dir>/requirements.txt
```

### Step 2 — Transcribe

```bash
<this-skill-dir>/.venv/bin/python3 <this-skill-dir>/audio_transcriber.py "<file_path>" 2>/dev/null
```

Returns JSON:
```json
{
  "source_path": "/path/to/file",
  "audio_path": "/tmp/transcribe_<hash>/audio.mp3",
  "segments": [{"start": 0.0, "end": 3.2, "text": "...", "speaker": null}],
  "language": "en",
  "duration": 3621.0
}
```

### Step 3 — Process screenshots (video files only)

If the input was a video file and the user provided screenshots with visible player timecodes:
1. Read each screenshot image
2. Extract the visible timecodes from the player UI
3. Match timecodes to transcript segments — mark those sections as especially important
4. These screenshots will be embedded in the note near the corresponding key points

### Step 4 — Analyze transcript

Read all transcript segments and produce:

1. **Key points** — numbered list with nested sub-points for important details. If screenshots marked certain sections as important, expand those sections with more detail.

2. **To try** — action items the viewer/listener should attempt.

### Step 5 — Choose vault location

Explore the vault with `ls` to find the best existing folder for this content. If there are several appropriate places, ask the user to choose.

### Step 6 — Save files

1. Create `<target-folder>/attachments/` if it doesn't exist.
2. If there are screenshots, copy them: `cp <path> "<target-folder>/attachments/<safe-title>_<timecode>.jpg"`
3. Save the full transcript JSON:
   `<target-folder>/<Title>_transcript.json`

### Step 7 — Create the note

Create `<target-folder>/<Title>.md`:

```markdown
---
source: "<path to file>"
platform: local-audio | local-video
date_saved: <today>
tags:
  - source/local
  - topic/<topic>
---

# Key points
1. Point
   - Sub-point

![[attachments/screenshot.jpg|700]]

2. Point related to screenshot — expanded in more detail because it was marked by screenshot

# To try
- [ ] Action item

# References
```

**Rules:**
- Language: use `NOTE_LANGUAGE` env var — `auto` (default) = transcript language, otherwise the specified language
- Place `![[...]]` screenshot embeds inline within Key points where they are most relevant
- Use `|700` width on all image embeds
- Leave `# References` section empty — the user fills it in
- Do not dump the raw transcript — the note should be a curated summary
