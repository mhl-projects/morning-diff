# Run Morning Diff on your own account

Every morning a GitHub Actions workflow (`.github/workflows/edition.yml`) runs Claude Code on your Claude subscription. It:

1. collects the last 24 hours of candidates (`tools/collect.py`): AI news feeds, newsletters, Hacker News, Anthropic, Claude Code releases, YouTube channels, trending repos, Hugging Face models and skills, with anything published in an earlier edition removed,
2. shortlists the most useful ones and reads each in full (`tools/read.py`),
3. writes the edition: picks, short descriptions and key points from what it read,
4. builds the pages (`tools/build.py`): `index.html`, `archive/<date>.html`, `archive/days.json` and `archive/seen.json`,
5. commits them and starts a GitHub Pages build.

Claude's instructions for steps 1-4 are in `tools/edition.md`. Claude works with a read-only token; a second job, without Claude, commits and publishes.

## Set up (once)

1. **Copy the repo** to your own GitHub account or organization, for example `your-name/morning-diff`.
2. **Start clean (optional).** Delete `index.html` and everything in `archive/`, so the first edition is yours alone.
3. **Turn on GitHub Pages.** Repo → Settings → Pages → Deploy from a branch → `main`, folder `/ (root)`.
4. **Make a token.** On a computer with Claude Code, signed in to a Pro, Max, Team or Enterprise plan, run `claude setup-token`, approve in the browser and copy the token it prints. It lasts one year.
5. **Add the token as a secret.** Repo → Settings → Secrets and variables → Actions → New repository secret, named `CLAUDE_CODE_OAUTH_TOKEN`.
6. **Make it yours.** In `tools/edition.md`, rewrite the Reader paragraph for the person who'll read it. For a time zone other than `Europe/Bratislava`, change `TZ` in `tools/collect.py` and `tools/build.py`, and the time zone and hours in the workflow.
7. **First edition.** Actions tab → Morning Diff edition → Run workflow. About 20-30 minutes later a commit named "Edition <date>" lands and the site shows it.

## Every morning

The edition is made at 05:23 Nitra time, so it's ready by 06:00. GitHub schedules run on UTC, so the workflow runs at 03:23, 04:23 and 05:23 UTC and keeps the first run that falls at or after 05:00 local time; later runs only retry a morning that failed. Runs count against your Claude plan's usage limits; there's no API billing.

## Once a year

The token expires after a year. Run `claude setup-token` again and replace the secret.

## If no edition appears

Open the Actions tab and the latest "Morning Diff edition" run. The "Check the build" step shows Claude's last message, which names what failed. The usual causes are a missing or expired token, Actions turned off for the repo, GitHub Pages not turned on, or the plan's usage limit reached at that hour.
