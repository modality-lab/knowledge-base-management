---
name: parse-article-to-note
description: Extract an article/blog/documentation page with text, images, and metadata, and save as an Obsidian note
---

Extract the article from the user's URL and save it as an Obsidian note in this vault.

## Instructions

### Step 1 — Set up environment

If `.venv` does not exist in this skill's directory, create it and install dependencies:

```bash
python3 -m venv <this-skill-dir>/.venv
<this-skill-dir>/.venv/bin/pip install -r <this-skill-dir>/requirements.txt
```

### Step 2 — Extract content

```bash
<this-skill-dir>/.venv/bin/python3 <this-skill-dir>/article_extractor.py "<url>"
```

Returns JSON: `url`, `platform` (`article`), `title`, `author`, `date`, `text`, `media`, `metadata` (`sitename`, `categories`, `tags`).

### Step 3 — Save as note

Invoke the `save-content-to-note` skill with the extracted JSON.
