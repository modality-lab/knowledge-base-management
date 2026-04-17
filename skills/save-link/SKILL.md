---
name: save-link
description: Extract content from a URL and save it as an Obsidian note in the right vault location
---

Save the URL from the user's message as a structured Obsidian note. This skill is a dispatcher — it determines the platform from the URL and delegates to the appropriate specialized skill.

## Instructions

1. **Determine platform** from the URL:

   | URL pattern | Skill to invoke |
   |---|---|
   | `twitter.com`, `x.com` | `parse-tweet-to-note` |
   | `instagram.com` | `parse-instagram-post-to-note` |
   | `youtube.com`, `youtu.be` | `parse-youtube-video-to-note` |
   | `reddit.com` | `parse-reddit-post-to-note` |
   | Everything else | `parse-article-to-note` |

2. **Invoke the corresponding skill** with the user's URL.
