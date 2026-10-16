# Turn one curated edition into the site: archive/<date>.html (kept forever), index.html (always the latest)
# and archive/days.json (the list the date picker uses). Each page carries its own data.
# Adds what the curator leaves out: exact times (Nitra time) and a preview image for every item.
# Items without a reachable image are dropped, because the page only shows entries with one.
# Usage (from the repo root): python3 -I tools/build.py edition.json
import datetime, json, pathlib, re, subprocess, sys, time, urllib.parse, zoneinfo
from html import unescape
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
TZ = zoneinfo.ZoneInfo("Europe/Bratislava")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
META = ("og:image", "og:image:secure_url", "og:image:url", "twitter:image", "twitter:image:src")
PUBLISHED = (r'article:published_time"\s+content="([^"]+)"', r'content="([^"]+)"\s+property="article:published_time"',
             r'"datePublished"\s*:\s*"([^"]+)"', r'<time[^>]+datetime="([^"]+)"')

def curl(*args):
    return subprocess.run(["curl", "-sfL", "--max-time", "20", "-A", UA, *args], capture_output=True)

class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found = {}
    def handle_starttag(self, tag, attrs):
        if tag == "meta":
            a = dict(attrs)
            k = (a.get("property") or a.get("name") or "").lower()
            if k in META and a.get("content"):
                self.found.setdefault(k, a["content"])

def page_info(url):
    """-> (publish time as ISO string or None, candidate image URLs)"""
    yt = re.search(r"youtube\.com/watch\?v=([\w-]{11})", url)
    if yt:
        return None, [f"https://i.ytimg.com/vi/{yt.group(1)}/{q}.jpg" for q in ("maxresdefault", "hqdefault")]
    gh = re.match(r"https://github\.com/([^/]+/[^/#?]+)/?$", url)
    if gh:  # GitHub's share card
        return None, [f"https://opengraph.githubassets.com/1/{gh.group(1)}"]
    r = curl("--max-filesize", "3000000", url)
    page = r.stdout.decode("utf-8", "ignore")[:600_000] if r.returncode == 0 else ""
    p = Meta()
    try:
        p.feed(page)
    except Exception:
        pass
    when = next((m.group(1) for pat in PUBLISHED for m in [re.search(pat, page)] if m and "T" in m.group(1)), None)
    return when, [urllib.parse.urljoin(url, unescape(p.found[k])) for k in META if k in p.found]

def is_image(url):
    for attempt in range(3):  # image hosts sometimes answer slowly or with 429
        r = curl("-r", "0-0", "-o", "/dev/null", "-w", "%{content_type}", url)
        if r.returncode == 0:
            return r.stdout.decode().startswith("image/")
        time.sleep(2 * (attempt + 1))
    return False

def local(iso):
    dt = datetime.datetime.fromisoformat(iso.strip().replace("Z", "+00:00"))
    return (dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)).astimezone(TZ)

data = json.loads(pathlib.Path(sys.argv[1]).read_text())
now = datetime.datetime.now(TZ)
data["updatedAt"] = data.get("updatedAt") or now.astimezone(datetime.timezone.utc).isoformat(timespec="seconds")
data["edition"] = local(data["updatedAt"]).date().isoformat()
dropped = []
for sec in data["sections"]:
    kept = []
    for it in sec["items"]:
        when, urls = page_info(it.get("url", ""))
        if sec["id"] in ("news", "videos"):
            if not it.get("time") and when:  # exact time from the page when the curator had none
                try:
                    t = local(when)
                    it["date"], it["time"] = t.date().isoformat(), t.strftime("%H:%M")
                except ValueError:
                    pass
        else:  # projects and skills: when they were picked up for this edition
            it["date"], it["time"] = it.get("date") or data["edition"], it.get("time") or now.strftime("%H:%M")
        it["img"] = next((u for u in urls[:3] if u.startswith("https://") and is_image(u)), "")
        (kept if it["img"] else dropped).append(it)
    sec["items"] = kept
data["added"] = sum(len(s["items"]) for s in data["sections"])

page = (ROOT / "tools" / "template.html").read_text().replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
archive = ROOT / "archive"
archive.mkdir(exist_ok=True)
(archive / f"{data['edition']}.html").write_text(page.replace("__BASE__", "../", 1))
(ROOT / "index.html").write_text(page.replace("__BASE__", "./", 1))
html = page
days_file = archive / "days.json"
days = json.loads(days_file.read_text()) if days_file.exists() else []
days_file.write_text(json.dumps(sorted(set(days) | {data["edition"]})))
print(data["edition"], {s["id"]: len(s["items"]) for s in data["sections"]}, f"| {len(html) // 1000} KB")
for it in dropped:
    print("dropped, no image:", it["title"][:70])
