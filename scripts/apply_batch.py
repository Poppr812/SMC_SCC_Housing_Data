"""Add researched projects and corrections from a batch file.

    python scripts/apply_batch.py batch.json --check   report problems, change nothing
    python scripts/apply_batch.py batch.json           apply what passes, list what didn't

Batch format (source keys are local to the file):
{
  "sources": {"k1": {"title": "", "publisher": "", "date": "2026-05-01 or null", "type": "<schema.SOURCE_TYPES>",
                     "url": "", "copyright": true}},
  "new": [{"county": "SMC or SCC", "name": "", "apns": ["..."],
           "addresses": [{"text": "", "src": ["k1"]}],
           "facts": {"status": {"claims": [{"value": "", "src": ["k1"], "note": ""}]}, ...},
           "parties": [{"role": "", "company": "", "contact": null, "other_role": null, "src": ["k1"]}],
           "events": [{"date": "", "type": "", "label": "", "src": ["k1"], "estimated": false}],
           "financing": [{"type": "", "provider": "", "program": null, "amount": 1, "date": null, "src": ["k1"]}],
           "notes": [{"text": "", "src": ["k1"]}]}],
  "updates": [{"id": "SCC-000012", "name": "better project name",
               "claims": {"total_units": [{"value": 300, "src": ["k1"], "note": "", "best": true}]},
               "parties": [...], "events": [...], "financing": [...], "addresses": [...], "notes": [...],
               "checked_against_city": true}]
}
A new claim on a fact keeps the old claims. "best": true flags it as the value to use.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

import parcels
import schema

ROOT = Path(__file__).resolve().parent.parent
RECORDS, SOURCES = ROOT / "data" / "records", ROOT / "data" / "sources"
TODAY = date.today().isoformat()
PARCEL_SRC = {
    "SMC": ("Active Parcels (county parcel layer)", "San Mateo County GIS", "https://gis.smcgov.org/maps/rest/services/Common/ACTIVE_PARCELS_APN/MapServer/0"),
    "SCC": ("Parcels (county parcel dataset)", "County of Santa Clara", "https://data.sccgov.org/d/ubcd-cewv"),
}
IMPORT_NOTE = "Not yet checked against the city's own project list."


def main():
    path, check = sys.argv[1], "--check" in sys.argv
    b = json.loads(Path(path).read_text(encoding="utf-8"))
    by_url = {}
    next_src = 0
    for f in SOURCES.glob("SRC-*.json"):
        s = json.loads(f.read_text(encoding="utf-8"))
        by_url[s["url"]] = s["id"]
        next_src = max(next_src, int(s["id"][4:]))
    next_src += 1
    records = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in RECORDS.glob("*.json")}
    apn_owner = {parcels.digits(p["apn"]): r["id"] for r in records.values() for p in r["parcels"]}
    nextid = {pre: max([int(k[4:]) for k in records if k.startswith(pre)] or [0]) + 1 for pre in ("SMC", "SCC")}
    new_sources, problems, done = {}, [], []

    def src_id(key):
        nonlocal next_src
        s = b["sources"][key]
        if s["url"] in by_url:
            return by_url[s["url"]]
        sid = f"SRC-{next_src:06d}"
        next_src += 1
        by_url[s["url"]] = sid
        new_sources[sid] = {"id": sid, "title": s["title"], "publisher": s["publisher"], "date": s.get("date"), "type": s["type"],
                            "url": s["url"], "retrieved": TODAY, "wayback": None, "copyright": bool(s.get("copyright")), "sha256": None}
        return sid

    def resolve(items, where, errs):
        """Swap local source keys for source ids on a list of dicts."""
        out = []
        for it in items or []:
            it = dict(it)
            srcs = it.get("src") or []
            bad = [k for k in srcs if k not in b["sources"]]
            if bad or not srcs:
                errs.append(f"{where}: unknown or missing source {bad or ''}")
                continue
            it["src"] = [src_id(k) for k in srcs]
            out.append(it)
        return out

    def check_claim(key, v, errs):
        if key not in schema.FACTS:
            return errs.append(f"unknown fact {key}")
        _, _, kind, opts = schema.FACTS[key]
        if kind == "cat" and v not in opts:
            errs.append(f"{key}: {v!r} is not a defined label")
        if kind == "catmulti" and (not isinstance(v, list) or any(x not in opts for x in v)):
            errs.append(f"{key}: {v!r} has an undefined label")
        if kind in ("int", "money") and not isinstance(v, int):
            errs.append(f"{key}: {v!r} should be a whole number")

    def check_lists(x, errs):
        for p in x.get("parties") or []:
            if p.get("role") not in schema.PARTY_ROLES:
                errs.append(f"party role {p.get('role')!r} not defined")
            if p.get("role") == "Other" and not p.get("other_role"):
                errs.append(f"party {p.get('company')}: role Other needs other_role")
        for e in x.get("events") or []:
            if e.get("type") not in schema.EVENT_TYPES:
                errs.append(f"event type {e.get('type')!r} not defined")
            if not re.match(r"^\d{4}(-\d\d(-\d\d)?)?$", str(e.get("date"))):
                errs.append(f"event date {e.get('date')!r} not YYYY, YYYY-MM or YYYY-MM-DD")
        for f in x.get("financing") or []:
            if f.get("type") not in schema.FINANCING_TYPES:
                errs.append(f"financing type {f.get('type')!r} not defined")

    def parties_of(items, where, errs):
        return [{"role": p["role"], "company": p["company"], "contact": p.get("contact"), "linkedin": p.get("linkedin"), **({"other_role": p["other_role"]} if p.get("other_role") else {}), "src": p["src"]}
                for p in resolve(items, where, errs)]

    def notes_of(items, where, errs):
        return [{"text": n["text"], "src": n["src"]} for n in resolve(items, where, errs)]

    for x in b.get("new", []):
        errs, tag = [], x.get("name", "?")
        pre = x.get("county")
        if pre not in nextid:
            problems.append(f"{tag}: county must be SMC or SCC")
            continue
        check_lists(x, errs)
        facts = {}
        for key, f in (x.get("facts") or {}).items():
            for c in f["claims"]:
                check_claim(key, c.get("value"), errs)
            facts[key] = dict(f, claims=resolve(f["claims"], key, errs))
        for key in ("product_type", "status", "jurisdiction"):
            if key not in facts:
                errs.append(f"missing fact {key}")
        county = schema.COUNTIES["San Mateo County" if pre == "SMC" else "Santa Clara County"]
        jur = (facts.get("jurisdiction") or {"claims": [{}]})["claims"][0].get("value") if facts.get("jurisdiction", {}).get("claims") else None
        if jur == "Unincorporated":
            com = (facts.get("community") or {"claims": [{}]})["claims"][0].get("value")
            if com not in county["unincorporated"]:
                errs.append(f"unincorporated needs community from {county['unincorporated']}")
        elif jur not in county["cities"]:
            errs.append(f"jurisdiction {jur!r} is not in this county")
        found = []
        for a in x.get("apns") or []:
            hit = parcels.lookup(pre, apn=a)
            if not hit or not hit["outline"]:
                errs.append(f"APN {a} is not a parcel in county data")
            elif parcels.digits(hit["apn"]) in apn_owner:
                errs.append(f"APN {a} is already in {apn_owner[parcels.digits(hit['apn'])]}: send an update, not a new record")
            else:
                found.append(hit)
        if not found and not errs:
            errs.append("no APN")
        if errs:
            problems.append(f"{tag}: " + "; ".join(errs))
            continue
        rid = f"{pre}-{nextid[pre]:06d}"
        nextid[pre] += 1
        s = PARCEL_SRC[pre]
        if s[2] not in by_url:
            b["sources"]["__parcel" + pre] = {"title": s[0], "publisher": s[1], "date": TODAY, "type": "Government dataset", "url": s[2], "copyright": False}
            ps = src_id("__parcel" + pre)
        else:
            ps = by_url[s[2]]
        rec = {"id": rid, "name": x["name"],
               "parcels": [{"apn": h["apn"], "from": None, "to": None, "src": [ps], "outline": h["outline"]} for h in found],
               "addresses": [{"text": a["text"], "src": a["src"]} for a in resolve(x.get("addresses"), "address", errs)],
               "images": [], "facts": facts, "construction_notes": notes_of(x.get("notes"), "note", errs),
               "parties": parties_of(x.get("parties"), "party", errs), "financing": resolve(x.get("financing"), "financing", errs), "groups": {},
               "events": sorted(resolve(x.get("events"), "event", errs), key=lambda e: str(e["date"])),
               "history": [{"date": TODAY, "by": "Paul via Claude", "action": "Record created from city, state and news sources"}]}
        records[rid] = rec
        for h in found:
            apn_owner[parcels.digits(h["apn"])] = rid
        done.append(rid)

    for u in b.get("updates", []):
        rid, errs = u.get("id"), []
        r = records.get(rid)
        if not r:
            problems.append(f"update {rid}: no such record")
            continue
        check_lists(u, errs)
        for key, cl in (u.get("claims") or {}).items():
            for c in cl:
                check_claim(key, c.get("value"), errs)
        if errs:
            problems.append(f"update {rid}: " + "; ".join(errs))
            continue
        if u.get("name"):
            r["name"] = u["name"]
        for key, cl in (u.get("claims") or {}).items():
            f = r["facts"].setdefault(key, {"claims": []})
            for c in resolve(cl, key, errs):
                best = c.pop("best", False)
                same = next((i for i, o in enumerate(f["claims"]) if o["value"] == c["value"]), None)
                if same is None:
                    f["claims"].append(c)
                    same = len(f["claims"]) - 1
                else:
                    f["claims"][same]["src"] = list(dict.fromkeys(f["claims"][same]["src"] + c["src"]))
                if best:
                    f["best"] = same
            if len(f["claims"]) > 1 and f.get("best") is None and key in ("product_type", "status", "jurisdiction"):
                errs.append(f"{key} now has competing claims; mark one best")
        r["parties"] += [p for p in parties_of(u.get("parties"), "party", errs)
                         if not any(o["role"] == p["role"] and o["company"].lower() == p["company"].lower() for o in r["parties"])]
        r["financing"] += resolve(u.get("financing"), "financing", errs)
        r["events"] = sorted(r["events"] + [e for e in resolve(u.get("events"), "event", errs)
                                            if not any(o["date"] == e["date"] and o["type"] == e["type"] for o in r["events"])], key=lambda e: str(e["date"]))
        r["addresses"] += [a for a in resolve(u.get("addresses"), "address", errs) if not any(o["text"].lower() == a["text"].lower() for o in r["addresses"])]
        r["construction_notes"] = r.get("construction_notes", []) + notes_of(u.get("notes"), "note", errs)
        if u.get("checked_against_city"):
            for n in r["construction_notes"]:
                n["text"] = n["text"].replace(" " + IMPORT_NOTE, "")
        if errs:
            problems.append(f"update {rid}: " + "; ".join(errs))
            continue
        r["history"].append({"date": TODAY, "by": "Paul via Claude", "action": "Updated from city, state and news sources"})
        done.append(rid)

    print(f"{'Would apply' if check else 'Applied'} {len(done)} of {len(b.get('new', [])) + len(b.get('updates', []))}; new sources {len(new_sources)}")
    for p in problems:
        print("  PROBLEM", p)
    if check:
        return
    for rid in done:
        (RECORDS / f"{rid}.json").write_text(json.dumps(records[rid], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    cited = json.dumps([records[rid] for rid in done])
    for sid, s in new_sources.items():
        if sid in cited:
            (SOURCES / f"{sid}.json").write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
