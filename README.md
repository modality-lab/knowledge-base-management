# knowledge-base-managment

Agent Skills for saving web content and media to an Obsidian knowledge base.

These skills follow the [Agent Skills specification](https://agentskills.io/specification) and can be used with Claude Code and any other skills-compatible agent.

## Installation

### Marketplace

```
/plugin marketplace add modality-lab/knowledge-base-managment
/plugin install knowledge-base-managment@modality-lab
```

### Manually

Copy the `skills/` directory into `~/.claude/skills/`.

## Requirements

- Python 3.9+
- `ffmpeg` on PATH (for `parse-audio-to-note` with video files)

## Skills

| Skill | Description |
|---|---|
| [save-link](skills/save-link) | Dispatcher: detects platform from URL and routes to the appropriate skill |
| [save-content-to-note](skills/save-content-to-note) | Shared: saves extracted JSON content as an Obsidian note (vault location, media, note format) |
| [parse-tweet-to-note](skills/parse-tweet-to-note) | Extract a tweet/X post with text and media, save as a note |
| [parse-instagram-post-to-note](skills/parse-instagram-post-to-note) | Extract an Instagram post with description and media, save as a note |
| [parse-reddit-post-to-note](skills/parse-reddit-post-to-note) | Extract a Reddit post with top comments and media, save as a note |
| [parse-article-to-note](skills/parse-article-to-note) | Extract any article, blog post, or documentation page, save as a note |
| [parse-youtube-video-to-note](skills/parse-youtube-video-to-note) | Download a YouTube video, transcribe with Whisper, save as a note with timecodes |
| [parse-audio-to-note](skills/parse-audio-to-note) | Transcribe a local audio or video file with Whisper, save as a note with transcript JSON |

## Usage

The simplest entry point is `save-link` — paste any URL and it routes automatically:

```
/save-link https://...
```

Or invoke a specific skill directly for more control.

## Configuration

Set environment variables to customize behavior:

| Variable | Default | Description |
|---|---|---|
| `NOTE_LANGUAGE` | `auto` | Note language: `auto` matches content language, or use a code like `en`, `ru` |
| `WHISPER_MODEL` | `base` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3` |
| `HF_TOKEN` | — | Hugging Face token to enable speaker diarization in `parse-audio-to-note` |
