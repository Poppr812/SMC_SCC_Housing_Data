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
MAX_BYTES = 25 * 1024 * 1024  # larger documents, such as drawing sets, are not saved; they stay cited by link
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


def skip_large(src, folder, sid):
    """Drawing sets and other large documents aren't saved: the source stays cited by its link."""
    json.dump({"id": sid, "title": src["title"], "publisher": src["publisher"], "date": src.get("date"), "url": src["url"],
               "captured": datetime.datetime.now().isoformat(timespec="seconds"), "skipped": f"over {MAX_BYTES // 1048576} MB"},
              open(os.path.join(folder, "meta.json"), "w", encoding="utf-8"), indent=2)
    print(f"  {sid}  skipped, over {MAX_BYTES // 1048576} MB; stays cited by its link  {src['title'][:60]}")


def archive(sid):
    path = os.path.join(ROOT, "data", "sources", sid + ".json")
    src = json.load(open(path, encoding="utf-8"))
    url = src["url"]
    folder = os.path.join(ARCHIVE, sid)
    os.makedirs(folder, exist_ok=True)

    t, raw = Text(), b""
    html_path, pdf = os.path.join(folder, sid + ".html"), os.path.join(folder, sid + ".pdf")
    if os.path.exists(pdf):
        os.remove(pdf)  # never fingerprint a leftover from an earlier, interrupted run
    try:  # some sites refuse scripted downloads; the browser print below may still work
        raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40).read(MAX_BYTES + 1)
    except Exception as e:
        print(f"  {sid}  page download refused ({e}); trying the browser print only")
    is_pdf = raw[:4] == b"%PDF"  # the source itself is a PDF document: keep it as is
    if is_pdf and len(raw) > MAX_BYTES:
        skip_large(src, folder, sid)
        return
    if is_pdf:
        open(pdf, "wb").write(raw)
        if os.path.exists(html_path):
            os.remove(html_path)
    elif raw:
        open(html_path, "wb").write(raw)
        t.feed(raw.decode("utf-8", "replace"))
    open(os.path.join(folder, sid + ".txt"), "w", encoding="utf-8").write(
        f"{src['title']}\n{src['publisher']} · {src.get('date') or ''}\n{url}\n\n"
        + ("(The source is a PDF document; see the PDF in this folder.)" if is_pdf else t.text()) + "\n")

    browsers = [] if is_pdf else [b for b in BROWSERS if os.path.exists(b)]
    # the live page in Edge, then Chrome, then the saved copy (for sites that block automated browsers)
    targets = [(b, url) for b in browsers] + [(b, "file:///" + html_path.replace("\\", "/")) for b in browsers[:1] if raw]
    for browser, target in targets:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:  # throwaway profile, never the user's own
            try:
                subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                                f"--user-data-dir={profile}", "--virtual-time-budget=20000",
                                f"--print-to-pdf={pdf}", target], timeout=150,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.TimeoutExpired:
                pass
        if os.path.exists(pdf) and os.path.getsize(pdf) > 5000:
            break
    if not (os.path.exists(pdf) and os.path.getsize(pdf) > 5000):
        raise RuntimeError("no browser produced a PDF")
    if os.path.getsize(pdf) > MAX_BYTES:
        os.remove(pdf)
        skip_large(src, folder, sid)
        return
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
               and not os.path.exists(os.path.join(ARCHIVE, f[:-5], f[:-5] + ".pdf"))
               and not os.path.exists(os.path.join(ARCHIVE, f[:-5], "meta.json"))]
    for sid in ids:
        try:
            archive(sid)
        except Exception as e:
            print(f"  {sid}  FAILED: {e}")
