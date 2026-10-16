# Morning Diff

A daily AI briefing for the phone: the last 24 hours of AI news and videos, rising AI projects and Claude skills, each as its own timeline.

- `index.html` is always the latest edition; `archive/` keeps every day (`archive/YYYY-MM-DD.html`). The date picker opens any past day.
- `assets/` holds the app icons and manifest; `tools/` the daily build scripts.
- Installable as an app (PWA) from the browser.
- Rebuilt every morning by a GitHub Actions workflow that runs Claude Code on a Claude subscription (`.github/workflows/edition.yml`, instructions in `tools/edition.md`, setup in `SETUP.md`):
  1. `tools/collect.py` gathers the last 24 hours from news feeds, newsletters, Hacker News, Anthropic, YouTube channels, trendshift.io, Hugging Face and skills.sh.
  2. `tools/read.py` fetches the full text of the shortlisted items; Claude picks the most useful and writes a description and key points for each.
  3. `tools/build.py` adds exact times and preview images and writes the pages.
