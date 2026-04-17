---
name: parse-instagram-post-to-note
description: Extract an Instagram post with description, media, and metadata, and save as an Obsidian note
---

Extract the Instagram post from the user's URL and save it as an Obsidian note in this vault.

## Instructions

### Step 1 — Set up environment

If `.venv` does not exist in this skill's directory, create it and install dependencies:

```bash
python3 -m venv <this-skill-dir>/.venv
<this-skill-dir>/.venv/bin/pip install -r <this-skill-dir>/requirements.txt
```

### Step 2 — Extract content

```bash
<this-skill-dir>/.venv/bin/python3 <this-skill-dir>/instagram_extractor.py "<url>"
```

Returns JSON: `url`, `platform` (`instagram`), `title`, `author`, `date`, `text`, `media`, `metadata`.

### Step 3 — Save as note

Invoke the `save-content-to-note` skill with the extracted JSON.
