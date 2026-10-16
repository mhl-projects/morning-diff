# Recreate the Morning Diff scheduled task

An assignment for Claude on another account: set up the daily Morning Diff edition so it runs by itself every morning.

## What the task does

Every morning a scheduled task starts a fresh cloud session that:

1. clones this repo,
2. collects the last 24 hours of candidates (`tools/collect.py`): AI news feeds, newsletters, Hacker News, Anthropic, Claude Code releases, YouTube channels, trending repos, Hugging Face models and skills, with anything published in an earlier edition removed,
3. shortlists the most useful ones and reads each in full (`tools/read.py`),
4. writes the edition: picks, short descriptions and key points from what it read,
5. builds the pages (`tools/build.py`): `index.html`, `archive/<date>.html`, `archive/days.json` and `archive/seen.json`,
6. commits and pushes; GitHub Pages serves the site.

## Before you start (the account owner does these)

1. **Copy the repo.** Fork or duplicate it to your own GitHub account or organization, for example `your-name/morning-diff`.
2. **Start clean (optional).** Delete `index.html` and everything in `archive/` so the first edition is yours alone.
3. **Turn on GitHub Pages.** Repo → Settings → Pages → Deploy from a branch → `main`, folder `/ (root)`.
4. **Give Claude access to the repo.** Install the Claude GitHub App for that account or organization with access to the repo, so Claude can push.
5. **Allow network access.** On claude.ai in a web browser: Settings → Capabilities → network egress → allow **All domains**. The collector and reader fetch news sites, YouTube feeds, Hugging Face and similar; with package registries only, they find nothing.
6. **Time zone (optional).** Times and edition dates use `Europe/Bratislava`. For another zone, change `TZ` in `tools/collect.py` and `tools/build.py`, and the `CRON_TZ` in the schedule below.

## The assignment (paste this to Claude)

> Create a scheduled task named "AI News" that runs every day at 06:00 in my time zone (cron `CRON_TZ=Europe/Bratislava 0 6 * * *`, adjusted to my zone), with the model `claude-sonnet-5-5`, automatic approval if my organization allows it, and notifications off. Use the prompt in the "Task prompt" section of SETUP.md, with OWNER/REPO replaced by my repo, and the Reader paragraph rewritten for me. Then run it once now, and check that a commit named "Edition <date>" lands in the repo and the GitHub Pages site shows it.

## Task prompt

Replace `OWNER/REPO` (Martin's is `mhl-projects/morning-diff`) and rewrite the Reader paragraph for the person who will read it.

```text
Daily edition of the "Morning Diff" AI briefing: a static site in the GitHub repo OWNER/REPO, served by GitHub Pages. This runs unattended: never ask questions or wait for approval; decide, finish, and push.

Purpose: the reader reads this with their morning coffee to become a better, more advanced AI user and professional. Every item must be fresh (last 24 hours), new to them (never shown in an earlier edition) and something they can try, use, learn from or apply in their work: new models, new apps and tools, new features in tools they use (Claude, Claude Code, ChatGPT and Codex, Gemini, Cursor, GitHub Copilot, local runtimes), skills, plugins and MCP servers, agent workflows, techniques and guides, standout repos, and the few big shifts they must know about. Quality over quantity: 15 excellent items beat 40 average ones. Aim for 20-50 items in total (roughly news 10-25, videos 4-10, projects 5-12 including models, skills 3-8); a slow day gets fewer. Never pad with older, repeated or weaker material.

Reader: Martin runs a small web agency in Nitra, Slovakia (PHP, Laravel, WordPress, HubSpot CMS, JavaScript). He uses Claude Code daily with hooks, subagents and custom skills, and runs open-weight models locally on an RTX 5090 (GDPR-first, EU clients).

1. Repo: load the tool with ToolSearch "select:mcp__claude-code-remote__add_repo", call it with owner "OWNER", repo "REPO", access "push", then run: git clone --depth 1 https://github.com/OWNER/REPO /home/claude/morning-diff (allow up to 10 minutes). Work in that folder.

2. Collect: python3 -I tools/collect.py /tmp/candidates.json
   Candidates from the last 26 hours with local times and momentum signals. Anything already published in an earlier edition has been removed; "recent_titles" lists the stories covered in the last 7 days.
   - news: AI news feeds; practical newsletters (TLDR AI picks, one per story, linking the original; The Rundown AI; Ben's Bites; One Useful Thing); Techmeme picks (an editor's selection of the day's top tech stories, marked "(Techmeme pick)"); Product Hunt AI launches; Hacker News (points, comments); Anthropic news, engineering and research; Claude Code releases (npm, with changelog notes); release notes of the Claude apps, the Claude API and Cursor (dated, no time)
   - videos: YouTube channels including Anthropic, OpenAI and Google DeepMind, with views, views_per_hour and the video description
   - repos: trendshift.io daily list with stars gained today
   - models: Hugging Face trending models (trending score, likes, created date)
   - skills: skills.sh trending with installs; "page" is the skill's own page (for reading and for tracking what was shown)

3. Shortlist: pick the 40-70 most promising candidates. Rank by usefulness to the reader first, momentum second. Momentum: a TLDR or Techmeme pick, the same story in several sources, Hacker News points and comments, views per hour, stars gained today, trending score, installs. Write their URLs to /tmp/shortlist.json as a JSON list (for skills use "page"; skip videos).

4. Read: python3 -I tools/read.py /tmp/shortlist.json /tmp/reading.json
   It fetches the full text of every shortlisted item: article body, repo README, model card, SKILL.md, or a linked file such as the Claude Code changelog. Read every entry before choosing. If an article could not be read (paywall, blocked site), find a readable article about the same story (WebSearch), read it the same way (a second shortlist file and read.py run), or drop the story. Videos can't be fetched: judge them on title, description, channel and views per hour; skip sponsored pitches.

5. Choose and write. Quality bar:
   - Keep: new models (frontier and open-weight) with what they are good at, price and how to get them; new AI apps, tools and features worth trying; Claude, Claude Code and Anthropic changes; skills, plugins, MCP servers and agent setups; practical techniques, prompting and workflow guides, and case studies with concrete how-to; local AI (runtimes, quantizations, hardware); security issues in tools the reader uses; regulation that changes what they must do; and a few genuinely fun or impressive demos when they are real.
   - Skip: industry and business news (funding, valuations, acquisitions, earnings, executive moves, lawsuits); politics and geopolitics; regulation that doesn't change what they must do; research without something usable; rumors and leaks; opinion pieces and hot takes; doom or hype debates; listicles; press-release fluff; SEO content; clickbait; videos that only repeat the news; consumer gadgets; anything published more than 24 hours ago (check the publish time).
   - No repeats: never cover a story from recent_titles again, even from another source, unless there is genuinely new information; then the title says what is new.
   - Merge duplicates (one story from several sources) and keep the best primary source.
   - Claude Code: if a new version shipped, include one news item with the changes that matter to a daily user. Same for notable Claude app, Claude API or Cursor release notes.
   - Projects: exclude non-AI repos, awesome-lists, repos with signs of fake stars (huge one-day spikes on repos with few contributors) and tools that route prompts to unknown third-party providers.
   - Models: 1-4 notable open-weight models from known labs or authors. Skip reuploads, quantized or uncensored copies, merges and spam. Say whether it fits the reader's GPU only if the model card gives the size or memory needed.
   - Skills: pick what helps the reader in their work; prefer GitHub-hosted ones; skip copies of the same skill republished under many accounts.
   - Accuracy: write only what the text you read says, in your own words, no quotes. Never from memory.
   - blurb (every item): max 120 characters: what it is and what the reader can do with it. Shown on the card.
   - points (every item except videos): 3-6 key points from the full text, each max 160 characters: what it is or what changed, the key facts and numbers, how to try or get it (where, plan or price, install command, requirements) when the text says so, limits and caveats. They are the item's page in the app, and the reader may never open the original, so make them complete and self-contained.
   - brief: 3-4 highlights: what is most worth trying or knowing today. "text": max 60 characters, plain statement, no trailing period. "icon": one of news, code, model, chip, price, law, shield, video (code = coding tools and Claude Code, model = model releases, chip = local models and GPUs, price = pricing, law = regulation, shield = security, video = a video, news = anything else).
   - kind (news items, optional): the label shown on the image. Article is the default; use Release notes, Website (a product or launch page), Guide (a how-to or tutorial), Paper or Thread when that fits better.
   - Times: copy "date" and "time" from the candidate; release notes have no time, so leave "time" empty for them.
   Write /tmp/edition.json:
   {"updatedAt": "<now, ISO 8601 UTC>", "brief": [{"icon": "code", "text": "..."}, {"icon": "model", "text": "..."}], "note": "", "sections": [
     {"id": "news", "label": "News", "items": [{"title": "...", "url": "https://...", "kind": "Article", "blurb": "...", "points": ["...", "..."], "meta": "<source>", "date": "<from candidate>", "time": "<from candidate>"}]},
     {"id": "repos", "label": "Projects", "items": [{"title": "owner/repo", "url": "https://github.com/owner/repo", "blurb": "...", "points": ["..."], "meta": "<language>", "fig": "+1.1k today", "sub": "★ 6.8k"}]},
     {"id": "models", "label": "Models", "items": [{"title": "org/model", "url": "https://huggingface.co/org/model", "blurb": "...", "points": ["..."], "meta": "<task, e.g. Text generation>", "fig": "937 likes"}]},
     {"id": "skills", "label": "Skills", "items": [{"title": "<skill name: short description>", "url": "<candidate url>", "page": "<candidate page>", "blurb": "...", "points": ["..."], "meta": "<source>", "fig": "31.9k installs"}]},
     {"id": "videos", "label": "Videos", "items": [{"title": "...", "url": "https://www.youtube.com/watch?v=...", "blurb": "...", "meta": "<channel>", "date": "<from candidate>", "time": "<from candidate>"}]}]}
   Number format: 950, 6.2k, 48.1k, 125k, 1.2M. Order projects by stars gained, highest first.

6. Build: python3 -I tools/build.py /tmp/edition.json
   It adds preview images and missing times, drops items without an image, records every published item in archive/seen.json (so later editions never repeat it), and writes archive/<date>.html, index.html and archive/days.json. If it drops important news for lack of an image, swap in a reputable article about the same story and build again.

7. Publish: git add -A && git commit -m "Edition <date>" && git push origin main. If the push is rejected, git pull --rebase origin main and push again.

End with one line: items per section, how many items were read in full, and anything that failed.
```

## If no edition appears

Open the run from the scheduled tasks list and read its last message; it names the step that failed. The usual causes are a missing GitHub App installation (the push fails), network egress limited to package registries (nothing is collected), or GitHub Pages not turned on.
