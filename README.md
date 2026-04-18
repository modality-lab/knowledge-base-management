# knowledge-base-management

Agent Skills for saving web content and media to an Obsidian knowledge base.

These skills follow the [Agent Skills specification](https://agentskills.io/specification) and can be used with Claude Code and any other skills-compatible agent.

## Installation

### Marketplace

```
/plugin marketplace add modality-lab/knowledge-base-management
/plugin install knowledge-base-management@modality-lab
```

### Manually

Copy the `skills/` directory into `~/.claude/skills/`.

## Requirements

- Python 3.9+
- `ffmpeg` on PATH (for `note-youtube-video` and `note-audio`)

## Skills

| Skill | Description |
|---|---|
| [note-link](skills/note-link) | Dispatcher: detects platform from URL and routes to the appropriate skill |
| [note-article](skills/note-article) | Extract any article, blog post, or documentation page, save as a note |
| [note-twitter-post](skills/note-twitter-post) | Extract a tweet/X post with text and media, save as a note |
| [note-instagram](skills/note-instagram) | Extract an Instagram post with description and media, save as a note |
| [note-reddit](skills/note-reddit) | Extract a Reddit post with top comments and media, save as a note |
| [note-youtube-video](skills/note-youtube-video) | Download a YouTube video, transcribe with Whisper, save as a note with timecodes |
| [note-audio](skills/note-audio) | Transcribe a local audio or video file with Whisper, save as a note with transcript JSON |

## Usage

The simplest entry point is `note-link` — paste any URL and it routes automatically:

```
/note-link https://...
```

Or invoke a specific skill directly for more control.

## Configuration

Set environment variables to customize behavior:

| Variable | Default | Description |
|---|---|---|
| `NOTE_LANGUAGE` | `auto` | Note language: `auto` matches content language, or use a code like `en`, `ru` |
| `WHISPER_MODEL` | `base` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3` |
| `HF_TOKEN` | — | Hugging Face token to enable speaker diarization in `note-audio` |
