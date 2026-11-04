"""Import pipeline projects from the state Housing Element Annual Progress Reports (APR).

    python scripts/import_apr.py path/to/apr_raw.json          dry run: counts only
    python scripts/import_apr.py path/to/apr_raw.json --write  create records and sources

Data: data.ca.gov, HCD APR Tables A (applications) and A2 (entitlements, permits, completions).
Cities report these rows themselves, one row per activity and year, so rows are merged into
projects here. A project enters only if its parcel checks out against county GIS. Anything
doubtful goes to reference/apr_import_review.csv for a person, not into the database.
Records already matching an existing record by APN or address are skipped, so a rerun is safe.
"""
import collections
import csv
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import parcels
import schema

ROOT = Path(__file__).resolve().parent.parent
RECORDS, SOURCES = ROOT / "data" / "records", ROOT / "data" / "sources"
TODAY = date.today().isoformat()
DATASET = "https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year"
TABLES = {"A": "c78b769d-cc02-4050-91ef-79ded665b5a8", "A2": "fe505d9b-8c36-42ba-ba30-08bc4f34e022"}
PARCEL_SRC = {
    "SMC": ("Active Parcels (county parcel layer)", "San Mateo County GIS", "https://gis.smcgov.org/maps/rest/services/Common/ACTIVE_PARCELS_APN/MapServer/0"),
    "SCC": ("Parcels (county parcel dataset)", "County of Santa Clara", "https://data.sccgov.org/d/ubcd-cewv"),
}
INC = ["ACUTELY_LOW_INCOME", "EXTREMELY_LOW_INCOME", "VLOW_INCOME", "LOW_INCOME", "MOD_INCOME"]
NOTE = ("Imported from the state Housing Element Annual Progress Report, which cities file themselves and which runs through 2025. "
        "Not yet checked against the city's own project list.")
MAX_ADDRESSES = 25
MIN_UNITS = 5


def n(x):
    try:
        return int(float(x or 0))
    except (TypeError, ValueError):
        return 0


def norm(a):
    a = re.sub(r"[^A-Z0-9 ]", " ", (a or "").upper())
    a = re.sub(r"\b(STREET|ST|AVENUE|AVE|AV|ROAD|RD|BOULEVARD|BLVD|BL|DRIVE|DR|WAY|WY|LANE|LN|COURT|CT|PLACE|PL|UNIT|APT|STE|BLDG)\b.*$", "", a)
    return re.sub(r"\s+", " ", a).strip()


def apn_tokens(text, county):
    pat = r"\b\d{3}-?\d{2}-?\d{3}\b" if county == "SCC" else r"\b\d{3}-?\d{3}-?\d{3}\b"
    return [parcels.fmt_apn(t, county) for t in re.findall(pat, str(text or ""))]


def good_date(d):
    d = str(d or "")[:10]
    return d if re.match(r"^20(1\d|2[0-6])-\d\d-\d\d$", d) else None


def rollup(raw):
    rows = [dict(r, _t=t) for t in ("A", "A2") for r in raw[t]]
    par = {}

    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for i, r in enumerate(rows):
        me, j = ("r", i), r["JURIS_NAME"]
        ad = norm(r.get("STREET_ADDRESS"))
        if re.match(r"^[1-9]", ad):
            par[find(me)] = find(("ad", j, ad))
        county = "SMC" if r["CNTY_NAME"] == "San Mateo" else "SCC"
        for t in apn_tokens(r.get("APN"), county):
            if not set(parcels.digits(t)) <= {"0"}:
                par[find(me)] = find(("ap", j, parcels.digits(t)))
        pid = str(r.get("JURS_TRACKING_ID") or "").strip()
        if len(pid) >= 5 and not re.match(r"^(N/?A|NONE|TBD|0+)$", pid, re.I):
            par[find(me)] = find(("id", j, pid))
    groups = collections.defaultdict(list)
    for i, r in enumerate(rows):
        groups[find(("r", i))].append(r)

    out = []
    for rs in groups.values():
        a2 = [r for r in rs if r["_t"] == "A2"]
        a = [r for r in rs if r["_t"] == "A"]
        by = collections.defaultdict(int)
        for r in a2:
            u = sum(n(r.get(i + "_DR")) + n(r.get(i + "_NDR")) for i in INC) + n(r.get("ABOVE_MOD_INCOME"))
            k = norm(r.get("STREET_ADDRESS"))
            by[k] = max(by[k], u, n(r.get("NO_ENTITLEMENTS")))
        a2u, prop = sum(by.values()), max([n(r.get("TOT_PROPOSED_UNITS")) for r in a] or [0])
        dates = lambda col, src: sorted(filter(None, (good_date(r.get(col)) for r in src)))
        latest = max(a, key=lambda r: (r["YEAR"], str(r.get("APP_SUBMIT_DT"))), default=None)
        r0 = max(rs, key=lambda r: r.get("SCORE") or 0)
        county = "SMC" if r0["CNTY_NAME"] == "San Mateo" else "SCC"
        out.append({
            "county": county, "juris": r0["JURIS_NAME"],
            "addresses": sorted({str(r["STREET_ADDRESS"]).strip() for r in rs if r.get("STREET_ADDRESS")},
                                key=lambda x: (not re.match(r"^[1-9]", x), len(x))),
            "names": sorted({str(r["PROJECT_NAME"]).strip() for r in rs if r.get("PROJECT_NAME")}),
            "apns": sorted({t for r in rs for t in apn_tokens(r.get("APN"), county)}),
            "files": sorted({str(r["JURS_TRACKING_ID"]).strip() for r in rs if r.get("JURS_TRACKING_ID")}),
            "cats": {r["UNIT_CAT"] for r in rs if r.get("UNIT_CAT")},
            "tenure": {r["TENURE"] for r in rs if r.get("TENURE")},
            "a2units": a2u, "proposed": prop, "size": max(a2u, prop),
            "dr": max([sum(n(r.get(i + "_DR")) for i in INC) for r in a2] or [0]),
            "app_dt": (dates("APP_SUBMIT_DT", a) or [None])[0],
            "ent_dt": (dates("ENT_APPROVE_DT1", a2) or [None])[-1],
            "bp_dt": (dates("BP_ISSUE_DT1", a2) or [None])[-1],
            "co_dt": (dates("CO_ISSUE_DT1", a2) or [None])[-1],
            "co_units": sum(n(r.get("NO_OTHER_FORMS_OF_READINESS")) for r in a2),
            "app_status": latest.get("APPLICATION_STATUS") if latest else None,
            "lat": r0.get("LATITUDE"), "lng": r0.get("LONGITUDE"), "score": r0.get("SCORE") or 0, "std": r0.get("STD_ADDRESS"),
            "sb35": any(str(r.get("APPROVE_SB35") or r.get("APP_SUBMITTED_SB35") or "").upper() in ("YES", "Y") for r in rs),
            "tables": {r["_t"] for r in rs},
        })
    return out


def stage(p):
    """(status, note) from what the report states; None when the project is finished."""
    if p["co_units"] >= p["size"]:
        return None, ""
    if p["co_dt"]:
        return "Under construction", "State report shows certificates of occupancy for some of the units, not all"
    if p["bp_dt"]:
        return "Permitted", "State report shows a building permit issued; it does not say whether construction started"
    if p["ent_dt"]:
        return "Approved", "State report shows entitlement approval"
    if p["app_status"] == "Withdrawn":
        return "Inactive pipeline", "State report shows the application withdrawn"
    if p["app_status"] == "Disapproved":
        return "Inactive pipeline", "State report shows the application disapproved"
    if p["app_status"] == "Approved":
        return "Approved", "State report shows the application approved"
    return "Proposed", "State report shows an application with no approval reported"


def product(p):
    cats = p["cats"] - {"ADU", "MH", "2 to 4"}
    multi, sfa, sfd = any(c.startswith("5") for c in cats), "SFA" in cats, "SFD" in cats
    if multi + sfa + sfd > 1:
        return "Mixed product", "State categories: " + ", ".join(sorted(cats))
    if sfa:
        return "Townhomes", "State category: single-family attached"
    if sfd:
        return "Single-family", "State category: single-family detached"
    if multi:
        if p["tenure"] == {"Owner"}:
            return "Condominiums", "State category 5+ units, for-sale tenure"
        return "Apartments", "State category 5+ units, " + ("rental tenure" if p["tenure"] == {"Renter"} else "tenure not clear")
    return None, ""


def place(p):
    j = p["juris"]
    if j.endswith(" COUNTY"):
        city = ((p["std"] or "").split(",") + ["", ""])[1].strip().lower()
        county = schema.COUNTIES["San Mateo County" if p["county"] == "SMC" else "Santa Clara County"]
        com = next((u for u in county["unincorporated"] if u.lower() == city), None)
        return "Unincorporated", com or county["unincorporated"][-1]
    t = j.title().replace(" Of ", " of ")
    return t, None


def is_file_number(s):
    return bool(re.match(r"^[A-Z]{1,5}[\s-]?\d{2,}[\w-]*(\s|$)", s.strip())) or bool(re.match(r"^\d{2,4}-\d+", s.strip()))


JUNK_NAME = re.compile(r"^(none|n/?a|tbd|-|ar|aho\b.*|preliminary.*|pre-?app.*|tesp.*|.*exempt|.*-plex|.*\btract|.*investments?|.*\bllc|.*\binc\.?)$", re.I)


def clean_address(a, city):
    """One street address in readable case, without a repeated city, state or zip."""
    a = re.split(r"\s*;\s*", str(a))[0]
    a = re.sub(r",?\s*(#|unit|ste|suite)\s*\w+\s*,", ",", a, flags=re.I)
    a = re.sub(rf",?\s*({re.escape(city)})?\s*,?\s*(CA|California)?\s*(\d{{5}}(-\d{{4}})?)?\s*$", "", a, flags=re.I).strip(" ,.")
    a = re.sub(r"\b\w+\b", lambda m: m.group(0).upper() if re.match(r"^[NSEW]{2}$", m.group(0), re.I) else m.group(0).capitalize(), a)
    return re.sub(r"(\d)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), a)


def name_of(p, city):
    good = [re.sub(r"\s*-\s*Pre-?Application$", "", x, flags=re.I).strip() for x in p["names"]]
    good = [x for x in good if not JUNK_NAME.match(x) and len(x) >= 4 and len(x) <= 70 and not is_file_number(x) and not re.match(r"^\d", x)]
    return good[0] if good else (clean_address(p["addresses"][0], city) if p["addresses"] else "")


def by_address(p, a):
    """The parcel whose situs is this house number and street in this city, if exactly one matches."""
    m = re.match(r"^([1-9]\d*)\s+(?:[NSEW]\.?\s+)?(.+)", norm(a))
    if not m or len(m.group(2)) < 3:
        return None
    num, street = m.group(1), parcels.esc(m.group(2))
    if p["county"] == "SCC":
        rows = parcels.scc_query(f"situs_house_number='{num}' AND upper(situs_street_name) like '{street}%' AND jurisdiction='{p['juris']}'", limit=3)
        apns = {x.get("apn") for x in rows if x.get("apn")}
    else:
        feats = parcels.smc_query(f"SITUS_ADDR LIKE '{num} %{street}%'", limit=5)
        city = p["juris"]
        apns = {f["attributes"]["APN"] for f in feats if city.endswith(" COUNTY") or (f["attributes"]["SITUS_CITY"] or "").upper() == city}
    if len(apns) != 1:
        return None
    got = parcels.lookup(p["county"], apn=apns.pop())
    return got if got and got["outline"] else None


def locate(p):
    """(list of parcels, how) checked against county GIS, or ([], reason)."""
    found = []
    for t in p["apns"][:10]:
        got = parcels.lookup(p["county"], apn=t)
        if got and got["outline"]:
            found.append(got)
    if found:
        return found, "apn"
    for a in p["addresses"][:3]:
        got = by_address(p, a)
        if got:
            return [got], "address"
    if p["lat"] and p["score"] >= 90 and p["addresses"]:
        got = parcels.lookup(p["county"], point=(p["lat"], p["lng"]))
        num = re.match(r"^(\d+)", p["addresses"][0])
        if got and got["outline"] and num and re.match(rf"^{num.group(1)}\b", got["situs"] or ""):
            return [got], "point"
        return [], "state map point lands on a parcel with a different address"
    return [], "no usable APN or map point"


def main():
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    write = "--write" in sys.argv
    projects = rollup(raw)
    existing = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(RECORDS.glob("*.json"))]
    seen_apn, seen_addr = {}, {}
    for r in existing:
        jur = r["facts"]["jurisdiction"]["claims"][0]["value"] if "jurisdiction" in r["facts"] else ""
        for x in r["parcels"]:
            seen_apn[parcels.digits(x["apn"])] = r["id"]
        for a in r["addresses"]:
            seen_addr[(jur.upper(), norm(a["text"].split(",")[0]))] = r["id"]

    review, counts, cand = [], collections.Counter(), []
    def skip(p, why):
        counts[why.split(":")[0]] += 1
        review.append({"city": p["juris"], "address": (p["addresses"] or [""])[0], "units": p["size"], "name": "; ".join(p["names"][:2]), "apn": "; ".join(p["apns"][:3]), "why": why})
    for p in projects:
        if p["size"] < MIN_UNITS or not p["cats"] - {"ADU", "MH", "2 to 4"}:
            counts["under 5 units or not a housing project"] += 1
            continue
        status, note = stage(p)
        if status is None:
            counts["finished, not pipeline"] += 1
            continue
        if len(p["addresses"]) > MAX_ADDRESSES:
            skip(p, f"rows merged across {len(p['addresses'])} addresses; a person should decide if this is one project")
            continue
        cand.append((p, status, note))
    with ThreadPoolExecutor(8) as ex:
        located = list(ex.map(lambda c: locate(c[0]), cand))

    sources = sorted(SOURCES.glob("SRC-*.json"))
    next_src = max(int(f.stem[4:]) for f in sources) + 1
    src_new, src_index = {}, {}

    def source(key, title, publisher, url, typ="Government dataset", dated=None):
        nonlocal next_src
        if key not in src_index:
            sid = f"SRC-{next_src:06d}"
            next_src += 1
            src_index[key] = sid
            src_new[sid] = {"id": sid, "title": title, "publisher": publisher, "date": dated or TODAY, "type": typ, "url": url,
                            "retrieved": TODAY, "wayback": None, "copyright": False, "sha256": None}
        return src_index[key]

    nextid = {pre: max([int(r["id"][4:]) for r in existing if r["id"].startswith(pre)] or [0]) + 1 for pre in ("SMC", "SCC")}
    new_records = []
    for (p, status, note), (found, how) in sorted(zip(cand, located), key=lambda x: -x[0][0]["size"]):
        if not found:
            skip(p, how)
            continue
        jur, com = place(p)
        if jur != "Unincorporated" and jur not in schema.JURISDICTIONS:
            skip(p, f"jurisdiction {jur} not recognized")
            continue
        hit = next((seen_apn[parcels.digits(x["apn"])] for x in found if parcels.digits(x["apn"]) in seen_apn), None)
        hit = hit or next((seen_addr[(jur.upper(), norm(a))] for a in p["addresses"] if (jur.upper(), norm(a)) in seen_addr), None)
        if hit:
            counts["already in the database"] += 1
            if hit.startswith(("SMC-", "SCC-")) and any(hit == r["id"] for r in new_records):
                review.append({"city": p["juris"], "address": (p["addresses"] or [""])[0], "units": p["size"], "name": "; ".join(p["names"][:2]), "apn": "; ".join(x["apn"] for x in found[:3]), "why": f"same parcel as {hit}, also imported; possibly a second application for the site"})
            continue
        ptype, pnote = product(p)
        if not ptype:
            skip(p, "no housing category")
            continue
        def s(t):
            label = "Table A (applications)" if t == "A" else "Table A2 (entitlements, permits, completions)"
            return source(("apr", p["juris"], t), f"Housing Element Annual Progress Report, {label}, {p['juris'].title()}",
                          "California Department of Housing and Community Development",
                          f"{DATASET}/resource/{TABLES[t]}?filters=JURIS_NAME:{p['juris'].replace(' ', '+')}", dated="2026-10-30")
        pre = p["county"]
        ps = source(("parcel", pre), *PARCEL_SRC[pre])
        src_all = [s(t) for t in sorted(p["tables"])]
        sA, sA2 = (s("A") if "A" in p["tables"] else None), (s("A2") if "A2" in p["tables"] else None)
        city = jur if jur != "Unincorporated" else com
        addrs = [{"text": f"{clean_address(a, city)}, {city}, CA", "src": src_all} for a in p["addresses"][:6] if re.match(r"^[1-9]", a)]
        facts = {
            "product_type": {"claims": [{"value": ptype, "src": src_all, "note": pnote}]},
            "status": {"claims": [{"value": status, "src": src_all, "note": note}]},
            "jurisdiction": {"claims": [{"value": jur, "src": src_all}]},
        }
        if com:
            facts["community"] = {"claims": [{"value": com, "src": src_all, "note": "Named from the state's mapped address" if not com.startswith("Other") else "Community not stated in the state report"}]}
        claims = []
        if p["a2units"]:
            claims.append({"value": p["a2units"], "src": [sA2], "note": "Units reported in entitlement and permit rows"})
        if p["proposed"] and p["proposed"] != p["a2units"]:
            claims.append({"value": p["proposed"], "src": [sA], "note": "Units in the application as reported"})
        facts["total_units"] = {"claims": claims}
        if len(claims) > 1 and p["a2units"] < p["proposed"]:
            facts["total_units"]["best"] = 1  # permit rows can cover only part of a project; the application states the whole
        if p["dr"] and sA2:
            facts["affordability_type"] = {"claims": [{"value": "100% affordable" if p["dr"] >= p["a2units"] - 2 else "Mixed-income", "src": [sA2]}]}
            facts["affordability_notes"] = {"claims": [{"value": f"{p['dr']} deed-restricted units reported to the state", "src": [sA2]}]}
        if p["sb35"]:
            facts["approval_type"] = {"claims": [{"value": ["Streamlined / ministerial"], "src": src_all, "note": "SB 35 flagged in the state report"}]}
        file_ids = [x for x in p["names"] + p["files"] if is_file_number(x)][:3] or p["files"][:3]
        if file_ids:
            facts["planning_file"] = {"claims": [{"value": ", ".join(dict.fromkeys(x.split()[0] if is_file_number(x) else x for x in file_ids)), "src": src_all, "note": "Local tracking number as reported to the state"}]}
        events = []
        if p["app_dt"] and sA:
            events.append({"date": p["app_dt"], "type": "Application filed", "label": "Application submitted", "src": [sA]})
        if p["ent_dt"] and sA2:
            events.append({"date": p["ent_dt"], "type": "Approved", "label": "Entitlement approved", "src": [sA2]})
        if p["bp_dt"] and sA2:
            events.append({"date": p["bp_dt"], "type": "Permit issued", "label": "Building permit issued", "src": [sA2]})
        if p["co_dt"] and sA2:
            events.append({"date": p["co_dt"], "type": "Other", "label": "Certificate of occupancy reported for some units", "src": [sA2]})
        parties = [{"role": "Recorded owner", "company": o, "contact": None, "linkedin": None, "src": [ps]}
                   for o in dict.fromkeys(x["owner"] for x in found if x["owner"])][:3]
        rid = f"{pre}-{nextid[pre]:06d}"
        nextid[pre] += 1
        rec = {"id": rid, "name": name_of(p, city) or found[0]["situs"], "parcels": [{"apn": x["apn"], "from": None, "to": None, "src": [ps], "outline": x["outline"]} for x in found],
               "addresses": addrs, "images": [], "facts": facts,
               "construction_notes": [{"text": NOTE, "src": src_all}], "parties": parties, "financing": [], "groups": {},
               "events": sorted(events, key=lambda e: e["date"]),
               "history": [{"date": TODAY, "by": "Paul via Claude", "action": "Record created from the state Annual Progress Report data"}]}
        new_records.append(rec)
        counts["imported"] += 1
        for x in found:
            seen_apn[parcels.digits(x["apn"])] = rid
        for a in p["addresses"]:
            seen_addr[(jur.upper(), norm(a))] = rid

    print(dict(counts))
    print("new records", len(new_records), "units", sum(max(c["value"] for c in r["facts"]["total_units"]["claims"]) for r in new_records), "new sources", len(src_new), "review", len(review))
    print(collections.Counter(r["facts"]["status"]["claims"][0]["value"] for r in new_records))
    if not write:
        return
    for r in new_records:
        (RECORDS / f"{r['id']}.json").write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for sid, v in src_new.items():
        (SOURCES / f"{sid}.json").write_text(json.dumps(v, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with open(ROOT / "reference" / "apr_import_review.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["city", "address", "units", "name", "apn", "why"])
        w.writeheader()
        w.writerows(sorted(review, key=lambda x: (x["city"], -x["units"])))
    print("written")


if __name__ == "__main__":
    main()
