# Make today's Morning Diff edition

Instructions for Claude Code, run every morning by `.github/workflows/edition.yml`. Work in the repository root, unattended: never ask questions or wait for approval; decide and finish. The tools available are Read, Write, Edit, Glob, Grep, WebSearch, WebFetch and `python3` in the shell (the scripts below, and short inline snippets such as printing part of a JSON file). Keep every working file in `.work/`. Don't commit or push: the workflow publishes the result.

Purpose: the reader reads this with their morning coffee to become a better, more advanced AI user and professional. Every item must be fresh (last 24 hours), new to them (never shown in an earlier edition) and something they can try, use, learn from or apply in their work: new models, new apps and tools, new features in tools they use (Claude, Claude Code, ChatGPT and Codex, Gemini, Cursor, GitHub Copilot, local runtimes), skills, plugins and MCP servers, agent workflows, techniques and guides, standout repos, and the few big shifts they must know about. Quality over quantity: 15 excellent items beat 40 average ones. Aim for 20-50 items in total (roughly news 10-25, videos 4-10, projects 5-12 including models, skills 3-8); a slow day gets fewer. Never pad with older, repeated or weaker material.

Reader: Martin runs a small web agency in Nitra, Slovakia (PHP, Laravel, WordPress, HubSpot CMS, JavaScript). He uses Claude Code daily with hooks, subagents and custom skills, and runs open-weight models locally on a single RTX 5090 (32 GB). He works GDPR-first for EU clients, so EU AI Act or GDPR changes that change what he must do for clients matter. Skills that help him: web dev, PHP/Laravel/WordPress, frontend, testing, code review, security, debugging, documents, SEO and skill authoring.

1. Collect: `python3 -I tools/collect.py .work/candidates.json`
   Candidates from the last 26 hours with local times and momentum signals. Anything already published in an earlier edition has been removed; "recent_titles" lists the stories covered in the last 7 days.
   - news: AI news feeds; practical newsletters (TLDR AI picks, one per story, linking the original; The Rundown AI; Ben's Bites; One Useful Thing); Techmeme picks (an editor's selection of the day's top tech stories, marked "(Techmeme pick)"); Product Hunt AI launches; Hacker News (points, comments); Anthropic news, engineering and research; Claude Code releases (npm, with changelog notes); release notes of the Claude apps, the Claude API and Cursor (dated, no time)
   - videos: YouTube channels including Anthropic, OpenAI and Google DeepMind, with views, views_per_hour and the video description
   - repos: trendshift.io daily list with stars gained today
   - models: Hugging Face trending models (trending score, likes, created date)
   - skills: skills.sh trending with installs; "page" is the skill's own page (for reading and for tracking what was shown)

2. Shortlist: pick the 40-70 most promising candidates. Rank by usefulness to the reader first, momentum second. Momentum: a TLDR or Techmeme pick, the same story in several sources, Hacker News points and comments, views per hour, stars gained today, trending score, installs. Write their URLs to `.work/shortlist.json` as a JSON list (for skills use "page"; skip videos).

3. Read: `python3 -I tools/read.py .work/shortlist.json .work/reading.json`
   It fetches the full text of every shortlisted item: article body, repo README, model card, SKILL.md, or a linked file such as the Claude Code changelog. Read every entry before choosing. If an article could not be read (paywall, blocked site), find a readable article about the same story (WebSearch), read it the same way (a second shortlist file and read.py run), or drop the story. Videos can't be fetched: judge them on title, description, channel and views per hour; skip sponsored pitches.

4. Choose and write. Quality bar:
   - Keep: new models (frontier and open-weight) with what they are good at, price and how to get them; new AI apps, tools and features worth trying; Claude, Claude Code and Anthropic changes; skills, plugins, MCP servers and agent setups; practical techniques, prompting and workflow guides, and case studies with concrete how-to; local AI (runtimes, quantizations, hardware); security issues in tools the reader uses; regulation that changes what they must do; and a few genuinely fun or impressive demos when they are real.
   - Skip: industry and business news (funding, valuations, acquisitions, earnings, executive moves, lawsuits); politics and geopolitics; regulation that doesn't change what they must do; research without something usable; rumors and leaks; opinion pieces and hot takes; doom or hype debates; listicles; press-release fluff; SEO content; clickbait; videos that only repeat the news; consumer gadgets; anything published more than 24 hours ago (check the publish time).
   - No repeats: never cover a story from recent_titles again, even from another source, unless there is genuinely new information; then the title says what is new.
   - Merge duplicates (one story from several sources) and keep the best primary source.
   - Claude Code: if a new version shipped, include one news item with the changes that matter to a daily user. Same for notable Claude app, Claude API or Cursor release notes.
   - Projects: exclude non-AI repos, awesome-lists, repos with signs of fake stars (huge one-day spikes on repos with few contributors, e.g. morluto/rea) and tools that route prompts to unknown third-party providers.
   - Models: 1-4 notable open-weight models from known labs or authors. Skip reuploads, quantized or uncensored copies, merges and spam. Say whether it fits the reader's GPU only if the model card gives the size or memory needed.
   - Skills: pick what helps the reader in their work; prefer GitHub-hosted ones; skip copies of the same skill republished under many accounts.
   - Accuracy: write only what the text you read says, in your own words, no quotes. Never from memory.
   - blurb (every item): max 120 characters: what it is and what the reader can do with it. Shown on the card.
   - points (every item except videos): 3-6 key points from the full text, each max 160 characters: what it is or what changed, the key facts and numbers, how to try or get it (where, plan or price, install command, requirements) when the text says so, limits and caveats. They are the item's page in the app, and the reader may never open the original, so make them complete and self-contained.
   - brief: 3-4 highlights: what is most worth trying or knowing today, each about one item of the edition. "url": that item's "url" ("page" for a skill), so tapping the highlight opens it. "text": max 60 characters, plain statement, no trailing period. "icon": one of news, code, model, chip, price, law, shield, video (code = coding tools and Claude Code, model = model releases, chip = local models and GPUs, price = pricing, law = regulation, shield = security, video = a video, news = anything else).
   - kind (news items, optional): the label shown on the image. Article is the default; use Release notes, Website (a product or launch page), Guide (a how-to or tutorial), Paper or Thread when that fits better.
   - Times: copy "date" and "time" from the candidate; release notes have no time, so leave "time" empty for them.
   Write `.work/edition.json`:
   {"updatedAt": "<now, ISO 8601 UTC>", "brief": [{"icon": "code", "text": "...", "url": "<the item's url>"}, {"icon": "model", "text": "...", "url": "<the item's url>"}], "note": "", "sections": [
     {"id": "news", "label": "News", "items": [{"title": "...", "url": "https://...", "kind": "Article", "blurb": "...", "points": ["...", "..."], "meta": "<source>", "date": "<from candidate>", "time": "<from candidate>"}]},
     {"id": "repos", "label": "Projects", "items": [{"title": "owner/repo", "url": "https://github.com/owner/repo", "blurb": "...", "points": ["..."], "meta": "<language>", "fig": "+1.1k today", "sub": "★ 6.8k"}]},
     {"id": "models", "label": "Models", "items": [{"title": "org/model", "url": "https://huggingface.co/org/model", "blurb": "...", "points": ["..."], "meta": "<task, e.g. Text generation>", "fig": "937 likes"}]},
     {"id": "skills", "label": "Skills", "items": [{"title": "<skill name: short description>", "url": "<candidate url>", "page": "<candidate page>", "blurb": "...", "points": ["..."], "meta": "<source>", "fig": "31.9k installs"}]},
     {"id": "videos", "label": "Videos", "items": [{"title": "...", "url": "https://www.youtube.com/watch?v=...", "blurb": "...", "meta": "<channel>", "date": "<from candidate>", "time": "<from candidate>"}]}]}
   Number format: 950, 6.2k, 48.1k, 125k, 1.2M. Order projects by stars gained, highest first.

5. Build: `python3 -I tools/build.py .work/edition.json`
   It adds preview images and missing times, drops items without an image, records every published item in archive/seen.json (so later editions never repeat it), and writes archive/<date>.html, index.html and archive/days.json. If it drops important news for lack of an image, swap in a reputable article about the same story and build again.

End with one line: items per section, how many items were read in full, and anything that failed.
