"""Label each record's addresses. Safe to rerun; apply_batch.py and import_apr.py run it for you.

    python scripts/addresses.py           rewrite records in the labeled form
    python scripts/addresses.py --check   report what would change, write nothing

Each address on a record ends up as:
    {"text": "470 S Market St, San Jose, CA", "role": "main", "src": [...],
     "written_as": [{"text": "470 South Market Street, San Jose, CA", "src": [...]}]}

- role "main": the one address a record leads with. "other": a different street address on the site.
- written_as: the same address as a source wrote it. Spelling, a missing direction, a unit number or an
  obvious typo. Kept in the database, shown small on the page, found by search.
- possible_typo_of: an "other" address whose number is one digit off another (133 and 1330 S Bascom). Not
  merged, because it could be real. A person should look.

To choose a different main address by hand, set role "main" on it and "other" on the old one; reruns keep it.
"""
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import schema  # noqa: E402

RECORDS = Path(__file__).resolve().parent.parent / "data" / "records"

CITIES = {c.upper(): c for c in [*schema.SMC_CITIES, *schema.SCC_CITIES, *schema.SMC_UNINCORPORATED, *schema.SCC_UNINCORPORATED]
          if not c.startswith("Other")}
CITIES["SAN JOSÉ"] = "San Jose"
SUFFIX = {"STREET": "St", "STR": "St", "ST": "St", "AVENUE": "Ave", "AV": "Ave", "AVE": "Ave", "BOULEVARD": "Blvd", "BL": "Blvd",
          "BLVD": "Blvd", "ROAD": "Rd", "RD": "Rd", "DRIVE": "Dr", "DR": "Dr", "LANE": "Ln", "LN": "Ln", "COURT": "Ct", "CT": "Ct",
          "PLACE": "Pl", "PL": "Pl", "WAY": "Way", "WY": "Way", "PARKWAY": "Pkwy", "PKWY": "Pkwy", "PY": "Pkwy",
          "EXPRESSWAY": "Expy", "EXPY": "Expy", "CIRCLE": "Cir", "CIR": "Cir", "TERRACE": "Ter", "TER": "Ter", "HIGHWAY": "Hwy", "HWY": "Hwy"}
ORDINAL = {"FIRST": "1st", "SECOND": "2nd", "THIRD": "3rd", "FOURTH": "4th", "FIFTH": "5th", "SIXTH": "6th", "SEVENTH": "7th",
           "EIGHTH": "8th", "NINTH": "9th", "TENTH": "10th"}
DIRS = {"NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}
ENDS = r"(?=\s*(?:$|,|&|/|\band\b|\bunit\b|\bbuilding\b|\bbldg\b|\bsuite\b|\bste\b|\bapt\b|#))"
UNIT = re.compile(r"\s+(?:unit|building|bldg|suite|ste|apt)\b[:\s]*\S*$|\s*#\s*\S+$", re.I)
SIMPLE = re.compile(r"^(\d+)\s+(?:([NSEW])\s+)?(.+)$")


def split_tail(text):
    """Street part and city of an address, dropping state and zip."""
    parts = [p.strip() for p in text.split(",") if p.strip()]
    city = None
    while parts:
        last = re.sub(r"\s+CA(?:LIFORNIA)?(?:\s+\d{5}(?:-\d{4})?)?$", "", parts[-1], flags=re.I).strip()
        if re.fullmatch(r"(?:CA|CALIFORNIA|USA|\d{5}(?:-\d{4})?|Other .+ County)", last, re.I) or not last:
            parts.pop()
        elif last.upper() in CITIES:
            city = city or CITIES[last.upper()]
            parts.pop()
        else:
            parts[-1] = last
            break
    return ", ".join(parts), city


def tidy(street):
    """One standard way of writing a street, without changing what it says."""
    s = re.sub(r"\s+", " ", street.replace(".", "")).strip()
    s = re.sub(r"\b[A-Z]{3,}\b", lambda m: m.group().capitalize(), s)
    s = re.sub(r"\b(\d+)(ST|ND|RD|TH)\b", lambda m: m.group(1) + m.group(2).lower(), s)
    s = re.sub(r"\bMc([a-z])", lambda m: "Mc" + m.group(1).upper(), s)
    s = re.sub(r"\bAnd\b", "and", s)
    s = re.sub(r"\b(" + "|".join(SUFFIX) + r")\b" + ENDS, lambda m: SUFFIX[m.group(1).upper()], s, flags=re.I)
    s = re.sub(r"\b(\d+)\s+(north|south|east|west)\s+(?=[\w']+\s+\w)", lambda m: f"{m.group(1)} {DIRS[m.group(2).upper()]} ", s, flags=re.I)
    s = re.sub(r"\b(" + "|".join(ORDINAL) + r")\s+(?=(?:St|Ave)\b)", lambda m: ORDINAL[m.group(1).upper()] + " ", s, flags=re.I)
    return s


def parts_of(street):
    """(number, direction, street name, suffix) for a plain single address, else None."""
    s = UNIT.sub("", street)
    if re.search(r"[,&/]|\band\b", s, re.I):
        return None
    m = SIMPLE.match(s)
    if not m:
        return None
    words = m.group(3).split()
    suffix = words.pop() if len(words) > 1 and words[-1] in SUFFIX.values() else ""
    return m.group(1), m.group(2) or "", " ".join(words).upper(), suffix


def same_place(a, b):
    """Are two tidied streets the same address written differently?"""
    if a.upper() == b.upper():
        return True
    pa, pb = parts_of(a), parts_of(b)
    if not pa or not pb or pa[0] != pb[0]:
        return False
    if pa[1] and pb[1] and pa[1] != pb[1]:
        return False
    if pa[2] == pb[2]:
        return not (pa[3] and pb[3] and pa[3] != pb[3])
    full = lambda p: f"{p[2]} {p[3]}".strip()
    return difflib.SequenceMatcher(None, full(pa), full(pb)).ratio() >= 0.85  # a typo in the street name


def one_digit_off(a, b):
    return len(a) == len(b) + 1 and any(a[:i] + a[i + 1:] == b for i in range(len(a)))


def best_claim(rec, key):
    f = rec.get("facts", {}).get(key)
    if not f or not f.get("claims"):
        return None
    return f["claims"][f.get("best") or 0].get("value")


def label(rec):
    """Return the record's addresses in labeled form."""
    # Flatten, so a rerun treats new and earlier spellings alike.
    entries = []
    for a in rec.get("addresses", []):
        entries.append({"text": a["text"], "src": list(a.get("src") or []), "role": a.get("role")})
        entries += [{"text": w["text"], "src": list(w.get("src") or []), "role": None} for w in a.get("written_as", [])]

    place = best_claim(rec, "jurisdiction")
    if place not in schema.SMC_CITIES and place not in schema.SCC_CITIES:
        place = best_claim(rec, "community")
        place = None if not place or str(place).startswith("Other") else place

    groups = []
    for e in entries:
        street, city = split_tail(e["text"])
        e.update(street=street, tidy=tidy(street), city=city)
        for g in groups:
            if any(same_place(e["tidy"], x["tidy"]) for x in g):
                g.append(e)
                break
        else:
            groups.append([e])

    out = []
    for g in groups:
        # The address to lead with: already chosen, else the most common way of writing it, fullest form first.
        keep = next((x for x in g if x["role"]), None)
        if keep:
            lead = keep["tidy"]
        else:
            count = lambda x: sum(y["tidy"].upper() == x["tidy"].upper() for y in g)
            def rank(x):
                p = parts_of(x["tidy"])
                return (count(x), bool(p and p[1]), bool(p and p[3]), not UNIT.search(x["tidy"]), -len(x["tidy"]))
            lead = UNIT.sub("", max(g, key=rank)["tidy"])
        city = next((x["city"] for x in g if x["city"]), place)
        written, src, seen = [], [], {lead.upper()}
        for x in g:
            src += [s for s in x["src"] if s not in src]
            if x["street"].upper() not in seen:
                seen.add(x["street"].upper())
                written.append({"text": x["text"], "src": x["src"]})
        a = {"text": f"{lead}, {city}, CA" if city else f"{lead}, CA", "role": keep["role"] if keep else "other", "src": src}
        if written:
            a["written_as"] = written
        out.append(a)

    # One main address: the one the record's name points to, else the best sourced.
    if out and not any(a["role"] == "main" for a in out):
        name = rec.get("name", "").upper()
        def score(ia):
            i, a = ia
            street = split_tail(a["text"])[0]
            num = re.match(r"\d+", street)
            return (street.upper() in name, bool(num and re.search(rf"\b{num.group()}\b", name)), len(a["src"]), -i)
        out[max(enumerate(out), key=score)[0]]["role"] = "main"

    # Numbers one digit apart on the same street are flagged, not merged.
    for a in out:
        pa = parts_of(split_tail(a["text"])[0])
        for b in out:
            pb = parts_of(split_tail(b["text"])[0])
            if a is b or not pa or not pb or pa[1:3] != pb[1:3] or a["role"] == "main":
                continue
            if one_digit_off(pa[0], pb[0]) or one_digit_off(pb[0], pa[0]):
                a["possible_typo_of"] = b["text"]
    out.sort(key=lambda a: a["role"] != "main")
    return out


def run(check=False):
    changed = 0
    for path in sorted(RECORDS.glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        new = label(rec)
        if new != rec.get("addresses", []):
            changed += 1
            if not check:
                rec["addresses"] = new
                path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


if __name__ == "__main__":
    check = "--check" in sys.argv
    print(f"{run(check)} records {'would change' if check else 'updated'}")
