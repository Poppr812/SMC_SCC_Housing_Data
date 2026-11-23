"""Backups for cited sources: a Wayback Machine snapshot (public) and a private copy of copyrighted sources.

Usage (from the repo root):
  python scripts/archive.py SRC-000007 [SRC-000008 ...]   save private copies of these sources
  python scripts/archive.py --copyrighted      every copyrighted source not yet saved
  python scripts/archive.py --wayback [--save N]
        find an existing Wayback Machine snapshot for every source that has none; with --save,
        ask the Wayback Machine to capture up to N sources that still have none
  python scripts/archive.py --text-only        convert older copies of web pages to text only

The Wayback snapshot is the backup anyone can check: the site links to it on every source, and
if a link later breaks, the snapshot still shows what the source said.

The private copy, in ../SMC_SCC_Housing_Archive/<SRC-id>/, is for copyrighted sources only
(news, trade press, developer pages), kept for Paul's verification and never republished:
  <id>.txt   readable text of a web page (web pages are kept as text only)
  <id>.pdf   the source as is, when the source itself is a PDF document (up to 25 MB)
  meta.json  url, title, publisher, capture time, sha256 and size of the saved file
The saved file's sha256 is also written into data/sources/<id>.json, so the public record
can prove which copy was saved without republishing it.

Downloads say plainly what they are. A site that refuses is left alone: the source stays cited
by its link, with no retry and no other route to the page.
"""
import datetime
import hashlib
import html.parser
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "data", "sources")
ARCHIVE = os.path.join(os.path.dirname(ROOT), "SMC_SCC_Housing_Archive")
MAX_BYTES = 25 * 1024 * 1024  # larger documents, such as drawing sets, are not saved; they stay cited by link
TOO_LARGE = f"over {MAX_BYTES // 1048576} MB"
REFUSED = (401, 403, 429, 451)
UA = "HousingCompsArchive/1.0 (+https://poppr812.github.io/SMC_SCC_Housing_Data/)"
TODAY = datetime.date.today().isoformat()


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


def get(url, timeout=40, limit=MAX_BYTES + 1):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout).read(limit)


def load(sid):
    return json.load(open(os.path.join(SOURCES, sid + ".json"), encoding="utf-8"))


def save_source(src):
    body = json.dumps(src, indent=2, ensure_ascii=False) + "\n"
    for attempt in range(5):  # another program can hold the file for a moment
        try:
            with open(os.path.join(SOURCES, src["id"] + ".json"), "w", encoding="utf-8", newline="\n") as f:
                f.write(body)
            return
        except OSError:
            if attempt == 4:
                raise
            time.sleep(2)


def all_ids():
    return sorted(f[:-5] for f in os.listdir(SOURCES) if f.endswith(".json"))


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def write_meta(folder, src, saved):
    json.dump({"id": src["id"], "title": src["title"], "publisher": src["publisher"], "date": src.get("date"),
               "url": src["url"], "captured": datetime.datetime.now().isoformat(timespec="seconds"),
               "file": os.path.basename(saved), "sha256": sha(saved), "bytes": os.path.getsize(saved)},
              open(os.path.join(folder, "meta.json"), "w", encoding="utf-8"), indent=2)


# ---------- private copies ----------

def no_copy(src, folder, reason):
    """Record why there is no saved copy: the source stays cited by its link."""
    sid = src["id"]
    if any(os.path.exists(os.path.join(folder, sid + x)) for x in (".pdf", ".txt")) and src.get("sha256"):
        print(f"  {sid}  {reason}; keeping the copy already saved  {src['title'][:60]}")
        return
    json.dump({"id": sid, "title": src["title"], "publisher": src["publisher"], "date": src.get("date"), "url": src["url"],
               "captured": datetime.datetime.now().isoformat(timespec="seconds"), "skipped": reason},
              open(os.path.join(folder, "meta.json"), "w", encoding="utf-8"), indent=2)
    src["no_copy"] = reason
    save_source(src)
    print(f"  {sid}  no copy, {reason}; stays cited by its link  {src['title'][:60]}")


def archive(sid):
    src = load(sid)
    url = src["url"]
    folder = os.path.join(ARCHIVE, sid)
    os.makedirs(folder, exist_ok=True)
    try:
        raw = get(url)
    except urllib.error.HTTPError as e:
        if e.code not in REFUSED:
            raise
        no_copy(src, folder, f"site refused the download (HTTP {e.code})")
        return
    if len(raw) > MAX_BYTES:
        no_copy(src, folder, TOO_LARGE)
        return

    pdf, txt, html_path = (os.path.join(folder, sid + x) for x in (".pdf", ".txt", ".html"))
    head = f"{src['title']}\n{src['publisher']} · {src.get('date') or ''}\n{url}\n\n"
    if b"%PDF" in raw[:1024]:  # the source itself is a PDF document: keep it as is
        open(pdf, "wb").write(raw)
        open(txt, "w", encoding="utf-8").write(head + "(The source is a PDF document; see the PDF in this folder.)\n")
        saved = pdf
    else:  # a web page: keep its readable text only
        t = Text()
        t.feed(raw.decode("utf-8", "replace"))
        open(txt, "w", encoding="utf-8").write(head + t.text() + "\n")
        for old in (pdf, html_path):
            if os.path.exists(old):
                os.remove(old)
        saved = txt
    write_meta(folder, src, saved)
    src["sha256"] = sha(saved)
    src.pop("no_copy", None)
    save_source(src)
    print(f"  {sid}  {os.path.getsize(saved)//1024} KB {'PDF' if saved == pdf else 'text'}  {src['title'][:60]}")


def pending_copies():
    out = []
    for sid in all_ids():
        if load(sid).get("copyright") and not os.path.exists(os.path.join(ARCHIVE, sid, "meta.json")):
            out.append(sid)
    return out


def text_only():
    """Older copies of web pages were saved as the raw page plus a printed PDF. Keep the text only."""
    n = 0
    for sid in all_ids():
        folder = os.path.join(ARCHIVE, sid)
        html_path, pdf, txt = (os.path.join(folder, sid + x) for x in (".html", ".pdf", ".txt"))
        if not os.path.exists(html_path):
            continue  # a PDF document kept as is, or no copy
        if not os.path.exists(txt):
            t = Text()
            t.feed(open(html_path, encoding="utf-8", errors="replace").read())
            src = load(sid)
            open(txt, "w", encoding="utf-8").write(
                f"{src['title']}\n{src['publisher']} · {src.get('date') or ''}\n{src['url']}\n\n{t.text()}\n")
        for old in (html_path, pdf):
            if os.path.exists(old):
                os.remove(old)
        src = load(sid)
        if os.path.exists(os.path.join(folder, "meta.json")) or src.get("sha256"):
            write_meta(folder, src, txt)
            src["sha256"] = sha(txt)
            src.pop("no_copy", None)
            save_source(src)
        n += 1
    print(f"converted {n} web-page copies to text only")


# ---------- Wayback Machine ----------

def wayback_lookup(src):
    """Date of the existing snapshot closest to the retrieval date, or None."""
    q = urllib.parse.urlencode({"url": src["url"], "timestamp": (src.get("retrieved") or TODAY).replace("-", "")})
    data = json.loads(get("https://archive.org/wayback/available?" + q, timeout=30, limit=100000))
    snap = (data.get("archived_snapshots") or {}).get("closest") or {}
    if snap.get("available") and str(snap.get("status", "200")).startswith(("2", "3")):
        ts = snap["timestamp"]
        return f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
    return None


def wayback_save(src):
    """Ask the Wayback Machine to capture the page now. True if it did."""
    try:
        get("https://web.archive.org/save/" + src["url"], timeout=120, limit=1000)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise  # the service asked us to slow down: stop this run
        return False


def wayback(save_limit):
    missing = [s for s in (load(i) for i in all_ids()) if not s.get("wayback")]
    found = 0
    still = []
    for src in missing:
        try:
            date = wayback_lookup(src)
        except Exception:
            date = None
        if date:
            src["wayback"] = date
            save_source(src)
            found += 1
        else:
            still.append(src)
        time.sleep(1)
    print(f"Wayback: {found} existing snapshots found; {len(still)} sources still have none")
    saved = 0
    for src in still[:save_limit]:
        try:
            if wayback_save(src):
                time.sleep(5)
                date = wayback_lookup(src)
                if date:
                    src["wayback"] = date
                    save_source(src)
                    saved += 1
        except urllib.error.HTTPError:
            print("Wayback asked us to slow down; stopping captures for this run")
            break
        except Exception:
            pass
        time.sleep(15)
    if save_limit:
        print(f"Wayback: {saved} new snapshots captured")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if args[:1] == ["--wayback"]:
        wayback(int(args[2]) if args[1:2] == ["--save"] else 0)
    elif args == ["--text-only"]:
        text_only()
    else:
        for sid in (pending_copies() if args == ["--copyrighted"] else args):
            try:
                archive(sid)
            except Exception as e:
                print(f"  {sid}  FAILED: {e}")
