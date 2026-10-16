# Morning Diff

A daily AI briefing for the phone: the last 24 hours of AI news and videos, rising AI projects and Claude skills, each as its own timeline.

- `index.html` is always the latest edition; `YYYY-MM-DD.html` keeps every day. The date picker opens any past day.
- Installable as an app (PWA) from the browser.
- Rebuilt every morning by a scheduled Claude task:
  1. `python3 -I tools/collect.py /tmp/candidates.json` gathers the last 24 hours from news feeds, Hacker News, Anthropic news, YouTube channel feeds, trendshift.io and skills.sh.
  2. Claude picks the 20–50 most relevant items and writes one-line summaries into an edition file.
  3. `python3 -I tools/build.py edition.json` adds exact times and preview images and writes the pages.
