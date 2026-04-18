---
name: note-reddit
description: Extract a Reddit post with text, top comments, media, and save as an Obsidian note
---

Extract the Reddit post from the user's URL and save it as an Obsidian note in this vault.

## Instructions

### Step 1 — Check system dependencies

```bash
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required but not found on PATH"; exit 1; }
```

### Step 2 — Set up environment

If `.venv` does not exist in this skill's directory, create it and install dependencies:

```bash
python3 -m venv <this-skill-dir>/.venv
<this-skill-dir>/.venv/bin/pip install -r <this-skill-dir>/requirements.txt
```

### Step 3 — Extract content

```bash
<this-skill-dir>/.venv/bin/python3 <this-skill-dir>/reddit_extractor.py "<url>"
```

Returns JSON: `url`, `platform` (`reddit`), `title`, `author` (`u/handle`), `date`, `text` (post + top 5 comments), `media`, `metadata` (`score`, `upvote_ratio`, `num_comments`, `subreddit`).

### Step 4 — Save as note

Read `<this-skill-dir>/../shared/save-note.md` and follow its instructions to save the note.
