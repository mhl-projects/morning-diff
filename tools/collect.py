# Collect candidates from the last 24 hours into one compact JSON, so Claude only has to pick and summarise.
# Sources: news feeds (incl. Techmeme's AI stories), Hacker News, Anthropic news/engineering/research, Claude Code releases (npm),
# YouTube channel feeds (with views per hour), trendshift.io (repos), Hugging Face trending models, skills.sh (skills).
# Also: practical newsletters (TLDR AI picks, The Rundown, Ben's Bites, One Useful Thing), Product Hunt AI launches,
# and release notes of Claude (apps, API) and Cursor.
# Momentum signals for ranking: HN points, Techmeme/TLDR pick, views per hour, stars gained today, trending score, installs.
# Usage: python3 -I collect.py candidates.json
import datetime, email.utils, html, json, pathlib, re, subprocess, sys, time, zoneinfo
import xml.etree.ElementTree as ET

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
HOURS = 26
FEEDS = [("OpenAI", "https://openai.com/news/rss.xml"), ("Google", "https://blog.google/technology/ai/rss/"),
         ("Google DeepMind", "https://deepmind.google/blog/rss.xml"), ("GitHub Changelog", "https://github.blog/changelog/feed/"),
         ("Hugging Face", "https://huggingface.co/blog/feed.xml"), ("Simon Willison", "https://simonwillison.net/atom/everything/"),
         ("Latent Space", "https://www.latent.space/feed"), ("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/"),
         ("The Verge", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"), ("Interconnects", "https://www.interconnects.ai/feed"),
         ("Ars Technica", "https://arstechnica.com/ai/feed/"), ("The Decoder", "https://the-decoder.com/feed/"),
         ("EU AI Act Newsletter", "https://artificialintelligenceact.substack.com/feed"), ("Import AI", "https://importai.substack.com/feed"),
         ("The Rundown AI", "https://www.therundown.ai/feed"), ("Ben's Bites", "https://www.bensbites.com/feed"),
         ("One Useful Thing", "https://www.oneusefulthing.org/feed"),
         ("Techmeme", "https://www.techmeme.com/feed.xml"), ("Product Hunt", "https://www.producthunt.com/feed")]
GENERAL = {"Techmeme", "Product Hunt"}  # cover all of tech: only their AI items are kept
# Release notes of tools Martin uses: dated sections, kept when dated today or yesterday (no times given).
NOTES = [("Claude apps release notes", "https://docs.claude.com/en/release-notes/claude-apps"),
         ("Claude API release notes", "https://docs.claude.com/en/release-notes/api"), ("Cursor changelog", "https://cursor.com/changelog")]
DATE = r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? (\d{1,2}), (20\d\d)\b"
CHANNELS = {"AI Explained": "UCNJ1Ymd5yFuUPtn21xtRbbw", "The AI Daily Brief": "UCKelCK4ZaO6HeEI1KQjqzWA",
            "Fireship": "UCsBjURrPoezykLs9EqgamOA", "Theo - t3.gg": "UCbRP3c757lWg9M-U7TyEkXA",
            "IndyDevDan": "UC_x36zCEGilGpB1m-V4gmjg", "Cole Medin": "UCMwVTLZIRRUyyVrkjDpn4pA",
            "AICodeKing": "UC0m81bQuthaQZmFbXEY9QSw", "AI Engineer": "UCLKPca3kwwd-B59HNr-_lvA",
            "Two Minute Papers": "UCbfYPyITQ-7l4upoX8nvctg", "Sam Witteveen": "UC55ODQSvARtgSyc8ThfiepQ",
            "Alex Ziskind": "UCajiMK_CY9icRhLepS8_3ug", "Fahd Mirza": "UCPix8N6PMRI4KzgyjuZeF0g",
            "Digital Spaceport": "UCiaQzXI5528Il6r2NNkrkJA", "Anthropic": "UCrDwWp7EBBv4NwvScIpBDOA",
            "OpenAI": "UCXZCJLdBC09xxGZ6gcdrc6A", "Google DeepMind": "UCP7jMXSY2xbc3KCAE0MHQ-A",
            "Andrej Karpathy": "UCXUPKJO5MZQN11PqgIvyuvQ", "Dwarkesh Patel": "UCXl4i9dYBrFOabk0xGmbkRA",
            "bycloud": "UCgfe2ooZD3VJPB6aJAnuQng", "Matt Wolfe": "UChpleBmo18P08aKCIgti38g",
            "Prompt Engineering": "UCDq7SjbgRKty5TgGafW8Clg", "Latent Space": "UCxBcwypKK-W3GHd_RZ9FZrQ",
            "AI Jason": "UCrXSVX9a1mj8l0CMLwKgMVw", "Matt Pocock": "UCswG6FSbgZjbWtdf_hMLaow",
            "The PrimeTime": "UCUyeluBRhGPCW4rPe_UvBZQ", "NetworkChuck": "UC9x0AN7BWHpCDHSm9NiJFJQ",
            "Jeff Geerling": "UCR-DXc1voovS8nhAvccRZhg"}
AI_WORDS = re.compile(r"\b(AI|A\.I\.|LLMs?|GPT[\w.-]*|Claude|Anthropic|OpenAI|Gemini|DeepMind|Llama|Mistral|Qwen|DeepSeek|Kimi|"
                      r"agents?|agentic|MCP|inference|models?|chatbots?|Copilot|Cursor|Codex|diffusion|transformers?|RAG|GPU|NVIDIA)\b", re.I)

now = datetime.datetime.now(datetime.timezone.utc)
since = now - datetime.timedelta(hours=HOURS)

def get(url, tries=2):
    for i in range(tries):  # one retry: listing sites sometimes answer 429 or time out
        r = subprocess.run(["curl", "-sfL", "--max-time", "25", "--max-filesize", "6000000", "-A", UA, url], capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout.decode("utf-8", "ignore")
        time.sleep(3)
    return ""

def when(s):
    s = (s or "").strip()
    try:
        dt = email.utils.parsedate_to_datetime(s) if s[:3].isalpha() else datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)
    except (TypeError, ValueError):
        return None

def text(s, n=300):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()[:n]

def feed_entries(xml):
    """Yield (title, link, published, summary, views) from RSS or Atom; views only for YouTube."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        f = {c.tag.split("}")[-1]: c for c in el}
        link = f.get("link")
        href = (link.get("href") or link.text) if link is not None else ""
        for c in el:  # Atom: prefer rel="alternate"
            if c.tag.endswith("link") and c.get("rel") in (None, "alternate") and c.get("href"):
                href = c.get("href")
                break
        pub = next((f[k].text for k in ("published", "pubDate", "updated", "date") if k in f and f[k].text), "")
        summ = next((f[k].text for k in ("description", "summary", "content") if k in f and (f[k].text or "").strip()), "")
        if "group" in f and not summ:  # YouTube: media:group/media:description
            d = next((c for c in f["group"] if c.tag.endswith("description")), None)
            summ = d.text if d is not None else ""
        views = next((c.get("views") for c in el.iter() if c.tag.endswith("statistics")), None)
        yield (f["title"].text if "title" in f else ""), (href or "").strip(), when(pub), summ, int(views or 0)

out = {"collected_at": now.isoformat(timespec="seconds"), "news": [], "videos": [], "repos": [], "models": [], "skills": []}

for source, url in FEEDS:
    for title, link, pub, summ, _ in feed_entries(get(url)):
        if not (pub and pub >= since and link.startswith("https://")):
            continue
        src = source
        if source in GENERAL and not AI_WORDS.search(f"{title} {text(summ)}"):
            continue
        if source == "Techmeme":  # an editor's pick of the day's top stories: link the original article
            link = next((u for u in re.findall(r'HREF="(https://[^"]+)"', summ or "", re.I) if "techmeme.com" not in u), link)
            name = re.search(r">([^<>]+)</A>:", summ or "", re.I)
            src = (name.group(1).strip() if name else "Techmeme") + " (Techmeme pick)"
        out["news"].append({"source": src, "title": text(title, 160), "url": link, "time": pub.isoformat(), "summary": text(summ)})

hn = get(f"https://hn.algolia.com/api/v1/search?tags=story&numericFilters=created_at_i>{int(since.timestamp())},points>40&hitsPerPage=200")
for h in (json.loads(hn).get("hits", []) if hn else []):
    if h.get("url", "").startswith("https://") and AI_WORDS.search(h.get("title", "")):
        out["news"].append({"source": "Hacker News", "title": text(h["title"], 160), "url": h["url"], "time": h["created_at"],
                            "summary": f"{h.get('points', 0)} points, {h.get('num_comments', 0)} comments on Hacker News"})

for section in ("news", "engineering", "research"):
    an = get(f"https://www.anthropic.com/{section}").replace('\\"', '"')
    for pub, slug in dict.fromkeys(re.findall(r'"publishedOn":"([^"]+)","slug":\{"_type":"slug","current":"([\w-]+)"', an)):
        t = when(pub)
        if t and t >= since:
            page = get(f"https://www.anthropic.com/{section}/{slug}")
            og = lambda p: text((re.search(rf'<meta[^>]+property="og:{p}"[^>]+content="([^"]*)"', page) or [None, ""])[1])
            out["news"].append({"source": "Anthropic", "title": og("title") or slug, "url": f"https://www.anthropic.com/{section}/{slug}",
                                "time": t.isoformat(), "summary": og("description")})

for source, url in NOTES:  # one candidate per page with the sections dated today or yesterday
    page = text(re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", get(url)), 2_000_000)
    parts, best = re.split(DATE, page), {}
    for mon, day, year, body in zip(parts[1::4], parts[2::4], parts[3::4], parts[4::4]):
        d = datetime.datetime.strptime(f"{mon} {day} {year}", "%b %d %Y").replace(tzinfo=datetime.timezone.utc)
        # dates in the future are deadlines mentioned in the text; a table of contents repeats dates with little text
        if since.date() <= d.date() <= now.date() and len(body) > len(best.get(d, "")):
            best[d] = body.strip()
    if best:
        out["news"].append({"source": source, "title": source, "url": url, "time": max(best).isoformat(), "date_only": True,
                            "summary": " | ".join(f"{d:%b} {d.day}: {body[:1200]}" for d, body in sorted(best.items(), reverse=True))})

# TLDR AI: the latest daily issue, one candidate per story (sponsors skipped), linking the original.
issue = max(feed_entries(get("https://tldr.tech/api/rss/ai")), key=lambda e: e[2] or since, default=None)
if issue and issue[2] and issue[2] >= now - datetime.timedelta(hours=36):
    for art in re.findall(r"(?is)<article\b.*?</article>", get(issue[1])):
        href, h3 = re.search(r'href="([^"]+)"', art), re.search(r"(?is)<h3[^>]*>(.*?)</h3>", art)
        body = re.search(r'(?is)class="newsletter-html"[^>]*>(.*?)</div>', art)
        title = text(h3.group(1) if h3 else "")
        if href and title and "(Sponsor)" not in title:
            out["news"].append({"source": "TLDR AI pick", "title": re.sub(r"\s*\(\d+ minute read\)$", "", title),
                                "url": re.sub(r"[?&]utm_[^&#]*", "", html.unescape(html.unescape(href.group(1)))).rstrip("?&"),
                                "time": issue[2].isoformat(), "summary": text(body.group(1) if body else "")})

# Claude Code releases: exact publish times from npm, release notes from the changelog. One candidate for the day's versions.
npm = get("https://registry.npmjs.org/@anthropic-ai/claude-code")
stamps = json.loads(npm).get("time", {}) if npm.startswith("{") else {}
versions = sorted((t, v) for v, s in stamps.items() if re.fullmatch(r"\d+\.\d+\.\d+", v) and (t := when(s)) and t >= since)
if versions:
    changelog = get("https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md")
    notes = [m.group(1) for _, v in versions for m in [re.search(rf"^## {re.escape(v)}\s*$(.*?)(?=^## |\Z)", changelog, re.S | re.M)] if m]
    out["news"].append({"source": "Claude Code", "title": "Claude Code " + ", ".join(v for _, v in versions),
                        "url": "https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md", "time": versions[-1][0].isoformat(),
                        "summary": text(" ".join(notes), 2500)})

def yt_feed(cid):
    for wait in (1, 4, 10):  # YouTube answers bursts with 429: back off and retry
        time.sleep(wait)
        xml = get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", tries=1)
        if xml:
            return xml
    print("feed unavailable:", cid, file=sys.stderr)
    return ""

for name, cid in CHANNELS.items():
    for title, link, pub, summ, views in feed_entries(yt_feed(cid)):
        if pub and pub >= since and "/shorts/" not in link:
            hours = max(1.0, (now - pub).total_seconds() / 3600)
            out["videos"].append({"channel": name, "title": text(title, 160), "url": link, "time": pub.isoformat(),
                                  "views": views, "views_per_hour": round(views / hours), "summary": text(summ)})

ts = get("https://trendshift.io/").replace('\\"', '"')
for obj in re.findall(r'\{"id":\d+,"date":"[^"]*","rank":\d+.*?\}', ts):
    try:
        r = json.loads(obj)
    except ValueError:
        continue
    if r.get("repository_stars", 0) >= 1000:
        out["repos"].append({"repo": r["full_name"], "url": f"https://github.com/{r['full_name']}", "language": r.get("language") or "",
                             "stars": r["repository_stars"], "stars_today": r.get("repository_stars_gained", 0),
                             "created": (r.get("repository_created_at") or "")[:10], "summary": text(r.get("repository_description"))})

hf = get("https://huggingface.co/api/models?sort=trendingScore&limit=30")
for m in (json.loads(hf) if hf.startswith("[") else []):
    out["models"].append({"model": m["id"], "url": f"https://huggingface.co/{m['id']}", "task": m.get("pipeline_tag") or "",
                          "trending": m.get("trendingScore", 0), "likes": m.get("likes", 0), "downloads": m.get("downloads", 0),
                          "created": (m.get("createdAt") or "")[:10]})

sk = get("https://skills.sh/trending").replace('\\"', '"')
m = re.search(r'"initialSkills":(\[.*?\])', sk)
for s in (json.loads(m.group(1)) if m else [])[:60]:
    src = s["source"]
    repo = re.fullmatch(r"[\w.-]+/[\w.-]+", src) and "." not in src.split("/")[0]
    out["skills"].append({"skill": s["name"], "source": src, "installs": s["installs"], "page": f"https://skills.sh/{src}/{s['skillId']}",
                          "url": f"https://github.com/{src}" if repo else f"https://skills.sh/{src}/{s['skillId']}"})

TZ = zoneinfo.ZoneInfo("Europe/Bratislava")
# Nothing published on an earlier day comes back: drop candidates already in archive/seen.json (written by build.py).
published_file = pathlib.Path(__file__).resolve().parent.parent / "archive" / "seen.json"
published = json.loads(published_file.read_text()) if published_file.exists() else {}
today = now.astimezone(TZ).date().isoformat()
norm = lambda u: re.sub(r"#.*$|[?&]utm_[^&#]*", "", u or "").rstrip("/?")
old = lambda u: published.get(norm(u), {}).get("date", today) < today
for key in ("news", "videos", "repos", "models"):
    out[key] = [i for i in out[key] if not old(i["url"])]
out["skills"] = [s for s in out["skills"] if not old(s["page"])]  # skills are tracked by their own page: one repo holds many
week_ago = (now - datetime.timedelta(days=7)).astimezone(TZ).date().isoformat()
out["recent_titles"] = sorted({v["title"] for v in published.values() if week_ago <= v["date"] < today})  # stories already covered
seen = set()
for key in ("news", "videos"):
    items = []
    for it in sorted(out[key], key=lambda i: i["time"], reverse=True):
        t = datetime.datetime.fromisoformat(it["time"].replace("Z", "+00:00")).astimezone(TZ)
        it["date"], it["time"] = t.date().isoformat(), "" if it.pop("date_only", False) else t.strftime("%H:%M")  # Nitra time
        k = re.sub(r"#.*$|[?&]utm_[^&#]*", "", it["url"]).rstrip("/?")  # keep ?v= for YouTube
        if k not in seen:
            seen.add(k)
            items.append(it)
    out[key] = items
pathlib.Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1))
print({k: len(v) for k, v in out.items() if isinstance(v, list)}, f"| {len(json.dumps(out)) // 1000} KB")
