# Collect candidates from the last 24 hours into one compact JSON, so Claude only has to pick and summarise.
# Sources: news feeds, Hacker News, Anthropic news, YouTube channel feeds, trendshift.io (repos), skills.sh (skills).
# Usage: python3 -I collect.py candidates.json
import datetime, email.utils, html, json, pathlib, re, subprocess, sys, time, zoneinfo
import xml.etree.ElementTree as ET

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
HOURS = 26
FEEDS = [("OpenAI", "https://openai.com/news/rss.xml"), ("Google", "https://blog.google/technology/ai/rss/"),
         ("Google DeepMind", "https://deepmind.google/blog/rss.xml"), ("GitHub Changelog", "https://github.blog/changelog/feed/"),
         ("Hugging Face", "https://huggingface.co/blog/feed.xml"), ("Simon Willison", "https://simonwillison.net/atom/everything/"),
         ("Latent Space", "https://www.latent.space/feed"), ("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/"),
         ("The Verge", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"), ("MarkTechPost", "https://www.marktechpost.com/feed/"),
         ("Ars Technica", "https://arstechnica.com/ai/feed/"), ("The Decoder", "https://the-decoder.com/feed/"),
         ("EU AI Act Newsletter", "https://artificialintelligenceact.substack.com/feed")]
CHANNELS = {"AI Explained": "UCNJ1Ymd5yFuUPtn21xtRbbw", "The AI Daily Brief": "UCKelCK4ZaO6HeEI1KQjqzWA",
            "Fireship": "UCsBjURrPoezykLs9EqgamOA", "Theo - t3.gg": "UCbRP3c757lWg9M-U7TyEkXA",
            "IndyDevDan": "UC_x36zCEGilGpB1m-V4gmjg", "Cole Medin": "UCMwVTLZIRRUyyVrkjDpn4pA",
            "AICodeKing": "UC0m81bQuthaQZmFbXEY9QSw", "AI Engineer": "UCLKPca3kwwd-B59HNr-_lvA",
            "Two Minute Papers": "UCbfYPyITQ-7l4upoX8nvctg", "Sam Witteveen": "UC55ODQSvARtgSyc8ThfiepQ",
            "Alex Ziskind": "UCajiMK_CY9icRhLepS8_3ug", "Fahd Mirza": "UCPix8N6PMRI4KzgyjuZeF0g",
            "Digital Spaceport": "UCiaQzXI5528Il6r2NNkrkJA"}
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
    """Yield (title, link, published, summary) from RSS or Atom."""
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
        summ = next((f[k].text for k in ("description", "summary", "content", "group") if k in f and f[k].text), "")
        if "group" in f and not summ:  # YouTube: media:group/media:description
            d = next((c for c in f["group"] if c.tag.endswith("description")), None)
            summ = d.text if d is not None else ""
        yield (f["title"].text if "title" in f else ""), (href or "").strip(), when(pub), summ

out = {"collected_at": now.isoformat(timespec="seconds"), "news": [], "videos": [], "repos": [], "skills": []}

for source, url in FEEDS:
    for title, link, pub, summ in feed_entries(get(url)):
        if pub and pub >= since and link.startswith("https://"):
            out["news"].append({"source": source, "title": text(title, 160), "url": link, "time": pub.isoformat(), "summary": text(summ)})

hn = get(f"https://hn.algolia.com/api/v1/search?tags=story&numericFilters=created_at_i>{int(since.timestamp())},points>40&hitsPerPage=200")
for h in (json.loads(hn).get("hits", []) if hn else []):
    if h.get("url", "").startswith("https://") and AI_WORDS.search(h.get("title", "")):
        out["news"].append({"source": "Hacker News", "title": text(h["title"], 160), "url": h["url"], "time": h["created_at"],
                            "summary": f"{h.get('points', 0)} points, {h.get('num_comments', 0)} comments on Hacker News"})

an = get("https://www.anthropic.com/news").replace('\\"', '"')
for pub, slug in dict.fromkeys(re.findall(r'"publishedOn":"([^"]+)","slug":\{"_type":"slug","current":"([\w-]+)"', an)):
    t = when(pub)
    if t and t >= since:
        page = get(f"https://www.anthropic.com/news/{slug}")
        og = lambda p: text((re.search(rf'<meta[^>]+property="og:{p}"[^>]+content="([^"]*)"', page) or [None, ""])[1])
        out["news"].append({"source": "Anthropic", "title": og("title") or slug, "url": f"https://www.anthropic.com/news/{slug}",
                            "time": t.isoformat(), "summary": og("description")})

def yt_feed(cid):
    for wait in (1, 4, 10):  # YouTube answers bursts with 429: back off and retry
        time.sleep(wait)
        xml = get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", tries=1)
        if xml:
            return xml
    print("feed unavailable:", cid, file=sys.stderr)
    return ""

for name, cid in CHANNELS.items():
    for title, link, pub, summ in feed_entries(yt_feed(cid)):
        if pub and pub >= since and "/shorts/" not in link:
            out["videos"].append({"channel": name, "title": text(title, 160), "url": link, "time": pub.isoformat(), "summary": text(summ)})

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

sk = get("https://skills.sh/trending").replace('\\"', '"')
m = re.search(r'"initialSkills":(\[.*?\])', sk)
for s in (json.loads(m.group(1)) if m else [])[:60]:
    src = s["source"]
    repo = re.fullmatch(r"[\w.-]+/[\w.-]+", src) and "." not in src.split("/")[0]
    out["skills"].append({"skill": s["name"], "source": src, "installs": s["installs"],
                          "url": f"https://github.com/{src}" if repo else f"https://skills.sh/{src}/{s['skillId']}"})

TZ = zoneinfo.ZoneInfo("Europe/Bratislava")
seen = set()
for key in ("news", "videos"):
    items = []
    for it in sorted(out[key], key=lambda i: i["time"], reverse=True):
        t = datetime.datetime.fromisoformat(it["time"].replace("Z", "+00:00")).astimezone(TZ)
        it["date"], it["time"] = t.date().isoformat(), t.strftime("%H:%M")  # Nitra time
        k = re.sub(r"#.*$|[?&]utm_[^&#]*", "", it["url"]).rstrip("/?")  # keep ?v= for YouTube
        if k not in seen:
            seen.add(k)
            items.append(it)
    out[key] = items
pathlib.Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1))
print({k: len(v) for k, v in out.items() if isinstance(v, list)}, f"| {len(json.dumps(out)) // 1000} KB")
