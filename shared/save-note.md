# Save as Obsidian Note

Save the extracted content JSON as a structured Obsidian note.

**Env vars:**
- `NOTE_LANGUAGE` — note language: `auto` (default, matches content language), or a language code like `en`, `ru`

## Step 1 — Review media

Read any files listed in the `media` array of the JSON to understand the visual content before writing the note.

## Step 2 — Choose vault location

Use `ls` to explore the vault and find the best existing folder for this content. If there are multiple appropriate locations, ask the user to choose.

## Step 3 — Copy media

Copy all media files (images, videos) to `<target-folder>/attachments/` with descriptive filenames.

## Step 4 — Create the note

Create `<target-folder>/<descriptive-title>.md`:

```markdown
---
source: "<url>"
platform: <platform>
author: "<author>"
date_published: <date>
date_saved: <today>
tags:
  - source/<platform>
  - topic/<topic>
---

## Content
<text>

## Media
![[attachments/<filename>|700]]

## Analysis
<key takeaways, why this is relevant>

## Related
- [[<related existing note>]]
```

**Rules:**
- `NOTE_LANGUAGE=auto` (default): write the note in the same language as the content
- `NOTE_LANGUAGE=en` / `ru` / etc.: write the note in the specified language regardless of content language
- Use `|700` width on all image embeds
- Omit `## Media` if there are no media files
- Omit `## Related` entry if no related notes come to mind — leave the section header but empty
