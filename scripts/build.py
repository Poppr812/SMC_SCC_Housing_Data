"""Build the public site from the data files.

    python scripts/build.py

Reads data/records/*.json and data/sources/*.json, validates them against
scripts/schema.py, computes calculated values, and writes:
    docs/index.html         the site (GitHub Pages serves /docs)
    docs/data/records.json  the full processed dataset (open data download)
Stops with a list of problems if any record breaks the rules.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

import schema

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"

PIPELINE_STATUSES = {"Proposed", "Approved", "Permitted", "Under construction", "Lease-up / selling", "Inactive pipeline"}
STALE_YEARS = 5  # no recorded movement for this long: shown as Inactive pipeline
STALE_STATUSES = {"Proposed", "Approved", "Permitted"}
SHORT_TERM = {"Predevelopment loan", "Construction loan", "Bridge loan"}
EQUITY = {"Tax-credit equity (4%)", "Tax-credit equity (9%)", "State tax-credit equity",
          "Sponsor / GP equity", "Private equity", "Deferred developer fee"}
APN_RE = {"SMC": re.compile(r"^\d{3}-\d{3}-\d{3}$"), "SCC": re.compile(r"^\d{3}-\d{2}-\d{3}$")}
ID_RE = re.compile(r"^(SMC|SCC)-\d{6}$")
COUNTY_BY_PREFIX = {v["prefix"]: k for k, v in schema.COUNTIES.items()}
SRC_RE = re.compile(r"^SRC-\d{6}$")


def load(folder, pattern):
    out = {}
    for p in sorted((DATA / folder).glob("*.json")):
        obj = json.loads(p.read_text(encoding="utf-8"))
        if obj.get("id") != p.stem:
            sys.exit(f"{p.name}: id {obj.get('id')!r} doesn't match file name")
        if not pattern.match(obj["id"]):
            sys.exit(f"{p.name}: bad id format")
        out[obj["id"]] = obj
    return out


def m(n):
    return f"${n:,.0f}"


class Checker:
    def __init__(self, rid, sources):
        self.rid, self.sources, self.errors = rid, sources, []

    def err(self, msg):
        self.errors.append(f"{self.rid}: {msg}")

    def src(self, srcs, where):
        if not srcs:
            self.err(f"{where} has no source")
        for s in srcs or []:
            if s not in self.sources:
                self.err(f"{where} cites unknown source {s}")


def validate(r, sources):
    c = Checker(r["id"], sources)
    if not r.get("name"):
        c.err("missing name")
    if not r.get("parcels"):
        c.err("needs at least one parcel")
    for p in r.get("parcels", []):
        if not APN_RE[r["id"][:3]].match(p.get("apn", "")):
            c.err(f"APN {p.get('apn')!r} is not in this county's form")
        if not p.get("outline"):
            c.err(f"parcel {p.get('apn')} has no outline; run: python scripts/parcels.py fill {r.get('id')}")
        c.src(p.get("src"), f"parcel {p.get('apn')}")
    for a in r.get("addresses", []):
        c.src(a.get("src"), f"address {a.get('text')}")
        for w in a.get("written_as", []):
            c.src(w.get("src"), f"address spelling {w.get('text')}")
    if r.get("addresses") and sum(a.get("role") == "main" for a in r["addresses"]) != 1:
        c.err("needs exactly one main address; run: python scripts/addresses.py")
    for key in schema.REQUIRED_FACTS:
        if key not in r.get("facts", {}):
            c.err(f"missing required fact {key}")
    for key, f in r.get("facts", {}).items():
        if key not in schema.FACTS:
            c.err(f"unknown fact {key}")
            continue
        _, label, kind, opts = schema.FACTS[key]
        claims = f.get("claims", [])
        if not claims:
            c.err(f"{key} has no claims")
        if len(claims) > 1 and not f.get("combine") and f.get("best") is None and key in ("product_type", "status", "jurisdiction"):
            c.err(f"{key} has competing claims; set 'best' so the record can be placed")
        for cl in claims:
            c.src(cl.get("src"), key)
            v = cl.get("value")
            if kind == "cat" and v not in opts:
                c.err(f"{key}: {v!r} is not a defined label")
            if kind == "catmulti" and (not isinstance(v, list) or any(x not in opts for x in v)):
                c.err(f"{key}: {v!r} has an undefined label")
            if kind in ("int", "money") and not isinstance(v, int):
                c.err(f"{key}: {v!r} should be a whole number")
            if kind == "num" and not isinstance(v, (int, float)):
                c.err(f"{key}: {v!r} should be a number")
            if kind == "mix" and (not isinstance(v, dict) or any(k not in schema.MIX_KEYS for k in v)):
                c.err(f"{key}: unit mix keys must be {schema.MIX_KEYS}")
            if kind == "ami" and not all(isinstance(x, dict) and "count" in x and "ami" in x for x in v):
                c.err(f"{key}: entries need count and ami")
    jur = (r.get("facts", {}).get("jurisdiction") or {}).get("claims", [{}])[0].get("value")
    com = (r.get("facts", {}).get("community") or {}).get("claims", [{}])[0].get("value")
    county = schema.COUNTIES[COUNTY_BY_PREFIX[r["id"][:3]]]
    if jur == "Unincorporated" and com not in county["unincorporated"]:
        c.err(f"unincorporated record needs facts.community set to one of this county's communities (got {com!r})")
    if jur and jur != "Unincorporated" and jur not in county["cities"]:
        c.err(f"jurisdiction {jur!r} is not in {COUNTY_BY_PREFIX[r['id'][:3]]}")
    for n in r.get("construction_notes", []):
        c.src(n.get("src"), "construction note")
    for p in r.get("parties", []):
        if p.get("role") not in schema.PARTY_ROLES:
            c.err(f"party role {p.get('role')!r} not defined")
        if p.get("role") == "Other" and not p.get("other_role"):
            c.err(f"party {p.get('company')}: 'Other' needs other_role text")
        c.src(p.get("src"), f"party {p.get('company')}")
    for x in r.get("financing", []):
        if x.get("type") not in schema.FINANCING_TYPES:
            c.err(f"financing type {x.get('type')!r} not defined")
        if x.get("group") and x["group"] not in r.get("groups", {}):
            c.err(f"financing group {x['group']!r} not defined in groups")
        c.src(x.get("src"), f"financing {x.get('provider')}")
    for e in r.get("events", []):
        if e.get("type") not in schema.EVENT_TYPES:
            c.err(f"event type {e.get('type')!r} not defined")
        c.src(e.get("src"), f"event {e.get('label')}")
    for im in r.get("images", []):
        if im.get("kind") == "copyright":
            c.src([im.get("src")], "image")
    return c.errors


def address_texts(r):
    """Every address on a record, including the spellings kept under it."""
    return [t for a in r["addresses"] for t in [a["text"]] + [w["text"] for w in a.get("written_as", [])]]


def read_leads(records):
    """Open items in INTAKE.md: pipeline bullets and transaction headings, flagged if a record seems to cover them."""
    hay = [(r["id"], " ".join([r["name"]] + address_texts(r)).lower()) for r in records]
    section, leads = "", []
    for line in (ROOT / "INTAKE.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].split(" (")[0]
        pipeline = section.startswith("Development") and line.startswith("- ")
        deal = section.startswith("Transactions") and line.startswith("### ")
        if not (pipeline or deal):
            continue
        text = re.sub(r"\s*https?://\S+", "", line.lstrip("-# ")).strip()
        m = re.search(r"\b(\d+)(?:-\d+)?\s+(?:[NSEW]\.?\s+)?([A-Za-z]+)", text)
        hit = ""
        if m and m.group(2).lower() != "units":
            pat = rf"\b{m.group(1)}\b[^,]{{0,8}}\b{m.group(2).lower()}\b"
            hit = next((i for i, h in hay if re.search(pat, h)), "")
        leads.append({"section": section, "text": text[:140], "entered": hit})
    return leads


def is_stale(latest, today):
    """latest is YYYY, YYYY-MM or YYYY-MM-DD; a partial date counts as the end of that period."""
    if not latest:
        return False
    full = latest + {4: "-12-31", 7: "-31"}.get(len(latest), "")
    return full < f"{today.year - STALE_YEARS}-{today:%m-%d}"


def best(f):
    """The value to use in summaries: single claim, flagged best, else None."""
    if f is None:
        return None
    cl = f["claims"]
    if len(cl) == 1:
        return cl[0]["value"]
    if f.get("best") is not None:
        return cl[f["best"]]["value"]
    return None


def units_display(f):
    """'71', or '1,014–1,514' when sources give different counts and none is flagged best."""
    if f is None:
        return ""
    b = best(f)
    if isinstance(b, int):
        return f"{b:,}"
    nums = [c["value"] for c in f["claims"] if isinstance(c["value"], int)]
    if not nums:
        return ""
    lo, hi = min(nums), max(nums)
    return f"{lo:,}" if lo == hi else f"{lo:,}–{hi:,}"


def units_range(f):
    """[low, high] unit count for totals: the best value twice, or the spread of the claims."""
    if f is None:
        return None
    b = best(f)
    if isinstance(b, int):
        return [b, b]
    nums = [c["value"] for c in f["claims"] if isinstance(c["value"], int)]
    return [min(nums), max(nums)] if nums else None


INCLUSIONARY_MAX = 0.25  # up to 25% deed-restricted is market with inclusionary; above that the project competes for affordable financing
TAX_CREDIT_TYPES = {"Tax-exempt bonds", "Tax-credit equity (4%)", "Tax-credit equity (9%)", "State tax-credit equity"}
STATE_DR = re.compile(r"^([\d,]+) deed-restricted units reported to the state")


def affordability(facts, ami, units):
    """Market or Affordable, with a short label. Returns (bucket or None, label, share or None)."""
    t = best(facts.get("affordability_type"))
    if t == "100% affordable":
        return "Affordable", "Affordable, 100%", 1.0
    if t in ("Market-rate", "Below-market (unrestricted)"):
        return "Market", "Market", 0.0
    if t != "Mixed-income":
        return None, "Not stated", None
    restricted = sum(x["count"] for x in ami) if ami else None
    if restricted is None:
        note = best(facts.get("affordability_notes")) or ""
        mt = STATE_DR.match(note) if isinstance(note, str) else None
        restricted = int(mt.group(1).replace(",", "")) if mt else None
    share = restricted / units if restricted and units else None
    if share is not None and units - restricted <= 3:  # only managers' units are unrestricted
        return "Affordable", "Affordable, 100%", 1.0
    if share is not None and share > INCLUSIONARY_MAX:
        return "Affordable", f"Affordable, {min(99, round(share * 100))}%", share
    return "Market", "Market, with inclusionary", share


def process(r, sources):
    facts = r["facts"]
    # Local source labels S1, S2... in order of first appearance on the page.
    order = []
    def see(srcs):
        for s in srcs or []:
            if s not in order:
                order.append(s)
    for p in r["parcels"]:
        see(p["src"])
    for a in r["addresses"]:
        see(a["src"])
        for w in a.get("written_as", []):
            see(w["src"])
    for key in schema.FACTS:
        if key in facts:
            for cl in facts[key]["claims"]:
                see(cl["src"])
    for n in r.get("construction_notes", []):
        see(n["src"])
    for p in r.get("parties", []):
        see(p["src"])
    for x in r.get("financing", []):
        see(x["src"])
    for e in r.get("events", []):
        see(e["src"])
    for im in r.get("images", []):
        if im.get("src"):
            see([im["src"]])
    src_labels = {s: f"S{i + 1}" for i, s in enumerate(order)}

    pts = [pt for p in r["parcels"] for pt in (p.get("outline") or [])[:-1]]
    lng = sum(p[0] for p in pts) / len(pts)
    lat = sum(p[1] for p in pts) / len(pts)

    units = best(facts.get("total_units"))
    tdc = best(facts.get("total_development_cost"))
    price = best(facts.get("sale_price"))
    rsf = best(facts.get("residential_sf"))
    calcs = {}
    if tdc and units:
        calcs["cost_per_unit"] = {"value": round(tdc / units), "how": f"Total development cost {m(tdc)} ÷ {units:,} total units"}
    if tdc and rsf:
        calcs["cost_per_sf"] = {"value": round(tdc / rsf), "how": f"Total development cost {m(tdc)} ÷ {rsf:,} sq ft"}
    if price and units:
        calcs["price_per_unit"] = {"value": round(price / units), "how": f"Sale price {m(price)} ÷ {units:,} total units"}
    if price and rsf:
        calcs["price_per_sf"] = {"value": round(price / rsf), "how": f"Sale price {m(price)} ÷ {rsf:,} sq ft"}
    long_term = [x for x in r.get("financing", []) if x.get("amount") and x["type"] not in SHORT_TERM]
    if len(long_term) >= 2:
        tot = sum(x["amount"] for x in long_term)
        basis = f"; compares with a {m(price)} sale price" if price else (f"; compares with a {m(tdc)} total development cost" if tdc else "")
        excl = " (excludes short-term construction, bridge and predevelopment loans)" if any(x["type"] in SHORT_TERM for x in r["financing"]) else ""
        calcs["financing_total"] = {"value": tot, "how": " + ".join(m(x["amount"]) for x in long_term) + excl + basis}

    statuses = best(facts["status"])
    dated = [e["date"] for e in r.get("events", []) if not e.get("estimated")]
    stale_since = max(dated) if dated and statuses in STALE_STATUSES and is_stale(max(dated), date.today()) else ""
    if stale_since:
        statuses = "Inactive pipeline"
    kinds = []
    if statuses in PIPELINE_STATUSES:
        kinds.append("pipeline")
    ev_types = {e["type"] for e in r.get("events", [])}
    if "Sale" in ev_types:
        kinds.append("sale")
    if "Refinance" in ev_types:
        kinds.append("refi")
    if "sale" in kinds or "refi" in kinds:
        kinds.append("transaction")
    elif statuses == "Existing":
        kinds.append("existing")

    debt = [x for x in r.get("financing", []) if x["type"] not in EQUITY and x.get("amount")]
    main_lender = ""
    if debt:
        top = max(debt, key=lambda x: x["amount"])
        if top.get("group"):
            g = [x["provider"] for x in r["financing"] if x.get("group") == top["group"]]
            main_lender = "Possibly " + " or ".join(g)
        else:
            main_lender = top["provider"] + (f" ({top['program']})" if top.get("program") else "")

    ami = best(facts.get("restricted_by_ami"))
    aff_bucket, aff_label, aff_share = affordability(facts, ami, units)
    lihtc = (any(x["type"] in TAX_CREDIT_TYPES - {"Tax-exempt bonds"} for x in r.get("financing", []))
             or any(sources[s]["publisher"].startswith("California Tax Credit Allocation Committee") for s in order if s in sources))
    tax_credit = lihtc or any(x["type"] == "Tax-exempt bonds" for x in r.get("financing", []))
    if lihtc and aff_bucket != "Affordable":  # a tax credit project competes for affordable financing whatever its label says
        aff_bucket, aff_label = "Affordable", "Affordable"
    use_price = price is not None and ("transaction" in kinds or tdc is None)
    summary = {
        "product_type": best(facts["product_type"]),
        "status": statuses,
        "jurisdiction": best(facts.get("jurisdiction")) or "",
        "community": best(facts.get("community")) or "",
        "county": COUNTY_BY_PREFIX[r["id"][:3]],
        "area": (f"Unincorporated ({best(facts.get('community'))})" if best(facts.get("jurisdiction")) == "Unincorporated"
                 else best(facts.get("jurisdiction")) or ""),
        "total_units": units,
        "units_display": units_display(facts.get("total_units")),
        "units_range": units_range(facts.get("total_units")),
        "restricted_units": sum(x["count"] for x in ami) if ami else None,
        "aff_bucket": aff_bucket,
        "aff_label": aff_label,
        "aff_share": aff_share,
        "tax_credit": tax_credit,
        "owner": "; ".join(p["company"] for p in r.get("parties", []) if p["role"] == "Recorded owner"),
        "developer": "; ".join(p["company"] for p in r.get("parties", []) if p["role"] == "Developer"),
        "cost_basis": "Sale price" if use_price else ("Total development cost" if tdc else ""),
        "cost": price if use_price else tdc,
        "per_unit": (calcs.get("price_per_unit") if use_price else calcs.get("cost_per_unit") or {}).get("value") if (price or tdc) and units else None,
        "main_lender": main_lender,
        "latest_event": max(dated) if dated else "",
        "stale_since": stale_since,
    }

    words = [r["name"], summary["community"], summary["jurisdiction"]]
    words += [p["apn"] for p in r["parcels"]] + address_texts(r)
    for f in facts.values():
        for cl in f["claims"]:
            words.append(json.dumps(cl["value"]) if not isinstance(cl["value"], str) else cl["value"])
            words.append(cl.get("note") or "")
    words += [n["text"] for n in r.get("construction_notes", [])]
    for p in r.get("parties", []):
        words += [p["role"], p.get("other_role") or "", p["company"], p.get("contact") or ""]
    for x in r.get("financing", []):
        words += [x["provider"], x["type"], x.get("program") or ""]
    words += [e["label"] for e in r.get("events", [])]

    out = dict(r)
    out.update({"srcLabels": src_labels, "lat": lat, "lng": lng, "calcs": calcs, "kinds": kinds,
                "summary": summary, "search": " ".join(w for w in words if w).lower()})
    out.setdefault("groups", {})
    out.setdefault("construction_notes", [])
    return out


def main():
    sources = load("sources", SRC_RE)
    records = load("records", ID_RE)
    errors = [e for r in records.values() for e in validate(r, sources)]
    errors += [f"{s['id']}: source type {s.get('type')!r} not in schema.SOURCE_TYPES" for s in sources.values() if s.get("type") not in schema.SOURCE_TYPES]
    cited = set(json.dumps(list(records.values())).split('"'))
    errors += [f"{sid}: source is not cited by any record (delete it or cite it)" for sid in sources if sid not in cited]
    seen = {}
    for r in records.values():
        for p in r.get("parcels", []):
            if p.get("apn") in seen and seen[p["apn"]] != r["id"]:
                errors.append(f"{r['id']}: APN {p['apn']} is already in {seen[p['apn']]} (possible duplicate project)")
            seen.setdefault(p.get("apn"), r["id"])
    if errors:
        print("Build stopped. Fix these first:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    processed = [process(r, sources) for r in records.values()]
    payload = {"built": date.today().isoformat(), "registry": schema.registry(),
               "sources": sources, "records": processed, "leads": read_leads(processed)}

    template = (ROOT / "scripts" / "template.html").read_text(encoding="utf-8")
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = template.replace("/*__DATA__*/null", blob)
    (DOCS / "data").mkdir(parents=True, exist_ok=True)
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    (DOCS / "data" / "records.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {len(processed)} records from {len(sources)} sources -> docs/index.html")
    for r in processed:
        s = r["summary"]
        print(f"  {r['id']}  {r['name']}: {s['status']}, {s['total_units']} units, {', '.join(r['kinds'])}")


if __name__ == "__main__":
    main()
