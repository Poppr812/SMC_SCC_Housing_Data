"""Save private copies of cited sources into the private archive repo.

Usage (from the repo root):
  python scripts/archive.py SRC-000007 [SRC-000008 ...]
  python scripts/archive.py --copyrighted      every copyrighted source not yet archived

Each source gets a folder in ../SMC_SCC_Housing_Archive/<SRC-id>/ with:
  <id>.pdf   the page as printed by a headless browser (Edge or Chrome)
  <id>.html  the raw page
  <id>.txt   readable text
  meta.json  url, title, publisher, capture time, sha256 of the PDF
The PDF's sha256 is also written into data/sources/<id>.json so the public record
can prove which copy was archived without republishing it.
"""
import datetime
import hashlib
import html.parser
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE = os.path.join(os.path.dirname(ROOT), "SMC_SCC_Housing_Archive")
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


class Text(html.parser.HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form"}
    BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "tr", "section", "article"}

    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)

    def text(self):
        lines = [" ".join(l.split()) for l in "".join(self.out).splitlines()]
        return "\n".join(l for l in lines if l)


def archive(sid):
    path = os.path.join(ROOT, "data", "sources", sid + ".json")
    src = json.load(open(path, encoding="utf-8"))
    url = src["url"]
    folder = os.path.join(ARCHIVE, sid)
    os.makedirs(folder, exist_ok=True)

    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=40).read()
    open(os.path.join(folder, sid + ".html"), "wb").write(raw)
    t = Text()
    t.feed(raw.decode("utf-8", "replace"))
    open(os.path.join(folder, sid + ".txt"), "w", encoding="utf-8").write(
        f"{src['title']}\n{src['publisher']} · {src.get('date') or ''}\n{url}\n\n{t.text()}\n")

    pdf = os.path.join(folder, sid + ".pdf")
    browser = next(b for b in BROWSERS if os.path.exists(b))
    with tempfile.TemporaryDirectory() as profile:  # throwaway profile, never the user's own
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={profile}", "--virtual-time-budget=15000",
                        f"--print-to-pdf={pdf}", url], check=True, timeout=120,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sha = hashlib.sha256(open(pdf, "rb").read()).hexdigest()

    now = datetime.datetime.now().isoformat(timespec="seconds")
    json.dump({"id": sid, "title": src["title"], "publisher": src["publisher"], "date": src.get("date"),
               "url": url, "captured": now, "pdf_sha256": sha, "pdf_bytes": os.path.getsize(pdf)},
              open(os.path.join(folder, "meta.json"), "w", encoding="utf-8"), indent=2)

    src["sha256"] = sha
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(src, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  {sid}  {os.path.getsize(pdf)//1024} KB PDF, {len(t.text()):,} chars text  {src['title'][:60]}")


if __name__ == "__main__":
    ids = sys.argv[1:]
    if ids == ["--copyrighted"]:
        d = os.path.join(ROOT, "data", "sources")
        ids = [f[:-5] for f in sorted(os.listdir(d))
               if json.load(open(os.path.join(d, f), encoding="utf-8")).get("copyright")
               and not os.path.exists(os.path.join(ARCHIVE, f[:-5], f[:-5] + ".pdf"))]
    for sid in ids:
        try:
            archive(sid)
        except Exception as e:
            print(f"  {sid}  FAILED: {e}")
