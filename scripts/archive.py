"""Save private copies of cited sources into the private archive repo.

Usage (from the repo root):
  python scripts/archive.py SRC-000007 [SRC-000008 ...]
  python scripts/archive.py --copyrighted      every copyrighted source not yet archived

Each source gets a folder in ../SMC_SCC_Housing_Archive/<SRC-id>/ with:
  <id>.pdf   the source PDF as is, or the saved page printed by a headless browser (Edge or Chrome)
  <id>.html  the raw page
  <id>.txt   readable text
  meta.json  url, title, publisher, capture time, sha256 of the PDF
The PDF's sha256 is also written into data/sources/<id>.json so the public record
can prove which copy was archived without republishing it.

The download says plainly what it is. A site that refuses it is left alone: the source
stays cited by its link, with no retry and no other route to the page.
"""
import datetime
import hashlib
import html.parser
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE = os.path.join(os.path.dirname(ROOT), "SMC_SCC_Housing_Archive")
MAX_BYTES = 25 * 1024 * 1024  # larger documents, such as drawing sets, are not saved; they stay cited by link
TOO_LARGE = f"over {MAX_BYTES // 1048576} MB"
REFUSED = (401, 403, 429, 451)
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
UA = "HousingCompsArchive/1.0 (+https://poppr812.github.io/SMC_SCC_Housing_Data/)"


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


def wait_for_file(path, seconds=180):
    """Return once the file exists and hasn't grown for 3 seconds, or when time runs out.
    Pages that pull images from the web can take a few minutes to print."""
    last, steady = -1, 0
    for _ in range(seconds):
        size = os.path.getsize(path) if os.path.exists(path) else -1
        steady = steady + 1 if size > 0 and size == last else 0
        if steady >= 3:
            return
        last = size
        time.sleep(1)


def save_source(path, src):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(src, f, indent=2, ensure_ascii=False)
        f.write("\n")


def no_copy(src, path, folder, sid, reason):
    """Record why there is no saved copy: the source stays cited by its link."""
    if os.path.exists(os.path.join(folder, sid + ".pdf")):
        print(f"  {sid}  {reason}; keeping the copy already saved  {src['title'][:60]}")
        return
    json.dump({"id": sid, "title": src["title"], "publisher": src["publisher"], "date": src.get("date"), "url": src["url"],
               "captured": datetime.datetime.now().isoformat(timespec="seconds"), "skipped": reason},
              open(os.path.join(folder, "meta.json"), "w", encoding="utf-8"), indent=2)
    src["no_copy"] = reason
    save_source(path, src)
    print(f"  {sid}  no copy, {reason}; stays cited by its link  {src['title'][:60]}")


def archive(sid):
    path = os.path.join(ROOT, "data", "sources", sid + ".json")
    src = json.load(open(path, encoding="utf-8"))
    url = src["url"]
    folder = os.path.join(ARCHIVE, sid)
    os.makedirs(folder, exist_ok=True)

    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40).read(MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        if e.code not in REFUSED:
            raise
        no_copy(src, path, folder, sid, f"site refused the download (HTTP {e.code})")
        return
    if len(raw) > MAX_BYTES:
        no_copy(src, path, folder, sid, TOO_LARGE)
        return

    t = Text()
    html_path, pdf = os.path.join(folder, sid + ".html"), os.path.join(folder, sid + ".pdf")
    if os.path.exists(pdf):
        os.remove(pdf)  # never fingerprint a leftover from an earlier, interrupted run
    is_pdf = b"%PDF" in raw[:1024]  # the source itself is a PDF document: keep it as is
    if is_pdf:
        open(pdf, "wb").write(raw)
        if os.path.exists(html_path):
            os.remove(html_path)
    else:
        open(html_path, "wb").write(raw)
        t.feed(raw.decode("utf-8", "replace"))
    open(os.path.join(folder, sid + ".txt"), "w", encoding="utf-8").write(
        f"{src['title']}\n{src['publisher']} · {src.get('date') or ''}\n{url}\n\n"
        + ("(The source is a PDF document; see the PDF in this folder.)" if is_pdf else t.text()) + "\n")

    if not is_pdf:  # print the page already downloaded, fully offline: no images or scripts are fetched from the web
        browser = next((b for b in BROWSERS if os.path.exists(b)), None)
        if not browser:
            raise RuntimeError("no browser to print the page")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:  # throwaway profile, never the user's own
            out = os.path.join(profile, "print.pdf")  # a late print lands here, never over an archived copy
            try:
                subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                                f"--user-data-dir={profile}", "--host-resolver-rules=MAP * ~NOTFOUND",
                                "--virtual-time-budget=5000", f"--print-to-pdf={out}",
                                "file:///" + html_path.replace("\\", "/")], timeout=150,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.TimeoutExpired:
                pass
            wait_for_file(out)  # the browser's launcher can return before the print is written
            if os.path.exists(out) and os.path.getsize(out) > 5000:
                os.replace(out, pdf)
        if not os.path.exists(pdf):
            raise RuntimeError("the browser did not produce a PDF")
    if os.path.getsize(pdf) > MAX_BYTES:
        os.remove(pdf)
        no_copy(src, path, folder, sid, TOO_LARGE)
        return
    sha = hashlib.sha256(open(pdf, "rb").read()).hexdigest()

    now = datetime.datetime.now().isoformat(timespec="seconds")
    json.dump({"id": sid, "title": src["title"], "publisher": src["publisher"], "date": src.get("date"),
               "url": url, "captured": now, "pdf_sha256": sha, "pdf_bytes": os.path.getsize(pdf)},
              open(os.path.join(folder, "meta.json"), "w", encoding="utf-8"), indent=2)

    src["sha256"] = sha
    src.pop("no_copy", None)
    save_source(path, src)
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
