# Read every shortlisted item in full before it is written up, so descriptions come from the source, not from a feed teaser.
# Articles: the page's main text. GitHub: the README (or the linked file, e.g. CHANGELOG.md). Hugging Face: the model card.
# Skills (skills.sh/<owner>/<repo>/<skill>): the skill's SKILL.md.
# YouTube pages can't be fetched from here (rate-limited): videos are judged on the channel feed's description instead.
# Usage: python3 -I tools/read.py shortlist.json reading.json   (shortlist.json: a JSON list of candidate URLs)
import concurrent.futures, html, json, pathlib, re, subprocess, sys

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
LIMIT = 4000  # characters kept per item: enough for the substance, small enough to read 60 items

def get(url):
    r = subprocess.run(["curl", "-sfL", "--max-time", "20", "--max-filesize", "5000000", "-A", UA, url], capture_output=True)
    return r.stdout.decode("utf-8", "ignore") if r.returncode == 0 else ""

def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def markdown(md):  # drop images, badges and HTML; keep the words
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)|<[^>]+>|\[!\[.*?\]\(.*?\)\]\(.*?\)", " ", md)
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)

def article(page):
    page = re.sub(r"(?is)<(script|style|noscript|svg)\b[^>]*>.*?</\1>", " ", page)
    def paras(part):  # paragraphs, headings and longer list items; short list items are menus
        found = ((tag.lower(), clean(inner)) for tag, inner in re.findall(r"(?is)<(p|li|h2|h3)\b[^>]*>(.*?)</\1>", part))
        return " ".join(t for tag, t in found if tag != "li" or len(t) >= 40)
    # the post itself: its longest <article> when that holds the story, else the whole page (some blogs put only cards in <article>)
    best = max((paras(a) for a in re.findall(r"(?is)<article\b[^>]*>(.*?)</article>", page)), key=len, default="")
    return best if len(best) >= 600 else paras(page)

def read(url):
    gh = re.match(r"https://github\.com/([^/]+/[^/#?]+)(?:/blob/([^/]+)/([^#?]+))?", url)
    if gh:
        repo, ref, path = gh.groups()
        paths = [path] if path else ["README.md", "readme.md", "README.MD", "README.rst", "README"]
        return next((markdown(t) for p in paths if (t := get(f"https://raw.githubusercontent.com/{repo}/{ref or 'HEAD'}/{p}"))), "")
    hf = re.match(r"https://huggingface\.co/(?!(?:blog|papers|spaces|datasets|docs|learn|posts|collections)/)([^/]+/[^/#?]+)/?$", url)  # models only
    if hf:
        return markdown(re.sub(r"(?s)^---.*?---", "", get(f"https://huggingface.co/{hf.group(1)}/raw/main/README.md")))
    sk = re.match(r"https://skills\.sh/([\w.-]+/[\w.-]+)/([^/#?]+)", url)
    if sk:  # a skill: its SKILL.md from the repo, in the usual places
        repo, sid = sk.groups()
        for path in (f"skills/{sid}/SKILL.md", f"{sid}/SKILL.md", f".claude/skills/{sid}/SKILL.md", "SKILL.md"):
            if t := get(f"https://raw.githubusercontent.com/{repo}/HEAD/{path}"):
                return markdown(t)
    if "youtube.com/" in url:
        return ""
    return article(get(url))

urls = list(dict.fromkeys(json.loads(pathlib.Path(sys.argv[1]).read_text())))
with concurrent.futures.ThreadPoolExecutor(8) as pool:
    texts = list(pool.map(lambda u: re.sub(r"\s+", " ", read(u)).strip()[:LIMIT], urls))
pathlib.Path(sys.argv[2]).write_text(json.dumps([{"url": u, "text": t} for u, t in zip(urls, texts)], ensure_ascii=False, indent=1))
print(f"read {sum(1 for t in texts if len(t) > 300)} of {len(urls)} in full")
for u, t in zip(urls, texts):
    if len(t) <= 300 and "youtube.com/" not in u:
        print("not readable:", u)
